# DataJoint Documentation

DataJoint is a framework for scientific data pipelines that introduces the **Relational Workflow Model**—a paradigm where your database schema is an executable specification of your workflow.

## What is the Relational Workflow Model?

Traditional databases store data but don't understand how it was computed. DataJoint extends relational databases with native workflow semantics:

- **Tables represent workflow steps** — Each table is a step in your pipeline where entities are created
- **Foreign keys encode dependencies** — Parent tables must be populated before child tables
- **Computations are declarative** — Define *what* to compute; DataJoint determines *when* and tracks *what's done*
- **Results are immutable** — Computed results preserve full provenance and reproducibility

The result is a **Computational Database** where data transformations are first-class citizens. Just as spreadsheets recalculate formulas when inputs change, DataJoint pipelines automatically propagate computations through your workflow.

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

## Quick Start

```bash
pip install datajoint
```

Configure database credentials in your project (see [Configuration](reference/configuration.md)):

```bash
# Create datajoint.json for non-sensitive settings
echo '{"database": {"host": "localhost", "port": 3306}}' > datajoint.json

# Create secrets directory for credentials
mkdir -p .secrets
echo "root" > .secrets/database.user
echo "password" > .secrets/database.password
```

Define and populate a simple pipeline:

```python
import datajoint as dj

schema = dj.Schema('my_pipeline')

@schema
class Subject(dj.Manual):
    definition = """
    subject_id : uint16
    ---
    name : varchar(100)
    date_of_birth : date
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : uint8
    ---
    session_date : date
    """

@schema
class SessionAnalysis(dj.Computed):
    definition = """
    -> Session
    ---
    result : float64
    """

    def make(self, key):
        # Compute result for this session
        self.insert1({**key, 'result': 42.0})

# Insert data
Subject.insert1({'subject_id': 1, 'name': 'M001', 'date_of_birth': '2024-01-15'})
Session.insert1({'subject_id': 1, 'session_idx': 1, 'session_date': '2024-06-01'})

# Run computations
SessionAnalysis.populate()
```

[:octicons-arrow-right-24: Continue with the tutorials](tutorials/index.md)
