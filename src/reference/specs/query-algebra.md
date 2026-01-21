# DataJoint Query Algebra Specification

## Overview

This document specifies the query algebra in DataJoint Python. Query expressions are composable objects that represent database queries. All operators return new QueryExpression objects without modifying the original—expressions are immutable.

## 1. Query Expression Fundamentals

### 1.1 Immutability

All query expressions are immutable. Every operator creates a new expression:

```python
original = Session()
restricted = original & "session_date > '2024-01-01'"  # New object
# original is unchanged
```

### 1.2 Primary Key Preservation

Most operators preserve the primary key of their input. The exceptions are:

- **Join**: May expand or contract PK based on functional dependencies
- **U & table**: Sets PK to U's attributes

### 1.3 Lazy Evaluation

Expressions are not executed until data is fetched:

```python
expr = (Session * Trial) & "trial_type = 'test'"  # No database query yet
data = expr.to_dicts()  # Query executed here
```

---

## 2. Restriction (`&` and `-`)

### 2.1 Syntax

```python
result = expression & condition    # Select matching rows
result = expression - condition    # Select non-matching rows (anti-restriction)
result = expression.restrict(condition, semantic_check=True)
```

### 2.2 Condition Types

| Type | Example | Behavior |
|------|---------|----------|
| String | `"x > 5"` | SQL WHERE condition |
| Dict | `{"status": "active"}` | Equality on attributes |
| QueryExpression | `OtherTable` | Rows with matching keys in other table |
| List/Tuple/Set | `[cond1, cond2]` | OR of conditions |
| Boolean | `True` / `False` | No effect / empty result |
| pandas.DataFrame | `df` | OR of row conditions |
| numpy.void | `record` | Treated as dict |

### 2.3 String Conditions

SQL expressions using attribute names:

```python
Session & "session_date > '2024-01-01'"
Session & "subject_id IN (1, 2, 3)"
Session & "notes LIKE '%test%'"
Session & "(x > 0) AND (y < 100)"
```

### 2.4 Dictionary Conditions

Attribute-value equality:

```python
Session & {"subject_id": 1}
Session & {"subject_id": 1, "session_type": "training"}
```

Multiple key-value pairs are combined with AND.

### 2.5 Restriction by Query Expression

Restrict to rows with matching primary keys in another expression:

```python
# Sessions that have at least one trial
Session & Trial

# Sessions for active subjects only
Session & (Subject & "status = 'active'")
```

### 2.6 Collection Conditions (OR)

Lists, tuples, and sets create OR conditions:

```python
# Either condition matches
Session & [{"subject_id": 1}, {"subject_id": 2}]

# Equivalent to
Session & "subject_id IN (1, 2)"
```

### 2.7 Anti-Restriction

The `-` operator selects rows that do NOT match:

```python
# Sessions without any trials
Session - Trial

# Sessions not from subject 1
Session - {"subject_id": 1}
```

### 2.8 Chaining Restrictions

Sequential restrictions combine with AND:

```python
(Session & cond1) & cond2
# Equivalent to
Session & cond1 & cond2
```

### 2.9 Semantic Matching

With `semantic_check=True` (default), expression conditions match only on homologous namesakes—attributes with the same name AND same lineage.

```python
# Default: semantic matching
Session & Trial

# Disable semantic check (natural join on all namesakes)
Session.restrict(Trial, semantic_check=False)
```

### 2.10 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | Preserved: PK(result) = PK(input) |
| Attributes | Preserved: all attributes retained |
| Entity Type | Preserved |

### 2.11 Error Conditions

| Condition | Error |
|-----------|-------|
| Unknown attribute in string | `UnknownAttributeError` |
| Non-homologous namesakes | `DataJointError` (semantic mismatch) |

---

## 3. Projection (`.proj()`)

### 3.1 Syntax

