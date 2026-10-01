# Extrinsic Provenance at Entry Tables

## Overview

Rows that enter a pipeline from outside carry a hidden `_prov` attribute recording where they came from. The framework declares the attribute on Manual tables and fills it on insert; no author writes it.

!!! version-added "New in 2.3.4"

    `dj.Entry` is available from 2.3.4 as a permanent alias for `dj.Manual`. This page uses `dj.Manual` throughout; both names declare the same table.

## Motivation

Inside a pipeline, provenance is **structural**. A Computed table's row cannot exist unless its declared upstream exists and is correct, so the foreign-key graph *is* the lineage. Nothing has to be recorded for that to hold.

At the boundary the structure runs out. Rows arrive in Manual tables from a person, an instrument, or an automated feed, and the graph has nothing to say about where they came from. Before 2.3.4 each pipeline answered that question its own way — a `source_file` column here, a `notes` varchar there, an ingestion log somewhere else, or nothing at all.

`_prov` gives the boundary one shape, so that two pipelines answer "where did this row come from" the same way, and so that "which rows have no recorded origin" is a query rather than an audit.

## The Attribute

| Attribute | Type | Description |
|-----------|------|-------------|
| `_prov` | `json` (MySQL) / `jsonb` (PostgreSQL) | Extrinsic provenance for a row that entered from outside the pipeline. `NULL` when nothing was recorded. |

Hidden attributes are prefixed with `_`: stored in the database, filtered out of `heading.attributes`, and excluded from query composition.

