---
title: Creating Schemas
---

# Schemas

On the database server, related tables are grouped into a named
collection called a **schema**. This grouping organizes the data and
allows control of user access. A database server may contain multiple
schemas each containing a subset of the tables. A single pipeline may
comprise multiple schemas. Tables are defined within a schema, so a
schema must be created before the creation of any tables.

=== "Python"

    <div class="note">

    <div class="title">

    Note: By convention, the `datajoint` package is imported as `dj`. The
    documentation refers to the package as `dj` throughout.

    </div>

    Create a new schema using the `dj.Schema` class object:

    ``` python
    import datajoint as dj
    schema = dj.Schema('alice_experiment')
    ```

    This statement creates the database schema `alice_experiment` on the
    server.

    The returned object `schema` will then serve as a decorator for
    DataJoint classes, as described in `table`.

    It is a common practice to have a separate Python module for each
    schema. Therefore, each such module has only one `dj.Schema` object
    defined and is usually named `schema`.

    The `dj.Schema` constructor can take a number of optional parameters
    after the schema name.

    -   `context` - Dictionary for looking up foreign key references.
        Defaults to `None` to use local context.
    -   `connection` - Specifies the DataJoint connection object. Defaults
        to `dj.conn()`.
    -   `create_schema` - When `False`, the schema object will not create a
        schema on the database and will raise an error if one does not
        already exist. Defaults to `True`.
    -   `create_tables` - When `False`, the schema object will not create
        tables on the database and will raise errors when accessing missing
        tables. Defaults to `True`.

=== "Matlab"

    A schema can be created either automatically using the `dj.createSchema`
    script or manually. While `dj.createSchema` simplifies the process, the
    manual approach yields a better understanding of what actually takes
    place, so both approaches are listed below.

    ## Manual

    **Step 1.** Create the database schema

    Use the following command to create a new schema on the database server:

    ``` matlab
    query(dj.conn, 'CREATE SCHEMA `alice_experiment`')
    ```

    Note that you must have create privileges for the schema name pattern
    (as described in `hosting`). It is a common practice to grant all
    privileges to users for schemas that begin with the username, in
    addition to some shared schemas. Thus the user `alice` would be able to
    perform any work in any schema that begins with `alice_`.

    **Step 2.** Create the MATLAB package

    DataJoint organizes schemas as MATLAB **packages**. If you are not
    familiar with packages, please review:

    -   [How to work with MATLAB
        packages](https://www.mathworks.com/help/matlab/matlab_oop/scoping-classes-with-packages.html)
    -   [How to manage MATLAB's search
        paths](https://www.mathworks.com/help/matlab/search-path.html)

    In your project directory, create the package folder, which must begin
    with a `+` sign. For example, for the schema called `experiment`, you
    would create the folder `+experiment`. Make sure that your project
    directory (the parent directory of your package folder) is added to the
    MATLAB search path.

    **Step 3.** Associate the package with the database schema

    This step tells DataJoint that all classes in the package folder
    `+experiment` will work with tables in the database schema
    `alice_experiment`. Each package corresponds to exactly one schema. In
    some special cases, multiple packages may all relate to a single
    database schema, but in most cases there will be a one-to-one
    relationship between packages and schemas.

    In the `+experiment` folder, create the file `getSchema.m` with the
    following contents:

    ``` matlab
    function obj = getSchema
    persistent OBJ
    if isempty(OBJ)
        OBJ = dj.Schema(dj.conn, 'experiment', 'alice_experiment');
    end
    obj = OBJ;
    end
    ```

    This function returns a persistent object of type `dj.Schema`,
    establishing the link between the `experiment` package in MATLAB and the
    schema `alice_experiment` on the database server.

    ## Automatic

    Alternatively, you can execute

    ``` matlab
    >> dj.createSchema
    ```

    This automated script will walk you through the steps 1--3 above and
    will create the schema, the package folder, and the `getSchema` function
    in that folder.
