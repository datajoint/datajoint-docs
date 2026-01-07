# Handle Errors

Manage computation errors and recover failed jobs.

## Suppress Errors During Populate

Continue processing despite individual failures:

```python
# Stop on first error (default)
ProcessedData.populate()

# Log errors but continue
ProcessedData.populate(suppress_errors=True)
```

## View Failed Jobs

Check the jobs table for errors:

```python
# All error jobs
ProcessedData.jobs.errors

# View error details
for job in ProcessedData.jobs.errors.fetch(as_dict=True):
    print(f"Key: {job}")
    print(f"Message: {job['error_message']}")
```

## Get Full Stack Trace

Error stack traces are stored in the jobs table:

```python
job = (ProcessedData.jobs.errors & key).fetch1()
print(job['error_stack'])
```

## Retry Failed Jobs

Clear error status and rerun:

```python
# Delete error records to retry
ProcessedData.jobs.errors.delete()

# Reprocess
ProcessedData.populate(reserve_jobs=True)
```

## Retry Specific Jobs

Target specific failed jobs:

```python
# Clear one error
(ProcessedData.jobs & key & 'status="error"').delete()

# Retry just that key
ProcessedData.populate(key, reserve_jobs=True)
```

## Ignore Problematic Jobs

Mark jobs to skip permanently:

```python
# Mark job as ignored
ProcessedData.jobs.ignore(key)

# View ignored jobs
ProcessedData.jobs.ignored
```

## Error Handling in make()

Handle expected errors gracefully:

```python
@schema
class ProcessedData(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    def make(self, key):
        try:
            data = (RawData & key).fetch1('data')
            result = risky_computation(data)
        except ValueError as e:
            # Log and skip this key
            logger.warning(f"Skipping {key}: {e}")
            return  # Don't insert, job remains pending

        self.insert1({**key, 'result': result})
```

## Transaction Rollback

Failed `make()` calls automatically rollback:

```python
def make(self, key):
    # These inserts are in a transaction
    self.insert1({**key, 'result': value1})
    PartTable.insert(parts)

    # If this raises, all inserts are rolled back
    validate_result(key)
```

## Return Exception Objects

Get exception objects for programmatic handling:

```python
result = ProcessedData.populate(
    suppress_errors=True,
    return_exception_objects=True
)

for key, exception in result['error_list']:
    if isinstance(exception, TimeoutError):
        # Handle timeout differently
        schedule_for_later(key)
```

## Monitor Error Rate

Track errors over time:

```python
progress = ProcessedData.jobs.progress()
print(f"Pending: {progress.get('pending', 0)}")
print(f"Errors: {progress.get('error', 0)}")
print(f"Success: {progress.get('success', 0)}")

error_rate = progress.get('error', 0) / sum(progress.values())
print(f"Error rate: {error_rate:.1%}")
```

## Common Error Patterns

### Data Quality Issues

```python
def make(self, key):
    data = (RawData & key).fetch1('data')

    if not validate_data(data):
        raise DataJointError(f"Invalid data for {key}")

    # Process valid data
    self.insert1({**key, 'result': process(data)})
```

### Resource Constraints

```python
def make(self, key):
    try:
        result = memory_intensive_computation(key)
    except MemoryError:
        # Clear caches and retry once
        gc.collect()
        result = memory_intensive_computation(key)

    self.insert1({**key, 'result': result})
```

### External Service Failures

```python
def make(self, key):
    for attempt in range(3):
        try:
            data = fetch_from_external_api(key)
            break
        except ConnectionError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

    self.insert1({**key, 'result': process(data)})
```

## See Also

- [Run Computations](run-computations.md) — Basic populate usage
- [Distributed Computing](distributed-computing.md) — Multi-worker error handling
- [Monitor Progress](monitor-progress.md) — Tracking job status