**Why JSON rather than typed columns.** The useful key set is not settled, and deployments add to it. A JSON document absorbs a new key as a configuration change; typed columns would freeze the set at declaration and make every later addition an `ALTER` across every Manual table in every deployment. Filtering on a field stays portable — see [Querying](#querying).

## Which Tables Carry It

Manual tables only.

| Tier | Carries `_prov` | Why |
|------|-----------------|-----|
| `dj.Manual` | **Yes** | The pipeline's boundary with the outside world |
| `dj.Lookup` | No | Rows come from the committed `contents`, so the code is the record |
| `dj.Imported` | No | See below |
| `dj.Computed` | No | Provenance is entailed by the foreign-key graph |
| `dj.Part` | No | A part inherits its master's |

The slot is granted by matching the Manual tier, not by excluding the other
tiers' prefixes, so DataJoint's own system tables — job queues, lineage — never
carry it either.

**Why not Imported.** An Imported table already records agent, time and version through [job metadata](job-metadata.md) when `config.jobs.add_job_metadata` is on, so a `_prov` there would record the same facts twice. The half that is *not* covered — which specific file, endpoint, or instrument session its `make()` read — is known per row inside the `make()` body, which configuration cannot supply.

In a well-modeled pipeline the external source is registered as a Manual row and the Imported table reaches it through a declared foreign key, which makes that table's provenance structural. An Imported table reading a source no Manual row records is the modeling problem described in [Table Declaration](table-declaration.md); the fix is to register the source, not to add a slot.

## Content

Three sources fill the attribute, and **none of them is the insert call site**.

| Source | Supplies |
|---|---|
| Configuration | `config.provenance.source` — the deployment constant naming the external system this process draws from |
| Ambient connection state | the connecting user, host and database; the insert time; the code version |
| Ambient execution state | the ingesting table and key, when the insert runs inside a `make()` |

A recorded document:

```json
{
  "time": "2026-09-30T14:22:05.481203+00:00",
  "agent": {"user": "ingest_svc", "host": "db.example.org", "database_name": "lab_subjects"},
  "version": "a1b2c3d",
  "source": {"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"},
  "context": {"table": "`lab`.`_ingest`", "key": {"file_id": 7}, "version": "a1b2c3d"}
}
```

Keys are omitted when they have nothing to report: `source` when none is configured, `context` outside a `make()`, `version` when `config.jobs.version_method` is disabled. When only `time` would remain the attribute is left `NULL`, because a bare timestamp says nothing about origin.

`time` is the client's UTC clock at insert, not the server's.

### The author cannot write it

`insert()` takes no provenance argument, and passing `_prov` in a row raises `KeyError` — hidden attributes are not in the heading.

This is the design rather than a limitation. A field an operator can set is weaker evidence than one the system sets, which is what *attributable* and *contemporaneous* require of externally-sourced data. It also removes the failure mode a supported-but-optional field would have: there is nothing left for a pipeline to neglect.

**Anything an author wants to record deliberately belongs in the data model**, as an ordinary visible attribute. Pipeline code can restrict and join on a modeled column; it cannot on a hidden one. The two do different jobs — `_prov` is the audit record, a modeled column is the domain link. See [Fan-Out Ingestion](../../explanation/fan-out-ingestion.md), where both appear side by side.

## Configuration

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `provenance.capture` | `DJ_PROVENANCE_CAPTURE` | `True` | Declare `_prov` on Manual tables and fill it on insert |
| `provenance.source` | `DJ_PROVENANCE_SOURCE` | `{}` | External source identity recorded on every row this process enters |

```python
import datajoint as dj

dj.config.provenance.capture          # True
dj.config.provenance.source = {"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"}
```

Deployments set these where they set stores and credentials, not in pipeline code:

```bash
export DJ_PROVENANCE_SOURCE='{"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"}'
```

```json
{
    "provenance": {
        "source": {"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"}
    }
}
```

!!! warning "Changing the source mid-process is silent"

    Rows inserted before the change keep what was configured then, and rows after keep the new value. Nothing records that the setting moved. Set it once at start-up.

### Capture defaults on

A slot that is absent on most tables is a slot nobody codes against. With capture off by default, no consumer could assume the column exists, and "which rows have no recorded origin" would be conditional on each table's declaration-time configuration rather than a query.

Stated plainly: a Manual table declared under 2.3.4 differs in DDL from one declared under 2.3.3. The difference is one hidden nullable column.

## Behavior

### At declaration

With `provenance.capture` true, `_prov` is added to the `CREATE TABLE` of every Manual table that is not a part. Turning capture off later does not remove the column from tables that already have it.

### At insert

Every `insert()` and `insert1()` into a Manual table that carries the column appends the assembled document. A table declared without the column is left alone and the insert succeeds — silently, which is what [retrofitting](#retrofitting-existing-tables) addresses.

### Inside `make()`

An insert executed inside a `make()` records the ingesting table and key in `context`. This is what makes the [fan-out ingestion pattern](../../explanation/fan-out-ingestion.md) traceable: rows written into Manual tables that carry no foreign key back to the loader still record what wrote them.

## Retrofitting Existing Tables

Tables declared before 2.3.4, or while capture was off, have no column and record nothing. `datajoint.deploy.add_prov_column` adds the slot:

```python
from datajoint.deploy import add_prov_column

# Preview
add_prov_column(schema, dry_run=True)["ddl"]

# Apply to every Manual table in a schema
add_prov_column(schema, dry_run=False)

# Or a single table
add_prov_column(Subject, dry_run=False)
```

It is idempotent — a table that already has the column is reported and left alone — and it lives in `datajoint.deploy` rather than `datajoint.migrate` for that reason.

Rows already present keep `NULL`. Provenance is recorded at insert and is never reconstructed after the fact.

## Querying

`_prov` is excluded from `heading.attributes`, so it does not appear in `to_dicts()`, in `describe()`, or in a join.

**Restricting** on it works, written as a SQL condition string:

```python
# Rows with no recorded origin
Subject & "_prov IS NULL"

# Rows from a particular external system (MySQL)
Subject & "JSON_VALUE(_prov, '$.source.system') = 'PyRat'"
```

!!! warning "The mapping form does not reach a hidden attribute"

    `Subject & {"_prov.system": "PyRat"}` returns **every row**. A mapping
    restriction ignores attributes it cannot match, which is deliberate and
    useful — it is what lets `Session & key` work when `key` carries attributes
    from a more detailed table. A hidden attribute is invisible to that matching,
    so the predicate is dropped along with it.

    Write the condition as a string, which reaches the column directly. Tracked in
    [datajoint-python#1561](https://github.com/datajoint/datajoint-python/issues/1561).

**Reading the value back requires SQL** until 2.4. There is no public API that
returns a hidden attribute — `to_arrays('_prov')` and `proj('_prov')` both raise:

```python
# Until 2.4
rows = Subject.connection.query(
    f"SELECT subject_id, _prov FROM {Subject.full_table_name}"
).fetchall()
```

A supported accessor is planned for 2.4
([datajoint-python#1562](https://github.com/datajoint/datajoint-python/issues/1562)),
which will cover `_prov` and the job-metadata attributes together.

!!! note "Range queries on capture time"

    Filtering by `time` goes through JSON extraction, so it does not use an index. If that becomes hot for a deployment, add a generated column over the JSON path and index it; no change to the pipeline or to DataJoint is needed.

## Implementation Details

| Module | Role |
|--------|------|
| `datajoint/provenance.py` | payload assembly, tier test, the ingesting context |
| `datajoint/settings.py` | `ProvenanceSettings`, exposed as `config.provenance` |
| `datajoint/declare.py` | adds the column to Manual tables at declaration |
| `datajoint/adapters/` | `provenance_columns()` — `json` on MySQL, `jsonb` on PostgreSQL |
| `datajoint/table.py` | appends the value on the insert path |
| `datajoint/autopopulate.py` | scopes the ingesting context to a `make()` call |
| `datajoint/deploy.py` | `add_prov_column` |

## See Also

- [Hidden Job Metadata](job-metadata.md) — the same hidden-attribute mechanism, for the automated tiers
- [Record Data Origin](../../how-to/record-data-origin.md) — the task-oriented guide
- [Fan-Out Ingestion](../../explanation/fan-out-ingestion.md) — where a loader writes into tables that do not depend on it
- [Comparison to Provenance Systems](../../explanation/comparison-to-provenance-systems.md) — what DataJoint records and what it leaves to provenance systems
