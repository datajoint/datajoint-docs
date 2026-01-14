# DataJoint Documentation

> **DataJoint 2.0 is a major release.** Existing pipelines require migration.
> See the [Migration Guide](how-to/migrate-to-v20.md) for upgrade instructions.
> For pre-2.0 documentation, visit [datajoint.github.io/datajoint-python](https://datajoint.github.io/datajoint-python).

**DataJoint** is a framework for scientific data pipelines built on the [Relational Workflow Model](explanation/relational-workflow-model.md)—a paradigm where your database schema is an executable specification of your workflow.

![pipeline](images/pipeline.png){: style="height:300px;"}

Unlike traditional databases that merely store data, DataJoint pipelines **process** data: tables represent workflow steps, foreign keys encode computational dependencies, and the schema itself defines what computations exist and how they relate. Combined with [Object-Augmented Schemas](explanation/data-pipelines.md#object-augmented-schemas) for seamless large-data handling, DataJoint delivers reproducible, scalable scientific computing with full provenance tracking.

<div class="grid cards" markdown>

-   :material-lightbulb-outline: **Concepts**

    ---

    Understand the Relational Workflow Model and DataJoint's core principles

    [:octicons-arrow-right-24: Learn the concepts](explanation/index.md)

-   :material-school-outline: **Tutorials**

    ---

    Build your first pipeline with hands-on Jupyter notebooks

    [:octicons-arrow-right-24: Start learning](tutorials/index.md)

-   :material-tools: **How-To Guides**

    ---

    Practical guides for common tasks and patterns

    [:octicons-arrow-right-24: Find solutions](how-to/index.md)

-   :material-book-open-variant: **Reference**

    ---

    Specifications, API documentation, and technical details

    [:octicons-arrow-right-24: Look it up](reference/index.md)

-   :material-puzzle: **DataJoint Elements**

    ---

    Reusable pipeline modules for neurophysiology experiments

    [:octicons-arrow-right-24: Explore Elements](elements/index.md)

-   :material-cloud: **DataJoint Platform**

    ---

    A cloud platform for automated analysis workflows. It relies on DataJoint Python and DataJoint Elements.

    [:octicons-arrow-right-24: Learn more](https://datajoint.com/){:target="_blank"} | [Sign-in](https://works.datajoint.com){:target="_blank"}

</div>

---

**New to DataJoint?** Start with the [:octicons-arrow-right-24: Quick Start tutorial](tutorials/index.md).
