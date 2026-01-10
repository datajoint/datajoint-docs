# Run Computations

Execute automated computations with `populate()`.

## Basic Usage

```python
# Populate all missing entries
ProcessedData.populate()

# With progress display
ProcessedData.populate(display_progress=True)
```

## Restrict What to Compute

```python
# Only specific subjects
ProcessedData.populate(Subject & "sex = 'M'")

# Only recent sessions
ProcessedData.populate(Session & "session_date > '2026-01-01'")

# Specific key
ProcessedData.populate({'subject_id': 'M001', 'session_idx': 1})
```

## Limit Number of Jobs

```python
# Process at most 100 entries
ProcessedData.populate(limit=100)
```

## Error Handling

```python
# Continue on errors (log but don't stop)
ProcessedData.populate(suppress_errors=True)

# Check what failed
failed = ProcessedData.jobs & 'status = "error"'
print(failed)

# Clear errors to retry
failed.delete()
ProcessedData.populate()
```

## Distributed Computing

```python
# Reserve jobs to prevent conflicts between workers
ProcessedData.populate(reserve_jobs=True)

# Run on multiple machines/processes simultaneously
# Each worker reserves and processes different keys
```

## Check Progress

```python
# What's left to compute
remaining = ProcessedData.key_source - ProcessedData
print(f"{len(remaining)} entries remaining")

# View job status
ProcessedData.jobs
```

## The `make()` Method

```python
@schema
class ProcessedData(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    def make(self, key):
        # 1. Fetch input data
        raw = (RawData & key).fetch1('data')

        # 2. Compute
        result = process(raw)

        # 3. Insert
        self.insert1({**key, 'result': result})
```

## Three-Part Make for Long Computations

For computations taking hours or days:

```python
@schema
class LongComputation(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    def make_fetch(self, key):
        """Fetch input data (outside transaction)"""
        data = (RawData & key).fetch1('data')
        return (data,)

    def make_compute(self, key, fetched):
        """Perform computation (outside transaction)"""
        (data,) = fetched
        result = expensive_computation(data)
        return (result,)

    def make_insert(self, key, fetched, computed):
        """Insert results (inside brief transaction)"""
        (result,) = computed
        self.insert1({**key, 'result': result})
```

## Custom Key Source

```python
@schema
class FilteredComputation(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    @property
    def key_source(self):
        # Only compute for high-quality data
        return (RawData & 'quality > 0.8') - self
```

## Populate Options

| Option | Default | Description |
|--------|---------|-------------|
| `restriction` | `None` | Filter what to compute |
| `limit` | `None` | Max entries to process |
| `display_progress` | `False` | Show progress bar |
| `reserve_jobs` | `False` | Reserve jobs for distributed computing |
| `suppress_errors` | `False` | Continue on errors |

## See Also

- [Computation Model](../explanation/computation-model.md) — How computation works
- [Distributed Computing](distributed-computing.md) — Multi-worker setup
- [Handle Errors](handle-errors.md) — Error recovery
