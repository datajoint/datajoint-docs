# DataJoint Documentation

!!! tip "Upgrading from 0.14.x?"

    - **Migration guide:** [Migrate to 2.0](how-to/migrate-to-v20.md)
    - **Legacy docs:** [datajoint.github.io](https://datajoint.github.io/datajoint-python)

## About DataJoint

**DataJoint** implements the [Relational Workflow Model](explanation/relational-workflow-model.md)—a data model where your database schema defines an executable data pipeline. Tables represent workflow steps, foreign keys encode dependencies, and the system handles job management, parallel execution, and provenance tracking. [Object storage](explanation/data-pipelines.md#object-augmented-schemas) integration enables seamless handling of large scientific data.

![pipeline](images/pipeline.png){: style="height:300px;"}

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
