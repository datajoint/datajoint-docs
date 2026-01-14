# Object Store Configuration Specification

This specification defines DataJoint's unified object store system, including store configuration, path generation algorithms, and storage models.

## Overview

DataJoint's Object-Augmented Schema (OAS) integrates relational tables with object storage as a single coherent system. Large data objects are stored in file systems or cloud storage while maintaining full referential integrity with the relational database.

### Storage Models

DataJoint 2.0 supports three storage models, all sharing the same store configuration:

| Model | Data Types | Path Structure | Integration | Use Case |
|-------|------------|----------------|-------------|----------|
| **Hash-addressed** | `<blob@store>`, `<attach@store>` | Content-addressed by hash | **Integrated** (OAS) | Immutable data, automatic deduplication |
| **Schema-addressed** | `<object@store>`, `<npy@store>` | Key-based hierarchical paths | **Integrated** (OAS) | Mutable data, streaming access, arrays |
| **Filepath** | `<filepath@store>` | User-managed paths | **Reference** | User-managed files (no lifecycle management) |

**Key distinction:**
- **Hash-addressed** and **schema-addressed** storage are **integrated** into the Object-Augmented Schema. DataJoint manages their lifecycle, paths, integrity, garbage collection, transaction safety, and deduplication.
- **Filepath** storage stores only the path string. DataJoint provides no lifecycle management, garbage collection, transaction safety, or deduplication. Users control file creation, organization, and lifecycle.

**Legacy note:** DataJoint 0.14.x only supported hash-addressed (called "external") and filepath storage. Schema-addressed storage is new in 2.0.

## Store Configuration

### Minimal Configuration

Every store requires two fields:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/my-project"
    }
  }
}
```

This creates a store named `main` and designates it as the default.

### Default Store

DataJoint uses two default settings to reflect the architectural distinction between integrated and reference storage:

#### stores.default — Integrated Storage (OAS)

The `stores.default` setting determines which store is used for **integrated storage** (hash-addressed and schema-addressed) when no store is specified:

```python
# These are equivalent when stores.default = "main"
signal : <blob>           # Uses stores.default
signal : <blob@main>      # Explicitly names store

arrays : <object>         # Uses stores.default
arrays : <object@main>    # Explicitly names store
```

**Rules:**
- `stores.default` must be a string naming a configured store
- Required for `<blob>`, `<attach>`, `<object>`, `<npy>` without explicit `@store`
- Each project typically uses one primary store for integrated data

#### stores.filepath_default — Filepath References

The `stores.filepath_default` setting determines which store is used for **filepath references** when no store is specified:

```python
# These are equivalent when stores.filepath_default = "raw_data"
recording : <filepath@>          # Uses stores.filepath_default
recording : <filepath@raw_data>  # Explicitly names store
```

**Rules:**
- `stores.filepath_default` must be a string naming a configured store
- Required for `<filepath@>` without explicit store name
- Often configured differently from `stores.default` because filepath references are not part of OAS
- Users manage file lifecycle and organization

**Why separate defaults?**

Integrated storage (hash, schema) is managed by DataJoint as part of the Object-Augmented Schema—DataJoint controls paths, lifecycle, integrity, garbage collection, transaction safety, and deduplication. Filepath storage is user-managed—DataJoint only stores the path string and provides no lifecycle management, garbage collection, transaction safety, or deduplication. These are architecturally distinct, so they often use different storage locations and require separate defaults.

### Complete Store Configuration

A fully configured store specifying all sections:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "neuroscience-data",
      "location": "lab-project-2024",

      "hash_prefix": "blobs",
      "schema_prefix": "arrays",
      "filepath_prefix": "imported",

      "subfolding": [2, 2],
      "partition_pattern": "subject_id/session_date",
      "token_length": 8
    }
  }
}
```

### Section Prefixes

Each store is divided into sections controlled by prefix configuration:

| Prefix | Default | Controls | Used By |
|--------|---------|----------|---------|
| `hash_prefix` | `"_hash"` | Hash-addressed storage | `<blob@>`, `<attach@>` |
| `schema_prefix` | `"_schema"` | Schema-addressed storage | `<object@>`, `<npy@>` |
| `filepath_prefix` | `null` | Optional filepath restriction | `<filepath@>` |

