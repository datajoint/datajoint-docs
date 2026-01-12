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

## Why Migrate?

DataJoint 2.0 is a major architectural improvement that makes pipelines faster, more reliable, and easier to maintain.

### Key Benefits

| Improvement | Before (0.x) | After (2.0) |
|-------------|--------------|-------------|
| **Transparency** | Hidden tables, implicit serialization, magic behavior | Everything visible in schema, explicit codecs, no hidden state |
| **Extensibility** | Fixed set of blob/attachment types | Custom codecs for any data type (images, video, domain objects) |
| **Portability** | MySQL-specific hidden tables, tight coupling | Backend-agnostic design ready for Polars, Databricks, and other platforms |
| **Type Safety** | Implicit types inferred at runtime | Explicit type labels in schema metadata |
| **External Storage** | Metadata in hidden tables, UUID indirection | Inline JSON with direct URLs, no hidden tables |
| **Configuration** | Python dict, credentials in code | JSON config file, secrets separated |
| **Data Retrieval** | Single `.fetch()` with many options | Explicit methods: `to_dicts()`, `to_pandas()`, `to_polars()` |

### What You Gain

**Transparency:**
- **No hidden tables** — External storage metadata visible directly in table rows as JSON
- **Explicit types** — Column types declared in schema, not inferred at runtime
- **Clear serialization** — `<blob>` codec makes serialization intent obvious
- **Inspectable storage** — External URLs visible in data, easy to debug and verify

**Extensibility:**
- **Custom codecs** — Define your own codecs for domain-specific types (e.g., `<nifti>` for neuroimaging, `<video>` for behavior recordings)
- **Pluggable serialization** — Choose how objects are stored (numpy, pickle, custom formats)
- **Storage flexibility** — Same codec interface works with internal blobs and external stores

**Portability:**
- **Backend-agnostic architecture** — No MySQL-specific hidden tables or features required
- **Future-ready** — Designed for compatibility with alternative backends (Polars, DuckDB, Databricks, cloud data warehouses)
- **Standard formats** — JSON metadata and explicit type labels work across platforms
- **Clean separation** — Data model decoupled from storage implementation

**Performance & Usability:**
- **Faster queries** — No hidden table joins for external data
- **Modern formats** — Native support for pandas, polars, and Arrow
- **Lazy iteration** — Stream rows from cursor instead of fetching all keys first
- **Better security** — Credentials separated from configuration

### What Changes

- Column comments gain type label prefixes (e.g., `:int32:`, `:blob:`)
- External storage columns change from `BINARY(16)` UUID to `JSON` metadata
- Configuration moves from `dj_local_conf.json` to `datajoint.json` + `.secrets/`
- Code updates needed for new fetch API (`to_dicts()` instead of `fetch()`)

---

## Overview

DataJoint 2.0 introduces a unified type system with explicit codecs for object storage. **Migration is required** to use 2.0's full feature set. The migration updates table metadata (column comments) to include type labels that 2.0 uses to interpret data correctly.

**Key points:**
- DataJoint 2.0 **cannot read external storage** until migration is complete
- Migration updates metadata (column comments) and converts external references to JSON fields
- **External storage migration is irreversible** — once migrated, 0.14 loses access
- Underlying blob/attachment data in storage remains unchanged

### Migration Components

| Step | Component | Description | Reversible |
|------|-----------|-------------|------------|
| 0 | Settings | Update configuration to `datajoint.json` format | Yes |
| 1 | Core Types | Add type labels to column comments for numeric/string types | Yes |
| 2 | Internal Blobs | Convert `LONGBLOB` columns to `<blob>` codec | Yes |
| 3 | Internal Attachments | Convert attachment columns to `<attach>` codec | Yes |
| 4 | External Objects | Convert external blobs/attachments to `<blob@>` / `<attach@>` codecs | **No** |
| 5 | Filepaths | Convert filepath columns to `<filepath@>` codec | **No** |
| 6 | AdaptedTypes | Convert `AttributeAdapter` classes to `Codec` classes | Yes |

### Safety and Reversibility

**Safe to run repeatedly (idempotent):** All steps check current state before making changes and skip already-migrated items. Re-running any step will not corrupt data.

**Reversible steps (0-3, 6):**
- Only modify column comments (metadata) and Python code
- Original data remains unchanged
- Can revert by restoring original comments and code
- DataJoint 0.14 continues to work after these steps

