# Configure Object Storage

Set up S3, MinIO, or filesystem storage for your Object-Augmented Schema.

> **Tip:** [DataJoint.com](https://datajoint.com) provides pre-configured object storage integrated with your database—no setup required.

## Overview

An Object-Augmented Schema (OAS) integrates relational tables with object storage as a single system. Large data objects (arrays, files, Zarr datasets) are stored in object storage while maintaining full referential integrity with the relational database.

Object storage is configured per-project and can include multiple named stores for different data types or storage tiers.

## Configuration Methods

DataJoint loads configuration in priority order:

1. **Environment variables** (highest priority)
2. **Secrets directory** (`.secrets/`)
3. **Config file** (`datajoint.json`)
4. **Defaults** (lowest priority)

## File System Store

For local or network-mounted storage:

```json
{
  "object_storage": {
    "project_name": "my_project",
    "protocol": "file",
    "location": "/data/datajoint-store"
  }
}
```

## S3 Store

For Amazon S3 or S3-compatible storage:

```json
{
  "object_storage": {
    "project_name": "my_project",
    "protocol": "s3",
    "endpoint": "s3.amazonaws.com",
    "bucket": "my-bucket",
    "location": "dj/objects",
    "secure": true
  }
}
```

Store credentials separately in `.secrets/`:

```
.secrets/
├── object_storage.access_key
└── object_storage.secret_key
```

Or use environment variables:

```bash
export DJ_OBJECT_STORAGE_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
export DJ_OBJECT_STORAGE_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## MinIO Store

MinIO uses the S3 protocol with a custom endpoint:

```json
{
  "object_storage": {
    "project_name": "my_project",
    "protocol": "s3",
    "endpoint": "minio.example.com:9000",
    "bucket": "datajoint",
    "location": "dj/objects",
    "secure": false
  }
}
```

## Named Stores

Define multiple stores for different data types or storage tiers:

```json
{
  "object_storage": {
    "project_name": "my_project",
    "protocol": "file",
    "location": "/data/default",
    "stores": {
      "raw": {
        "protocol": "file",
        "location": "/data/raw"
      },
      "archive": {
        "protocol": "s3",
        "endpoint": "s3.amazonaws.com",
        "bucket": "archive-bucket",
        "location": "dj/archive"
      }
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
    raw_data : <blob@raw>         # Uses 'raw' store
    processed : <blob@archive>    # Uses 'archive' store
    """
```

## Verify Configuration

```python
import datajoint as dj

# Check default store
spec = dj.config.get_object_store_spec()
print(spec)

# Check named store
spec = dj.config.get_object_store_spec("archive")
print(spec)
```

## Configuration Options

| Option | Required | Description |
|--------|----------|-------------|
| `project_name` | Yes | Unique identifier for your project |
| `protocol` | Yes | `file`, `s3`, `gcs`, or `azure` |
| `location` | Yes | Base path or prefix within bucket |
| `bucket` | S3/GCS | Bucket name |
| `endpoint` | S3 | S3 endpoint URL |
| `secure` | No | Use HTTPS (default: true) |
| `access_key` | S3 | Access key ID |
| `secret_key` | S3 | Secret access key |
| `subfolding` | No | Directory hierarchy pattern (e.g., `[2, 2]`) |

## Subfolding

Hash-addressed storage (used by `<blob@>`, `<attach@>`, and `<hash@>` types) stores content
using a Base32-encoded hash as the filename. By default, all files are stored in a flat
directory structure:

```
_hash/{schema}/abcdefghijklmnopqrstuvwxyz
```

Some filesystems perform poorly with large directories (thousands of files). Subfolding
creates a directory hierarchy to distribute files:

```json
{
  "object_storage": {
    "project_name": "my_project",
    "protocol": "file",
    "location": "/data/store",
    "subfolding": [2, 2]
  }
}
```

With `[2, 2]` subfolding, paths become:

```
_hash/{schema}/ab/cd/abcdefghijklmnopqrstuvwxyz
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