**Validation rules:**
1. All prefixes must be mutually exclusive (no nesting)
2. `hash_prefix` and `schema_prefix` are reserved for DataJoint
3. `filepath_prefix` is optional:
   - `null` (default): filepaths can use any path except reserved sections
   - `"some/prefix"`: all filepaths must start with this prefix

**Example with custom prefixes:**

```json
{
  "hash_prefix": "content_addressed",
  "schema_prefix": "structured_data",
  "filepath_prefix": "user_files"
}
```

Results in these sections:
- `{location}/content_addressed/{schema}/{hash}` — hash-addressed
- `{location}/structured_data/{schema}/{table}/{key}/` — schema-addressed
- `{location}/user_files/{user_path}` — filepath (required prefix)

### Multiple Stores

Configure multiple stores for different data types or storage tiers:

```json
{
  "stores": {
    "default": "main",
    "filepath_default": "raw_data",
    "main": {
      "protocol": "file",
      "location": "/data/fast-storage",
      "hash_prefix": "blobs",
      "schema_prefix": "arrays"
    },
    "archive": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive-bucket",
      "location": "long-term-storage",
      "hash_prefix": "archived_blobs",
      "schema_prefix": "archived_arrays",
      "subfolding": [2, 2]
    },
    "raw_data": {
      "protocol": "file",
      "location": "/data/acquisition",
      "filepath_prefix": "recordings"
    }
  }
}
```

Use named stores in table definitions:

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    metadata     : <blob@main>          # Fast storage, hash-addressed
    raw_file     : <filepath@raw_data>  # Reference existing acquisition file
    processed    : <object@main>        # Fast storage, schema-addressed
    backup       : <blob@archive>       # Long-term storage
    """
```

## Secret Management

Store credentials separately from configuration files using the `.secrets/` directory.

### Secrets Directory Structure

```
project/
├── datajoint.json              # Non-sensitive configuration
└── .secrets/                   # Credentials (gitignored)
    ├── .gitignore              # Ensures secrets aren't committed
    ├── database.user
    ├── database.password
    ├── stores.main.access_key
    ├── stores.main.secret_key
    ├── stores.archive.access_key
    └── stores.archive.secret_key
```

### Configuration Priority

DataJoint loads configuration in this order (highest priority first):

1. **Environment variables**: `DJ_HOST`, `DJ_USER`, `DJ_PASS`
2. **Secrets directory**: `.secrets/database.user`, `.secrets/stores.main.access_key`
3. **Config file**: `datajoint.json`
4. **Defaults**: Built-in defaults

### Secrets File Format

Each secret file contains a single value (no quotes, no JSON):

```bash
# .secrets/database.password
my_secure_password
```

```bash
# .secrets/stores.main.access_key
AKIAIOSFODNN7EXAMPLE
```

### Per-Store Credentials

Store credentials use the naming pattern: `stores.<name>.<attribute>`

**S3 stores:**
```
.secrets/stores.main.access_key
.secrets/stores.main.secret_key
```

**GCS stores:**
```
.secrets/stores.gcs_store.token
```

**Azure stores:**
```
.secrets/stores.azure_store.account_key
```

### Setting Up Secrets

```bash
# Create secrets directory
mkdir .secrets
echo "*" > .secrets/.gitignore

# Add credentials (no quotes)
echo "analyst" > .secrets/database.user
echo "dbpass123" > .secrets/database.password
echo "AKIAIOSFODNN7EXAMPLE" > .secrets/stores.main.access_key
echo "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" > .secrets/stores.main.secret_key

# Verify .secrets/ is gitignored
git check-ignore .secrets/database.password  # Should output the path
```

### Template Generation

Generate configuration templates:

```python
import datajoint as dj

# Create config file
dj.config.save_template('datajoint.json')

# Create config + secrets directory with placeholders
dj.config.save_template('datajoint.json', create_secrets_dir=True)
```

## Path Generation

### Hash-Addressed Storage

**Data types:** `<blob@store>`, `<attach@store>`

**Path structure:**
```
{location}/{hash_prefix}/{schema_name}/{hash}[.ext]
```

**With subfolding `[2, 2]`:**
```
{location}/{hash_prefix}/{schema_name}/{h1}{h2}/{h3}{h4}/{hash}[.ext]
```

**Algorithm:**

1. Serialize value using codec-specific format
2. Compute Blake2b hash of serialized data
3. Encode hash as base32 (lowercase, no padding)
4. Apply subfolding if configured
5. Construct path: `{hash_prefix}/{schema}/{subfolded_hash}`
6. Store metadata in relational database as JSON

**Properties:**
- **Immutable**: Content defines path, cannot be changed
- **Deduplicated**: Identical content stored once
- **Integrity**: Hash validates content on retrieval

**Example:**

```python
# Table definition
@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : int
    ---
    data : <blob@main>
    """

