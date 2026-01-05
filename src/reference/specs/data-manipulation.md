# DataJoint Data Manipulation Specification

Version: 1.0
Status: Draft
Last Updated: 2025-01-04

## Overview

This document specifies data manipulation operations in DataJoint Python: insert, update, and delete. These operations maintain referential integrity across the pipeline while supporting the **workflow normalization** paradigm.

## 1. Workflow Normalization Philosophy

### 1.1 Insert and Delete as Primary Operations

DataJoint pipelines are designed around **insert** and **delete** as the primary data manipulation operations:

```
Insert: Add complete entities (rows) to tables
Delete: Remove entities and all dependent data (cascading)
```

This design maintains referential integrity at the **entity level**—each row represents a complete, self-consistent unit of data.

### 1.2 Updates as Surgical Corrections

**Updates are intentionally limited** to the `update1()` method, which modifies a single row at a time. This is by design:

- Updates bypass the normal workflow
- They can create inconsistencies with derived data
- They should be used sparingly for **corrective operations**

**Appropriate uses of update1():**
- Fixing data entry errors
- Correcting metadata after the fact
- Administrative annotations

**Inappropriate uses:**
- Regular workflow operations
- Batch modifications
- Anything that should trigger recomputation

### 1.3 The Recomputation Pattern

When source data changes, the correct pattern is:

```python
# 1. Delete the incorrect data (cascades to all derived tables)
(SourceTable & {"key": value}).delete()

# 2. Insert the corrected data
SourceTable.insert1(corrected_row)

# 3. Recompute derived tables
DerivedTable.populate()
```

This ensures all derived data remains consistent with its sources.

---

## 2. Insert Operations

### 2.1 `insert()` Method

**Signature:**
```python
def insert(
    self,
    rows,
    replace=False,
    skip_duplicates=False,
    ignore_extra_fields=False,
    allow_direct_insert=None,
    chunk_size=None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rows` | iterable | — | Data to insert |
| `replace` | bool | `False` | Replace existing rows with matching PK |
| `skip_duplicates` | bool | `False` | Silently skip duplicate keys |
| `ignore_extra_fields` | bool | `False` | Ignore fields not in table |
| `allow_direct_insert` | bool | `None` | Allow insert into auto-populated tables |
| `chunk_size` | int | `None` | Insert in batches of this size |

### 2.2 Accepted Input Formats

| Format | Example |
|--------|---------|
| List of dicts | `[{"id": 1, "name": "Alice"}, ...]` |
| pandas DataFrame | `pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})` |
| polars DataFrame | `pl.DataFrame({"id": [1, 2], "name": ["A", "B"]})` |
| numpy structured array | `np.array([(1, "A")], dtype=[("id", int), ("name", "U10")])` |
| QueryExpression | `OtherTable.proj(...)` (INSERT...SELECT) |
| Path to CSV | `Path("data.csv")` |

### 2.3 Basic Usage

```python
# Single row
Subject.insert1({"subject_id": 1, "name": "Mouse001", "dob": "2024-01-15"})

# Multiple rows
Subject.insert([
    {"subject_id": 1, "name": "Mouse001", "dob": "2024-01-15"},
    {"subject_id": 2, "name": "Mouse002", "dob": "2024-01-16"},
])

# From DataFrame
df = pd.DataFrame({"subject_id": [1, 2], "name": ["M1", "M2"], "dob": ["2024-01-15", "2024-01-16"]})
Subject.insert(df)

# From query (INSERT...SELECT)
ActiveSubjects.insert(Subject & "status = 'active'")
```

### 2.4 Handling Duplicates

```python
# Error on duplicate (default)
Subject.insert1({"subject_id": 1, ...})  # Raises DuplicateError if exists

# Skip duplicates silently
Subject.insert(rows, skip_duplicates=True)

# Replace existing rows
Subject.insert(rows, replace=True)
```

**Difference between skip and replace:**
- `skip_duplicates`: Keeps existing row unchanged
- `replace`: Overwrites existing row with new values