```python
result = expression.proj()                          # Primary key only
result = expression.proj(...)                       # All attributes
result = expression.proj('attr1', 'attr2')          # PK + specified
result = expression.proj(..., '-secret')            # All except secret
result = expression.proj(new_name='old_name')       # Rename
result = expression.proj(computed='x + y')          # Computed attribute
```

### 3.2 Attribute Selection

| Syntax | Meaning |
|--------|---------|
| `'attr'` | Include attribute |
| `...` (Ellipsis) | Include all secondary attributes |
| `'-attr'` | Exclude attribute (use with `...`) |

Primary key attributes are always included, even if not specified.

### 3.3 Renaming Attributes

```python
# Rename 'name' to 'subject_name'
Subject.proj(subject_name='name')

# Duplicate attribute with new name (parentheses preserve original)
Subject.proj('name', subject_name='(name)')
```

### 3.4 Computed Attributes

Create new attributes from SQL expressions:

```python
# Arithmetic
Trial.proj(speed='distance / duration')

# Functions
Session.proj(year='YEAR(session_date)')

# Aggregation-like (per row)
Trial.proj(centered='value - mean_value')
```

### 3.5 Primary Key Renaming

Primary key attributes CAN be renamed:

```python
Subject.proj(mouse_id='subject_id')
# Result PK: (mouse_id,) instead of (subject_id,)
```

### 3.6 Excluding Attributes

Use `-` prefix with ellipsis to exclude:

```python
# All attributes except 'internal_notes'
Session.proj(..., '-internal_notes')

# Multiple exclusions
Session.proj(..., '-notes', '-metadata')
```

Cannot exclude primary key attributes.

### 3.7 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | Preserved (may be renamed) |
| Attributes | Selected/computed subset |
| Entity Type | Preserved |

### 3.8 Error Conditions

| Condition | Error |
|-----------|-------|
| Attribute not found | `UnknownAttributeError` |
| Excluding PK attribute | `DataJointError` |
| Duplicate attribute name | `DataJointError` |

---

## 4. Join (`*`)

### 4.1 Syntax

```python
result = A * B                                    # Inner join
result = A.join(B, semantic_check=True, left=False)
```

### 4.2 Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `semantic_check` | `True` | Match only homologous namesakes |
| `left` | `False` | LEFT JOIN (preserve all rows from A) |

### 4.3 Join Condition

Joins match on all shared non-hidden attributes (namesakes):

```python
# If Session has (subject_id, session_id) and Trial has (subject_id, session_id, trial_id)
# Join matches on (subject_id, session_id)
Session * Trial
```

### 4.4 Primary Key Determination

The result's primary key depends on functional dependencies:

| Condition | Result PK | Attribute Order |
|-----------|-----------|-----------------|
| A → B | PK(A) | A's attributes first |
| B → A | PK(B) | B's attributes first |
| Both | PK(A) | A's attributes first |
| Neither | PK(A) ∪ PK(B) | A's PK, then B's additional PK |

**A → B** means: All of B's primary key attributes exist in A (as PK or secondary).

### 4.5 Examples

```python
# Session → Trial (Session's PK is subset of Trial's PK)
Session * Trial
# Result PK: (subject_id, session_id) — same as Session

# Neither determines the other
Subject * Experimenter
# Result PK: (subject_id, experimenter_id) — union of PKs
```

### 4.6 Left Join

Preserve all rows from left operand:

```python
# All sessions, with trial data where available
Session.join(Trial, left=True)
```

**Constraint**: Left join requires A → B to prevent NULL values in result's primary key.

### 4.7 Semantic Matching

With `semantic_check=True`, only homologous namesakes are matched:

```python
# Semantic join (default)
TableA * TableB

# Natural join (match all namesakes regardless of lineage)
TableA.join(TableB, semantic_check=False)
```

### 4.8 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | Depends on functional dependencies |
| Attributes | Union of both operands' attributes |
| Commutativity | Result rows same, but PK/order may differ |

### 4.9 Error Conditions

