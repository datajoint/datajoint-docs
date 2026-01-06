# Table Definition Syntax

DataJoint's declarative table definition language.

## Basic Structure

```python
@schema
class TableName(dj.Manual):
    definition = """
    # Table comment
    primary_attr1 : type    # comment
    primary_attr2 : type    # comment
    ---
    secondary_attr1 : type  # comment
    secondary_attr2 = default : type  # comment with default
    """
```

## Grammar

```
definition     = [comment] pk_section "---" secondary_section
pk_section     = attribute_line+
secondary_section = attribute_line*

attribute_line = [foreign_key | attribute]
foreign_key    = "->" table_reference [alias]
attribute      = [default "="] name ":" type [# comment]

default        = NULL | literal | CURRENT_TIMESTAMP
type           = core_type | codec_type | native_type
core_type      = int32 | float64 | varchar(n) | ...
codec_type     = "<" name ["@" [store]] ">"
```

## Foreign Keys

```python
-> ParentTable                    # Inherit all PK attributes
-> ParentTable.proj(new='old')    # Rename attributes
```

## Attribute Types

### Core Types

```python
mouse_id : int32                  # 32-bit integer
weight : float64                  # 64-bit float
name : varchar(100)               # Variable string up to 100 chars
is_active : bool                  # Boolean
created : datetime                # Date and time
data : json                       # JSON document
```

### Codec Types

```python
image : <blob>                    # Serialized Python object (in DB)
large_array : <blob@>             # Serialized Python object (external)
config_file : <attach>            # File attachment (in DB)
data_file : <attach@archive>      # File attachment (named store)
zarr_data : <object@>             # Path-addressed folder
raw_path : <filepath@raw>         # Portable file reference
```

## Defaults

```python
status = "pending" : varchar(20)  # String default
count = 0 : int32                 # Numeric default
notes = '' : varchar(1000)        # Empty string default (preferred for strings)
created = CURRENT_TIMESTAMP : datetime  # Auto-timestamp
ratio = NULL : float64            # Nullable (only NULL can be default)
```

**Nullable attributes:** An attribute is nullable if and only if its default is `NULL`.
DataJoint does not allow other defaults for nullable attributes—this prevents ambiguity
about whether an attribute is optional. For strings, prefer empty string `''` as the
default rather than `NULL`.

## Comments

```python
# Table-level comment (first line)
mouse_id : int32    # Inline attribute comment
```

## Indexes

```python
definition = """
    ...
    ---
    ...
    INDEX (attr1)                 # Single-column index
    INDEX (attr1, attr2)          # Composite index
    UNIQUE INDEX (email)          # Unique constraint
    """
```

## Complete Example

```python
@schema
class Session(dj.Manual):
    definition = """
    # Experimental session
    -> Subject
    session_idx : int32           # Session number for this subject
    ---
    session_date : date           # Date of session
    -> [nullable] Experimenter    # Optional experimenter
    notes = '' : varchar(1000)    # Session notes
    start_time : datetime         # Session start
    duration : float64            # Duration in minutes
    INDEX (session_date)
    """
```

## Validation

DataJoint validates definitions at declaration time:

- Primary key must have at least one attribute
- Attribute names must be valid identifiers
- Types must be recognized
- Foreign key references must exist
- No circular dependencies allowed

## See Also

- [Primary Keys](specs/primary-keys.md) — Key determination rules
- [Type System](specs/type-system.md) — Type architecture
- [Codec API](specs/codec-api.md) — Custom types