**Irreversible steps (4-5):**
- Convert column types from `BINARY(16)` to `JSON`
- Transform data from UUID hash references to inline JSON metadata
- Hidden tables become obsolete
- **DataJoint 0.14 loses access** to external data after these steps
- Rollback requires restoring from backup

**Recommended approach:**
1. Run steps 0-3 first (safe, reversible)
2. Run step 6 if using custom AttributeAdapters (safe, reversible)
3. Validate that DataJoint 2.0 works with internal data
4. Create full backup
5. Run steps 4-5 (irreversible)
6. Validate external data access
7. Update all pipeline code to DataJoint 2.0

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

### How 0.x Marked External Columns

DataJoint 0.x used **column comments** to identify external storage columns. The markers appear after the column description:

| 0.x Column Comment Pattern | Type | Example |
|---------------------------|------|---------|
| `... :external:` | External blob (default store) | `large array :external:` |
| `... :external-<store>:` | External blob (named store) | `large array :external-s3store:` |
| `... :external-attach:` | External attachment (default store) | `data file :external-attach:` |
| `... :external-attach-<store>:` | External attachment (named store) | `data file :external-attach-s3store:` |

**SQL examples from 0.x tables:**
```sql
-- External blob using default store
data_array BINARY(16) COMMENT 'neural data :external:'

-- External blob using named store "s3data"
large_matrix BINARY(16) COMMENT 'preprocessed matrix :external-s3data:'

-- External attachment using default store
raw_file BINARY(16) COMMENT 'raw recording :external-attach:'

-- External attachment using named store
video_file BINARY(16) COMMENT 'behavior video :external-attach-videos:'
```

The column type is `BINARY(16)` because it stores the **UUID hash** (16 bytes) that references the actual data location in the hidden `~external_<store>` table.

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

## Step 6: AdaptedTypes to Codecs

DataJoint 0.x provided `dj.AttributeAdapter` for custom attribute types. DataJoint 2.0 replaces this with the more powerful `dj.Codec` system.

### Background

In 0.x, users created adapter instances and registered them via `spawn_missing_classes()`:

```python
# 0.x AttributeAdapter pattern
class ImageAdapter(dj.AttributeAdapter):
    attribute_type = 'longblob'

    def put(self, img):
        # Called on INSERT
        return cv2.imencode('.png', img)[1].tobytes()

    def get(self, data):
        # Called on FETCH
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

# Registration
image_adapter = ImageAdapter()
schema.spawn_missing_classes(context={..., 'image': image_adapter})
```

In 2.0, codecs are class-based and auto-register:

```python
# 2.0 Codec pattern
class ImageCodec(dj.Codec):
    name = "image"  # Use as <image> in definitions

    def get_dtype(self, is_external: bool) -> str:
        return "<blob>"  # Underlying storage type

    def encode(self, img, *, key=None, store_name=None):
        return cv2.imencode('.png', img)[1].tobytes()

    def decode(self, data, *, key=None):
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

# No registration needed—Codec auto-registers when class is defined
```

### Key Changes

| 0.x `AttributeAdapter` | 2.0 `Codec` |
|------------------------|-------------|
| `attribute_type` property | `get_dtype(is_external)` method |
| `put(value)` method | `encode(value, *, key=None, store_name=None)` method |
| `get(data)` method | `decode(data, *, key=None)` method |
| Instance-based, manual registration | Class-based, auto-registration |
| Single underlying type | Can vary based on `is_external` parameter |

### New Capabilities in Codecs

The 2.0 Codec system provides features not available in 0.x:

1. **Context-aware encoding**: `key` parameter provides primary key values
2. **Store-aware encoding**: `store_name` parameter for external storage
3. **Conditional storage**: `get_dtype()` can return different types for internal vs external
4. **Validation hook**: Optional `validate()` method for pre-insertion checks
5. **Entry point plugins**: Codecs can be distributed as installable packages

### Migration Actions

1. **Identify all `AttributeAdapter` subclasses** in your codebase:
   ```bash
   grep -rn "class.*AttributeAdapter" --include="*.py"
   grep -rn "dj.AttributeAdapter" --include="*.py"
   ```