| Condition | Error |
|-----------|-------|
| Different database connections | `DataJointError` |
| Non-homologous namesakes (semantic mode) | `DataJointError` |
| Left join without A → B | `DataJointError` |

---

## 5. Aggregation (`.aggr()`)

### 5.1 Syntax

```python
result = A.aggr(B, ...)                           # All A attributes
result = A.aggr(B, 'attr1', 'attr2')              # PK + specified from A
result = A.aggr(B, ..., count='count(*)')         # With aggregate
result = A.aggr(B, ..., exclude_nonmatching=True) # Only rows with matches
```

### 5.2 Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `*attributes` | — | Attributes from A to include |
| `exclude_nonmatching` | `False` | If True, exclude rows from A that have no matches in B (INNER JOIN). Default keeps all rows (LEFT JOIN). |
| `**named_attributes` | — | Computed aggregates |

### 5.3 Requirement

**B must contain all primary key attributes of A.** This enables grouping B's rows by A's primary key.

### 5.4 Aggregate Functions

```python
# Count
Session.aggr(Trial, n_trials='count(*)')

# Sum, average, min, max
Session.aggr(Trial,
    total='sum(score)',
    avg_score='avg(score)',
    best='max(score)',
    worst='min(score)'
)

# Group concatenation
Session.aggr(Trial, trial_list='group_concat(trial_id)')

# Conditional count
Session.aggr(Trial, n_correct='sum(correct = 1)')
```

### 5.5 SQL Equivalent

```sql
SELECT A.pk1, A.pk2, A.secondary, agg_func(B.col) AS new_attr
FROM A
[LEFT] JOIN B USING (pk1, pk2)
WHERE <A restrictions>
GROUP BY A.pk1, A.pk2
HAVING <B restrictions>
```

### 5.6 Restriction Behavior

Restrictions on A attributes → WHERE clause (before GROUP BY)
Restrictions on B attributes → HAVING clause (after GROUP BY)

```python
# WHERE: only 2024 sessions, then count trials
(Session & "YEAR(session_date) = 2024").aggr(Trial, n='count(*)')

# HAVING: sessions with more than 10 trials
Session.aggr(Trial, n='count(*)') & "n > 10"
```

### 5.7 Default Behavior: Keep All Rows

By default (`exclude_nonmatching=False`), aggregation keeps all rows from A, even those without matches in B:

```python
# All sessions included; those without trials have n=0
Session.aggr(Trial, n='count(trial_id)')

# Only sessions that have at least one trial
Session.aggr(Trial, n='count(trial_id)', exclude_nonmatching=True)
```

Note: Use `count(pk_attr)` rather than `count(*)` to correctly count 0 for sessions without trials. `count(*)` counts all rows including the NULL-filled left join row.

### 5.8 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | PK(A) — grouping expression's PK |
| Entity Type | Same as A |

### 5.9 Error Conditions

| Condition | Error |
|-----------|-------|
| B missing A's PK attributes | `DataJointError` |
| Semantic mismatch | `DataJointError` |

---

## 6. Extension (`.extend()`)

### 6.1 Syntax

```python
result = A.extend(B)
result = A.extend(B, semantic_check=True)
```

### 6.2 Semantics

Extend is a left join that adds attributes from B while preserving A's entity identity:

```python
A.extend(B)
# Equivalent to:
A.join(B, left=True)
```

### 6.3 Requirement

**A must determine B** (A → B). All of B's primary key attributes must exist in A.

### 6.4 Use Case

Add optional attributes without losing rows:

```python
# Add experimenter info to sessions (some sessions may lack experimenter)
Session.extend(Experimenter)
```

### 6.5 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | PK(A) |
| Attributes | A's attributes + B's non-PK attributes |
| Entity Type | Same as A |

### 6.6 Error Conditions

| Condition | Error |
|-----------|-------|
| A does not determine B | `DataJointError` |

---

## 7. Union (`+`)

### 7.1 Syntax

```python
result = A + B
```

