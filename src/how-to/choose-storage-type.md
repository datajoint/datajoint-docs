# Choose a Storage Type

Select the right storage codec for your data based on size, access patterns, and lifecycle requirements.

## Quick Decision Tree

```
Start: What type of data are you storing?

├─ Small data (typically < 1-10 MB per row)?
│  ├─ Python objects (dicts, arrays)? → Use <blob> (in-table)
│  └─ Files with filename? → Use <attach> (in-table)
│
├─ Externally managed files?
│  └─ YES → Use <filepath@> (reference only)
│  └─ NO  → Continue...
│
├─ Need browsable storage or access by external tools?
│  └─ YES → Use <object@> or <npy@> (schema-addressed)
│  └─ NO  → Continue...
│
├─ Need streaming or partial reads?
│  └─ YES → Use <object@> (schema-addressed, Zarr/HDF5)
│  └─ NO  → Continue...
│
├─ NumPy arrays that benefit from lazy loading?
│  └─ YES → Use <npy@> (optimized NumPy storage)
│  └─ NO  → Continue...
│
├─ Python objects (dicts, arrays)?
│  └─ YES → Use <blob@> (hash-addressed)
│  └─ NO  → Use <attach@> (files with filename preserved)
```

## Storage Types Overview

| Codec | Location | Addressing | Python Objects | Dedup | Best For |
|-------|----------|------------|----------------|-------|----------|
| `<blob>` | In-table (database) | Row-based | ✅ Yes | No | Small Python objects (typically < 1-10 MB) |
| `<attach>` | In-table (database) | Row-based | ❌ No (file path) | No | Small files with filename preserved |
| `<blob@>` | Object store | Content hash | ✅ Yes | Yes | Large Python objects (with dedup) |
| `<attach@>` | Object store | Content hash | ❌ No (file path) | Yes | Large files with filename preserved |
| `<npy@>` | Object store | Schema + key | ✅ Yes (arrays) | No | NumPy arrays (lazy load, navigable) |
| `<object@>` | Object store | Schema + key | ❌ No (you manage format) | No | Zarr, HDF5 (browsable, streaming) |
| `<filepath@>` | Object store | User path | ❌ No (you manage format) | No | External file references |

## Key Usability: Python Object Convenience

**Major advantage of `<blob>`, `<blob@>`, and `<npy@>`:** You work with Python objects directly. No manual serialization, file handling, or IO management.

```python
# <blob> and <blob@>: Insert Python objects, get Python objects back
@schema
class Analysis(dj.Computed):
    definition = """
    -> Experiment
    ---
    results : <blob@>         # Any Python object: dicts, lists, arrays
    """

    def make(self, key):
        # Insert nested Python structures directly
        results = {
            'accuracy': 0.95,
            'confusion_matrix': np.array([[10, 2], [1, 15]]),
            'metadata': {'method': 'SVM', 'params': [1, 2, 3]}
        }
        self.insert1({**key, 'results': results})

# Fetch: Get Python object back (no manual unpickling)
data = (Analysis & key).fetch1('results')
print(data['accuracy'])           # 0.95
print(data['confusion_matrix'])   # numpy array
```

```python
# <npy@>: Insert array-like objects, get array-like objects back
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    traces : <npy@>           # NumPy arrays (no manual .npy files)
    """

# Insert: Just pass the array
Recording.insert1({'recording_id': uuid.uuid4(), 'traces': np.random.randn(1000, 32)})

# Fetch: Get array-like object (NpyRef with lazy loading)
ref = (Recording & key).fetch1('traces')
print(ref.shape)              # (1000, 32) - metadata without download
subset = ref[:100, :]         # Lazy slicing
```

**Contrast with `<object@>` and `<filepath@>`:** You manage the format (Zarr, HDF5, etc.) and handle file IO yourself. More flexible, but requires format knowledge.

## Detailed Decision Criteria

### Size and Storage Location

**Technical Limits:**

- **MySQL**: In-table blobs up to 4 GiB (`LONGBLOB`)
- **PostgreSQL**: In-table blobs unlimited (`BYTEA`)
- **Object stores**: Effectively unlimited (S3, file systems, etc.)

**Practical Guidance:**

The choice between in-table (`<blob>`) and object storage (`<blob@>`, `<npy@>`, `<object@>`) is a complex decision involving:

- **Accessibility**: How fast do you need to access the data?
- **Cost**: Database storage vs object storage pricing
- **Performance**: Query speed, backup time, replication overhead

**General recommendations:**

