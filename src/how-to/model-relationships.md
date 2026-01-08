# Model Relationships

Define foreign key relationships between tables.

## Basic Foreign Key

Reference another table with `->`:

```python
@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    species : varchar(32)
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : uint16
    ---
    session_date : date
    """
```

The `->` syntax:

- Inherits all primary key attributes from the referenced table
- Creates a foreign key constraint
- Establishes dependency for cascading deletes
- Defines workflow order (parent must exist before child)

## Foreign Key Placement

Where you place a foreign key determines the relationship type:

| Placement | Relationship | Diagram Line |
|-----------|--------------|--------------|
| Entire primary key | One-to-one extension | Thick solid |
| Part of primary key | One-to-many containment | Thin solid |
| Secondary attribute | One-to-many reference | Dashed |

## One-to-Many: Containment

Foreign key as part of the primary key (above `---`):

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject              # Part of primary key
    session_idx : uint16    # Additional PK attribute
    ---
    session_date : date
    """
```

Sessions are identified **within** their subject. Session #1 for Subject A is different from Session #1 for Subject B.

## One-to-Many: Reference

Foreign key as secondary attribute (below `---`):

```python
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uuid     # Independent identity
    ---
    -> Equipment            # Reference, not part of identity
    duration : float32
    """
```

Recordings have their own global identity independent of equipment.

## One-to-One: Extension

Foreign key is the entire primary key:

```python
@schema
class SubjectDetails(dj.Manual):
    definition = """
    -> Subject              # Entire primary key
    ---
    weight : float32
    notes : varchar(1000)
    """
```

Each subject has at most one details record. The tables share identity.

## Optional (Nullable) Foreign Keys

Make a reference optional with `[nullable]`:

```python
@schema
class Trial(dj.Manual):
    definition = """
    -> Session
    trial_idx : uint16
    ---
    -> [nullable] Stimulus   # Some trials have no stimulus
    outcome : enum('hit', 'miss')
    """
```

Only secondary foreign keys (below `---`) can be nullable.

## Unique Foreign Keys

Enforce one-to-one with `[unique]`:

```python
@schema
class ParkingSpot(dj.Manual):
    definition = """
    spot_id : uint32
    ---
    -> [unique] Employee     # Each employee has at most one spot
    location : varchar(30)
    """
```

## Many-to-Many

Use an association table with composite primary key:

```python
@schema
class Assignment(dj.Manual):
    definition = """
    -> Subject
    -> Protocol
    ---
    assigned_date : date
    """
```

Each subject-protocol combination appears at most once.

## Hierarchies

Cascading one-to-many relationships create tree structures:

```python
@schema
class Study(dj.Manual):
    definition = """
    study : varchar(8)
    ---
    investigator : varchar(60)
    """

@schema
class Subject(dj.Manual):
    definition = """
    -> Study
    subject_id : varchar(12)
    ---
    species : varchar(32)
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : uint16
    ---
    session_date : date
    """
```

Primary keys cascade: Session's key is `(study, subject_id, session_idx)`.

## Part Tables

Part tables have an implicit foreign key to their master:

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : uint16
    ---
    session_date : date
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_idx : uint16
        ---
        outcome : enum('hit', 'miss')
        """
```

`-> master` references the enclosing table's primary key.

## Renamed Foreign Keys

Reference the same table multiple times with renamed attributes:

```python
@schema
class Comparison(dj.Manual):
    definition = """
    -> Session.proj(session_a='session_idx')
    -> Session.proj(session_b='session_idx')
    ---
    similarity : float32
    """
```

## Computed Dependencies

Computed tables inherit keys from their dependencies:

```python
@schema
class ProcessedData(dj.Computed):
    definition = """
    -> RawData
    ---
    result : float64
    """

    def make(self, key):
        data = (RawData & key).fetch1('data')
        self.insert1({**key, 'result': process(data)})
```

## Schema as DAG

DataJoint schemas form a directed acyclic graph (DAG). Foreign keys:

- Define data relationships
- Prescribe workflow execution order
- Enable cascading deletes

There are no cyclic dependencies—parent tables must always be populated before their children.

## See Also

- [Define Tables](define-tables.md) — Table definition syntax
- [Design Primary Keys](design-primary-keys.md) — Key selection strategies
- [Delete Data](delete-data.md) — Cascade behavior
