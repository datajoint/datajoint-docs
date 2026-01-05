# Specifications

Formal specifications of DataJoint's data model and behavior.

These documents define how DataJoint works at a detailed level. They serve as
authoritative references for:

- Understanding exact behavior of operations
- Implementing compatible tools and extensions
- Debugging complex scenarios

## Document Structure

Each specification follows a consistent structure:

1. **Overview** — What this specifies
2. **User Guide** — Practical usage
3. **API Reference** — Methods and signatures
4. **Concepts** — Definitions and rules
5. **Implementation Details** — Internal behavior
6. **Examples** — Concrete code samples
7. **Best Practices** — Recommendations

## Specifications

### Schema Definition

| Specification | Description |
|---------------|-------------|
| [Table Declaration](table-declaration.md) | Table definition syntax, tiers, foreign keys, and indexes |
| [Primary Keys](primary-keys.md) | How primary keys propagate through query operators |
| [Semantic Matching](semantic-matching.md) | Attribute lineage and join compatibility |

### Type System

| Specification | Description |
|---------------|-------------|
| [Type System](type-system.md) | Three-layer type architecture: native, core, and codec types |
| [Codec API](codec-api.md) | Custom type implementation with encode/decode semantics |

### Queries

| Specification | Description |
|---------------|-------------|
| [Fetch API](fetch-api.md) | Data retrieval methods and formats |

### Computation

| Specification | Description |
|---------------|-------------|
| [AutoPopulate](autopopulate.md) | Jobs 2.0 system for automated computation |
| [Job Metadata](job-metadata.md) | Hidden columns for job tracking |
