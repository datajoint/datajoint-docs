# Entity Integrity

## Formal definition

**Entity integrity** is the guarantee of a **one-to-one correspondence**
between real-world entities and their representations in the database:

- Each real-world entity corresponds to **exactly one** database record.
- Each database record corresponds to **exactly one** real-world entity.

The correspondence is *bidirectional*. A primary-key constraint alone is not
sufficient; uniqueness inside the database is only half the requirement.

## Two required components

Entity integrity requires both an external mechanism and an internal one.
Neither suffices on its own.

| Component | Where it lives | What it does |
|---|---|---|
| **Real-world identification process** | Outside the database | Establishes and maintains a reliable, unique association between each real-world entity and its identifier (ear tag, student ID, VIN, ISBN, SSN). |
| **Database uniqueness constraint** | Inside the database | Enforces — via the primary key — that no two records share the same identifier. |

The database can enforce uniqueness but cannot create it. The real-world
identification process is what links a physical entity to its identifier in
the first place; the database mirrors and protects that association.

## The three questions

When designing the primary key for a table, answer all three:

1. **How do I prevent duplicate records?** — The same entity must not appear
   twice. The primary-key constraint handles this once the entity has been
   identified.
2. **How do I prevent record sharing?** — Two different entities must not
   share the same record. This is what the real-world identification process
   prevents; the database alone cannot.
3. **How do I match an entity to its record?** — When an entity arrives, how
   do I find the record that represents it? This depends on the
   identification mechanism — ear tag, barcode, government ID, token issued
   at first contact.

## Example: laboratory mouse database

| Question | Answer |
|----------|--------|
| Prevent duplicates? | Each mouse gets a unique ear tag at arrival; the database rejects duplicate tags. |
| Prevent sharing? | Ear tags are never reused; retired tags are archived. |
| Match entity to record? | Read the ear tag → look up the record by primary key. |

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

The database enforces the first question through the primary-key constraint.
The second and third questions require a **physical identification system**
— ear tags, microchips, barcodes, RFID — that links physical entities to
their identifiers. Without that, the database is enforcing uniqueness of an
identifier with no reliable connection to anything real.

## Primary-key requirements

Every DataJoint table must have a primary key. Primary-key attributes:

- **Cannot be NULL** — every entity must be identifiable.
- **Must be unique** — no two entities share the same key.
- **Cannot be changed** — keys are immutable after insertion.
- **Declared above the `---`** in the table definition.

### Explicit keys, no auto-increment

DataJoint requires every primary-key value to be provided explicitly at
insertion. There is no `AUTO_INCREMENT`. This is a deliberate choice that
follows from the formal definition above:

- **Identification before insertion.** The client must commit to *which*
  entity it is inserting. Auto-increment treats the key as a row number —
  the database invents an identifier the client never sees — which breaks
  the bidirectional mapping at the point of entry.
- **Duplicate detection.** Running the same insertion twice with the same
  explicit key produces a key collision rather than two records for one
  entity. Auto-increment would silently insert twice.
- **Composite keys.** Auto-increment is incompatible with composite primary
  keys, which DataJoint uses extensively for hierarchical entities.
- **Reproducibility.** Re-building a pipeline from sources should produce
  the same identifiers; auto-increment makes them depend on insertion
  order.

For surrogate keys, generate values client-side (UUID, ULID, NanoID, or a
client-side counter) before insertion.

## Natural keys and surrogate keys

A primary key can be **natural** or **surrogate** depending on whether the
identifier is used outside the database.

### Natural keys

A **natural key** is an identifier used *outside* the database to refer to
the entity. It requires a real-world mechanism — ear tag, ID card, VIN — to
establish and maintain the entity-to-identifier association. Examples:

- External standards: ISBN, VIN, ISO RFID identifiers for animals
- Government systems: SSN, passport numbers
- Institutional systems: student IDs, employee numbers
- Lab systems: animal IDs printed on ear tags, sample IDs on barcoded vials

Even when an identifier is *generated* by the database or a management
system, it functions as a natural key as soon as it is printed on a label
and used in the real world to refer to the entity.

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

### Surrogate keys

A **surrogate key** is an identifier used *only inside* the database. Users
do not see or reference it. Surrogate keys are appropriate for:

