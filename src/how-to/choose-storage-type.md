# Choose a Storage Type

Select the right storage codec for your data based on size, access patterns, and lifecycle requirements.

## Quick Decision Tree

```
Start: What type of data are you storing?

├─ Small data (< 1 MB per row)?
│  └─ YES → Use <blob> (in-table storage)
│  └─ NO  → Continue...
│
├─ Externally managed files?
│  └─ YES → Use <filepath@> (reference only)
│  └─ NO  → Continue...
│
├─ Need streaming or partial reads?
│  └─ YES → Use <object@> (schema-addressed, Zarr/HDF5)
│  └─ NO  → Continue...
│
├─ NumPy arrays that benefit from lazy loading?
│  └─ YES → Use <npy@> (optimized NumPy storage)
│  └─ NO  → Use <blob@> (hash-addressed, general purpose)
```

## Storage Types Overview

| Codec | Location | Addressing | Dedup | Best For |
|-------|----------|------------|-------|----------|
| `<blob>` | In-table (database) | Row-based | No | Small objects < 1 MB |
| `<blob@>` | Object store | Content hash | Yes | Large blobs, attachments |
| `<npy@>` | Object store | Schema + key | No | NumPy arrays (lazy load) |
| `<object@>` | Object store | Schema + key | No | Zarr, HDF5, streaming |
| `<filepath@>` | Object store | User path | No | External file references |

## Detailed Decision Criteria

### Size Guidelines

**< 1 MB: In-Table Storage**

```python
@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : uuid
    ---
    metadata : <blob>         # JSON, small arrays, parameters
    thumbnail : <blob>        # Small preview images
    """
```

**Why:**
- Fast access (no external fetch)
- Transactional consistency
- Automatic backup with database
- No storage configuration needed

**Examples:**
- Configuration JSON (< 100 KB)
- Small parameter arrays (< 1 MB)
- Thumbnails (< 500 KB)
- Text data, metadata

---

**1 MB - 100 MB: Hash-Addressed Storage**

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid
    ---
    waveform : <blob@>        # 10 MB array
    notes : <attach@>         # PDF attachments
    """
```

**Why:**
- Content deduplication (saves space)
- Suitable for moderate-sized data
- Simple storage management
- Good for write-once data

**Examples:**
- Neural waveforms (1-50 MB)
- Image files (1-20 MB)
- PDF attachments
- Processed results

---

**> 100 MB: Schema-Addressed Storage**

```python
@schema
class ScanVolume(dj.Manual):
    definition = """
    scan_id : uuid
    ---
    volume : <object@>        # 5 GB Zarr array
    """
```

**Why:**
- Streaming access (don't download full dataset)
- Partial reads (fetch only needed chunks)
- Browsable storage structure
- Better for very large files

**Examples:**
- Zarr arrays (> 100 MB)
- HDF5 datasets
- Large video files (> 1 GB)
- Multi-file datasets

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
- ❌ Size limit (~1 MB practical)
- ❌ No deduplication
- ❌ Database bloat for large data

**Best for:**
- Configuration JSON
- Small arrays/matrices
- Thumbnails
- Metadata blobs

---

### Hash-Addressed: `<blob@>` or `<attach@>`

**Storage:** Object store at `{store}/_hash/{schema}/{hash}`

**Syntax:**
```python
data : <blob@>              # Default store
data : <blob@mystore>       # Named store
file : <attach@>            # File attachments
```

**Characteristics:**
- ✅ Content deduplication (identical data stored once)
- ✅ Garbage collection
- ✅ Transaction safety
- ✅ Referential integrity
- ✅ Moderate to large files (1 MB - 100 GB)
- ❌ Full download on fetch (no streaming)
- ❌ Storage path not browsable

**Best for:**
- Neural waveforms
- Processed images
- PDF/document attachments
- Any write-once data with duplicates

**Difference `<blob@>` vs `<attach@>`:**
- `<blob@>`: Stores Python objects (pickled)
- `<attach@>`: Stores files as-is (preserves format)

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
- ✅ Very large files (100 MB - TB+)
- ✅ Multi-file datasets
- ❌ No deduplication
- ❌ One file per field per row

**Best for:**
- Zarr arrays (multi-dimensional data)
- HDF5 datasets
- Large video files
- Multi-file experimental outputs

**Difference `<npy@>` vs `<object@>`:**
- `<npy@>`: Optimized for NumPy (lazy loading, slicing)
- `<object@>`: General purpose (Zarr, HDF5, custom formats)

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
    unit_id : uint32
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
    cell_id : uint32
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
| `<blob>` | ❌ No | ❌ No | Low |
| `<blob@>` | ✅ Yes | ⚠️ Can add | Medium |
| `<npy@>` | ❌ No | ⚠️ External | Low |
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
- [Type System](../explanation/type-system.md) — Complete type system overview
- [Type System Specification](../reference/specs/type-system.md) — Technical details
- [NPY Codec Specification](../reference/specs/npy-codec.md) — NumPy array storage
