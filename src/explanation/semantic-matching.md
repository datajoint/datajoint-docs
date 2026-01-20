# Semantic Matching

Semantic matching ensures that attributes are only matched in joins when they share both the same name and the same **lineage** (origin). This prevents accidental joins on unrelated attributes that happen to share names.

## Relationship to Natural Joins

DataJoint's join operator (`*`) performs a **natural join**—the standard relational operation that matches tuples on all common attribute names. If you're familiar with SQL's `NATURAL JOIN` or relational algebra, DataJoint's join works the same way.

**Semantic matching adds a safety check** on top of the natural join. Before performing the join, DataJoint verifies that all common attributes (namesakes) actually represent the same thing by checking their lineage. If two attributes share a name but have different origins, the join is rejected rather than silently producing incorrect results.

In other words: **semantic matching is a natural join that rejects common pitfalls of joining on unrelated attributes.**

Two attributes are **homologous** if they share the same lineage—that is, they trace back to the same original definition. Attributes with the same name are called **namesakes**. Semantic matching requires that all namesakes be homologous.

### All Binary Operators Use Semantic Matching

Semantic matching applies to **all binary operators** that combine two query expressions, not just join:

| Operator | Syntax | Semantic Check |
|----------|--------|----------------|
| Join | `A * B` | Namesakes must be homologous |
| Restriction | `A & B` | Namesakes must be homologous |
| Anti-restriction | `A - B` | Namesakes must be homologous |
| Aggregation | `A.aggr(B, ...)` | Namesakes must be homologous |
| Extension | `A.extend(B)` | Namesakes must be homologous |
| Union | `A + B` | Namesakes must be homologous |

In each case, DataJoint verifies that any common attribute names between the two operands share the same lineage before proceeding with the operation.

These concepts were first introduced in Yatsenko et al., 2018[^1].

