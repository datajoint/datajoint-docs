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
- DataJoint 2.0 **cannot read external storage** until migration is complete
- Migration updates metadata (column comments) and converts external references to JSON fields
- **External storage migration is irreversible** — once migrated, 0.14 loses access
- Underlying blob/attachment data in storage remains unchanged

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

### Background

DataJoint 0.x **automatically serialized Python objects** (numpy arrays, lists, dicts, etc.) into `LONGBLOB` fields using a custom serialization format. Users simply assigned Python objects to blob attributes, and DataJoint handled serialization transparently.

DataJoint 2.0 introduces a **core type `bytes`** for raw binary data. Serialization is now **explicit** via the `<blob>` codec, which translates Python objects into bytes. The codec uses the same serialization format as 0.x for backward compatibility.

### Identification
- Column type: `LONGBLOB`
- No external store reference in comment
- Contains serialized numpy arrays, pickled objects, etc.

### Current Storage (0.x)
```sql
column_name LONGBLOB COMMENT 'some description'
-- Implicitly serialized Python objects
```

### Target Format (2.0)
```sql
column_name LONGBLOB COMMENT ':blob: some description'
-- Explicitly marks column as using <blob> codec for serialization
```

### Migration Actions
1. Identify all `LONGBLOB` columns without external store markers
2. Add `:blob:` prefix to column comment
3. **No data modification required** — the serialization format is unchanged, only the metadata is updated to explicitly declare the codec

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

> **This step is irreversible.** Once external references are migrated from hidden tables to JSON fields, DataJoint 0.14 can no longer access the external data.

### Current Architecture (0.14.x)
- External object **hash** stored in main table column (`VARCHAR(255)`)
- Object metadata stored in hidden `~external_<store>` table
- Hidden table maps hash → storage path, size, timestamp

### Target Architecture (2.0)
- External object **metadata** stored directly as JSON in main table
- No hidden tables required
- JSON contains: URL, size, hash, timestamp

### Current Storage (0.14.x)
```sql
-- Main table
external_data VARCHAR(255) COMMENT ':external: large array'
-- Value: 'mYhAsH123...'

-- Hidden table: ~external_store
-- hash | size | timestamp | path
-- mYhAsH123... | 1024 | 2024-01-01 | /data/store/mY/hA/mYhAsH123...
```

### Target Format (2.0)
```sql
external_data JSON COMMENT ':blob@external: large array'
-- Value: {"url": "file:///data/store/mY/hA/mYhAsH123...", "size": 1024, "hash": "mYhAsH123..."}
```

### Migration Actions
1. **Back up database** before proceeding
2. Identify all external blob/attachment columns
3. Verify store configuration exists in `datajoint.json`
4. For each row with external data:
   - Look up hash in `~external_<store>` hidden table
   - Build JSON object with URL, size, hash, timestamp
   - Update column value from hash string to JSON object
5. Update column type from `VARCHAR` to `JSON`
6. Update column comment to `<blob@store>` or `<attach@store>` format
7. Optionally drop hidden `~external_*` tables after verification

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
| 0.14.x | Yes | No |
| 2.0.x | No (external storage) | Yes |

### External Storage Breaking Change

**External storage migration is required and irreversible.**

- **0.14.x** stores external object references in hidden tables (`~external_*`)
- **2.0** stores external object references as JSON fields directly in the table
- **2.0 does not read the legacy hidden external tables**

| Scenario | Result |
|----------|--------|
| Before migration, 0.14 reads schema | Works |
| Before migration, 2.0 reads schema | **Fails for external data** - 2.0 cannot read hidden tables |
| After migration, 2.0 reads schema | Works - uses JSON field format |
| After migration, 0.14 reads schema | **Fails** - 0.14 cannot read JSON format |

**Warning:**
- DataJoint 2.0 **cannot access external storage** until migration is complete
- Migration converts hidden table references to JSON fields (irreversible)
- After migration, DataJoint 0.14 **loses access** to external data
- **Back up your database before migration**

### Recommended Migration Order

1. **Back up database** - Full backup before any changes
2. **Audit external storage** - Identify all schemas using external stores
3. **Coordinate downtime** - All pipelines must stop during migration
4. **Run migration** - Convert external references to JSON fields
5. **Update all code** - Switch to DataJoint 2.0
6. **Verify data access** - Test all external data retrieval
7. **Resume operations** - Only after verification
