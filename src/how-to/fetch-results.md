# Fetch Results

Retrieve query results in various formats.

## List of Dictionaries

```python
rows = Subject.to_dicts()
# [{'subject_id': 'M001', 'species': 'Mus musculus', ...}, ...]

for row in rows:
    print(row['subject_id'], row['species'])
```

## pandas DataFrame

```python
df = Subject.to_pandas()
# Primary key becomes the index

# With multi-column primary key
df = Session.to_pandas()
# MultiIndex on (subject_id, session_idx)
```

## NumPy Arrays

```python
# Structured array (all columns)
arr = Subject.to_arrays()

# Specific columns as separate arrays
species, weights = Subject.to_arrays('species', 'weight')
```

## Primary Keys Only

```python
keys = Session.keys()
# [{'subject_id': 'M001', 'session_idx': 1}, ...]

for key in keys:
    process(Session & key)
```

## Single Row

```python
# As dictionary (raises if not exactly 1 row)
row = (Subject & {'subject_id': 'M001'}).fetch1()

# Specific attributes
species, weight = (Subject & {'subject_id': 'M001'}).fetch1('species', 'weight')
```

## Ordering and Limiting

```python
# Sort by single attribute
Subject.to_dicts(order_by='weight DESC')

# Sort by multiple attributes
Session.to_dicts(order_by=['session_date DESC', 'duration'])

# Sort by primary key
Subject.to_dicts(order_by='KEY')

# Limit rows
Subject.to_dicts(limit=10)

# Pagination
Subject.to_dicts(order_by='KEY', limit=10, offset=20)
```

## Streaming (Lazy Iteration)

```python
# Memory-efficient iteration
for row in Subject:
    process(row)
    if done:
        break  # Early termination
```

## polars DataFrame

```python
# Requires: pip install datajoint[polars]
df = Subject.to_polars()
```

## PyArrow Table

```python
# Requires: pip install datajoint[arrow]
table = Subject.to_arrow()
```

## Method Summary

| Method | Returns | Use Case |
|--------|---------|----------|
| `to_dicts()` | `list[dict]` | JSON, iteration |
| `to_pandas()` | `DataFrame` | Data analysis |
| `to_polars()` | `polars.DataFrame` | Fast analysis |
| `to_arrow()` | `pyarrow.Table` | Interop |
| `to_arrays()` | `np.ndarray` | Numeric computation |
| `to_arrays('a', 'b')` | `tuple[array, ...]` | Specific columns |
| `keys()` | `list[dict]` | Primary keys |
| `fetch1()` | `dict` | Single row |
| `for row in table:` | Iterator | Streaming |

## Common Parameters

All output methods accept:

| Parameter | Description |
|-----------|-------------|
| `order_by` | Sort by column(s): `'name'`, `'name DESC'`, `['a', 'b DESC']`, `'KEY'` |
| `limit` | Maximum rows to return |
| `offset` | Rows to skip |

## See Also

- [Query Data](query-data.md) — Building queries
- [Fetch API Specification](../reference/specs/fetch-api.md/) — Complete reference
