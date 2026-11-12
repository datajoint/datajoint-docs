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
| Union | `A + B` | Same primary key; no secondary attribute in common |

In each case except union, DataJoint verifies that any common attribute names between the two operands share the same lineage before proceeding with the operation. Union matches the operands' primary keys by name and refuses any secondary attribute they have in common.

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

Lineage follows foreign keys. A table's native primary-key attributes start a lineage, and each foreign key passes it on to the referencing table. Any other attribute has no lineage: a native secondary attribute, an attribute computed in a projection, or a key that `dj.U` promotes from a secondary attribute.

| Attribute Type | Lineage Value |
|----------------|---------------|
| Native primary key | `this_schema.this_table.attr_name` |
| FK-inherited (primary or secondary) | Traced to original definition |
| Native secondary | `None` |
| Computed (in projection) | `None` |
| Promoted to a key by `dj.U` | `None` |

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
| Same name, no lineage on either side | **Error** — unrelated namesakes: that side does not inherit the attribute through a foreign key |
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

### Joining on unrelated namesakes

!!! version-changed "Changed in 2.4"
    Before 2.4, this case reported a missing `~lineage` entry and suggested `schema.rebuild_lineage()`, which cannot change the outcome ([#1640](https://github.com/datajoint/datajoint-python/issues/1640)).

Two tables can each declare a secondary attribute with the same name:

```python
@schema
class Segmentation(dj.Manual):
    definition = """
    -> Image
    ---
    input_hash : varchar(64)
    cell_count : int32
    """

@schema
class Profile(dj.Manual):
    definition = """
    -> Image
    ---
    input_hash : varchar(64)
    mean_area : float32
    """

Segmentation * Profile
```

```
DataJointError: Cannot join on attribute `input_hash`: neither side inherits it
through a foreign key, so the two are unrelated. Use .proj() to rename or exclude
it on one side.
```

No foreign key relates the two `input_hash` attributes, so they have no lineage, and DataJoint does not join on them. The same applies to attributes computed in two projections, and to keys that `dj.U` promotes on both sides. Rename or exclude the attribute on one side:

```python
Segmentation * Profile.proj("mean_area")                                # exclude input_hash
Segmentation * Profile.proj("mean_area", profile_hash="input_hash")    # keep it under another name
```

When only one side has no lineage, the message says which lineage the other side traces it to.

## The `~lineage` table

Lineage is stored per-schema in a hidden table called `~lineage`. DataJoint writes one row per `(table, attribute)` pair recording the lineage string for that attribute, and consults `~lineage` whenever it needs to compare lineages across query expressions.

`~lineage` is maintained as part of normal table declaration:

- Declaring a new table inserts its lineage rows as the last step of `Table.declare()`.
- When `@schema(MyTable)` runs on an already-declared table, DataJoint checks the heading's loaded lineage values for the symptom of missing rows — any primary-key attribute with `lineage=None`. The check is in memory, against values already loaded when the heading was constructed, so a healthy schema pays zero additional database queries on re-decoration. If the check fires, DataJoint refreshes the table's `~lineage` rows from the current foreign-key definition. *(New in DataJoint 2.3.)*

This automatic check addresses the load-bearing failure mode: a partial declare or an upgrade that left some rows missing entirely. **It does not auto-heal stale-but-non-None entries** (e.g. older DataJoint versions that wrote lineage strings in a slightly different format). Those still require a manual rebuild — see below.

### Manual lineage rebuild

When the in-memory check is not enough — stale rows that exist but carry the wrong value, schemas whose tables have not been re-decorated under DataJoint 2.3+, or schemas in `create_tables=False` production mode — call `schema.rebuild_lineage()` or the equivalent migration helper:

```python
import datajoint as dj
from datajoint import migrate

schema = dj.Schema("my_schema")

# Option 1: instance method
schema.rebuild_lineage()

# Option 2: migration helper with dry-run preview
migrate.rebuild_lineage(schema, dry_run=True)   # show what would change
migrate.rebuild_lineage(schema, dry_run=False)  # apply
```

`rebuild_lineage()` is safe to run on a healthy schema — it's idempotent and produces the same end state regardless of starting condition.

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

### Renamed Foreign Key

When you rename a foreign key, the new name gets the same lineage as the original:

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
