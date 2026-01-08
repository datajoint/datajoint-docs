# What's New in DataJoint 2.0

DataJoint 2.0 is a major release that establishes DataJoint as a mature framework for scientific data pipelines. The version jump from 0.14 to 2.0 reflects the significance of these changes.

## Object-Augmented Schema (OAS)

DataJoint 2.0 unifies relational tables with object storage into a single coherent system. The relational database stores metadata and references while large objects (arrays, files, Zarr datasets) are stored in object storage—with full referential integrity maintained across both layers.

→ [Type System Specification](../reference/specs/type-system.md)

**Three storage sections:**

| Section | Addressing | Use Case |
|---------|------------|----------|
| **Internal** | Row-based (in database) | Small objects (< 1 MB) |
| **Hash-addressed** | Content hash | Arrays, files (deduplication) |
| **Path-addressed** | Primary key path | Zarr, HDF5, streaming access |

**New syntax:**

```python
definition = """
recording_id : uuid
---
metadata : <blob>           # Internal storage
raw_data : <blob@store>     # Hash-addressed object storage
zarr_array : <object@store> # Path-addressed for Zarr/HDF5
"""
```

## Extensible Type System

A three-layer architecture separates Python types, DataJoint core types, and storage.

→ [Type System Specification](../reference/specs/type-system.md) · [Codec API Specification](../reference/specs/codec-api.md)

- **Core types**: Portable types like `int32`, `float64`, `uuid`, `json`
- **Codecs**: Transform Python objects for storage (`<blob>`, `<attach>`, `<object@>`)
- **Custom codecs**: Implement domain-specific types for your data

```python
class GraphCodec(dj.Codec):
    name = "graph"

    def encode(self, value, **kwargs):
        return list(value.edges)

    def decode(self, stored, **kwargs):
        import networkx as nx
        return nx.Graph(stored)
```

## Jobs 2.0

A redesigned job coordination system for distributed computing.

→ [AutoPopulate Specification](../reference/specs/autopopulate.md) · [Job Metadata Specification](../reference/specs/job-metadata.md)

- **Per-table jobs**: Each computed table has its own jobs table (`Table.jobs`)
- **Automatic refresh**: Job queue synchronized with pending work
- **Distributed coordination**: Multiple workers coordinate via database
- **Error tracking**: Built-in error table with stack traces

```python
# Distributed mode with coordination
Analysis.populate(reserve_jobs=True, processes=4)

# Monitor progress
Analysis.jobs.progress()  # {'pending': 10, 'reserved': 2, 'error': 0}

# Handle errors
Analysis.jobs.errors.to_dicts()
```

## Semantic Matching

Query operations now use **lineage-based matching**—attributes are matched not just by name but by their origin through foreign key chains. This prevents accidental matches between attributes that happen to share a name but represent different concepts.

→ [Semantic Matching Specification](../reference/specs/semantic-matching.md)

```python
# Attributes matched by lineage, not just name
result = TableA * TableB  # Semantic join (default)
```

## Configuration System

A cleaner configuration approach with separation of concerns.

→ [Configuration Reference](../reference/configuration.md)

- **`datajoint.json`**: Non-sensitive settings (commit to version control)
- **`.secrets/`**: Credentials (never commit)
- **Environment variables**: For CI/CD and production

```bash
export DJ_HOST=db.example.com
export DJ_USER=myuser
export DJ_PASS=mypassword
```

## ObjectRef API

Path-addressed storage returns `ObjectRef` handles that support streaming access:

```python
ref = (Dataset & key).fetch1('zarr_array')

# Direct fsspec access for Zarr/xarray
z = zarr.open(ref.fsmap, mode='r')

# Or download locally
local_path = ref.download('/tmp/data')
```

## License Change

DataJoint 2.0 is licensed under the **Apache License 2.0** (previously LGPL). This provides more flexibility for commercial and academic use.

## Migration Path

Upgrading from DataJoint 0.x requires:

1. Update configuration files
2. Update blob syntax (`longblob` → `<blob>`)
3. Update jobs code (schema-level → per-table)
4. Test semantic matching behavior

See [Migrate from 0.x](../how-to/migrate-from-0x.md) for detailed upgrade steps.

## See Also

- [Installation](../how-to/installation.md) — Get started with DataJoint 2.0
- [Tutorials](../tutorials/index.md) — Learn DataJoint step by step
- [Type System](type-system.md) — Core types and codecs
- [Computation Model](computation-model.md) — Jobs 2.0 details