2. **Convert each adapter to a Codec**:
   - Add `name` class attribute (the name used in `<name>` syntax)
   - Rename `attribute_type` → `get_dtype()` method
   - Rename `put()` → `encode()` with new signature
   - Rename `get()` → `decode()` with new signature
   - Optionally add `validate()` method

3. **Update table definitions**:
   - Change type references if adapter names changed
   - Ensure column comments use 2.0 format

4. **Remove adapter registration**:
   - Remove adapter instances from `spawn_missing_classes()` context
   - Ensure codec module is imported before table definitions

5. **Update column comments** (database):
   ```sql
   -- Update comment to reflect new codec name if changed
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` LONGBLOB COMMENT ':newcodec: description';
   ```

### Reversibility

This step is **reversible**:
- Codec classes can coexist with AttributeAdapter classes during transition
- Column comments can be reverted to 0.x format
- Data is unchanged (only serialization interface changes)
- DataJoint 0.x continues to work if adapters are restored

### Example Migration

**Before (0.x):**
```python
# adapters.py
class GraphAdapter(dj.AttributeAdapter):
    attribute_type = 'longblob'

    def put(self, graph):
        return pickle.dumps(graph)

    def get(self, data):
        return pickle.loads(data)

# schema.py
graph_adapter = GraphAdapter()
schema.spawn_missing_classes(context={'graph': graph_adapter})

@schema
class Networks(dj.Manual):
    definition = '''
    network_id : int
    ---
    topology : <graph>
    '''
```

**After (2.0):**
```python
# codecs.py
class GraphCodec(dj.Codec):
    name = "graph"

    def get_dtype(self, is_external: bool) -> str:
        return "<blob>"

    def encode(self, graph, *, key=None, store_name=None):
        return pickle.dumps(graph)

    def decode(self, data, *, key=None):
        return pickle.loads(data)

# schema.py
import codecs  # Ensure codec is registered before table definition

@schema
class Networks(dj.Manual):
    definition = '''
    network_id : int32
    ---
    topology : <graph>
    '''
```

---

## AI-Assisted Migration

The migration process is optimized for execution by AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.). This section provides detailed prompts for each phase of the migration.

### Safety Features

All prompts are designed with safety in mind:

- **Dry-run by default:** Analysis phases (1-2) make no changes
- **Confirmation required:** All modification phases show changes before executing
- **Idempotent:** Safe to re-run any phase; already-migrated items are skipped
- **Staged execution:** Reversible steps (0-3, 6) can run separately from irreversible steps (4-5)
- **Backup verification:** Phase 2 explicitly verifies backups before any changes

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

   Find external columns using 0.x comment patterns:
   - COLUMN_COMMENT LIKE '%:external:%'          -> blob, default store
   - COLUMN_COMMENT LIKE '%:external-%'          -> blob, named store
   - COLUMN_COMMENT LIKE '%:external-attach:%'   -> attachment, default store
   - COLUMN_COMMENT LIKE '%:external-attach-%'   -> attachment, named store

   For each external column in user tables:
     - Column type should be BINARY(16) (UUID hash)
     - Count rows with external references
     - Verify referenced hashes exist in ~external_<store> table
     - Check if external files are accessible in storage

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

This phase is IDEMPOTENT - safe to run multiple times.

1. CHECK EXISTING 2.0 CONFIGURATION
   - If datajoint.json exists, read and validate it
   - If .secrets/ exists, verify contents
   - Report: "2.0 config already exists" or "needs migration"

2. READ CURRENT CONFIGURATION (if migration needed)
   - Load dj_local_conf.json if exists
   - Read dj.config programmatically
   - Check for DJ_* environment variables

3. CREATE OR UPDATE datajoint.json
   - If file exists, MERGE new settings (don't overwrite)
   - If file doesn't exist, create with structure:
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

4. CREATE .secrets/ DIRECTORY (if not exists)
   - Skip if .secrets/database.user already exists
   - Skip if .secrets/database.password already exists
   - Only create missing files
   - Set permissions: chmod 600 .secrets/*

5. UPDATE .gitignore (idempotent)
   - Check if entries already exist before adding
   - Add only if not present:
   .secrets/
   datajoint.json

6. VERIFY CONFIGURATION
   - Test connection with DataJoint 2.0
   - Verify all stores are accessible

Report what was created vs what was skipped (already existed).
```

