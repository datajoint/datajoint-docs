# Semantic Matching - Specification

## Overview

This document specifies **semantic matching** for binary operators in DataJoint 2.0. Semantic matching ensures that attributes are only matched when they share both the same name and the same **lineage** (origin), preventing accidental matches on unrelated attributes that happen to share names. This replaces the name-based matching rules from pre-2.0 versions.

### Goals

1. **Prevent incorrect matches** on attributes that share names but represent different entities
2. **Enable valid operations** that were previously blocked due to overly restrictive rules
3. **Maintain backward compatibility** for well-designed schemas
4. **Provide clear error messages** when semantic conflicts are detected

---

## User Guide

### Quick Start

Semantic matching is enabled by default in DataJoint 2.0. For most well-designed schemas, no changes are required.

#### When You Might See Errors

```python
# Two tables with generic 'id' attribute
class Student(dj.Manual):
    definition = """
    id : int64
    ---
    name : varchar(100)
    """

class Course(dj.Manual):
    definition = """
    id : int64
    ---
    title : varchar(100)
    """

# This will raise an error because 'id' has different lineages
Student() * Course()  # DataJointError!
```

#### How to Resolve

**Option 1: Rename attributes using projection**
```python
Student() * Course().proj(course_id='id')  # OK
```

**Option 2: Bypass semantic check (use with caution)**
```python
Student().join(Course(), semantic_check=False)  # OK, but be careful!
```

**Option 3: Use descriptive names (best practice)**
```python
class Student(dj.Manual):
    definition = """
    student_id : int64
    ---
    name : varchar(100)
    """
```

### Rebuilding Lineage for Existing Schemas

If you have existing schemas created before DataJoint 2.0, rebuild their lineage tables:

```python
import datajoint as dj

# Connect and get your schema
schema = dj.Schema('my_database')

# Rebuild lineage (do this once per schema)
schema.rebuild_lineage()

# Restart Python kernel to pick up changes
```

**Important**: If your schema references tables in other schemas, rebuild those upstream schemas first.

---

## API Reference

### Schema Methods

#### `schema.rebuild_lineage()`

Rebuild the `~lineage` table for all tables in this schema.

```python
schema.rebuild_lineage()
```

**Description**: Recomputes lineage for all attributes by querying FK relationships from the database's `information_schema`. Use this to restore lineage for schemas that predate the lineage system or after corruption.

**Requirements**:

- Schema must exist
- Upstream schemas (referenced via cross-schema FKs) must have their lineage rebuilt first

**Side Effects**:

- Creates `~lineage` table if it doesn't exist
- Deletes and repopulates all lineage entries for tables in the schema

**Post-Action**: Restart Python kernel and reimport to pick up new lineage information.

#### `schema.lineage_table_exists`

Property indicating whether the `~lineage` table exists in this schema.

```python
if schema.lineage_table_exists:
    print("Lineage tracking is enabled")
```

**Returns**: `bool` - `True` if `~lineage` table exists, `False` otherwise.

#### `schema.lineage`

Property returning all lineage entries for the schema.

```python
schema.lineage
# {'myschema.session.session_id': 'myschema.session.session_id',
#  'myschema.trial.session_id': 'myschema.session.session_id',
#  'myschema.trial.trial_num': 'myschema.trial.trial_num'}
```

**Returns**: `dict` - Maps `'schema.table.attribute'` to its lineage origin

### Join Methods

#### `expr.join(other, semantic_check=True)`

Join two expressions with optional semantic checking.

```python
result = A.join(B)                        # semantic_check=True (default)
result = A.join(B, semantic_check=False)  # bypass semantic check
```

**Parameters**:

- `other`: Another query expression to join with
- `semantic_check` (bool): If `True` (default), raise error on non-homologous namesakes. If `False`, perform natural join without lineage checking.

**Raises**: `DataJointError` if `semantic_check=True` and namesake attributes have different lineages.

#### `expr.restrict(other, semantic_check=True)`

Restrict expression with optional semantic checking.

```python
result = A.restrict(B)                        # semantic_check=True (default)
result = A.restrict(B, semantic_check=False)  # bypass semantic check
```

**Parameters**:

- `other`: Restriction condition (expression, dict, string, etc.)
- `semantic_check` (bool): If `True` (default), raise error on non-homologous namesakes when restricting by another expression. If `False`, no lineage checking.

**Raises**: `DataJointError` if `semantic_check=True` and namesake attributes have different lineages.

### Operators

#### `A * B` (Join)

Equivalent to `A.join(B, semantic_check=True)`.

#### `A & B` (Restriction)

Equivalent to `A.restrict(B, semantic_check=True)`.

#### `A - B` (Anti-restriction)

Restriction with negation. Semantic checking applies.

To bypass semantic checking: `A.restrict(dj.Not(B), semantic_check=False)`

#### `A + B` (Union)

Union of expressions. Requires all namesake attributes to have matching lineage.

### Universal Set (`dj.U`)

#### Valid Operations

```python
dj.U('a', 'b') & A           # Restriction: promotes a, b to PK
dj.U('a', 'b').aggr(A, ...)  # Aggregation: groups by a, b
dj.U() & A                   # Distinct primary keys of A
```

#### Invalid Operations

```python
dj.U('a', 'b') - A   # DataJointError: produces infinite set
dj.U('a', 'b') * A   # DataJointError: use & instead
```

---

For conceptual background on lineage, terminology, and matching rules, see [Semantic Matching (Explanation)](../../explanation/semantic-matching.md/).

---

## Implementation Details

### `~lineage` Table

Each schema has a hidden `~lineage` table storing lineage information:

```sql
CREATE TABLE `schema_name`.`~lineage` (
    table_name VARCHAR(64) NOT NULL,
    attribute_name VARCHAR(64) NOT NULL,
    lineage VARCHAR(255) NOT NULL,
    PRIMARY KEY (table_name, attribute_name)
)
```

### Lineage Population

**At table declaration**:

1. Delete any existing lineage entries for the table
2. For FK attributes: copy lineage from parent (with warning if parent lineage missing)
3. For native PK attributes: set lineage to `schema.table.attribute`
4. Native secondary attributes: no entry (lineage = None)

**At table drop**:

- Delete all lineage entries for the table

### Missing Lineage Handling

**If `~lineage` table doesn't exist**:

- Warning issued during semantic check
- Semantic checking disabled (join proceeds as natural join)

**If parent lineage missing during declaration**:

- Warning issued
- Parent attribute used as origin
- Recommend rebuilding lineage after parent schema is fixed

### Heading's `lineage_available` Property

The `Heading` class tracks whether lineage information is available:

```python
heading.lineage_available  # True if ~lineage table exists for this schema
```

This property is:

- Set when heading is loaded from database
- Propagated through projections, joins, and other operations
- Used by `assert_join_compatibility` to decide whether to perform semantic checking

---

## Error Messages

### Non-Homologous Namesakes

```
DataJointError: Cannot join on attribute `id`: different lineages
(university.student.id vs university.course.id).
Use .proj() to rename one of the attributes.
```

### Missing Lineage Warning

```
WARNING: Semantic check disabled: ~lineage table not found.
To enable semantic matching, rebuild lineage with: schema.rebuild_lineage()
```

### Parent Lineage Missing Warning

```
WARNING: Lineage for `parent_db`.`parent_table`.`attr` not found
(parent schema's ~lineage table may be missing or incomplete).
Using it as origin. Once the parent schema's lineage is rebuilt,
run schema.rebuild_lineage() on this schema to correct the lineage.
```

