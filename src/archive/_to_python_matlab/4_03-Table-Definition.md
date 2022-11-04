# Table Definition

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

   Furthermore, DataJoint provides the `syncDef` method to update the
   `classdef` file definition string for the table with the definition in
   the actual table:

   ``` matlab
      syncDef(lab.User)    % updates the table definition in file +lab/User.m
   ```