# With config:
# hash_prefix = "blobs"
# location = "/data/store"
# subfolding = [2, 2]

# Insert
Experiment.insert1({'experiment_id': 1, 'data': my_data})

# Resulting path:
# /data/store/blobs/my_schema/ab/cd/abcdef123456...
```

### Schema-Addressed Storage

**Data types:** `<object@store>`, `<npy@store>`

**Path structure (no partitioning):**
```
{location}/{schema_prefix}/{schema_name}/{table_name}/{key_string}/{field_name}.{token}.{ext}
```

**With partitioning:**
```
{location}/{schema_prefix}/{partition_path}/{schema_name}/{table_name}/{remaining_key}/{field_name}.{token}.{ext}
```

**Algorithm:**

1. Extract primary key values from the row
2. If partition pattern configured, extract partition attributes
3. Build partition path from partition attributes (if any)
4. Build remaining key string from non-partition primary key attributes
5. Generate random token (default 8 characters)
6. Construct full path
7. Store path metadata in relational database as JSON

**Partition pattern format:**

```json
{
  "partition_pattern": "subject_id/session_date"
}
```

This creates paths like:
```
{schema_prefix}/subject_id=042/session_date=2024-01-15/{schema}/{table}/{remaining_key}/
```

**Key string encoding:**

Primary key values are encoded as: `{attr}={value}`

- Multiple attributes joined with `/`
- Values URL-encoded if necessary
- Order matches table definition

**Properties:**
- **Mutable**: Can overwrite by writing to same path
- **Streaming**: fsspec integration for lazy loading
- **Organized**: Hierarchical structure mirrors data relationships

**Example without partitioning:**

```python
@schema
class Recording(dj.Manual):
    definition = """
    subject_id : int
    session_id : int
    ---
    neural_data : <object@main>
    """

# With config:
# schema_prefix = "arrays"
# location = "/data/store"
# token_length = 8

Recording.insert1({
    'subject_id': 42,
    'session_id': 100,
    'neural_data': zarr_array
})

# Resulting path:
# /data/store/arrays/neuroscience/Recording/subject_id=42/session_id=100/neural_data.x8a7b2c4.zarr
```

**Example with partitioning:**

```python
# Same table, but with partition configuration:
# partition_pattern = "subject_id/session_date"

@schema
class Recording(dj.Manual):
    definition = """
    subject_id : int
    session_date : date
    session_id : int
    ---
    neural_data : <object@main>
    """

Recording.insert1({
    'subject_id': 42,
    'session_date': '2024-01-15',
    'session_id': 100,
    'neural_data': zarr_array
})

# Resulting path:
# /data/store/arrays/subject_id=42/session_date=2024-01-15/neuroscience/Recording/session_id=100/neural_data.x8a7b2c4.zarr
```

**Partition extraction:**

When a partition pattern is configured:

1. Check if table has all partition attributes in primary key
2. If yes: extract those attributes to partition path, remaining attributes to key path
3. If no: use normal structure (no partitioning for this table)

This allows a single `partition_pattern` to apply to multiple tables, with automatic fallback for tables lacking partition attributes.

**Path collision prevention:**

The random token ensures uniqueness:
- 8 characters (default): 62^8 = ~218 trillion combinations
- Collision probability negligible for typical table sizes
- Token regenerated on each write

### Filepath Storage

**Data type:** `<filepath@store>`

**Path structure:**
```
{location}/{filepath_prefix}/{user_path}
```

Or if `filepath_prefix = null`:
```
{location}/{user_path}
```

**Algorithm:**

1. User provides relative path within store
2. Validate path doesn't use reserved sections (`hash_prefix`, `schema_prefix`)
3. If `filepath_prefix` configured, validate path starts with it
4. Check file exists at `{location}/{user_path}`
5. Record path, size, and timestamp in JSON metadata
6. No file copying occurs

**Properties:**
- **Path-only storage**: DataJoint stores path string, no file management
- **No lifecycle management**: No garbage collection, transaction safety, or deduplication
- **User-managed**: User controls file creation, organization, and lifecycle
- **Collision-prone**: **User responsible for avoiding name collisions**
- **Flexible**: Can reference existing files or create new ones

**Collision handling:**

DataJoint does **not** prevent filename collisions for filepath storage. Users must ensure:

1. Unique paths for each referenced file
2. No overwrites of files still referenced by database
3. Coordination if multiple processes write to same store

**Strategies for avoiding collisions:**

```python
# Strategy 1: Include primary key in path
recording_path = f"subject_{subject_id}/session_{session_id}/data.bin"

