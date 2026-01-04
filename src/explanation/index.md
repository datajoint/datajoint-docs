# Concepts

Understanding the principles behind DataJoint.

DataJoint implements the **Relational Workflow Model**—a paradigm that extends
relational databases with native support for computational workflows. This section
explains the core concepts that make DataJoint pipelines reliable, reproducible,
and scalable.

## Topics

- [Relational Workflow Model](relational-workflow-model.md) — How DataJoint differs from traditional databases
- [Entity Integrity](entity-integrity.md) — Primary keys and the three questions
- [Normalization](normalization.md) — Schema design principles
- [Query Algebra](query-algebra.md) — Operators and their semantics
- [Type System](type-system.md) — Storage architecture and codecs
- [Computation Model](computation-model.md) — AutoPopulate and job management

## Why These Concepts Matter

Traditional databases store data. DataJoint pipelines **process** data. Understanding
the Relational Workflow Model helps you:

- Design schemas that naturally express your workflow
- Write queries that are both powerful and intuitive
- Build computations that scale from laptop to cluster
- Maintain data integrity throughout the pipeline lifecycle
