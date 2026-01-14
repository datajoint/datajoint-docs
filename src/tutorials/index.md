# Tutorials

Learn DataJoint by building real pipelines.

These tutorials guide you through building data pipelines step by step. Each tutorial
is a Jupyter notebook that you can run interactively. Start with the basics and
progress to domain-specific and advanced topics.

## Quick Start

Install DataJoint:

```bash
pip install datajoint
```

Configure database credentials in your project (see [Configuration](../reference/configuration.md)):

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

Continue learning with the structured tutorials below.

## Basics

Core concepts for getting started with DataJoint:

1. [First Pipeline](basics/01-first-pipeline.ipynb) — Tables, queries, and the four core operations
2. [Schema Design](basics/02-schema-design.ipynb) — Primary keys, relationships, and table tiers
3. [Data Entry](basics/03-data-entry.ipynb) — Inserting and managing data
4. [Queries](basics/04-queries.ipynb) — Operators and fetching results
5. [Computation](basics/05-computation.ipynb) — Imported and Computed tables
6. [Object Storage](basics/06-object-storage.ipynb) — Blobs, attachments, and external stores

## Examples

Complete pipelines demonstrating DataJoint patterns:

- [University Database](examples/university.ipynb) — Academic records with students, courses, and grades
- [Hotel Reservations](examples/hotel-reservations.ipynb) — Booking system with rooms, guests, and reservations
- [Languages & Proficiency](examples/languages.ipynb) — Language skills tracking with many-to-many relationships
- [Fractal Pipeline](examples/fractal-pipeline.ipynb) — Iterative computation and parameter sweeps
- [Blob Detection](examples/blob-detection.ipynb) — Image processing with automated computation

## Domain Tutorials

Real-world scientific pipelines:

- [Calcium Imaging](domain/calcium-imaging/calcium-imaging.ipynb) — Import TIFF movies, segment cells, extract fluorescence traces
- [Electrophysiology](domain/electrophysiology/electrophysiology.ipynb) — Import recordings, detect spikes, extract waveforms
- [Allen CCF](domain/allen-ccf/allen-ccf.ipynb) — Brain atlas with hierarchical region ontology

## Advanced Topics

Extending DataJoint for specialized use cases:

- [SQL Comparison](advanced/sql-comparison.ipynb) — DataJoint for SQL users
- [JSON Data Type](advanced/json-type.ipynb) — Semi-structured data in tables
- [Distributed Computing](advanced/distributed.ipynb) — Multi-process and cluster workflows
- [Custom Codecs](advanced/custom-codecs.ipynb) — Extending the type system

## Running the Tutorials

```bash
# Clone the repository
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs

# Start the tutorial environment
docker compose up -d

# Launch Jupyter
jupyter lab src/tutorials/
```

All tutorials use a local MySQL database that resets between sessions.
