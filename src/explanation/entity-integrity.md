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

A **surrogate key** is an identifier used *primarily inside* the database, with minimal or no exposure to end users. Users typically don't search for entities by surrogate keys or use them in conversation.

```python
@schema
class InternalRecord(dj.Manual):
    definition = """
    record_id : uuid    # internal identifier, not exposed to users
    ---
    created_timestamp : datetime(3)
    data : <blob>
    """
```

**Key distinction from natural keys:** Surrogate keys don't require external identification systems because users don't need to match physical entities to records by these keys.

**When surrogate keys are appropriate:**

- Entities that exist only within the system (no physical counterpart)
- Privacy-sensitive contexts where natural identifiers shouldn't be stored
- Internal system records that users never reference directly

**Generating surrogate keys:** DataJoint requires explicit key values rather than database-generated auto-increment. This is intentional:

- Auto-increment encourages treating keys as "row numbers" rather than entity identifiers
- It's incompatible with composite keys, which DataJoint uses extensively
- It breaks reproducibility (different IDs when rebuilding pipelines)
- It prevents the client-server handshake needed for proper entity integrity

Use client-side generation instead:

- **UUIDs** — Generate with `uuid.uuid4()` before insertion
- **ULIDs** — Sortable unique IDs
- **Client-side counters** — Query max value and increment

**DataJoint recommendation:** Prefer natural keys when they're stable and
meaningful. Use surrogates only when no natural identifier exists or for
privacy-sensitive contexts.

## Composite Keys

When no single attribute uniquely identifies an entity, combine multiple
attributes:

```python
@schema
class Recording(dj.Manual):
    definition = """
    -> Session
    recording_idx : uint16   # Recording number within session
    ---
    duration : float32       # seconds
    """
```

Here, `(subject_id, session_idx, recording_idx)` together form the primary key.
Neither alone would be unique.

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
    num_cells : uint32
    """
```

The arrow `->` inherits the primary key from `Scan` and establishes both
referential integrity and workflow dependency.

## Schema Dimensions

A **dimension** is an independent axis of variation in your data, introduced by
a table that defines new primary key attributes. Dimensions are the fundamental
building blocks of schema design.

### Dimension-Introducing Tables

A table **introduces a dimension** when it defines primary key attributes that
don't come from a foreign key. In schema diagrams, these tables have
**underlined names**.

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)   # NEW dimension: subject_id
    ---
    species : varchar(50)
    """

@schema
class Modality(dj.Lookup):
    definition = """
    modality : varchar(32)     # NEW dimension: modality
    ---
    description : varchar(255)
    """
```

Both `Subject` and `Modality` are dimension-introducing tables—they create new
axes along which data varies.

### Dimension-Inheriting Tables

A table **inherits dimensions** when its entire primary key comes from foreign
keys. In schema diagrams, these tables have **non-underlined names**.

```python
@schema
class SubjectProfile(dj.Manual):
    definition = """
    -> Subject                 # Inherits subject_id dimension
    ---
    weight : float32
    """
```

`SubjectProfile` doesn't introduce a new dimension—it extends the `Subject`
dimension with additional attributes. There's exactly one profile per subject.

### Mixed Tables

Most tables both inherit and introduce dimensions:

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject                 # Inherits subject_id dimension
    session_idx : uint16       # NEW dimension within subject
    ---
    session_date : date
    """
```

`Session` inherits the subject dimension but introduces a new dimension
(`session_idx`) within each subject. This creates a hierarchical structure.

### Computed Tables and Dimensions

**Computed tables never introduce dimensions.** Their primary key is entirely
inherited from their dependencies:

```python
@schema
class SessionSummary(dj.Computed):
    definition = """
    -> Session                 # PK = (subject_id, session_idx)
    ---
    num_trials : uint32
    accuracy : float32
    """
```

This makes sense—computed tables derive data from existing entities rather
than introducing new ones.

### Part Tables CAN Introduce Dimensions

Unlike computed tables, **part tables can introduce new dimensions**:

```python
@schema
class Detection(dj.Computed):
    definition = """
    -> Image                   # Inherits image_id
    -> DetectionParams         # Inherits params_id
    ---
    num_blobs : uint32
    """

    class Blob(dj.Part):
        definition = """
        -> master              # Inherits (image_id, params_id)
        blob_idx : uint16      # NEW dimension within detection
        ---
        x : float32
        y : float32
        """
```

`Detection` inherits dimensions (no underline in diagram), but `Detection.Blob`
introduces a new dimension (`blob_idx`) for individual blobs within each
detection.

### Dimensions and Attribute Lineage

Every primary key attribute traces back to the dimension where it was first
defined. This is called **attribute lineage**:

```
Subject.subject_id      → myschema.subject.subject_id (origin)
Session.subject_id      → myschema.subject.subject_id (inherited)
Session.session_idx     → myschema.session.session_idx (origin)
Trial.subject_id        → myschema.subject.subject_id (inherited)
Trial.session_idx       → myschema.session.session_idx (inherited)
Trial.trial_idx         → myschema.trial.trial_idx (origin)
```

Lineage enables **semantic matching**—DataJoint only joins attributes that
trace back to the same dimension. Two attributes named `id` from different
dimensions cannot be accidentally joined.

See [Semantic Matching](../reference/specs/semantic-matching.md) for details.

### Recognizing Dimensions in Diagrams

In schema diagrams:

| Visual | Meaning |
|--------|---------|
| **Underlined name** | Introduces at least one new dimension |
| Non-underlined name | All PK attributes inherited (no new dimensions) |
| **Thick solid line** | One-to-one extension (no new dimension) |
| **Thin solid line** | Containment (may introduce dimension) |

Common dimensions in neuroscience:

- **Subject** — Who/what is being studied
- **Session** — When data was collected
- **Trial** — Individual experimental unit
- **Modality** — Type of data (ephys, imaging, behavior)
- **Parameter set** — Configuration for analysis

Understanding dimensions helps design schemas that naturally express your
experimental structure and ensures correct joins through semantic matching.

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
    experiment_id : uint32
    ---
    trial_number : uint16   # Should be part of key!
    result : float32
    """
```

### Too many key attributes

```python
# Wrong: timestamp makes every row unique, losing entity semantics
class Measurement(dj.Manual):
    definition = """
    subject_id : uint32
    timestamp : datetime(6)   # Microsecond precision
    ---
    value : float32
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
