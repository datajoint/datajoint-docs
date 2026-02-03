# Query Operators Reference

DataJoint provides a small set of operators for querying data. All operators return new query expressions without modifying the original—queries are immutable and composable.

## Operator Summary

| Operator | Syntax | Description |
|----------|--------|-------------|
| Restriction | `A & condition` | Select rows matching condition |
| Anti-restriction | `A - condition` | Select rows NOT matching condition |
| Projection | `A.proj(...)` | Select, rename, or compute attributes |
| Join | `A * B` | Combine tables on matching attributes |
| Extension | `A.extend(B)` | Add attributes from B, keeping all rows of A |
| Aggregation | `A.aggr(B, ...)` | Group B by A's primary key and compute summaries |
| Union | `A + B` | Combine entity sets |

---

## Restriction (`&`)

Select rows that match a condition.

```python
# String condition (SQL expression)
Session & "session_date > '2024-01-01'"
Session & "duration BETWEEN 30 AND 60"

# Dictionary (exact match)
Session & {'subject_id': 'M001'}
Session & {'subject_id': 'M001', 'session_idx': 1}

# Query expression (matching keys)
Session & Subject                    # Sessions for subjects in Subject table
Session & (Subject & "sex = 'M'")    # Sessions for male subjects

# List (OR of conditions)
Session & [{'subject_id': 'M001'}, {'subject_id': 'M002'}]
```

**Chaining**: Multiple restrictions combine with AND:
```python
Session & "duration > 30" & {"experimenter": "alice"}
```

### Top N Rows (`dj.Top`)

Restrict to the top N rows with optional ordering:

```python
# First row by primary key
Session & dj.Top()

# First 10 rows by primary key (ascending)
Session & dj.Top(10)

# First 10 rows by primary key (descending)
Session & dj.Top(10, 'KEY DESC')

# Top 5 by score descending
Result & dj.Top(5, 'score DESC')

# Top 10 most recent sessions
Session & dj.Top(10, 'session_date DESC')

# Pagination: skip 20, take 10
Session & dj.Top(10, 'session_date DESC', offset=20)

# All rows ordered (no limit)
Session & dj.Top(None, 'session_date DESC')
```

**Parameters**:
- `limit` (default=1): Maximum rows. Use `None` for no limit.
- `order_by` (default="KEY"): Attribute(s) to sort by. `"KEY"` expands to all primary key attributes. Add `DESC` for descending order (e.g., `"KEY DESC"`, `"score DESC"`). Use `None` to inherit existing order.
- `offset` (default=0): Rows to skip.

**Chaining Tops**: When chaining multiple Top restrictions, the second Top can inherit the first's ordering by using `order_by=None`:

```python
# First Top sets the order, second inherits it
(Session & dj.Top(100, 'date DESC')) & dj.Top(10, order_by=None)
# Result: top 10 of top 100 by date descending
```

**Note**: `dj.Top` can only be used with restriction (`&`), not with anti-restriction (`-`).

---

## Anti-Restriction (`-`)

Select rows that do NOT match a condition.

```python
# Subjects without any sessions
Subject - Session

# Sessions not from subject M001
Session - {'subject_id': 'M001'}

# Sessions without trials
Session - Trial
```

---

## Projection (`.proj()`)

Select, rename, or compute attributes. Primary key is always included.

```python
# Primary key only
Subject.proj()

# Specific attributes
Subject.proj('species', 'sex')

# All attributes
Subject.proj(...)

# All except some
Subject.proj(..., '-notes', '-internal_id')

# Rename attribute
Subject.proj(animal_species='species')

# Computed attribute (SQL expression)
Subject.proj(weight_kg='weight / 1000')
Session.proj(year='YEAR(session_date)')
Trial.proj(is_correct='response = stimulus')
```

---

## Join (`*`)

Combine tables on shared attributes. DataJoint matches attributes by **semantic matching**—only attributes with the same name AND same origin (through foreign keys) are matched.

```python
# Join Subject and Session on subject_id
Subject * Session

# Three-way join
Subject * Session * Experimenter

# Join then restrict
(Subject * Session) & "sex = 'M'"

# Restrict then join (equivalent)
(Subject & "sex = 'M'") * Session
```

