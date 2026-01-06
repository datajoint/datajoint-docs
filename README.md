# DataJoint Documentation

Official documentation for [DataJoint](https://github.com/datajoint/datajoint-python),
an open-source framework for building scientific data pipelines.

**Live site:** https://docs.datajoint.com

## What is DataJoint?

DataJoint is a Python framework for building scientific data pipelines using relational
databases. It implements the **Relational Workflow Model**—a paradigm that extends
relational databases with native support for computational workflows.

Key features:

- **Declarative schema design** — Define tables and relationships in Python
- **Automatic dependency tracking** — Foreign keys encode workflow dependencies
- **Built-in computation** — Imported and Computed tables run automatically
- **Data integrity** — Referential integrity and transaction support
- **Reproducibility** — Immutable data with full provenance

## Quick Start

### Installation

```bash
pip install datajoint
```

For schema diagrams, install Graphviz (the system library, not just Python bindings):

```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz libgraphviz-dev

# conda (any platform)
conda install -c conda-forge graphviz pygraphviz
```

If using pip (after installing system Graphviz):
```bash
pip install pygraphviz
```

### Configuration

DataJoint uses configuration files to manage database credentials securely. Create these
files in your project directory:

**datajoint.json** (non-sensitive settings, commit to version control):
```json
{
  "database": {
    "host": "localhost",
    "port": 3306
  }
}
```

**.secrets/database.user** and **.secrets/database.password** (sensitive, add to .gitignore):
```bash
mkdir -p .secrets
echo "your_username" > .secrets/database.user
echo "your_password" > .secrets/database.password
chmod 600 .secrets/*
echo ".secrets/" >> .gitignore
```

DataJoint automatically discovers these files by searching up from the current directory.
This keeps credentials out of your code and version control.

### Define a Schema

```python
import datajoint as dj

schema = dj.Schema('my_pipeline')

@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    ---
    name : varchar(100)
    date_of_birth : date
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : int32
    ---
    session_date : date
    duration : float32          # minutes
    notes = '' : varchar(1000)
    """

@schema
class ProcessedData(dj.Computed):
    definition = """
    -> Session
    ---
    result : float64
    """

    def make(self, key):
        # Compute result from session data
        duration = (Session & key).fetch1('duration')
        self.insert1({**key, 'result': duration * 2})
```

Note: Use DataJoint core types (`int32`, `float32`, `float64`, `varchar`) for portability
across database backends.

### View Schema Diagram

```python
dj.Diagram(schema)
```

### Run Computations

```python
ProcessedData.populate()
```

## Documentation Structure

This documentation follows the [Diátaxis](https://diataxis.fr/) framework:

| Section | Purpose |
|---------|---------|
| [Concepts](src/explanation/) | Understand the principles behind DataJoint |
| [Tutorials](src/tutorials/) | Learn by building real pipelines (Jupyter notebooks) |
| [How-To](src/how-to/) | Practical guides for common tasks |
| [Reference](src/reference/) | Specifications and API documentation |

## Local Development with Docker (Recommended)

The Docker environment includes MySQL, MinIO (S3-compatible storage), Graphviz, and all
dependencies needed to build documentation and execute tutorial notebooks.

### Start the Environment

```bash
# Clone the repository
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs

# Start all services (MySQL, MinIO, docs server)
MODE="LIVE" docker compose up --build
```

Navigate to http://127.0.0.1:8000/

### Services

| Service | Port | Description |
|---------|------|-------------|
| `docs` | 8000 | MkDocs live server |
| `mysql` | 3306 | MySQL 8.0 database |
| `minio` | 9002 | MinIO S3 API |
| `minio` | 9003 | MinIO console |

### Execute Tutorial Notebooks

Tutorial notebooks can be executed inside the Docker environment where the database
is available:

```bash
# Execute a single notebook
docker compose exec docs jupyter nbconvert \
    --to notebook --execute --inplace \
    /main/src/tutorials/01-getting-started.ipynb

# Execute all tutorials
docker compose exec docs bash -c '
    for nb in /main/src/tutorials/*.ipynb; do
        jupyter nbconvert --to notebook --execute --inplace "$nb"
    done
'
```

### Build Static Site

```bash
# Build static HTML (output in site/)
MODE="BUILD" docker compose up --build
```

### Reset Database

```bash
# Stop services and remove data volumes
docker compose down -v
```

## Local Development without Docker

### Prerequisites

- Python 3.10+
- MySQL 8.0+ (running locally)
- Graphviz (for schema diagrams)

### Setup

```bash
# Clone the repository
git clone https://github.com/datajoint/datajoint-docs.git
cd datajoint-docs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r pip_requirements.txt
```

Note: For schema diagrams, ensure Graphviz system libraries are installed (see Quick Start).

### Configure Database Connection

The repository includes a `datajoint.json` with default settings. Create the secrets
directory with your credentials:

```bash
mkdir -p .secrets
echo "your_username" > .secrets/database.user
echo "your_password" > .secrets/database.password
chmod 600 .secrets/*
```

### Preview Documentation

```bash
mkdocs serve
```

Navigate to http://127.0.0.1:8000/

## Contributing

Contributions are welcome! See our [contribution guidelines](src/about/contributing.md).

### Quick Fixes

1. Fork the repository
2. Edit the relevant markdown file in `src/`
3. Submit a pull request

### Larger Changes

1. Open an issue to discuss the change
2. Fork and create a feature branch
3. Make changes with `mkdocs serve` for preview
4. Submit a pull request

### Executing Notebooks for CI

When modifying tutorial notebooks, re-execute them to update outputs:

```bash
docker compose exec docs jupyter nbconvert \
    --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    /main/src/tutorials/YOUR_NOTEBOOK.ipynb
```

## Related Repositories

- [datajoint-python](https://github.com/datajoint/datajoint-python) — Core DataJoint library
- [DataJoint Elements](https://docs.datajoint.com/elements/) — Neuroscience pipeline elements

## Citation

If you use DataJoint in your research, please cite:

> Yatsenko D, Reimer J, Ecker AS, Walker EY, Sinz F, Berens P, Hoenselaar A,
> Cotton RJ, Siapas AS, Tolias AS. DataJoint: managing big scientific data
> using MATLAB or Python. bioRxiv. 2015:031658. doi: [10.1101/031658](https://doi.org/10.1101/031658)

## License

Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

DataJoint software: [Apache 2.0](https://github.com/datajoint/datajoint-python/blob/main/LICENSE)
