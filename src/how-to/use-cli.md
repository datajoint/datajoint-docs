# Use the Command-Line Interface

Start an interactive Python REPL with DataJoint pre-loaded.

The `dj` command provides quick access to DataJoint for exploring schemas, running queries, and testing connections without writing scripts.

## Start the REPL

```bash
dj
```

This opens a Python REPL with `dj` (DataJoint) already imported:

```
DataJoint 2.0.0 REPL
Type 'dj.' and press Tab for available functions.

>>> dj.conn()  # Connect to database
>>> dj.list_schemas()  # List available schemas
```

## Specify Database Credentials

Override config file settings from the command line:

```bash
dj --host localhost:3306 --user root --password secret
```

| Option | Description |
|--------|-------------|
| `--host HOST` | Database host as `host:port` |
| `-u`, `--user USER` | Database username |
| `-p`, `--password PASS` | Database password |

Credentials from command-line arguments override values in config files.

## Load Schemas as Virtual Modules

Load database schemas directly into the REPL namespace:

```bash
dj -s my_lab:lab -s my_analysis:analysis
```

The format is `schema_name:alias` where:

- `schema_name` is the database schema name
- `alias` is the variable name in the REPL

This outputs:

```
DataJoint 2.0.0 REPL
Type 'dj.' and press Tab for available functions.

Loaded schemas:
  lab -> my_lab
  analysis -> my_analysis

>>> lab.Subject.to_dicts()  # Query Subject table
>>> dj.Diagram(lab.schema)  # View schema diagram
```

## Common Workflows

### Explore an Existing Schema

```bash
dj -s production_db:db
```

```python
>>> list(db.schema)  # List all tables
>>> db.Experiment().to_dicts()[:5]  # Preview data
>>> dj.Diagram(db.schema)  # Visualize structure
```

### Quick Data Check

```bash
dj --host db.example.com -s my_lab:lab
```

```python
>>> len(lab.Session())  # Count sessions
>>> lab.Session.describe()  # Show table definition
```

### Test Connection

```bash
dj --host localhost:3306 --user testuser --password testpass
```

```python
>>> dj.conn()  # Verify connection works
>>> dj.list_schemas()  # Check accessible schemas
```

## Version Information

Display DataJoint version:

```bash
dj --version
```

## Help

Display all options:

```bash
dj --help
```

## Entry Points

The CLI is available as both `dj` and `datajoint`:

```bash
dj --version
datajoint --version  # Same command
```

## Programmatic Usage

The CLI function can also be called from Python:

```python
from datajoint.cli import cli

# Show version and exit
cli(["--version"])

# Start REPL with schemas
cli(["-s", "my_lab:lab"])
```