### 7.2 Requirements

1. **Same connection**: Both from same database
2. **Same primary key**: Identical PK attributes (names and types)
3. **No secondary attribute overlap**: A and B cannot share secondary attributes

### 7.3 Semantics

Combines entity sets from both operands:

```python
# All subjects that are either mice or rats
Mouse + Rat
```

### 7.4 Attribute Handling

| Scenario | Result |
|----------|--------|
| PK only in both | Union of PKs |
| A has secondary attrs | A's secondaries (NULL for B-only rows) |
| B has secondary attrs | B's secondaries (NULL for A-only rows) |
| Overlapping PKs | A's values take precedence |

### 7.5 SQL Implementation

```sql
-- With secondary attributes
(SELECT A.* FROM A LEFT JOIN B USING (pk))
UNION
(SELECT B.* FROM B WHERE (B.pk) NOT IN (SELECT A.pk FROM A))
```

### 7.6 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | PK(A) = PK(B) |
| Associative | (A + B) + C = A + (B + C) |
| Commutative | A + B has same rows as B + A |

### 7.7 Error Conditions

| Condition | Error |
|-----------|-------|
| Different connections | `DataJointError` |
| Different primary keys | `DataJointError` |
| Overlapping secondary attributes | `DataJointError` |

---

## 8. Universal Sets (`dj.U()`)

### 8.1 Syntax

```python
dj.U()                    # Singular entity (one row, no attributes)
dj.U('attr1', 'attr2')    # Set of all combinations
```

### 8.2 Unique Value Enumeration

Extract distinct values:

```python
# All unique last names
dj.U('last_name') & Student

# All unique (year, month) combinations
dj.U('year', 'month') & Session.proj(year='YEAR(date)', month='MONTH(date)')
```

Result has specified attributes as primary key, with DISTINCT semantics.

### 8.3 Universal Aggregation

Aggregate entire table (no grouping):

```python
# Count all students
dj.U().aggr(Student, n='count(*)')
# Result: single row with n = total count

# Global statistics
dj.U().aggr(Trial,
    total='count(*)',
    avg_score='avg(score)',
    std_score='std(score)'
)
```

### 8.4 Arbitrary Grouping

Group by attributes not in original PK:

```python
# Count students by graduation year
dj.U('grad_year').aggr(Student, n='count(*)')

# Monthly session counts
dj.U('year', 'month').aggr(
    Session.proj(year='YEAR(date)', month='MONTH(date)'),
    n='count(*)'
)
```

### 8.5 Primary Key Behavior

| Usage | Result PK |
|-------|-----------|
| `dj.U() & table` | Empty (single row) |
| `dj.U('a', 'b') & table` | (a, b) |
| `dj.U().aggr(table, ...)` | Empty (single row) |
| `dj.U('a').aggr(table, ...)` | (a,) |

### 8.6 Restrictions

```python
# U attributes must exist in the table
dj.U('name') & Student        # OK: 'name' in Student
dj.U('invalid') & Student     # Error: 'invalid' not found
```

### 8.7 Error Conditions

| Condition | Error |
|-----------|-------|
| `table * dj.U()` | `DataJointError` (use `&` instead) |
| `dj.U() - table` | `DataJointError` (infinite set) |
| U attributes not in table | `DataJointError` |
| `dj.U().aggr(..., exclude_nonmatching=False)` | `DataJointError` (cannot keep all rows from infinite set) |

---

## 9. Semantic Matching

### 9.1 Attribute Lineage

Every attribute has a lineage tracing to its original definition:

```
schema.table.attribute
```

Foreign key inheritance preserves lineage:

```python
class Session(dj.Manual):
    definition = """
    -> Subject          # Inherits subject_id with Subject's lineage
    session_id : int
    """
```

### 9.2 Homologous Namesakes

Two attributes are **homologous namesakes** if they have:
1. Same name
2. Same lineage (trace to same original definition)

### 9.3 Non-Homologous Namesakes

