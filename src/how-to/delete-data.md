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

## Confirmation Prompt

The `prompt` parameter controls confirmation behavior:

```python
# Uses dj.config['safemode'] setting (default behavior)
(Subject & key).delete()

# Explicitly skip confirmation
(Subject & key).delete(prompt=False)

# Explicitly require confirmation
(Subject & key).delete(prompt=True)
```

When prompted, you'll see what will be deleted:

```
About to delete:
  1 rows from `lab`.`subject`
  5 rows from `lab`.`session`
  127 rows from `lab`.`trial`

Proceed? [yes, No]:
```

## Safe Mode Configuration

Control the default prompting behavior:

```python
import datajoint as dj

# Check current setting
print(dj.config['safemode'])

# Disable prompts globally (use with caution)
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
with dj.conn().transaction:
    (Table1 & key1).delete(transaction=False)
    (Table2 & key2).delete(transaction=False)
    Table3.insert(rows)
```

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
with dj.conn().transaction:
    Session.insert1({**key, 'session_date': '2024-01-08', 'duration': 40.0})
    Session.Trial.insert(corrected_trials)

# 3. Recompute derived data
ProcessedData.populate()
```

This ensures all derived data remains consistent with source data.

## Return Value

`delete()` returns the count of deleted rows from the primary table:

```python
count = (Subject & restriction).delete(prompt=False)
print(f"Deleted {count} subjects")
```

## Diagram-Level Delete

!!! version-added "New in 2.2"
    Diagram-level delete was added in DataJoint 2.2.

For complex scenarios — previewing the blast radius, working across schemas, or understanding the dependency graph before deleting — use `dj.Diagram` to build and inspect the cascade before executing.

### Build, Preview, Execute

```python
import datajoint as dj

# 1. Build the dependency graph
diag = dj.Diagram(schema)

# 2. Apply cascade restriction (nothing deleted yet)
restricted = diag.cascade(Session & {'subject_id': 'M001'})

# 3. Preview: see affected tables and row counts
counts = restricted.preview()
# {'`lab`.`session`': 3, '`lab`.`trial`': 45, '`lab`.`processed_data`': 45}

# 4. Execute only after reviewing
restricted.delete(prompt=False)
```

### When to Use

- **Preview blast radius**: Understand what a cascade delete will affect before committing
- **Multi-schema cascades**: Build a diagram spanning multiple schemas and delete across them in one operation
- **Programmatic control**: Use `preview()` return values to make decisions in automated workflows

For simple single-table deletes, `(Table & restriction).delete()` remains the simplest approach. The diagram-level API is for when you need more visibility or control.

## See Also

- [Diagram Specification](../reference/specs/diagram.md/) — Full reference for diagram operations
- [Master-Part Tables](master-part.ipynb) — Compositional data patterns
- [Model Relationships](model-relationships.ipynb) — Foreign key patterns
- [Insert Data](insert-data.md) — Adding data to tables
- [Run Computations](run-computations.md) — Recomputing after changes
