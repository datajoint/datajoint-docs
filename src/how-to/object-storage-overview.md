# Object Storage Overview

Navigate DataJoint's object storage documentation to find what you need.

## Quick Navigation by Task

**I want to...**

| Task | Guide | Est. Time |
|------|-------|-----------|
| ✅ Decide which storage type to use | [Choose a Storage Type](choose-storage-type.md) | 5-10 min |
| ✅ Set up S3, MinIO, or file storage | [Configure Object Storage](configure-storage.md) | 10-15 min |
| ✅ Store and retrieve large data | [Use Object Storage](use-object-storage.md) | 15-20 min |
| ✅ Work with NumPy arrays efficiently | [Use NPY Codec](use-npy-codec.md) | 10 min |
| ✅ Create domain-specific types | [Create Custom Codec](create-custom-codec.md) | 30-45 min |
| ✅ Optimize storage performance | [Manage Large Data](manage-large-data.md) | 20 min |
| ✅ Clean up unused data | [Garbage Collection](garbage-collection.md) | 10 min |

## Conceptual Understanding

**Why does DataJoint have object storage?**

Traditional databases excel at structured, relational data but struggle with large arrays, files, and streaming data. DataJoint's **Object-Augmented Schema (OAS)** unifies relational tables with object storage into a single coherent system:

- **Relational database:** Metadata, keys, relationships (structured data < 1 MB)
- **Object storage:** Arrays, files, datasets (large data > 1 MB)
- **Full referential integrity:** Maintained across both layers

