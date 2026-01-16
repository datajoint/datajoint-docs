# `<npy>` Codec Specification

Schema-addressed storage for numpy arrays as portable `.npy` files.

## Overview

The `<npy@>` codec stores numpy arrays as standard `.npy` files using
schema-addressed paths that mirror the database structure. On fetch, it returns
`NpyRef`—a lazy reference that provides metadata access without downloading,
and transparent numpy integration via the `__array__` protocol.

**Key characteristics:**

- **Store only**: Requires `@` modifier (`<npy@>` or `<npy@store>`)
- **Schema-addressed**: Paths mirror database structure (`{schema}/{table}/{pk}/{attr}.npy`)
- **Lazy loading**: Shape/dtype available without download
- **Transparent**: Use directly in numpy operations
- **Portable**: Standard `.npy` format readable by numpy, MATLAB, etc.

## Quick Start

```python
import datajoint as dj
import numpy as np

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int
    ---
    waveform : <npy@>
    """

# Insert - just pass the array
Recording.insert1({
    'recording_id': 1,
    'waveform': np.random.randn(1000, 32),
})

# Fetch - returns NpyRef (lazy)
ref = (Recording & 'recording_id=1').fetch1('waveform')

# Metadata without download
ref.shape   # (1000, 32)
ref.dtype   # float64

# Use in numpy ops - downloads automatically
mean = np.mean(ref, axis=0)

# Or load explicitly
arr = ref.load()
```

## NpyRef: Lazy Array Reference

When you fetch an `<npy@>` attribute, you get an `NpyRef` object:

```python
ref = (Recording & key).fetch1('waveform')
type(ref)  # <class 'datajoint.builtin_codecs.NpyRef'>
```

### Metadata Access (No I/O)

```python
ref.shape    # tuple: (1000, 32)
ref.dtype    # numpy.dtype: float64
ref.ndim     # int: 2
ref.size     # int: 32000
ref.nbytes   # int: 256000 (estimated)
ref.path     # str: "my_schema/recording/recording_id=1/waveform.npy"
ref.store    # str or None: store name
ref.is_loaded  # bool: False (until loaded)
```

### Loading Data

**Explicit loading:**
```python
arr = ref.load()  # Downloads, caches, returns np.ndarray
arr = ref.load()  # Returns cached copy (no re-download)
```

**Implicit loading via `__array__`:**
```python
# These all trigger automatic download
result = ref + 1
result = np.mean(ref)
result = np.dot(ref, weights)
arr = np.asarray(ref)
```

**Indexing/slicing:**
```python
first_row = ref[0]      # Loads then indexes
subset = ref[100:200]   # Loads then slices
```

### Memory Mapping

For very large arrays, use `mmap_mode` to access data without loading it all:

```python
# Memory-mapped loading (random access)
arr = ref.load(mmap_mode='r')

# Efficient random access - only reads needed portions
slice = arr[1000:2000, :]
chunk = arr[::100]
```

**Modes:**
- `'r'` - Read-only (recommended)
- `'r+'` - Read-write (modifications persist)
- `'c'` - Copy-on-write (changes not saved)

**Performance characteristics:**
- Local filesystem stores: memory-maps the file directly (zero-copy)
- Remote stores (S3, GCS): downloads to local cache first, then memory-maps

**When to use:**
- Arrays too large to fit in memory
- Only need random access to portions of the array
- Processing data in chunks

### Safe Bulk Fetch

The lazy design protects against accidental mass downloads:

```python
# Fetch 10,000 recordings - NO downloads happen yet
recs = Recording.fetch()

# Inspect without downloading
for rec in recs:
    ref = rec['waveform']
    print(f"Shape: {ref.shape}, dtype: {ref.dtype}")  # No I/O

# Download only what you need
large_arrays = [rec['waveform'] for rec in recs if rec['waveform'].shape[0] > 1000]
for ref in large_arrays:
    process(ref.load())  # Downloads here
```

### Repr for Debugging

```python
>>> ref
NpyRef(shape=(1000, 32), dtype=float64, not loaded)

>>> ref.load()
>>> ref
NpyRef(shape=(1000, 32), dtype=float64, loaded)
```

