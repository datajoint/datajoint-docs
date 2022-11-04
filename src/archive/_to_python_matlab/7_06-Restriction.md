---
title: Restriction
---


# Restriction by a table

When restricting table `A` with another table, written `A & B`, the two
tables must be **join-compatible** (see `join-compatible`). The result
will contain all entities from `A` for which there exist a matching
entity in `B`. Exclusion of table `A` with table `B`, or `A - B`, will
contain all entities from `A` for which there are no matching entities
in `B`.

<figure>
<img src="../_static/img/restrict-example1.png" class="align-center"
width="546" alt="Restriction by another table." />
<figcaption aria-hidden="true">Restriction by another
table.</figcaption>
</figure>

<figure>
<img src="../_static/img/diff-example1.png" class="align-center"
width="539" alt="Exclusion by another table." />
<figcaption aria-hidden="true">Exclusion by another table.</figcaption>
</figure>

## Restriction by a table with no common attributes

Restriction of table `A` with another table `B` having none of the same
attributes as `A` will simply return all entities in `A`, unless `B` is
empty as described below. Exclusion of table `A` with `B` having no
common attributes will return no entities, unless `B` is empty as
described below.

<figure>
<img src="../_static/img/restrict-example2.png" class="align-center"
width="571" alt="Restriction by a table having no common attributes." />
<figcaption aria-hidden="true">Restriction by a table having no common
attributes.</figcaption>
</figure>

<figure>
<img src="../_static/img/diff-example2.png" class="align-center"
width="571" alt="Exclusion by a table having no common attributes." />
<figcaption aria-hidden="true">Exclusion by a table having no common
attributes.</figcaption>
</figure>

## Restriction by an empty table

Restriction of table `A` with an empty table will return no entities
regardless of whether there are any matching attributes. Exclusion of
table `A` with an empty table will return all entities in `A`.

<figure>
<img src="../_static/img/restrict-example3.png" class="align-center"
width="563" alt="Restriction by an empty table." />
<figcaption aria-hidden="true">Restriction by an empty
table.</figcaption>
</figure>

<figure>
<img src="../_static/img/diff-example3.png" class="align-center"
width="571" alt="Exclusion by an empty table." />
<figcaption aria-hidden="true">Exclusion by an empty table.</figcaption>
</figure>

# Restriction by a mapping

A key-value mapping may be used as an operand in restriction. For each
key that is an attribute in `A`, the paired value is treated as part of
an equality condition. Any key-value pairs without corresponding
attributes in `A` are ignored.

Restriction by an empty mapping or by a mapping with no keys matching
the attributes in `A` will return all the entities in `A`. Exclusion by
an empty mapping or by a mapping with no matches will return no
entities.

For example, let's say that table `Session` has the attribute
`session_date` of `datatype <datatypes>` `datetime`. You are interested
in sessions from January 1st, 2018, so you write the following
restriction query using a mapping.

=== "Python"

    ``` python
    Session & {'session_dat': "2018-01-01"}
    ```

=== "Matlab"

    ``` matlab
    ephys.Session & struct('session_dat', '2018-01-01')
    ```

Our mapping contains a typo omitting the final `e` from `session_date`,
so no keys in our mapping will match any attribute in `Session`. As
such, our query will return all of the entities of `Session`.

# Restriction by a string

Restriction can be performed when `cond` is an explicit condition on
attribute values, expressed as a string. Such conditions may include
arithmetic operations, functions, range tests, etc. Restriction of table
`A` by a string containing an attribute not found in table `A` produces
an error.

=== "Python"

    ``` python
    # All the sessions performed by Alice
    Session & 'user = "Alice"'

    # All the experiments at least one minute long
    Experiment & 'duration >= 60'
    ```

=== "Matlab"

    ``` matlab
    % All the sessions performed by Alice
    ephys.Session & 'user = "Alice"'

    % All the experiments at least one minute long
    ephys.Experiment & 'duration >= 60'
    ```

# Restriction by a collection

=== "Python"

    A collection can be a list, a tuple, or a Pandas `DataFrame`.

    ``` python
    # a list:
    cond_list = ['first_name = "Aaron"', 'last_name = "Aaronson"']

    # a tuple:
    cond_tuple = ('first_name = "Aaron"', 'last_name = "Aaronson"')

    # a dataframe:
    import pandas as pd
    cond_frame = pd.DataFrame(
                data={'first_name': ['Aaron'], 'last_name': ['Aaronson']})
    ```

