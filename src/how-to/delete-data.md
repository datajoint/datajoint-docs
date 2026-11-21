# Delete Data

Remove data safely with proper cascade handling.

## Basic Delete

Delete rows matching a restriction:

```python
# Delete specific subject
(Subject & {'subject_id': 'M001'}).delete()

# Delete with condition
(Session & "session_date < '2024-01-01'").delete()
```

## Cascade Behavior

Deleting a row automatically cascades to all dependent tables:

```python
# Deletes subject AND all their sessions AND all trials
(Subject & {'subject_id': 'M001'}).delete()
```

This maintains referential integrity—no orphaned records remain.

## Interactive and Production Deletes

The `prompt` parameter controls whether `delete()` asks for confirmation:

```python
# Uses dj.config['safemode'] setting (default behavior)
(Subject & key).delete()

# Explicitly skip confirmation
(Subject & key).delete(prompt=False)

# Explicitly require confirmation
(Subject & key).delete(prompt=True)
```

### Confirmation Prompt for Development

With `prompt=True`, `delete()` logs the row count of each affected table, opens a
transaction, runs the whole cascade inside it, and then, if any rows matched, asks
whether to commit.
Answering `yes` commits. Answering `no`, or pressing Enter, rolls everything back.
Any other answer repeats the question:

```text
[2026-01-15 10:30:00] `lab`.`subject` (1 tuples)
[2026-01-15 10:30:00] `lab`.`session` (5 tuples)
[2026-01-15 10:30:00] `lab`.`trial` (127 tuples)
[2026-01-15 10:30:00] Deleting 127 rows from `lab`.`trial`
[2026-01-15 10:30:00] Deleting 5 rows from `lab`.`session`
[2026-01-15 10:30:00] Deleting 1 rows from `lab`.`subject`
Commit deletes? [yes, No]:
```

This mode is meant for prototyping and development, where you watch the delete
happen and can back out of it.

!!! warning "The prompt waits inside an open transaction"
    When the question appears, the deletes have already run and the transaction stays
    open until someone answers. While it waits, other users' writes and schema changes
    on the affected tables may wait too, and reads can queue behind a waiting schema
    change such as `ALTER TABLE`. On a shared server, an unanswered prompt can stall
    other users.

### Production Deletes

In production, decide what to delete before any transaction opens. Preview the delete,
then run it with `prompt=False`:

```python
import datajoint as dj

restricted = Session & {'subject_id': 'M001'}

# 1. Preview: read-only, opens no transaction
counts = dj.Diagram.cascade(restricted).counts()
# {'`lab`.`session`': 3, '`lab`.`trial`': 45, '`lab`.`processed_data`': 45}

# 2. After reviewing the counts, delete without the prompt
restricted.delete(prompt=False)
```

If you pass `part_integrity` to `delete()`, pass the same value to `Diagram.cascade()`,
so that the preview covers the same rows. The `part_integrity` check itself runs only in
`delete()`: with `"enforce"`, a delete that would remove part rows without their
master raises an error and rolls back (when `delete()` runs its own transaction), and
the preview does not warn about it.

