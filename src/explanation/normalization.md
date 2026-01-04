# Schema Normalization

Schema normalization ensures data integrity by organizing tables to minimize
redundancy and prevent update anomalies. DataJoint's workflow-centric approach
makes normalization intuitive.

## The Workflow Normalization Principle

> **"Every table represents an entity type that is created at a specific step
> in a workflow, and all attributes describe that entity as it exists at that
> workflow step."**

This principle naturally leads to well-normalized schemas.

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

**Denormalized (problematic):**

```python
# Wrong: cage info repeated for every mouse
class Mouse(dj.Manual):
    definition = """
    mouse_id : int
    ---
    cage_id : int
    cage_location : varchar(50)    # Redundant!
    cage_temperature : float       # Redundant!
    weight : float
    """
```

**Normalized (correct):**

```python
@schema
class Cage(dj.Manual):
    definition = """
    cage_id : int
    ---
    location : varchar(50)
    temperature : float
    """

@schema
class Mouse(dj.Manual):
    definition = """
    mouse_id : int
    ---
    -> Cage
    """

@schema
class MouseWeight(dj.Manual):
    definition = """
    -> Mouse
    weigh_date : date
    ---
    weight : float
    """
```

This normalized design:

- Stores cage info once (no redundancy)
- Tracks weight history (temporal dimension)
- Allows cage changes without data loss

## The Workflow Test

Ask: "At which workflow step is this attribute determined?"

- If an attribute is determined at a **different step**, it belongs in a
  **different table**
- If an attribute **changes over time**, it needs its own table with a
  **temporal key**

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
    params_id : int
    ---
    threshold : float
    window_size : int
    """
```

### Temporal Tracking

Track attributes that change over time:

```python
@schema
class SubjectWeight(dj.Manual):
    definition = """
    -> Subject
    weight_date : date
    ---
    weight : float   # grams
    """
```

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

- Normalize by designing around **workflow steps**
- Each table = one entity type at one workflow step
- Attributes belong with the step that **determines** them
- Temporal data needs **temporal keys**
