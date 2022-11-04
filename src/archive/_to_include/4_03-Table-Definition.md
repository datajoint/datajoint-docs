---
title: Table Definition
---

DataJoint models data as sets of **entities** with shared
**attributes**, often visualized as tables with rows and columns. Each
row represents a single entity and the values of all of its attributes.
Each column represents a single attribute with a name and a datatype,
applicable to entity in the table. Unlike rows in a spreadsheet,
entities in DataJoint don't have names or numbers: they can only be
identified by the values of their attributes. Defining a table means
defining the names and datatypes of the attributes as well as the
constraints to be applied to those attributes. Both MATLAB and Python
use the same syntax define tables.

For example, the following code in defines the table `User`, that
contains users of the database:

=== "Python"

   The table definition is contained in the `definition` property of the
   class.

   ``` python
      @schema
      class User(dj.Manual):
          definition = """
          # database users
          username : varchar(20)   # unique user name
          ---
          first_name : varchar(30)
          last_name  : varchar(30)
          role : enum('admin', 'contributor', 'viewer')
          """
   ```

=== "Matlab"

   The table definition is contained in the first block comment in the
   class definition file. Note that although it looks like a mere comment,
   the table definition is parsed by DataJoint. This solution is thought to
   be convenient since MATLAB does not provide convenient syntax for
   multiline strings.

   ``` matlab
      %{
      # database users
      username : varchar(20)   # unique user name
      ---
      first_name : varchar(30)
      last_name  : varchar(30)
      role : enum('admin', 'contributor', 'viewer')
      %}
      classdef User < dj.Manual
      end
   ```

This defines the class `User` that creates the table in the database and
provides all its data manipulation functionality.

# Table creation on the database server

=== "Python"

   Users do not need to do anything special to have a table created in the
   database. Tables are created at the time of class definition. In fact,
   table creation on the database is one of the jobs performed by the
   decorator `@schema` of the class.

=== "Matlab"

   Users do not need to do anything special to have the table created in
   the database. The table is created upon the first attempt to use the
   class for manipulating its data (e.g. inserting or fetching entities).

# Changing the definition of an existing table

Once the table is created in the database, the definition string has no
further effect. In other words, changing the definition string in the
class of an existing table will not actually update the table
definition. To change the table definition, one must first `drop <drop>`
the existing table. This means that all the data will be lost, and the
new definition will be applied to create the new empty table.

Therefore, in the initial phases of designing a DataJoint pipeline, it
is common to experiment with variations of the design before populating
it with substantial amounts of data.

It is possible to modify a table without dropping it. This topic is
covered separately.

# Reverse-engineering the table definition

DataJoint objects provide the `describe` method, which displays the
table definition used to define the table when it was created in the
database. This definition may differ from the definition string of the
class if the definition string has been edited after creation of the
table.

## Examples

=== "Python"

   ``` python
      s = lab.User.describe()
   ```

=== "Matlab"

   ``` matlab
      s = describe(lab.User)
   ```

=== "Python"

=== "Matlab"

   Furthermore, DataJoint provides the `syncDef` method to update the
   `classdef` file definition string for the table with the definition in
   the actual table:

   ``` matlab
      syncDef(lab.User)    % updates the table definition in file +lab/User.m
   ```

