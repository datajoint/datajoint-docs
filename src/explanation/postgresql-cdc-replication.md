# PostgreSQL CDC and Replica Identity

This page explains how DataJoint integrates with **change-data-capture (CDC)** consumers on PostgreSQL — what `REPLICA IDENTITY` is, why some CDC tools require `FULL`, and how to configure a DataJoint schema for downstream replication.

For the normative API specification, see [Deployment Operations](../reference/specs/deploy-operations.md).

## What is REPLICA IDENTITY?

PostgreSQL records every data change in its write-ahead log (WAL). When a row is `UPDATE`d or `DELETE`d, the **old version** of the row must be representable in WAL so logical replication consumers can identify which row changed. `REPLICA IDENTITY` is a per-table setting that controls how much of the old row is logged:

| Setting | Old row contents logged | WAL cost on UPDATE/DELETE |
|---|---|---|
| `DEFAULT` | Primary-key columns only | Minimal |
| `FULL` | Entire old row, all columns | Higher (proportional to row width, including TOASTed columns) |
| `NOTHING` | Nothing — disables logical replication for the table | n/a |
| `USING INDEX` | Columns of a specified unique index | Between `DEFAULT` and `FULL` |

`INSERT` is unaffected — the full new row is always written to WAL regardless of the setting. Only the **pre-image** (old row state) for updates and deletes is governed by `REPLICA IDENTITY`.

The `ALTER TABLE … REPLICA IDENTITY …` statement is metadata-only and instant: it changes how subsequent updates are logged but does not rewrite any data. Re-applying the same setting is a no-op at the storage layer.

## Why CDC consumers care

Logical replication subscribers — including most CDC pipelines — reconstruct downstream tables (or event streams) from WAL. For deletes and updates, they need enough information about the old row to identify it on the other side. With `REPLICA IDENTITY DEFAULT`, the subscriber gets only the primary key — enough to match the row but **not enough to reconstruct its prior column values**.

Most modern CDC tools work fine with `DEFAULT` when tables have a primary key:

| CDC Tool | `FULL` required? | Notes |
|---|---|---|
| Debezium | No | Recommends `DEFAULT` for performance |
| Azure CDC | No | Recommends against `FULL` |
| ClickHouse ClickPipes | No | `DEFAULT` is fine when PK exists |
| **Databricks Lakehouse Sync** | **Yes** | Tables without `FULL` are silently skipped — the table is not replicated, with no error |

Databricks Lakehouse Sync is the load-bearing case. It needs the full pre-image to drive Slowly-Changing-Dimension (SCD Type 2) history downstream, and tables that lack `REPLICA IDENTITY FULL` are dropped from the sync entirely. There is no error or warning at sync time; the table simply does not appear in the destination. This silent-failure mode is what motivates DataJoint's first-class deploy helper.

## Cost considerations

The `ALTER` itself is free. The cost lives in subsequent WAL volume on `UPDATE` and `DELETE`. Under `FULL`, every modified row writes its **entire prior contents** to WAL — including any TOASTed `bytea` columns that were unchanged by the operation.

For DataJoint's workload, this is usually negligible:

- **Inserts are unaffected.** DataJoint pipelines are insert-append dominated; this is the common case.
- **Updates are rare and surgical.** `update1()` is intended for occasional metadata corrections, not bulk modification.
- **The notable scenario is bulk delete on tables with `<blob>` columns.** A delete of *N* rows × *B*-byte blobs writes ≈ *N × B* bytes of WAL. For a delete of 100 rows × 10 MB blobs, that's a ~1 GB WAL burst — transient (cleared at the next checkpoint) but real.

The cost is bounded by what you actually update or delete, not by table size at rest. For pipelines that rarely modify data after insert, `FULL` is effectively free.

## Compliance considerations

Under `DEFAULT`, only primary-key values appear in WAL — so even if WAL is exposed to a wider audience than the database itself, sensitive non-key columns don't leak through replication channels.

Under `FULL`, the entire row appears in WAL — including any column that may carry PHI, PII, or otherwise sensitive data. Whether this matters depends on **who can read WAL**:

| Environment | WAL access | Practical risk of `FULL` |
|---|---|---|
| Self-hosted PostgreSQL | Filesystem access + logical-replication subscribers can read WAL | Real — treat as sensitive surface |
| Managed PostgreSQL (RDS, Lakebase) with logical replication to a single trusted subscriber | WAL stays inside the managed environment | Bounded to the subscriber's security boundary |

`FULL` should be applied **intentionally**, not by default, on tables that hold sensitive columns. DataJoint does not enable it automatically — the `set_replica_identity` helper is explicitly opt-in.

## How DataJoint integrates this

`REPLICA IDENTITY` is a **deployment-environment concern**: two installs of the same DataJoint pipeline can legitimately want different settings (one for CDC, one not). It is not part of the schema definition — declaring a table does not commit to a replica-identity mode.

The integration is a single function in the `datajoint.deploy` module: `set_replica_identity(target, mode, dry_run)`. It applies the ALTER across a Schema or a single Table, supports a dry-run preview, and raises a clear error on non-PostgreSQL backends.

A representative workflow for adding a Databricks Lakehouse Sync consumer to an existing pipeline:

```python
import datajoint as dj
from datajoint import deploy

schema = dj.Schema("acquisition")
schema.activate()  # existing pipeline; tables already declared

# Preview what would change.
plan = deploy.set_replica_identity(schema, mode="full", dry_run=True)
print(f"Would alter {plan['tables_analyzed']} tables:")
for ddl in plan["ddl"]:
    print(" ", ddl)

# Apply.
deploy.set_replica_identity(schema, mode="full", dry_run=False)
```

Because the operation is idempotent — re-applying the same mode is a no-op at the storage layer — a CI/CD pipeline can include it in the deploy hook for every release without accumulating side effects. New tables added in a future release pick up the setting on the next deploy.

To revert (for example, to reduce WAL volume after a CDC consumer is decommissioned):

```python
deploy.set_replica_identity(schema, mode="default", dry_run=False)
```

`set_replica_identity` is PostgreSQL-only by design — there is no MySQL equivalent of `REPLICA IDENTITY`, since MySQL's binlog-based CDC follows different mechanics. Calling it against a MySQL connection raises `DataJointError` rather than warning quietly.

## Related

- Specification: [Deployment Operations](../reference/specs/deploy-operations.md) — normative API
- PostgreSQL: [Logical Replication — Replica Identity](https://www.postgresql.org/docs/current/logical-replication-publication.html)
- Databricks: [Lakehouse Sync](https://docs.databricks.com/aws/en/oltp/projects/lakehouse-sync)
