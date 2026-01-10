# DataJoint 2.0 Migration Specification

This specification defines the migration process from DataJoint 0.x to DataJoint 2.0. The migration preserves all existing data while updating metadata to leverage 2.0's enhanced type system.

> **Warning: Read and understand this entire specification before migrating.**
>
> Migration involves irreversible changes to external storage metadata. We strongly recommend using an advanced AI coding assistant (e.g., Claude Code, Cursor, GitHub Copilot) to:
>
> 1. **Analyze your schema** — Identify all tables, data types, and external storage usage
> 2. **Generate a migration plan** — Create a step-by-step plan specific to your pipeline
> 3. **Execute with oversight** — Run migration steps with human review at each stage
>
> The migration process is designed and tested for agentic execution, allowing AI assistants to safely perform the migration while keeping you informed of each change.

## Overview

DataJoint 2.0 introduces a unified type system with explicit codecs for object storage. **Migration is required** to use 2.0's full feature set. The migration updates table metadata (column comments) to include type labels that 2.0 uses to interpret data correctly.

**Key points:**
- DataJoint 2.0 can read 0.x schemas **before migration** (including external storage)
- Migration updates metadata only; underlying data remains unchanged
- **External storage migration is one-way** — once migrated, 0.14 loses access to external data

### Migration Components

| Step | Component | Description |
|------|-----------|-------------|
| 0 | Settings | Update configuration to `datajoint.json` format |
| 1 | Core Types | Add type labels to column comments for numeric/string types |
| 2 | Internal Blobs | Convert `LONGBLOB` columns to `<blob>` codec |
| 3 | Internal Attachments | Convert attachment columns to `<attach>` codec |
| 4 | External Objects | Convert external blobs/attachments to `<blob@>` / `<attach@>` codecs |
| 5 | Filepaths | Convert filepath columns to `<filepath@>` codec |

---

## Step 0: Settings File Migration

### Current (0.x)
```python
dj.config['database.host'] = 'localhost'
dj.config['database.user'] = 'root'
dj.config['database.password'] = 'secret'
dj.config['stores'] = {
    'external': {
        'protocol': 'file',
        'location': '/data/external'
    }
}
```

### Target (2.0)
```
project/
├── datajoint.json
└── .secrets/
    ├── database.password
    └── database.user
```

**datajoint.json:**
```json
{
  "database.host": "localhost",
  "stores": {
    "external": {
      "protocol": "file",
      "location": "/data/external"
    }
  }
}
```

### Migration Actions
1. Create `datajoint.json` from existing `dj_local_conf.json` or `dj.config` settings
2. Move credentials to `.secrets/` directory
3. Add `.secrets/` to `.gitignore`
4. Update environment variables if used (`DJ_*` prefix)

---

## Step 1: Core Type Labels

DataJoint 2.0 uses explicit type aliases (`int32`, `float64`, etc.) stored in column comments.

### Type Mapping

| MySQL Native | DataJoint 2.0 | Comment Label |
|--------------|---------------|---------------|
| `TINYINT` | `int8` | `:int8:` |
| `TINYINT UNSIGNED` | `uint8` | `:uint8:` |
| `SMALLINT` | `int16` | `:int16:` |
| `SMALLINT UNSIGNED` | `uint16` | `:uint16:` |
| `INT` | `int32` | `:int32:` |
| `INT UNSIGNED` | `uint32` | `:uint32:` |
| `BIGINT` | `int64` | `:int64:` |
| `BIGINT UNSIGNED` | `uint64` | `:uint64:` |
| `FLOAT` | `float32` | `:float32:` |
| `DOUBLE` | `float64` | `:float64:` |
| `TINYINT(1)` | `bool` | `:bool:` |

### Migration Actions
1. Query `INFORMATION_SCHEMA.COLUMNS` for all tables in schema
2. For each numeric column, determine the appropriate 2.0 type
3. Update column comment to include type label prefix

### Example SQL
```sql
ALTER TABLE `schema`.`table_name`
MODIFY COLUMN `column_name` INT NOT NULL COMMENT ':int32: original comment';
```

---

## Step 2: Internal Blobs (`<blob>`)

Internal blobs are stored directly in the database as `LONGBLOB` columns.

### Identification
- Column type: `LONGBLOB`
- No external store reference in comment
- Used for numpy arrays, pickled objects

### Current Storage
```sql
column_name LONGBLOB COMMENT 'some description'
```

### Target Format
```sql
column_name LONGBLOB COMMENT ':blob: some description'
```

### Migration Actions
1. Identify all `LONGBLOB` columns without external store markers
2. Add `:blob:` prefix to column comment
3. No data modification required (format unchanged)

---

## Step 3: Internal Attachments (`<attach>`)

Internal attachments store files directly in the database with filename metadata.

### Identification
- Column type: `LONGBLOB`
- Comment contains `:attach:` or attachment indicator
- Stores serialized (filename, content) tuples

### Current Storage
```sql
attachment LONGBLOB COMMENT ':attach: uploaded file'
```

### Target Format
```sql
attachment LONGBLOB COMMENT ':attach: uploaded file'
```

