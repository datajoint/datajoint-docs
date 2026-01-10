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
- External object **UUID hash** stored in main table column (`BINARY(16)` for uuid)
- Object metadata stored in hidden `~external_<store>` table
- Hidden table maps hash → storage path, size, timestamp

**Hidden table schema (`~external_<store>`):**
```sql
hash              : uuid                  # hash of contents (primary key)
---
size              : bigint unsigned       # size of object in bytes
attachment_name   : varchar(255)          # filename for attachments (nullable)
filepath          : varchar(1000)         # relative filepath (nullable)
contents_hash     : uuid                  # used for filepath datatype (nullable)
timestamp         : timestamp             # automatic timestamp
```

### Target Architecture (2.0)
- External object **metadata** stored directly as JSON in main table
- No hidden tables required
- JSON contains: URL, size, hash, timestamp

### Current Storage (0.14.x)
```sql
-- Main table column stores UUID hash
external_data BINARY(16) COMMENT ':external: large array'
-- Value: 0x1A2B3C4D...  (UUID bytes)

-- Hidden table (~external_mystore) row:
-- hash: 1a2b3c4d-...
-- size: 1048576
-- filepath: 1a/2b/1a2b3c4d...
-- timestamp: 2024-01-15 10:30:00
```

### Target Format (2.0)
```sql
external_data JSON COMMENT ':blob@mystore: large array'
-- Value: {"url": "file:///data/mystore/1a/2b/1a2b3c4d...", "size": 1048576, "hash": "1a2b3c4d..."}
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

The migration process is optimized for execution by AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.). This section provides detailed prompts for each phase of the migration.

### Getting Started

Start a conversation with your AI coding assistant using this initial prompt:

```
I need to migrate my DataJoint database from version 0.14 to 2.0.

Database connection:
- Host: [your_host]
- User: [your_user]
- Schema(s): [schema1, schema2, ...]

Please read the DataJoint 2.0 Migration Specification at:
https://docs.datajoint.com/reference/specs/migration-2.0/

Then analyze my schema and create a migration plan.
```

---

### Phase 1: Schema Analysis

Use this prompt to analyze your database before migration:

```
Analyze my DataJoint schema for 2.0 migration readiness.

Connect to the database and for each schema:

1. LIST ALL TABLES
   - Query INFORMATION_SCHEMA.TABLES for all tables
   - Identify user tables vs hidden tables (~external_*, ~jobs_*, ~log)
   - Count rows in each table

2. IDENTIFY BLOB COLUMNS
   - Find all LONGBLOB columns in user tables
   - Check column comments for existing type markers
   - These will need :blob: codec marker

3. IDENTIFY EXTERNAL STORAGE
   - Find hidden ~external_* tables
   - List which stores are configured
   - For each external column in user tables:
     - Count rows with external references
     - Verify referenced hashes exist in external table
     - Check if external files are accessible

4. IDENTIFY ATTACHMENT COLUMNS
   - Find columns with :attach: or :attachment: markers
   - Distinguish internal vs external attachments

5. IDENTIFY FILEPATH COLUMNS
   - Find columns with :filepath: markers
   - Verify file accessibility

6. CHECK STORE CONFIGURATION
   - Read current dj.config['stores'] settings
   - Verify each store location is accessible
   - Note protocol (file, s3) for each store

Output a migration readiness report with:
- Total tables and rows
- Columns requiring migration by type
- External storage summary
- Potential issues or warnings
```

---

### Phase 2: Backup Verification

Before any changes, ensure backups are in place:

```
Before proceeding with migration, verify backups:

1. DATABASE BACKUP
   - Confirm a full mysqldump or equivalent exists
   - Verify backup timestamp is recent
   - Test that backup can be restored (on a test server if possible)

2. EXTERNAL STORAGE BACKUP
   - For each store location, confirm backup exists
   - File stores: verify rsync/copy of directory
   - S3 stores: verify bucket versioning or cross-region replication

3. CONFIGURATION BACKUP
   - Save current dj_local_conf.json
   - Save current dj.config output
   - Document environment variables (DJ_*)

4. CREATE ROLLBACK PLAN
   - Document exact steps to restore from backup
   - Note that external storage migration is irreversible
   - Identify point-of-no-return in migration

Confirm all backups are verified before proceeding.
```

---

### Phase 3: Settings Migration

Migrate configuration to 2.0 format:

```
Migrate DataJoint configuration to 2.0 format.

1. READ CURRENT CONFIGURATION
   - Load dj_local_conf.json if exists
   - Read dj.config programmatically
   - Check for DJ_* environment variables

2. CREATE datajoint.json
   Create the new config file with structure:
   {
     "database.host": "...",
     "database.port": 3306,
     "stores": {
       "store_name": {
         "protocol": "file|s3",
         "location": "...",
         ...
       }
     }
   }

