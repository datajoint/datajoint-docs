# Concepts

The following conventions describe the DataJoint Python API implementation. 

## DataJoint Schemas

The DataJoint Python API allows creating _database schemas_, which are namespaces for
collections of related tables.

The following commands declare a new schema and create the object named `schema` to
reference the database schema.

=== "Python"

    ```python
    import datajoint as dj
    schema = dj.schema('<schema_name>')
    ```

    We follow the convention of having only one schema defined per Python module. Then
    such a module becomes a _DataJoint schema_ comprising a Python module with a
    corresponding _database schema_.

    The module's `schema` object is then used as the decorator for classes that define
    tables in the database. 

=== "Matlab"

    ```matlab
    dj.createSchema
    ```

    In Matlab, we list one table per file and place schemas in folders.

## Elements

An Element is a software package defining one or more DataJoint schemas serving a
particular purpose. By convention, such packages are hosted in individual GitHub
repositories. For example, Element `element_calcium_imaging` is hosted at
[this GitHub repository](https://github.com/datajoint/element-calcium-imaging) and contains two DataJoint
schemas: `scan` and `imaging`.

### YouTube Tutorials

The following YouTube videos provide information on basic design principles and file organization.

- [Why neuroscientists should use relational databases](https://www.youtube.com/watch?v=q-PMUSC5P5o)
  compared to traditional file hierarchies.
- [Quickstart Guide](https://www.youtube.com/watch?v=5R-qnz37BKU) including 
  terminology, and how to read DataJoint Diagrams and DataJoint Python table 
  definitions.
- [Intro to the Element and Workflow files](https://www.youtube.com/watch?v=tat9MSjkH_U)
  for an overview of the respective GitHub repositories.
- [Overview of upstream Elements](https://www.youtube.com/watch?v=NRqpKNoHEY0) to 
  ingest and explore Lab, Animal, and Session metadata. 

???+ Note

    Some videos feature outdated versions of the respective GitHub repositories. For the
    most updated information, check the
    [documentation page](../) for the corresponding Element.

### Deferred schemas

A _deferred schema_ is one in which the name of the database schema name is not specified.
This module does not declare schema and tables upon import.
Instead, they are declared by calling `schema.activate('<schema_name>')` after import.

By convention, all modules corresponding to deferred schema must declare the function
`activate` which in turn calls `schema.activate`.

Thus, Element modules begin with:

```python
import datajoint as dj
schema = dj.schema()

def activate(schema_name):
schema.activate(schema_name)
```

However, many activate functions perform other work associated with activating the
schema such as activating other schemas upstream.

### Linking Module

To make the code more modular with fewer dependencies, Element modules do not `import`
upstream schemas directly. Instead, all required classes and functions must be defined
in a `linking_module` and passed to the module's `activate` function. By keeping all
upstream requirements in the linking module, all Elements can be activated as part of
any larger pipeline.

For instance, the 
[Scan module](https://github.com/datajoint/element-calcium-imaging/blob/main/element_calcium_imaging/scan.py)
receives its required functions from the linking module passed into the module's
`activate` function. See the 
[example notebooks](https://github.com/datajoint/element-calcium-imaging/)
for an example of how the linking module is passed into the Element's module.
