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
pk_section     = attribute_line*
secondary_section = attribute_line*

attribute_line = [foreign_key | attribute]
foreign_key    = "->" [modifiers] table_reference [rename]
modifiers      = "[" modifier ("," modifier)* "]"
modifier       = "nullable" | "unique"
attribute      = [default "="] name ":" type [# comment]

default        = NULL | literal | CURRENT_TIMESTAMP
type           = core_type | codec_type | native_type
core_type      = int32 | float64 | varchar(n) | ...
codec_type     = "<" name ["@" [store]] ">"
```

## Singleton Tables

!!! version-added "New in 2.1"

    Singleton tables were introduced in DataJoint 2.1.

The primary key section may be empty. A table declared that way is a **singleton**: it holds at
most one row, which is what you want for global configuration, pipeline-wide parameters, or a
single summary. Start the definition with the `---` separator and declare only secondary
attributes.

```python
@schema
class Config(dj.Lookup):
    definition = """
    # Global configuration
    ---
    setting1 : varchar(100)
    setting2 : int32
    """
```

`insert1` takes no key, a second insert raises `DuplicateError`, `fetch1()` returns the row, and
`heading.primary_key` is `[]`. Internally the table carries a hidden `_singleton` attribute as
its key, which is excluded from the heading, from `fetch()` results, and from join matching.

See [Table Declaration](specs/table-declaration.md#25-singleton-tables-empty-primary-keys) for
the full behavior.

## Foreign Keys

```python
-> ParentTable                    # Inherit all PK attributes
-> ParentTable.proj(new='old')    # Rename attributes
-> [nullable] ParentTable         # Optional reference (secondary only)
-> [unique] ParentTable           # One-to-one constraint
-> [nullable, unique] ParentTable # Optional one-to-one
```

### Modifiers

| Modifier | Effect | Position |
|----------|--------|----------|
| `[nullable]` | FK attributes can be NULL | Secondary only |
| `[unique]` | Creates UNIQUE INDEX on FK | Primary or secondary |
| `[nullable, unique]` | Optional one-to-one | Secondary only |

**Note:** Multiple rows can have NULL in a `[nullable, unique]` FK because SQL's UNIQUE constraint does not consider NULLs equal.

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
stage = '' : enum('', 'draft', 'reviewed', 'released')  # Empty-string member (preferred for enums)
created = CURRENT_TIMESTAMP : datetime  # Auto-timestamp
ratio = NULL : float64            # Nullable (only NULL can be default)
```

**Nullable attributes:** An attribute is nullable if and only if its default is `NULL`.
DataJoint does not allow other defaults for nullable attributes—this prevents ambiguity
about whether an attribute is optional.

**`varchar`, `char`, and `enum` attributes should default to `''`, not `NULL`.** `NULL`
and `''` both read as "nothing," and once an attribute allows both, every query and every
`make()` body has to handle two representations of the same absence. For `enum`, this
means adding `''` as an explicit member rather than making the attribute nullable—the
empty string is then just another value the type already enumerates, not a second
absence-mechanism layered on top of it. Reserve `NULL` for an attribute that is
genuinely optional and where "not yet known" must be distinguishable from "known to be
empty"—a case that arises rarely for text, and rarer still for a closed set of values a
schema author chose in the first place.

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
    -> [unique] Protocol          # Each protocol used at most once per session
    notes = '' : varchar(1000)    # Session notes
    start_time : datetime         # Session start
    duration : float64            # Duration in minutes
    INDEX (session_date)
    """
```

## Validation

DataJoint validates definitions at declaration time:

- Attribute names must be valid identifiers
- Types must be recognized
- Foreign key references must exist
- No circular dependencies allowed

## See Also

- [Primary Keys](specs/primary-keys.md) — Key determination rules
- [Type System](specs/type-system.md) — Type architecture
- [Codec API](specs/codec-api.md) — Custom types