=== "Matlab"

    <div class="warning">

    <div class="title">

    Warning

    </div>

    This section documents future intended behavior in MATLAB, which is
    contrary to current behavior. DataJoint for MATLAB has an open
    [issue](https://github.com/datajoint/datajoint-matlab/issues/128)
    tracking this change.

    </div>

    A collection can be a cell array or structure array. Cell arrays can
    contain collections of arbitrary restriction conditions. Structure
    arrays are limited to collections of mappings, each having the same
    attributes.

    ``` matlab
    % a cell aray:
    cond_cell = {'first_name = "Aaron"', 'last_name = "Aaronson"'}

    % a structure array:
    cond_struct = struct('first_name', 'Aaron', 'last_name', 'Paul')
    cond_struct(2) = struct('first_name', 'Rosie', 'last_name', 'Aaronson')
    ```

When `cond` is a collection of conditions, the conditions are applied by
logical disjunction (logical OR). Thus, restriction of table `A` by a
collection will return all entities in `A` that meet *any* of the
conditions in the collection. For example, if you restrict the `Student`
table by a collection containing two conditions, one for a first and one
for a last name, your query will return any students with a matching
first name *or* a matching last name.

=== "Python"

    ``` python
    Student() & ['first_name = "Aaron"', 'last_name = "Aaronson"']
    ```

    <figure>
    <img src="../_static/img/python_collection.png" class="align-center"
    alt="Restriction by a collection, returning all entities matching any condition in the collection." />
    <figcaption aria-hidden="true">Restriction by a collection, returning
    all entities matching any condition in the collection.</figcaption>
    </figure>

=== "Matlab"

    ``` matlab
    university.Student() & {'first_name = "Aaron"', 'last_name = "Aaronson"'}
    ```

    <figure>
    <img src="../_static/img/matlab_collection.png" class="align-center"
    alt="Restriction by a collection, returning any entities matching any condition in the collection." />
    <figcaption aria-hidden="true">Restriction by a collection, returning
    any entities matching any condition in the collection.</figcaption>
    </figure>

Restriction by an empty collection returns no entities. Exclusion of
table `A` by an empty collection returns all the entities of `A`.

# Restriction by a Boolean expression

=== "Python"

    `A & True` and `A - False` are equivalent to `A`.

    `A & False` and `A - True` are empty.

=== "Matlab"

    `A & true` and `A - false` are equivalent to `A`.

    `A & false` and `A - true` are empty.

=== "Python"

    # Restriction by an `AndList`

    The special function `dj.AndList` represents logical conjunction
    (logical AND). Restriction of table `A` by an `AndList` will return all
    entities in `A` that meet *all* of the conditions in the list.
    `A & dj.AndList([c1, c2, c3])` is equivalent to `A & c1 & c2 & c3`.
    Usually, it is more convenient to simply write out all of the
    conditions, as `A & c1 & c2 & c3`. However, when a list of conditions
    has already been generated, the list can simply be passed as the
    argument to `dj.AndList`.

    Restriction of table `A` by an empty `AndList`, as in
    `A & dj.AndList([])`, will return all of the entities in `A`. Exclusion
    by an empty `AndList` will return no entities.

    # Restriction by a `Not` object

    The special function `dj.Not` represents logical negation, such that
    `A & dj.Not(cond)` is equivalent to `A - cond`.

=== "Matlab"

# Restriction by a query

Restriction by a query object is a generalization of restriction by a
table (which is also a query object), because DataJoint queries always
produce well-defined entity sets, as described in
`entity normalization <normalization>`. As such, restriction by queries
follows the same behavior as restriction by tables described above.

The example below creates a query object corresponding to all the
sessions performed by the user Alice. The `Experiment` table is then
restricted by the query object, returning all the experiments that are
part of sessions performed by Alice.

=== "Python"

    ``` python
    query = Session & 'user = "Alice"'
    Experiment & query
    ```

=== "Matlab"

    ``` matlab
    query = ephys.Session & 'user = "Alice"'
    ephys.Experiment & query
    ```