---

### Phase 4: Core Type Migration

Add type labels to numeric and string columns:

```
Migrate core data types for schema [schema_name].

This phase is IDEMPOTENT - safe to run multiple times.

For each table in the schema:

1. QUERY COLUMN INFORMATION
   SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, COLUMN_COMMENT
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '[schema_name]' AND TABLE_NAME = '[table_name]'

2. CHECK IF ALREADY MIGRATED
   Skip columns where COLUMN_COMMENT already starts with a type label:
   - REGEXP '^:(int8|uint8|int16|uint16|int32|uint32|int64|uint64|float32|float64|bool):'

   Report: "Column X already has type label, skipping"

3. DETERMINE 2.0 TYPE LABELS (for unmigrated columns only)
   Map MySQL types to DataJoint 2.0 labels:
   - TINYINT -> :int8: (or :uint8: if unsigned)
   - SMALLINT -> :int16: (or :uint16: if unsigned)
   - INT -> :int32: (or :uint32: if unsigned)
   - BIGINT -> :int64: (or :uint64: if unsigned)
   - FLOAT -> :float32:
   - DOUBLE -> :float64:
   - TINYINT(1) -> :bool:

4. GENERATE ALTER STATEMENTS (only for columns needing migration)
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` [TYPE] COMMENT ':type_label: original comment';

5. EXECUTE WITH VERIFICATION
   - Run each ALTER statement
   - Verify column comment was updated
   - Log success/failure

6. SUMMARY REPORT
   - Columns migrated: X
   - Columns skipped (already migrated): Y
   - Columns skipped (not applicable): Z
   - Errors: N

Generate and show me all ALTER statements before executing.
Re-running this phase will skip already-migrated columns.
```

---

### Phase 5: Blob Codec Migration

Mark blob columns with the <blob> codec:

```
Migrate internal blob columns for schema [schema_name].

This phase is IDEMPOTENT - safe to run multiple times.

1. IDENTIFY BLOB COLUMNS NEEDING MIGRATION
   Find LONGBLOB columns that are NOT already migrated:
   SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = '[schema_name]'
     AND DATA_TYPE = 'longblob'
     AND COLUMN_COMMENT NOT LIKE ':blob:%'      -- not already internal blob
     AND COLUMN_COMMENT NOT LIKE ':blob@%'      -- not external blob
     AND COLUMN_COMMENT NOT LIKE ':attach:%'    -- not internal attachment
     AND COLUMN_COMMENT NOT LIKE ':attach@%'    -- not external attachment

2. CHECK ALREADY MIGRATED
   Report columns that already have codec markers:
   - ":blob: ..." -> "Already migrated as internal blob"
   - ":blob@store: ..." -> "Already migrated as external blob"
   - ":attach: ..." -> "Already migrated as internal attachment"

3. GENERATE ALTER STATEMENTS (only for unmigrated columns)
   For each blob column needing migration:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` LONGBLOB COMMENT ':blob: original comment';

4. EXECUTE AND VERIFY
   - Run each ALTER statement
   - Verify data is still readable (fetch one row)
   - Log success/failure

5. SUMMARY REPORT
   - Columns migrated: X
   - Columns skipped (already have :blob:): Y
   - Columns skipped (external storage): Z
   - Errors: N

Show all ALTER statements for review before executing.
Re-running this phase will skip already-migrated columns.
```

---

### Phase 6: External Storage Migration (IRREVERSIBLE)

**This step cannot be undone. Confirm backups before proceeding.**

