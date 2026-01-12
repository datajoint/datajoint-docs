# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

## Migration Phases

| Phase | What | Changes | Reversible |
|-------|------|---------|------------|
| 1. Code | Query syntax, API methods | Python code only | 100% |
| 2. Settings | Config files | Files only | 100% |
| 3. Numeric Types | Type names in definitions | Column comments | 100% |
| 4. Blob/Attach (Internal) | Internal blob columns | Column comments | 100% |
| 5. External Blob/Attach | External storage columns | FK → JSON | Yes |
| 6. Filepath | Filepath columns | FK → JSON | Yes |

**Phases 1-4** are trivial. Phases 3-4 only modify column comments—the actual
data and column types are unchanged. You can return to DataJoint 0.x at any
time without data loss.

**Phases 5-6** convert foreign key references to external storage tables into
JSON entries. The critical step is configuring stores to generate the same
paths as stored in the legacy external tables.

Most users only need Phases 1-4.

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
grep -rn "\.fetch('KEY')" --include="*.py"
grep -rn "fetch(as_dict=True)" --include="*.py"
grep -rn "dj\.U.*\*" --include="*.py"
```

**Rollback:** `git checkout` to revert code.

---

## Phase 2: Settings

Update configuration. No database changes.

### Environment Variables (Recommended)

```bash
export DJ_HOST=your-host
export DJ_USER=your-user
export DJ_PASS=your-password
```

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

**Rollback:** Delete `datajoint.json`, use `dj_local_conf.json`.

---

## Phase 3: Numeric Types

Update type names in definitions. Only modifies column comments—the underlying
MySQL column type (INT, FLOAT, etc.) is unchanged.

### Definition Changes

```python
# 0.x
id : int
count : int unsigned
value : float

# 2.0
id : int32
count : uint32
value : float64
```

### Type Mapping

| 0.x | 2.0 | MySQL (unchanged) |
|-----|-----|-------------------|
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

### Apply

```python
from datajoint.migrate import migrate_types

migrate_types(schema, dry_run=True)   # Preview
migrate_types(schema)                  # Apply
```

**Safe:** Only modifies column comments. Data and column types unchanged.

---

## Phase 4: Blob/Attach (Internal)

Migrate internal blobs stored in database. Only modifies column comments.

### Definition Changes

```python
# 0.x
data : longblob
file : attach

# 2.0
data : <blob>
file : <attach>
```

### Apply

```python
from datajoint.migrate import migrate_blobs

migrate_blobs(schema, dry_run=True)   # Preview
migrate_blobs(schema, external=False) # Apply internal only
```

**Safe:** Only modifies column comments. Data unchanged.

---

## Phase 5: External Blob/Attach

Migrate external blobs stored in object storage.

**This phase converts foreign key references to external storage tables into
JSON metadata entries.**

### Definition Changes

```python
# 0.x
data : blob@store
file : attach@store

# 2.0
data : <blob@store>
file : <attach@store>
```

### Critical: Store Configuration

The new store configuration must generate the **same paths** as the legacy
external tables. Verify path compatibility before migrating.

#### Check Legacy Paths

```python
# Examine existing external table entries
from your_pipeline import schema

external_table = schema.external['store']
sample = external_table.fetch(limit=5)
print(sample)  # Note the path structure
```

#### Configure Matching Paths

```json
{
  "stores": {
    "store": {
      "protocol": "file",
      "location": "/path/matching/legacy/store"
    }
  }
}
```

### Verify Before Migration

```python
from datajoint.migrate import verify_external_paths

# Check that new config generates compatible paths
verify_external_paths(schema, store='store')
```

### Apply

```python
from datajoint.migrate import migrate_external

migrate_external(schema, dry_run=True)  # Preview
migrate_external(schema)                 # Apply
```

**Careful:** Converts FK references to JSON. Verify paths first.

---

## Phase 6: Filepath

Migrate filepath references to external files.

**This phase converts foreign key references to external tables into JSON
metadata entries.**

### Definition Changes

```python
# 0.x
path : filepath@store

# 2.0
path : <filepath@store>
```

### Critical: Path Compatibility

Same as Phase 5—ensure store configuration generates matching paths.

### Apply

```python
from datajoint.migrate import migrate_filepath

migrate_filepath(schema, dry_run=True)  # Preview
migrate_filepath(schema)                 # Apply
```

---

## Quick Reference

### Safe Phases (1-4)

Phases 3-4 only modify column comments. Return to 0.x anytime.

| 0.x | 2.0 |
|-----|-----|
| `int` | `int32` |
| `float` | `float64` |
| `longblob` | `<blob>` |
| `attach` | `<attach>` |

### Careful Phases (5-6)

Convert FK references to JSON. Verify path compatibility first.

| 0.x | 2.0 |
|-----|-----|
| `blob@store` | `<blob@store>` |
| `attach@store` | `<attach@store>` |
| `filepath@store` | `<filepath@store>` |

### Code Changes (Phase 1)

| 0.x | 2.0 |
|-----|-----|
| `dj.U() * expr` | `dj.U() & expr` |
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |

---

## Troubleshooting

### "Native type 'int' is used"

Run Phase 3 (numeric types).

### "No codec registered"

Run Phase 4 (blob/attach).

### External data not found

Phase 5/6: Store paths don't match legacy external table paths.
Verify configuration with `verify_external_paths()`.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Configure Storage](configure-storage.md)