### 2.5 Extra Fields

```python
# Error on extra fields (default)
Subject.insert1({"subject_id": 1, "unknown_field": "x"})  # Raises error

# Ignore extra fields
Subject.insert1({"subject_id": 1, "unknown_field": "x"}, ignore_extra_fields=True)
```

### 2.6 Auto-Populated Tables

Computed and Imported tables normally only accept inserts from their `make()` method:

```python
# Raises DataJointError by default
ComputedTable.insert1({"key": 1, "result": 42})

# Explicit override
ComputedTable.insert1({"key": 1, "result": 42}, allow_direct_insert=True)
```

### 2.7 Chunked Insertion

For large datasets, insert in batches:

```python
# Insert 10,000 rows at a time
Subject.insert(large_dataset, chunk_size=10000)
```

Each chunk is a separate transaction. If interrupted, completed chunks persist.

### 2.8 `insert1()` Method

Convenience wrapper for single-row inserts:

```python
def insert1(self, row, **kwargs)
```

Equivalent to `insert((row,), **kwargs)`.

### 2.9 Staged Insert for Large Objects

For large objects (Zarr arrays, HDF5 files), use staged insert to write directly to object storage:

```python
with table.staged_insert1 as staged:
    # Set primary key and metadata
    staged.rec["session_id"] = 123
    staged.rec["timestamp"] = datetime.now()

    # Write large data directly to storage
    zarr_path = staged.store("raw_data", ".zarr")
    z = zarr.open(zarr_path, mode="w")
    z[:] = large_array
    staged.rec["raw_data"] = z

# Row automatically inserted on successful exit
# Storage cleaned up if exception occurs
```

---

## 3. Update Operations

### 3.1 `update1()` Method

**Signature:**
```python
def update1(self, row: dict) -> None
```

**Parameters:**
- `row`: Dictionary containing all primary key values plus attributes to update

### 3.2 Basic Usage

```python
# Update a single attribute
Subject.update1({"subject_id": 1, "name": "NewName"})

# Update multiple attributes
Subject.update1({
    "subject_id": 1,
    "name": "NewName",
    "notes": "Updated on 2024-01-15"
})
```

### 3.3 Requirements

1. **Complete primary key**: All PK attributes must be provided
2. **Exactly one match**: Must match exactly one existing row
3. **No restrictions**: Cannot call on restricted table

```python
# Error: incomplete primary key
Subject.update1({"name": "NewName"})

# Error: row doesn't exist
Subject.update1({"subject_id": 999, "name": "Ghost"})

# Error: cannot update restricted table
(Subject & "subject_id > 10").update1({...})
```

### 3.4 Resetting to Default

Setting an attribute to `None` resets it to its default value:

```python
# Reset 'notes' to its default (NULL if nullable)
Subject.update1({"subject_id": 1, "notes": None})
```

### 3.5 When to Use Updates

**Appropriate:**
```python
# Fix a typo in metadata
Subject.update1({"subject_id": 1, "name": "Mouse001"})  # Was "Mous001"

# Add a note to an existing record
Session.update1({"session_id": 5, "notes": "Excluded from analysis"})
```

**Inappropriate (use delete + insert + populate instead):**
```python
# DON'T: Update source data that affects computed results
Trial.update1({"trial_id": 1, "stimulus": "new_stim"})  # Computed tables now stale!

# DO: Delete and recompute
(Trial & {"trial_id": 1}).delete()  # Cascades to computed tables
Trial.insert1({"trial_id": 1, "stimulus": "new_stim"})
ComputedResults.populate()
```

### 3.6 Why No Bulk Update?

DataJoint intentionally does not provide `update()` for multiple rows:

1. **Consistency**: Bulk updates easily create inconsistencies with derived data
2. **Auditability**: Single-row updates are explicit and traceable
3. **Workflow**: The insert/delete pattern maintains referential integrity

If you need to update many rows, iterate explicitly:

```python
for key in (Subject & condition).fetch("KEY"):
    Subject.update1({**key, "status": "archived"})
```