Attributes with same name but different lineage create semantic collisions:

```python
# Both have 'name' but from different origins
Student * Course  # Error if both have 'name' attribute
```

### 9.4 Resolution

Rename to avoid collisions:

```python
Student * Course.proj(..., course_name='name')
```

### 9.5 Semantic Check Parameter

| Value | Behavior |
|-------|----------|
| `True` (default) | Match only homologous namesakes; error on collisions |
| `False` | Natural join on all namesakes regardless of lineage |

---

## 10. Operator Precedence

Python operator precedence applies:

| Precedence | Operator | Operation |
|------------|----------|-----------|
| Highest | `*` | Join |
| | `+`, `-` | Union, Anti-restriction |
| Lowest | `&` | Restriction |

Use parentheses for clarity:

```python
(Session & condition) * Trial    # Restrict then join
Session & (Trial * Stimulus)     # Join then restrict
```

---

## 11. Subquery Generation

Subqueries are generated automatically when needed:

| Situation | Subquery Created |
|-----------|------------------|
| Restrict on computed attribute | Yes |
| Join on computed attribute | Yes |
| Aggregation operand | Yes |
| Union operand | Yes |
| Restriction after TOP | Yes |

---

## 12. Top (`dj.Top`)

### 12.1 Syntax

```python
result = expression & dj.Top()                          # First row by primary key
result = expression & dj.Top(limit=5)                   # First 5 rows by primary key
result = expression & dj.Top(5, 'score DESC')           # Top 5 by score descending
result = expression & dj.Top(10, order_by='date DESC')  # Top 10 by date descending
result = expression & dj.Top(5, offset=10)              # Skip 10, take 5
result = expression & dj.Top(None, 'score DESC')        # All rows, ordered by score
```

### 12.2 Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` or `None` | `1` | Maximum rows to return. `None` = unlimited. |
| `order_by` | `str`, `list[str]`, or `None` | `"KEY"` | Ordering. `"KEY"` = primary key order. `None` = inherit existing order. |
| `offset` | `int` | `0` | Rows to skip before taking `limit`. |

### 12.3 Ordering Specification

| Format | Meaning |
|--------|---------|
| `"KEY"` | Order by primary key (ascending) |
| `"attr"` | Order by attribute (ascending) |
| `"attr DESC"` | Order by attribute (descending) |
| `"attr ASC"` | Order by attribute (ascending, explicit) |
| `["attr1 DESC", "attr2"]` | Multiple columns |
| `None` | Inherit ordering from existing Top |

### 12.4 SQL Equivalent

```sql
SELECT * FROM table
ORDER BY order_by
LIMIT limit OFFSET offset
```

### 12.5 Chaining Tops

When multiple Tops are chained, behavior depends on the `order_by` parameter:

| Scenario | Behavior |
|----------|----------|
| Second Top has `order_by=None` | **Merge**: inherits ordering, limits combined |
| Both Tops have identical `order_by` | **Merge**: ordering preserved, limits combined |
| Tops have different `order_by` | **Subquery**: first Top executed, then second applied |

**Merge behavior:**
- `limit` = minimum of both limits
- `offset` = sum of both offsets
- `order_by` = preserved from first Top

```python
# Merge: same result, single query
(Table & dj.Top(10, "score DESC")) & dj.Top(5, order_by=None)
# Effective: Top(5, "score DESC", offset=0)

# Merge with offsets
(Table & dj.Top(10, "x", offset=5)) & dj.Top(3, order_by=None, offset=2)
# Effective: Top(3, "x", offset=7)

# Subquery: different orderings
(Table & dj.Top(10, "score DESC")) & dj.Top(3, "id ASC")
# First selects top 10 by score, then reorders those 10 by id and takes 3
```

### 12.6 Preview and Limit

When fetching with a `limit` parameter, the limit is applied as an additional Top that inherits existing ordering:

