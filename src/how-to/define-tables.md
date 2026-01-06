# Define Tables

Create DataJoint table classes with proper definitions.

## Basic Structure

```python
import datajoint as dj

schema = dj.Schema('my_schema')

@schema
class MyTable(dj.Manual):
    definition = """
    # Table comment (optional)
    primary_attr : type      # attribute comment
    ---
    secondary_attr : type    # attribute comment
    optional_attr = null : type
    """
```

## Table Types

| Type | Base Class | Purpose |
|------|------------|---------|
| Manual | `dj.Manual` | User-entered data |
| Lookup | `dj.Lookup` | Reference data with `contents` |
| Imported | `dj.Imported` | Data from external sources |
| Computed | `dj.Computed` | Derived data |
| Part | `dj.Part` | Child of master table |

## Primary Key (Above `---`)

```python
definition = """
subject_id : varchar(16)      # Subject identifier
session_idx : uint16          # Session number
---
...
"""
```

Primary key attributes:
- Cannot be NULL
- Must be unique together
- Cannot be changed after insertion

## Secondary Attributes (Below `---`)

```python
definition = """
...
---
session_date : date           # Required attribute
notes = '' : varchar(1000)    # Optional with default
score = null : float32        # Nullable attribute
"""
```

## Core DataJoint Types

| Type | Description |
|------|-------------|
| `bool` | Boolean (true/false) |
| `int8`, `int16`, `int32`, `int64` | Signed integers |
| `uint8`, `uint16`, `uint32`, `uint64` | Unsigned integers |
| `float32`, `float64` | Floating point |
| `decimal(m,n)` | Fixed precision decimal |
| `varchar(n)` | Variable-length string |
| `char(n)` | Fixed-length string |
| `date` | Date (YYYY-MM-DD) |
| `time` | Time (HH:MM:SS) |
| `datetime` | Date and time |
| `datetime(3)` | With millisecond precision |
| `datetime(6)` | With microsecond precision |
| `timestamp` | Auto-updating timestamp |
| `uuid` | UUID type |
| `enum('a', 'b', 'c')` | Enumerated values |
| `<blob>` | Binary data (internal storage) |
| `<blob@store>` | Binary data (external storage) |

## Foreign Keys

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject                # References Subject table
    session_idx : uint16
    ---
    session_date : date
    """
```

The `->` inherits primary key attributes from the referenced table.

## Lookup Tables with Contents

```python
@schema
class TaskType(dj.Lookup):
    definition = """
    task_type : varchar(32)
    ---
    description : varchar(200)
    """
    contents = [
        {'task_type': 'detection', 'description': 'Detect target stimulus'},
        {'task_type': 'discrimination', 'description': 'Distinguish between stimuli'},
    ]
```

## Part Tables

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_idx : uint16
    ---
    session_date : date
    """

    class Trial(dj.Part):
        definition = """
        -> master
        trial_idx : uint16
        ---
        outcome : enum('hit', 'miss')
        reaction_time : float32
        """
```

## Computed Tables

```python
@schema
class SessionStats(dj.Computed):
    definition = """
    -> Session
    ---
    n_trials : uint32
    hit_rate : float32
    """

    def make(self, key):
        trials = (Session.Trial & key).fetch()
        self.insert1({
            **key,
            'n_trials': len(trials),
            'hit_rate': sum(t['outcome'] == 'hit' for t in trials) / len(trials)
        })
```

## Unique Constraints

```python
definition = """
record_id : uuid
---
unique index (email)        # email must be unique
email : varchar(100)
name : varchar(100)
"""
```

## Indexes

```python
definition = """
subject_id : varchar(16)
session_idx : uint16
---
index (session_date)        # Index for faster queries
session_date : date
experimenter : varchar(50)
"""
```

## JSON Attributes

```python
definition = """
config_id : uuid
---
parameters : <json>         # Stores JSON data
"""
```

## Declaring Tables

Tables are declared when first accessed:

```python
# Declaration happens here
Session()

# Or explicitly
Session().declare()
```

## View Table Definition

```python
# Show SQL definition
print(Session().describe())

# Show heading
print(Session().heading)
```
