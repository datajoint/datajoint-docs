# Use Isolated Instances

Create independent database connections using `dj.Instance` for multi-tenant applications, testing, and parallel pipelines.

## Create an Instance

Provide database credentials directly:

```python
import datajoint as dj

inst = dj.Instance(host="localhost", user="root", password="secret")
```

The Instance has its own config and connection, independent of `dj.config`:

```python
inst.config.safemode = False  # only affects this instance
```

## Create Schemas and Tables

Use `inst.Schema()` instead of `dj.Schema()`:

```python
schema = inst.Schema("my_experiment")

@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    ---
    species : varchar(32)
    """
```

All table operations (insert, query, delete, populate) work identically to the global pattern.

## Pass Config Overrides

Set config values at creation time using keyword arguments:

```python
inst = dj.Instance(
    host="localhost", user="root", password="secret",
    safemode=False,
    database__reconnect=False,  # double underscore for nested keys
)
```

## Work with Multiple Databases

Create one Instance per database:

```python
prod = dj.Instance(host="prod.example.com", user="analyst", password="...")
staging = dj.Instance(host="staging.example.com", user="dev", password="...")

prod_schema = prod.Schema("experiment_data")
staging_schema = staging.Schema("experiment_data")
```

Tables from different Instances are fully independent.

## Use FreeTable with Instances

To access an existing table without defining a class:

```python
inst = dj.Instance(host="localhost", user="root", password="secret")
table = inst.FreeTable("`my_schema`.`my_table`")
table.to_dicts()
```

## Enable Thread-Safe Mode

For web servers and multi-threaded applications, disable global state:

```bash
export DJ_THREAD_SAFE=true
```

In thread-safe mode, `dj.config`, `dj.conn()`, and `dj.Schema()` (without an explicit connection) all raise `ThreadSafetyError`. Only `dj.Instance()` works.

## Use in Web Servers

Create an Instance per request or per tenant:

```python
from flask import Flask, g

app = Flask(__name__)

def get_instance():
    if "dj_inst" not in g:
        g.dj_inst = dj.Instance(
            host="db.example.com",
            user=current_user.db_user,
            password=current_user.db_password,
        )
    return g.dj_inst

@app.route("/subjects")
def list_subjects():
    inst = get_instance()
    schema = inst.Schema("lab_data")
    return Subject.to_dicts()
```

## Use in Tests

Create a fresh Instance per test to ensure isolation:

```python
import pytest
import datajoint as dj

@pytest.fixture
def test_instance():
    inst = dj.Instance(host="localhost", user="root", password="test")
    schema = inst.Schema("test_db")
    yield inst, schema
    schema.drop(prompt=False)

def test_insert(test_instance):
    inst, schema = test_instance

    @schema
    class Item(dj.Manual):
        definition = """
        item_id : int32
        ---
        name : varchar(100)
        """

    Item.insert1({"item_id": 1, "name": "test"})
    assert len(Item) == 1
```

## See Also

- [What's New in 2.2](../explanation/whats-new-22.md/) — Feature overview and rationale
- [Working with Instances](../tutorials/advanced/instances.ipynb/) — Step-by-step tutorial
- [Configuration Reference](../reference/configuration.md/) — Thread-safe mode settings
