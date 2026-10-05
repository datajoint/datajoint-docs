# What's New in DataJoint Library 2.3

DataJoint 2.3 adds a first-class **upstream read surface** — `Diagram.trace` and `self.upstream` — which make "a computed row derives only from its declared upstream inputs" easy to follow inside `make()` and easy to query afterward. It also ships the **SparkAdapter Codec Protocol** for typed rendering to Spark-native types, **`dj.deploy.set_replica_identity`** for PostgreSQL change-data-capture, and a **cascade fix** for Part-of-Part and renamed-foreign-key chains.

Later releases on the line added **redesigned diagram rendering** on the DataJoint brand palette, with a light/dark [`display.diagram_theme`](../reference/configuration.md#display-settings) setting, **S3 stores that resolve an ambient AWS identity** instead of requiring static keys, and **extrinsic provenance at the pipeline's entry points** — a hidden `_prov` attribute the framework records on every row arriving from outside.

> **Upgrading from 2.0, 2.1, or 2.2?** No API breaks — every feature on the 2.3 line is additive.
> Two fixes in 2.3.3 do, however, reject input that previously passed silently: a misspelled native
> type is now caught at declaration, and inserting a NumPy array into a **native** `blob` attribute
> now raises. Both cases were already broken — the first produced invalid DDL at the server, the
> second stored the array's text representation — so anything affected was losing data rather than
> working. See [Changes in 2.3.3](#changes-in-233).

> **Citation:** Yatsenko D, Nguyen TT. *DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows.* arXiv:2602.16585. 2026. [doi:10.48550/arXiv.2602.16585](https://doi.org/10.48550/arXiv.2602.16585)

## Changes in 2.3.4

2.3.4 is a patch release on the 2.3 line. If you are upgrading from **2.3.3**:

- **Rows that enter the pipeline record where they came from.** A `Manual` table can carry a hidden `_prov` attribute, declared when a deployment enables `provenance.capture` and filled on insert. Inside a pipeline provenance is structural — a computed row cannot exist without its declared upstream, so the foreign-key graph is the lineage — but at the boundary that runs out, and until now each pipeline invented its own record of external origin. `_prov` gives the boundary one shape, so that "which rows have no recorded origin" is a query rather than an audit. **No author writes it:** `insert()` takes no provenance argument, and the content comes from deployment configuration (`provenance.source`), from the connection (user, host, database, time, code version), and — for an insert running inside a `make()` — from the ingesting table and key. That last source is what makes the [fan-out ingestion pattern](../explanation/fan-out-ingestion.md) traceable without a foreign key. A field the operator can set is weaker evidence than one the system sets, which is the point for an audit; anything an author wants to record deliberately belongs in the data model as a visible attribute, where queries can reach it. A table declared before capture was enabled has no column and records nothing until `dj.deploy.add_prov_column` adds it. See [Extrinsic Provenance at Entry Tables](../reference/specs/boundary-provenance.md), [Record Data Origin](../how-to/record-data-origin.md) and [#1547](https://github.com/datajoint/datajoint-python/issues/1547).
- **New settings: `provenance.capture` and `provenance.source`.** Capture defaults to **off**, like `jobs.add_job_metadata` and for the same reason: it changes the DDL of every `Manual` table declared afterwards, so upgrading to 2.3.4 leaves an unchanged schema declaring exactly what it declared under 2.3.3. `provenance.source` names the external system a process draws from, set per deployment through `DJ_PROVENANCE_SOURCE`, the config file, or the secrets directory rather than in pipeline code. See [Configuration](../reference/configuration.md#provenance-settings).
- **Three tiers gain a second name.** `dj.Entry`, `dj.Ingest` and `dj.Compute` join `dj.Manual`, `dj.Imported` and `dj.Computed`. Each pair is one class rather than a subclass, so a table declared either way is identical — same SQL prefix, same tier detection, same `describe()` and diagram — and both names are permanent, with no deprecation and nothing to migrate. `dj.Lookup` and `dj.Part` are unchanged. The documentation keeps the original names for now; adopting the new ones as primary is slated for 2.4 ([#1546](https://github.com/datajoint/datajoint-python/issues/1546)). See [Relational Workflow Model](../explanation/relational-workflow-model.md) and [#1546](https://github.com/datajoint/datajoint-python/issues/1546).
- **Every platform-managed column goes through the DataJoint type system.** `_job_start_time`, `_job_duration`, `_job_version`, `_prov` and `_singleton` are declared in DataJoint notation and compiled by the same path as a user attribute, so each backend's mapping comes from one place. This fixes two PostgreSQL defects: `_job_start_time` was declared as a bare `timestamp` and so took microsecond precision where MySQL got `datetime(3)` ([#1566](https://github.com/datajoint/datajoint-python/issues/1566)), and `migrate.add_job_metadata_columns` built its `ALTER` with backtick-quoted identifiers, which is a syntax error there — the retrofit had never run on PostgreSQL. Existing tables are untouched; only new declarations and retrofits change. See [#1567](https://github.com/datajoint/datajoint-python/issues/1567).
- **Codecs receive connection context explicitly.** `encode()` and `decode()` now take a `context` argument carrying `schema`, `table`, `field` and `config`, so `key` means what it means everywhere else in DataJoint — the primary key. Passing the calling connection's `config` matters: `_build_path` and `_get_backend` fall back to the global `dj.config` without it, which in a process holding connections for several users belongs to none of them and resolves a different store silently rather than raising. Two third-party codecs hit exactly that, both following the `SchemaCodec` docstring, which is updated here. **Nothing breaks:** DataJoint passes `context` only to codecs whose signature declares it, the pre-2.3.4 underscore keys are still populated in `key`, and `_extract_context(key)` still accepts one argument — it warns only when it falls back to those keys. Codecs written before 2.3.4 keep working unchanged; `key` reverting to primary-key-only, and `config` becoming required, wait for 2.4. See [Custom Codecs](../tutorials/advanced/custom-codecs.ipynb) and [#1550](https://github.com/datajoint/datajoint-python/issues/1550).

## Changes in 2.3.3

2.3.3 is a patch release on the 2.3 line. If you are upgrading from **2.3.2**:

- **S3 stores work without static credentials.** `access_key` and `secret_key` are now optional in an `s3` store spec — omit both and the AWS credential chain resolves an ambient identity (EC2 instance profile, IRSA, ECS task role, SSO), matching how the `gcs` and `azure` protocols already behaved. This is what lets a pipeline run under an assumed role with no long-lived keys in its configuration. Setting exactly one of the two is now rejected at validation with a clear message, rather than failing later inside the AWS client as a partial credential. See [Configure Storage](../how-to/configure-storage.md) and [#1537](https://github.com/datajoint/datajoint-python/issues/1537).
- **Redesigned diagram rendering.** `dj.Diagram` output adopts the DataJoint brand palette: Manual and Lookup stay rectangles, Imported and Computed stay ovals, and each tier now carries its brand fill — Manual green, Lookup grey, Imported blue, Computed orange. Renamed foreign keys render as amber edges. Edge thickness now encodes **cardinality** rather than the master-part relationship, which it conflated before. See [Read Diagrams](../how-to/read-diagrams.ipynb) and [#1532](https://github.com/datajoint/datajoint-python/issues/1532).
- **New setting: `display.diagram_theme`.** Choose `auto` (the default — one SVG that follows the viewer's light or dark mode), `light`, or `dark`. Settable as `dj.config.display.diagram_theme` or via `DJ_DIAGRAM_THEME`. See [Configuration](../reference/configuration.md#display-settings).
- **Diagrams render when a table cannot be resolved.** A diagram containing a node that maps to no Python class — a table declared by another project, or one whose module is not imported — now draws that node with its raw table name instead of raising. This came up on PostgreSQL, where schema qualification made unresolved nodes more common. See [#1535](https://github.com/datajoint/datajoint-python/issues/1535).
- **Braces in comments no longer break declaration.** A `{...}` sequence anywhere in a table or attribute comment — `payload : json  # {data, config} payload` — crashed `declare` with an opaque `KeyError`. Comments and `enum` values now pass through verbatim. The same defect was live on `Table.alter`, which additionally lost the declared type of any attribute it added; a table altered on PostgreSQL could become permanently un-alterable as a result. `alter()` now preserves type metadata, so `describe()` keeps round-tripping, and `ADD`/`DROP` work on PostgreSQL. See [datajoint-python#1548](https://github.com/datajoint/datajoint-python/pull/1548).
- **Attribute types are validated at declaration and insert.** Four related gaps closed. A misspelled native type (`int24`, `intbanana`) is now rejected with `Unsupported attribute type` instead of being passed to the server as invalid DDL. `decimal(M,D) unsigned` is accepted again — it was rejected in 2.x while the equivalent `numeric(M,D) unsigned` passed. A bare `blob` is accepted alongside `tinyblob`/`longblob`. And inserting a NumPy array into a **native** `blob` attribute now raises instead of silently storing the array's text representation; use a `<blob>` codec attribute to store arrays. See [#1527](https://github.com/datajoint/datajoint-python/issues/1527), [#1528](https://github.com/datajoint/datajoint-python/issues/1528), [#1529](https://github.com/datajoint/datajoint-python/issues/1529) and [#1530](https://github.com/datajoint/datajoint-python/issues/1530).
- **File-protocol stores are safe on Windows.** Paths in `file://` store URLs are now built with POSIX separators on every platform. Previously a Windows backslash in a stored path did not match the forward-slash form used during reference discovery, so `gc.collect()` could classify live files as orphans and delete them. Windows is now covered by CI. See [Clean Up Object Storage](../how-to/garbage-collection.md) and [#1520](https://github.com/datajoint/datajoint-python/issues/1520).
- **Foreign-key columns are indexed on PostgreSQL.** Table declaration emitted an index for unique foreign keys only, leaving ordinary ones unindexed and making joins and cascading deletes scan. Non-unique foreign-key columns are now indexed, skipping any already covered by an existing index. Existing tables are unaffected until redeclared. See [#1512](https://github.com/datajoint/datajoint-python/issues/1512).
- **Custom codecs must resolve stores against the calling connection.** The `SchemaCodec` example previously omitted `config=` when calling `_build_path` and `_get_backend`, so a codec written from it resolved its store against the module-level `dj.config` rather than the connection actually in use — reading the wrong store, or failing validation, in any process holding more than one connection. The example now threads `key["_config"]` through both, as the built-in `object` and `npy` codecs already did. If you maintain a codec, check both call sites. This threading is scheduled to be replaced by an explicit `context=` parameter in 2.3.4 — see [#1550](https://github.com/datajoint/datajoint-python/issues/1550) — so the underscore key will keep working with a deprecation warning rather than changing under you. See [Custom Codecs](../tutorials/advanced/custom-codecs.ipynb).

## Changes in 2.3.2

2.3.2 is a patch release on the 2.3 line. If you are upgrading from **2.3.1**:

- **Uncaught exceptions show full tracebacks again.** Importing `datajoint` no longer installs a process-wide `sys.excepthook`. Previously any uncaught exception in the process — DataJoint-related or not — was reduced to a single opaque `[ERROR]: Uncaught exception` line with no type, message, or traceback; now Python's default handler prints the full traceback to stderr. The log formatter also renders exception and stack info correctly. See [#1516](https://github.com/datajoint/datajoint-python/issues/1516).
- **`populate(reserve_jobs=True)` works with `uuid`-derived primary keys.** Auto-populating a `Computed`/`Imported` table whose primary key derives from a `uuid` attribute no longer crashes with `Unsupported attribute type binary(16)` when its jobs table is first created. See [#1515](https://github.com/datajoint/datajoint-python/issues/1515).
- **Safer garbage collection.** `gc.collect()` no longer acts on a partial store listing, closing a path where an interrupted or incomplete storage enumeration could misclassify live files as orphans. See [Clean Up Object Storage](../how-to/garbage-collection.md).
- **Clearer diagram notation for renamed foreign keys.** A renamed (aliased) foreign key now renders as a distinctly colored **orange edge** — with a hover tooltip listing the renamed columns (e.g. `spouse1 ← person_id`) — instead of the small orange **alias dot** used previously. Orange layers on top of the existing line styles (solid/dashed for primary/secondary, thick for one-to-one), so the foreign-key kind stays legible. Internally the dependency graph is now an `nx.MultiDiGraph` with parallel edges rather than alias nodes; behavior is unchanged. See [Read Diagrams](../how-to/read-diagrams.ipynb).
- **Version derived from the release tag.** The package version now comes from the git tag (via `hatch-vcs`), so a git install of a tagged commit (`pip install "git+https://github.com/datajoint/datajoint-python.git@v2.3.2"`) and `pip show datajoint` both report `2.3.2` — previously such an install could report the prior release. Running from an uninstalled source tree now reports `0.0.0+unknown`; use `pip install -e .` for development.

## Changes in 2.3.1

2.3.1 is a patch release on the 2.3 line. If you are upgrading from **2.3.0**:

- **`strict_provenance` removed.** The opt-in `dj.config["strict_provenance"]` runtime guardrail that shipped in 2.3.0 has been retired. Comprehensively checking the `make()` read/write contract across every access path is a code-inspection problem rather than a runtime one, so it is validated at review or deploy time rather than by an in-process flag. The flag was off by default with no known adoption, so existing pipelines are unaffected. The ergonomic read surface — `Diagram.trace` and `self.upstream` — is unchanged, and the rules are documented as the [make() reproducibility contract](../reference/specs/autopopulate.md#43-the-make-reproducibility-contract).
- **Python 3.14 support.** `requires-python` now spans `>=3.10,<3.15`; CI exercises both ends of the range (3.10 and 3.14).
- **Cascade multi-part-master fix.** `Table.delete(part_integrity="cascade")` now restricts the master from *every* restricted Part, closing a silent-integrity path where two Parts of the same Master reached through different foreign-key paths could leave the Master with rows that should have been deleted. See [Cascade Specification](../reference/specs/cascade.md).
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

## Redesigned Diagrams

`dj.Diagram` output was restyled onto the DataJoint brand palette, and one notation rule that
had been conflating two different things was corrected.

**Tier is shape *and* color.** Manual and Lookup are rectangles, Imported and Computed are
ovals — unchanged — and each tier now carries its brand fill: Manual green, Lookup grey,
Imported blue, Computed orange. A Part keeps a neutral box rather than its master's tier shape,
so it stays a distinct, selectable node.

**Line weight now encodes cardinality, and only cardinality.** It is binary: a **thick** edge is
a one-to-one dependency, where the foreign key fills the child's entire primary key; a **thin**
edge is one-to-many, where the child adds primary-key attributes of its own. Previously weight
also tried to signal the master-part relationship, which made the two unreadable together. The
rule is rename-safe — what matters is whether the foreign key covers the child's whole primary
key, not whether the attribute names match, so a renamed foreign key can still be one-to-one.

**Renamed foreign keys are amber.** A renamed (aliased) foreign key is drawn in amber `#C77D3A`
— distinct from the orange Computed tier — layered on top of the ordinary line styles, so
solid/dashed and thick/thin still read normally. Hover the edge in the SVG for the column
renames (e.g. `spouse1 ← person_id`).

**Themes.** The new `display.diagram_theme` setting takes `auto`, `light`, or `dark`:

```python
dj.config.display.diagram_theme = "dark"

# or per-diagram
with dj.config.override(display__diagram_theme="light"):
    dj.Diagram(schema)
```

`auto` — the default — emits a **single** SVG that adapts to the viewer's light or dark mode
through an embedded `prefers-color-scheme` block, so the same file works in both. It also reads
`DJ_DIAGRAM_THEME`.

Diagrams no longer fail on a node they cannot resolve to a Python class — a table declared by
another project, or one whose module is not imported, is drawn with its raw table name instead
of raising.

See [Read Diagrams](../how-to/read-diagrams.ipynb) for the full notation and the
[Diagram Specification](../reference/specs/diagram.md) for the exact palette and rules.

## Other Fixes

- **`~lineage` self-heals** — missing `~lineage` rows are detected and repaired on every `@schema` decoration.
- **Staged inserts** — object metadata shape now converges with `ObjectCodec.encode`.
- **Garbage collection** — the docs now note that GC is single-pass and best-effort; see [Clean Up Object Storage](../how-to/garbage-collection.md).

## See Also

- [Upstream Trace Specification](../reference/specs/trace.md) — `Diagram.trace` and `self.upstream` in full
- [SparkAdapter Codec Protocol](../reference/specs/spark-adapter.md) — typed rendering to Spark-native types
- [Deployment Operations](../reference/specs/deploy-operations.md) — the `dj.deploy` module
- [Cascade Specification](../reference/specs/cascade.md) — propagation rules shared with `trace`
- [Read Diagrams](../how-to/read-diagrams.ipynb) — diagram notation, tiers, edges and themes
- [Diagram Specification](../reference/specs/diagram.md) — the brand palette and the cardinality rule
- [What's New in 2.2](whats-new-22.md) — Previous release
- [Release Notes (2.3.x)](https://github.com/datajoint/datajoint-python/releases) — GitHub changelog
