
# Defining a table

=== "Python"

   To define a DataJoint table in Python:

   1.  Define a class inheriting from the appropriate DataJoint class:
       `dj.Lookup`, `dj.Manual`, `dj.Imported` or `dj.Computed`.
   2.  Decorate the class with the schema object (see `schema`)
   3.  Define the class property `definition` to define the table heading.

   For example, the following code defines the table `Person`:

   ``` python
      import datajoint as dj
      schema = dj.Schema('alice_experiment')

      @schema
      class Person(dj.Manual):
          definition = '''
      		username : varchar(20)   # unique user name
          ---
          first_name : varchar(30)
          last_name  : varchar(30)
          '''
   ```

   The `@schema` decorator uses the class name and the data tier to check
   whether an appropriate table exists on the database. If a table does not
   already exist, the decorator creates one on the database using the
   definition property. The decorator attaches the information about the
   table to the class, and then returns the class.

   The class will become usable after you define the `definition` property
   as described in `definitions`.

   ## DataJoint classes in Python

   DataJoint for Python is implemented through the use of classes providing
   access to the actual tables stored on the database. Since only a single
   table exists on the database for any class, interactions with all
   instances of the class are equivalent. As such, most methods can be
   called on the classes themselves rather than on an object, for
   convenience. Whether calling a DataJoint method on a class or on an
   instance, the result will only depend on or apply to the corresponding
   table. All of the basic functionality of DataJoint is built to operate
   on the classes themselves, even when called on an instance. For example,
   calling `Person.insert(...)` (on the class) and `Person.insert(...)` (on
   an instance) both have the identical effect of inserting data into the
   table on the database server. DataJoint does not prevent a user from
   working with instances, but the workflow is complete without the need
   for instantiation. It is up to the user whether to implement additional
   functionality as class methods or methods called on instances.

=== "Matlab"

   DataJoint provides the interactive script `dj.new` for creating a new
   table. It will prompt to enter the new table's class name in the form
   `package.ClassName`. This will create the file `+package/ClassName.m`.

   For example, define the table `experiment.Person`

   ``` matlab
      >> dj.new
      Enter <package>.<ClassName>: experiment.Person

      Choose table tier:
        L=lookup
        M=manual
        I=imported
        C=computed
        P=part
       (L/M/I/C/P) > M
   ```

   This will create the file `+experiment/Person.m` with the following
   contents:

   ``` matlab
      %{
      # my newest table
      # add primary key here
      -----
      # add additional attributes
      %}

      classdef Person < dj.Manual
      end
   ```

   While `dj.new` adds a little bit of convenience, some users may create
   the classes from scratch manually.

   Each newly created class must inherit from the DataJoint class
   corresponding to the correct `data tier <tiers>`: `dj.Lookup`,
   `dj.Manual`, `dj.Imported` or `dj.Computed`.

   The most important part of the table definition is the comment preceding
   the `classdef`. DataJoint will parse this comment to define the table.

   The class will become usable after you edit this comment as described in
   `definitions`.

