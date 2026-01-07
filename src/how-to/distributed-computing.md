# Distributed Computing

Run computations across multiple workers with job coordination.

## Enable Distributed Mode

Use `reserve_jobs=True` to enable job coordination:

```python
# Single worker (default)
ProcessedData.populate()

# Distributed mode with job reservation
ProcessedData.populate(reserve_jobs=True)
```

## How It Works

With `reserve_jobs=True`:
1. Worker checks the jobs table for pending work
2. Atomically reserves a job before processing
3. Other workers see the job as reserved and skip it
4. On completion, job is marked success (or error)

## Multi-Process on Single Machine

```python
# Use multiple processes
ProcessedData.populate(reserve_jobs=True, processes=4)
```

Each process:
- Opens its own database connection
- Reserves jobs independently
- Processes in parallel

## Multi-Machine Cluster

Run the same script on multiple machines:

```python
# worker_script.py - run on each machine
import datajoint as dj
from my_pipeline import ProcessedData

# Each worker reserves and processes different jobs
ProcessedData.populate(
    reserve_jobs=True,
    display_progress=True,
    suppress_errors=True
)
```

Workers automatically coordinate through the jobs table.

## Job Table

Each auto-populated table has a jobs table (`~~table_name`):

```python
# View job status
ProcessedData.jobs

# Filter by status
ProcessedData.jobs.pending
ProcessedData.jobs.reserved
ProcessedData.jobs.errors
ProcessedData.jobs.completed
```

## Job Statuses

| Status | Description |
|--------|-------------|
| `pending` | Queued, ready to process |
| `reserved` | Being processed by a worker |
| `success` | Completed successfully |
| `error` | Failed with error |
| `ignore` | Marked to skip |

## Refresh Job Queue

Sync the job queue with current key_source:

```python
# Add new pending jobs, remove stale ones
result = ProcessedData.jobs.refresh()
print(f"Added: {result['added']}, Removed: {result['removed']}")
```

## Priority Scheduling

Control processing order with priorities:

```python
# Refresh with specific priority
ProcessedData.jobs.refresh(priority=1)  # Lower = more urgent

# Process only high-priority jobs
ProcessedData.populate(reserve_jobs=True, priority=3)
```

## Error Recovery

Handle failed jobs:

```python
# View errors
errors = ProcessedData.jobs.errors
for job in errors.fetch(as_dict=True):
    print(f"Key: {job}, Error: {job['error_message']}")

# Clear errors to retry
errors.delete()
ProcessedData.populate(reserve_jobs=True)
```

## Orphan Detection

Jobs from crashed workers are automatically recovered:

```python
# Refresh with orphan timeout (seconds)
ProcessedData.jobs.refresh(orphan_timeout=3600)
```

Reserved jobs older than the timeout are reset to pending.

## Configuration

```python
import datajoint as dj

# Auto-refresh on populate (default: True)
dj.config.jobs.auto_refresh = True

# Keep completed job records (default: False)
dj.config.jobs.keep_completed = True

# Stale job timeout in seconds (default: 3600)
dj.config.jobs.stale_timeout = 3600

# Default job priority (default: 5)
dj.config.jobs.default_priority = 5

# Track code version (default: None)
dj.config.jobs.version_method = "git"
```

## Populate Options

| Option | Default | Description |
|--------|---------|-------------|
| `reserve_jobs` | `False` | Enable job coordination |
| `processes` | `1` | Number of worker processes |
| `max_calls` | `None` | Limit jobs per run |
| `display_progress` | `False` | Show progress bar |
| `suppress_errors` | `False` | Continue on errors |
| `priority` | `None` | Filter by priority |
| `refresh` | `None` | Force refresh before run |

## Example: Cluster Setup

```python
# config.py - shared configuration
import datajoint as dj

dj.config.jobs.auto_refresh = True
dj.config.jobs.keep_completed = True
dj.config.jobs.version_method = "git"

# worker.py - run on each node
from config import *
from my_pipeline import ProcessedData

while True:
    result = ProcessedData.populate(
        reserve_jobs=True,
        max_calls=100,
        suppress_errors=True,
        display_progress=True
    )
    if result['success_count'] == 0:
        break  # No more work
```

## See Also

- [Run Computations](run-computations.md) — Basic populate usage
- [Handle Errors](handle-errors.md) — Error recovery patterns
- [Monitor Progress](monitor-progress.md) — Tracking job status
