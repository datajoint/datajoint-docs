# Specifications

Formal specifications of DataJoint's data model and behavior.

These documents define how DataJoint works at a detailed level. They serve as
authoritative references for:

- Understanding exact behavior of operations
- Implementing compatible tools and extensions
- Debugging complex scenarios

## How to Use These Specifications

**If you're new to DataJoint:**
Start with the [tutorials](../../tutorials/index.md) and [how-to guides](../../how-to/index.md) before diving into specifications. Specs are technical references, not learning materials.

**If you're implementing features:**
Use specs as authoritative sources for behavior. Start with dependencies (see below) and work up to your target specification.

**If you're debugging:**
Specs clarify exact behavior when documentation or examples are ambiguous.

## Reading Order

### Start Here

1. [Database Backends](database-backends.md) — Supported databases (MySQL, PostgreSQL)
2. [Table Declaration](table-declaration.md) — How to define tables
3. [Primary Keys](primary-keys.md) — Key propagation rules
4. [Type System](type-system.md) — Three-layer type architecture

**Next:** Choose based on your needs:
- **Working with data?** → Data Operations
- **Building queries?** → Query Algebra
- **Using large data?** → Object Storage

### Query Algebra

**Prerequisites:** Table Declaration, Primary Keys

1. [Query Operators](query-algebra.md) — Restrict, proj, join, aggr, union
2. [Semantic Matching](semantic-matching.md) — Attribute lineage
3. [Fetch API](fetch-api.md) — Data retrieval

### Data Operations

**Prerequisites:** Table Declaration

1. [Data Manipulation](data-manipulation.md) — Insert, update, delete
2. [AutoPopulate](autopopulate.md) — Jobs 2.0 system
3. [Job Metadata](job-metadata.md) — Hidden job tracking columns

### Object Storage

**Prerequisites:** Type System

1. [Object Store Configuration](object-store-configuration.md) — Store setup
2. [Codec API](codec-api.md) — Custom type implementation
3. [`<npy>` Codec](npy-codec.md) — NumPy array storage

### Advanced Topics

1. [Master-Part Relationships](master-part.md) — Compositional modeling
2. [Virtual Schemas](virtual-schemas.md) — Schema introspection without source

## Document Structure

Each specification follows a consistent structure:

1. **Overview** — What this specifies
2. **User Guide** — Practical usage
3. **API Reference** — Methods and signatures
4. **Concepts** — Definitions and rules
5. **Implementation Details** — Internal behavior
6. **Examples** — Concrete code samples
7. **Best Practices** — Recommendations

## Specifications by Topic

### Schema Definition

| Specification | Prerequisites | Related How-To | Related Explanation |
|---------------|---------------|----------------|---------------------|
| [Table Declaration](table-declaration.md) | None | [Define Tables](../../how-to/define-tables.md) | [Relational Workflow Model](../../explanation/relational-workflow-model.md) |
| [Master-Part Relationships](master-part.md) | Table Declaration | [Model Relationships](../../how-to/model-relationships.ipynb) | [Data Pipelines](../../explanation/data-pipelines.md) |
| [Virtual Schemas](virtual-schemas.md) | Table Declaration | — | — |

**Key concepts:** Table tiers (Manual, Lookup, Imported, Computed, Part), foreign keys, dependency graphs, compositional modeling

---

### Query Algebra

| Specification | Prerequisites | Related How-To | Related Explanation |
|---------------|---------------|----------------|---------------------|
| [Query Operators](query-algebra.md) | Table Declaration, Primary Keys | [Query Data](../../how-to/query-data.md) | [Query Algebra](../../explanation/query-algebra.md) |
| [Semantic Matching](semantic-matching.md) | Query Operators | [Model Relationships](../../how-to/model-relationships.ipynb) | [Query Algebra](../../explanation/query-algebra.md) |
| [Primary Keys](primary-keys.md) | Table Declaration | [Design Primary Keys](../../how-to/design-primary-keys.md) | [Entity Integrity](../../explanation/entity-integrity.md) |
| [Fetch API](fetch-api.md) | Query Operators | [Fetch Results](../../how-to/fetch-results.md) | — |
| [Diagram](diagram.md) | Table Declaration | [Read Diagrams](../../how-to/read-diagrams.ipynb) | — |

**Key concepts:** Restriction (`&`, `-`), projection (`.proj()`), join (`*`), aggregation (`.aggr()`), union, universal set (`U()`), attribute lineage, schema visualization

---

### Type System

| Specification | Prerequisites | Related How-To | Related Explanation |
|---------------|---------------|----------------|---------------------|
| [Type System](type-system.md) | None | [Choose a Storage Type](../../how-to/choose-storage-type.md) | [Type System](../../explanation/type-system.md) |
| [Codec API](codec-api.md) | Type System | [Create Custom Codec](../../how-to/create-custom-codec.md) | [Custom Codecs](../../explanation/custom-codecs.md) |
| [`<npy>` Codec](npy-codec.md) | Type System | [Use Object Storage](../../how-to/use-object-storage.md) | — |

**Key concepts:** Native types (MySQL), core types (portable), codec types (Python objects), in-table vs object storage, addressing schemes

---

### Object Storage

| Specification | Prerequisites | Related How-To | Related Explanation |
|---------------|---------------|----------------|---------------------|
| [Object Store Configuration](object-store-configuration.md) | Type System | [Configure Object Storage](../../how-to/configure-storage.md) | [Data Pipelines (OAS)](../../explanation/data-pipelines.md#object-augmented-schemas) |

**Key concepts:** Hash-addressed storage (deduplication), schema-addressed storage (browsable paths), filepath storage (user-managed), store configuration, path generation

---

### Data Operations

| Specification | Prerequisites | Related How-To | Related Explanation |
|---------------|---------------|----------------|---------------------|
| [Data Manipulation](data-manipulation.md) | Table Declaration | [Insert Data](../../how-to/insert-data.md) | [Normalization](../../explanation/normalization.md) |
| [AutoPopulate](autopopulate.md) | Table Declaration, Data Manipulation | [Run Computations](../../how-to/run-computations.md), [Distributed Computing](../../how-to/distributed-computing.md) | [Computation Model](../../explanation/computation-model.md) |
| [Job Metadata](job-metadata.md) | AutoPopulate | [Handle Errors](../../how-to/handle-errors.md) | [Computation Model](../../explanation/computation-model.md) |

**Key concepts:** Insert patterns, transactional integrity, workflow normalization, Jobs 2.0, job coordination, populate(), make() method, job states