```python
# User applies custom ordering
query = Table & dj.Top(order_by="score DESC")

# Preview respects the ordering
query.to_arrays("id", "score", limit=5)  # Top 5 by score descending
```

Internally, `to_arrays(..., limit=N)` applies `dj.Top(N, order_by=None)`, which inherits the existing ordering.

### 12.7 Use Cases

**Top N rows:**
```python
# Top 10 highest scores
Result & dj.Top(10, "score DESC")
```

**Pagination:**
```python
# Page 3 (rows 20-29) sorted by date
Session & dj.Top(10, "session_date DESC", offset=20)
```

**Sampling (deterministic):**
```python
# First 100 rows by primary key
BigTable & dj.Top(100)
```

**Ordering without limit:**
```python
# All rows ordered by date
Session & dj.Top(None, "session_date DESC")
```

### 12.8 Algebraic Properties

| Property | Value |
|----------|-------|
| Primary Key | Preserved: PK(result) = PK(input) |
| Attributes | Preserved: all attributes retained |
| Entity Type | Preserved |
| Row Order | Determined by `order_by` |

### 12.9 Error Conditions

| Condition | Error |
|-----------|-------|
| `limit` not int or None | `TypeError` |
| `order_by` not str, list[str], or None | `TypeError` |
| `offset` not int | `TypeError` |
| Top in OR list | `DataJointError` |
| Top in AndList | `DataJointError` |

---

## 13. SQL Transpilation

This section describes how DataJoint translates query expressions to SQL.

### 13.1 MySQL Clause Evaluation Order

MySQL differs from standard SQL in clause evaluation:

```
Standard SQL: FROM → WHERE → GROUP BY → HAVING → SELECT
MySQL:        FROM → WHERE → SELECT → GROUP BY → HAVING
```

This allows `GROUP BY` and `HAVING` clauses to use alias column names created by `SELECT`. DataJoint targets MySQL's behavior where column aliases can be used in `HAVING`.

### 13.2 QueryExpression Properties

Each `QueryExpression` represents a SQL `SELECT` statement with these properties:

| Property | SQL Clause | Description |
|----------|------------|-------------|
| `heading` | `SELECT` | Attributes and computed expressions |
| `restriction` | `WHERE` / `HAVING` | Filter conditions |
| `support` | `FROM` | Base tables and joined tables |
| `_top` | `ORDER BY` / `LIMIT` | Ordering and pagination |
| `_group_by` | `GROUP BY` | Grouping (for aggregations) |

### 13.3 Modify-in-Place vs. Subquery Wrapping

When an operator is applied to a QueryExpression, DataJoint either:

1. **Modifies in place**: Adds/modifies clauses in the existing SELECT statement
2. **Wraps as subquery**: Creates a new outer SELECT with the input as a FROM subquery

The choice depends on SQL semantics—whether the operation can be expressed by adding clauses, or whether the input must first be materialized as a derived table.

### 13.4 Restriction Rules (`&` and `-`)

**Modify in place** when restricting on:
- Base table attributes (columns from FROM tables)
- Primary key attributes (including those inherited via FK)

**Wrap as subquery** when restricting on:
- Computed/aliased attributes (created by `.proj()`)
- Aggregated attributes (created by `.aggr()`)
- Any attribute after `LIMIT`/`OFFSET` has been applied

```python
# Modify in place: condition added to WHERE
Session & "session_date > '2024-01-01'"
# SQL: SELECT ... FROM session WHERE session_date > '2024-01-01'

# Subquery required: restriction references computed alias
Session.proj(year='YEAR(session_date)') & "year = 2024"
# SQL: SELECT * FROM (
#        SELECT ..., YEAR(session_date) as year FROM session
#      ) AS _s1 WHERE year = 2024
```

**Aggregation special case**: Restrictions after aggregation go to HAVING (MySQL) or require subquery (PostgreSQL):

