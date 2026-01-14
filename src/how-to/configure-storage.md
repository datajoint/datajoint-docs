# Configure External Storage

Set up S3, MinIO, or filesystem storage for hash-addressed and path-addressed external storage.

> **Tip:** [DataJoint.com](https://datajoint.com) provides pre-configured external storage integrated with your database—no setup required.

## Overview

DataJoint's Object-Augmented Schema (OAS) integrates relational tables with external storage as a single system. Large data objects (arrays, files, Zarr datasets) are stored externally while maintaining full referential integrity with the relational database.

Storage is configured per-project using named stores. Each store can be used for both:
- **Hash-addressed storage** (`<blob@>`, `<attach@>`, `<filepath@>`) — content-addressed with deduplication
- **Path-addressed storage** (`<object@>`, `<npy@>`) — schema-addressed with streaming access

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
      "location": "/data/datajoint-store",
      "project_name": "my_project"
    }
  }
}
```

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
      "location": "datajoint",
      "project_name": "my_project",
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
      "project_name": "my_project",
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
      "location": "/data/main",
      "project_name": "my_project"
    },
    "raw": {
      "protocol": "file",
      "location": "/data/raw",
      "project_name": "my_project",
      "subfolding": [2, 2]
    },
    "archive": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive-bucket",
      "location": "long-term",
      "project_name": "my_project"
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
    raw_data : <blob@raw>         # Hash-addressed in 'raw' store
    zarr_scan : <object@raw>      # Path-addressed in 'raw' store
    summary : <blob@>             # Uses default store (main)
    old_data : <blob@archive>     # Hash-addressed in 'archive' store
    """
```

Notice that `<blob@raw>` and `<object@raw>` both use the "raw" store, just different sections within it.

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
| `stores.<name>.location` | Yes | Base path or prefix within bucket |
| `stores.<name>.project_name` | Yes | Unique project identifier |
| `stores.<name>.bucket` | S3/GCS | Bucket name |
| `stores.<name>.endpoint` | S3 | S3 endpoint URL |
| `stores.<name>.secure` | No | Use HTTPS (default: true) |
| `stores.<name>.access_key` | S3 | Access key ID (store in `.secrets/`) |
| `stores.<name>.secret_key` | S3 | Secret access key (store in `.secrets/`) |
| `stores.<name>.subfolding` | No | Hash-addressed hierarchy: `[2, 2]` for 2-level nesting (default: no subfolding) |

## Subfolding (Hash-Addressed Storage Only)

Hash-addressed storage (`<blob@>`, `<attach@>`, `<filepath@>`) stores content using a Base32-encoded hash as the filename. By default, all files are stored in a flat directory structure:

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

Path-addressed storage (`<object@>`, `<npy@>`) does not use subfolding—it uses schema-based paths:

```
{project_name}/{schema}/{table}/{key}/filename
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

## See Also

- [Use Object Storage](use-object-storage.md) — When and how to use object storage
- [Manage Large Data](manage-large-data.md) — Working with blobs and objects