## Table Definition

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int
    ---
    waveform : <npy@>           # default store
    spectrogram : <npy@archive>  # specific store
    """
```

## Storage Details

### Addressing Scheme

The `<npy@>` codec uses **schema-addressed** storage, where paths mirror the
database schema structure. This creates a browsable organization in object
storage that reflects your data model.

### Type Chain

```
<npy@> → "json" (metadata stored in JSON column)
```

### File Format

- Format: NumPy `.npy` (version 1.0 or 2.0 depending on array size)
- Encoding: `numpy.save()` with `allow_pickle=False`
- Extension: `.npy`

### Schema-Addressed Path Construction

```
{schema}/{table}/{primary_key_values}/{attribute}.npy
```

Example: `lab_ephys/recording/recording_id=1/waveform.npy`

This schema-addressed layout means you can browse the object store and understand
the organization because it mirrors your database schema.

### JSON Metadata

The database column stores:

```json
{
  "path": "lab_ephys/recording/recording_id=1/waveform.npy",
  "store": "main",
  "dtype": "float64",
  "shape": [1000, 32]
}
```

## Validation

The codec validates on insert:

- Value must be `numpy.ndarray`
- Array must not have `object` dtype

```python
# Valid
Recording.insert1({'recording_id': 1, 'waveform': np.array([1, 2, 3])})

# Invalid - not an array
Recording.insert1({'recording_id': 1, 'waveform': [1, 2, 3]})
# DataJointError: <npy> requires numpy.ndarray, got list

# Invalid - object dtype
Recording.insert1({'recording_id': 1, 'waveform': np.array([{}, []])})
# DataJointError: <npy> does not support object dtype arrays
```

## Direct File Access

Files are stored at predictable paths and can be accessed directly:

```python
# Get the storage path
ref = (Recording & 'recording_id=1').fetch1('waveform')
print(ref.path)  # "my_schema/recording/recording_id=1/waveform.npy"

# Load directly with numpy (if you have store access)
arr = np.load('/path/to/store/my_schema/recording/recording_id=1/waveform.npy')
```

## Comparison with Other Codecs

| Codec | Format | Addressing | Lazy | Memory Map | Portability |
|-------|--------|------------|------|------------|-------------|
| `<npy@>` | `.npy` | Schema | Yes (NpyRef) | Yes | High (numpy, MATLAB) |
| `<object@>` | varies | Schema | Yes (ObjectRef) | No | Depends on content |
| `<blob@>` | pickle | Hash | No | No | Python only |
| `<hash@>` | raw bytes | Hash | No | No | N/A |

**Addressing schemes:**
- **Schema-addressed**: Path mirrors database structure. Browsable, one location per entity.
- **Hash-addressed**: Path from content hash. Automatic deduplication.

## When to Use `<npy@>`

**Use `<npy@>` when:**
- Storing single numpy arrays
- Interoperability matters (non-Python tools)
- You want lazy loading with metadata inspection
- Fetching many rows where not all arrays are needed
- Random access to large arrays via memory mapping
- Browsable object store organization is valuable

**Use `<blob@>` when:**
- Storing arbitrary Python objects (dicts, lists, mixed types)
- Arrays are small and eager loading is fine
- MATLAB compatibility with DataJoint's mYm format is needed
- Deduplication is beneficial (hash-addressed)

**Use `<object@>` when:**
- Storing files/folders (Zarr, HDF5, multi-file outputs)
- Content is not a single numpy array

## Limitations

1. **Single array only**: For multiple arrays, use separate attributes or `<object@>` with `.npz`
2. **No compression**: For compressed storage, use a custom codec with `numpy.savez_compressed`
3. **No object dtype**: Arrays containing arbitrary Python objects are not supported
4. **Store only**: Cannot store inline in the database column

## See Also

- [Type System Specification](type-system.md) - Complete type system overview
- [Codec API](codec-api.md) - Creating custom codecs
- [Schema-Addressed Storage](type-system.md#objectobjectstore-schema-addressed-storage) - Path-addressed storage details