3. CREATE .secrets/ DIRECTORY
   - Create .secrets/database.user with username
   - Create .secrets/database.password with password
   - Set permissions: chmod 600 .secrets/*

4. UPDATE .gitignore
   Add if not present:
   .secrets/
   datajoint.json

5. VERIFY NEW CONFIGURATION
   - Test connection with DataJoint 2.0
   - Verify all stores are accessible

Show me the generated datajoint.json (without secrets) for review.
```

---

### Phase 4: Core Type Migration

Add type labels to numeric and string columns:

```
Migrate core data types for schema [schema_name].

For each table in the schema:

1. QUERY COLUMN INFORMATION
   SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, COLUMN_COMMENT
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '[schema_name]' AND TABLE_NAME = '[table_name]'

2. DETERMINE 2.0 TYPE LABELS
   Map MySQL types to DataJoint 2.0 labels:
   - TINYINT -> :int8: (or :uint8: if unsigned)
   - SMALLINT -> :int16: (or :uint16: if unsigned)
   - INT -> :int32: (or :uint32: if unsigned)
   - BIGINT -> :int64: (or :uint64: if unsigned)
   - FLOAT -> :float32:
   - DOUBLE -> :float64:
   - TINYINT(1) -> :bool:

3. GENERATE ALTER STATEMENTS
   For each column needing migration:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` [TYPE] COMMENT ':type_label: original comment';

4. EXECUTE WITH VERIFICATION
   - Run each ALTER statement
   - Verify column comment was updated
   - Log success/failure

Generate and show me all ALTER statements before executing.
```

---

### Phase 5: Blob Codec Migration

Mark blob columns with the <blob> codec:

```
Migrate internal blob columns for schema [schema_name].

1. IDENTIFY BLOB COLUMNS
   Find all LONGBLOB columns without external markers:
   SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '[schema_name]'
     AND DATA_TYPE = 'longblob'
     AND COLUMN_COMMENT NOT LIKE '%:external%'
     AND COLUMN_COMMENT NOT LIKE '%:blob@%'

2. GENERATE ALTER STATEMENTS
   For each blob column:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` LONGBLOB COMMENT ':blob: original comment';

3. EXECUTE AND VERIFY
   - Run each ALTER statement
   - Verify data is still readable (fetch one row)
   - Log success/failure

Show all ALTER statements for review before executing.
```

---

### Phase 6: External Storage Migration (IRREVERSIBLE)

**This step cannot be undone. Confirm backups before proceeding.**

```
Migrate external storage for schema [schema_name].

WARNING: This step is IRREVERSIBLE. Confirm:
- [ ] Database backup verified
- [ ] External storage backup verified
- [ ] All pipelines stopped
- [ ] Team notified of downtime

For each table with external columns:

1. IDENTIFY EXTERNAL COLUMNS
   Find columns referencing external storage:
   - Column type is BINARY(16) (uuid)
   - Comment contains :external: or similar marker

2. GET STORE INFORMATION
   For each external column, identify the store name from the comment

3. BUILD MIGRATION QUERY
   For each row with external data:

   a. Read the UUID hash from the main table
   b. Look up metadata in ~external_[store]:
      SELECT size, filepath, attachment_name, contents_hash, timestamp
      FROM `~external_[store]`
      WHERE hash = [uuid_value]

   c. Build the JSON object:
      {
        "url": "[protocol]://[location]/[filepath]",
        "size": [size],
        "hash": "[uuid_hex]",
        "timestamp": "[timestamp]"
      }

   d. For attachments, include filename:
      {
        "url": "...",
        "size": ...,
        "hash": "...",
        "filename": "[attachment_name]"
      }

4. ALTER COLUMN TYPE
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` JSON COMMENT ':blob@[store]: original comment';

5. UPDATE EACH ROW
   UPDATE `schema`.`table`
   SET `column` = '[json_object]'
   WHERE [primary_key_condition];

6. VERIFY MIGRATION
   - Count rows with JSON values
   - Verify JSON structure is valid
   - Test fetching data through DataJoint 2.0

7. OPTIONAL: DROP HIDDEN TABLES
   After verification, optionally remove:
   DROP TABLE `~external_[store]`;

Show me the migration plan with row counts before executing.
Pause for confirmation before each table.
```

---

### Phase 7: Validation

Verify the migration was successful:

```
Validate the DataJoint 2.0 migration for schema [schema_name].

1. CONNECTION TEST
   - Connect using DataJoint 2.0
   - Verify schema loads without errors

2. TABLE ACCESS TEST
   For each table:
   - Instantiate the table class
   - Verify heading loads correctly
   - Fetch 1-5 sample rows
   - Verify all columns are readable

3. BLOB DATA TEST
   For tables with blob columns:
   - Fetch a row with blob data
   - Verify blob deserializes correctly (numpy array, etc.)
   - Check data type and shape match expected

4. EXTERNAL DATA TEST
   For tables with external columns:
   - Fetch a row with external data
   - Verify file is retrieved from storage
   - Verify data deserializes correctly
   - Check file size matches JSON metadata

5. COMPUTED TABLE TEST
   For computed tables:
   - Verify populate() can run on new data
   - Check that dependencies resolve correctly

6. GENERATE VALIDATION REPORT
   - Tables tested: X/Y passed
   - Blob columns verified: X/Y
   - External columns verified: X/Y
   - Any errors or warnings

Report any issues found during validation.
```

---

### Troubleshooting Prompts

If issues arise during migration:

```
I encountered an error during migration:

Error: [paste error message]
Step: [which phase/step]
Table: [table name if applicable]

Please help me:
1. Diagnose the root cause
2. Determine if rollback is needed
3. Provide corrective action
4. Verify the fix before continuing
```

```
The migration completed but I'm seeing issues:

Problem: [describe the issue]
- Which tables are affected?
- What data is not accessible?
- What error messages appear?

Please help me investigate and resolve this.
```

---

### Post-Migration Checklist

```
Run the post-migration checklist for schema [schema_name]:

1. [ ] All tables accessible via DataJoint 2.0
2. [ ] All blob data deserializes correctly
3. [ ] All external data retrieves correctly
4. [ ] Computed tables can populate new data
5. [ ] Job tables functioning (if used)
6. [ ] All team members updated to DataJoint 2.0
7. [ ] CI/CD pipelines updated
8. [ ] Documentation updated with new connection info
9. [ ] Old dj_local_conf.json archived/removed
10. [ ] Monitoring in place for any issues

Mark each item as verified.
```

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
