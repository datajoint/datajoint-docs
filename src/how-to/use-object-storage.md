# Use Object Storage

Store large data objects as part of your Object-Augmented Schema.

## When to Use Object Storage

Use the `@` modifier for:
- Large arrays (images, videos, neural recordings)
- File attachments
- Zarr arrays and HDF5 files
- Any data too large for efficient database storage

## Internal vs Object Storage

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    metadata : <blob>           # Internal: stored in database
    raw_data : <blob@>          # Object storage: stored externally
    """
```

| Syntax | Storage | Best For |
|--------|---------|----------|
| `<blob>` | Database | Small objects (< 1 MB) |
| `<blob@>` | Default store | Large objects |
| `<blob@store>` | Named store | Specific storage tier |

## Store Data

Insert works the same regardless of storage location:

```python
import numpy as np

Recording.insert1({
    'recording_id': uuid.uuid4(),
    'metadata': {'channels': 32, 'rate': 30000},
    'raw_data': np.random.randn(32, 30000)  # ~7.7 MB array
})
```

DataJoint automatically routes to the configured store.

## Retrieve Data

Fetch works transparently:

```python
data = (Recording & key).fetch1('raw_data')
# Returns the numpy array, regardless of where it was stored
```

## Named Stores

Use different stores for different data types:

```python
@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : uuid
    ---
    raw_video : <blob@raw>        # Fast local storage
    processed : <blob@archive>    # S3 for long-term
    """
```

Configure stores in `datajoint.json`:

```json
{
  "object_storage": {
    "stores": {
      "raw": {"protocol": "file", "location": "/fast/storage"},
      "archive": {"protocol": "s3", "bucket": "archive", ...}
    }
  }
}
```

## Content-Addressed Storage

`<blob@>` uses hash-based deduplication:
- Identical data is stored once
- Multiple references share the same object
- Automatic deduplication saves space

## Path-Addressed Storage

`<object@>` uses key-based paths for file-like objects:

```python
@schema
class Dataset(dj.Manual):
    definition = """
    dataset_id : uuid
    ---
    zarr_array : <object@>      # Zarr array stored by path
    """
```

Objects are stored at: `{schema}/{table}/{pk}/{attribute}/`

## Attachments

Preserve original filenames with `<attach@>`:

```python
@schema
class Document(dj.Manual):
    definition = """
    doc_id : uuid
    ---
    report : <attach@>          # Preserves filename
    """

# Insert with AttachFileType
from datajoint import AttachFileType
Document.insert1({
    'doc_id': uuid.uuid4(),
    'report': AttachFileType('/path/to/report.pdf')
})
```

## Lazy Loading with ObjectRef

`<object@>` and `<filepath@>` return lazy references:

```python
ref = (Dataset & key).fetch1('zarr_array')

# Open for streaming access
with ref.open() as f:
    data = zarr.open(f)

# Or download to local path
local_path = ref.download('/tmp/data')
```

## Storage Best Practices

### Choose the Right Codec

| Data Type | Codec | Storage |
|-----------|-------|---------|
| NumPy arrays | `<blob@>` | Hash-addressed |
| File attachments | `<attach@>` | Hash-addressed |
| Zarr/HDF5 | `<object@>` | Path-addressed |
| File references | `<filepath@>` | Path-addressed |

### Size Guidelines

- **< 1 MB**: Internal storage (`<blob>`) is fine
- **1 MB - 1 GB**: Object storage (`<blob@>`)
- **> 1 GB**: Path-addressed (`<object@>`) for streaming

### Store Tiers

Configure stores for different access patterns:

```json
{
  "object_storage": {
    "stores": {
      "hot": {"protocol": "file", "location": "/ssd/data"},
      "warm": {"protocol": "s3", "bucket": "project-data"},
      "cold": {"protocol": "s3", "bucket": "archive", ...}
    }
  }
}
```

## See Also

- [Configure Object Storage](configure-storage.md) — Storage setup
- [Create Custom Codecs](create-custom-codec.md) — Domain-specific types
- [Manage Large Data](manage-large-data.md) — Working with blobs
