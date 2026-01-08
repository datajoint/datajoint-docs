# Use Object Storage

Store large data objects as part of your Object-Augmented Schema.

## Object-Augmented Schema (OAS)

An **Object-Augmented Schema** extends relational tables with object storage as a unified system. The relational database stores metadata, references, and small values while large objects (arrays, files, datasets) are stored in object storage. DataJoint maintains referential integrity across both storage layers—when you delete a row, its associated objects are cleaned up automatically.

OAS supports three storage sections:

| Section | Location | Addressing | Use Case |
|---------|----------|------------|----------|
| **Internal** | Database | Row-based | Small objects (< 1 MB) |
| **Hash-addressed** | Object store | Content hash | Arrays, files (deduplication) |
| **Path-addressed** | Object store | Primary key path | Zarr, HDF5, streaming access |

For complete details, see the [Type System specification](../reference/specs/type-system.md).

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

## Hash-Addressed Storage

`<blob@>` and `<attach@>` use **hash-addressed** storage:

- Objects are stored by their content hash (SHA-256)
- Identical data is stored once (automatic deduplication)
- Multiple rows can reference the same object
- Immutable—changing data creates a new object

```python
# These two inserts store the same array only once
data = np.zeros((1000, 1000))
Table.insert1({'id': 1, 'array': data})
Table.insert1({'id': 2, 'array': data})  # References same object
```

## Path-Addressed Storage

`<object@>` uses **path-addressed** storage for file-like objects:

- Objects stored at predictable paths based on primary key
- Path format: `{schema}/{table}/{pk_hash}/{attribute}/`
- Supports streaming access and partial reads
- Mutable—can update in place (e.g., append to Zarr)

```python
@schema
class Dataset(dj.Manual):
    definition = """
    dataset_id : uuid
    ---
    zarr_array : <object@>      # Zarr array stored by path
    """
```

Use path-addressed storage for:

- Zarr arrays (chunked, appendable)
- HDF5 files
- Large datasets requiring streaming access

## Write Directly to Object Storage

For large datasets like multi-GB imaging recordings, avoid intermediate copies by writing directly to object storage with `staged_insert1`:

```python
import zarr

@schema
class ImagingSession(dj.Manual):
    definition = """
    subject_id : int32
    session_id : int32
    ---
    n_frames : int32
    frame_rate : float32
    frames : <object@>
    """

# Write Zarr directly to object storage
with ImagingSession.staged_insert1 as staged:
    # 1. Set primary key values first
    staged.rec['subject_id'] = 1
    staged.rec['session_id'] = 1

    # 2. Get storage handle
    store = staged.store('frames', '.zarr')

    # 3. Write directly (no local copy)
    z = zarr.open(store, mode='w', shape=(1000, 512, 512),
                  chunks=(10, 512, 512), dtype='uint16')
    for i in range(1000):
        z[i] = acquire_frame()  # Write frame-by-frame

    # 4. Set remaining attributes
    staged.rec['n_frames'] = 1000
    staged.rec['frame_rate'] = 30.0

# Record inserted with computed metadata on successful exit
```

The `staged_insert1` context manager:

- Writes directly to the object store (no intermediate files)
- Computes metadata (size, manifest) automatically on exit
- Cleans up storage if an error occurs (atomic)
- Requires primary key values before calling `store()` or `open()`

Use `staged.store(field, ext)` for FSMap access (Zarr), or `staged.open(field, ext)` for file-like access.

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
