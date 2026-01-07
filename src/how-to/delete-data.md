# Delete Data

Remove data safely with proper cascade handling.

## Basic Delete

Delete rows matching a restriction:

```python
# Delete specific subject
(Subject & {'subject_id': 'M001'}).delete()

# Delete with condition
(Session & 'session_date < "2024-01-01"').delete()
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

Part tables cannot be deleted directly:

```python
# This raises an error
Session.Trial.delete()  # DataJointError

# Delete from master instead (cascades to parts)
(Session & key).delete()
```

Force direct deletion when necessary:

```python
(Session.Trial & key).delete(force_parts=True)
```

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
(Trial & 'outcome = "miss"').delete()
```

### By Join

```python
# Delete trials from sessions before 2024
old_sessions = Session & 'session_date < "2024-01-01"'
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

## See Also

- [Model Relationships](model-relationships.md) — Foreign key patterns
- [Insert Data](insert-data.md) — Adding data to tables
- [Run Computations](run-computations.md) — Recomputing after changes