`delete(prompt=False)` runs the cascade in a transaction and commits as soon as the
deletes finish. The preview opens no transaction, so rows can change between the preview
and the delete; the delete removes whatever matches the restriction when it runs.
[Inspecting Cascade Before Deleting](#inspecting-cascade-before-deleting) shows the
counts and a diagram of the affected tables, and how to iterate the cascade to see the
rows themselves. See [Deploy to Production](deploy-production.md) for turning off
`safemode` in production processes.

## Safe Mode Configuration

Control the default prompting behavior:

```python
import datajoint as dj

# Check current setting
print(dj.config['safemode'])

# Disable prompts globally (production processes)
dj.config['safemode'] = False

# Re-enable prompts
dj.config['safemode'] = True
```

Or temporarily override:

```python
with dj.config.override(safemode=False):
    (Subject & restriction).delete()
```

## Transaction Handling

Deletes are atomic—all cascading deletes succeed or none do:

```python
# All-or-nothing delete (default)
(Subject & restriction).delete(transaction=True)
```

Within an existing transaction:

```python
with schema.connection.transaction:
    (Table1 & key1).delete(transaction=False)
    (Table2 & key2).delete(transaction=False)
    Table3.insert(rows)
```

With `transaction=False`, `delete()` asks no confirmation, even with `prompt=True`.
Each `DELETE` takes effect as it runs, and `delete()` does not roll it back. Inside
your own transaction, as above, that transaction commits or rolls back the deletes.

## Part Tables

Part tables cannot be deleted directly by default (master-part integrity):

```python
# This raises an error
Session.Trial.delete()  # DataJointError

# Delete from master instead (cascades to parts)
(Session & key).delete()
```

Use `part_integrity` to control this behavior:

```python
# Allow direct deletion (breaks master-part integrity)
(Session.Trial & key).delete(part_integrity="ignore")

# Delete parts AND cascade up to delete master
(Session.Trial & key).delete(part_integrity="cascade")
```

| Policy | Behavior |
|--------|----------|
| `"enforce"` | (default) Error if parts deleted without masters |
| `"ignore"` | Allow deleting parts without masters |
| `"cascade"` | Also delete masters when parts are deleted |

## Quick Delete

Delete without cascade (fails if dependent rows exist):

```python
# Only works if no dependent tables have matching rows
(Subject & key).delete_quick()
```

## Delete Patterns

### By Primary Key

```python
(Session & {'subject_id': 'M001', 'session_idx': 1}).delete()
```

### By Condition

```python
(Trial & "outcome = 'miss'").delete()
```

### By Join

```python
# Delete trials from sessions before 2024
old_sessions = Session & "session_date < '2024-01-01'"
(Trial & old_sessions).delete()
```

### All Rows

```python
# Delete everything in table (and dependents)
MyTable.delete()
```

## The Recomputation Pattern

When source data needs correction, use **delete → insert → populate**:

```python
key = {'subject_id': 'M001', 'session_idx': 1}

# 1. Delete cascades to computed tables
(Session & key).delete(prompt=False)

# 2. Reinsert with corrected data
with schema.connection.transaction:
    Session.insert1({**key, 'session_date': '2024-01-08', 'duration': 40.0})
    Session.Trial.insert(corrected_trials)

# 3. Recompute derived data
SessionAnalysis.populate()
```

This ensures all derived data remains consistent with source data.

## Return Value

`delete()` returns the count of deleted rows from the primary table:

```python
count = (Subject & restriction).delete(prompt=False)
print(f"Deleted {count} subjects")
```

## Inspecting Cascade Before Deleting

!!! version-added "New in 2.2"
    Cascade inspection via `dj.Diagram` was added in DataJoint 2.2.

`delete(prompt=True)` logs the affected tables and row counts, but it asks for confirmation only after running the deletes inside an open transaction (see [Interactive and Production Deletes](#interactive-and-production-deletes)). To preview a delete without running it, to work across schemas, or to visualize the dependency graph, use `Diagram.cascade()`:

```python
import datajoint as dj

restricted = Session & {'subject_id': 'M001'}

# 1. Preview: see affected tables and row counts (across all loaded schemas)
cascade = dj.Diagram.cascade(restricted)
counts = cascade.counts()
# {'`lab`.`session`': 3, '`lab`.`trial`': 45, '`lab`.`processed_data`': 45}

# 2. Visualize the cascade subgraph (in Jupyter)
cascade

# 3. See the rows: each item is a table restricted to the rows to be deleted
for table in cascade:
    print(table.full_table_name, len(table))
    print(table.head(5))  # first rows; table.keys() returns all primary keys

# 4. Execute via Table.delete() after reviewing
restricted.delete(prompt=False)
```

If you delete with a non-default `part_integrity`, pass the same value to
`Diagram.cascade()`.

### When to Use

- **Preview blast radius**: Understand what a cascade delete will affect before committing
- **Multi-schema inspection**: Build a diagram spanning multiple schemas to visualize cascade impact
- **Programmatic control**: Use `counts()` return values to make decisions in automated workflows

For simple single-table deletes, `(Table & restriction).delete()` remains the simplest approach. The diagram API is for when you need more visibility before executing.

## Reclaiming Object Storage

Deleting rows removes their database records, but for tables with in-store types
(`<blob@>`, `<attach@>`, `<object@>`, `<npy@>`) the stored objects remain — by
design (hash-addressed storage is deduplicated, and immediate deletion is unsafe
under concurrency). Those orphaned objects are reclaimed separately by
[garbage collection](garbage-collection.md); run it periodically to free storage
after large deletes.

## See Also

- [Clean Up Object Storage](garbage-collection.md) — reclaim stored objects orphaned by deletes
- [Diagram Specification](../reference/specs/diagram.md) — Full reference for diagram operations
- [Master-Part Tables](master-part.ipynb) — Compositional data patterns
- [Model Relationships](model-relationships.ipynb) — Foreign key patterns
- [Insert Data](insert-data.md) — Adding data to tables
- [Update Data](update-data.md) — Correcting or replacing existing rows
- [Run Computations](run-computations.md) — Recomputing after changes
