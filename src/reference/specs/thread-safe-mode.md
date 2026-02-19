# Thread-Safe Mode & Instance API

*New in DataJoint 2.2*

## Overview

DataJoint provides two patterns for database access:

1. **Global pattern** — a singleton config (`dj.config`) and connection (`dj.conn()`) shared across the process. Suitable for interactive sessions and single-user scripts.

2. **Instance pattern** — isolated `dj.Instance` objects, each with its own config and connection. Required for multi-tenant applications, web servers, and concurrent pipelines.

**Thread-safe mode** (`DJ_THREAD_SAFE=true`) disables the global pattern, forcing all code to use explicit Instances.

## Instance API

### `dj.Instance`

```python
dj.Instance(host, user, password, port=None, use_tls=None, **kwargs)
```

Creates an isolated config and connection pair.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | — | Database hostname (required) |
| `user` | `str` | — | Database username (required) |
| `password` | `str` | — | Database password (required) |
| `port` | `int` | from config | Database port |
| `use_tls` | `bool \| dict` | `None` | TLS configuration |
| `**kwargs` | — | — | Config overrides (see below) |

**Config overrides:** Any keyword argument that matches a config attribute is applied to the Instance's config. Use double underscores for nested settings:

```python
inst = dj.Instance(
    host="localhost", user="root", password="secret",
    safemode=False,                 # inst.config.safemode = False
    database__reconnect=False,      # inst.config.database.reconnect = False
)
```

### Instance attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `inst.config` | `Config` | This Instance's configuration object |
| `inst.connection` | `Connection` | This Instance's database connection |

### Instance methods

#### `inst.Schema(schema_name, *, context=None, create_schema=True, create_tables=None, add_objects=None)`

Create a `Schema` bound to this Instance's connection. Parameters are identical to `dj.Schema()`.

#### `inst.FreeTable(full_table_name)`

Create a `FreeTable` bound to this Instance's connection. The `full_table_name` argument is the full table name as `'schema.table'` or `` `schema`.`table` ``.

## Global Pattern (Legacy)

The global pattern uses module-level state:

| Symbol | Description |
|--------|-------------|
| `dj.config` | Proxy to the global `Config` object. Raises `ThreadSafetyError` in thread-safe mode. |
| `dj.conn()` | Returns the singleton `Connection`. Creates it lazily on first call. Raises `ThreadSafetyError` in thread-safe mode. |
| `dj.Schema()` | Creates a Schema using the singleton connection (when no `connection=` argument is provided). Raises `ThreadSafetyError` in thread-safe mode. |
| `dj.FreeTable()` | Creates a FreeTable using the singleton connection (when called with a single string argument). Raises `ThreadSafetyError` in thread-safe mode. |

The global config is created at import time from environment variables and the `datajoint.json` config file. The singleton connection is created lazily on first access to `dj.conn()` or `dj.Schema()`.

## Thread-Safe Mode

### Activation

Thread-safe mode is controlled by the `DJ_THREAD_SAFE` environment variable. It must be set before the process starts — there is no runtime API to toggle it, because mutating a global to enable thread-safety would be self-contradictory.

| Variable | Enabled values | Disabled values | Default |
|----------|---------------|-----------------|---------|
| `DJ_THREAD_SAFE` | `true`, `1`, `yes` | `false`, `0`, `no` | `false` (disabled) |

### Behavior

When thread-safe mode is enabled:

| Operation | Behavior |
|-----------|----------|
| `dj.config` (any access) | Raises `ThreadSafetyError` |
| `dj.conn()` | Raises `ThreadSafetyError` |
| `dj.Schema()` without `connection=` | Raises `ThreadSafetyError` |
| `dj.FreeTable("name")` without connection | Raises `ThreadSafetyError` |
| `dj.Instance(...)` | Works normally |
| `inst.Schema(...)` | Works normally |
| `inst.FreeTable(...)` | Works normally |
| `inst.config` | Works normally |
| `dj.config.save_template()` | Works (static method, no global state access) |

