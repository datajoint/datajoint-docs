# Define Tables

Create DataJoint table classes with proper definitions.

## Create a Schema

```python
import datajoint as dj

schema = dj.Schema('my_schema')  # Creates schema in database if it doesn't exist
```

The `Schema` object connects to the database and creates the schema (database) if it doesn't already exist.

## Basic Table Structure

```python
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

## Default Values and Nullable Attributes

Default values are specified with `= value` before the type:

```python
definition = """
subject_id : varchar(16)
---
weight = null : float32           # Nullable (default is NULL)
notes = '' : varchar(1000)        # Default empty string
is_active = 1 : bool              # Default true
created = CURRENT_TIMESTAMP : timestamp
"""
```

**Key rules:**

- The **only** way to make an attribute nullable is `= null`
- Attributes without defaults are required (NOT NULL)
- Primary key attributes cannot be nullable
- Primary key attributes cannot have static defaults

**Timestamp defaults:**

Primary keys can use time-dependent defaults like `CURRENT_TIMESTAMP`:

```python
definition = """
created_at = CURRENT_TIMESTAMP : timestamp(6)   # Microsecond precision
---
data : <blob>
"""
```

Timestamp precision options:

- `timestamp` or `datetime` — Second precision
- `timestamp(3)` or `datetime(3)` — Millisecond precision
- `timestamp(6)` or `datetime(6)` — Microsecond precision

## Auto-Increment (Not Recommended)

DataJoint core types do not support `AUTO_INCREMENT`. This is intentional—explicit key values enforce entity integrity and prevent silent creation of duplicate records.

Use `uuid` or natural keys instead:

```python
definition = """
recording_id : uuid              # Globally unique, client-generated
---
...
"""
```

If you must use auto-increment, native MySQL types allow it (with a warning):

```python
definition = """
record_id : int unsigned auto_increment    # Native type
---
...
"""
```

See [Design Primary Keys](design-primary-keys.md) for detailed guidance on key selection and why DataJoint avoids auto-increment.

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
| `datetime` | Date and time |
| `datetime(3)` | With millisecond precision |
| `datetime(6)` | With microsecond precision |
| `uuid` | UUID type |
| `enum('a', 'b', 'c')` | Enumerated values |
| `json` | JSON data |
| `bytes` | Raw binary data |

## Built-in Codecs

Codecs serialize Python objects to database storage. Use angle brackets for codec types:

| Codec | Description |
|-------|-------------|
| `<blob>` | Serialized Python objects (NumPy arrays, etc.) stored in database |
| `<blob@store>` | Serialized objects in object storage |
| `<attach>` | File attachments in database |
| `<attach@store>` | File attachments in object storage |
| `<object@store>` | Files/folders via ObjectRef (path-addressed, supports Zarr/HDF5) |

Example:

```python
definition = """
recording_id : uuid
---
neural_data : <blob@raw>      # NumPy array in 'raw' store
config_file : <attach>        # Attached file in database
parameters : json             # JSON data (core type, no brackets)
"""
```

## Native Database Types

You can also use native MySQL/MariaDB types directly when needed:

```python
definition = """
record_id : int unsigned      # Native MySQL type
data : mediumblob             # For larger binary data
description : text            # Unlimited text
"""
```

Native types are flagged with a warning at declaration time but are allowed. Core DataJoint types (like `int32`, `float64`) are portable and recommended for most use cases. Native database types provide access to database-specific features when needed.

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
        trials = (Session.Trial & key).to_dicts()
        self.insert1({
            **key,
            'n_trials': len(trials),
            'hit_rate': sum(t['outcome'] == 'hit' for t in trials) / len(trials)
        })
```

## Indexes

Declare indexes at the end of the definition, after all attributes:

```python
definition = """
subject_id : varchar(16)
session_idx : uint16
---
session_date : date
experimenter : varchar(50)
index (session_date)              # Index for faster queries
index (experimenter)              # Another index
unique index (external_id)        # Unique constraint
"""
```

## Declaring Tables

Tables are declared in the database when the `@schema` decorator applies to the class:

```python
@schema  # Table is declared here
class Session(dj.Manual):
    definition = """
    session_id : uint16
    ---
    session_date : date
    """
```

The decorator reads the `definition` string, parses it, and creates the corresponding table in the database if it doesn't exist.

## Dropping Tables and Schemas

During prototyping (before data are populated), you can drop and recreate tables:

```python
# Drop a single table
Session.drop()

# Drop entire schema (all tables)
schema.drop()
```

**Warning:** These operations permanently delete data. Use only during development.

## View Table Definition

```python
# Show SQL definition
print(Session().describe())

# Show heading
print(Session().heading)
```
