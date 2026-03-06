# Use the `<npy>` Codec

Store NumPy arrays with lazy loading and metadata access.

## Overview

The `<npy@>` codec stores NumPy arrays as portable `.npy` files in object storage. On fetch, you get an `NpyRef` that provides metadata without downloading.

**Key benefits:**
- Access shape, dtype, size without I/O
- Lazy loading - download only when needed
- Memory mapping - random access to large arrays
- Safe bulk fetch - inspect before downloading
- Portable `.npy` format

## Quick Start

### 1. Configure a Store

```python
import datajoint as dj

# Add store configuration
dj.config.object_storage.stores['mystore'] = {
    'protocol': 's3',
    'endpoint': 'localhost:9000',
    'bucket': 'my-bucket',
    'access_key': 'access_key',
    'secret_key': 'secret_key',
    'location': 'data',
}
```

Or in `datajoint.json`:
```json
{
  "object_storage": {
    "stores": {
      "mystore": {
        "protocol": "s3",
        "endpoint": "s3.amazonaws.com",
        "bucket": "my-bucket",
        "location": "data"
      }
    }
  }
}
```

### 2. Define Table with `<npy@>`

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int32
    ---
    waveform : <npy@mystore>
    """
```

### 3. Insert Arrays

```python
import numpy as np

Recording.insert1({
    'recording_id': 1,
    'waveform': np.random.randn(1000, 32),
})
```

### 4. Fetch with Lazy Loading

```python
# Returns NpyRef, not array
ref = (Recording & 'recording_id=1').fetch1('waveform')

# Metadata without download
print(ref.shape)   # (1000, 32)
print(ref.dtype)   # float64

# Load when ready
arr = ref.load()
```

## NpyRef Reference

### Metadata Properties (No I/O)

```python
ref.shape      # Tuple of dimensions
ref.dtype      # NumPy dtype
ref.ndim       # Number of dimensions
ref.size       # Total elements
ref.nbytes     # Total bytes
ref.path       # Storage path
ref.store      # Store name
ref.is_loaded  # Whether data is cached
```

### Loading Methods

```python
# Explicit load (recommended)
arr = ref.load()

# Via NumPy functions (auto-loads)
mean = np.mean(ref)
std = np.std(ref, axis=0)

# Via conversion (auto-loads)
arr = np.asarray(ref)

# Indexing (loads then indexes)
first_row = ref[0]
snippet = ref[100:200, :]
```

### Memory Mapping

For large arrays, use `mmap_mode` to access data without loading it all into memory:

```python
# Memory-mapped loading (random access)
arr = ref.load(mmap_mode='r')

# Only reads the portion you access
slice = arr[1000:2000, :]  # Efficient for large arrays
```

**Modes:**
- `'r'` - Read-only (recommended)
- `'r+'` - Read-write
- `'c'` - Copy-on-write (changes not saved)

**Performance:**
- Local filesystem stores: mmaps directly (no copy)
- Remote stores (S3): downloads to cache first, then mmaps

## Common Patterns

### Bulk Fetch with Filtering

```python
# Fetch all - returns NpyRefs, not arrays
results = MyTable.to_dicts()

# Filter by metadata (no downloads)
large = [r for r in results if r['data'].shape[0] > 1000]

# Load only what you need
for rec in large:
    arr = rec['data'].load()
    process(arr)
```

### Computed Tables

```python
@schema
class ProcessedData(dj.Computed):
    definition = """
    -> RawData
    ---
    result : <npy@mystore>
    """

    def make(self, key):
        # Fetch lazy reference
        ref = (RawData & key).fetch1('raw')

        # NumPy functions auto-load
        result = np.fft.fft(ref, axis=1)

        self.insert1({**key, 'result': result})
```

### Memory-Efficient Processing

```python
# Process recordings one at a time
for key in Recording.keys():
    ref = (Recording & key).fetch1('data')

    # Check size before loading
    if ref.nbytes > 1e9:  # > 1 GB
        print(f"Skipping large recording: {ref.nbytes/1e9:.1f} GB")
        continue

    process(ref.load())
```

## Comparison with `<blob@>`

| Aspect | `<npy@>` | `<blob@>` |
|--------|----------|----------|
| **On fetch** | NpyRef (lazy) | Array (eager) |
| **Metadata access** | Without download | Must download |
| **Memory mapping** | Yes, via `mmap_mode` | No |
| **Addressing** | Schema-addressed | Hash-addressed |
| **Deduplication** | No | Yes |
| **Format** | `.npy` (portable) | DJ blob (Python) |
| **Best for** | Large arrays, lazy loading | Small arrays, dedup |

### When to Use Each

**Use `<npy@>` when:**
- Arrays are large (> 10 MB)
- You need to inspect shape/dtype before loading
- Fetching many rows but processing few
- Random access to slices of very large arrays (memory mapping)
- Interoperability matters (non-Python tools)

**Use `<blob@>` when:**
- Arrays are small (< 10 MB)
- Same arrays appear in multiple rows (deduplication)
- Storing non-array Python objects (dicts, lists)

## Supported Array Types

The `<npy>` codec supports any NumPy array except object dtype:

```python
# Supported
np.array([1, 2, 3], dtype=np.int32)          # Integer
np.array([1.0, 2.0], dtype=np.float64)       # Float
np.array([True, False], dtype=np.bool_)      # Boolean
np.array([1+2j, 3+4j], dtype=np.complex128)  # Complex
np.zeros((10, 10, 10))                       # N-dimensional
np.array(42)                                 # 0-dimensional scalar

# Structured arrays
dt = np.dtype([('x', np.float64), ('y', np.float64)])
np.array([(1.0, 2.0), (3.0, 4.0)], dtype=dt)

# NOT supported
np.array([{}, []], dtype=object)  # Object dtype
```

## Troubleshooting

### "Store not configured"

Ensure your store is configured before using `<npy@store>`:

```python
dj.config.object_storage.stores['store'] = {...}
```

### "requires @ (store only)"

The `<npy>` codec requires the `@` modifier:

```python
# Wrong
data : <npy>

# Correct
data : <npy@>
data : <npy@mystore>
```

### Memory issues with large arrays

Use lazy loading or memory mapping to control memory:

```python
# Check size before loading
if ref.nbytes > available_memory:
    # Use memory mapping for random access
    arr = ref.load(mmap_mode='r')
    # Process in chunks
    for i in range(0, len(arr), chunk_size):
        process(arr[i:i+chunk_size])
else:
    arr = ref.load()
```

## See Also

- [Use Object Storage](use-object-storage.md) - Complete storage guide
- [Configure Object Storage](configure-storage.md) - Store setup
- [`<npy>` Codec Specification](../reference/specs/npy-codec.md/) - Full spec
