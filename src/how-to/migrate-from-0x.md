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
| 7. AdaptedTypes | Custom AttributeAdapter classes | Code + column comments | 100% |

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

### Key API Changes

| 0.x | 2.0 |
|-----|-----|
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |
| `.fetch(format='frame')` | `.to_pandas()` |

### AI-Assisted Code Conversion

We recommend using an AI coding assistant (Claude Code, Cursor, GitHub Copilot)
to identify and update deprecated patterns in your codebase:

```
Analyze my DataJoint pipeline code for 0.x patterns that need updating for 2.0.

Search for:
1. .fetch('KEY') calls — replace with .keys()
2. .fetch(as_dict=True) calls — replace with .to_dicts()
3. .fetch(format='frame') calls — replace with .to_pandas()
4. Any other deprecated fetch patterns

For each file, show me the changes needed before applying them.
```

### Manual Search

```bash
grep -rn "\.fetch('KEY')" --include="*.py"
grep -rn "fetch(as_dict=True)" --include="*.py"
grep -rn "fetch(format=" --include="*.py"
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

## Phase 7: AdaptedTypes to Codecs

Migrate custom `AttributeAdapter` classes to user-defined codecs.

**This phase requires updating Python code and column comments.**

### Background

DataJoint 0.x used `dj.AttributeAdapter` subclasses to define custom attribute
types. In 2.0, this is replaced by the more powerful `dj.Codec` system.

### Definition Changes

```python
# 0.x — AttributeAdapter
@schema
class MyAdapter(dj.AttributeAdapter):
    attribute_type = 'filepath@store'  # underlying type

    def put(self, filepath):
        # transform on insert
        return filepath

    def get(self, filepath):
        # transform on fetch
        return pathlib.Path(filepath)

# Usage in 0.x
my_adapter = MyAdapter()
schema.spawn_missing_classes(context={..., 'adapted': my_adapter})

@schema
class MyTable(dj.Manual):
    definition = '''
    id : int
    ---
    path : <adapted>
    '''

# 2.0 — Codec
class PathCodec(dj.Codec):
    name = "path"

    def get_dtype(self, is_external: bool) -> str:
        return "<filepath>"  # underlying storage

    def encode(self, value, *, key=None, store_name=None):
        return str(value)

    def decode(self, stored, *, key=None):
        return pathlib.Path(stored)

# Usage in 2.0 — codec auto-registers when class is defined
@schema
class MyTable(dj.Manual):
    definition = '''
    id : int32
    ---
    path : <path@store>
    '''
```

### Key Differences

| 0.x AttributeAdapter | 2.0 Codec |
|---------------------|-----------|
| `attribute_type` property | `get_dtype(is_external)` method |
| `put()` method | `encode()` method |
| `get()` method | `decode()` method |
| Manual registration via context | Auto-registration on class definition |
| Instance-based | Class-based with singleton instance |

### Migration Steps

1. **Identify all AttributeAdapter subclasses** in your codebase

2. **Convert each to a Codec class**:
   - Rename `put()` → `encode()`
   - Rename `get()` → `decode()`
   - Replace `attribute_type` with `get_dtype()` method
   - Add `name` class attribute

3. **Update table definitions**:
   - Replace adapter references with codec names
   - Update column comments if needed

4. **Remove adapter registration** from `spawn_missing_classes()` calls

### Apply

```python
from datajoint.migrate import migrate_adapted_types

migrate_adapted_types(schema, dry_run=True)  # Preview
migrate_adapted_types(schema)                 # Apply
```

**Safe:** Only modifies column comments. Data unchanged. Requires code changes.

---

## Quick Reference

### Safe Phases (1-4, 7)

Phases 3-4 and 7 only modify column comments. Return to 0.x anytime.

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
| `.fetch('KEY')` | `.keys()` |
| `.fetch(as_dict=True)` | `.to_dicts()` |
| `.fetch(format='frame')` | `.to_pandas()` |

Use an AI coding assistant to find and update deprecated patterns.

### AdaptedTypes (Phase 7)

| 0.x | 2.0 |
|-----|-----|
| `dj.AttributeAdapter` | `dj.Codec` |
| `put()` method | `encode()` method |
| `get()` method | `decode()` method |
| `attribute_type` | `get_dtype()` method |

---

## Troubleshooting

### "Native type 'int' is used"

Run Phase 3 (numeric types).

### "No codec registered"

Run Phase 4 (blob/attach).

### External data not found

Phase 5/6: Store paths don't match legacy external table paths.
Verify configuration with `verify_external_paths()`.

### "Unknown codec" after Phase 7

Ensure your new Codec class is imported before table definitions.
Codecs auto-register when the class is defined.

### AttributeAdapter still referenced

Remove old adapter instances from `spawn_missing_classes()` context dicts.
Update table definitions to use new codec names.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Codec API](../reference/specs/codec-api.md)
- [Configure Storage](configure-storage.md)
