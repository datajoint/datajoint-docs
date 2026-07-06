# Clean Up Object Storage

Remove orphaned data from object storage after deleting database rows.

## Why Garbage Collection?

When you delete rows from tables with in-store types (`<blob@>`, `<attach@>`,
`<object@>`, `<npy@>`), the database records are removed but the stored objects
remain. This is by design:

- **Hash-addressed storage** (`<blob@>`, `<attach@>`) uses deduplication—the
  same content may be referenced by multiple rows
- **Schema-addressed storage** (`<object@>`, `<npy@>`) stores each row's data
  at a unique path, but immediate deletion could cause issues with concurrent
  operations

Run garbage collection periodically to reclaim storage space.

!!! note "Concurrency semantics"
    Garbage collection is single-pass and best-effort: it scans references,
    then deletes objects the scan did not see referenced. If a row is inserted
    between the scan and the delete, the object it references can be deleted
    even though it is now in use — leaving the new row with a dangling
    reference. A future release will add quarantine-based serialization to
    close this window. Until then, prefer running GC during quiet periods, and
    treat any single GC pass as best-effort rather than transactionally safe.

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

!!! warning "Per-schema paths and multi-schema stores"
    Every hash-addressed path embeds the schema name
    (`{hash_prefix}/{schema}/{hash}`), so deduplication is scoped **within**
    each schema and every stored object is attributable to the schema that
    wrote it. Orphan detection, however, lists the **entire store** on the
    storage side: a schema that uses the store but is not passed to
    `scan()`/`collect()` has its live objects misclassified as orphans —
    and deleted. Always pass **every** schema that uses the store. The same
    per-schema attribution is what makes leftovers of fully dropped schemas
    identifiable and reclaimable by a later `collect()`.

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
{hash_prefix}/                     # store setting, default: _hash/
  {schema}/
    ab/
      cd/
        abcdefghij...  # Content identified by Base32-encoded MD5 hash
```

- The section location comes from the store's `hash_prefix` setting
  (default `_hash`) — the same value the writer uses, so scanner and writer
  cannot drift
- Duplicate content shares storage within each schema — the schema name is
  part of every path, which is what scopes deduplication and lets GC
  attribute each stored object to a schema
- Paths are stored in metadata—safe from config changes
- Cannot delete until no rows reference the content
- GC compares stored paths against the filesystem

### Schema-Addressed (`<object@>`, `<npy@>`)

```
{schema_prefix}/                   # store setting, default: _schema/
  {schema}/
    {table}/
      {primary_key_values}/
        {attribute}_{token}.npy         # single-file object
        {attribute}_{token}.zarr/       # folder object (many files)
        {attribute}_{token}.zarr.manifest.json
```

- The section location comes from the store's `schema_prefix` setting
  (default `_schema`). DataJoint 2.3.0 and earlier wrote these objects at
  root level (`{schema}/...`); GC lists both layouts, so legacy objects
  remain reclaimable
- Every write gets a unique random token, so multiple versions of a row's
  object can coexist; GC reclaims superseded tokens
- Orphan matching is coverage-based: a stored file is live if it **is** a
  referenced path, lies **under** a referenced folder object, or is its
  `.manifest.json` sidecar — live folder objects are never partially
  collected
- GC never touches the store's declared `filepath_prefix` namespace
  (user-managed `<filepath@>` files)

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
