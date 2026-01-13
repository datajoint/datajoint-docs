# DataJoint Documentation

**DataJoint** is a framework for scientific data pipelines built on the [Relational Workflow Model](explanation/relational-workflow-model.md)—a paradigm where your database schema is an executable specification of your workflow.

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
Subject.insert1({'subject_id': 1, 'name': 'M001', 'date_of_birth': '2026-01-15'})
Session.insert1({'subject_id': 1, 'session_idx': 1, 'session_date': '2026-01-06'})

# Run computations
SessionAnalysis.populate()
```

[:octicons-arrow-right-24: Continue with the tutorials](tutorials/index.md)
