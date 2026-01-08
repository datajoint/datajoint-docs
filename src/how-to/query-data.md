# Query Data

Filter, join, and transform data with DataJoint operators.

## Restriction (`&`)

Filter rows that match a condition:

```python
# String condition
Session & "session_date > '2026-01-01'"
Session & "duration BETWEEN 30 AND 60"

# Dictionary (exact match)
Session & {'subject_id': 'M001'}
Session & {'subject_id': 'M001', 'session_idx': 1}

# Query expression
Session & Subject                    # Sessions for subjects in Subject
Session & (Subject & "sex = 'M'")    # Sessions for male subjects

# List (OR)
Session & [{'subject_id': 'M001'}, {'subject_id': 'M002'}]
```

## Anti-Restriction (`-`)

Filter rows that do NOT match:

```python
Subject - Session          # Subjects without sessions
Session - {'subject_id': 'M001'}
```

## Projection (`.proj()`)

Select, rename, or compute attributes:

```python
# Primary key only
Subject.proj()

# Specific attributes
Subject.proj('species', 'sex')

# All attributes
Subject.proj(...)

# All except some
Subject.proj(..., '-notes')

# Rename
Subject.proj(animal_species='species')

# Computed
Subject.proj(weight_kg='weight / 1000')
```

## Join (`*`)

Combine tables on matching attributes:

```python
Subject * Session
Subject * Session * Experimenter

# Restrict then join
(Subject & "sex = 'M'") * Session
```

## Aggregation (`.aggr()`)

Group and summarize:

```python
# Count trials per session
Session.aggr(Session.Trial, n_trials='count(trial_idx)')

# Multiple aggregates
Session.aggr(
    Session.Trial,
    n_trials='count(trial_idx)',
    avg_rt='avg(reaction_time)',
    min_rt='min(reaction_time)'
)

# Exclude sessions without trials
Session.aggr(Session.Trial, n='count(trial_idx)', exclude_nonmatching=True)
```

## Universal Set (`dj.U()`)

Group by arbitrary attributes:

```python
# Unique values
dj.U('species') & Subject

# Group by non-primary-key attribute
dj.U('session_date').aggr(Session, n='count(session_idx)')

# Global aggregation (one row)
dj.U().aggr(Session, total='count(*)')
```

## Extension (`.extend()`)

Add attributes without losing rows:

```python
# Add experimenter info, keep all sessions
Session.extend(Experimenter)
```

## Chain Operations

```python
result = (
    Subject
    & "sex = 'M'"
    * Session
    & "duration > 30"
).proj('species', 'session_date', 'duration')
```

## Operator Precedence

| Priority | Operator | Operation |
|----------|----------|-----------|
| Highest | `*` | Join |
| | `+`, `-` | Union, Anti-restriction |
| Lowest | `&` | Restriction |

Use parentheses for clarity:

```python
(Subject & condition) * Session    # Restrict then join
Subject * (Session & condition)    # Join then restrict
```

## View Query

```python
# See generated SQL
print((Subject & condition).make_sql())

# Count rows without fetching
len(Subject & condition)
```

## See Also

- [Operators Reference](../reference/operators.md) — Complete operator documentation
- [Fetch Results](fetch-results.md) — Retrieving query results
