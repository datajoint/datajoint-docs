# What's New in DataJoint 2.0

DataJoint 2.0 is a major release that establishes DataJoint as a mature framework for scientific data pipelines. The version jump from 0.14 to 2.0 reflects the significance of these changes.

> **📘 Upgrading from legacy DataJoint (pre-2.0)?**
>
> This page summarizes new features and concepts. For step-by-step migration instructions, see the **[Migration Guide](../how-to/migrate-to-v20.md)**.

## Overview

DataJoint 2.0 introduces fundamental improvements to type handling, job coordination, and object storage while maintaining compatibility with your existing pipelines during migration. Key themes:

- **Explicit over implicit**: All type conversions are now explicit through the codec system
- **Better distributed computing**: Per-table job coordination with improved error handling
- **Object storage integration**: Native support for large arrays and files
- **Future-proof architecture**: Portable types preparing for PostgreSQL backend support

### Breaking Changes at a Glance

If you're upgrading from legacy DataJoint, these changes require code updates:

| Area | Legacy | 2.0 |
|------|--------|-----|
| **Fetch API** | `table.fetch()` | `table.to_dicts()` or `.to_arrays()` |
| **Update** | `(table & key)._update('attr', val)` | `table.update1({**key, 'attr': val})` |
| **Join** | `table1 @ table2` | `table1 * table2` (with semantic check) |
| **Type syntax** | `longblob`, `int unsigned` | `<blob>`, `int64` |
| **Jobs** | `~jobs` table | Per-table `~~table_name` |

See the [Migration Guide](../how-to/migrate-to-v20.md) for complete upgrade steps.

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

## Explicit Type System

**Breaking change**: DataJoint 2.0 makes all type conversions explicit through a three-tier architecture.

→ [Type System Specification](../reference/specs/type-system.md) · [Codec API Specification](../reference/specs/codec-api.md)

### What Changed

Legacy DataJoint overloaded MySQL types with implicit conversions:
- `longblob` could be blob serialization OR in-table attachment
- `attach` was implicitly converted to longblob
- `uuid` was used internally for external storage

**DataJoint 2.0 makes everything explicit:**

| Legacy (Implicit) | 2.0 (Explicit) |
|-------------------|----------------|
| `longblob` | `<blob>` |
| `attach` | `<attach>` |
| `blob@store` | `<blob@store>` |
| `int unsigned` | `int64` |

### Three-Tier Architecture

1. **Native types**: MySQL types (`INT`, `VARCHAR`, `LONGBLOB`)
2. **Core types**: Portable aliases (`int32`, `float64`, `varchar`, `uuid`, `json`)
3. **Codecs**: Serialization for Python objects (`<blob>`, `<attach>`, `<object@>`)

### Custom Codecs

Replace legacy AdaptedTypes with the new codec API:

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

**Breaking change**: Redesigned job coordination with per-table job management.

→ [AutoPopulate Specification](../reference/specs/autopopulate.md) · [Job Metadata Specification](../reference/specs/job-metadata.md)

### What Changed

| Legacy (Schema-level) | 2.0 (Per-table) |
|----------------------|-----------------|
| One `~jobs` table per schema | One `~~table_name` per Computed/Imported table |
| Opaque hashed keys | Native primary keys (readable) |
| Statuses: `reserved`, `error`, `ignore` | Added: `pending`, `success` |
| No priority support | Priority column (lower = more urgent) |

### New Features

- **Automatic refresh**: Job queue synchronized with pending work automatically
- **Better coordination**: Multiple workers coordinate via database without conflicts
- **Error tracking**: Built-in error table (`Table.jobs.errors`) with full stack traces
- **Priority support**: Control computation order with priority values

```python
# Distributed mode with coordination
Analysis.populate(reserve_jobs=True, processes=4)

# Monitor progress
Analysis.jobs.progress()  # {'pending': 10, 'reserved': 2, 'error': 0}

# Handle errors
Analysis.jobs.errors.to_dicts()

# Set priorities
Analysis.jobs.update({'session_id': 123}, priority=1)  # High priority
```

## Semantic Matching

**Breaking change**: Query operations now use **lineage-based matching** by default.

→ [Semantic Matching Specification](../reference/specs/semantic-matching.md)

### What Changed

Legacy DataJoint used SQL-style natural joins: attributes matched if they had the same name, regardless of meaning.

**DataJoint 2.0 validates semantic lineage**: Attributes must share common origin through foreign key chains, not just coincidentally matching names.

