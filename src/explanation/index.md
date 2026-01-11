# Concepts

Understanding the principles behind DataJoint.

DataJoint implements the **Relational Workflow Model**—a paradigm that extends
relational databases with native support for computational workflows. This section
explains the core concepts that make DataJoint pipelines reliable, reproducible,
and scalable.

## Core Concepts

<div class="grid cards" markdown>

-   :material-sitemap: **[Relational Workflow Model](relational-workflow-model.md)**

    How DataJoint differs from traditional databases. The paradigm shift from
    storage to workflow.

-   :material-key: **[Entity Integrity](entity-integrity.md)**

    Primary keys and the three questions. Ensuring one-to-one correspondence
    between entities and records.

-   :material-table-split-cell: **[Normalization](normalization.md)**

    Schema design principles. Organizing tables around workflow steps to
    minimize redundancy.

-   :material-set-split: **[Query Algebra](query-algebra.md)**

    The five operators: restriction, join, projection, aggregation, union.
    Workflow-aware query semantics.

-   :material-code-tags: **[Type System](type-system.md)**

    Three-layer architecture: native, core, and codec types. Internal and
    external storage modes.

-   :material-cog-play: **[Computation Model](computation-model.md)**

    AutoPopulate and Jobs 2.0. Automated, reproducible, distributed computation.

-   :material-puzzle: **[Custom Codecs](custom-codecs.md)**

    Extend DataJoint with domain-specific types. The codec extensibility system.

-   :material-pipe: **[Data Pipelines](data-pipelines.md)**

    From workflows to complete data operations systems. Project structure and
    object-augmented schemas.

-   :material-frequently-asked-questions: **[FAQ](faq.md)**

    How DataJoint compares to ORMs, workflow managers, and lakehouses.
    Common questions answered.

</div>

## Why These Concepts Matter

Traditional databases store data. DataJoint pipelines **process** data. Understanding
the Relational Workflow Model helps you:

- Design schemas that naturally express your workflow
- Write queries that are both powerful and intuitive
- Build computations that scale from laptop to cluster
- Maintain data integrity throughout the pipeline lifecycle
