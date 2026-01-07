# Alter Tables

Modify existing table structures for schema evolution.

## Basic Alter

Sync table definition with code:

```python
# Update definition in code, then:
MyTable.alter()
```

This compares the current code definition with the database and generates `ALTER TABLE` statements.

## What Can Be Altered

| Change | Supported |
|--------|-----------|
| Add columns | Yes |
| Drop columns | Yes |
| Modify column types | Yes |
| Rename columns | Yes |
| Change defaults | Yes |
| Update table comment | Yes |
| **Modify primary key** | **No** |
| **Add/remove foreign keys** | **No** |
| **Modify indexes** | **No** |

## Add a Column

```python
# Original
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    species : varchar(32)
    """

# Updated - add column
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    species : varchar(32)
    weight = null : float32      # New column
    """

# Apply change
Subject.alter()
```

## Drop a Column

Remove from definition and alter:

```python
# Column 'old_field' removed from definition
Subject.alter()
```

## Modify Column Type

```python
# Change varchar(32) to varchar(100)
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    species : varchar(100)       # Was varchar(32)
    """

Subject.alter()
```

## Rename a Column

DataJoint tracks renames via comment metadata:

```python
# Original: species
# Renamed to: species_name
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    species_name : varchar(32)   # Renamed from 'species'
    """

Subject.alter()
```

## Skip Confirmation

```python
# Apply without prompting
Subject.alter(prompt=False)
```

## View Pending Changes

Check what would change without applying:

```python
# Show current definition
print(Subject.describe())

# Compare with code definition
# (alter() shows diff before prompting)
```

## Unsupported Changes

### Primary Key Changes

Cannot modify primary key attributes:

```python
# This will raise NotImplementedError
@schema
class Subject(dj.Manual):
    definition = """
    new_id : uuid               # Changed primary key
    ---
    species : varchar(32)
    """

Subject.alter()  # Error!
```

**Workaround**: Create new table, migrate data, drop old table.

### Foreign Key Changes

Cannot add or remove foreign key references:

```python
# Cannot add new FK via alter()
definition = """
subject_id : varchar(16)
---
-> NewReference              # Cannot add via alter
species : varchar(32)
"""
```

**Workaround**: Drop dependent tables, recreate with new structure.

### Index Changes

Cannot modify indexes via alter:

```python
# Cannot add/remove indexes via alter()
definition = """
subject_id : varchar(16)
---
index(species)               # Cannot add via alter
species : varchar(32)
"""
```

## Migration Pattern

For unsupported changes, use this pattern:

```python
# 1. Create new table with desired structure
@schema
class SubjectNew(dj.Manual):
    definition = """
    subject_id : uuid            # New primary key type
    ---
    species : varchar(32)
    """

# 2. Migrate data
for row in Subject.fetch(as_dict=True):
    SubjectNew.insert1({
        'subject_id': uuid.uuid4(),  # Generate new keys
        'species': row['species']
    })

# 3. Update dependent tables
# 4. Drop old table
# 5. Rename new table (if needed, via SQL)
```

## Add Job Metadata Columns

For tables created before enabling job metadata:

```python
from datajoint.migrate import add_job_metadata_columns

# Dry run
add_job_metadata_columns(ProcessedData, dry_run=True)

# Apply
add_job_metadata_columns(ProcessedData, dry_run=False)
```

## Best Practices

### Plan Schema Carefully

Primary keys and foreign keys cannot be changed easily. Design carefully upfront.

### Use Migrations for Production

For production systems, use versioned migration scripts:

```python
# migrations/001_add_weight_column.py
def upgrade():
    Subject.alter(prompt=False)

def downgrade():
    # Reverse the change
    pass
```

### Test in Development First

Always test schema changes on a copy:

```python
# Clone schema for testing
test_schema = dj.Schema('test_' + schema.database)
```

## See Also

- [Define Tables](define-tables.md) — Table definition syntax
- [Migrate from 0.x](migrate-from-0x.md) — Version migration
