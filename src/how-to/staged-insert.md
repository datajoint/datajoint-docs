# Staged Insert

Write large objects directly to object storage as part of an atomic insert.

## Overview

`staged_insert1` is a context manager for inserting rows whose object-typed fields are too large to copy through local storage first. It writes directly to the destination object store while the row is being built, then finalizes the database insert when the block exits cleanly. If an exception is raised inside the block, the staged objects are cleaned up and no row is inserted.

This pattern is the right choice when:

- Objects are large (multi-GB arrays, long recordings, image stacks)
- You want to stream or write in chunks rather than buffer in memory
- You want all-or-nothing semantics across object storage and the database

It is only available for object-typed fields (`<...@>` syntax) and codecs that support direct storage handles — primarily `<object@>` (Zarr / HDF5 / multi-file) and `<blob@>` written via a file handle. For ordinary inserts of small or in-memory objects, use [`insert` / `insert1`](insert-data.md).

## Quick Start

```python
import zarr
import datajoint as dj

schema = dj.Schema('imaging')

@schema
class ImagingSession(dj.Manual):
    definition = """
    subject_id : int32
    session_id : int32
    ---
    n_frames   : int32
    frame_rate : float32
    frames     : <object@>
    """

with ImagingSession.staged_insert1 as staged:
    # 1. Set primary key values first
    staged.rec['subject_id'] = 1
    staged.rec['session_id'] = 1

    # 2. Get a storage handle for the object field
    store = staged.store('frames', '.zarr')

    # 3. Write directly to object storage (no local copy)
    z = zarr.open(store, mode='w', shape=(1000, 512, 512),
                  chunks=(10, 512, 512), dtype='int32')
    for i in range(1000):
        z[i] = acquire_frame()

    # 4. Set remaining record attributes
    staged.rec['n_frames'] = 1000
    staged.rec['frame_rate'] = 30.0

# On clean exit: metadata is computed, row is inserted
# On exception: staged objects are removed, no row is inserted
```

## How It Works

Inside the `with` block, the row is a draft — `staged.rec` collects attribute values, and `staged.store(field, ext)` / `staged.open(field, ext)` return handles that write directly to the destination object store.

When the block exits without an exception, DataJoint:

1. Computes object metadata (size, manifest, content hash for hash-addressed codecs) from the staged objects.
2. Inserts the row into the database with the populated metadata.

When the block raises, DataJoint:

1. Removes any objects that were written inside the block.
2. Skips the database insert.

This gives the same atomicity guarantee as an ordinary `insert1` — readers never see a row whose object data is partial.

## API Reference

### `Table.staged_insert1`

```python
with Table.staged_insert1 as staged:
    ...
```

Context manager property on every `dj.Table` subclass. Yields a `StagedInsert` object scoped to one row.

### `staged.rec`

A dict for the row's attribute values. Set primary key fields **before** calling `staged.store()` or `staged.open()` — the storage path is derived from the primary key.

```python
staged.rec['subject_id'] = 1
staged.rec['session_id'] = 1
```

### `staged.store(field, ext='')`

Returns an `fsspec.FSMap` for an object field. Suitable for Zarr, xarray, or any library that takes a mapping-style store.

```python
store = staged.store('frames', '.zarr')
z = zarr.open(store, mode='w', shape=..., dtype=...)
```

### `staged.open(field, ext='', mode='wb')`

Returns a file-like object for an object field. Suitable for HDF5, raw binary, or any library that takes a file handle.

```python
with staged.open('recording', '.h5') as f:
    h5py.File(f, mode='w').create_dataset('data', data=arr)
```

### `staged.fs`

The underlying `fsspec.AbstractFileSystem` for advanced operations (listing, deleting, custom paths). Most users won't need this.

## Patterns

### Zarr arrays

```python
with Recording.staged_insert1 as staged:
    staged.rec['recording_id'] = recording_id
    z = zarr.open(staged.store('frames', '.zarr'), mode='w',
                  shape=(n_frames, h, w), chunks=(1, h, w), dtype='uint16')
    for i, frame in enumerate(stream):
        z[i] = frame
```

### HDF5 files

```python
import h5py

with Recording.staged_insert1 as staged:
    staged.rec['recording_id'] = recording_id
    with staged.open('raw', '.h5') as f:
        with h5py.File(f, 'w') as h5:
            h5.create_dataset('signal', data=signal, chunks=True)
            h5.attrs['fs'] = sampling_rate
```

### Streaming from an instrument

Set the primary key, get the handle, then write as data arrives. The block exits — and the row commits — only after the stream is fully captured:

```python
with ImagingSession.staged_insert1 as staged:
    staged.rec['subject_id'] = subject_id
    staged.rec['session_id'] = session_id

    z = zarr.open(staged.store('frames', '.zarr'), mode='w', ...)
    for i in range(n_frames):
        z[i] = camera.grab()

    staged.rec['n_frames'] = n_frames
```

If the camera errors out mid-stream, the partial Zarr is removed and the row is not inserted.

## Error Handling and Atomicity

A `staged_insert1` block is atomic across object storage and the database:

- **Object storage**: anything written via `staged.store()` / `staged.open()` is staged under a path derived from the primary key. On exception inside the block, those staged objects are removed.
- **Database**: the row is only inserted on clean exit.

If the database insert itself fails on exit (e.g., duplicate primary key), the staged objects are also removed.

## Limitations

- Only one row per block — use a loop of `with` blocks for many rows, or use the standard `insert` for batches that fit in memory.
- The block must set all primary key fields before calling `store()` or `open()`.
- Requires `stores.default` configured, or a named store referenced by the field's type spec.

## Troubleshooting

### `Storage is not configured`

Set `stores.default` and `stores.<name>` in `datajoint.json` or via `dj.config`. See [Configure Object Storage](configure-storage.md).

### `Primary key not set` when calling `staged.store()`

Set primary key attributes on `staged.rec` before calling `staged.store()` or `staged.open()`. The object path depends on the primary key.

## See Also

- [Insert Data](insert-data.md) — Standard insert for ordinary rows
- [Use Object Storage](use-object-storage.md) — Object-augmented schemas and storage types
- [Configure Object Storage](configure-storage.md) — Store configuration
- [Use the `<npy>` Codec](use-npy-codec.md) — NumPy array storage with lazy fetch