```
Migrate external storage for schema [schema_name].

This phase is IDEMPOTENT - safe to run multiple times (skips already-migrated data).
However, the changes are IRREVERSIBLE for DataJoint 0.14 compatibility.

WARNING: Confirm before proceeding:
- [ ] Database backup verified
- [ ] External storage backup verified
- [ ] All pipelines stopped
- [ ] Team notified of downtime

For each table with external columns:

1. IDENTIFY COLUMN MIGRATION STATE
   Check each potential external column using 0.x comment patterns:

   0.x EXTERNAL COLUMN COMMENT PATTERNS:
   - ':external:'           -> External blob (default store)
   - ':external-<store>:'   -> External blob (named store, e.g., ':external-s3data:')
   - ':external-attach:'    -> External attachment (default store)
   - ':external-attach-<store>:' -> External attachment (named store)

   a. Already migrated (JSON type with 2.0 codec comment):
      - DATA_TYPE = 'json'
      - COLUMN_COMMENT LIKE ':blob@%' OR COLUMN_COMMENT LIKE ':attach@%'
      -> Report "Already migrated" and SKIP

   b. Needs migration (BINARY uuid type with 0.x :external: pattern):
      - DATA_TYPE = 'binary' AND CHARACTER_MAXIMUM_LENGTH = 16
      - COLUMN_COMMENT matches one of the 0.x patterns above
      -> Include in migration

   c. Partially migrated (JSON type but old 0.x comment):
      - DATA_TYPE = 'json'
      - COLUMN_COMMENT still has ':external' pattern (not ':blob@' or ':attach@')
      -> Only update comment, skip data migration

2. GET STORE INFORMATION
   For columns needing migration, identify the store name from the comment

3. CHECK ROW MIGRATION STATE
   For each row, determine if already migrated:

   -- Row needs migration if column value is BINARY (uuid hash)
   -- Row already migrated if column value is valid JSON

   SELECT COUNT(*) as needs_migration
   FROM `table`
   WHERE `column` IS NOT NULL
     AND JSON_VALID(`column`) = 0;  -- Not valid JSON = needs migration

   SELECT COUNT(*) as already_migrated
   FROM `table`
   WHERE `column` IS NOT NULL
     AND JSON_VALID(`column`) = 1;  -- Valid JSON = already done

4. BUILD MIGRATION QUERY (only for unmigrated rows)
   For each row where JSON_VALID(`column`) = 0:

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

5. ALTER COLUMN TYPE (if not already JSON)
   Only if DATA_TYPE != 'json':
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` JSON COMMENT ':blob@[store]: original comment';

6. UPDATE UNMIGRATED ROWS ONLY
   UPDATE `schema`.`table`
   SET `column` = '[json_object]'
   WHERE [primary_key_condition]
     AND JSON_VALID(`column`) = 0;  -- Only update non-JSON values

7. UPDATE COMMENT (if not already updated)
   Only if comment doesn't have correct format:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` JSON COMMENT ':blob@[store]: original comment';

8. VERIFY MIGRATION
   - Count rows with valid JSON values
   - Verify JSON structure contains required fields
   - Test fetching data through DataJoint 2.0

9. SUMMARY REPORT
   - Columns migrated: X
   - Columns skipped (already JSON): Y
   - Rows migrated: N
   - Rows skipped (already JSON): M
   - Errors: E

10. OPTIONAL: DROP HIDDEN TABLES
    After verification, optionally remove:
    DROP TABLE `~external_[store]`;

Show me the migration plan with row counts before executing.
Pause for confirmation before each table.
Re-running this phase will skip already-migrated columns and rows.
```

---

### Phase 7: AdaptedTypes Migration

Convert custom AttributeAdapter classes to Codecs:

```
Migrate AttributeAdapter classes to Codecs for this project.

This phase is IDEMPOTENT - safe to run multiple times.
This phase requires CODE CHANGES in addition to database changes.

1. IDENTIFY ATTRIBUTEADAPTERS
   Search for all AttributeAdapter subclasses:

   grep -rn "class.*AttributeAdapter" --include="*.py"
   grep -rn "dj.AttributeAdapter" --include="*.py"

   For each adapter found, document:
   - Class name
   - attribute_type value
   - put() implementation
   - get() implementation
   - Where it's registered (spawn_missing_classes calls)

2. CREATE EQUIVALENT CODEC CLASSES
   For each AttributeAdapter, create a Codec class:

   # Original adapter
   class MyAdapter(dj.AttributeAdapter):
       attribute_type = 'longblob'
       def put(self, value): ...
       def get(self, data): ...

   # Equivalent codec
   class MyCodec(dj.Codec):
       name = "myadapter"  # Same name used in <myadapter> syntax

       def get_dtype(self, is_external: bool) -> str:
           return "<blob>"  # Map attribute_type to 2.0 type

       def encode(self, value, *, key=None, store_name=None):
           # Same logic as put()
           ...

       def decode(self, data, *, key=None):
           # Same logic as get()
           ...