- Entities with no physical counterpart (internal records, system events).
- Privacy-sensitive contexts where natural identifiers should not be stored.
- Internal references that never leave the system.

Surrogate keys do not require an external identification system precisely
because they are never used to match physical entities to records. The
database still enforces their uniqueness, but the "real-world process" half
of entity integrity does not apply.

```python
@schema
class InternalRecord(dj.Manual):
    definition = """
    record_id : uuid    # internal identifier
    ---
    created_timestamp : datetime(3)
    data : <blob>
    """
```

Prefer natural keys when a stable, meaningful identifier exists; use
surrogates when no natural identifier is available or when privacy requires
it.

## Composite keys

When no single attribute uniquely identifies an entity within a table,
combine multiple attributes. Composite keys most often arise from inheriting
foreign keys: a child entity is identified within the context of its parent.

```python
@schema
class Recording(dj.Manual):
    definition = """
    -> Session
    recording_idx : int32   # recording number within session
    ---
    duration : float32       # seconds
    """
```

Here `(subject_id, session_idx, recording_idx)` together form the primary
key. Neither attribute alone would identify a recording across the table.

## Foreign keys

A foreign key serves two distinct purposes in DataJoint:

1. **Referential integrity.** The referenced entity must exist.
2. **Workflow dependency.** This entity depends on another in the pipeline
   DAG.

```python
@schema
class Segmentation(dj.Computed):
    definition = """
    -> Scan
    ---
    n_cells : int64
    """
```

The arrow `->` inherits the primary key of `Scan` into `Segmentation`,
establishes the foreign-key constraint, and declares the workflow dependency
in a single statement.

## Schema dimensions

A **dimension** is an independent axis of variation in the data. The rule:

> **Any table that introduces a new primary-key attribute introduces a new
> dimension.**

The rule applies whether the table has only new attributes or also inherits
attributes through foreign keys. A new primary-key attribute means a new
dimension.

