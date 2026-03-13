# What's New in DataJoint 2.2

DataJoint 2.2 introduces **isolated instances** and **thread-safe mode** for applications that need multiple independent database connections, and **graph-driven diagram operations** that replace the legacy error-driven cascade with a reliable, inspectable approach for all users.

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

## Graph-Driven Diagram Operations

DataJoint 2.2 promotes `dj.Diagram` from a visualization tool to an operational component. The same dependency graph that renders pipeline diagrams now powers cascade delete, table drop, and data subsetting.

### From Visualization to Operations

In prior versions, `dj.Diagram` existed solely for visualization — drawing the dependency graph as SVG or Mermaid output. The cascade logic inside `Table.delete()` traversed dependencies independently using an error-driven approach: attempt `DELETE` on the parent, catch the foreign key integrity error, parse the error message to discover which child table is blocking, then recursively delete from that child first. This had several problems:

- **MySQL 8 with limited privileges** returns error 1217 (`ROW_IS_REFERENCED`) instead of 1451 (`ROW_IS_REFERENCED_2`), which provides no table name — the cascade crashes with no way to proceed.
- **PostgreSQL** aborts the entire transaction on any error, requiring `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` round-trips for each failed delete attempt.
- **Fragile error parsing** across MySQL versions and privilege levels, where different configurations produce different error message formats.

In 2.2, `Table.delete()` and `Table.drop()` use `dj.Diagram` internally to compute the dependency graph and walk it in reverse topological order — deleting leaves first, with no trial-and-error needed. The user-facing behavior of `Table.delete()` is unchanged. The Diagram's `cascade()` and `preview()` methods are available as a public inspection API for understanding cascade impact before executing.

### The Preview-Then-Execute Pattern

The key benefit of the diagram-level API is the ability to build a cascade explicitly, inspect it, and then execute via `Table.delete()`:

```python
# Build the dependency graph and inspect the cascade
diag = dj.Diagram(schema)
restricted = diag.cascade(Session & {'subject_id': 'M001'})

# Inspect: what tables and how many rows would be affected?
counts = restricted.preview()
# {'`lab`.`session`': 3, '`lab`.`trial`': 45, '`lab`.`processed_data`': 45}

# Execute via Table.delete() after reviewing the blast radius
(Session & {'subject_id': 'M001'}).delete(prompt=False)
```

This is valuable when working with unfamiliar pipelines, large datasets, or multi-schema dependencies where the cascade impact is not immediately obvious.

### Two Propagation Modes

The diagram supports two restriction propagation modes designed for fundamentally different tasks.

**`cascade()` prepares a delete.** It takes a single restricted table expression, propagates the restriction downstream through all descendants, and **trims the diagram** to the resulting subgraph — ancestors and unrelated tables are removed entirely. Convergence uses OR: a descendant row is marked for deletion if *any* ancestor path reaches it, because if any reason exists to remove a row, it should be removed. `cascade()` is one-shot and is always followed by `preview()` or `delete()`.

When the cascade encounters a part table whose master is not yet included in the cascade, the behavior depends on the `part_integrity` setting. With `"enforce"` (the default), `delete()` raises an error if part rows would be deleted without their master — preventing orphaned master rows. With `"cascade"`, the restriction propagates *upward* from the part to its master: the restricted part rows identify which master rows are affected, those masters receive a restriction, and that restriction then propagates back downstream to all sibling parts — deleting the entire compositional unit, not just the originally matched part rows.

**`restrict()` selects a data subset.** It propagates a restriction downstream but **preserves the full diagram**, allowing `restrict()` to be called again from a different seed table. This makes it possible to build up multi-condition subsets incrementally — for example, restricting by species from one table and by date from another. Convergence uses AND: a descendant row is included only if *all* restricted ancestors match, because an export should contain only rows satisfying every condition. After chaining restrictions, use `prune()` to remove empty tables and `preview()` to inspect the result.

The two modes are mutually exclusive on the same diagram — DataJoint raises an error if you attempt to mix `cascade()` and `restrict()`, or if you call `cascade()` more than once. This prevents accidental mixing of incompatible semantics: a delete diagram should never be reused for subsetting, and vice versa.

### Pruning Empty Tables

After applying restrictions, some tables in the diagram may have zero matching rows. The `prune()` method removes these tables from the diagram, leaving only the subgraph with actual data:

```python
export = (dj.Diagram(schema)
    .restrict(Subject & {'species': 'mouse'})
    .restrict(Session & 'session_date > "2024-01-01"')
    .prune())

export.preview()   # only tables with matching rows
export             # visualize the export subgraph
```

Without prior restrictions, `prune()` removes physically empty tables. This is useful for understanding which parts of a pipeline are populated.

### Architecture

`Table.delete()` constructs a `Diagram` internally, calls `cascade()` to compute the affected subgraph, then executes the delete itself in reverse topological order. The Diagram is purely a graph computation and inspection tool — it computes the cascade and provides `preview()`, but all mutation logic (transactions, SQL execution, prompts) lives in `Table.delete()` and `Table.drop()`.

### Advantages over Error-Driven Cascade

The graph-driven approach resolves every known limitation of the prior error-driven cascade:

| Scenario | Error-driven (prior) | Graph-driven (2.2) |
|---|---|---|
| MySQL 8 + limited privileges | Crashes (error 1217, no table name) | Works — no error parsing needed |
| PostgreSQL | Savepoint overhead per attempt | No errors triggered |
| Multiple FKs to same child | One-at-a-time via retry loop | All paths resolved upfront |
| Part integrity enforcement | Post-hoc check after delete | Data-driven post-check (no false positives) |
| Unloaded schemas | Crash with opaque error | Clear error: "activate schema X" |
| Reusability | Delete-only | Delete, drop, export, prune |
| Inspectability | Opaque recursive cascade | `preview()` / `dry_run` before executing |

## See Also

- [Use Isolated Instances](../how-to/use-instances.md) — Task-oriented guide
- [Working with Instances](../tutorials/advanced/instances.ipynb) — Step-by-step tutorial
- [Configuration Reference](../reference/configuration.md) — Thread-safe mode settings
- [Configure Database](../how-to/configure-database.md) — Connection setup
- [Diagram Specification](../reference/specs/diagram.md) — Full reference for diagram operations
- [Delete Data](../how-to/delete-data.md) — Task-oriented delete guide
