# Record Data Origin

Data entering a pipeline from outside carries no dependency that says where it came from. DataJoint records that origin for you on every Manual table, from configuration rather than from your insert code.

!!! version-added "New in 2.3.4"

## Configure the source

Name the external system this process draws from. Set it where you set credentials and stores — not in pipeline code:

```bash
export DJ_PROVENANCE_SOURCE='{"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"}'
```

or in `datajoint.json`:

```json
{
    "provenance": {
        "source": {"system": "PyRat", "endpoint": "https://pyrat.example.org/api/v2"}
    }
}
```

Every row this process inserts into a Manual table now records that source, along with the connecting user and host, the insert time, and the code version.

Nothing else is required. There is no argument to pass and no field to remember:

```python
Subject.insert1({"subject_id": 1, "species": "mouse"})
```

Even when the source offers little — a nightly sync against a colony-management API — recording "received from PyRat at 02:15" beats recording nothing.

## Check that rows are carrying an origin

The attribute is hidden, so it does not appear in `to_dicts()` or in a join. Query it directly:

```python
# Rows with no recorded origin
Subject & "_prov IS NULL"

# How many, out of how many
len(Subject & "_prov IS NULL"), len(Subject)
```

Write the condition as a **string**. The mapping form returns every row here: it
ignores attributes it cannot match — deliberately, so that `Session & key` works
when `key` carries attributes from a more detailed table — and a hidden
attribute is invisible to that matching
([#1561](https://github.com/datajoint/datajoint-python/issues/1561)):

```python
# MySQL
Subject & "JSON_VALUE(_prov, '$.source.system') = 'PyRat'"

# PostgreSQL
Subject & "jsonb_extract_path_text(_prov, 'source', 'system') = 'PyRat'"

# Subject & {"_prov.system": "PyRat"}   <- returns everything; do not use
```

`_prov IS NULL` and `_prov IS NOT NULL` are the same on both backends. Filtering
on a field inside the JSON is not: the mapping form is what would normally make
that portable, and it does not reach a hidden attribute.

## Read the record back

Until 2.4 this needs SQL. `to_arrays("_prov")` and `proj("_prov")` both raise,
because a hidden attribute cannot be named through the query API
([#1562](https://github.com/datajoint/datajoint-python/issues/1562) adds a
supported accessor):

```python
rows = Subject.connection.query(
    f"SELECT subject_id, _prov FROM {Subject.full_table_name}"
).fetchall()
```

On MySQL the value comes back as a JSON string and needs `json.loads`; on
PostgreSQL psycopg2 returns a dict already.

## Turn capture off

Capture is on by default. To declare tables without the column:

```bash
export DJ_PROVENANCE_CAPTURE=false
```

Turning it off does not remove the column from tables that already have it, and does not stop those tables from recording.

## Add the column to existing tables

Tables declared before 2.3.4 — or while capture was off — have no column, and inserts into them record nothing without complaining. Add the slot:

```python
from datajoint.deploy import add_prov_column

# See what would change
add_prov_column(schema, dry_run=True)["ddl"]

# Apply it
add_prov_column(schema, dry_run=False)
```

Safe to re-run: a table that already has the column is reported and left alone. Rows already present keep `NULL` — provenance is recorded when a row is inserted and is never reconstructed afterwards.

## What you cannot do, and what to do instead

**You cannot write `_prov` yourself.** Passing it in a row raises an error.

That is deliberate. A field the operator can set is weaker evidence than one the system sets, which is the whole point for an audit. It also means the record cannot be half-filled by inconsistent discipline across a team.

**When you want to record something specific to a row** — which file a value came from, which LIMS record, which operator — model it as an ordinary attribute:

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id   : int32
    ---
    species      : varchar(64)
    lims_record  : varchar(64)    # the external record this row was created from
    """
```

A modeled column is visible, queryable, and joinable; `_prov` is none of those, by design. Use `_prov` as the audit record and a modeled column as the domain link. Both can describe the same arrival.

## See Also

- [Extrinsic Provenance at Entry Tables](../reference/specs/boundary-provenance.md) — the specification
- [Insert Data](insert-data.md) — inserting into Manual tables
- [Fan-Out Ingestion](../explanation/fan-out-ingestion.md) — one loader writing into several entry-point tables
- [Configuration](../reference/configuration.md) — where settings come from
