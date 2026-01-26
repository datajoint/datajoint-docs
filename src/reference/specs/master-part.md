# Master-Part Relationships Specification

!!! tip "Looking for a task-oriented guide?"
    See [Master-Part Tables](../../how-to/master-part.ipynb) for step-by-step examples.

## Overview

Master-Part relationships model compositional data where a master entity contains multiple detail records. Part tables provide a way to store variable-length, structured data associated with each master entity while maintaining strict referential integrity.

---

## 1. Definition

### 1.1 Master Table

Any table class (`Manual`, `Lookup`, `Imported`, `Computed`) can serve as a master:

```python
@schema
class Session(dj.Manual):
    definition = """
    subject_id : varchar(16)
    session_idx : int16
    ---
    session_date : date
    """
```

### 1.2 Part Table

Part tables are nested classes inheriting from `dj.Part`:

```python
@schema
class Session(dj.Manual):
    definition = """
    subject_id : varchar(16)
    session_idx : int16
    ---
    session_date : date
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_idx : int32
        ---
        stimulus : varchar(32)
        response : varchar(32)
        """
```

### 1.3 SQL Naming

| Python | SQL Table Name |
|--------|----------------|
| `Session` | `schema`.`session` |
| `Session.Trial` | `schema`.`session__trial` |

Part tables use double underscore (`__`) separator in SQL.

### 1.4 Master Reference

Within a Part definition, reference the master using:

```python
-> master        # lowercase keyword (preferred)
-> Session       # explicit class name
```

The `-> master` reference:
- Automatically inherits master's primary key
- Creates foreign key constraint to master
- Enforces ON DELETE RESTRICT (by default)

---

## 2. Integrity Constraints

### 2.1 Compositional Integrity

Master-Part relationships enforce **compositional integrity**:

1. **Existence**: Parts cannot exist without their master
2. **Cohesion**: Parts should be deleted/dropped with their master
3. **Atomicity**: Master and parts form a logical unit

### 2.2 Foreign Key Behavior

Part tables have implicit foreign key to master:

```sql
FOREIGN KEY (master_pk) REFERENCES master_table (master_pk)
ON UPDATE CASCADE
ON DELETE RESTRICT
```

The `ON DELETE RESTRICT` prevents orphaned parts at the database level.

---

## 3. Insert Operations

### 3.1 Master-First Insertion

Master must exist before inserting parts:

```python
# Insert master
Session.insert1({
    'subject_id': 'M001',
    'session_idx': 1,
    'session_date': '2026-01-08'
})

# Insert parts
Session.Trial.insert([
    {'subject_id': 'M001', 'session_idx': 1, 'trial_idx': 1, 'stimulus': 'A', 'response': 'left'},
    {'subject_id': 'M001', 'session_idx': 1, 'trial_idx': 2, 'stimulus': 'B', 'response': 'right'},
])
```

### 3.2 Atomic Insertion

For atomic master+parts insertion, use transactions:

```python
with dj.conn().transaction:
    Session.insert1(master_data)
    Session.Trial.insert(trials_data)
```

### 3.3 Computed Tables with Parts

In `make()` methods, use `self.insert1()` for master and `self.PartName.insert()` for parts:

```python
class ProcessedSession(dj.Computed):
    definition = """
    -> Session
    ---
    n_trials : int32
    """

    class TrialResult(dj.Part):
        definition = """
        -> master
        -> Session.Trial
        ---
        score : float32
        """

    def make(self, key):
        trials = (Session.Trial & key).fetch()
        results = process(trials)

        self.insert1({**key, 'n_trials': len(trials)})
        self.TrialResult.insert(results)
```

---

## 4. Delete Operations

### 4.1 Cascade from Master

Deleting from master cascades to parts:

```python
# Deletes session AND all its trials
(Session & {'subject_id': 'M001', 'session_idx': 1}).delete()
```

### 4.2 Part Integrity Parameter

Direct deletion from Part tables is controlled by `part_integrity`:

```python
def delete(self, part_integrity: str = "enforce", ...) -> int
```

| Value | Behavior |
|-------|----------|
| `"enforce"` | (default) Error if parts deleted without masters |
| `"ignore"` | Allow deleting parts without masters (breaks integrity) |
| `"cascade"` | Also delete masters when parts are deleted |

### 4.3 Default Behavior (enforce)

