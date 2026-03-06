# Schema Normalization

Schema normalization ensures data integrity by organizing tables to minimize
redundancy and prevent update anomalies. DataJoint's workflow-centric approach
makes normalization intuitive.

## The Workflow Normalization Principle

> **"Every table represents an entity type that is created at a specific step
> in a workflow, and all attributes describe that entity as it exists at that
> workflow step."**

This principle naturally leads to well-normalized schemas.

## The Intrinsic Attributes Principle

> **"Each entity should contain only its intrinsic attributes—properties that are inherent to the entity itself. Relationships, assignments, and events that happen over time belong in separate tables."**

**Full workflow entity normalization** is achieved when:

1. Each row represents a single, well-defined entity
2. Each entity is entered once when first tracked
3. Events that happen at later stages belong in separate tables

## Why Normalization Matters

Without normalization, databases suffer from:

- **Redundancy** — Same information stored multiple times
- **Update anomalies** — Changes require updating multiple rows
- **Insertion anomalies** — Can't add data without unrelated data
- **Deletion anomalies** — Deleting data loses unrelated information

## DataJoint's Approach

Traditional normalization analyzes **functional dependencies** to determine
table structure. DataJoint takes a different approach: design tables around
**workflow steps**.

### Example: Mouse Housing

**Problem: Cage is not intrinsic to a mouse.** A mouse's cage can change over time. The cage assignment is an **event** that happens after the mouse is first tracked.

**Denormalized (problematic):**

```python
# Wrong: cage info repeated for every mouse
class Mouse(dj.Manual):
    definition = """
    mouse_id : int32
    ---
    cage_id : int32
    cage_location : varchar(50)    # Redundant!
    cage_temperature : float32     # Redundant!
    weight : float32
    """
```

**Partially normalized (better, but not complete):**

```python
@schema
class Cage(dj.Manual):
    definition = """
    cage_id : int32
    ---
    location : varchar(50)
    """

@schema
class Mouse(dj.Manual):
    definition = """
    mouse_id : int32
    ---
    -> Cage    # Still treats cage as static attribute
    """
```

**Fully normalized (correct):**

```python
@schema
class Cage(dj.Manual):
    definition = """
    cage_id : int32
    ---
    location : varchar(50)
    """

@schema
class Mouse(dj.Manual):
    definition = """
    mouse_id : int32
    ---
    date_of_birth : date
    sex : enum('M', 'F')
    # Note: NO cage reference here!
    # Cage is not intrinsic to the mouse
    """

@schema
class CageAssignment(dj.Manual):
    definition = """
    -> Mouse
    assignment_date : date
    ---
    -> Cage
    removal_date=null : date
    """

@schema
class MouseWeight(dj.Manual):
    definition = """
    -> Mouse
    weigh_date : date
    ---
    weight : float32
    """
```

This fully normalized design:

- **Intrinsic attributes only** — `Mouse` contains only attributes determined at creation (birth date, sex)
- **Cage assignment as event** — `CageAssignment` tracks the temporal relationship between mice and cages
- **Single entity per row** — Each mouse is entered once when first tracked
- **Later events separate** — Cage assignments, weight measurements happen after initial tracking
- **History preserved** — Can track cage moves over time without data loss

## The Workflow Test

Ask these questions to determine table structure:

### 1. "Is this an intrinsic attribute of the entity?"

An intrinsic attribute is inherent to the entity itself and determined when the entity is first created.

- **Intrinsic:** Mouse's date of birth, sex, genetic strain
- **Not intrinsic:** Mouse's cage (assignment that changes), weight (temporal measurement)

If not intrinsic → separate table for the relationship or event

### 2. "At which workflow step is this attribute determined?"

- If an attribute is determined at a **different step**, it belongs in a **different table**
- If an attribute **changes over time**, it needs its own table with a **temporal key**

### 3. "Is this a relationship or event?"

- **Relationships** (cage assignment, group membership) → association table with temporal keys
- **Events** (measurements, observations) → separate table with event date/time
- **States** (approval status, processing stage) → state transition table

## Common Patterns

### Lookup Tables

Store reference data that doesn't change:

```python
@schema
class Species(dj.Lookup):
    definition = """
    species : varchar(50)
    ---
    common_name : varchar(100)
    """
    contents = [
        ('Mus musculus', 'House mouse'),
        ('Rattus norvegicus', 'Brown rat'),
    ]
```

### Parameter Sets

Store versioned configurations:

```python
@schema
class AnalysisParams(dj.Lookup):
    definition = """
    params_id : int32
    ---
    threshold : float32
    window_size : int32
    """
```

### Temporal Tracking

Track measurements or observations over time:

```python
@schema
class SubjectWeight(dj.Manual):
    definition = """
    -> Subject
    weight_date : date
    ---
    weight : float32   # grams
    """
```

### Temporal Associations

Track relationships or assignments that change over time:

```python
@schema
class GroupAssignment(dj.Manual):
    definition = """
    -> Subject
    assignment_date : date
    ---
    -> ExperimentalGroup
    removal_date=null : date
    """

@schema
class HousingAssignment(dj.Manual):
    definition = """
    -> Animal
    move_date : date
    ---
    -> Cage
    move_reason : varchar(200)
    """
```

**Key pattern:** The relationship itself (subject-to-group, animal-to-cage) is **not intrinsic** to either entity. It's a temporal event that happens during the workflow.

## Benefits in DataJoint

1. **Natural from workflow thinking** — Designing around workflow steps
   naturally produces normalized schemas

2. **Cascade deletes** — Normalization + foreign keys enable safe cascade
   deletes that maintain consistency

3. **Join efficiency** — Normalized tables with proper keys enable efficient
   joins through the workflow graph

4. **Clear provenance** — Each table represents a distinct workflow step,
   making data lineage clear

## Summary

**Core principles:**

1. **Intrinsic attributes only** — Each entity contains only properties inherent to itself
2. **One entity, one entry** — Each entity entered once when first tracked
3. **Events separate** — Relationships, assignments, measurements that happen later belong in separate tables
4. **Workflow steps** — Design tables around the workflow step that creates each entity
5. **Temporal keys** — Relationships and observations that change over time need temporal keys (dates, timestamps)

**Ask yourself:**

- Is this attribute intrinsic to the entity? (No → separate table)
- Does this attribute change over time? (Yes → temporal table)
- Is this a relationship or event? (Yes → association/event table)

Following these principles achieves **full workflow entity normalization** where each table represents a single, well-defined entity type entered at a specific workflow step.