3. TYPE MAPPING FOR get_dtype()
   Convert attribute_type to 2.0 return values:

   | 0.x attribute_type | 2.0 get_dtype() return |
   |--------------------|------------------------|
   | 'longblob'         | '<blob>'               |
   | 'blob'             | '<blob>'               |
   | 'attach'           | '<attach>'             |
   | 'blob@store'       | '<blob>' (+ @store)    |
   | 'attach@store'     | '<attach>' (+ @store)  |
   | 'filepath@store'   | '<filepath>'           |
   | 'varchar(N)'       | 'varchar(N)'           |
   | 'json'             | 'json'                 |

4. UPDATE TABLE DEFINITIONS
   - Ensure codec name matches what's used in table definitions
   - Update any type references if names changed
   - Update numeric types (int -> int32, etc.)

5. UPDATE SCHEMA MODULES
   - Remove adapter instances from spawn_missing_classes() context
   - Import codec module before table definitions
   - Verify codecs auto-register when class is defined

6. UPDATE COLUMN COMMENTS (if codec name changed)
   If the adapter name differs from the new codec name:

   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` LONGBLOB COMMENT ':newcodec: description';

7. TEST ROUND-TRIP
   For each migrated codec:
   - Insert a test row with codec data
   - Fetch the row and verify data matches
   - Delete test row

8. SUMMARY REPORT
   - Adapters found: X
   - Codecs created: Y
   - Tables updated: Z
   - Column comments modified: N

Show the adapter-to-codec mapping before making changes.
Test each codec round-trip before proceeding to next.
```

---

### Phase 8: Validation

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
4. [ ] All custom codecs working (if migrated from AttributeAdapters)
5. [ ] Computed tables can populate new data
6. [ ] Job tables functioning (if used)
7. [ ] All team members updated to DataJoint 2.0
8. [ ] CI/CD pipelines updated
9. [ ] Documentation updated with new connection info
10. [ ] Old dj_local_conf.json archived/removed
11. [ ] Old AttributeAdapter code archived/removed (if applicable)
12. [ ] Monitoring in place for any issues

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

### Reversible Steps (0-3, 6): Safe Rollback

If you need to revert steps 0-3 or 6 (settings, core types, internal blobs, internal attachments, adapted types):

**Step 0 (Settings):**
```bash
# Restore original configuration
cp dj_local_conf.json.backup dj_local_conf.json
rm datajoint.json
rm -rf .secrets/
```

**Steps 1-3 (Column Comments):**
Column comment changes can be reverted with SQL:

```sql
-- Remove type label prefix from comment
-- Before: ':int32: original comment'
-- After:  'original comment'

ALTER TABLE `schema`.`table`
MODIFY COLUMN `column` INT NOT NULL
COMMENT 'original comment';  -- without :int32: prefix
```

**Batch rollback script** (for AI assistant):
```
Revert column comment migration for schema [schema_name].

For each table, query current column comments and remove 2.0 type labels:
- Remove leading ':int8:', ':uint8:', ':int16:', etc. for numeric types
- Remove leading ':blob:' for internal blobs
- Remove leading ':attach:' for internal attachments

Generate ALTER statements to restore original comments.
Execute only after confirmation.
```

**Step 6 (AdaptedTypes to Codecs):**
To revert adapter-to-codec migration:

1. **Restore AttributeAdapter classes** from version control
2. **Re-register adapters** in `spawn_missing_classes()` context
3. **Revert column comments** if codec names changed:
   ```sql
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `column` LONGBLOB COMMENT ':oldadapter: description';
   ```
4. **Remove Codec classes** or keep both (they can coexist)

Note: Data is unchanged during Step 6. The only changes are:
- Python code (adapters ↔ codecs)
- Column comments (adapter name ↔ codec name)

### Irreversible Steps (4-5): Backup Required

**External storage cannot be rolled back.** Once external object references are migrated from hidden tables to JSON fields:
- The hidden `~external_*` tables are no longer updated
- DataJoint 0.14 cannot read the JSON field format
- Reverting requires restoring from database backup

**Before running steps 4-5:**
```bash
# Create full backup
mysqldump --single-transaction --routines --triggers \
  -u root -p my_schema > my_schema_backup.sql

# Backup external storage
rsync -av /data/external/ /backup/external/
```

**Recommendation:** Test migration on a copy of your database before running on production.

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
        tbl.to_dicts(limit=1)
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
