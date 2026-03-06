# What's New in DataJoint 2.2

DataJoint 2.2 introduces **isolated instances** and **thread-safe mode** for applications that need multiple independent database connections—web servers, multi-tenant notebooks, parallel pipelines, and testing.

> **Upgrading from 2.0 or 2.1?** No breaking changes. All existing code using `dj.config` and `dj.Schema()` continues to work. The new Instance API is purely additive.

> **Citation:** Yatsenko D, Nguyen TT. *DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows.* arXiv:2602.16585. 2026. [doi:10.48550/arXiv.2602.16585](https://doi.org/10.48550/arXiv.2602.16585)

## Overview

DataJoint has traditionally used a global singleton pattern: one configuration (`dj.config`), one connection (`dj.conn()`), shared across all tables in a process. This works well for interactive sessions and single-user scripts, but breaks down when:

- A web server handles requests for different databases simultaneously
- A notebook connects to production and staging databases side by side
- Tests need isolated databases that don't interfere with each other
- Parallel pipelines need independent connections

DataJoint 2.2 solves this with `dj.Instance`—an object that bundles its own configuration and connection, independent of global state.

## `dj.Instance` API

An Instance encapsulates a config and connection pair. Create one by providing database credentials directly:

```python
import datajoint as dj

inst = dj.Instance(host="localhost", user="root", password="secret")
```

Then use `inst.Schema()` instead of `dj.Schema()`:

```python
schema = inst.Schema("my_database")

@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : int32
    ---
    description : varchar(255)
    """
```

Tables defined this way use the Instance's connection—completely independent of `dj.config` and `dj.conn()`.

### Instance Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | — | Database hostname (required) |
| `user` | str | — | Database username (required) |
| `password` | str | — | Database password (required) |
| `port` | int | from config | Database port (default: 3306 for MySQL, 5432 for PostgreSQL) |
| `use_tls` | bool or dict | `None` | TLS configuration |
| `**kwargs` | — | — | Config overrides (e.g., `safemode=False`) |

### Instance Methods

| Method | Description |
|--------|-------------|
| `inst.Schema(name)` | Create a Schema bound to this Instance's connection |
| `inst.FreeTable(full_name)` | Create a FreeTable bound to this Instance's connection |
| `inst.config` | Access this Instance's Config object |
| `inst.connection` | Access this Instance's Connection object |

### Config Overrides

Pass any config setting as a keyword argument. Use double underscores for nested settings:

```python
inst = dj.Instance(
    host="localhost", user="root", password="secret",
    safemode=False,
    database__reconnect=False,
)
```

## Multiple Databases

Instances make it straightforward to work with multiple databases simultaneously:

```python
production = dj.Instance(host="prod.example.com", user="analyst", password="...")
staging = dj.Instance(host="staging.example.com", user="dev", password="...")

prod_schema = production.Schema("experiment_data")
staging_schema = staging.Schema("experiment_data")

# Query both independently
prod_data = ProdTable.to_dicts()
staging_data = StagingTable.to_dicts()
```

Each Instance maintains its own connection pool and configuration—no cross-contamination.

## Thread-Safe Mode

For applications where global state is dangerous (web servers, multi-threaded workers), enable thread-safe mode:

```bash
export DJ_THREAD_SAFE=true
```

When thread-safe mode is enabled:

- `dj.config` raises `ThreadSafetyError` on any access
- `dj.conn()` raises `ThreadSafetyError`
- `dj.Schema()` without an explicit connection raises `ThreadSafetyError`
- Only `dj.Instance()` works, enforcing explicit connection management

This prevents accidental use of shared global state in concurrent environments.

### `ThreadSafetyError`

```python
import os
os.environ["DJ_THREAD_SAFE"] = "true"

import datajoint as dj

dj.config.database.host  # raises ThreadSafetyError
dj.conn()                # raises ThreadSafetyError

# Instead, use Instance:
inst = dj.Instance(host="localhost", user="root", password="secret")
schema = inst.Schema("my_db")  # works
```

### Environment Variable

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `DJ_THREAD_SAFE` | `true`, `1`, `yes` / `false`, `0`, `no` | `false` | Enable thread-safe mode |

## Connection-Scoped Config

Each Instance carries its own `Config` object. Runtime configuration reads go through the Instance's config, not global state:

```python
inst = dj.Instance(host="localhost", user="root", password="secret")

# Instance-scoped config
inst.config.safemode = False
inst.config.display.limit = 25

# Global config is unaffected
print(dj.config.safemode)  # still True (default)
```

Tables created through an Instance's Schema read config from that Instance's connection, not from `dj.config`.

## When to Use Instances

| Scenario | Pattern |
|----------|---------|
| Interactive notebook, single database | `dj.config` + `dj.Schema()` (global pattern) |
| Script connecting to one database | Either pattern works |
| Web server (Flask, FastAPI, Django) | `dj.Instance()` per request/tenant |
| Multi-database comparison | One `dj.Instance()` per database |
| Parallel workers | `dj.Instance()` per worker + `DJ_THREAD_SAFE=true` |
| Test suite | `dj.Instance()` per test for isolation |
| Shared notebook server | `dj.Instance()` per user session |

## Comparison: Global vs Instance

### Global Pattern (unchanged)

```python
import datajoint as dj

# Config set via environment, files, or programmatically
dj.config["database.host"] = "localhost"

schema = dj.Schema("my_db")

@schema
class MyTable(dj.Manual):
    definition = """
    id : int32
    ---
    value : float64
    """
```

### Instance Pattern (new in 2.2)

```python
import datajoint as dj

inst = dj.Instance(host="localhost", user="root", password="secret")
schema = inst.Schema("my_db")

@schema
class MyTable(dj.Manual):
    definition = """
    id : int32
    ---
    value : float64
    """
```

Once a Schema is created, table definitions, inserts, queries, and all other operations work identically regardless of which pattern was used to create the Schema.

## See Also

- [Use Isolated Instances](../how-to/use-instances.md/) — Task-oriented guide
- [Working with Instances](../tutorials/advanced/instances.ipynb/) — Step-by-step tutorial
- [Configuration Reference](../reference/configuration.md/) — Thread-safe mode settings
- [Configure Database](../how-to/configure-database.md/) — Connection setup
