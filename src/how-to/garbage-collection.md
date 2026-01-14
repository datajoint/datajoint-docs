# Clean Up External Storage

Remove orphaned data from object storage after deleting database rows.

## Why Garbage Collection?

When you delete rows from tables with external storage (`<blob@>`, `<attach@>`,
`<object@>`, `<npy@>`), the database records are removed but the external files
remain. This is by design:

- **Hash-addressed storage** (`<blob@>`, `<attach@>`) uses deduplication—the
  same content may be referenced by multiple rows
- **Schema-addressed storage** (`<object@>`, `<npy@>`) stores each row's data
  at a unique path, but immediate deletion could cause issues with concurrent
  operations

Run garbage collection periodically to reclaim storage space.

## Basic Usage

```python
import datajoint as dj

# Scan for orphaned items (dry run)
stats = dj.gc.scan(schema1, schema2)
print(dj.gc.format_stats(stats))

# Remove orphaned items
stats = dj.gc.collect(schema1, schema2, dry_run=False)
print(dj.gc.format_stats(stats))
```

## Scan Before Collecting

Always scan first to see what would be deleted:

```python
# Check what's orphaned
stats = dj.gc.scan(my_schema)

print(f"Hash-addressed orphaned: {stats['hash_orphaned']}")
print(f"Schema paths orphaned: {stats['schema_paths_orphaned']}")
print(f"Total bytes: {stats['orphaned_bytes'] / 1e6:.1f} MB")
```

## Dry Run Mode

The default `dry_run=True` reports what would be deleted without deleting:

```python
# Safe: shows what would be deleted
stats = dj.gc.collect(my_schema, dry_run=True)
print(dj.gc.format_stats(stats))

# After review, actually delete
stats = dj.gc.collect(my_schema, dry_run=False)
```

## Multiple Schemas

If your data spans multiple schemas, scan all of them together:

```python
# Important: include ALL schemas that might share storage
stats = dj.gc.collect(
    schema_raw,
    schema_processed,
    schema_analysis,
    dry_run=False
)
```

!!! note "Per-schema deduplication"
    Hash-addressed storage is deduplicated **within** each schema. Different
    schemas have independent storage, so you only need to scan schemas that
    share the same database.

## Named Stores

If you use multiple named stores, specify which to clean:

```python
# Clean specific store
stats = dj.gc.collect(my_schema, store_name='archive', dry_run=False)

# Or clean default store
stats = dj.gc.collect(my_schema, dry_run=False)  # uses default store
```

## Verbose Mode

See detailed progress:

```python
stats = dj.gc.collect(
    my_schema,
    dry_run=False,
    verbose=True  # logs each deletion
)
```

## Understanding the Statistics

```python
stats = dj.gc.scan(my_schema)

# Hash-addressed storage (<blob@>, <attach@>, <hash@>)
stats['hash_referenced']      # Items still in database
stats['hash_stored']          # Items in storage
stats['hash_orphaned']        # Unreferenced (can be deleted)
stats['hash_orphaned_bytes']  # Size of orphaned items

# Schema-addressed storage (<object@>, <npy@>)
stats['schema_paths_referenced']  # Paths still in database
stats['schema_paths_stored']      # Paths in storage
stats['schema_paths_orphaned']    # Unreferenced paths
stats['schema_paths_orphaned_bytes']

# Totals
stats['referenced']   # Total referenced items
stats['stored']       # Total stored items
stats['orphaned']     # Total orphaned items
stats['orphaned_bytes']
```

## Scheduled Collection

Run GC periodically in production:

```python
# In a cron job or scheduled task
import datajoint as dj
from myproject import schema1, schema2, schema3

stats = dj.gc.collect(
    schema1, schema2, schema3,
    dry_run=False,
    verbose=True
)

if stats['errors'] > 0:
    logging.warning(f"GC completed with {stats['errors']} errors")
else:
    logging.info(f"GC freed {stats['bytes_freed'] / 1e6:.1f} MB")
```

## How Storage Addressing Works

DataJoint uses two storage patterns:

### Hash-Addressed (`<blob@>`, `<attach@>`, `<hash@>`)

```
_hash/
  {schema}/
    ab/
      cd/
        abcdefghij...  # Content identified by Base32-encoded MD5 hash
```

- Duplicate content shares storage within each schema
- Paths are stored in metadata—safe from config changes
- Cannot delete until no rows reference the content
- GC compares stored paths against filesystem

### Schema-Addressed (`<object@>`, `<npy@>`)

```
myschema/
  mytable/
    primary_key_values/
      attribute_name/
        data.zarr/
        data.npy
```

- Each row has unique path based on schema structure
- Paths mirror database organization
- GC removes paths not referenced by any row

## Troubleshooting

### "At least one schema must be provided"

```python
# Wrong
dj.gc.scan()

# Right
dj.gc.scan(my_schema)
```

### Storage not decreasing

Check that you're scanning all schemas:

```python
# List all schemas that use this store
# Make sure to include them all in the scan
```

### Permission errors

Ensure your storage credentials allow deletion:

```python
# Check store configuration
spec = dj.config.get_object_store_spec('mystore')
# Verify write/delete permissions
```

## See Also

- [Manage Large Data](manage-large-data.md) — Storage patterns and streaming
- [Configure Object Storage](configure-storage.md) — Storage setup
- [Delete Data](delete-data.md) — Row deletion with cascades