[^1]: Yatsenko D, Walker EY, Tolias AS (2018). DataJoint: A Simpler Relational Data Model. [arXiv:1807.11104](https://doi.org/10.48550/arXiv.1807.11104)

## Why Semantic Matching?

The natural join is elegant and powerful, but it has a well-known weakness: it relies entirely on naming conventions. If two tables happen to have columns with the same name but different meanings, a natural join silently produces a Cartesian product filtered on unrelated values—a subtle bug that can go undetected.

```python
# Classic natural join pitfall
class Student(dj.Manual):
    definition = """
    id : int64  # student ID
    ---
    name : varchar(100)
    """

class Course(dj.Manual):
    definition = """
    id : int64  # course ID
    ---
    title : varchar(100)
    """

# Natural join would match on 'id', but these are unrelated!
# Student #5 paired with Course #5 is meaningless.
```

DataJoint's semantic matching solves this by tracking the **lineage** of each attribute—where it was originally defined. Attributes only match if they have the same lineage, ensuring that joins always combine semantically related data.

## Attribute Lineage

Lineage identifies the **origin** of an attribute—the **dimension** where it was first defined. A dimension is an independent axis of variation introduced by a table that defines new primary key attributes. See [Schema Dimensions](entity-integrity.md#schema-dimensions) for details.

Lineage is represented as a string:

```
schema_name.table_name.attribute_name
```

### Lineage Assignment Rules

| Attribute Type | Lineage Value |
|----------------|---------------|
| Native primary key | `this_schema.this_table.attr_name` |
| FK-inherited (primary or secondary) | Traced to original definition |
| Native secondary | `None` |
| Computed (in projection) | `None` |

### Example

```python
class Session(dj.Manual):         # table: session
    definition = """
    session_id : int64
    ---
    session_date : date
    """

class Trial(dj.Manual):           # table: trial
    definition = """
    -> Session
    trial_num : int32
    ---
    stimulus : varchar(100)
    """
```

Lineages:

- `Session.session_id` → `myschema.session.session_id` (native PK)
- `Session.session_date` → `None` (native secondary)
- `Trial.session_id` → `myschema.session.session_id` (inherited via FK)
- `Trial.trial_num` → `myschema.trial.trial_num` (native PK)
- `Trial.stimulus` → `None` (native secondary)

Notice that `Trial.session_id` has the same lineage as `Session.session_id` because it was inherited through the foreign key reference. This allows `Session * Trial` to work correctly—both `session_id` attributes are **homologous**.

## Terminology

| Term | Definition |
|------|------------|
| **Lineage** | The origin of an attribute: `schema.table.attribute` |
| **Homologous attributes** | Attributes with the same lineage |
| **Namesake attributes** | Attributes with the same name |
| **Homologous namesakes** | Same name AND same lineage — used for join matching |
| **Non-homologous namesakes** | Same name BUT different lineage — cause join errors |

## Semantic Matching Rules

When two expressions are joined, DataJoint checks all namesake attributes (attributes with the same name):

| Scenario | Action |
|----------|--------|
| Same name, same lineage (both non-null) | **Match** — attributes are joined |
| Same name, different lineage | **Error** — non-homologous namesakes |
| Same name, either lineage is null | **Error** — cannot verify homology |
| Different names | **No match** — attributes kept separate |

## When Semantic Matching Fails

If you see an error like:

```
DataJointError: Cannot join on attribute `id`: different lineages
(university.student.id vs university.course.id).
Use .proj() to rename one of the attributes.
```

This means you're trying to join tables that have a namesake attribute (`id`) with different lineages. The solutions are:

1. **Rename one attribute** using projection:
   ```python
   Student() * Course().proj(course_id='id')
   ```

2. **Bypass semantic checking** (use with caution):
   ```python
   Student().join(Course(), semantic_check=False)
   ```

3. **Use descriptive names** in your schema design (best practice):
   ```python
   class Student(dj.Manual):
       definition = """
       student_id : int64  # not just 'id'
       ---
       name : varchar(100)
       """
   ```

## Examples

### Valid Join (Shared Lineage)

```python
class Student(dj.Manual):
    definition = """
    student_id : int64
    ---
    name : varchar(100)
    """

class Enrollment(dj.Manual):
    definition = """
    -> Student
    -> Course
    ---
    grade : varchar(2)
    """

# Works: student_id has same lineage in both
Student() * Enrollment()
```

### Multi-hop FK Inheritance

Lineage is preserved through multiple levels of foreign key inheritance:

```python
class Session(dj.Manual):
    definition = """
    session_id : int64
    ---
    session_date : date
    """

class Trial(dj.Manual):
    definition = """
    -> Session
    trial_num : int32
    """

class Response(dj.Computed):
    definition = """
    -> Trial
    ---
    response_time : float64
    """

# All work: session_id traces back to Session in all tables
Session() * Trial()
Session() * Response()
Trial() * Response()
```

### Secondary FK Attribute

Lineage works for secondary (non-primary-key) foreign key attributes too:

```python
class Course(dj.Manual):
    definition = """
    course_id : int unsigned
    ---
    title : varchar(100)
    """

class FavoriteCourse(dj.Manual):
    definition = """
    student_id : int unsigned
    ---
    -> Course
    """

class RequiredCourse(dj.Manual):
    definition = """
    major_id : int unsigned
    ---
    -> Course
    """

# Works: course_id is secondary in both, but has same lineage
FavoriteCourse() * RequiredCourse()
```

### Aliased Foreign Key

When you alias a foreign key, the new name gets the same lineage as the original:

```python
class Person(dj.Manual):
    definition = """
    person_id : int unsigned
    ---
    full_name : varchar(100)
    """

class Marriage(dj.Manual):
    definition = """
    -> Person.proj(husband='person_id')
    -> Person.proj(wife='person_id')
    ---
    marriage_date : date
    """

# husband and wife both have lineage: schema.person.person_id
# They are homologous (same lineage) but have different names
```

## Best Practices

1. **Use descriptive attribute names**: Prefer `student_id` over generic `id`

2. **Leverage foreign keys**: Inherited attributes maintain lineage automatically

3. **Rebuild lineage for legacy schemas**: Run `schema.rebuild_lineage()` once

4. **Rebuild upstream schemas first**: For cross-schema FKs, rebuild parent schemas before child schemas

5. **Restart after rebuilding**: Restart Python kernel to pick up new lineage information

6. **Use `semantic_check=False` sparingly**: Only when you're certain the natural join is correct

## Design Rationale

Semantic matching reflects a core DataJoint principle: **schema design should encode meaning**. When you create a foreign key reference, you're declaring that two attributes represent the same concept. DataJoint tracks this through lineage, allowing safe joins without relying on naming conventions alone.

This is especially valuable in large, collaborative projects where different teams might independently choose similar attribute names for unrelated concepts.
