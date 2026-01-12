# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

## Overview

DataJoint 2.0 is largely backward-compatible. Migration happens in two parts:

| Part | What Changes | Database Changes |
|------|--------------|------------------|
| **Part 1: Code** | Python code, config files | None |
| **Part 2: Blobs** | Blob column metadata | Column comments only |

**After Part 1, most pipelines work immediately.** Part 2 is only needed if you
use blob types (`longblob`, `blob@store`, `attach`, `filepath@store`).

---

## Part 1: Code Migration

Update your Python code and configuration. No database changes required.

### 1.1 Install DataJoint 2.0

```bash
# In your project environment
pip install datajoint>=2.0

# Verify
python -c "import datajoint; print(datajoint.__version__)"
```

### 1.2 Update Configuration

#### Option A: Environment Variables (Recommended)

```bash
export DJ_HOST=your-database-host
export DJ_USER=your-username
export DJ_PASS=your-password
```

No file changes needed. Works with both 0.x and 2.0.

#### Option B: Config File

Create `datajoint.json` (2.0 ignores `dj_local_conf.json`):

```json
{
  "database": {
    "host": "localhost",
    "user": "datajoint",
    "port": 3306
  }
}
```

For credentials, create `.secrets/database.password`:

```bash
mkdir -p .secrets && chmod 700 .secrets
echo "your_password" > .secrets/database.password
chmod 600 .secrets/database.password
```

### 1.3 Update Table Definitions

Most definitions work unchanged. Update these patterns:

#### Type Syntax

```python
# 0.x (still works for non-blob types)
mouse_id : int
name : varchar(100)

# 2.0 (same - no change needed)
mouse_id : int
name : varchar(100)
```

#### Blob Types (Update Required)

```python
# 0.x
data : longblob
data : blob@store
file : attach
file : attach@store
path : filepath@store

# 2.0
data : <blob>
data : <blob@store>
file : <attach>
file : <attach@store>
path : <filepath@store>
```

### 1.4 Update Queries

#### Universal Set

```python
# 0.x
dj.U('attr') * Table

# 2.0
dj.U('attr') & Table
```

#### Fetch Methods

```python
# 0.x
Table.fetch('KEY')
Table.fetch(as_dict=True)

# 2.0
Table.keys()
Table.to_dicts()
```

#### Aggregation

```python
# 0.x
Table.aggr(dj.U('group'), count='count(*)')

# 2.0
dj.U('group').aggr(Table, count='count(*)')
```

### 1.5 Test Your Pipeline

After code changes, test with existing tables:

```python
import datajoint as dj
from your_pipeline import schema, Mouse, Session, ...

# These should work immediately
Mouse()                          # View table
len(Session)                     # Count rows
(Mouse & 'mouse_id=1').fetch1()  # Query data
```

**If you don't use blob types, you're done!**

---

## Part 2: Blob Migration

Required only if your pipeline uses blob types. This updates column metadata
(comments) to register codecs. **Data is not modified.**

### 2.1 Check If Needed

```python
from datajoint.migrate import check_blob_columns

# Returns list of columns needing migration
columns = check_blob_columns(schema)
if not columns:
    print("No blob migration needed!")
else:
    print(f"Columns to migrate: {columns}")
```

### 2.2 Preview Changes

```python
from datajoint.migrate import migrate_blobs

# Dry run - shows what would change
migrate_blobs(schema, dry_run=True)
```

Output shows:
```
Table.column: longblob -> <blob>
Table.external_data: blob@store -> <blob@store>
```

### 2.3 Apply Migration

```python
# Apply changes (modifies column comments only)
migrate_blobs(schema, dry_run=False)
```

**Idempotent:** Running multiple times is safe - already-migrated columns are skipped.

### 2.4 Verify

```python
# Test blob fetch
data = (MyTable & key).fetch1('blob_column')
print(f"Fetched: {type(data)}")
```

---

## External Storage Migration

If you use external storage (`blob@store`, `attach@store`, etc.), configure stores:

### Update Store Configuration

```json
{
  "stores": {
    "your_store_name": {
      "protocol": "file",
      "location": "/path/to/existing/store"
    }
  }
}
```

**Use the same paths as 0.x.** DataJoint 2.0 reads existing external data without modification.

### S3/MinIO Stores

```json
{
  "stores": {
    "s3store": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "your-bucket",
      "location": "datajoint"
    }
  }
}
```

---

## Rollback

### Rollback Part 1 (Code)

```bash
# Downgrade package
pip install datajoint==0.14.2

# Revert code changes
git checkout <previous-commit>
```

### Rollback Part 2 (Blobs)

Blob migration only changes column comments. To rollback:

```python
from datajoint.migrate import rollback_blobs

rollback_blobs(schema)  # Removes codec markers from comments
```

Or manually:
```sql
ALTER TABLE `schema`.`table`
MODIFY COLUMN `column` LONGBLOB COMMENT 'original comment';
```

---

## Quick Reference

### What Works Immediately (No Migration)

- All non-blob table operations
- Inserts, updates, deletes
- Queries (restriction, join, projection)
- Schema inspection (`dj.Diagram`, `heading`)
- Foreign key relationships

### What Requires Code Changes

| 0.x | 2.0 |
|-----|-----|
| `dj.U() * expr` | `dj.U() & expr` |
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |
| `longblob` | `<blob>` |
| `blob@store` | `<blob@store>` |

### What Requires Blob Migration

- Fetching existing blob data with 2.0
- Using codec features (compression, external storage)

---

## Troubleshooting

### "No codec registered" Error

Run blob migration:
```python
from datajoint.migrate import migrate_blobs
migrate_blobs(schema)
```

### External Data Not Found

Check store configuration matches 0.x paths:
```python
import datajoint as dj
print(dj.config.stores)  # Verify store paths
```

### Import Errors After Downgrade

Clear Python cache:
```bash
find . -name __pycache__ -type d -exec rm -rf {} +
```

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Configure Storage](configure-storage.md)
