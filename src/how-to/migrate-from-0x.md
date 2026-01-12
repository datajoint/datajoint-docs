# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

## Migration Phases

| Phase | What | Database Changes | Reversible |
|-------|------|------------------|------------|
| 1. Code | Query syntax, API methods | None | Yes |
| 2. Settings | Config files | None | Yes |
| 3. Numeric Types | Type definitions | Column types | Yes |
| 4. Blob/Attach | Internal blobs | Column comments | Yes |
| 5. External Blob/Attach | External storage | Column comments | Yes |
| 6. Filepath | Filepath references | Column comments | Yes |

Each phase is independent. Complete phases in order, testing after each.

---

## Phase 1: Code Migration

Update Python code. No database changes.

### Query Syntax

```python
# 0.x
dj.U('attr') * Table

# 2.0
dj.U('attr') & Table
```

### Aggregation

```python
# 0.x
Table.aggr(dj.U('group'), count='count(*)')

# 2.0
dj.U('group').aggr(Table, count='count(*)')
```

### Fetch Methods

```python
# 0.x
Table.fetch('KEY')
Table.fetch(as_dict=True)

# 2.0
Table.keys()
Table.to_dicts()
```

### Find and Replace

```bash
# Find patterns to update
grep -rn "\.fetch('KEY')" --include="*.py"
grep -rn "fetch(as_dict=True)" --include="*.py"
grep -rn "dj\.U.*\*" --include="*.py"
```

**Rollback:** Revert code changes with git.

---

## Phase 2: Settings

Update configuration files. No database changes.

### Environment Variables (Recommended)

```bash
export DJ_HOST=your-host
export DJ_USER=your-user
export DJ_PASS=your-password
```

Works with both 0.x and 2.0.

### Config File

Replace `dj_local_conf.json` with `datajoint.json`:

```json
{
  "database": {
    "host": "localhost",
    "user": "datajoint",
    "port": 3306
  }
}
```

### Secrets

```bash
mkdir -p .secrets && chmod 700 .secrets
echo "password" > .secrets/database.password
chmod 600 .secrets/database.password
```

**Rollback:** Delete `datajoint.json`, revert to `dj_local_conf.json`.

---

## Phase 3: Numeric Types

Update type definitions and database columns.

### Definition Changes

```python
# 0.x native types
definition = """
id : int
count : int unsigned
value : float
"""

# 2.0 core types
definition = """
id : int32
count : uint32
value : float64
"""
```

### Type Mapping

| 0.x | 2.0 | MySQL |
|-----|-----|-------|
| `int` | `int32` | INT |
| `int unsigned` | `uint32` | INT UNSIGNED |
| `smallint` | `int16` | SMALLINT |
| `smallint unsigned` | `uint16` | SMALLINT UNSIGNED |
| `tinyint` | `int8` | TINYINT |
| `tinyint unsigned` | `uint8` | TINYINT UNSIGNED |
| `bigint` | `int64` | BIGINT |
| `bigint unsigned` | `uint64` | BIGINT UNSIGNED |
| `float` | `float32` | FLOAT |
| `double` | `float64` | DOUBLE |

### Migration Steps

1. Update definitions in Python code
2. Run migration to update database:

```python
from datajoint.migrate import migrate_types

# Preview
migrate_types(schema, dry_run=True)

# Apply
migrate_types(schema, dry_run=False)
```

**Idempotent:** Safe to run multiple times.

**Rollback:**
```python
from datajoint.migrate import rollback_types
rollback_types(schema)
```

---

## Phase 4: Blob/Attach (Internal)

Migrate internal blob and attach columns (stored in database).

### Definition Changes

```python
# 0.x
data : longblob
file : attach

# 2.0
data : <blob>
file : <attach>
```

### Migration Steps

1. Update definitions in Python code
2. Run migration:

```python
from datajoint.migrate import migrate_blobs

# Preview
migrate_blobs(schema, dry_run=True)

# Apply (internal only)
migrate_blobs(schema, external=False)
```

This updates column comments to register codecs. **Data unchanged.**

**Rollback:**
```python
from datajoint.migrate import rollback_blobs
rollback_blobs(schema, external=False)
```

---

## Phase 5: External Blob/Attach

Migrate external blob and attach columns (stored in object storage).

### Definition Changes

```python
# 0.x
data : blob@store
file : attach@store

# 2.0
data : <blob@store>
file : <attach@store>
```

### Configure Stores

Ensure stores are configured in `datajoint.json`:

```json
{
  "stores": {
    "store": {
      "protocol": "file",
      "location": "/path/to/existing/store"
    }
  }
}
```

**Use same paths as 0.x** - DataJoint 2.0 reads existing data.

### Migration Steps

1. Update definitions in Python code
2. Configure stores
3. Run migration:

```python
from datajoint.migrate import migrate_blobs

# Preview
migrate_blobs(schema, dry_run=True, external=True)

# Apply
migrate_blobs(schema, external=True)
```

**Rollback:**
```python
rollback_blobs(schema, external=True)
```

---

## Phase 6: Filepath

Migrate filepath references to external files.

### Definition Changes

```python
# 0.x
path : filepath@store

# 2.0
path : <filepath@store>
```

### Migration Steps

1. Update definitions in Python code
2. Run migration:

```python
from datajoint.migrate import migrate_filepath

# Preview
migrate_filepath(schema, dry_run=True)

# Apply
migrate_filepath(schema)
```

**Rollback:**
```python
from datajoint.migrate import rollback_filepath
rollback_filepath(schema)
```

---

## Verification

After each phase, verify your pipeline:

```python
import datajoint as dj
from your_pipeline import schema

# List tables
print(schema.list_tables())

# Check a table
SomeTable()

# Test fetch
data = (SomeTable & key).fetch1()
```

---

## Quick Reference

### Code Changes (Phase 1)

| 0.x | 2.0 |
|-----|-----|
| `dj.U() * expr` | `dj.U() & expr` |
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |
| `Table.aggr(dj.U('x'), ...)` | `dj.U('x').aggr(Table, ...)` |

### Type Changes (Phase 3)

| 0.x | 2.0 |
|-----|-----|
| `int` | `int32` |
| `int unsigned` | `uint32` |
| `float` | `float32` |
| `double` | `float64` |

### Blob Changes (Phases 4-6)

| 0.x | 2.0 |
|-----|-----|
| `longblob` | `<blob>` |
| `blob@store` | `<blob@store>` |
| `attach` | `<attach>` |
| `attach@store` | `<attach@store>` |
| `filepath@store` | `<filepath@store>` |

---

## Troubleshooting

### "Native type 'int' is used"

Update to core types (Phase 3):
```python
# Change: int -> int32
```

### "No codec registered"

Run blob migration (Phases 4-6).

### External data not found

Check store configuration matches 0.x paths.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Configure Storage](configure-storage.md)
