# Entity Integrity

**Entity integrity** ensures a one-to-one correspondence between real-world
entities and their database records. This is the foundation of reliable data
management.

## The Core Guarantee

- Each real-world entity → exactly one database record
- Each database record → exactly one real-world entity

Without entity integrity, databases become unreliable:

| Integrity Failure | Consequence |
|-------------------|-------------|
| Same entity, multiple records | Fragmented data, conflicting information |
| Multiple entities, same record | Mixed data, privacy violations |
| Cannot match entity to record | Lost data, broken workflows |

## The Three Questions

When designing a primary key, answer these three questions:

### 1. How do I prevent duplicate records?

Ensure the same entity cannot appear twice in the table.

### 2. How do I prevent record sharing?

Ensure different entities cannot share the same record.

### 3. How do I match entities to records?

When an entity arrives, how do I find its corresponding record?

## Example: Laboratory Mouse Database

Consider a neuroscience lab tracking mice:

| Question | Answer |
|----------|--------|
| Prevent duplicates? | Each mouse gets a unique ear tag at arrival; database rejects duplicate tags |
| Prevent sharing? | Ear tags are never reused; retired tags are archived |
| Match entities? | Read the ear tag → look up record by primary key |

```python
@schema
class Mouse(dj.Manual):
    definition = """
    ear_tag : char(6)   # unique ear tag (e.g., 'M00142')
    ---
    date_of_birth : date
    sex : enum('M', 'F', 'U')
    strain : varchar(50)
    """
```

The database enforces the first two questions through the primary key constraint.
The third question requires a **physical identification system**—ear tags,
barcodes, or RFID chips that link physical entities to database records.

## Primary Key Requirements

In DataJoint, every table must have a primary key. Primary key attributes:

- **Cannot be NULL** — Every entity must be identifiable
- **Must be unique** — No two entities share the same key
- **Cannot be changed** — Keys are immutable after insertion
- **Declared above the `---` line** — Syntactic convention

## Natural Keys vs. Surrogate Keys

### Natural Keys

Use attributes that naturally identify entities in your domain:

```python
@schema
class Gene(dj.Lookup):
    definition = """
    gene_symbol : varchar(20)   # Official gene symbol (e.g., 'BRCA1')
    ---
    full_name : varchar(200)
    chromosome : varchar(5)
    """
```

**Advantages:**

- Meaningful to humans
- Self-documenting
- No additional lookup needed

### Surrogate Keys

Use system-generated identifiers:

```python
@schema
class Sample(dj.Manual):
    definition = """
    sample_id : int unsigned auto_increment
    ---
    collection_date : date
    sample_type : varchar(50)
    """
```

**Advantages:**

- Stable (never change)
- Compact for joins
- No business logic dependency

**DataJoint recommendation:** Prefer natural keys when they're stable and
meaningful. Use surrogates when natural keys are unstable or complex.

## Composite Keys

When no single attribute uniquely identifies an entity, combine multiple
attributes:

```python
@schema
class Recording(dj.Manual):
    definition = """
    -> Session
    recording_id : int   # Recording number within session
    ---
    duration : float     # seconds
    """
```

Here, `(session_id, recording_id)` together form the primary key. Neither
alone would be unique.

## Foreign Keys and Dependencies

Foreign keys in DataJoint serve dual purposes:

1. **Referential integrity** — Ensures referenced entities exist
2. **Workflow dependency** — Declares that this entity depends on another

```python
@schema
class Segmentation(dj.Computed):
    definition = """
    -> Scan           # Depends on Scan
    ---
    num_cells : int
    """
```

The arrow `->` inherits the primary key from `Scan` and establishes both
referential integrity and workflow dependency.

## Schema Dimensions

Primary keys across tables define **schema dimensions**—the axes along which
your data varies. Common dimensions in neuroscience:

- **Subject** — Who/what is being studied
- **Session** — When data was collected
- **Modality** — What type of data (ephys, imaging, behavior)

Understanding dimensions helps design schemas that naturally express your
experimental structure.

## Best Practices

1. **Answer the three questions** before designing any table
2. **Choose stable identifiers** that won't need to change
3. **Keep keys minimal** — Include only what's necessary for uniqueness
4. **Document key semantics** — Explain what the key represents
5. **Consider downstream queries** — Keys affect join performance

## Common Mistakes

### Too few key attributes

```python
# Wrong: experiment_id alone isn't unique
class Trial(dj.Manual):
    definition = """
    experiment_id : int
    ---
    trial_number : int   # Should be part of key!
    result : float
    """
```

### Too many key attributes

```python
# Wrong: timestamp makes every row unique, losing entity semantics
class Measurement(dj.Manual):
    definition = """
    subject_id : int
    timestamp : datetime(6)   # Microsecond precision
    ---
    value : float
    """
```

### Mutable natural keys

```python
# Risky: names can change
class Patient(dj.Manual):
    definition = """
    patient_name : varchar(100)   # What if they change their name?
    ---
    date_of_birth : date
    """
```

## Summary

Entity integrity is maintained by:

1. **Primary keys** that uniquely identify each entity
2. **Foreign keys** that establish valid references
3. **Physical systems** that link real-world entities to records

The three questions framework ensures your primary keys provide meaningful,
stable identification for your domain entities.
