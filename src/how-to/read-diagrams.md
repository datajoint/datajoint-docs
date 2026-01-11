# Read Schema Diagrams

DataJoint diagrams visualize schema structure as directed acyclic graphs (DAGs).
Tables are nodes; foreign keys are edges flowing from parent to child.

## Quick Reference

| Line Style | Appearance | Relationship | Child's Primary Key |
|------------|------------|--------------|---------------------|
| **Thick Solid** | ━━━ | Extension | Parent PK only |
| **Thin Solid** | ─── | Containment | Parent PK + own field(s) |
| **Dashed** | ┄┄┄ | Reference | Own independent PK |

**Key principle:** Solid lines mean the parent's identity becomes part of the
child's identity. Dashed lines mean the child maintains independent identity.

## Line Styles

### Thick Solid: Extension (One-to-One)

The foreign key **is** the entire primary key of the child.

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_date : date
    ---
    notes : varchar(1000)
    """

@schema
class SessionQC(dj.Computed):
    definition = """
    -> Session              # FK is entire PK
    ---
    passed : bool
    """
```

**Semantics:** The child extends or specializes the parent. At most one child
exists per parent.

**Use cases:** Workflow sequences, optional extensions, computed summaries.

### Thin Solid: Containment (One-to-Many)

The foreign key is **part of** (but not all of) the child's primary key.

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_date : date
    ---
    notes : varchar(1000)
    """

@schema
class Trial(dj.Manual):
    definition = """
    -> Session              # Part of PK
    trial_idx : uint16      # Additional PK component
    ---
    outcome : varchar(20)
    """
```

**Semantics:** The child belongs to or is contained within the parent. Multiple
children can exist per parent.

**Use cases:** Hierarchies (Subject → Session → Trial), ownership, containment.

### Dashed: Reference (One-to-Many)

The foreign key is a **secondary attribute** (below the `---` line).

```python
@schema
class Experimenter(dj.Manual):
    definition = """
    experimenter_id : uuid
    ---
    name : varchar(100)
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_date : date
    ---
    -> Experimenter         # Secondary attribute
    notes : varchar(1000)
    """
```

**Semantics:** The child references the parent but maintains independent
identity. The parent is just one attribute describing the child.

**Use cases:** Loose associations, references that might change, lookup
references.

## Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| **Underlined name** | Independent entity introducing a new schema dimension |
| Non-underlined name | Dependent entity whose identity derives from parent(s) |
| **Green** | Manual table |
| **Gray** | Lookup table |
| **Red** | Computed table |
| **Blue** | Imported table |
| **Orange dots** | Renamed foreign keys (via `.proj()`) |

## What Diagrams Don't Show

Diagrams do NOT reflect these foreign key modifiers:

- `[nullable]` — Optional references
- `[unique]` — One-to-one constraints on secondary FKs

A dashed line could represent any of:

- Required one-to-many (default)
- Optional one-to-many (`[nullable]`)
- Required one-to-one (`[unique]`)
- Optional one-to-one (`[nullable, unique]`)

**Always check the table definition** to determine if modifiers are applied.

## Diagram Operations

Filter and combine diagrams to explore large schemas:

```python
# Entire schema
dj.Diagram(schema)

# Specific tables
dj.Diagram(Table1) + dj.Diagram(Table2)

# Table and N levels of upstream dependencies
dj.Diagram(Table) - N

# Table and N levels of downstream dependents
dj.Diagram(Table) + N

# Combine operations
(dj.Diagram(Table1) - 2) + (dj.Diagram(Table2) + 1)

# Intersection: common nodes between two diagrams
dj.Diagram(Table1) * dj.Diagram(Table2)
```

### Finding Paths Between Tables

Use intersection to find connection paths in large schemas:

```python
# Find all paths from upstream_table to downstream_table
(dj.Diagram(upstream_table) + 100) * (dj.Diagram(downstream_table) - 100)
```

This works because:

- `+ 100` expands downstream from the first table
- `- 100` expands upstream from the second table
- `*` shows only tables in both — the connecting path(s)

## Many-to-Many Patterns

Many-to-many relationships appear as tables with converging solid lines:

```python
@schema
class Student(dj.Manual):
    definition = """
    student_id : uint32
    ---
    name : varchar(60)
    """

@schema
class Course(dj.Manual):
    definition = """
    course_code : char(8)
    ---
    title : varchar(100)
    """

@schema
class Enrollment(dj.Manual):
    definition = """
    -> Student              # Solid line from Student
    -> Course               # Solid line from Course
    ---
    grade : enum('A','B','C','D','F')
    """
```

The diagram shows two thin solid lines converging into `Enrollment`, indicating
a many-to-many relationship between `Student` and `Course`.

## Renamed Foreign Keys

When referencing the same table multiple times, use `.proj()` to rename:

```python
@schema
class Neuron(dj.Manual):
    definition = """
    neuron_id : uint32
    ---
    cell_type : varchar(30)
    """

@schema
class Synapse(dj.Manual):
    definition = """
    synapse_id : uint32
    ---
    -> Neuron.proj(pre='neuron_id')
    -> Neuron.proj(post='neuron_id')
    strength : float32
    """
```

**Orange dots** appear on connections where projections renamed attributes.
Hover over them in Jupyter to see the projection expression.

## Diagrams and Queries

Diagram structure informs query patterns:

**Solid line paths enable direct joins:**

```python
# If Subject → Session → Trial are connected by solid lines:
Subject * Trial  # Valid — PKs cascade through solid lines
```

**Dashed lines require intermediate tables:**

```python
# If Experimenter ---> Session (dashed), Session → Trial (solid):
Experimenter * Session * Trial  # Must include Session
```

## Comparison to Other Notations

| Feature | Chen's ER | Crow's Foot | DataJoint |
|---------|-----------|-------------|-----------|
| Cardinality | Numbers | Line symbols | Line style |
| Direction | None | None | Top-to-bottom |
| Cycles | Allowed | Allowed | Not allowed |
| PK cascade | Not shown | Not shown | Solid lines |

DataJoint diagrams are **executable specifications** — the diagram is generated
from the actual schema and cannot drift out of sync.
