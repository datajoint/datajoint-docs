# Installation

Install DataJoint Python and set up your environment.

## Requirements

- Python 3.10+
- MySQL 8.0.13+ or PostgreSQL 15+
- Network access to database server
- Linux, macOS, or Windows (see [Platform support](#platform-support))

## Install DataJoint 2.0+

```bash
pip install datajoint
```

**With optional dependencies:**

```bash
# For Diagram.draw(), which renders diagrams into a matplotlib figure
pip install datajoint[viz]

# For polars DataFrame support
pip install datajoint[polars]

# For the PostgreSQL backend (psycopg2-binary) — added in 2.1
pip install datajoint[postgres]

# For cloud storage backends
pip install datajoint[s3]    # AWS S3
pip install datajoint[gcs]   # Google Cloud Storage
pip install datajoint[azure] # Azure Blob Storage
```

!!! note "Upgrading from 0.14.x?"

    See the [Migration Guide](migrate-to-v20.md) for breaking changes and upgrade instructions.
    Legacy documentation for 0.14.x is available at [datajoint.github.io](https://datajoint.github.io/datajoint-python).

## Verify Installation

Check your installed version:

```python
import datajoint as dj
print(dj.__version__)
```

**Expected output for this documentation:**

- `2.0.0` or higher — You're ready to follow this documentation
- `0.14.x` or lower — You have the stable version, use [legacy docs](https://datajoint.github.io/datajoint-python) instead

### If You Have an Older Version

| Your Situation | Action |
|----------------|--------|
| Installed 0.14.x, want to upgrade | `pip install --upgrade datajoint` |
| Have existing 0.14.x pipeline to upgrade | Follow [Migration Guide](migrate-to-v20.md) |

## Database Server

DataJoint connects to either MySQL or PostgreSQL. MySQL has been supported since the original release; PostgreSQL support was added in **2.1**, and the `database.name` setting for selecting a non-default PostgreSQL database was added in **2.2.1**. See [Configure Database Connection](configure-database.md#postgresql-backend) for the full configuration reference.

### DataJoint.com (Recommended)

[DataJoint.com](https://datajoint.com) provides fully managed infrastructure for scientific data pipelines—cloud or on-premises—with comprehensive support, automatic backups, object storage, and team collaboration features.

### Local Development (Docker)

```bash
# MySQL
docker run -d \
  --name datajoint-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=simple \
  mysql:8.0
```

```bash
# PostgreSQL (added in 2.1)
docker run -d \
  --name datajoint-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=simple \
  postgres:15
```

### Self-Managed Cloud Databases

- **Amazon RDS** — MySQL, Aurora MySQL, PostgreSQL, or Aurora PostgreSQL
- **Google Cloud SQL** — MySQL or PostgreSQL
- **Azure Database** — MySQL or PostgreSQL

See [Configure Database Connection](configure-database.md) for connection setup.

## Your First Pipeline

With DataJoint installed and a database reachable, this is the shortest end-to-end path: point
DataJoint at your database, declare a few tables, insert a row, and run a computation.

Configure your project (see [Configuration](../reference/configuration.md) for the full
reference):

```bash
# Non-sensitive settings
echo '{"database": {"host": "localhost", "port": 3306}}' > datajoint.json

# Credentials, kept out of the project files
mkdir -p .secrets
echo "<your-username>" > .secrets/database.user
echo "<your-password>" > .secrets/database.password
chmod 600 .secrets/*
```

Define and populate a simple pipeline:

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
    session_idx : int16
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

`Subject` and `Session` are entered by hand; `SessionAnalysis` derives from `Session` and fills
itself when you call `populate()`. That dependency — declared with `->` — is the whole of the
[Relational Workflow Model](../explanation/relational-workflow-model.md) in miniature.

## Running the Tutorial Notebooks

The [tutorials](../tutorials/index.md) are published with their outputs, so you can read them
straight through. To run them yourself, add Jupyter to the environment above and get a copy of
the notebooks — each tutorial page has a download link, or clone the documentation repository
for all of them at once:

```bash
pip install jupyterlab

git clone https://github.com/datajoint/datajoint-docs.git
jupyter lab datajoint-docs/src/tutorials/
```

Configuration works exactly as in the example above: DataJoint searches upward from the
notebook's directory for `datajoint.json` and reads credentials from the `.secrets/` directory
beside it. The repository ships a `datajoint.json` at its root pointing at `localhost:3306` —
edit it to match your own server, and add your own `.secrets/`. Each tutorial creates its own
schema, so they do not collide with each other or with your existing databases.

Two dependencies are worth installing up front:

- **Graphviz**, for the `dj.Diagram` cells — see
  [Troubleshooting](#djdiagram-raises-filenotfounderror) below.
- **An object store**, for the tutorials that use `<blob@>`, `<npy@>`, or `<attach@>` types. The
  committed `datajoint.json` writes to a local directory, which needs no extra services; see
  [Configure Storage](configure-storage.md) to point it elsewhere.

## Platform support

DataJoint runs on **Linux, macOS, and Windows**.

- CI validates the **full test suite — including database integration** — on Linux, across both ends of the supported Python range (3.10 and 3.14).
- The **unit-test suite additionally runs on Windows** (Python 3.10 and 3.14). This covers OS-specific behavior — notably filesystem path handling for file-protocol object stores and garbage collection, where native path separators must not leak into store paths.
- macOS is a supported development platform.

## Troubleshooting

### `pymysql` connection errors

```bash
pip install pymysql --force-reinstall
```

### `psycopg2` connection errors

```bash
pip install datajoint[postgres] --force-reinstall
```

The PostgreSQL backend (added in 2.1) requires the `postgres` extra, which installs `psycopg2-binary`.

### SSL/TLS connection issues

Set `use_tls=False` for local development:

```python
dj.config['database.use_tls'] = False
```

### Permission denied

Ensure your database user has appropriate privileges:

```sql
-- MySQL
GRANT ALL PRIVILEGES ON `your_schema%`.* TO 'username'@'%';
```

```sql
-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE my_db TO username;
```

### `dj.Diagram` raises `FileNotFoundError`

Install Graphviz:

```bash
brew install graphviz                 # macOS
sudo apt-get install graphviz         # Debian/Ubuntu
conda install -c conda-forge graphviz # conda, any platform
```

Diagrams render through `pydot` — installed with DataJoint — which calls the Graphviz `dot`
executable. Graphviz is a system package, so `pip` cannot supply it. On Windows, install
from [graphviz.org/download](https://graphviz.org/download/) and put its `bin` directory on
your `PATH`. Verify with `dot -V`.
