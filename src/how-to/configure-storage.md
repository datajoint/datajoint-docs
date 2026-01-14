# Configure Object Stores

Set up S3, MinIO, or filesystem storage for DataJoint's Object-Augmented Schema (OAS).

> **Tip:** [DataJoint.com](https://datajoint.com) provides pre-configured object stores integrated with your database—no setup required.

## Overview

DataJoint's Object-Augmented Schema (OAS) integrates relational tables with object storage as a single coherent system. Large data objects (arrays, files, Zarr datasets) are stored in file systems or cloud storage while maintaining full referential integrity with the relational database.

**Storage models:**
- **Hash-addressed** and **schema-addressed** storage are **integrated** into the OAS. DataJoint manages paths, lifecycle, and integrity.
- **Filepath** storage provides **references** to externally-managed files. Users control organization and lifecycle.

Storage is configured per-project using named stores. Each store can be used for:
- **Hash-addressed storage** (`<blob@>`, `<attach@>`) — content-addressed with deduplication using `_hash/` section
- **Schema-addressed storage** (`<object@>`, `<npy@>`) — key-based paths with streaming access using `_schema/` section
- **Filepath storage** (`<filepath@>`) — user-managed paths anywhere in the store **except** `_hash/` and `_schema/` (reserved for DataJoint)

Multiple stores can be configured for different data types or storage tiers. One store is designated as the default.

## Configuration Methods

DataJoint loads configuration in priority order:

1. **Environment variables** (highest priority)
2. **Secrets directory** (`.secrets/`)
3. **Config file** (`datajoint.json`)
4. **Defaults** (lowest priority)

## Single Store Configuration

### File System Store

For local or network-mounted storage:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/my-project/production"
    }
  }
}
```

Paths will be:
- Hash: `/data/my-project/production/_hash/{schema}/{hash}`
- Schema: `/data/my-project/production/_schema/{schema}/{table}/{key}/`

### S3 Store

For Amazon S3 or S3-compatible storage:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-bucket",
      "location": "my-project/production",
      "secure": true
    }
  }
}
```

Store credentials separately in `.secrets/`:

```
.secrets/
├── stores.main.access_key
└── stores.main.secret_key
```

Paths will be:
- Hash: `s3://my-bucket/my-project/production/_hash/{schema}/{hash}`
- Schema: `s3://my-bucket/my-project/production/_schema/{schema}/{table}/{key}/`

### MinIO Store

MinIO uses the S3 protocol with a custom endpoint:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "minio.example.com:9000",
      "bucket": "datajoint",
      "location": "lab-data",
      "secure": false
    }
  }
}
```

## Multiple Stores Configuration

Define multiple stores for different data types or storage tiers:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/my-project/main",
      "partition_pattern": "subject_id/session_date"
    },
    "raw": {
      "protocol": "file",
      "location": "/data/my-project/raw",
      "subfolding": [2, 2]
    },
    "archive": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive-bucket",
      "location": "my-project/long-term"
    }
  }
}
```

Store credentials in `.secrets/`:

```
.secrets/
├── stores.archive.access_key
└── stores.archive.secret_key
```

