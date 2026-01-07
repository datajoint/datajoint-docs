# Monitor Progress

Track computation progress and job status.

## Progress Display

Show progress bar during populate:

```python
ProcessedData.populate(display_progress=True)
```

## Check Remaining Work

Count entries left to compute:

```python
# What's left to compute
remaining = ProcessedData.key_source - ProcessedData
print(f"{len(remaining)} entries remaining")
```

## Job Status Summary

Get counts by status:

```python
progress = ProcessedData.jobs.progress()
# {'pending': 100, 'reserved': 5, 'error': 3, 'success': 892}

for status, count in progress.items():
    print(f"{status}: {count}")
```

## Filter Jobs by Status

Access jobs by their current status:

```python
# Pending jobs (waiting to run)
ProcessedData.jobs.pending

# Currently running
ProcessedData.jobs.reserved

# Failed jobs
ProcessedData.jobs.errors

# Completed jobs (if keep_completed=True)
ProcessedData.jobs.completed

# Skipped jobs
ProcessedData.jobs.ignored
```

## View Job Details

Inspect specific jobs:

```python
# All jobs for a key
(ProcessedData.jobs & key).fetch1()

# Recent errors
ProcessedData.jobs.errors.to_dicts(
    order_by='completed_time DESC',
    limit=10
)
```

## Worker Information

See which workers are processing:

```python
for job in ProcessedData.jobs.reserved.to_dicts():
    print(f"Key: {job}")
    print(f"Host: {job['host']}")
    print(f"PID: {job['pid']}")
    print(f"Started: {job['reserved_time']}")
```

## Computation Timing

Track how long jobs take:

```python
# Average duration of completed jobs
completed = ProcessedData.jobs.completed.to_arrays('duration')
print(f"Average: {np.mean(completed):.1f}s")
print(f"Median: {np.median(completed):.1f}s")
```

## Enable Job Metadata

Store timing info in computed tables:

```python
import datajoint as dj

dj.config.jobs.add_job_metadata = True
dj.config.jobs.keep_completed = True
```

This adds hidden attributes to computed tables:

- `_job_start_time` — When computation began
- `_job_duration` — How long it took
- `_job_version` — Code version (if configured)

## Simple Progress Script

```python
import time
from my_pipeline import ProcessedData

while True:
    remaining = len(ProcessedData.key_source - ProcessedData)
    progress = ProcessedData.jobs.progress()

    print(f"\rRemaining: {remaining} | "
          f"Pending: {progress.get('pending', 0)} | "
          f"Running: {progress.get('reserved', 0)} | "
          f"Errors: {progress.get('error', 0)}", end='')

    if remaining == 0:
        print("\nDone!")
        break

    time.sleep(10)
```

## Pipeline-Wide Status

Check multiple tables:

```python
tables = [RawData, ProcessedData, Analysis]

for table in tables:
    total = len(table.key_source)
    done = len(table())
    print(f"{table.__name__}: {done}/{total} ({done/total:.0%})")
```

## See Also

- [Run Computations](run-computations.md) — Basic populate usage
- [Distributed Computing](distributed-computing.md) — Multi-worker setup
- [Handle Errors](handle-errors.md) — Error recovery
