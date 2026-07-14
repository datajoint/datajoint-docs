# Run Computations

Execute automated computations with `populate()`.

## Basic Usage

```python
# Populate all missing entries
SessionAnalysis.populate()

# With progress display
SessionAnalysis.populate(display_progress=True)
```

## Restrict What to Compute

```python
# Only specific subjects
SessionAnalysis.populate(Subject & "sex = 'M'")

# Only recent sessions
SessionAnalysis.populate(Session & "session_date > '2026-01-01'")

# Specific key
SessionAnalysis.populate({'subject_id': 'M001', 'session_idx': 1})
```

## Limit Number of Jobs

```python
# Process at most 100 entries
SessionAnalysis.populate(limit=100)
```

## Error Handling

```python
# Continue on errors (log but don't stop)
SessionAnalysis.populate(suppress_errors=True)

# Check what failed
failed = SessionAnalysis.jobs & "status = 'error'"
print(failed)

# Clear errors to retry
failed.delete()
SessionAnalysis.populate()
```

## When to Use Distributed Mode

Choose your populate strategy based on your workload and infrastructure:

### Use `populate()` (Default) When:

- ✅ **Single worker** - Only one process computing at a time
- ✅ **Very fast computations** - Each make() completes in < 1 second
- ✅ **Small job count** - Processing < 100 entries
- ✅ **Development/testing** - Iterating on make() logic

**Advantages:**

- Simplest approach (no job management overhead)
- Immediate execution (no reservation delay)
- Easy debugging (errors stop execution)

**Example:**
```python
# Simple, direct execution
SessionAnalysis.populate()
```

---

### Use `populate(reserve_jobs=True)` When:

- ✅ **Multiple workers** - Running on multiple machines or processes
- ✅ **Computations > 1 second** - Job reservation overhead (~100ms) becomes negligible
- ✅ **Production pipelines** - Need fault tolerance and monitoring
- ✅ **Worker crashes expected** - Jobs can be resumed

**Advantages:**

- Prevents duplicate work between workers
- Fault tolerance (crashed jobs can be retried)
- Job status tracking (`SessionAnalysis.jobs`)
- Error isolation (one failure doesn't stop others)

**Example:**
```python
# Distributed mode with job coordination
SessionAnalysis.populate(reserve_jobs=True)
```

**Job reservation overhead:** ~100ms per job
**Worth it when:** Computations take > 1 second (overhead becomes < 10%)

---

### Use `populate(reserve_jobs=True, processes=N)` When:

- ✅ **Multi-core machine** - Want to use all CPU cores
- ✅ **CPU-bound tasks** - Computations are CPU-intensive, not I/O
- ✅ **Independent computations** - No shared state between jobs

**Advantages:**

- Parallel execution on single machine
- No network coordination needed
- Combines job safety with parallelism

**Example:**
```python
# Use 4 CPU cores
SessionAnalysis.populate(reserve_jobs=True, processes=4)
```

**Caution:** Don't use more processes than CPU cores (causes context switching overhead)

---

## Decision Tree

```
How many workers?
├─ One → populate()
└─ Multiple → Continue...

How long per computation?
├─ < 1 second → populate() (overhead not worth it)
└─ > 1 second → Continue...

Need fault tolerance?
├─ Yes → populate(reserve_jobs=True)
└─ No → populate() (simpler)

Multiple cores on one machine?
└─ Yes → populate(reserve_jobs=True, processes=N)
```

## Distributed Computing

For multi-worker coordination:

```python
# Worker 1 (on machine A)
SessionAnalysis.populate(reserve_jobs=True)

# Worker 2 (on machine B)
SessionAnalysis.populate(reserve_jobs=True)

# Workers coordinate automatically via database
# Each reserves different keys, no duplicates
```

## Check Progress

```python
# What's left to compute
remaining = SessionAnalysis.key_source - SessionAnalysis
print(f"{len(remaining)} entries remaining")

# View job status
SessionAnalysis.jobs
```

## The `make()` Method

```python
@schema
class SessionAnalysis(dj.Computed):
    definition = """
    -> Session
    ---
    result : float64
    """

    def make(self, key):
        # 1. Fetch input data
        data = (Session & key).fetch1('data')

        # 2. Compute
        result = process(data)

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

    def make_fetch(self, key, **kwargs):
        """Fetch input data (outside transaction).

        kwargs are passed from populate(make_kwargs={...}).
        """
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

- [Computation Model](../explanation/computation-model.md/) — How computation works
- [Distributed Computing](distributed-computing.md) — Multi-worker setup
- [Handle Errors](handle-errors.md) — Error recovery
