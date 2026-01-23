# Testing DataJoint Packages

Best practices for integration and unit testing in packages that depend on DataJoint.

## Principles

1. **Use real databases** — Test against MySQL or PostgreSQL, not mocks. DataJoint's behavior depends on database semantics (transactions, foreign keys, type coercion).

2. **Isolate tests** — Each test should use its own schema to avoid interference. Clean up on both success and failure.

3. **Reuse connections** — Create connections once per session, not per test. Database connections are expensive.

4. **Test logic, not volume** — Use minimal data that exercises your code paths. Integration tests should be fast.

## Database Setup

### Local Development

Use Docker Compose to run test databases:

```yaml
# docker-compose.yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: datajoint
      POSTGRES_PASSWORD: datajoint
    ports:
      - "5432:5432"
```

```bash
docker compose up -d
```

### Environment Variables

Configure DataJoint via environment variables for flexibility across environments:

```bash
export DJ_HOST=localhost
export DJ_PORT=5432
export DJ_USER=datajoint
export DJ_PASS=datajoint
export DJ_BACKEND=postgresql
```

## Pytest Fixtures

### Connection Fixture (Session-Scoped)

Create the connection once per test session:

```python
# conftest.py
import os
import pytest
import datajoint as dj


@pytest.fixture(scope="session")
def dj_connection():
    """Configure and return DataJoint connection for the test session."""
    dj.config["database.host"] = os.getenv("DJ_HOST", "localhost")
    dj.config["database.port"] = int(os.getenv("DJ_PORT", 5432))
    dj.config["database.user"] = os.getenv("DJ_USER", "datajoint")
    dj.config["database.password"] = os.getenv("DJ_PASS", "datajoint")
    dj.config["database.use_tls"] = os.getenv("DJ_USE_TLS", "false").lower() == "true"

    backend = os.getenv("DJ_BACKEND", "postgresql")
    if backend == "postgresql":
        dj.config["database.backend"] = "postgresql"

    # Verify connection works
    dj.conn()

    yield dj.conn()
```

### Schema Fixture (Function-Scoped)

Create a fresh schema for each test, with automatic cleanup:

```python
@pytest.fixture
def schema(dj_connection):
    """Create a temporary schema for a single test."""
    import uuid

    # Unique schema name to avoid collisions in parallel runs
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    schema = dj.Schema(schema_name)

    yield schema

    # Cleanup: drop schema even if test fails
    schema.drop(prompt=False)
```

### Schema Fixture (Module-Scoped)

For tests that share table definitions, use module scope:

```python
@pytest.fixture(scope="module")
def shared_schema(dj_connection):
    """Schema shared across tests in a module."""
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    schema = dj.Schema(schema_name)

    yield schema

    schema.drop(prompt=False)
```

## Writing Tests

### Basic Table Test

```python
def test_insert_and_fetch(schema):
    @schema
    class Subject(dj.Manual):
        definition = """
        subject_id : int32
        ---
        name : varchar(100)
        """

    # Insert
    Subject.insert1({"subject_id": 1, "name": "Alice"})

    # Verify
    result = Subject.fetch1()
    assert result["name"] == "Alice"
```

### Testing Computed Tables

```python
def test_computed_table(schema):
    @schema
    class Source(dj.Manual):
        definition = """
        id : int32
        ---
        value : float64
        """

    @schema
    class Computed(dj.Computed):
        definition = """
        -> Source
        ---
        doubled : float64
        """

        def make(self, key):
            value = (Source & key).fetch1("value")
            self.insert1({**key, "doubled": value * 2})

    # Setup
    Source.insert1({"id": 1, "value": 3.5})

    # Run computation
    Computed.populate()

    # Verify
    assert Computed.fetch1("doubled") == 7.0
```

### Testing Foreign Key Constraints

```python
def test_referential_integrity(schema):
    @schema
    class Parent(dj.Manual):
        definition = """
        parent_id : int32
        """

    @schema
    class Child(dj.Manual):
        definition = """
        -> Parent
        child_id : int32
        """

    # Insert parent first
    Parent.insert1({"parent_id": 1})
    Child.insert1({"parent_id": 1, "child_id": 1})

    # Verify FK violation raises error
    with pytest.raises(dj.errors.IntegrityError):
        Child.insert1({"parent_id": 999, "child_id": 2})
```

### Testing Cascading Deletes