Try to keep in-table blobs under ~1-10 MB, but this depends on your specific use case:

```python
@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : uuid
    ---
    metadata : <blob>         # Small: config, parameters (< 1 MB)
    thumbnail : <blob>        # Medium: preview images (< 10 MB)
    raw_data : <blob@>        # Large: raw recordings (> 10 MB)
    """
```

**When to use in-table storage (`<blob>`):**
- Fast access needed (no external fetch)
- Data frequently queried alongside other columns
- Transactional consistency critical
- Automatic backup with database important
- No object storage configuration available

**When to use object storage (`<blob@>`, `<npy@>`, `<object@>`):**
- Data larger than ~10 MB
- Infrequent access patterns
- Need deduplication (hash-addressed types)
- Need browsable structure (schema-addressed types)
- Want to separate hot data (DB) from cold data (object store)

**Examples by size:**
- **< 1 MB**: Configuration JSON, metadata, small parameter arrays → `<blob>`
- **1-10 MB**: Thumbnails, processed features, small waveforms → `<blob>` or `<blob@>` depending on access pattern
- **10-100 MB**: Neural recordings, images, PDFs → `<blob@>` or `<attach@>`
- **> 100 MB**: Zarr arrays, HDF5 datasets, large videos → `<object@>` or `<npy@>`

### Access Pattern Guidelines

**Full Access Every Time**

Use `<blob@>` (hash-addressed):

```python
class ProcessedImage(dj.Computed):
    definition = """
    -> RawImage
    ---
    processed : <blob@>       # Always load full image
    """
```

**Typical pattern:**
```python
# Fetch always gets full data
img = (ProcessedImage & key).fetch1('processed')
```

---

**Streaming / Partial Reads**

Use `<object@>` (schema-addressed):

```python
class ScanVolume(dj.Manual):
    definition = """
    scan_id : uuid
    ---
    volume : <object@>        # Stream chunks as needed
    """
```

**Typical pattern:**
```python
# Get reference without downloading
ref = (ScanVolume & key).fetch1('volume')

# Stream specific chunks
import zarr
z = zarr.open(ref.fsmap, mode='r')
slice_data = z[100:200, :, :]  # Fetch only this slice
```

---

**NumPy Arrays with Lazy Loading**

Use `<npy@>` (optimized for NumPy):

```python
class NeuralActivity(dj.Computed):
    definition = """
    -> Recording
    ---
    traces : <npy@>           # NumPy array, lazy load
    """
```

**Typical pattern:**
```python
# Returns NpyRef (lazy)
ref = (NeuralActivity & key).fetch1('traces')

# Access like NumPy array (loads on demand)
subset = ref[:100, :]         # Efficient slicing
shape = ref.shape             # Metadata without loading
```

