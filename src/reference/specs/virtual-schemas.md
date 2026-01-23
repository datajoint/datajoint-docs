# Virtual Schemas Specification

## Overview

Virtual schemas provide a way to access existing database schemas without the original Python source code. This is useful for:

- Exploring schemas created by other users
- Accessing legacy schemas
- Quick data inspection and queries
- Schema migration and maintenance

---

## 1. Schema-Module Convention

DataJoint maintains a **1:1 mapping** between database schemas and Python modules:

| Database | Python |
|----------|--------|
| Schema | Module |
| Table | Class |

This convention reduces conceptual complexity: **modules are schemas, classes are tables**.

When you define tables in Python:
```python
# lab.py module
import datajoint as dj
schema = dj.Schema('lab')

@schema
class Subject(dj.Manual):  # Subject class → `lab`.`subject` table
    ...

@schema
class Session(dj.Manual):  # Session class → `lab`.`session` table
    ...
```

Virtual schemas recreate this mapping when the Python source isn't available:
```python
# Creates module-like object with table classes
lab = dj.virtual_schema('lab')
lab.Subject  # Subject class for `lab`.`subject`
lab.Session  # Session class for `lab`.`session`
```

---

## 2. Schema Introspection API

### 2.1 Direct Table Access

Access individual tables by name using bracket notation:

```python
schema = dj.Schema('my_schema')

# By CamelCase class name
experiment = schema['Experiment']

# By snake_case SQL name
experiment = schema['experiment']

# Query the table
experiment.fetch()
```

### 2.2 `get_table()` Method

Explicit method for table access:

```python
table = schema.get_table('Experiment')
table = schema.get_table('experiment')  # also works
```

**Parameters:**
- `name` (str): Table name in CamelCase or snake_case

**Returns:** `FreeTable` instance

**Raises:** `DataJointError` if table doesn't exist

### 2.3 Iteration

Iterate over all tables in dependency order:

```python
for table in schema:
    print(table.full_table_name, len(table))
```

Tables are yielded as `FreeTable` instances in topological order (dependencies before dependents).

### 2.4 Containment Check

Check if a table exists:

```python
if 'Experiment' in schema:
    print("Table exists")

if 'nonexistent' not in schema:
    print("Table doesn't exist")
```

---

## 3. Virtual Schema Function

### 3.1 `dj.virtual_schema()`

The recommended way to access existing schemas as modules:

```python
lab = dj.virtual_schema('my_lab_schema')

# Access tables as attributes (classes)
lab.Subject.fetch()
lab.Session & "subject_id='M001'"

# Full query algebra supported
(lab.Session * lab.Subject).fetch()
```

This maintains the module-class convention: `lab` behaves like a Python module with table classes as attributes.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema_name` | str | required | Database schema name |
| `connection` | Connection | None | Database connection (uses default) |
| `create_schema` | bool | False | Create schema if missing |
| `create_tables` | bool | False | Allow new table declarations |
| `add_objects` | dict | None | Additional objects for namespace |

**Returns:** `VirtualModule` instance

### 3.2 VirtualModule Class

The underlying class (prefer `virtual_schema()` function):

```python
module = dj.VirtualModule('lab', 'my_lab_schema')
module.Subject.fetch()
```

The first argument is the module display name, second is the schema name.

### 3.3 Accessing the Schema Object

Virtual modules expose the underlying Schema:

```python
lab = dj.virtual_schema('my_lab_schema')
lab.schema.database  # 'my_lab_schema'
lab.schema.list_tables()  # ['subject', 'session', ...]
```

---

## 4. Table Class Generation

### 4.1 `make_classes()`

Create Python classes for all tables in a schema:

```python
schema = dj.Schema('existing_schema')
schema.make_classes()

# Now table classes are available in local namespace
Subject.fetch()
Session & "date > '2024-01-01'"
```

**Parameters:**
- `into` (dict, optional): Namespace to populate. Defaults to caller's locals.

### 4.2 Generated Class Types

Classes are created based on table naming conventions:

| Table Name Pattern | Generated Class |
|-------------------|-----------------|
| `subject` | `dj.Manual` |
| `#lookup_table` | `dj.Lookup` |
| `_imported_table` | `dj.Imported` |
| `__computed_table` | `dj.Computed` |
| `master__part` | `dj.Part` |

### 4.3 Part Table Handling

Part tables are attached to their master classes:

```python
lab = dj.virtual_schema('my_lab')

# Part tables are nested attributes
lab.Session.Trial.fetch()  # Session.Trial is a Part table
```

---

## 5. Use Cases

### 5.1 Data Exploration

```python
# Quick exploration of unknown schema
lab = dj.virtual_schema('collaborator_lab')

# List all tables
print(lab.schema.list_tables())

# Check table structure
print(lab.Subject.describe())

# Preview data
lab.Subject.fetch(limit=5)
```

### 5.2 Cross-Schema Queries

```python
my_schema = dj.Schema('my_analysis')
external = dj.virtual_schema('external_lab')

# Reference external tables in queries
@my_schema
class Analysis(dj.Computed):
    definition = """
    -> external.Session
    ---
    result : float
    """
```

### 5.3 Schema Migration

```python
old = dj.virtual_schema('old_schema')
new = dj.Schema('new_schema')

# Copy data in topological order (iteration yields dependencies first)
for table in old:
    new_table = new.get_table(table.table_name)
    # Server-side INSERT...SELECT (no client-side data transfer)
    new_table.insert(table)
```

### 5.4 Garbage Collection

```python
from datajoint.gc import scan_hash_references

schema = dj.Schema('my_schema')

# Scan all tables for hash references
refs = scan_hash_references(schema, verbose=True)
```

---

## 6. Comparison of Methods

| Method | Use Case | Returns |
|--------|----------|---------|
| `schema['Name']` | Quick single table access | `FreeTable` |
| `schema.get_table('name')` | Explicit table access | `FreeTable` |
| `for t in schema` | Iterate all tables | `FreeTable` generator |
| `'Name' in schema` | Check existence | `bool` |
| `dj.virtual_schema(name)` | Module-like access | `VirtualModule` |
| `make_classes()` | Populate namespace | None (side effect) |

---

## 7. Implementation Reference

| File | Purpose |
|------|---------|
| `schemas.py` | Schema, VirtualModule, virtual_schema |
| `table.py` | FreeTable class |
| `gc.py` | Uses get_table() for scanning |

---

## 8. Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Table does not exist" | `get_table()` on missing table | Check table name spelling |
| "Schema must be activated" | Operations on unactivated schema | Call `schema.activate(name)` |
| "Schema does not exist" | Schema name not in database | Check schema name, create if needed |
