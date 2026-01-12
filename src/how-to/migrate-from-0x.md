# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

> **This guide is optimized for AI coding assistants.** Point your AI agent at this
> URL and it will execute the migration with your oversight.

## Quick Start

Create a `CLAUDE.md` (or similar) file in your project:

```markdown
# DataJoint Migration

Read the migration guide: https://datajoint.com/docs/how-to/migrate-from-0x/

Database: [host] / [schema1, schema2, ...]
```

Then tell your AI assistant:

```
Migrate my DataJoint pipeline from 0.x to 2.0.
Fetch the migration guide and create a plan for my project.
```

---

## Why Migrate?

| Improvement | Before (0.x) | After (2.0) |
|-------------|--------------|-------------|
| **Transparency** | Hidden tables, implicit serialization | Everything visible, explicit codecs |
| **Extensibility** | Fixed blob/attachment types | Custom codecs for any data type |
| **Type Safety** | Types inferred at runtime | Explicit type labels in schema |
| **External Storage** | UUID in hidden tables | Inline JSON with direct URLs |
| **Configuration** | Python dict, credentials in code | JSON config, secrets separated |
| **Data Retrieval** | `.fetch()` with options | Explicit: `.to_dicts()`, `.to_pandas()` |

---

## Migration Phases

| Phase | What | Changes |
|-------|------|---------|
| 1 | Code & Definitions | Python code, table definitions |
| 2 | Settings | Config files |
| 3 | Numeric Types | Column comments (database) |
| 4 | Internal Blobs | Column comments (database) |
| 5 | External Storage | Column type + data (FK → JSON) |
| 6 | Filepath | Column type + data (FK → JSON) |
| 7 | AdaptedTypes | Code + column comments |

**Phases 1-4, 7**: Only modify code and column comments. Data unchanged.

**Phases 5-6**: Convert external storage references from hidden tables to JSON.
Requires matching store configuration to preserve path compatibility.

Most pipelines only need Phases 1-4.

---

## Phase 1: Code & Definitions

Update Python code and table definitions. No database changes.

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

Search the codebase for:
1. .fetch('KEY') → replace with .keys()
2. .fetch(as_dict=True) → replace with .to_dicts()
3. .fetch(format='frame') → replace with .to_pandas()
4. Table definitions with native types (int, float, smallint, etc.)
   → replace with core types (int32, float64, int16, etc.)
5. Table definitions with longblob → replace with <blob>

Show changes before applying.
```

---

## Phase 2: Settings

Update configuration files.

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
5. Verify connection works with new config
```

---

## Phase 3: Numeric Types (Database)

Add type labels to column comments. Data and column types unchanged.

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
Migrate numeric types for schema [schema_name].

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
```

---

## Phase 4: Internal Blobs (Database)

Add codec labels to blob columns. Data unchanged.

### How It Works

```sql
-- 0.x: No codec label
data_col LONGBLOB COMMENT 'neural data'

-- 2.0: Codec label prefix
data_col LONGBLOB COMMENT ':blob: neural data'
```

### AI Prompt: Blob Migration

```
Migrate internal blob columns for schema [schema_name].

1. Find LONGBLOB columns without codec labels:
   - Skip if comment starts with :blob:, :attach:, :blob@, :attach@

2. Generate ALTER statements:
   ALTER TABLE `schema`.`table`
   MODIFY COLUMN `col` LONGBLOB COMMENT ':blob: original comment';

3. Show all statements before executing
```

---

## Phase 5: External Storage (Database)

Convert external blob/attachment references from hidden tables to JSON.

**This changes column types and data format.**

### 0.x Architecture

- Column type: `BINARY(16)` storing UUID hash
- Column comment: `description :external:` or `:external-storename:`
- Hidden table `~external_<store>` maps hash → filepath, size, timestamp

### 2.0 Architecture

- Column type: `JSON`
- Column comment: `:blob@store: description`
- JSON value: `{"url": "...", "size": ..., "hash": "..."}`

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
Migrate external storage for schema [schema_name].

WARNING: This changes column types. Back up first.

1. Find external columns:
   - DATA_TYPE = 'binary', length = 16
   - COMMENT matches ':external:' or ':external-*:'

2. For each external column:
   a. Identify store name from comment
   b. Query ~external_<store> for all referenced hashes
   c. Build JSON objects:
      {"url": "<protocol>://<location>/<filepath>", "size": N, "hash": "..."}
   d. For attachments, include "filename" field

3. ALTER column type to JSON:
   ALTER TABLE `t` MODIFY COLUMN `c` JSON COMMENT ':blob@store: desc';

4. UPDATE each row with JSON value

5. Verify data accessible through DataJoint 2.0

Show migration plan with row counts before executing.
```

---

## Phase 6: Filepath (Database)

Convert filepath references to JSON format. Similar to Phase 5.

### AI Prompt: Filepath Migration

```
Migrate filepath columns for schema [schema_name].

1. Find filepath columns (comment contains :filepath:)
2. Convert paths to JSON with URL format
3. ALTER column type to JSON
4. Verify file accessibility
```

---

## Phase 7: AdaptedTypes to Codecs

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
Validate DataJoint 2.0 migration for schema [schema_name].

1. Connect with DataJoint 2.0
2. For each table:
   - Verify heading loads without errors
   - Fetch sample rows
   - For blob columns: verify deserialization
   - For external columns: verify file retrieval
3. Test populate() on computed tables
4. Report any errors
```

---

## Post-Migration Checklist

```
[ ] All tables accessible via DataJoint 2.0
[ ] Blob data deserializes correctly
[ ] External data retrieves correctly
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

Phase 5/6: Store paths don't match legacy paths. Check:
1. Store location in datajoint.json matches original
2. Path structure matches what's in `~external_*` table

### "Unknown codec"

Ensure Codec class is imported before table definitions.
Codecs auto-register when the class is defined.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Codec API](../reference/specs/codec-api.md)
- [Configure Storage](configure-storage.md)
