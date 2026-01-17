# Design Primary Keys

Choose effective primary keys for your tables.

## Primary Key Principles

Primary key attributes:

- Uniquely identify each entity
- Cannot be NULL
- Cannot be changed after insertion
- Are inherited by dependent tables via foreign keys

## Natural Keys

Use meaningful identifiers when they exist:

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)    # Lab-assigned ID like 'M001'
    ---
    species : varchar(32)
    """
```

**Good candidates:**
- Lab-assigned IDs
- Standard identifiers (NCBI accession, DOI)
- Meaningful codes with enforced uniqueness

## Composite Keys

Combine attributes when a single attribute isn't unique:

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : int32        # Session number within subject
    ---
    session_date : date
    """
```

The primary key is `(subject_id, session_idx)`.

## Surrogate Keys

Use UUIDs when natural keys don't exist:

```python
@schema
class Experiment(dj.Manual):
    definition = """
    experiment_id : uuid
    ---
    description : varchar(500)
    """
```

Generate UUIDs:

```python
import uuid

Experiment.insert1({
    'experiment_id': uuid.uuid4(),
    'description': 'Pilot study'
})
```

## Why DataJoint Avoids Auto-Increment

DataJoint discourages `auto_increment` for primary keys:

1. **Encourages lazy design** — Users treat it as "row number" rather than thinking about what uniquely identifies the entity in their domain.

2. **Incompatible with composite keys** — DataJoint schemas routinely use composite keys like `(subject_id, session_idx, trial_idx)`. MySQL allows only one auto_increment column per table, and it must be first in the key.

3. **Breaks reproducibility** — Auto_increment values depend on insertion order. Rebuilding a pipeline produces different IDs.

4. **No client-server handshake** — The client discovers the ID only *after* insertion, complicating error handling and concurrent access.

5. **Meaningless foreign keys** — Downstream tables inherit opaque integers rather than traceable lineage.

**Instead, use:**
- Natural keys that identify entities in your domain
- UUIDs when no natural identifier exists
- Composite keys combining foreign keys with sequence numbers

## Foreign Keys in Primary Key

Foreign keys above the `---` become part of the primary key:

```python
@schema
class Trial(dj.Manual):
    definition = """
    -> Session                  # In primary key
    trial_idx : int32          # In primary key
    ---
    -> Stimulus                  # NOT in primary key
    outcome : enum('hit', 'miss')
    """
```

## Key Design Guidelines

### Keep Keys Small

Prefer `int32` over `int64` when the range allows:

```python
# Good: Appropriate size
session_idx : int32     # Max 65,535 sessions per subject

# Avoid: Unnecessarily large
session_idx : int64      # Wastes space, slower joins
```

### Use Fixed-Width for Joins

Fixed-width types join faster:

```python
# Good: Fixed width
subject_id : char(8)

# Acceptable: Variable width
subject_id : varchar(16)
```

### Avoid Dates as Primary Keys

Dates alone rarely guarantee uniqueness:

```python
# Bad: Date might not be unique
session_date : date
---
...

# Good: Add a sequence number
-> Subject
session_idx : int32
---
session_date : date
```

### Avoid Computed Values

Primary keys should be stable inputs, not derived:

```python
# Bad: Derived from other data
hash_id : varchar(64)  # MD5 of some content

# Good: Assigned identifier
recording_id : uuid
```

## Migration Considerations

Once a table has data, primary keys cannot be changed. Plan carefully:

```python
# Consider future needs
@schema
class Scan(dj.Manual):
    definition = """
    -> Session
    scan_idx : int16           # Might need int32 for high-throughput
    ---
    ...
    """
```

## See Also

- [Define Tables](define-tables.md) — Table definition syntax
- [Model Relationships](model-relationships.ipynb) — Foreign key patterns