### Tables that introduce dimensions

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)   # NEW dimension: subject_id
    ---
    species : varchar(50)
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject                 # inherits subject_id
    session_idx : int32        # NEW dimension: session_idx
    ---
    session_date : date
    """

@schema
class Trial(dj.Manual):
    definition = """
    -> Session                 # inherits subject_id, session_idx
    trial_idx : int32          # NEW dimension: trial_idx
    ---
    outcome : enum('success', 'fail')
    """
```

All three tables introduce dimensions:

- `Subject` introduces `subject_id`
- `Session` introduces `session_idx` (and inherits `subject_id`)
- `Trial` introduces `trial_idx` (and inherits both)

In schema diagrams, tables that introduce at least one new dimension have
**underlined names**.

### Tables that don't introduce dimensions

When the entire primary key comes from foreign keys, the table extends an
existing dimension rather than introducing a new one:

```python
@schema
class SubjectProfile(dj.Manual):
    definition = """
    -> Subject                 # PK = (subject_id) only
    ---
    weight : float32
    """
```

`SubjectProfile` represents a one-to-one extension of `Subject` — exactly
one profile per subject. In schema diagrams, such tables have
**non-underlined names**.

### Computed tables never introduce dimensions

A `Computed` table's primary key is fully inherited from its dependencies.
New entity types are introduced by Manual or Lookup tables, not by
computation:

```python
@schema
class SessionSummary(dj.Computed):
    definition = """
    -> Session                 # PK = (subject_id, session_idx)
    ---
    num_trials : int64
    accuracy : float32
    """
```

### Part tables CAN introduce dimensions

Unlike Computed master tables, part tables can introduce new dimensions
when a single computation produces multiple related results:

```python
@schema
class Detection(dj.Computed):
    definition = """
    -> Image
    -> DetectionParams
    ---
    num_blobs : int64
    """

    class Blob(dj.Part):
        definition = """
        -> master              # inherits (image_id, params_id)
        blob_idx : int32       # NEW dimension within detection
        ---
        x : float32
        y : float32
        """
```

`Detection` inherits its dimensions; `Detection.Blob` introduces `blob_idx`
to identify individual blobs within each detection.

### Dimensions and attribute lineage

Every foreign-key attribute traces back to the dimension where it was first
defined. This trace is called **attribute lineage**:

```
Subject.subject_id      → myschema.subject.subject_id (origin)
Session.subject_id      → myschema.subject.subject_id (inherited via FK)
Session.session_idx     → myschema.session.session_idx (origin)
Trial.subject_id        → myschema.subject.subject_id (inherited via FK)
Trial.session_idx       → myschema.session.session_idx (inherited via FK)
Trial.trial_idx         → myschema.trial.trial_idx (origin)
```

Lineage enables **semantic matching** — DataJoint joins attributes only
when they trace back to the same dimension. Two `id` attributes from
different dimensions cannot be accidentally joined.

See [Semantic Matching](semantic-matching.md) for the full mechanism.

### Recognizing dimensions in diagrams

| Visual | Meaning |
|--------|---------|
| **Underlined table name** | Introduces at least one new dimension |
| Non-underlined table name | All PK attributes inherited (no new dimensions) |
| **Thick solid line** | One-to-one extension (no new dimension) |
| Thin solid line | Containment (may introduce a dimension) |

## Partial entity integrity

Some applications need only one direction of the 1:1 mapping:

- **Record → entity (uniqueness only).** Each record corresponds to at most
  one entity, but an entity may have multiple records.
- **Entity → record (completeness only).** Each entity has a record, but
  records may be shared.

A social platform might ensure each account ties to at most one person
(record→entity) without preventing one person from creating multiple
accounts (entity→record not enforced). Design the primary key to match the
actual requirement — full bidirectional integrity is sometimes more than
the application needs.

## When no natural key exists

When no external identifier exists and no real-world mechanism maintains
the entity-to-record association, full entity integrity is still possible
through a multi-step identification process:

1. Generate a unique token at the time of first contact.
2. Deliver the token to the entity (email, printed card, RFID badge).
3. Require the token for all subsequent interactions.
4. Trust the external process to maintain the association.

The token then functions as a natural key — as long as the external process
reliably maintains it. The database enforces uniqueness; the process
enforces the entity-to-token binding.

## What the database can and cannot do

| The database CAN | The database CANNOT |
|---|---|
| Enforce that no two records share a primary key | Verify that a record represents the intended real-world entity |
| Reject inserts that violate foreign-key constraints | Prevent one entity from having two records (without an external mechanism) |
| Cascade deletes through workflow dependencies | Create real-world identifiers — only mirror and enforce them |

Entity integrity for real-world entities **always requires some external
identification process** alongside the database constraints — whether it is
ear tags on mice, ID cards for students, barcodes on samples, or a
token-issuance protocol for anonymous respondents.

## Best practices

1. **Answer the three questions** before designing any table.
2. **Choose stable identifiers** that will not need to change.
3. **Keep keys minimal** — include only what is necessary for uniqueness.
4. **Document key semantics** — explain what the key represents in the
   real world.
5. **Match the application's actual integrity requirement** — full,
   partial, or token-based.

## Common mistakes

### Too few key attributes

```python
# Wrong: experiment_id alone isn't unique
class Trial(dj.Manual):
    definition = """
    experiment_id : int64
    ---
    trial_number : int32   # Should be part of the key!
    result : float32
    """
```

### Too many key attributes

```python
# Wrong: timestamp makes every row unique, losing entity semantics
class Measurement(dj.Manual):
    definition = """
    subject_id : int64
    timestamp : datetime(6)   # Microsecond precision destroys entity identity
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

Entity integrity is the bidirectional one-to-one correspondence between
real-world entities and their database records. It rests on **two required
components**: a real-world identification process that creates the
association, and a database uniqueness constraint that enforces it. Neither
component alone is enough.

The three questions — *how do I prevent duplicates, prevent record sharing,
and match entities to records?* — operationalize this definition. The
primary key, declared above the `---` separator and supplied explicitly at
insertion, is the database's half of the answer. The real-world process is
yours to design.

## See also

- [Normalization](normalization.md) — entity normalization and the workflow
  test
- [Computation Model](computation-model.md) — how cascade deletes and
  populate preserve integrity through the pipeline
- [Semantic Matching](semantic-matching.md) — joins resolved by attribute
  lineage through schema dimensions
- [Relational Workflow Model](relational-workflow-model.md) — the
  conceptual frame in which entity integrity is one of several integrity
  guarantees
