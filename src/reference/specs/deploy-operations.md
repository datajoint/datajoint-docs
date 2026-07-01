# Deployment Operations Specification

This document specifies the `datajoint.deploy` module — idempotent, re-runnable operations that configure an existing schema for its **deployment environment** (CDC tools, replication, role grants, performance tuning).

For one-shot schema-evolution operations (column migrations, lineage repair, retroactive job-metadata columns), see `datajoint.migrate` (referenced in the [Data Manipulation Specification](data-manipulation.md)).

!!! version-added "New in 2.3"
    The `datajoint.deploy` module is introduced in DataJoint 2.3, beginning with `set_replica_identity` for PostgreSQL CDC integration.

## Scope: migration vs. deployment

DataJoint exposes two categories of operational helpers. The distinction is **load-bearing** — applying the wrong one at the wrong time produces inconsistent state.

| | `datajoint.migrate` | `datajoint.deploy` |
|---|---|---|
| **Purpose** | Schema/state evolution, fixing legacy | Configure an environment for a consumer's requirements |
| **Cadence** | One-shot transitions | Idempotent, re-runnable in deploy hooks |
| **Trigger** | Schema definition changed, or repair needed | Environment changes (new CDC consumer, replication topology) |
| **Examples** | `migrate_columns`, `add_job_metadata_columns`, `rebuild_lineage` | `set_replica_identity` |

A deployment operation must be safe to call repeatedly without accumulating side effects: re-running it brings the environment to the same end state and is a no-op when already there.

## `set_replica_identity`

Apply `ALTER TABLE ... REPLICA IDENTITY DEFAULT|FULL` to every user table in a schema, or to a single table, on PostgreSQL.

### Signature

```python
def set_replica_identity(
    target: Schema | Table,
    mode: Literal["default", "full"] = "full",
    dry_run: bool = True,
) -> dict
```

### Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `target` | `Schema` or `Table` (class or instance) | — | Schema (all user tables) or a single table. |
| `mode` | `str` | `"full"` | `"default"` (PK only) or `"full"` (entire old row). |
| `dry_run` | `bool` | `True` | If `True`, collect DDL but do not execute. |

### Return value

A dict:

| Key | Type | Description |
|---|---|---|
| `tables_analyzed` | `int` | Number of tables considered. |
| `tables_modified` | `int` | Tables on which the ALTER ran. `0` when `dry_run=True`. |
| `ddl` | `list[str]` | DDL statements that were (or would be) executed. |

### Errors

| Condition | Behavior |
|---|---|
| Connection's adapter is not PostgreSQL | `DataJointError`: `"set_replica_identity is PostgreSQL-only; …"` |
| `mode` is not `"default"` or `"full"` | `DataJointError`: `"mode must be 'default' or 'full'; …"` |
| `target` is not a `Schema` or `Table` | `DataJointError`: `"target must be a Schema or Table class/instance; …"` |

### Behavior

For each user table in the target (excluding `~`-prefixed hidden tables), the function builds `ALTER TABLE "{schema}"."{table}" REPLICA IDENTITY {MODE}` via the PostgreSQL adapter's `replica_identity_ddl()` and either records it (dry-run) or executes it on the connection.

Both `default` and `full` produce explicit `ALTER` statements. `default` is **not** treated as a no-op — it actively resets the table to PostgreSQL's default, which is the right semantics when reverting from `FULL`.

The underlying ALTER is metadata-only, instant, and idempotent at the PostgreSQL layer (re-applying the same mode is a no-op at the storage layer).

The operation is **not atomic**: tables are altered one at a time, so if execution raises on table _N_ of _M_, the first _N_−1 ALTERs have already committed and the exception propagates without returning a summary — re-run to converge (each ALTER is idempotent).

## Design rationale

Three structural decisions distinguish `dj.deploy` from alternatives that were considered and rejected. Each is informed by the failure modes the alternative would have produced.

### 1. Migration-only, not auto-emit on `declare()`

[Issue #1447](https://github.com/datajoint/datajoint-python/issues/1447) originally proposed two mechanisms — a `database.replica_identity` config flag applied automatically during `declare()`, plus a utility for existing tables. We collapsed to migration-only. Two mechanisms would produce **mixed state**: a deployment with the config set, applied mid-cycle, would have new tables at `FULL` and old tables at `DEFAULT` until someone remembered to run the migration. One mechanism is the only path that converges.

### 2. Not in `dj.migrate`

`dj.migrate` covers one-shot schema-evolution operations: fix lineage, add job-metadata columns, transform external store layouts. `set_replica_identity` is not a one-shot transition — a fresh declare in a staging environment may need it re-applied; deploy hooks may run it on every release. The cadence and trigger differ, and conflating them in one module obscures the difference.

### 3. New module for an emerging category

`set_replica_identity` is the first of a category. Plausible siblings, as needs arise:

- Publication membership for PostgreSQL logical replication (`CREATE PUBLICATION … FOR TABLE …`).
- Maintenance: `vacuum_analyze`, `reindex`, table-level autovacuum parameters.
- Role/grant management for shared environments.

Creating `dj.deploy` now — with one inhabitant — gives those future helpers a clear home and keeps `dj.migrate` focused. The cost is one file; the alternative is an indefinite period of "where do I put this?" for every operational helper.

## Idempotency and re-running

Every function in `datajoint.deploy` must be safe to re-run. `set_replica_identity` satisfies this because:

1. The DDL is generated freshly each call.
2. The PostgreSQL ALTER is metadata-only and applying the same mode again is a no-op at the storage layer.
3. The dry-run path produces a complete preview without executing.

Deploy hooks may call `set_replica_identity(schema, mode="full", dry_run=False)` on every release without accumulating side effects.

## Related

- Explanation: [PostgreSQL CDC and Replica Identity](../../explanation/postgresql-cdc-replication.md)
- Data Manipulation Specification: [Data Manipulation](data-manipulation.md) (insert / update / delete; not deployment-time)
- PostgreSQL: [Logical Replication — Replica Identity](https://www.postgresql.org/docs/current/logical-replication-publication.html)