Use named stores in table definitions:

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    raw_data : <blob@raw>         # Hash: _hash/{schema}/{hash}
    zarr_scan : <object@raw>      # Schema: _schema/{schema}/{table}/{key}/
    summary : <blob@>             # Uses default store (main)
    old_data : <blob@archive>     # Archive store, hash-addressed
    """
```

Notice that `<blob@raw>` and `<object@raw>` both use the "raw" store, just different `_hash` and `_schema` sections.

**Example paths with partitioning:**

For a Recording with `subject_id=042`, `session_date=2024-01-15` in the main store:
```
/data/my-project/main/_schema/subject_id=042/session_date=2024-01-15/experiment/Recording/recording_id=uuid-value/zarr_scan.x8f2a9b1.zarr
```

Without those attributes, it follows normal structure:
```
/data/my-project/main/_schema/experiment/Recording/recording_id=uuid-value/zarr_scan.x8f2a9b1.zarr
```

## Verify Configuration

```python
import datajoint as dj

# Check default store
spec = dj.config.get_store_spec()  # Uses stores.default
print(spec)

# Check named store
spec = dj.config.get_store_spec("archive")
print(spec)

# List all configured stores
print(dj.config.stores.keys())
```

## Configuration Options

| Option | Required | Description |
|--------|----------|-------------|
| `stores.default` | Yes | Name of the default store |
| `stores.<name>.protocol` | Yes | `file`, `s3`, `gcs`, or `azure` |
| `stores.<name>.location` | Yes | Base path or prefix (includes project context) |
| `stores.<name>.bucket` | S3/GCS | Bucket name |
| `stores.<name>.endpoint` | S3 | S3 endpoint URL |
| `stores.<name>.secure` | No | Use HTTPS (default: true) |
| `stores.<name>.access_key` | S3 | Access key ID (store in `.secrets/`) |
| `stores.<name>.secret_key` | S3 | Secret access key (store in `.secrets/`) |
| `stores.<name>.subfolding` | No | Hash-addressed hierarchy: `[2, 2]` for 2-level nesting (default: no subfolding) |
| `stores.<name>.partition_pattern` | No | Schema-addressed path partitioning: `"subject_id/session_date"` (default: no partitioning) |
| `stores.<name>.token_length` | No | Random token length for schema-addressed filenames (default: `8`) |

## Subfolding (Hash-Addressed Storage Only)

Hash-addressed storage (`<blob@>`, `<attach@>`) stores content using a Base32-encoded hash as the filename. By default, all files are stored in a flat directory structure:

```
_hash/{schema}/abcdefghijklmnopqrstuvwxyz
```

Some filesystems perform poorly with large directories (thousands of files). Subfolding creates a directory hierarchy to distribute files:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/store",
      "project_name": "my_project",
      "subfolding": [2, 2]
    }
  }
}
```

With `[2, 2]` subfolding, hash-addressed paths become:

```
_hash/{schema}/ab/cd/abcdefghijklmnopqrstuvwxyz
```

Schema-addressed storage (`<object@>`, `<npy@>`) does not use subfolding—it uses key-based paths:

```
{location}/_schema/{partition}/{schema}/{table}/{key}/{field_name}.{token}.{ext}
```

### Filesystem Recommendations

| Filesystem | Subfolding Needed | Notes |
|------------|-------------------|-------|
| ext3 | Yes | Limited directory indexing |
| FAT32/exFAT | Yes | Linear directory scans |
| NFS | Yes | Network latency amplifies directory lookups |
| CIFS/SMB | Yes | Windows network shares |
| ext4 | No | HTree indexing handles large directories |
| XFS | No | B+ tree directories scale well |
| ZFS | No | Efficient directory handling |
| Btrfs | No | B-tree based |
| S3/MinIO | No | Object storage uses hash-based lookups |
| GCS | No | Object storage |
| Azure Blob | No | Object storage |

**Recommendation:** Use `[2, 2]` for network-mounted filesystems and legacy systems.
Modern local filesystems and cloud object storage work well without subfolding.

## URL Representation

DataJoint uses consistent URL representation for all storage backends internally. This means:

- Local filesystem paths are represented as `file://` URLs
- S3 paths use `s3://bucket/path`
- GCS paths use `gs://bucket/path`
- Azure paths use `az://container/path`

You can use either format when specifying paths:

```python
# Both are equivalent for local files
"/data/myfile.dat"
"file:///data/myfile.dat"
```

This unified approach enables:

- **Consistent internal handling** across all storage types
- **Seamless switching** between local and cloud storage
- **Integration with fsspec** for streaming access

## Customizing Storage Prefixes

By default, DataJoint uses `_hash/` and `_schema/` prefixes for managed storage. You can customize these prefixes to map DataJoint to existing storage layouts:

```json
{
  "stores": {
    "legacy": {
      "protocol": "file",
      "location": "/data/existing_storage",
      "hash_prefix": "content_addressed",
      "schema_prefix": "structured_data",
      "filepath_prefix": "raw_files"
    }
  }
}
```

**Prefix requirements:**
- Prefixes must be mutually exclusive (no nesting)
- `hash_prefix` and `schema_prefix` are reserved for DataJoint
- `filepath_prefix` is optional (null = unrestricted)

**Example with hierarchical layout:**

```json
{
  "stores": {
    "organized": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "neuroscience-data",
      "location": "lab-project-2024",
      "hash_prefix": "managed/blobs",
      "schema_prefix": "managed/arrays",
      "filepath_prefix": "imported"
    }
  }
}
```

Paths become:
- Hash: `s3://neuroscience-data/lab-project-2024/managed/blobs/{schema}/{hash}`
- Schema: `s3://neuroscience-data/lab-project-2024/managed/arrays/{schema}/{table}/{key}/`
- Filepath: `s3://neuroscience-data/lab-project-2024/imported/{user_path}`

## Reserved Sections and Filepath Storage

DataJoint reserves sections within each store for managed storage based on the configured prefixes:

- **`hash_prefix`** (default: `_hash/`) — Hash-addressed storage for `<blob@>` and `<attach@>` with content deduplication
- **`schema_prefix`** (default: `_schema/`) — Schema-addressed storage for `<object@>` and `<npy@>` with key-based paths

### User-Managed Filepath Storage

The `<filepath@>` codec allows you to reference existing files anywhere in the store **except** these reserved sections. This gives you maximum freedom to organize files while reusing DataJoint's store configuration:

```python
@schema
class RawData(dj.Manual):
    definition = """
    session_id : int
    ---
    recording : <filepath@acquisition>  # Reference existing file
    """

# Valid paths (user-managed)
table.insert1({'session_id': 1, 'recording': 'subject01/session001/data.bin'})
table.insert1({'session_id': 2, 'recording': 'raw/experiment_2024/data.nwb'})

# Invalid paths (reserved for DataJoint - will raise ValueError)
# These use the default prefixes (_hash and _schema)
table.insert1({'session_id': 3, 'recording': '_hash/abc123...'})      # Error!
table.insert1({'session_id': 4, 'recording': '_schema/myschema/...'}) # Error!

# If you configured custom prefixes like "content_addressed", those would also be blocked
# table.insert1({'session_id': 5, 'recording': 'content_addressed/file.dat'})  # Error!
```

**Key characteristics of `<filepath@>`:**
- References existing files (no copying)
- User controls file organization
- User manages file lifecycle (DataJoint never deletes)
- Returns ObjectRef for lazy access on fetch
- Validates file exists on insert
- Cannot use reserved sections (configured by `hash_prefix` and `schema_prefix`)
- Can be restricted to specific prefix using `filepath_prefix` configuration

## See Also

- [Use Object Storage](use-object-storage.md) — When and how to use object storage
- [Manage Large Data](manage-large-data.md) — Working with blobs and objects