### Migration Actions
1. Identify attachment columns (existing `:attach:` marker or known attachment pattern)
2. Verify comment format matches 2.0 specification
3. No data modification required

---

## Step 4: External Objects (`<blob@>`, `<attach@>`)

External objects store data in configured storage backends (S3, filesystem) with metadata in the database.

### Identification
- Column type: `VARCHAR(255)` or similar (stores hash/path)
- Comment contains store reference (e.g., `:external:`)
- Corresponding entry in external storage

### Current Storage
```sql
external_data VARCHAR(255) COMMENT ':external: large array'
```

### Target Format
```sql
external_data JSON COMMENT ':blob@external: large array'
```

### Migration Actions
1. Identify external blob/attachment columns
2. Verify store configuration exists in `datajoint.json`
3. Update column comment to use `<blob@store>` or `<attach@store>` format
4. Migrate column type from `VARCHAR` to `JSON` if needed
5. Update path format to URL representation (`file://`, `s3://`)

### Store Configuration
Ensure stores are defined in `datajoint.json`:
```json
{
  "stores": {
    "external": {
      "protocol": "file",
      "location": "/data/external"
    },
    "s3store": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-bucket"
    }
  }
}
```

---

## Step 5: Filepath Codec (`<filepath@>`)

Filepath columns store references to managed files in external storage.

### Identification
- Column type: `VARCHAR(255)` or similar
- Comment contains `:filepath:` or filepath indicator
- References files in managed storage location

### Current Storage
```sql
file_path VARCHAR(255) COMMENT ':filepath@store: data file'
```

### Target Format
```sql
file_path JSON COMMENT ':filepath@store: data file'
```

### Migration Actions
1. Identify filepath columns
2. Verify store configuration
3. Update column type to `JSON` if needed
4. Convert stored paths to URL format
5. Update comment to 2.0 format

---

## AI-Assisted Migration

The migration process is optimized for execution by AI coding assistants. Before running the migration tool, use your AI assistant to:

### 1. Schema Analysis
```
Analyze my DataJoint schema at [database_host]:
- List all schemas and tables
- Identify column types requiring migration
- Flag external storage usage and store configurations
- Report any potential compatibility issues
```

### 2. Migration Plan Generation
```
Create a migration plan for schema [schema_name]:
- Step-by-step actions with SQL statements
- Backup checkpoints before irreversible changes
- Validation queries after each step
- Estimated impact (rows affected, storage changes)
```

### 3. Supervised Execution
```
Execute the migration plan for [schema_name]:
- Run each step and report results
- Pause for confirmation before external storage migration
- Verify data integrity after completion
```

The AI assistant will use this specification and the migration tool to execute the plan safely.

---

## Migration Tool

DataJoint 2.0 provides a migration utility:

```python
from datajoint.migrate import migrate_schema

# Analyze schema without making changes
report = migrate_schema('my_schema', dry_run=True)
print(report)

# Perform migration
migrate_schema('my_schema', dry_run=False)
```

### Options
- `dry_run`: Analyze without modifying (default: True)
- `backup`: Create backup before migration (default: True)
- `stores`: Store configuration dict (uses config if not provided)

---

## Rollback

If migration issues occur:

1. **Settings**: Restore original `dj_local_conf.json`
2. **Column comments**: Revert comment changes via SQL
3. **Core types and internal blobs**: Fully reversible

**External storage cannot be rolled back.** Once external object references are migrated from hidden tables to JSON fields:
- The hidden `~external_*` tables are no longer updated
- DataJoint 0.14 cannot read the JSON field format
- Reverting requires restoring from backup

**Recommendation:** Create a full database backup before migrating schemas with external storage.

---

## Validation

After migration, verify:

```python
import datajoint as dj

schema = dj.Schema('my_schema')

# Check all tables load correctly
for table in schema.list_tables():
    tbl = schema(table)
    print(f"{table}: {len(tbl)} rows")
    # Fetch sample to verify data access
    if len(tbl) > 0:
        tbl.fetch(limit=1)
```

---

## Version Compatibility

| DataJoint Version | Can Read 0.x Data | Can Read 2.0 Data |
|-------------------|-------------------|-------------------|
| 0.14.x | Yes | No (loses external data access) |
| 2.0.x | Yes (including external) | Yes |

### External Storage Breaking Change

**This is a one-way migration for external storage.**

- **0.14.x** stores external object references in hidden tables (`~external_*`)
- **2.0** stores external object references as JSON fields directly in the table

| Scenario | Result |
|----------|--------|
| Before migration, 2.0 reads 0.x schema | Works - 2.0 can read hidden table format |
| After migration, 2.0 reads schema | Works - uses JSON field format |
| After migration, 0.14 reads schema | **Breaks** - 0.14 cannot read JSON format, loses access to external data |

**Warning:** Once external storage is migrated to 2.0 format, reverting to DataJoint 0.14 will result in loss of access to externally stored data. Ensure all users/pipelines are ready for 2.0 before migrating schemas with external storage.

### Recommended Migration Order

1. Update all code to DataJoint 2.0
2. Test with existing schemas (2.0 can read 0.x format)
3. Migrate schemas once all systems are on 2.0
4. Verify data access after migration