```python
Session.aggr(Trial, n='count(*)') & "n > 10"
# MySQL:      ... GROUP BY pk HAVING n > 10
# PostgreSQL: SELECT * FROM (...GROUP BY pk) AS _s1 WHERE n > 10
```

### 13.5 Projection Rules (`.proj()`)

**Modify in place** when:
- Selecting a subset of existing attributes
- Renaming base attributes
- Computing new attributes from base columns

**Wrap as subquery** when:
- Computing attribute from another computed attribute (alias of alias)
- Projecting after `LIMIT`/`OFFSET` has been applied

```python
# Modify in place: adds computed column to SELECT
Session.proj(year='YEAR(session_date)')
# SQL: SELECT pk, YEAR(session_date) as year FROM session

# Subquery required: decade depends on year alias
Session.proj(year='YEAR(session_date)').proj(decade='year - year % 10')
# SQL: SELECT pk, year - year % 10 as decade FROM (
#        SELECT pk, YEAR(session_date) as year FROM session
#      ) AS _s1
```

### 13.5.1 Join Rules (`*`)

**Modify in place** (merge both operands' clauses) when:
- Both operands are base tables or simple projections
- Join attributes are base columns (not computed)
- Neither operand has `LIMIT`/`OFFSET` or `GROUP BY`

**Wrap operand as subquery** when operand has:
- Computed attributes used in join condition
- `LIMIT`/`OFFSET` applied
- `GROUP BY` (is an aggregation result)
- Is a union expression

```python
# Modify in place: merge FROM and WHERE clauses
Session * Trial
# SQL: SELECT ... FROM session JOIN trial USING (pk)

# Subquery required: aggregation as join operand
Session * Session.aggr(Trial, n='count(*)')
# SQL: SELECT ... FROM session JOIN (
#        SELECT pk, count(*) as n FROM session
#        LEFT JOIN trial USING (pk) GROUP BY pk
#      ) AS _s1 USING (pk)
```

### 13.5.2 Aggregation Rules (`.aggr()`)

Aggregation produces a query with `GROUP BY`. The grouped expression is joined:

```sql
SELECT A.pk, A.secondary, agg_func(B.col) AS computed
FROM A LEFT JOIN B USING (pk)
WHERE <restrictions on A attributes>
GROUP BY A.pk
HAVING <restrictions on B or computed attributes>
```

**Restrictions routing:**
- On grouping expression (A) attributes → `WHERE` (before GROUP BY)
- On grouped expression (B) or computed attributes → `HAVING` (after GROUP BY)

**Aggregation result requires subquery** when used as operand to:
- Another join (`*`)
- Further restriction on computed attributes
- Another aggregation

### 13.5.3 Top/Limit Rules (`dj.Top`)

**Any operation after Top requires subquery** (the limited result must materialize):

```python
(Session & dj.Top(10, 'date DESC')) & "notes IS NOT NULL"
# SQL: SELECT * FROM (
#        SELECT * FROM session ORDER BY date DESC LIMIT 10
#      ) AS _s1 WHERE notes IS NOT NULL
```

Exception: Chaining Tops with compatible ordering can merge (see Section 12.5)

### 13.6 Backend-Specific Transpilation

DataJoint supports multiple database backends with differing SQL dialects. The adapter layer handles:

#### 13.6.1 Function Translation

Aggregate functions are translated bidirectionally:

| DataJoint | MySQL | PostgreSQL |
|-----------|-------|------------|
| `GROUP_CONCAT(col)` | `GROUP_CONCAT(col)` | `STRING_AGG(col::text, ',')` |
| `STRING_AGG(col, sep)` | `GROUP_CONCAT(col SEPARATOR sep)` | `STRING_AGG(col, sep)` |

Code using either syntax works on both backends.

#### 13.6.2 HAVING Clause Alias References

MySQL allows column aliases in HAVING:

```sql
SELECT person_id, COUNT(*) as n_languages
FROM proficiency
GROUP BY person_id
HAVING n_languages >= 4   -- MySQL: OK, PostgreSQL: ERROR
```

PostgreSQL (following SQL standard) requires repeating the expression or using a subquery:

```sql
-- Option A: Repeat expression
HAVING COUNT(*) >= 4

-- Option B: Subquery wrapper
SELECT * FROM (
  SELECT person_id, COUNT(*) as n_languages
  FROM proficiency
  GROUP BY person_id
) AS subq
WHERE n_languages >= 4
```

**DataJoint approach:** When generating SQL for PostgreSQL, if the HAVING clause references computed attribute aliases, the aggregation is wrapped in a subquery and the HAVING condition becomes a WHERE clause on the outer query.

| Backend | HAVING with alias | Generated SQL |
|---------|------------------|---------------|
| MySQL | Direct | `... GROUP BY pk HAVING alias > 5` |
| PostgreSQL | Subquery wrapper | `SELECT * FROM (...) AS subq WHERE alias > 5` |

This ensures consistent behavior across backends while maintaining query correctness.

#### 13.6.3 Identifier Quoting

| Backend | Identifier Quote | Example |
|---------|-----------------|---------|
| MySQL | Backtick | `` `table`.`column` `` |
| PostgreSQL | Double quote | `"table"."column"` |

#### 13.6.4 String Literal Quoting

| Backend | String Literals | Identifier Literals |
|---------|----------------|-------------------|
| MySQL | `'value'` or `"value"` | `` `name` `` |
| PostgreSQL | `'value'` only | `"name"` |

In PostgreSQL, double quotes denote identifiers, not string literals. Dictionary restrictions handle this automatically; string restrictions must use single quotes for values.

### 13.7 Union SQL

Union performs an outer join:

```sql
(SELECT A.pk, A.secondary, NULL as B.secondary FROM A)
UNION
(SELECT B.pk, NULL as A.secondary, B.secondary FROM B
 WHERE B.pk NOT IN (SELECT pk FROM A))
```

All union inputs become subqueries except unrestricted unions.

### 13.8 Query Backprojection

Before execution, `finalize()` recursively projects out unnecessary attributes from all inputs. This optimization:

- Reduces data transfer (especially for blobs)
- Compensates for MySQL's query optimizer limitations
- Produces leaner queries for complex expressions

### 13.9 Subquery Generation Summary

| Trigger | Reason | Strategy |
|---------|--------|----------|
| Restrict on computed attribute | Alias must exist before WHERE references it | Wrap input |
| Restrict after LIMIT/OFFSET | Limited result must materialize first | Wrap input |
| Project alias from alias | First alias must materialize | Wrap input |
| Join on computed attribute | Join condition can't reference SELECT alias | Wrap operand |
| Aggregation as join operand | GROUP BY must complete first | Wrap operand |
| Restrict on aggregated attribute | HAVING result must materialize (PostgreSQL) | Wrap aggregation |
| Union operands | UNION requires complete subqueries | Wrap both |
| PostgreSQL HAVING with alias | Standard SQL compliance | Wrap + convert to WHERE |

---

## 14. Implementation Reference

| File | Purpose |
|------|---------|
| `expression.py` | QueryExpression base class, operators |
| `condition.py` | Restriction condition handling, Top class |
| `heading.py` | Attribute metadata and lineage |
| `table.py` | Table class, fetch interface |
| `U.py` | Universal set implementation |

---

## 15. Quick Reference

| Operation | Syntax | Result PK |
|-----------|--------|-----------|
| Restrict | `A & cond` | PK(A) |
| Anti-restrict | `A - cond` | PK(A) |
| Project | `A.proj(...)` | PK(A) |
| Join | `A * B` | Depends on A→B |
| Aggregate | `A.aggr(B, ...)` | PK(A) |
| Extend | `A.extend(B)` | PK(A) |
| Union | `A + B` | PK(A) = PK(B) |
| Unique values | `dj.U('x') & A` | (x,) |
| Global aggregate | `dj.U().aggr(A, ...)` | () |
