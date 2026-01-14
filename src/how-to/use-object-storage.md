# Use Object Storage

Store large data objects as part of your Object-Augmented Schema.

## Object-Augmented Schema (OAS)

An **Object-Augmented Schema** extends relational tables with object storage as a unified system. The relational database stores metadata, references, and small values while large objects (arrays, files, datasets) are stored in object storage. DataJoint maintains referential integrity across both storage layers—when you delete a row, its associated objects are cleaned up automatically.

OAS supports two addressing schemes:

| Addressing | Location | Path Derived From | Use Case |
|------------|----------|-------------------|----------|
| **Hash-addressed** | Object store | Content hash (MD5) | Blobs, attachments (with deduplication) |
| **Schema-addressed** | Object store | Schema structure | NumPy arrays, Zarr, HDF5 (browsable paths) |

Data can also be stored **in-table** directly in the database column (no `@` modifier).

For complete details, see the [Type System specification](../reference/specs/type-system.md).

## When to Use Object Storage

Use the `@` modifier for:

- Large arrays (images, videos, neural recordings)
- File attachments
- Zarr arrays and HDF5 files
- Any data too large for efficient database storage

## In-Table vs Object Store

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    metadata : <blob>           # In-table: stored in database column
    raw_data : <blob@>          # Object store: hash-addressed
    waveforms : <npy@>          # Object store: schema-addressed (lazy)
    """
```

| Syntax | Storage | Best For |
|--------|---------|----------|
| `<blob>` | Database | Small objects (< 1 MB) |
| `<blob@>` | Default store | Large objects (hash-addressed) |
| `<npy@>` | Default store | NumPy arrays (schema-addressed, lazy) |
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
  "stores": {
    "default": "raw",
    "raw": {
      "protocol": "file",
      "location": "/fast/storage"
    },
    "archive": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive",
      "location": "project-data"
    }
  }
}
```

## Hash-Addressed Storage

`<blob@>` and `<attach@>` use **hash-addressed** storage:

- Objects are stored by their content hash (MD5)
- Identical data is stored once (automatic deduplication)
- Multiple rows can reference the same object
- Immutable—changing data creates a new object

```python
# These two inserts store the same array only once
data = np.zeros((1000, 1000))
Table.insert1({'id': 1, 'array': data})
Table.insert1({'id': 2, 'array': data})  # References same object
```

## Schema-Addressed Storage

`<npy@>` and `<object@>` use **schema-addressed** storage:

- Objects stored at paths that mirror database schema: `{schema}/{table}/{pk}/{attribute}.npy`
- Browsable organization in object storage
- One object per entity (no deduplication)
- Supports lazy loading with metadata access

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

## NumPy Arrays with `<npy@>`

The `<npy@>` codec stores NumPy arrays as portable `.npy` files with lazy loading:

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int32
    ---
    waveform : <npy@mystore>    # NumPy array, schema-addressed
    """

# Insert - just pass the array
Recording.insert1({
    'recording_id': 1,
    'waveform': np.random.randn(1000, 32),
})

# Fetch returns NpyRef (lazy)
ref = (Recording & 'recording_id=1').fetch1('waveform')
```

### NpyRef: Lazy Array Reference

`NpyRef` provides metadata without downloading:

```python
ref = (Recording & key).fetch1('waveform')

# Metadata access - NO download
ref.shape    # (1000, 32)
ref.dtype    # float64
ref.nbytes   # 256000
ref.is_loaded  # False

# Explicit loading
arr = ref.load()    # Downloads and caches
ref.is_loaded       # True

# Numpy integration (triggers download)
result = np.mean(ref)           # Uses __array__ protocol
result = np.asarray(ref) + 1    # Convert then operate
```

### Bulk Fetch Safety

Fetching many rows doesn't download until you access each array:

```python
# Fetch 1000 recordings - NO downloads yet
results = Recording.to_dicts()

# Inspect metadata without downloading
for rec in results:
    ref = rec['waveform']
    if ref.shape[0] > 500:     # Check without download
        process(ref.load())     # Download only what you need
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

| Data Type | Codec | Addressing | Lazy | Best For |
|-----------|-------|------------|------|----------|
| NumPy arrays | `<npy@>` | Schema | Yes | Arrays needing lazy load, metadata inspection |
| Python objects | `<blob@>` | Hash | No | Dicts, lists, small arrays (with dedup) |
| File attachments | `<attach@>` | Hash | No | Files with original filename preserved |
| Zarr/HDF5 | `<object@>` | Schema | Yes | Chunked arrays, streaming access |
| File references | `<filepath@>` | External | Yes | References to external files |

### Size Guidelines

- **< 1 MB**: Inline storage (`<blob>`) is fine
- **1 MB - 1 GB**: Object store (`<npy@>` or `<blob@>`)
- **> 1 GB**: Schema-addressed (`<npy@>`, `<object@>`) for lazy loading

### Store Tiers

Configure stores for different access patterns:

```json
{
  "stores": {
    "default": "hot",
    "hot": {
      "protocol": "file",
      "location": "/ssd/data"
    },
    "warm": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "project-data",
      "location": "active"
    },
    "cold": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive",
      "location": "long-term"
    }
  }
}
```

## See Also

- [Configure Object Storage](configure-storage.md) — Storage setup
- [Create Custom Codecs](create-custom-codec.md) — Domain-specific types
- [Manage Large Data](manage-large-data.md) — Working with blobs