```python
# 2.0: Semantic join (default) - validates lineage
result = TableA * TableB  # Only matches attributes with shared origin

# Legacy behavior (if needed)
result = TableA.join(TableB, semantic_check=False)
```

**Why this matters**: Prevents accidental matches between attributes like `session_id` that happen to share a name but refer to different entities in different parts of your schema.

**During migration**: If semantic matching fails, it often indicates a malformed join that should be reviewed rather than forced.

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

## ObjectRef API (New)

**New feature**: Path-addressed storage returns `ObjectRef` handles that support streaming access without downloading entire datasets.

```python
ref = (Dataset & key).fetch1('zarr_array')

# Direct fsspec access for Zarr/xarray
z = zarr.open(ref.fsmap, mode='r')

# Or download locally
local_path = ref.download('/tmp/data')

# Stream chunks without full download
with ref.open('rb') as f:
    chunk = f.read(1024)
```

This enables efficient access to large datasets stored in Zarr, HDF5, or custom formats.

## Deprecated and Removed

### Removed APIs

- **`.fetch()` method**: Replaced with `.to_dicts()`, `.to_arrays()`, or `.to_pandas()`
- **`._update()` method**: Replaced with `.update1()`
- **`@` operator (natural join)**: Use `*` with semantic matching or `.join(semantic_check=False)`
- **`dj.U() * table` pattern**: Use just `table` (universal set is implicit)

### Deprecated Features

- **AdaptedTypes**: Replaced by codec system (still works but migration recommended)
- **Native type syntax**: `int unsigned` → `int64` (warnings on new tables)
- **Legacy external storage** (`blob@store`): Replaced by `<blob@store>` codec syntax

### Legacy Support

During migration (Phases 1-3), both legacy and 2.0 APIs can coexist:
- Legacy clients can still access data
- 2.0 clients understand legacy column types
- Dual attributes enable cross-testing

After finalization (Phase 4+), only 2.0 clients are supported.

## License Change

DataJoint 2.0 is licensed under the **Apache License 2.0** (previously LGPL-2.1). This provides:
- More permissive for commercial and academic use
- Clearer patent grant provisions
- Better compatibility with broader ecosystem

## Migration Path

→ **[Complete Migration Guide](../how-to/migrate-to-v20.md)**

Upgrading from DataJoint 0.x is a **phased process** designed to minimize risk:

### Phase 1: Code Updates (Reversible)
- Update Python code to 2.0 API patterns (`.fetch()` → `.to_dicts()`, etc.)
- Update configuration files (`dj_local_conf.json` → `datajoint.json` + `.secrets/`)
- **No database changes** — legacy clients still work

### Phase 2: Type Migration (Reversible)
- Update database column comments to use core types (`:int64:`, `:<blob>:`)
- Rebuild `~lineage` tables for semantic matching
- Update Python table definitions
- **Legacy clients still work** — only metadata changed

### Phase 3: External Storage Dual Attributes (Reversible)
- Create `*_v2` attributes alongside legacy external storage columns
- Both APIs can access data during transition
- Enables cross-testing between legacy and 2.0
- **Legacy clients still work**

### Phase 4: Finalize (Point of No Return)
- Remove legacy external storage columns
- Drop old `~jobs` and `~external_*` tables
- **Legacy clients stop working** — database backup required

### Phase 5: Adopt New Features (Optional)
- Use new codecs (`<object@>`, `<npy@>`)
- Leverage Jobs 2.0 features (priority, better errors)
- Implement custom codecs for domain-specific types

### Migration Support

The migration guide includes:
- **AI agent prompts** for automated migration steps
- **Validation commands** to check migration status
- **Rollback procedures** for each phase
- **Dry-run modes** for all database changes

Most users complete Phases 1-2 in a single session. Phases 3-4 only apply if you use legacy external storage.

## See Also

### Migration
- **[Migration Guide](../how-to/migrate-to-v20.md)** — Complete upgrade instructions
- [Configuration](../how-to/configure-database.md) — Setup new configuration system

### Core Concepts
- [Type System](type-system.md) — Understand the three-tier type architecture
- [Computation Model](computation-model.md) — Jobs 2.0 and AutoPopulate
- [Query Algebra](query-algebra.md) — Semantic matching and operators

### Getting Started
- [Installation](../how-to/installation.md) — Install DataJoint 2.0
- [Tutorials](../tutorials/index.md) — Learn by example

### Reference
- [Type System Specification](../reference/specs/type-system.md) — Complete type system details
- [Codec API](../reference/specs/codec-api.md) — Build custom codecs
- [AutoPopulate Specification](../reference/specs/autopopulate.md) — Jobs 2.0 reference