# Strategy 2: Use UUIDs
import uuid
recording_path = f"recordings/{uuid.uuid4()}.nwb"

# Strategy 3: Timestamps
from datetime import datetime
recording_path = f"data_{datetime.now().isoformat()}.dat"

# Strategy 4: Enforce via filepath_prefix
# Config: "filepath_prefix": "recordings"
# All paths must start with recordings/, organize within that namespace
```

**Reserved sections:**

Filepath storage cannot use paths starting with configured `hash_prefix` or `schema_prefix`:

```python
# Invalid (default prefixes)
table.insert1({'id': 1, 'file': '_hash/data.bin'})       # ERROR
table.insert1({'id': 2, 'file': '_schema/data.zarr'})    # ERROR

# Invalid (custom prefixes: hash_prefix="blobs")
table.insert1({'id': 3, 'file': 'blobs/data.bin'})       # ERROR

# Valid
table.insert1({'id': 4, 'file': 'raw/subject01/rec.bin'})  # OK
```

**Example:**

```python
@schema
class RawRecording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    acquisition_file : <filepath@acquisition>
    """

# With config:
# filepath_prefix = "imported"
# location = "/data/acquisition"

# File already exists at: /data/acquisition/imported/subject01/session001/data.nwb

RawRecording.insert1({
    'recording_id': my_uuid,
    'acquisition_file': 'imported/subject01/session001/data.nwb'
})

# DataJoint validates file exists, stores reference
# User responsible for ensuring path uniqueness across recordings
```

## Storage Type Comparison

| Feature | Hash-addressed | Schema-addressed | Filepath |
|---------|----------------|------------------|----------|
| **Mutability** | Immutable | Mutable | User-managed |
| **Deduplication** | Automatic | None | None |
| **Streaming** | No (load full) | Yes (fsspec) | Yes (fsspec) |
| **Organization** | Flat (by hash) | Hierarchical (by key) | User-defined |
| **Collision handling** | Automatic (by content) | Automatic (token) | **User responsibility** |
| **DataJoint manages lifecycle** | Yes | Yes | **No** |
| **Suitable for** | Immutable blobs | Large mutable arrays | Existing files |

## Protocol-Specific Configuration

### File Protocol

```json
{
  "protocol": "file",
  "location": "/data/my-project",
  "hash_prefix": "blobs",
  "schema_prefix": "arrays",
  "filepath_prefix": null
}
```

**Required:** `protocol`, `location`

### S3 Protocol

```json
{
  "protocol": "s3",
  "endpoint": "s3.amazonaws.com",
  "bucket": "my-bucket",
  "location": "my-project/production",
  "secure": true,
  "hash_prefix": "blobs",
  "schema_prefix": "arrays"
}
```

**Required:** `protocol`, `endpoint`, `bucket`, `location`, `access_key`, `secret_key`

**Credentials:** Store in `.secrets/stores.<name>.access_key` and `.secrets/stores.<name>.secret_key`

### GCS Protocol

```json
{
  "protocol": "gcs",
  "bucket": "my-gcs-bucket",
  "location": "my-project",
  "project": "my-gcp-project",
  "hash_prefix": "blobs",
  "schema_prefix": "arrays"
}
```

**Required:** `protocol`, `bucket`, `location`, `token`

**Credentials:** Store in `.secrets/stores.<name>.token` (path to service account JSON)

### Azure Protocol

```json
{
  "protocol": "azure",
  "container": "my-container",
  "location": "my-project",
  "hash_prefix": "blobs",
  "schema_prefix": "arrays"
}
```

**Required:** `protocol`, `container`, `location`, `account_name`, `account_key`

**Credentials:** Store in `.secrets/stores.<name>.account_key`

## Migration from Legacy Storage

DataJoint 0.14.x used separate configuration systems:

### Legacy "External" Storage (Hash-addressed Integrated)

```python
# 0.14.x config
dj.config['stores'] = {
    'my_store': {
        'protocol': 's3',
        'endpoint': 's3.amazonaws.com',
        'bucket': 'my-bucket',
        'location': 'my-project',
        'access_key': 'XXX',
        'secret_key': 'YYY'
    }
}

# 0.14.x usage
data : external-my_store
```

### 2.0 Equivalent

```json
{
  "stores": {
    "default": "my_store",
    "my_store": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-bucket",
      "location": "my-project",
      "hash_prefix": "_hash"
    }
  }
}
```

Credentials moved to `.secrets/`:
```
.secrets/stores.my_store.access_key
.secrets/stores.my_store.secret_key
```

```python
# 2.0 usage (equivalent)
data : <blob@my_store>
```

### New in 2.0: Schema-addressed Storage

Schema-addressed storage (`<object@>`, `<npy@>`) is entirely new in DataJoint 2.0. No migration needed as this feature didn't exist in 0.14.x.

## Validation and Testing

### Verify Store Configuration

```python
import datajoint as dj

# Check default store
spec = dj.config.get_store_spec()
print(f"Default store: {dj.config['stores']['default']}")
print(f"Protocol: {spec['protocol']}")
print(f"Location: {spec['location']}")
print(f"Hash prefix: {spec['hash_prefix']}")
print(f"Schema prefix: {spec['schema_prefix']}")
print(f"Filepath prefix: {spec['filepath_prefix']}")

# Check named store
spec = dj.config.get_store_spec('archive')
print(f"Archive location: {spec['location']}")

# List all stores
print(f"Configured stores: {list(dj.config['stores'].keys())}")
```

### Test Storage Access

```python
from datajoint.hash_registry import get_store_backend

# Test backend connectivity
backend = get_store_backend('main')
print(f"Backend type: {type(backend)}")

# For file protocol, check paths exist
if spec['protocol'] == 'file':
    import os
    assert os.path.exists(spec['location']), f"Location not found: {spec['location']}"
```

## Best Practices

### Store Organization

1. **Use one default store** for most data
2. **Add specialized stores** for specific needs:
   - `archive` — long-term cold storage
   - `fast` — high-performance tier
   - `shared` — cross-project data
   - `raw` — acquisition files (filepath only)

### Prefix Configuration

1. **Use defaults** unless integrating with existing storage
2. **Choose meaningful names** if customizing: `blobs`, `arrays`, `user_files`
3. **Keep prefixes short** to minimize path length

### Secret Management

1. **Never commit credentials** to version control
2. **Use `.secrets/` directory** for all credentials
3. **Set restrictive permissions**: `chmod 700 .secrets`
4. **Document required secrets** in project README

### Partitioning Strategy

1. **Choose partition attributes carefully:**
   - High cardinality (many unique values)
   - Natural data organization (subject, date)
   - Query patterns (often filtered by these attributes)

2. **Example patterns:**
   - Neuroscience: `subject_id/session_date`
   - Genomics: `sample_id/sequencing_run`
   - Microscopy: `experiment_id/imaging_session`

3. **Avoid over-partitioning:**
   - Don't partition by high-cardinality unique IDs
   - Limit to 2-3 partition levels

### Filepath Usage

1. **Design naming conventions** before inserting data
2. **Include unique identifiers** in paths
3. **Document collision prevention strategy** for the team
4. **Consider using `filepath_prefix`** to enforce structure

## See Also

- [Configuration Reference](../configuration.md) — All configuration options
- [Configure Object Stores](../../how-to/configure-storage.md) — Setup guide
- [Type System Specification](type-system.md) — Data type definitions
- [Codec API Specification](codec-api.md) — Codec implementation details
