# Scientific Data Pipelines

A **scientific data pipeline** extends beyond a database with computations. It is a comprehensive system that:

- Manages the complete lifecycle of scientific data from acquisition to delivery
- Integrates diverse tools for data entry, visualization, and analysis
- Provides infrastructure for secure, scalable computation
- Enables collaboration across teams and institutions
- Supports reproducibility and provenance tracking throughout

## The Relational Workflow Model

DataJoint pipelines are built on the [Relational Workflow Model](relational-workflow-model.md)—a paradigm that extends relational databases with native support for computational workflows. In this model:

- **Tables represent workflow steps**, not just data storage
- **Foreign keys encode dependencies**, prescribing the order of operations
- **Table tiers** (Lookup, Manual, Imported, Computed) classify how data enters the pipeline
- **The schema forms a DAG** (directed acyclic graph) that defines valid execution sequences

This model treats the database schema as an **executable workflow specification**—defining not just what data exists but when and how it comes into existence.

## Project Structure

A DataJoint pipeline is organized as a Python package where each module corresponds to a database schema. The project integrates three core components:

| Component | Purpose |
|-----------|---------|
| **Code Repository** | Version-controlled pipeline definitions, `make` methods, configuration |
| **Relational Database** | System of record for metadata, relationships, and integrity enforcement |
| **Object Store** | Scalable storage for large scientific data (images, recordings, signals) |

The module import structure mirrors the foreign key dependencies between schemas, ensuring code dependencies and data dependencies flow in the same direction.

```
my_pipeline/
├── datajoint.json          # Shared configuration (committed)
├── .secrets/               # Credentials (gitignored)
│   └── ...
├── pyproject.toml          # Package metadata and dependencies
├── src/
│   └── my_pipeline/
│       ├── __init__.py
│       ├── subject.py      # subject schema (no dependencies)
│       ├── session.py      # session schema (depends on subject)
│       ├── acquisition.py  # acquisition schema (depends on session)
│       └── analysis.py     # analysis schema (depends on acquisition)
├── tests/
│   └── ...
└── docs/
    └── ...
```

For detailed guidance on organizing multi-schema pipelines, configuring repositories, and managing team access, see [Manage a Pipeline Project](../how-to/manage-pipeline-project.md).

## Object-Augmented Schemas

Scientific data often includes large objects—images, recordings, time series, instrument outputs—that don't fit efficiently in relational tables. DataJoint addresses this through **Object-Augmented Schemas (OAS)**, a hybrid storage architecture that preserves relational semantics while handling arbitrarily large data.

### The OAS Philosophy

**1. The database remains the system of record.**

All metadata, relationships, and query logic live in the relational database. The schema defines what data exists, how entities relate, and what computations produce them. Queries operate on the relational structure; results are consistent and reproducible.

**2. Large objects live in external stores.**

Object storage (filesystems, S3, GCS, Azure Blob, MinIO) holds the actual bytes—arrays, images, files. The database stores only lightweight references (paths, checksums, metadata). This separation lets the database stay fast while data scales to terabytes.

**3. Transparent access through codecs.**

DataJoint's [type system](type-system.md) provides codec types that bridge Python objects and storage:

| Codec | Purpose |
|-------|---------|
| `<blob>` | Serialize Python objects (NumPy arrays, dicts) |
| `<blob@store>` | Same, but stored externally |
| `<attach>` | Store files with preserved filenames |
| `<object@store>` | Path-addressed storage for complex structures (Zarr, HDF5) |
| `<filepath@store>` | References to externally-managed files |

Users work with native Python objects; serialization and storage routing are invisible.

**4. Referential integrity extends to objects.**

When a database row is deleted, its associated external objects are garbage-collected. Foreign key cascades work correctly—delete upstream data and downstream results (including their objects) disappear. The database and object store remain synchronized without manual cleanup.

**5. Multiple storage tiers support diverse access patterns.**

Different attributes can route to different stores:

```python
class Recording(dj.Imported):
    definition = """
    -> Session
    ---
    raw_data : <blob@fast>       # Hot storage for active analysis
    archive : <blob@cold>        # Cold storage for long-term retention
    """
```

This architecture lets teams work with terabyte-scale datasets while retaining the query power, integrity guarantees, and reproducibility of the relational model.

## Pipeline Workflow

A typical data pipeline workflow:

1. **Acquisition** — Data is collected from instruments, experiments, or external sources. Raw files land in object storage; metadata populates Manual tables.

2. **Import** — Automated processes parse raw data, extract signals, and populate Imported tables with structured results.

3. **Computation** — The `populate()` mechanism identifies new data and triggers downstream processing. Compute resources execute transformations and populate Computed tables.

4. **Query & Analysis** — Users query results across the pipeline, combining data from multiple stages to generate insights, reports, or visualizations.

5. **Collaboration** — Team members access the same database concurrently, building on shared results. Foreign key constraints maintain consistency.

6. **Delivery** — Processed results are exported, integrated into downstream systems, or archived according to project requirements.

Throughout this process, the schema definition remains the single source of truth.

## Comparing Approaches

| Aspect | File-Based Approach | DataJoint Pipeline |
|--------|--------------------|--------------------|
| **Data Structure** | Implicit in filenames/folders | Explicit in schema definition |
| **Dependencies** | Encoded in scripts | Declared through foreign keys |
| **Provenance** | Manual tracking | Automatic through referential integrity |
| **Reproducibility** | Requires careful discipline | Built into the model |
| **Collaboration** | File sharing/conflicts | Concurrent database access |
| **Queries** | Custom scripts per question | Composable query algebra |
| **Scalability** | Limited by filesystem | Database + object-augmented storage |

The pipeline approach requires upfront investment in schema design. This investment pays dividends through reduced errors, improved reproducibility, and efficient collaboration as projects scale.

## Summary

Scientific data pipelines extend the Relational Workflow Model into complete data operations systems:

- **Relational Workflow Model** — schemas as executable workflow specifications
- **Project structure** — Python packages mirroring schema dependencies
- **Object-Augmented Schemas** — scalable storage with relational semantics

The schema remains central—defining data structures, dependencies, and computational flow. This pipeline-centric approach lets teams focus on their science while the system handles data integrity, provenance, and reproducibility automatically.

## See Also

- [Relational Workflow Model](relational-workflow-model.md) — The conceptual foundation
- [Type System](type-system.md) — Codec types and storage modes
- [Manage a Pipeline Project](../how-to/manage-pipeline-project.md) — Practical project organization
- [Configure Object Storage](../how-to/configure-storage.md) — Storage setup
