# Insert Data

Add data to DataJoint tables.

## Single Row

```python
Subject.insert1({
    'subject_id': 'M001',
    'species': 'Mus musculus',
    'date_of_birth': '2026-01-15',
    'sex': 'M'
})
```

## Multiple Rows

```python
Subject.insert([
    {'subject_id': 'M001', 'species': 'Mus musculus', 'date_of_birth': '2026-01-15', 'sex': 'M'},
    {'subject_id': 'M002', 'species': 'Mus musculus', 'date_of_birth': '2026-02-01', 'sex': 'F'},
    {'subject_id': 'M003', 'species': 'Mus musculus', 'date_of_birth': '2026-02-15', 'sex': 'M'},
])
```

## From pandas DataFrame

```python
import pandas as pd

df = pd.DataFrame({
    'subject_id': ['M004', 'M005'],
    'species': ['Mus musculus', 'Mus musculus'],
    'date_of_birth': ['2026-03-01', '2026-03-15'],
    'sex': ['F', 'M']
})

Subject.insert(df)
```

## Handle Duplicates

```python
# Skip rows with existing primary keys
Subject.insert(rows, skip_duplicates=True)

# Replace existing rows (use sparingly—breaks immutability)
Subject.insert(rows, replace=True)
```

## Ignore Extra Fields

```python
# Ignore fields not in the table definition
Subject.insert(rows, ignore_extra_fields=True)
```

## Master-Part Tables

Use a transaction to maintain compositional integrity:

```python
with dj.conn().transaction:
    Session.insert1({
        'subject_id': 'M001',
        'session_idx': 1,
        'session_date': '2026-01-20'
    })
    Session.Trial.insert([
        {'subject_id': 'M001', 'session_idx': 1, 'trial_idx': 1, 'outcome': 'hit', 'reaction_time': 0.35},
        {'subject_id': 'M001', 'session_idx': 1, 'trial_idx': 2, 'outcome': 'miss', 'reaction_time': 0.82},
    ])
```

## Insert from Query

```python
# Copy data from another table or query result
NewTable.insert(OldTable & 'condition')

# With projection
NewTable.insert(OldTable.proj('attr1', 'attr2', new_name='old_name'))
```

## Validate Before Insert

```python
result = Subject.validate(rows)

if result:
    Subject.insert(rows)
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  {error}")
```

## Insert with Blobs

```python
import numpy as np

data = np.random.randn(100, 100)

ImageData.insert1({
    'image_id': 1,
    'pixel_data': data  # Automatically serialized
})
```

## Insert Options Summary

| Option | Default | Description |
|--------|---------|-------------|
| `skip_duplicates` | `False` | Skip rows with existing keys |
| `replace` | `False` | Replace existing rows |
| `ignore_extra_fields` | `False` | Ignore unknown fields |

## Best Practices

### Batch inserts for performance

```python
# Good: Single insert call
Subject.insert(all_rows)

# Slow: Loop of insert1 calls
for row in all_rows:
    Subject.insert1(row)
```

### Use transactions for related inserts

```python
with dj.conn().transaction:
    Parent.insert1(parent_row)
    Child.insert(child_rows)
```

### Validate before bulk inserts

```python
if Subject.validate(rows):
    Subject.insert(rows)
```

## See Also

- [Master-Part Tables](master-part.ipynb) — Atomic insertion of master and parts
- [Define Tables](define-tables.md) — Table definition syntax
- [Delete Data](delete-data.md) — Removing data from tables
