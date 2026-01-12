# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

> **This guide is optimized for AI coding assistants.** Point your AI agent at this
> URL and it will execute the migration with your oversight.

## Quick Start

Create a `CLAUDE.md` (or similar) file in your project:

```markdown
# DataJoint Migration

Read the migration guide: https://datajoint.com/docs/how-to/migrate-from-0x/

Schemas in topological order (dependencies first):
1. lab
2. subject
3. session
4. ephys
```

Then tell your AI assistant:

```
Migrate my DataJoint pipeline from 0.x to 2.0.
Fetch the migration guide and create a plan for my project.
```

---

## Migration Phases

| Phase | What | Changes | Risk |
|-------|------|---------|------|
| 1 | Settings | Config files | None |
| 2 | Code & Definitions | Python code, table definitions | None |
| 3 | Numeric Types | Column comments | None |
| 4 | Internal Blobs | Column comments | None |
| 5 | Lineage Table | Create `~lineage` table | None |
| 6 | External Storage | Add new JSON columns | **Data** |
| 7 | Filepath | Add new JSON columns | **Data** |
| 8 | AdaptedTypes | Code + column comments | None |

**Phases 1-5, 8**: No risk of data loss. Only modify code, config, and column comments.

**Phases 6-7**: Risk of data loss. These phases add **new columns** alongside existing
ones, allowing 0.x and 2.0 to coexist during migration. After verification, drop the
old columns.

**Process each schema in topological order** (dependencies before dependents).

Most pipelines only need Phases 1-5.

---

## Phase 1: Settings

Update configuration files first, then verify the connection works.

### 0.x Configuration

```python
dj.config['database.host'] = 'localhost'
dj.config['database.user'] = 'root'
dj.config['database.password'] = 'secret'
dj.config['stores'] = {'external': {'protocol': 'file', 'location': '/data'}}
```

### 2.0 Configuration

**datajoint.json:**
```json
{
  "database.host": "localhost",
  "stores": {
    "external": {
      "protocol": "file",
      "location": "/data"
    }
  }
}
```

**.secrets/database.password:**
```
secret
```

### AI Prompt: Settings Migration

```
Migrate DataJoint configuration to 2.0 format.

1. Read existing dj_local_conf.json or dj.config settings
2. Create datajoint.json with non-sensitive settings
3. Create .secrets/ directory with credentials (chmod 600)
4. Add .secrets/ and datajoint.json to .gitignore
5. Test connection with DataJoint 2.0:
   import datajoint as dj
   dj.conn()  # Should connect successfully

Verify connection works before proceeding to Phase 2.
```

---

## Phase 2: Code & Definitions

Update Python code and table definitions. No database changes.

**Process each schema module in topological order** (dependencies first).

### API Changes

| 0.x | 2.0 |
|-----|-----|
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |
| `.fetch(format='frame')` | `.to_pandas()` |

### Type Names in Definitions

```python
# 0.x
@schema
class Session(dj.Manual):
    definition = """
    session_id : int unsigned
    ---
    weight : float
    data : longblob
    """

# 2.0
@schema
class Session(dj.Manual):
    definition = """
    session_id : uint32
    ---
    weight : float64
    data : <blob>
    """
```

### Complete Type Mapping

| 0.x (native) | 2.0 (core type) |
|--------------|-----------------|
| `int` | `int32` |
| `int unsigned` | `uint32` |
| `smallint` | `int16` |
| `smallint unsigned` | `uint16` |
| `tinyint` | `int8` |
| `tinyint unsigned` | `uint8` |
| `bigint` | `int64` |
| `bigint unsigned` | `uint64` |
| `float` | `float32` |
| `double` | `float64` |
| `tinyint(1)` | `bool` |
| `longblob` | `<blob>` |
| `attach` | `<attach>` |
| `blob@store` | `<blob@store>` |
| `attach@store` | `<attach@store>` |
| `filepath@store` | `<filepath@store>` |

### AI Prompt: Code Migration

```
Migrate Python code for DataJoint 2.0.

Process schema modules in topological order (dependencies first).

For each module:
1. .fetch('KEY') → replace with .keys()
2. .fetch(as_dict=True) → replace with .to_dicts()
3. .fetch(format='frame') → replace with .to_pandas()
4. Table definitions with native types (int, float, smallint, etc.)
   → replace with core types (int32, float64, int16, etc.)
5. Table definitions with longblob → replace with <blob>

Show changes before applying.
```

---

## Phase 3: Numeric Types (Database)

Add type labels to column comments. Data and column types unchanged.

**Process each schema in topological order.**

### How It Works

DataJoint 2.0 stores type information in column comments:

```sql
-- 0.x: No type label
column_name INT COMMENT 'session number'

-- 2.0: Type label prefix
column_name INT COMMENT ':int32: session number'
```

### AI Prompt: Numeric Type Migration