```python
def test_cascade_delete(schema):
    @schema
    class Parent(dj.Manual):
        definition = """
        parent_id : int32
        """

    @schema
    class Child(dj.Manual):
        definition = """
        -> Parent
        child_id : int32
        """

    Parent.insert1({"parent_id": 1})
    Child.insert([
        {"parent_id": 1, "child_id": 1},
        {"parent_id": 1, "child_id": 2},
    ])

    assert len(Child()) == 2

    # Delete parent cascades to children
    (Parent & {"parent_id": 1}).delete(prompt=False)

    assert len(Child()) == 0
```

## Testing with Object Storage

For tables using blob storage, configure a test store:

```python
import tempfile

@pytest.fixture(scope="session")
def blob_store(dj_connection):
    """Configure a temporary blob store for tests."""
    store_path = tempfile.mkdtemp(prefix="dj_test_store_")

    dj.config["stores"] = {
        "test": {
            "protocol": "file",
            "location": store_path,
        }
    }

    yield store_path

    # Cleanup
    import shutil
    shutil.rmtree(store_path, ignore_errors=True)


def test_blob_storage(schema, blob_store):
    import numpy as np

    @schema
    class ArrayData(dj.Manual):
        definition = """
        id : int32
        ---
        data : <blob@test>
        """

    arr = np.array([1, 2, 3])
    ArrayData.insert1({"id": 1, "data": arr})

    fetched = ArrayData.fetch1("data")
    assert np.array_equal(fetched, arr)
```

## CI/CD Configuration

### GitHub Actions

```yaml
# .github/workflows/test.yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: datajoint
          POSTGRES_PASSWORD: datajoint
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Run tests
        env:
          DJ_HOST: localhost
          DJ_PORT: 5432
          DJ_USER: datajoint
          DJ_PASS: datajoint
          DJ_BACKEND: postgresql
        run: pytest tests/ -v
```

### Testing Against Multiple Backends

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - backend: postgresql
            image: postgres:15
            port: 5432
          - backend: mysql
            image: mysql:8.0
            port: 3306

    services:
      db:
        image: ${{ matrix.image }}
        # ... service config

    steps:
      - name: Run tests
        env:
          DJ_BACKEND: ${{ matrix.backend }}
          DJ_PORT: ${{ matrix.port }}
        run: pytest tests/ -v
```

## Common Patterns

### Parameterized Tests

Test the same logic with different inputs:

```python
@pytest.mark.parametrize("value,expected", [
    (1, 2),
    (0, 0),
    (-5, -10),
])
def test_doubling(schema, value, expected):
    @schema
    class Numbers(dj.Manual):
        definition = """
        id : int32
        ---
        value : int32
        """

    @schema
    class Doubled(dj.Computed):
        definition = """
        -> Numbers
        ---
        result : int32
        """
        def make(self, key):
            v = (Numbers & key).fetch1("value")
            self.insert1({**key, "result": v * 2})

    Numbers.insert1({"id": 1, "value": value})
    Doubled.populate()

    assert Doubled.fetch1("result") == expected
```

### Testing Error Conditions

```python
def test_duplicate_insert_raises(schema):
    @schema
    class Data(dj.Manual):
        definition = """
        id : int32
        """

    Data.insert1({"id": 1})

    with pytest.raises(dj.errors.DuplicateError):
        Data.insert1({"id": 1})
```

### Fixtures for Sample Data

```python
@pytest.fixture
def sample_subjects(schema):
    """Create Subject table with sample data."""
    @schema
    class Subject(dj.Manual):
        definition = """
        subject_id : varchar(16)
        ---
        species : varchar(50)
        """

    Subject.insert([
        {"subject_id": "M001", "species": "mouse"},
        {"subject_id": "M002", "species": "mouse"},
        {"subject_id": "R001", "species": "rat"},
    ])

    return Subject
```

## Tips

1. **Use `prompt=False`** — Always pass `prompt=False` to `delete()` and `drop()` in tests to avoid interactive prompts.

2. **Unique schema names** — Use UUIDs or timestamps in schema names to allow parallel test execution.

3. **Don't test DataJoint itself** — Trust that DataJoint works. Test your application logic, not basic insert/fetch operations.

4. **Seed random data** — If using random test data, set a fixed seed for reproducibility:
   ```python
   import random
   random.seed(42)
   ```

5. **Skip slow tests** — Mark slow integration tests for optional execution:
   ```python
   @pytest.mark.slow
   def test_large_computation(schema):
       ...
   ```
   ```bash
   pytest -m "not slow"  # Skip slow tests
   pytest -m slow        # Run only slow tests
   ```