```python
# Error: Cannot delete from Part directly
Session.Trial.delete()
# DataJointError: Cannot delete from a Part directly.
# Delete from master instead, or use part_integrity='ignore'
# to break integrity, or part_integrity='cascade' to also delete master.
```

### 4.4 Breaking Integrity (ignore)

```python
# Allow direct part deletion (master retains incomplete parts)
(Session.Trial & {'trial_idx': 1}).delete(part_integrity="ignore")
```

**Use cases:**
- Removing specific invalid trials
- Partial data cleanup
- Testing/debugging

**Warning:** This leaves masters with incomplete part data.

### 4.5 Cascade to Master (cascade)

```python
# Delete parts AND their masters
(Session.Trial & condition).delete(part_integrity="cascade")
```

**Behavior:**
- Identifies affected masters
- Deletes masters (which cascades to ALL their parts)
- Maintains compositional integrity

### 4.6 Behavior Matrix

| Operation | Result |
|-----------|--------|
| `Master.delete()` | Deletes master + all parts |
| `Part.delete()` | Error (default) |
| `Part.delete(part_integrity="ignore")` | Deletes parts only |
| `Part.delete(part_integrity="cascade")` | Deletes parts + masters |

---

## 5. Drop Operations

### 5.1 Drop Master

Dropping a master table also drops all its part tables:

```python
Session.drop()  # Drops Session AND Session.Trial
```

### 5.2 Drop Part Directly

Part tables cannot be dropped directly by default:

```python
Session.Trial.drop()
# DataJointError: Cannot drop a Part directly. Drop master instead,
# or use part_integrity='ignore' to force.

# Override with part_integrity="ignore"
Session.Trial.drop(part_integrity="ignore")
```

**Note:** `part_integrity="cascade"` is not supported for drop (too destructive).

### 5.3 Schema Drop

Dropping schema drops all tables including masters and parts:

```python
schema.drop(prompt=False)
```

---

## 6. Query Operations

### 6.1 Accessing Parts

```python
# From master class
Session.Trial

# From master instance
session = Session()
session.Trial
```

### 6.2 Joining Master and Parts

```python
# All trials with session info
Session * Session.Trial

# Filtered
(Session & {'subject_id': 'M001'}) * Session.Trial
```

### 6.3 Aggregating Parts

```python
# Count trials per session
Session.aggr(Session.Trial, n_trials='count(trial_idx)')

# Statistics
Session.aggr(
    Session.Trial,
    n_trials='count(trial_idx)',
    n_correct='sum(response = stimulus)'
)
```

---

## 7. Best Practices

### 7.1 When to Use Part Tables

**Good use cases:**
- Trials within sessions
- Electrodes within probes
- Cells within imaging fields
- Frames within videos
- Rows within files

**Avoid when:**
- Parts have independent meaning (use regular FK instead)
- Need to query parts without master context
- Parts reference multiple masters

### 7.2 Naming Conventions

```python
class Master(dj.Manual):
    class Detail(dj.Part):      # Singular, descriptive
        ...
    class Items(dj.Part):       # Or plural for collections
        ...
```

### 7.3 Part Primary Keys

Include minimal additional keys beyond master reference:

```python
class Session(dj.Manual):
    definition = """
    session_id : int64
    ---
    ...
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_idx : int32      # Only trial-specific key
        ---
        ...
        """
```

### 7.4 Avoiding Deep Nesting

Part tables cannot have their own parts. For hierarchical data:

```python
# Instead of nested parts, use separate tables with FKs
@schema
class Session(dj.Manual):
    definition = """..."""
    class Trial(dj.Part):
        definition = """..."""

@schema
class TrialEvent(dj.Manual):  # Not a Part, but references Trial
    definition = """
    -> Session.Trial
    event_idx : int16
    ---
    event_time : float32
    """
```

---

## 8. Implementation Reference

| File | Purpose |
|------|---------|
| `user_tables.py` | Part class definition |
| `table.py` | delete() with part_integrity |
| `schemas.py` | Part table decoration |
| `declare.py` | Part table SQL generation |

---

## 9. Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Cannot delete from Part directly" | Called Part.delete() with part_integrity="enforce" | Delete from master, or use part_integrity="ignore" or "cascade" |
| "Cannot drop Part directly" | Called Part.drop() with part_integrity="enforce" | Drop master table, or use part_integrity="ignore" |
| "Attempt to delete part before master" | Cascade would delete part without master | Use part_integrity="ignore" or "cascade" |
