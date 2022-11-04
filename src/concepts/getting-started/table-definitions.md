# Table Definitions

DataJoint models data as sets of **entities** (rows) with shared **attributes**
(columns or fields). These are visualized as tables with rows and columns. Each row
represents a single entity and the values of all of its attributes. Each column
represents a single attribute with a name and a datatype. Unlike rows in a spreadsheet,
entities in DataJoint don't have names or numbers: they can only be identified by the
values of their attributes. Defining a table means defining the names and datatypes of
the attributes as well as the constraints to be applied to those attributes.

To make it easy to work with tables in Python and Matlab, DataJoint APIs create a
separate class for each table[^1]. For example, the class `experiment.Subject` in the
DataJoint client language may correspond to the table called `subject` on the database
server. Each table class must inherit from one of the 
[table tier](../reproduce/table-tiers/) classes.

[^1]: Computer programmers refer to this concept as 
[object-relational mapping](https://en.wikipedia.org/wiki/Object-relational_mapping). 

??? Note "Valid table names" 
    
    Note that in both MATLAB and Python, the class names must follow the CamelCase
    compound word notation:

    -   start with a capital letter and
    -   contain only alphanumerical characters (no underscores).

    Examples of valid class names:

    `TwoPhotonScan`, `Scan2P`, `Ephys`, `MembraneVoltage`

    Invalid class names:

    `Two_photon_Scan`, `twoPhotonScan`, `2PhotonScan`, `membranePotential`,
    `membrane_potential`

## Table Definition Syntax

Both MATLAB and Python use the same syntax define tables. A table definition consists of
one or more lines. Each line can be one of the following:

-   `#`: The optional first line may provide a description
    of the table's purpose. 

-   A field (i.e., attribute) definition can take any of the following forms (see
    also [valid datatypes](../query-lang/data-types)):

    - `name : datatype` 
    - `name : datatype # comment`
    - `name = default : datatype` 
    - `name = default : datatype  # comment`

-   The divider `---` (at least three hyphens) separates 
    [primary key attributes](../../../glossary#primary-key) above from 
    [secondary attributes](../../../glossary#seconday-attributes) below.

-   A [foreign key](../../../glossary#foreign-key) in the format `-> ReferencedTable`.

For example, the table for Persons may have the following definition:

``` text
# Persons in the lab
username :  varchar(16)   #  username in the database
---
full_name  : varchar(255)
start_date :  date   # date when joined the lab
```
```text      
    # Mice
    mouse_id: int            # unique mouse id
    ---
    dob: date                # mouse date of birth
    sex: enum('M', 'F', 'U') # sex of mouse - Male, Female, or Unknown
``` 

This will define the table with attributes `mouse_id`, `dob`, and
`sex`, in which `mouse_id` is the [primary key](../../../glossary#primary-key).

### Attribute names

Attribute names must be in lowercase and must start with a letter. They
can only contain alphanumerical characters and underscores. The
attribute name cannot exceed 64 characters.

??? Note "Valid attribute names"

    Attribute names should appear in
    [snake case](https://en.wikipedia.org/wiki/Snake_case), with underscores and not 
    spaces. 

    - Valid attribute names: `first_name`, `two_photon_scan`, `scan_2p`, 
        `two_photon_scan_`
    - Invalid attribute names: `firstName`, `first name`, `2photon_scan`, 
        `two-photon_scan`, `TwoPhotonScan`

Ideally, attribute names should be unique across all tables that are likely to be used
in queries together. For example, tables often have attributes representing the start
times of sessions, recordings, etc. Such attributes must be uniquely named in each
table, such as `session_start_time` or `recording_start_time`.

### Default values

Secondary attributes can be given default values. A default value will be used for an
attribute if no other value is given at the time the entry is 
[inserted](../query-lang/common-commands#insert) into the table. Generally, default 
values are numerical values or character strings. Default values for dates must be given
as strings as well, contained within quotes (with the exception of
`CURRENT_TIMESTAMP`). 
Primary key attributes cannot have default values (with the exceptions of
`auto_increment` and `CURRENT_TIMESTAMP` attributes; see 
[primary keys](../query-lang/primary-key]).

An attribute with a default value of `NULL` is called a **nullable attribute**, which
may be absent in some entities. Nullable attributes should *not* be used to indicate
that an attribute is inapplicable to some entities in a table (see 
[normalization](../query-lang/normalization)). Nullable attributes should be used
sparingly to indicate optional rather than inapplicable attributes that still apply to
all entities in the table. `NULL` is a special literal value and does not need to be
enclosed in quotes.

Here are some examples of attributes with default values:

``` text
    failures = 0 : int
    due_date = "2020-05-31" : date
    additional_comments = NULL : varchar(256)
```

## Changing the Definition

Once the table is created in the database, the definition string has no effect.
Just changing the definition string in the
class of an existing table will make any corresponding changes on the database
definition. 

To change the table in the database, one can either...

1. [Drop](..query-lang/common-commands#drop) the existing table, deleting the
entire contents, and then declare a new adjusted table.

2. Or alter the table definition. Altering is limited to 
[seconday attributes](../../../glossary#seconday-attribute) and should be done with 
caution, as it may impact existing data.

In the initial phases of designing a pipeline, it's best to experiment with variations
of the design before populating it with substantial amounts of data.


# Reverse-engineering the Definition

DataJoint objects provide the `describe` method, which displays the table definition
used to define the table when it was created in the database. This definition may
differ from the definition string of the class if the definition string has been edited
after creation of the table (see above).

=== "Python"

   ``` python
      s = lab.User.describe()
   ```

=== "Matlab"

   ``` matlab
      s = describe(lab.User)