Read: [Object-Augmented Schemas](../explanation/data-pipelines.md#object-augmented-schemas) for conceptual overview.

## Three Storage Modes

### In-Table Storage (`<blob>`)

**What:** Data stored directly in database column
**When:** Small objects < 1 MB (JSON, thumbnails, small arrays)
**Why:** Fast access, transactional consistency, no store setup

```python
metadata : <blob>         # Stored in MySQL
```

**Guide:** [Use Object Storage](use-object-storage.md#in-table-vs-object-store)

---

### Object Store (Integrated)

**What:** DataJoint-managed storage in S3, file systems, or cloud storage
**When:** Large data (arrays, files, datasets) needing lifecycle management
**Why:** Deduplication, garbage collection, transaction safety, referential integrity

**Two addressing schemes:**

#### Hash-Addressed (`<blob@>`, `<attach@>`)
- Content-based paths (MD5 hash)
- Automatic deduplication
- Best for: Write-once data, attachments

```python
waveform : <blob@>        # Hash: _hash/{schema}/{hash}
document : <attach@>      # Hash: _hash/{schema}/{hash}
```

#### Schema-Addressed (`<npy@>`, `<object@>`)
- Key-based paths (browsable)
- Streaming access, partial reads
- Best for: Zarr, HDF5, large arrays

```python
traces : <npy@>           # Schema: _schema/{schema}/{table}/{key}/
volume : <object@>        # Schema: _schema/{schema}/{table}/{key}/
```

**Guides:**
- [Choose a Storage Type](choose-storage-type.md) — Decision criteria
- [Use Object Storage](use-object-storage.md) — How to use codecs

---

### Filepath References (`<filepath@>`)

**What:** User-managed file paths (DataJoint stores path string only)
**When:** Existing data archives, externally managed files
**Why:** No file lifecycle management, no deduplication, user controls paths

```python
raw_data : <filepath@>    # User-managed path
```

**Guide:** [Use Object Storage](use-object-storage.md#filepath-references)

## Documentation by Level

### Getting Started

1. **[Choose a Storage Type](choose-storage-type.md)** — Start here
   - Quick decision tree (5 minutes)
   - Size guidelines (< 1 MB, 1-100 MB, > 100 MB)
   - Access pattern considerations
   - Lifecycle management options

2. **[Configure Object Storage](configure-storage.md)** — Setup
   - File system, S3, MinIO configuration
   - Single vs multiple stores
   - Credentials management
   - Store verification

3. **[Use Object Storage](use-object-storage.md)** — Basic usage
   - Insert/fetch patterns
   - In-table vs object store
   - Addressing schemes (hash vs schema)
   - ObjectRef for lazy access

### Intermediate

4. **[Use NPY Codec](use-npy-codec.md)** — NumPy arrays
   - Lazy loading (doesn't load until accessed)
   - Efficient slicing (fetch subsets)
   - Shape/dtype metadata
   - When to use `<npy@>` vs `<blob@>`

5. **[Manage Large Data](manage-large-data.md)** — Optimization
   - Storage tiers (hot/warm/cold)
   - Compression strategies
   - Batch operations
   - Performance tuning

6. **[Garbage Collection](garbage-collection.md)** — Cleanup
   - Automatic cleanup for integrated storage
   - Manual cleanup for filepath references
   - Orphan detection
   - Recovery procedures

### Advanced

7. **[Create Custom Codec](create-custom-codec.md)** — Extensibility
   - Domain-specific types
   - Codec API (encode/decode)
   - HashCodec vs SchemaCodec patterns
   - Integration with existing formats

## Technical Reference

For implementation details and specifications:

### Specifications

- [Type System Spec](../reference/specs/type-system.md) — Three-layer architecture
- [Codec API Spec](../reference/specs/codec-api.md) — Custom codec interface
- [NPY Codec Spec](../reference/specs/npy-codec.md) — NumPy array storage
- [Object Store Configuration Spec](../reference/specs/object-store-configuration.md) — Store config details

### Explanations

- [Type System](../explanation/type-system.md) — Conceptual overview
- [Data Pipelines (OAS section)](../explanation/data-pipelines.md#object-augmented-schemas) — Why OAS exists
- [Custom Codecs](../explanation/custom-codecs.md) — Design patterns

## Common Workflows

### Workflow 1: Adding Object Storage to Existing Pipeline

1. [Configure Object Storage](configure-storage.md) — Set up store
2. [Choose a Storage Type](choose-storage-type.md) — Select codec
3. Update table definitions with `@` modifier
4. [Use Object Storage](use-object-storage.md) — Insert/fetch patterns

**Estimate:** 30-60 minutes

---

### Workflow 2: Migrating from In-Table to Object Store

1. [Choose a Storage Type](choose-storage-type.md) — Determine new codec
2. Add new column with object storage codec
3. Migrate data (see [Use Object Storage](use-object-storage.md#migration-patterns))
4. Verify data integrity
5. Drop old column (see [Alter Tables](alter-tables.md))

**Estimate:** 1-2 hours for small datasets

---

### Workflow 3: Working with Very Large Arrays (> 1 GB)

1. Use `<object@>` or `<npy@>` (not `<blob@>`)
2. [Configure Object Storage](configure-storage.md) — Ensure adequate storage
3. For Zarr: Store as `<object@>` with `.zarr` extension
4. For streaming: Use `ObjectRef.fsmap` (see [Use Object Storage](use-object-storage.md#streaming-access))

**Key advantage:** No need to download full dataset into memory

---

### Workflow 4: Building Custom Domain Types

1. Read [Custom Codecs](../explanation/custom-codecs.md) — Understand patterns
2. [Create Custom Codec](create-custom-codec.md) — Implementation guide
3. [Codec API Spec](../reference/specs/codec-api.md) — Technical reference
4. Test with small dataset
5. Deploy to production

**Estimate:** 2-4 hours for simple codecs

## Decision Trees

### "Which storage mode?"

```
Is data < 1 MB per row?
├─ YES → <blob> (in-table)
└─ NO  → Continue...

Is data managed externally?
├─ YES → <filepath@> (user-managed reference)
└─ NO  → Continue...

Need streaming or partial reads?
├─ YES → <object@> or <npy@> (schema-addressed)
└─ NO  → <blob@> (hash-addressed, full download)
```

**Full guide:** [Choose a Storage Type](choose-storage-type.md)

---

### "Which codec for object storage?"

```
NumPy arrays that benefit from lazy loading?
├─ YES → <npy@>
└─ NO  → Continue...

Large files (> 100 MB) needing streaming?
├─ YES → <object@>
└─ NO  → Continue...

Write-once data with potential duplicates?
├─ YES → <blob@> (deduplication via hashing)
└─ NO  → <blob@> or <object@> (choose based on access pattern)
```

**Full guide:** [Choose a Storage Type](choose-storage-type.md#storage-type-comparison)

## Troubleshooting

### Common Issues

| Problem | Likely Cause | Solution Guide |
|---------|-------------|----------------|
| "Store not configured" | Missing stores config | [Configure Object Storage](configure-storage.md) |
| Out of memory loading array | Using `<blob@>` for huge data | [Choose a Storage Type](choose-storage-type.md) → Use `<object@>` |
| Slow fetches | Wrong codec choice | [Manage Large Data](manage-large-data.md) |
| Data not deduplicated | Using wrong codec | [Choose a Storage Type](choose-storage-type.md#deduplication) |
| Path conflicts with reserved | `<filepath@>` using `_hash/` or `_schema/` | [Use Object Storage](use-object-storage.md#filepath-references) |
| Missing files after delete | Expected behavior for integrated storage | [Garbage Collection](garbage-collection.md) |

### Getting Help

- Check [FAQ](../explanation/faq.md) for common questions
- Search [GitHub Discussions](https://github.com/datajoint/datajoint-python/discussions)
- Review specification for exact behavior

## See Also

### Related Concepts
- [Type System](../explanation/type-system.md) — Three-layer type architecture
- [Data Pipelines](../explanation/data-pipelines.md) — Object-Augmented Schemas

### Related How-Tos
- [Manage Secrets](manage-secrets.md) — Credentials for S3/cloud storage
- [Define Tables](define-tables.md) — Table definition syntax
- [Insert Data](insert-data.md) — Data insertion patterns

### Related Tutorials
- [Object Storage Tutorial](../tutorials/basics/06-object-storage.ipynb) — Hands-on learning
- [Custom Codecs Tutorial](../tutorials/advanced/custom-codecs.ipynb) — Build your own codec