**Why `<npy@>` over `<blob@>` for arrays:**
- Lazy loading (doesn't load until accessed)
- Efficient slicing (can fetch subsets)
- Preserves shape/dtype metadata
- Native NumPy serialization

### Lifecycle and Management

**DataJoint-Managed (Integrated)**

Use `<blob@>`, `<npy@>`, or `<object@>`:

```python
class ManagedData(dj.Manual):
    definition = """
    data_id : uuid
    ---
    content : <blob@>         # DataJoint manages lifecycle
    """
```

**DataJoint provides:**
- ✅ Automatic cleanup (garbage collection)
- ✅ Transactional integrity (atomic with database)
- ✅ Referential integrity (cascading deletes)
- ✅ Content deduplication (for `<blob@>`, `<attach@>`)

**User manages:**
- ❌ File paths (DataJoint decides)
- ❌ Cleanup (automatic)
- ❌ Integrity (enforced)

---

**User-Managed (References)**

Use `<filepath@>`:

```python
class ExternalData(dj.Manual):
    definition = """
    data_id : uuid
    ---
    raw_file : <filepath@>    # User manages file
    """
```

**User provides:**
- ✅ File paths (you control organization)
- ✅ File lifecycle (you create/delete)
- ✅ Existing files (reference external data)

**DataJoint provides:**
- ✅ Path validation (file exists on insert)
- ✅ ObjectRef for lazy access
- ❌ No garbage collection
- ❌ No transaction safety for files
- ❌ No deduplication

**Use when:**
- Files managed by external systems
- Referencing existing data archives
- Custom file organization required
- Large instrument output directories

## Storage Type Comparison

### In-Table: `<blob>`

**Storage:** Database column (LONGBLOB)

**Syntax:**
```python
small_data : <blob>
```

**Characteristics:**
- ✅ Fast access (in database)
- ✅ Transactional consistency
- ✅ Automatic backup
- ✅ No store configuration needed
- ✅ **Python object convenience**: Insert/fetch dicts, lists, arrays directly (no manual IO)
- ✅ Automatic serialization + gzip compression
- ✅ Technical limit: 4 GiB (MySQL), unlimited (PostgreSQL)
- ❌ Practical limit: Keep under ~1-10 MB for performance
- ❌ No deduplication
- ❌ Database bloat for large data

**Best for:**
- Configuration JSON (dicts/lists)
- Small arrays/matrices
- Thumbnails
- Nested data structures

---

### In-Table: `<attach>`

**Storage:** Database column (LONGBLOB)

**Syntax:**
```python
config_file : <attach>
```

**Characteristics:**
- ✅ Fast access (in database)
- ✅ Transactional consistency
- ✅ Automatic backup
- ✅ No store configuration needed
- ✅ **Filename preserved**: Original filename stored with content
- ✅ Automatic gzip compression
- ✅ Technical limit: 4 GiB (MySQL), unlimited (PostgreSQL)
- ❌ Practical limit: Keep under ~1-10 MB for performance
- ❌ No deduplication
- ❌ Returns file path (extracts to download directory), not Python object

**Best for:**
- Small configuration files
- Document attachments (< 10 MB)
- Files where original filename matters
- When you need the file extracted to disk

**Difference from `<blob>`:**
- `<blob>`: Stores Python objects (dicts, arrays) → returns Python object
- `<attach>`: Stores files with filename → returns local file path

---

### Hash-Addressed: `<blob@>` or `<attach@>`

**Storage:** Object store at `{store}/_hash/{schema}/{hash}`

**Syntax:**
```python
data : <blob@>              # Default store
data : <blob@mystore>       # Named store
file : <attach@>            # File attachments
```

**Characteristics (both):**
- ✅ Content deduplication (identical data stored once)
- ✅ Automatic gzip compression
- ✅ Garbage collection
- ✅ Transaction safety
- ✅ Referential integrity
- ✅ Moderate to large files (1 MB - 100 GB)
- ❌ Full download on fetch (no streaming)
- ❌ Storage path not browsable (hash-based)

**`<blob@>` specific:**
- ✅ **Python object convenience**: Insert/fetch dicts, lists, arrays directly (no manual IO)
- Returns: Python objects

**`<attach@>` specific:**
- ✅ **Filename preserved**: Original filename stored with content
- Returns: Local file path (extracts to download directory)

**Best for `<blob@>`:**
- Large Python objects (NumPy arrays, dicts)
- Processed results (nested structures)
- Any Python data with duplicates

**Best for `<attach@>`:**
- PDF/document files
- Images, videos
- Files where original filename/format matters

**Key difference:**
- `<blob@>`: Python objects in, Python objects out (no file handling)
- `<attach@>`: Files in, file paths out (preserves filename)

---

### Schema-Addressed: `<npy@>` or `<object@>`

**Storage:** Object store at `{store}/_schema/{schema}/{table}/{key}/{field}.{token}.ext`

**Syntax:**
```python
array : <npy@>              # NumPy arrays
dataset : <object@>         # Zarr, HDF5, custom
```

**Characteristics:**
- ✅ Streaming access (no full download)
- ✅ Partial reads (fetch chunks)
- ✅ Browsable paths (organized by key)
- ✅ Accessible by external tools (not just DataJoint)
- ✅ Very large files (100 MB - TB+)
- ✅ Multi-file datasets (e.g., Zarr directory structures)
- ❌ No deduplication
- ❌ One file per field per row

**Key advantages:**
- **Schema-addressed storage is browsable** - can be navigated and accessed by external tools (Zarr viewers, HDF5 utilities, direct filesystem access), not just through DataJoint
- **`<npy@>` provides array convenience** - insert/fetch array-like objects directly (no manual .npy file handling)
- **`<object@>` provides flexibility** - you manage the format (Zarr, HDF5, custom), DataJoint provides storage and references

**Best for:**
- `<npy@>`: NumPy arrays with lazy loading (no manual IO)
- `<object@>`: Zarr arrays, HDF5 datasets, custom formats (you manage format)
- Large video files
- Multi-file experimental outputs
- Data that needs to be accessed by non-DataJoint tools

**Difference `<npy@>` vs `<object@>`:**
- `<npy@>`: Insert/fetch array-like objects (like `<blob>` but lazy) - no manual .npy handling
- `<object@>`: You manage format and IO (Zarr, HDF5, custom) - more flexible but requires format knowledge

---

### Filepath References: `<filepath@>`

**Storage:** User-managed paths in object store

**Syntax:**
```python
raw_data : <filepath@>      # User-managed file
```

**Characteristics:**
- ✅ Reference existing files
- ✅ User controls paths
- ✅ External system compatibility
- ✅ Custom organization
- ❌ No lifecycle management
- ❌ No garbage collection
- ❌ No transaction safety
- ❌ No deduplication
- ❌ Must avoid `_hash/` and `_schema/` prefixes

**Best for:**
- Large instrument data directories
- Externally managed archives
- Legacy data integration
- Custom file organization requirements

## Common Scenarios

### Scenario 1: Image Processing Pipeline

```python
@schema
class RawImage(dj.Manual):
    """Imported from microscope"""
    definition = """
    image_id : uuid
    ---
    raw_file : <filepath@acquisition>    # Reference microscope output
    """

@schema
class CalibratedImage(dj.Computed):
    """Calibrated, moderate size"""
    definition = """
    -> RawImage
    ---
    calibrated : <blob@>                 # 5 MB processed image
    """

@schema
class Thumbnail(dj.Computed):
    """Preview for dashboard"""
    definition = """
    -> CalibratedImage
    ---
    preview : <blob>                     # 100 KB thumbnail, in-table
    """
```

**Rationale:**
- `<filepath@>`: Reference existing microscope files (large, externally managed)
- `<blob@>`: Processed images (moderate size, deduplicated if reprocessed)
- `<blob>`: Thumbnails (tiny, fast access for UI)

---

### Scenario 2: Electrophysiology Recording

```python
@schema
class RecordingSession(dj.Manual):
    """Recording metadata"""
    definition = """
    session_id : uuid
    ---
    config : <blob>                      # 50 KB parameters, in-table
    """

@schema
class ContinuousData(dj.Imported):
    """Raw voltage traces"""
    definition = """
    -> RecordingSession
    ---
    raw_voltage : <object@raw>           # 10 GB Zarr array, streaming
    """

@schema
class SpikeWaveforms(dj.Computed):
    """Extracted spike shapes"""
    definition = """
    -> ContinuousData
    unit_id : int64
    ---
    waveforms : <npy@>                   # 20 MB array, lazy load
    """

@schema
class UnitStats(dj.Computed):
    """Summary statistics"""
    definition = """
    -> SpikeWaveforms
    ---
    stats : <blob>                       # 10 KB stats dict, in-table
    """
```

**Rationale:**
- `<blob>`: Config and stats (small metadata, fast access)
- `<object@>`: Raw voltage (huge, stream for spike detection)
- `<npy@>`: Waveforms (moderate arrays, load for clustering)

---

### Scenario 3: Calcium Imaging Analysis

```python
@schema
class Movie(dj.Manual):
    """Raw calcium imaging movie"""
    definition = """
    movie_id : uuid
    ---
    frames : <object@movies>             # 2 GB TIFF stack, streaming
    """

@schema
class SegmentedCells(dj.Computed):
    """Cell masks"""
    definition = """
    -> Movie
    ---
    masks : <npy@>                       # 50 MB mask array, lazy load
    """

@schema
class FluorescenceTraces(dj.Computed):
    """Extracted time series"""
    definition = """
    -> SegmentedCells
    cell_id : int64
    ---
    trace : <blob@>                      # 500 KB per cell, deduplicated
    """

@schema
class TraceSummary(dj.Computed):
    """Event detection results"""
    definition = """
    -> FluorescenceTraces
    ---
    events : <blob>                      # 5 KB event times, in-table
    """
```

**Rationale:**
- `<object@>`: Movies (huge, stream for segmentation)
- `<npy@>`: Masks (moderate, load for trace extraction)
- `<blob@>`: Traces (per-cell, many rows, deduplication helps)
- `<blob>`: Event summaries (tiny, fast query results)

## Configuration Examples

### Single Store (Development)

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

All `@` codecs use this store:
- `<blob@>` → `/data/my-project/_hash/{schema}/{hash}`
- `<npy@>` → `/data/my-project/_schema/{schema}/{table}/{key}/`

---

### Multiple Stores (Production)

```json
{
  "stores": {
    "default": "main",
    "filepath_default": "acquisition",
    "main": {
      "protocol": "file",
      "location": "/data/processed"
    },
    "acquisition": {
      "protocol": "file",
      "location": "/mnt/microscope"
    },
    "archive": {
      "protocol": "s3",
      "bucket": "long-term-storage",
      "location": "lab-data/archive"
    }
  }
}
```

Usage in table definitions:
```python
raw : <filepath@>               # Uses filepath_default (acquisition)
processed : <blob@>             # Uses default (main)
backup : <blob@archive>         # Uses named store (archive)
```

## Performance Considerations

### Read Performance

| Codec | Random Access | Streaming | Latency |
|-------|---------------|-----------|---------|
| `<blob>` | ⚡ Excellent | N/A | <1ms |
| `<blob@>` | ✅ Good | ❌ No | ~100ms |
| `<npy@>` | ✅ Good (lazy) | ✅ Yes | ~100ms + chunk time |
| `<object@>` | ✅ Excellent | ✅ Yes | ~100ms + chunk time |
| `<filepath@>` | ✅ Good | ✅ Yes | ~100ms + network |

### Write Performance

| Codec | Insert Speed | Transaction Safe | Deduplication |
|-------|--------------|------------------|---------------|
| `<blob>` | ⚡ Fastest | ✅ Yes | ❌ No |
| `<blob@>` | ✅ Fast | ✅ Yes | ✅ Yes |
| `<npy@>` | ✅ Fast | ✅ Yes | ❌ No |
| `<object@>` | ✅ Fast | ✅ Yes | ❌ No |
| `<filepath@>` | ⚡ Fastest | ⚠️ Path only | ❌ No |

### Storage Efficiency

| Codec | Deduplication | Compression | Overhead |
|-------|---------------|-------------|----------|
| `<blob>` | ❌ No | ✅ gzip (automatic) | Low |
| `<blob@>` | ✅ Yes | ✅ gzip (automatic) | Medium |
| `<npy@>` | ❌ No | ⚠️ Format-specific | Low |
| `<object@>` | ❌ No | ⚠️ Format-specific | Low |
| `<filepath@>` | ❌ No | User-managed | Minimal |

## Migration Between Storage Types

### In-Table → Object Store

```python
# Add new column with object storage
@schema
class MyTable(dj.Manual):
    definition = """
    id : int
    ---
    data_old : <blob>          # Legacy in-table
    data_new : <blob@>         # New object storage
    """

# Migrate data
for key in MyTable.fetch('KEY'):
    old_data = (MyTable & key).fetch1('data_old')
    (MyTable & key).update1({**key, 'data_new': old_data})

# After verification, drop old column via alter()
```

### Hash-Addressed → Schema-Addressed

```python
# For large files that need streaming
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    data_blob : <blob@>        # Old: full download
    data_stream : <object@>    # New: streaming access
    """

# Convert and store as Zarr
import zarr
for key in Recording.fetch('KEY'):
    data = (Recording & key).fetch1('data_blob')

    # Create Zarr array
    ref = (Recording & key).create_object_ref('data_stream', '.zarr')
    z = zarr.open(ref.fsmap, mode='w', shape=data.shape, dtype=data.dtype)
    z[:] = data

    # Update row
    (Recording & key).update1({**key, 'data_stream': ref})
```

## Troubleshooting

### "DataJointError: Store not configured"

**Problem:** Using `@` without store configuration

**Solution:**
```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/storage"
    }
  }
}
```

### "ValueError: Path conflicts with reserved section"

**Problem:** `<filepath@>` path uses `_hash/` or `_schema/`

**Solution:** Use different path:
```python
# Bad
table.insert1({'id': 1, 'file': '_hash/mydata.bin'})  # Error!

# Good
table.insert1({'id': 1, 'file': 'raw/mydata.bin'})    # OK
```

### Data not deduplicated

**Problem:** Using `<npy@>` or `<object@>` expecting deduplication

**Solution:** Use `<blob@>` for deduplication:
```python
# No deduplication
data : <npy@>

# With deduplication
data : <blob@>
```

### Out of memory loading large array

**Problem:** Using `<blob@>` for huge files

**Solution:** Use `<object@>` or `<npy@>` for streaming:
```python
# Bad: loads 10 GB into memory
large_data : <blob@>

# Good: streaming access
large_data : <object@>
```

## See Also

- [Use Object Storage](use-object-storage.md) — How to use codecs in practice
- [Configure Object Storage](configure-storage.md) — Store configuration
- [Type System](../explanation/type-system.md/) — Complete type system overview
- [Type System Specification](../reference/specs/type-system.md/) — Technical details
- [NPY Codec Specification](../reference/specs/npy-codec.md/) — NumPy array storage
