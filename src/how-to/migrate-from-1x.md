# Migrate from 1.x

Upgrade existing pipelines to DataJoint 2.0.

## Configuration Changes

### Config File

Replace `dj_local_conf.json` with `datajoint.json`:

```json
{
  "database": {
    "host": "localhost",
    "user": "datajoint",
    "port": 3306
  },
  "object_storage": {
    "project_name": "my_project",
    "protocol": "file",
    "location": "/data/store"
  }
}
```

### Secrets

Move credentials to `.secrets/` directory:

```
.secrets/
├── database.password
├── object_storage.access_key
└── object_storage.secret_key
```

### Environment Variables

New prefix pattern:

| 1.x | 2.0 |
|-----|-----|
| `DJ_HOST` | `DJ_HOST` (unchanged) |
| `DJ_USER` | `DJ_USER` (unchanged) |
| `DJ_PASS` | `DJ_PASS` (unchanged) |
| — | `DJ_OBJECT_STORAGE_*` |
| — | `DJ_JOBS_*` |

## Type System Changes

### Blob Types

Update blob syntax:

```python
# 1.x syntax
definition = """
data : longblob
data_external : blob@store
"""

# 2.0 syntax
definition = """
data : <blob>
data_external : <blob@store>
"""
```

### Attach Types

```python
# 1.x
attachment : attach

# 2.0
attachment : <attach>
attachment_ext : <attach@store>
```

### Filepath Types

```python
# 1.x (copy-based)
file : filepath@store

# 2.0 (ObjectRef-based)
file : <filepath@store>
```

## Jobs System Changes

### Per-Table Jobs

Jobs are now per-table instead of per-schema:

```python
# 1.x: schema-level ~jobs table
schema.jobs

# 2.0: per-table ~~table_name
MyTable.jobs
MyTable.jobs.pending
MyTable.jobs.errors
```

### Jobs Configuration

```python
# 2.0 job settings
dj.config.jobs.auto_refresh = True
dj.config.jobs.keep_completed = True
dj.config.jobs.stale_timeout = 3600
dj.config.jobs.version_method = "git"
```

## Query Changes

### Universal Set

```python
# 1.x
dj.U() * expression

# 2.0
dj.U() & expression
```

### Natural Join

```python
# 1.x: @ operator for natural join
A @ B

# 2.0: explicit method
A.join(B, semantic_check=False)
```

### Semantic Matching

2.0 uses lineage-based matching by default:

```python
# Attributes matched by lineage, not just name
result = A * B  # Semantic join (default)

# Force name-only matching
result = A.join(B, semantic_check=False)
```

## Migration Steps

### 1. Update Configuration

```bash
# Move config file
mv dj_local_conf.json datajoint.json

# Create secrets directory
mkdir .secrets
echo "password" > .secrets/database.password
chmod 600 .secrets/database.password
```

### 2. Update Table Definitions

Run migration analysis:

```python
from datajoint.migrate import analyze_blob_columns

# Find columns needing migration
results = analyze_blob_columns(schema)
for table, columns in results:
    print(f"{table}: {columns}")
```

Update definitions:

```python
# Old
data : longblob

# New
data : <blob>
```

### 3. Update Blob Column Metadata

Add codec markers to existing columns:

```python
from datajoint.migrate import migrate_blob_columns

# Dry run
migrate_blob_columns(schema, dry_run=True)

# Apply
migrate_blob_columns(schema, dry_run=False)
```

### 4. Update Jobs Code

```python
# Old
schema.jobs

# New
for table in [Table1, Table2, Table3]:
    print(f"{table.__name__}: {table.jobs.progress()}")
```

### 5. Update Queries

Search for deprecated patterns:

```python
# Find uses of @ operator
grep -r " @ " *.py

# Find dj.U() * pattern
grep -r "dj.U() \*" *.py
```

## Compatibility Notes

### Semantic Matching

2.0's semantic matching may change join behavior if:
- Tables have attributes with same name but different lineage
- You relied on name-only matching

Test joins carefully after migration.

### External Storage

Object storage paths changed. If using external storage:
1. Keep 1.x stores accessible during migration
2. Re-insert data to new storage format if needed
3. Or configure stores to use existing paths

### Database Compatibility

2.0 is compatible with MySQL 5.7+ and PostgreSQL 12+.
No database migration required for core functionality.

## See Also

- [Configure Object Storage](configure-storage.md) — New storage configuration
- [Distributed Computing](distributed-computing.md) — Jobs 2.0 system
