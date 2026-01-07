# Manage Large Data

Work effectively with blobs and object storage.

## Choose the Right Storage

| Data Size | Recommended | Syntax |
|-----------|-------------|--------|
| < 1 MB | Database | `<blob>` |
| 1 MB - 1 GB | Object storage | `<blob@>` |
| > 1 GB | Path-addressed | `<object@>` |

## Streaming Large Results

Avoid loading everything into memory:

```python
# Bad: loads all data at once
all_data = LargeTable.fetch('big_column')

# Good: iterate with limit
for batch in range(0, len(LargeTable), 100):
    data = (LargeTable & f'id >= {batch}').fetch(
        'big_column',
        limit=100
    )
    process(data)
```

## Lazy Loading with ObjectRef

`<object@>` and `<filepath@>` return lazy references:

```python
# Returns ObjectRef, not the actual data
ref = (Dataset & key).fetch1('large_file')

# Stream without full download
with ref.open('rb') as f:
    # Process in chunks
    while chunk := f.read(1024 * 1024):
        process(chunk)

# Or download when needed
local_path = ref.download('/tmp/working')
```

## Selective Fetching

Fetch only what you need:

```python
# Bad: fetches all columns including blobs
row = MyTable.fetch1()

# Good: fetch only metadata
metadata = (MyTable & key).fetch1('name', 'date', 'status')

# Then fetch blob only if needed
if needs_processing(metadata):
    data = (MyTable & key).fetch1('large_data')
```

## Projection for Efficiency

Exclude large columns from joins:

```python
# Slow: joins include blob columns
result = Table1 * Table2

# Fast: project away blobs before join
result = Table1.proj('id', 'name') * Table2.proj('id', 'status')
```

## Batch Inserts

Insert large data efficiently:

```python
# Good: single transaction for related data
with dj.conn().transaction:
    for item in large_batch:
        MyTable.insert1(item)
```

## Content Deduplication

`<blob@>` and `<attach@>` automatically deduplicate:

```python
# Same array inserted twice
data = np.random.randn(1000, 1000)
Table.insert1({'id': 1, 'data': data})
Table.insert1({'id': 2, 'data': data})  # References same storage

# Only one copy exists in object storage
```

## Storage Cleanup

Remove orphaned objects after deletes:

```python
# Objects are NOT automatically deleted with rows
(MyTable & old_data).delete()

# Run garbage collection periodically
# (Implementation depends on your storage backend)
```

## Monitor Storage Usage

Check object store size:

```python
# Get store configuration
spec = dj.config.get_object_store_spec()

# For S3/MinIO, use boto3 or similar
# For filesystem, use standard tools
```

## Compression

Blobs are compressed by default:

```python
# Compression happens automatically in <blob>
large_array = np.zeros((10000, 10000))  # Compresses well
sparse_data = np.random.randn(10000, 10000)  # Less compression
```

## Memory Management

For very large computations:

```python
def make(self, key):
    # Process in chunks
    for chunk_idx in range(n_chunks):
        chunk_data = load_chunk(key, chunk_idx)
        result = process(chunk_data)
        save_partial_result(key, chunk_idx, result)
        del chunk_data  # Free memory

    # Combine results
    final = combine_results(key)
    self.insert1({**key, 'result': final})
```

## External Tools for Very Large Data

For datasets too large for DataJoint:

```python
@schema
class LargeDataset(dj.Manual):
    definition = """
    dataset_id : uuid
    ---
    zarr_path : <filepath@>     # Reference to external Zarr
    """

# Store path reference, process with specialized tools
import zarr
store = zarr.open(local_zarr_path)
# ... process with Zarr/Dask ...

LargeDataset.insert1({
    'dataset_id': uuid.uuid4(),
    'zarr_path': local_zarr_path
})
```

## See Also

- [Use Object Storage](use-object-storage.md) — Storage patterns
- [Configure Object Storage](configure-storage.md) — Storage setup
- [Create Custom Codecs](create-custom-codec.md) — Domain-specific types
