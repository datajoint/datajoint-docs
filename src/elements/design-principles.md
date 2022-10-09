# Design Principles

The following conventions describe the Python implementation. Matlab conventions are similar and will be described separately.

## DataJoint Schemas

DataJoint allows creating _database schemas_, which are namespaces for collections of related tables.

The following commands declare a new schema and create the object named `schema` to reference the database schema.

```python
import datajoint as dj
schema = dj.schema('<schema_name>')
```

We follow the convention of having only one schema defined per Python module.
Then such a module becomes a "DataJoint schema" comprising a python module with a corresponding database schema.

The module's `schema` object is then used as the decorator for classes that define tables in the database.

## Elements

An Element is a software package defining one or more DataJoint schemas serving a particular purpose.
By convention, such packages are hosted in individual GitHub repositories.
For example, Element `element_calcium_imaging` is hosted at https://github.com/datajoint/element-calcium-imaging,
and contains two DataJoint schemas: `scan` and `imaging`.

### Deferred schemas

A _deferred schema_ is one in which the name of the database schema name is not specified.
This module does not declare schema and tables upon import.
Instead, they are declared by calling `schema.activate('<schema_name>')` after import.

By convention, all modules corresponding to deferred schema must declare the function `activate` which in turn calls `schema.activate`.

Thus Element modules begin with

```python
import datajoint as dj
schema = dj.schema()

def activate(schema_name):
	schema.activate(schema_name)
```

However, many activate functions perform other work associated with activating the schema such as activating other schemas upstream.

### Linking Module

To make the code more modular with fewer dependencies, Elements' modules do not `import` upstream schemas directly. 
Instead, all required classes and functions must be defined in a `linking_module` and passed to the module's `activate` function.

For instance, the [`element_calcium_imaging.scan`](https://github.com/datajoint/element-calcium-imaging/blob/main/element_calcium_imaging/scan.py) module receives
its required functions from the linking module passed into the module's `activate` function.
See the [corresponding workflow](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/pipeline.py) for an example of how the linking module is passed into the Element's module.
