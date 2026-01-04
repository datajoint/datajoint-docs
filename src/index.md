# DataJoint Documentation

DataJoint is a framework for building scientific data pipelines using relational
databases. It combines the rigor of relational data modeling with native support
for computational workflows.

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

</div>

---

## DataJoint Elements

[DataJoint Elements](elements/index.md) are open-source data pipelines for
neuroscience experiments, built on DataJoint. They provide ready-to-use
schemas for common experimental modalities.

[:octicons-arrow-right-24: Explore Elements](elements/index.md)

---

## Quick Start

```bash
pip install datajoint
```

```python
import datajoint as dj

# Connect to database
dj.config['database.host'] = 'localhost'
dj.config['database.user'] = 'root'
dj.config['database.password'] = 'secret'

# Create a schema
schema = dj.Schema('my_pipeline')

# Define a table
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int
    ---
    name : varchar(100)
    date_of_birth : date
    """

# Insert data
Subject.insert1({'subject_id': 1, 'name': 'Mouse001', 'date_of_birth': '2024-01-15'})

# Query data
Subject()
```

[:octicons-arrow-right-24: Continue with the tutorial](tutorials/index.md)
