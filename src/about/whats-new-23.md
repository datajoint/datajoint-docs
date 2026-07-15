# What's New in DataJoint 2.3

DataJoint 2.3 adds a first-class **upstream read surface** — `Diagram.trace` and `self.upstream` — which make "a computed row derives only from its declared upstream inputs" easy to follow inside `make()` and easy to query afterward. It also ships the **SparkAdapter Codec Protocol** for typed rendering to Spark-native types, **`dj.deploy.set_replica_identity`** for PostgreSQL change-data-capture, and a **cascade fix** for Part-of-Part and renamed-foreign-key chains.

> **Upgrading from 2.0, 2.1, or 2.2?** No breaking changes. Everything here is additive — existing pipelines run identically.

> **Citation:** Yatsenko D, Nguyen TT. *DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows.* arXiv:2602.16585. 2026. [doi:10.48550/arXiv.2602.16585](https://doi.org/10.48550/arXiv.2602.16585)

## Changes in 2.3.1

2.3.1 is a patch release on the 2.3 line. If you are upgrading from **2.3.0**:

- **`strict_provenance` removed.** The opt-in `dj.config["strict_provenance"]` runtime guardrail that shipped in 2.3.0 has been retired. Comprehensively checking the `make()` read/write contract across every access path is a code-inspection problem rather than a runtime one, so it is validated at review or deploy time rather than by an in-process flag. The flag was off by default with no known adoption, so existing pipelines are unaffected. The ergonomic read surface — `Diagram.trace` and `self.upstream` — is unchanged, and the rules are documented as the [make() reproducibility contract](../reference/specs/autopopulate.md#43-the-make-reproducibility-contract).
- **Python 3.14 support.** `requires-python` now spans `>=3.10,<3.15`; CI exercises both ends of the range (3.10 and 3.14).
- **Garbage-collection fix.** `gc.collect()` now discovers codec-referenced files correctly, closing a path where live custom-codec and schema-addressed object-store files (`<object@>`, `<npy@>`) could be misclassified as orphans and deleted. See [Clean Up Object Storage](../how-to/garbage-collection.md).

## Overview

A computed row is reproducible only when `make(self, key)` reads only from its declared upstream dependencies and writes only to `self` (and its Parts). DataJoint 2.3 makes that read/write boundary easy to follow — and the resulting data lineage easy to query — with two features designed as a unit:

1. **`Diagram.trace()`** constructs the upstream view as a first-class query object.
2. **`self.upstream`** exposes that view ergonomically inside `make()`.

## Upstream Trace and `self.upstream`

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

Construction is lazy — the SQL fires only when you access an ancestor and fetch. Outside `make()`, accessing `self.upstream` raises a clear error. It's a pure ergonomic win over `(Recording & key).fetch1(...)`, and it keeps the read inside the declared upstream — which is what makes the result reproducible. See the [make() reproducibility contract](../reference/specs/autopopulate.md#43-the-make-reproducibility-contract) for the full rule set.

### Adopting `self.upstream` incrementally

1. Upgrade to 2.3 — the new APIs are available; existing code is unaffected.
2. Use `self.upstream` in new `make()` implementations.
3. Migrate existing `make()` reads from `(Upstream & key).fetch(...)` to `self.upstream[Upstream].fetch(...)` — no semantic change, but the read is now visibly confined to the declared upstream.

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

- [Upstream Trace Specification](../reference/specs/trace.md) — `Diagram.trace` and `self.upstream` in full
- [SparkAdapter Codec Protocol](../reference/specs/spark-adapter.md) — typed rendering to Spark-native types
- [Deployment Operations](../reference/specs/deploy-operations.md) — the `dj.deploy` module
- [Cascade Specification](../reference/specs/cascade.md) — propagation rules shared with `trace`
- [What's New in 2.2](whats-new-22.md) — Previous release
- [Release Notes (v2.3.0)](https://github.com/datajoint/datajoint-python/releases) — GitHub changelog