```
Migrate numeric types for each schema in topological order.

For schema [schema_name]:

1. Query INFORMATION_SCHEMA.COLUMNS for all tables
2. For each numeric column without type label:
   - TINYINT → :int8: (or :uint8: if unsigned)
   - SMALLINT → :int16: (or :uint16: if unsigned)
   - INT → :int32: (or :uint32: if unsigned)
   - BIGINT → :int64: (or :uint64: if unsigned)
   - FLOAT → :float32:
   - DOUBLE → :float64:
   - TINYINT(1) → :bool:

3. Generate ALTER TABLE statements:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `col` INT COMMENT ':int32: original comment';

4. Show all statements before executing
5. Skip columns that already have type labels

Process schemas in order: [list schemas]
```

---

## Phase 4: Internal Blobs (Database)

Add codec labels to blob columns. Data unchanged.

**Process each schema in topological order.**

### How It Works

```sql
-- 0.x: No codec label
data_col LONGBLOB COMMENT 'neural data'

-- 2.0: Codec label prefix
data_col LONGBLOB COMMENT ':blob: neural data'
```

### AI Prompt: Blob Migration

```
Migrate internal blob columns for each schema in topological order.

For schema [schema_name]:

1. Find LONGBLOB columns without codec labels:
   - Skip if comment starts with :blob:, :attach:, :blob@, :attach@

2. Generate ALTER statements:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `col` LONGBLOB COMMENT ':blob: original comment';

3. Show all statements before executing

Process schemas in order: [list schemas]
```

---

## Phase 5: Lineage Table

Create the `~lineage` table to track data provenance in each schema.

**Process each schema in topological order.**

### What It Does

DataJoint 2.0 uses a `~lineage` table to track which rows in parent tables
contributed to each row in child tables. This enables precise dependency
tracking for deletions and recomputation.

### AI Prompt: Lineage Table Creation

```
Create lineage tables for each schema in topological order.

For schema [schema_name]:

1. Check if ~lineage table already exists:
   SHOW TABLES LIKE '~lineage';

2. If not exists, create it:
   CREATE TABLE `schema`.`~lineage` (
     `master` varchar(255) NOT NULL COMMENT ':varchar(255): master table',
     `master_hash` binary(16) NOT NULL COMMENT ':hash: master row hash',
     `child` varchar(255) NOT NULL COMMENT ':varchar(255): child table',
     `child_hash` binary(16) NOT NULL COMMENT ':hash: child row hash',
     PRIMARY KEY (`master`, `master_hash`, `child`, `child_hash`),
     KEY `child_idx` (`child`, `child_hash`)
   ) ENGINE=InnoDB;

3. Verify table was created

Process schemas in order: [list schemas]
```

---

## Phase 6: External Storage (Database)

Migrate external blob/attachment references from hidden tables to JSON.

**This is the only phase with risk of data loss.** The migration adds new columns
alongside existing ones, allowing 0.x and 2.0 to coexist until you verify the
migration succeeded.

**Process each schema in topological order.**

### 0.x Architecture

- Column type: `BINARY(16)` storing UUID hash
- Column comment: `description :external:` or `:external-storename:`
- Hidden table `~external_<store>` maps hash → filepath, size, timestamp

### 2.0 Architecture

- Column type: `JSON`
- Column comment: `:blob@store: description`
- JSON value: `{"url": "...", "size": ..., "hash": "..."}`

### Migration Strategy: New Columns

Instead of modifying existing columns (risking data loss), the migration:

1. **Adds a new column** `<name>_v2` with JSON type for 2.0
2. **Copies data** from the old column to the new column, converting format
3. **Verifies** all data is accessible via 2.0
4. **After verification**, you rename columns and drop the old one

This allows rolling back if issues are discovered.

### Using the Migration Module

```python
from datajoint.migrate import migrate_external

# Preview what will be migrated
migrate_external(schema, dry_run=True)

# Run migration (adds new columns, copies data)
migrate_external(schema)

# After verification, finalize (rename columns, drop old)
migrate_external(schema, finalize=True)
```

### 0.x Comment Patterns

| Pattern | Meaning |
|---------|---------|
| `:external:` | External blob, default store |
| `:external-storename:` | External blob, named store |
| `:external-attach:` | External attachment, default store |
| `:external-attach-storename:` | External attachment, named store |

### Critical: Path Compatibility

The 2.0 store configuration must generate the **same paths** as stored in the
legacy `~external_*` tables. Verify before migrating:

```python
# Check existing paths in hidden table
from your_pipeline import schema
external = schema.external['store']
print(external.fetch(limit=5))  # Note the filepath structure
```

### AI Prompt: External Storage Migration

```
Migrate external storage for each schema in topological order.

Use the datajoint.migrate module:

from datajoint.migrate import migrate_external

For each schema:
1. migrate_external(schema, dry_run=True)  # Preview
2. migrate_external(schema)                 # Add new columns, copy data
3. Verify data accessible via DataJoint 2.0
4. migrate_external(schema, finalize=True)  # Rename and drop old columns

Process schemas in order: [list schemas]
```

---

## Phase 7: Filepath (Database)