---

## 4. Delete Operations

### 4.1 `delete()` Method

**Signature:**
```python
def delete(
    self,
    transaction: bool = True,
    safemode: bool | None = None,
    force_parts: bool = False,
    force_masters: bool = False,
) -> int
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transaction` | bool | `True` | Wrap in atomic transaction |
| `safemode` | bool | `None` | Prompt for confirmation (default: config setting) |
| `force_parts` | bool | `False` | Allow deleting parts without master |
| `force_masters` | bool | `False` | Include master/part pairs in cascade |

**Returns:** Number of deleted rows from the primary table.

### 4.2 Cascade Behavior

Delete automatically cascades to all dependent tables:

```python
# Deleting a subject deletes all their sessions, trials, and computed results
(Subject & {"subject_id": 1}).delete()
```

**Cascade order:**
1. Identify all tables with foreign keys referencing target
2. Recursively delete matching rows in child tables
3. Delete rows in target table

### 4.3 Basic Usage

```python
# Delete specific rows
(Subject & {"subject_id": 1}).delete()

# Delete matching a condition
(Session & "session_date < '2024-01-01'").delete()

# Delete all rows (use with caution!)
Subject.delete()
```

### 4.4 Safe Mode

When `safemode=True` (default from config):

```
About to delete:
  Subject: 1 rows
  Session: 5 rows
  Trial: 150 rows
  ProcessedData: 150 rows

Commit deletes? [yes, No]:
```

Disable for automated scripts:

```python
Subject.delete(safemode=False)
```

### 4.5 Transaction Control

```python
# Atomic delete (default) - all or nothing
(Subject & condition).delete(transaction=True)

# Non-transactional (for nested transactions)
(Subject & condition).delete(transaction=False)
```

### 4.6 Part Table Constraints

Cannot delete from part tables without deleting from master:

```python
# Error: cannot delete part without master
Session.Recording.delete()

# Override with force_parts
Session.Recording.delete(force_parts=True)
```

### 4.7 `delete_quick()` Method

Fast delete without cascade or confirmation:

```python
def delete_quick(self, get_count: bool = False) -> int | None
```

**Use cases:**
- Internal cleanup
- Tables with no dependents
- When you've already handled dependencies

**Behavior:**
- No cascade to child tables
- No user confirmation
- Fails on FK constraint violation

```python
# Quick delete (fails if has dependents)
(TempTable & condition).delete_quick()

# Get count of deleted rows
n = (TempTable & condition).delete_quick(get_count=True)
```

---

## 5. Validation

### 5.1 `validate()` Method

Pre-validate rows before insertion:

```python
def validate(self, rows, *, ignore_extra_fields=False) -> ValidationResult
```

**Returns:** `ValidationResult` with:
- `is_valid`: Boolean indicating all rows passed
- `errors`: List of (row_idx, field_name, error_message)
- `rows_checked`: Number of rows validated

### 5.2 Usage

```python
result = Subject.validate(rows)

if result:
    Subject.insert(rows)
else:
    print(result.summary())
    # Row 3, field 'dob': Invalid date format
    # Row 7, field 'subject_id': Missing required field
```

### 5.3 Validations Performed

| Check | Description |
|-------|-------------|
| Field existence | All fields must exist in table |
| NULL constraints | Required fields must have values |
| Primary key completeness | All PK fields must be present |
| UUID format | Valid UUID string or object |
| JSON serializability | JSON fields must be serializable |
| Codec validation | Custom type validation via codecs |

### 5.4 Limitations

These constraints are only checked at database level:
- Foreign key references
- Unique constraints (beyond PK)
- Custom CHECK constraints

---

## 6. Part Tables

### 6.1 Inserting into Part Tables

Part tables are inserted via their master:

```python
@schema
class Session(dj.Manual):
    definition = """
    session_id : int
    ---
    date : date
    """

    class Recording(dj.Part):
        definition = """
        -> master
        recording_id : int
        ---
        duration : float
        """

# Insert master with parts
Session.insert1({"session_id": 1, "date": "2024-01-15"})
Session.Recording.insert([
    {"session_id": 1, "recording_id": 1, "duration": 60.0},
    {"session_id": 1, "recording_id": 2, "duration": 45.5},
])
```