**Primary key of result**: Determined by functional dependencies between operands. See [Query Algebra Specification](specs/query-algebra.md) for details.

---

## Extension (`.extend()`)

Add attributes from another table while preserving all rows. This is useful for adding optional attributes.

```python
# Add experimenter info to sessions
# Sessions without an experimenter get NULL values
Session.extend(Experimenter)
```

**Requirement**: The left operand must "determine" the right operand—all of B's primary key attributes must exist in A.

---

## Aggregation (`.aggr()`)

Group one entity type by another and compute summary statistics.

```python
# Count trials per session
Session.aggr(Session.Trial, n_trials='count(trial_idx)')

# Multiple aggregates
Session.aggr(
    Session.Trial,
    n_trials='count(trial_idx)',
    n_correct='sum(correct)',
    avg_rt='avg(reaction_time)',
    min_rt='min(reaction_time)',
    max_rt='max(reaction_time)'
)

# Count sessions per subject
Subject.aggr(Session, n_sessions='count(session_idx)')
```

**Default behavior**: Keeps all rows from the grouping table (left operand), even those without matches. Use `count(pk_attribute)` to get 0 for entities without matches.

```python
# All subjects, including those with 0 sessions
Subject.aggr(Session, n_sessions='count(session_idx)')

# Only subjects with at least one session
Subject.aggr(Session, n_sessions='count(session_idx)', exclude_nonmatching=True)
```

### Common Aggregate Functions

| Function | Description |
|----------|-------------|
| `count(attr)` | Count non-NULL values |
| `count(*)` | Count all rows (including NULL) |
| `sum(attr)` | Sum of values |
| `avg(attr)` | Average |
| `min(attr)` | Minimum |
| `max(attr)` | Maximum |
| `std(attr)` | Standard deviation |
| `group_concat(attr)` | Concatenate values |

---

## Union (`+`)

Combine entity sets from two tables with the same primary key.

```python
# All subjects that are either mice or rats
Mouse + Rat
```

**Requirements**:
- Same primary key attributes
- No overlapping secondary attributes

---

## Universal Set (`dj.U()`)

Create ad-hoc groupings or extract unique values.

### Unique Values

```python
# Unique species
dj.U('species') & Subject

# Unique (year, month) combinations
dj.U('year', 'month') & Session.proj(year='YEAR(session_date)', month='MONTH(session_date)')
```

### Aggregation by Non-Primary-Key Attributes

```python
# Count sessions by date (session_date is not a primary key)
dj.U('session_date').aggr(Session, n='count(session_idx)')

# Count by experimenter
dj.U('experimenter_id').aggr(Session, n='count(session_idx)')
```

### Universal Aggregation (Single Row Result)

```python
# Total count across all sessions
dj.U().aggr(Session, total='count(*)')

# Global statistics
dj.U().aggr(Trial,
    total='count(*)',
    avg_rt='avg(reaction_time)',
    std_rt='std(reaction_time)'
)
```

---

## Operator Precedence

Python operator precedence applies:

| Precedence | Operator | Operation |
|------------|----------|-----------|
| Highest | `*` | Join |
| | `+`, `-` | Union, Anti-restriction |
| Lowest | `&` | Restriction |

Use parentheses to make intent clear:

```python
# Join happens before restriction
Subject * Session & condition    # Same as: (Subject * Session) & condition

# Use parentheses to restrict first
(Subject & condition) * Session
```

---

## Semantic Matching

DataJoint uses **semantic matching** for joins and restrictions by query expression. Attributes match only if they have:

1. The same name
2. The same origin (traced through foreign key lineage)

This prevents accidental matches on attributes that happen to share names but represent different things (like generic `id` columns in unrelated tables).

```python
# These match on subject_id because Session references Subject
Subject * Session  # Correct: subject_id has same lineage

# These would error if both have 'name' from different origins
Student * Course   # Error if both define their own 'name' attribute
```

**Resolution**: Rename attributes to avoid conflicts:
```python
Student * Course.proj(..., course_name='name')
```

---

## See Also

- [Query Algebra Specification](specs/query-algebra.md) — Complete formal specification
- [Fetch API](specs/fetch-api.md) — Retrieving query results
- [Queries Tutorial](../tutorials/basics/04-queries.ipynb/) — Hands-on examples