Migrate filepath references to JSON format. Same strategy as Phase 6.

**Process each schema in topological order.**

### Using the Migration Module

```python
from datajoint.migrate import migrate_filepath

# Preview what will be migrated
migrate_filepath(schema, dry_run=True)

# Run migration (adds new columns, copies data)
migrate_filepath(schema)

# After verification, finalize (rename columns, drop old)
migrate_filepath(schema, finalize=True)
```

### AI Prompt: Filepath Migration

```
Migrate filepath columns for each schema in topological order.

Use the datajoint.migrate module:

from datajoint.migrate import migrate_filepath

For each schema:
1. migrate_filepath(schema, dry_run=True)  # Preview
2. migrate_filepath(schema)                 # Add new columns, copy data
3. Verify files accessible via DataJoint 2.0
4. migrate_filepath(schema, finalize=True)  # Rename and drop old columns

Process schemas in order: [list schemas]
```

---

## Phase 8: AdaptedTypes to Codecs

Convert custom `AttributeAdapter` classes to `Codec` classes.

### 0.x AttributeAdapter

```python
class ImageAdapter(dj.AttributeAdapter):
    attribute_type = 'longblob'

    def put(self, img):
        return cv2.imencode('.png', img)[1].tobytes()

    def get(self, data):
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

# Registration required
image_adapter = ImageAdapter()
schema.spawn_missing_classes(context={'image': image_adapter})
```

### 2.0 Codec

```python
class ImageCodec(dj.Codec):
    name = "image"  # Use as <image> in definitions

    def get_dtype(self, is_external: bool) -> str:
        return "<blob>"

    def encode(self, img, *, key=None, store_name=None):
        return cv2.imencode('.png', img)[1].tobytes()

    def decode(self, data, *, key=None):
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

# Auto-registers when class is defined
```

### Conversion Table

| 0.x | 2.0 |
|-----|-----|
| `attribute_type` property | `get_dtype(is_external)` method |
| `put(value)` | `encode(value, *, key=None, store_name=None)` |
| `get(data)` | `decode(data, *, key=None)` |
| Manual registration | Auto-registration |

### attribute_type to get_dtype() Mapping

| 0.x `attribute_type` | 2.0 `get_dtype()` return |
|----------------------|--------------------------|
| `'longblob'` | `'<blob>'` |
| `'blob@store'` | `'<blob>'` (with @store in definition) |
| `'attach'` | `'<attach>'` |
| `'filepath@store'` | `'<filepath>'` |
| `'varchar(N)'` | `'varchar(N)'` |
| `'json'` | `'json'` |

### AI Prompt: AdaptedTypes Migration

```
Migrate AttributeAdapter classes to Codecs.

1. Search for AttributeAdapter subclasses:
   grep -rn "AttributeAdapter" --include="*.py"

2. For each adapter:
   - Create equivalent Codec class
   - Rename put() → encode(), get() → decode()
   - Replace attribute_type with get_dtype() method
   - Add name class attribute

3. Update table definitions if type names changed

4. Remove spawn_missing_classes() registrations

5. Ensure codec module is imported before table definitions

6. Test round-trip: insert, fetch, verify data matches
```

---

## Validation

After migration, verify everything works:

```python
import datajoint as dj

schema = dj.Schema('my_schema')

# Check all tables
for name in schema.list_tables():
    table = schema(name)
    print(f"{name}: {len(table)} rows")
    if len(table) > 0:
        table.to_dicts(limit=1)  # Verify fetch works
```

### AI Prompt: Validation

```
Validate DataJoint 2.0 migration for each schema in topological order.

For schema [schema_name]:

1. Connect with DataJoint 2.0
2. For each table:
   - Verify heading loads without errors
   - Fetch sample rows
   - For blob columns: verify deserialization
   - For external columns: verify file retrieval
3. Verify ~lineage table exists
4. Test populate() on computed tables
5. Report any errors

Process schemas in order: [list schemas]
```

---

## Post-Migration Checklist

```
[ ] All tables accessible via DataJoint 2.0
[ ] Blob data deserializes correctly
[ ] External data retrieves correctly
[ ] Lineage tables created in all schemas
[ ] Custom codecs working (if applicable)
[ ] Computed tables can populate
[ ] Team updated to DataJoint 2.0
[ ] CI/CD pipelines updated
[ ] Old config files archived
```

---

## Troubleshooting

### "Native type 'int' is used"

Run Phase 3 to add type labels to numeric columns.

### "No codec registered"

Run Phase 4 to add codec labels to blob columns.

### External data not found

Phase 6/7: Store paths don't match legacy paths. Check:
1. Store location in datajoint.json matches original
2. Path structure matches what's in `~external_*` table

### "Unknown codec"

Ensure Codec class is imported before table definitions.
Codecs auto-register when the class is defined.

### Missing ~lineage table

Run Phase 5 to create the lineage table.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Codec API](../reference/specs/codec-api.md)
- [Configure Storage](configure-storage.md)