### 6.2 Deleting with Part Tables

Deleting master cascades to parts:

```python
# Deletes session AND all its recordings
(Session & {"session_id": 1}).delete()
```

Cannot delete parts independently (by default):

```python
# Error
Session.Recording.delete()

# Must use force_parts
Session.Recording.delete(force_parts=True)
```

---

## 7. Transaction Handling

### 7.1 Implicit Transactions

Single operations are atomic:

```python
Subject.insert1(row)  # Atomic
Subject.update1(row)  # Atomic
Subject.delete()      # Atomic (by default)
```

### 7.2 Explicit Transactions

For multi-table operations:

```python
with dj.conn().transaction:
    Parent.insert1(parent_row)
    Child.insert(child_rows)
    # Commits on successful exit
    # Rolls back on exception
```

### 7.3 Chunked Inserts and Transactions

With `chunk_size`, each chunk is a separate transaction:

```python
# Each chunk of 1000 rows commits independently
Subject.insert(large_dataset, chunk_size=1000)
```

If interrupted, completed chunks persist.

---

## 8. Error Handling

### 8.1 Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `DuplicateError` | Primary key already exists | Use `skip_duplicates=True` or `replace=True` |
| `IntegrityError` | Foreign key constraint violated | Insert parent rows first |
| `MissingAttributeError` | Required field not provided | Include all required fields |
| `UnknownAttributeError` | Field not in table | Use `ignore_extra_fields=True` or fix field name |
| `DataJointError` | Various validation failures | Check error message for details |

### 8.2 Error Recovery Pattern

```python
try:
    Subject.insert(rows)
except dj.errors.DuplicateError as e:
    # Handle specific duplicate
    print(f"Duplicate: {e}")
except dj.errors.IntegrityError as e:
    # Missing parent reference
    print(f"Missing parent: {e}")
except dj.DataJointError as e:
    # Other DataJoint errors
    print(f"Error: {e}")
```

---

## 9. Best Practices

### 9.1 Prefer Insert/Delete Over Update

```python
# Good: Delete and reinsert
(Trial & key).delete()
Trial.insert1(corrected_trial)
DerivedTable.populate()

# Avoid: Update that creates stale derived data
Trial.update1({**key, "value": new_value})  # Derived tables now inconsistent!
```

### 9.2 Validate Before Insert

```python
result = Subject.validate(rows)
if not result:
    raise ValueError(result.summary())
Subject.insert(rows)
```

### 9.3 Use Transactions for Related Inserts

```python
with dj.conn().transaction:
    session_key = Session.insert1(session_data, skip_duplicates=True)
    Session.Recording.insert(recordings)
    Session.Stimulus.insert(stimuli)
```

### 9.4 Batch Inserts for Performance

```python
# Good: Single insert call
Subject.insert(all_rows)

# Avoid: Loop of insert1 calls
for row in all_rows:
    Subject.insert1(row)  # Slow!
```

### 9.5 Safe Deletion in Production

```python
# Always use safemode in interactive sessions
(Subject & condition).delete(safemode=True)

# Disable only in tested automated scripts
(Subject & condition).delete(safemode=False)
```

---

## 10. Quick Reference

| Operation | Method | Cascades | Transaction | Typical Use |
|-----------|--------|----------|-------------|-------------|
| Insert one | `insert1()` | — | Implicit | Adding single entity |
| Insert many | `insert()` | — | Per-chunk | Bulk data loading |
| Insert large object | `staged_insert1` | — | On exit | Zarr, HDF5 files |
| Update one | `update1()` | — | Implicit | Surgical corrections |
| Delete | `delete()` | Yes | Optional | Removing entities |
| Delete quick | `delete_quick()` | No | No | Internal cleanup |
| Validate | `validate()` | — | — | Pre-insert check |