### `ThreadSafetyError`

```python
from datajoint.errors import ThreadSafetyError
```

`ThreadSafetyError` is a subclass of `DataJointError`. It is raised when global state is accessed in thread-safe mode.

## Architecture

### Object graph

```
settings.py
  config = _create_config()          ← the single global Config

instance.py
  _global_config = settings.config   ← same object (not a copy)
  _singleton_connection = None       ← lazily created Connection

__init__.py
  dj.config = _ConfigProxy()         ← proxy → _global_config (with thread-safety check)
  dj.conn()                          ← returns _singleton_connection
  dj.Schema()                        ← uses _singleton_connection
  dj.FreeTable()                     ← uses _singleton_connection

Connection (singleton)
  _config → _global_config           ← same Config that dj.config writes to

Connection (Instance)
  _config → fresh Config             ← isolated per-instance
```

### Config flow: singleton path

```
dj.config["safemode"] = False
       ↓ _ConfigProxy.__setitem__
_global_config["safemode"] = False   (same object as settings.config)
       ↓
Connection._config["safemode"]       (points to _global_config)
       ↓
schema.drop() reads self.connection._config["safemode"]  → False ✓
```

### Config flow: Instance path

```
inst = dj.Instance(host=..., user=..., password=...)
       ↓
inst.config = _create_config()       (fresh Config, independent)
inst.connection = Connection(..., config_override=inst.config)
       ↓
inst.config.safemode = False
       ↓
schema.drop() reads self.connection._config["safemode"]  → False ✓
```

### Key invariant

**All runtime config reads go through `self.connection._config`**, never through the global `config` directly. This ensures both the singleton and Instance paths read the correct config.

### Connection dependency injection

`Connection.__init__` accepts `backend` and `config_override` keyword arguments:

```python
Connection(host, user, password, port, use_tls,
           backend="mysql",              # explicit backend selection
           config_override=inst.config)  # use this config, not the global
```

When `config_override` is provided, the Connection uses it for all config reads (port, charset, reconnect, query cache, etc.). When omitted, it falls back to the module-level `settings.config`.

When `backend` is provided, it is used directly. When omitted, the backend is read from `self._config["database.backend"]`.

### Connection-scoped config reads

Every module that needs runtime config reads it from `self.connection._config`, not from the global `config` import. This includes:

- `schemas.py` — `safemode`, `create_tables`
- `table.py` — `safemode` in `delete()`, `drop()`
- `expression.py` — `loglevel` in `__repr__()`
- `preview.py` — `display.*` settings
- `autopopulate.py` — `jobs.*` settings
- `jobs.py` — `jobs.*` settings
- `diagram.py` — `display.*` settings

Functions that cannot access `self.connection` receive config as a parameter (e.g., `declare()`, `_get_job_version()`, hash registry functions).

## Global State Audit

### Guarded (blocked in thread-safe mode)

| State | Location | Mechanism |
|-------|----------|-----------|
| Global config | `settings.py` | `_ConfigProxy` raises `ThreadSafetyError` |
| Singleton connection | `instance.py` | `_check_thread_safe()` guard |

### Safe by design (no guard needed)

| State | Location | Rationale |
|-------|----------|-----------|
| `_codec_registry` | `codecs.py` | Immutable after import. Registration runs under Python's import lock. |
| `_entry_points_loaded` | `codecs.py` | Idempotent lazy loading flag. |
| `ADAPTERS` dict | `adapters/__init__.py` | Backend registry, populated at import time. |
| `_lazy_modules` | `__init__.py` | Import caching via `globals()`. Protected by import lock. |
| Logging config | `logging.py` | Standard Python logging. Not connection-scoped. |

### Design principle

Only **connection-scoped** state (credentials, database settings, connection objects) needs thread-safe guards. **Code-scoped** state (type registries, import caches, logging) is shared across all threads by design.
