# What's New in DataJoint 2.3

DataJoint 2.3 introduces the **provenance trinity** — `Diagram.trace`, `self.upstream`, and `strict_provenance` — which together turn "a computed row can be traced to the exact upstream rows it came from" from a convention into something the framework helps construct and check. It also ships the **SparkAdapter Codec Protocol** for typed rendering to Spark-native types, **`dj.deploy.set_replica_identity`** for PostgreSQL change-data-capture, and a **cascade fix** for Part-of-Part and renamed-foreign-key chains.

> **Upgrading from 2.0, 2.1, or 2.2?** No breaking changes. Everything here is additive, and `strict_provenance` defaults to off — existing pipelines run identically.

> **Citation:** Yatsenko D, Nguyen TT. *DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows.* arXiv:2602.16585. 2026. [doi:10.48550/arXiv.2602.16585](https://doi.org/10.48550/arXiv.2602.16585)

## Overview

DataJoint's provenance model rests on the convention that `make(self, key)` reads only from declared upstream dependencies and writes only to `self` (and its Parts). The framework has always *defined* this boundary but never *checked* it: a `make()` could `fetch()` from any table, making the dependency invisible to the foreign-key graph and silently breaking the provenance claim downstream.

The 2.3 trinity closes that loop with three pieces designed as a unit:

1. **`Diagram.trace()`** constructs the upstream view as a first-class query object.
2. **`self.upstream`** exposes that view ergonomically inside `make()`.
3. **`strict_provenance`** checks (best-effort) that nothing else is read or written.

## The Provenance Trinity

### `Diagram.trace()` — the upstream mirror of `cascade`

`Diagram.cascade()` walks **downstream** and answers *"what is affected if these rows are deleted?"* `Diagram.trace()` walks **upstream** and answers *"what contributed to these rows?"* — reusing the same dependency graph and (inverted) propagation rules.

```python
key = {"subject_id": 1, "session_id": 5, "scan_id": 2}
trace = dj.Diagram.trace(Summary & key)

trace[Session].fetch1("session_date")   # ancestor, pre-restricted to what fed this Summary
trace[Scan].fetch1("scan_id")

trace.counts()   # per-table row counts under the seed's restriction, keyed by full table name
```

`trace[T]` returns the ancestor pre-restricted through the FK join path (a `FreeTable`, so every query operator and the fetch API apply). Renamed foreign keys are reversed automatically, and convergence is **OR** — an ancestor is included if it's reachable through *any* FK path. Requesting a table that isn't an ancestor raises `DataJointError`.

### `self.upstream` — pre-restricted ancestor access inside `make()`

Before each `make()` call, the framework sets `self.upstream = Diagram.trace(self & key)`. Indexing it gives you each declared ancestor already restricted to the rows that contributed to the current `key` — no boilerplate:

```python
class Spectrum(dj.Computed):
    definition = "-> Recording"

    def make(self, key):
        rate = self.upstream[Recording].fetch1("sampling_rate")
        samples = self.upstream[Recording].to_arrays("signal")
        self.insert1({**key, "spectrum": compute_spectrum(samples, rate)})
```

Construction is lazy — the SQL fires only when you access an ancestor and fetch. Outside `make()`, accessing `self.upstream` raises a clear error. Even without `strict_provenance`, it's a pure ergonomic win over `(Recording & key).fetch1(...)`.

### `strict_provenance` — an opt-in runtime guardrail

Setting the flag makes the provenance boundary checked at runtime:

```python
dj.config["strict_provenance"] = True
```

When enabled, inside a `make()`:

- **Reads** of tables outside the declared-ancestor set (plus `self` and its Parts) raise `DataJointError`.
- **Writes** to anything other than `self` and its Parts raise `DataJointError`.
- **Key consistency** is checked: rows inserted into `self`/Parts must carry primary-key values consistent with the current `key`.

`strict_provenance` is an **operational** flag — a property of how a deployment runs, not of the schema. It's a **best-effort development guardrail**, not an airtight boundary: it observes access through the DataJoint Python client and is designed to surface *accidental* undeclared dependencies (turn it on in staging, fix what it flags). Comprehensive enforcement across every access path is handled on the DataJoint platform, which combines these runtime checks with agentic review of `make()` source in its code-deployment CI/CD. See the [Provenance Specification](../reference/specs/provenance.md) for the exact enforcement model and its documented limits.

### Adopting the trinity incrementally

1. Upgrade to 2.3 — the APIs are available; `strict_provenance` stays off.
2. Use `self.upstream` in new `make()` implementations.
3. Migrate existing `make()` reads from `(Upstream & key).fetch(...)` to `self.upstream[Upstream].fetch(...)`.
4. Enable `strict_provenance=True` in staging and fix the undeclared dependencies it surfaces.
5. Enable in production.

## SparkAdapter Codec Protocol

DataJoint's `<blob@>` codec stores arbitrary Python values as serialized binary — general, but opaque to consumers that need typed access at query time (Spark SQL, Delta Sharing, BI tools). The **SparkAdapter** Protocol is the minimum framework-side contract that lets a codec declare its decoded values can be expressed as Spark-native types (primitives, lists, dicts, and nested combinations):

- It's a small, opt-in `@runtime_checkable` `Protocol` — no inheritance, no abstract-method burden on existing codecs.
- Generic codecs (`<blob@>`, `<hash@>`) remain non-adapting by design; typed codecs (`<float_array@>`, `<image_2d@>`, and future shapes) opt in.
- The downstream driver is Databricks Linked Delta Tables (the "silver layer"), where every column must render to a Spark-native type to be queryable.

See the [SparkAdapter Codec Protocol Specification](../reference/specs/spark-adapter.md) and the [explainer](../explanation/spark-adapters.md).

## PostgreSQL CDC: `dj.deploy.set_replica_identity`

2.3 adds a new `datajoint.deploy` module for idempotent, re-runnable operations that configure an existing schema for its deployment environment. Its first member configures PostgreSQL `REPLICA IDENTITY` — required by logical-replication / CDC consumers (e.g., Databricks Lakehouse Sync) that need the full pre-image of updated and deleted rows:

```python
from datajoint import deploy

# Preview
deploy.set_replica_identity(my_schema, mode="full", dry_run=True)
# {'tables_analyzed': 12, 'tables_modified': 0, 'ddl': ['ALTER TABLE "ms"."t1" REPLICA IDENTITY FULL', ...]}

# Apply (schema-wide or a single table)
deploy.set_replica_identity(my_schema, mode="full", dry_run=False)
```

It is PostgreSQL-only (raising a clear error on other backends), idempotent at the storage layer, and deliberately a **deployment concern** rather than a schema-definition one. See the [Deployment Operations Specification](../reference/specs/deploy-operations.md) and [PostgreSQL CDC and Replica Identity](../explanation/postgresql-cdc-replication.md).

## Cascade Fix: Part-of-Part and Renamed-FK Chains

`part_integrity="cascade"` now correctly propagates a Part's restriction up to its Master through **renamed foreign keys** and **Part-of-Part chains**, and materializes the master restriction to avoid MySQL's self-referential-subquery error (1093) on the subsequent downstream cascade. This is the same upward-propagation machinery that `Diagram.trace` builds on. See the [Cascade Specification](../reference/specs/cascade.md).

## Other Fixes

- **`~lineage` self-heals** — missing `~lineage` rows are detected and repaired on every `@schema` decoration.
- **Staged inserts** — object metadata shape now converges with `ObjectCodec.encode`.
- **Garbage collection** — the docs now note that GC is single-pass and best-effort; see [Clean Up Object Storage](../how-to/garbage-collection.md).

## See Also

- [Provenance Specification](../reference/specs/provenance.md) — `trace`, `self.upstream`, and `strict_provenance` in full
- [SparkAdapter Codec Protocol](../reference/specs/spark-adapter.md) — typed rendering to Spark-native types
- [Deployment Operations](../reference/specs/deploy-operations.md) — the `dj.deploy` module
- [Cascade Specification](../reference/specs/cascade.md) — propagation rules shared with `trace`
- [What's New in 2.2](whats-new-22.md) — Previous release
- [Release Notes (v2.3.0)](https://github.com/datajoint/datajoint-python/releases) — GitHub changelog
