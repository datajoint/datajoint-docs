---
title: Universal Sets
---

For example, you may like to query the university database for the
complete list of students' home cities, along with the number of
students from each city. The `schema <query-example>` for the university
database does not have a table for cities and states. A virtual table
can fill the role of the nonexistent base table, allowing queries that
would not be possible otherwise.

=== "Python"

    ``` python
    # All home cities of students
    dj.U('home_city', 'home_state') & Student

    # Total number of students from each city
    dj.U('home_city', 'home_state').aggr(Student, n="count(*)")

    # Total number of students from each state
    U('home_state').aggr(Student, n="count(*)")

    # Total number of students in the database
    U().aggr(Student, n="count(*)")
    ```

=== "Matlab"

    Note: `dj.U` is not yet implemented in MATLAB. The feature will be added in an
    upcoming release:
    <https://github.com/datajoint/datajoint-matlab/issues/144>

    ``` matlab
    % All home cities of students
    dj.U('home_city', 'home_state') & university.Student

    % Total number of students from each city
    aggr(dj.U('home_city', 'home_state'), university.Student, 'count(*)->n')

    % Total number of students from each state
    aggr(U('home_state'), university.Student, 'count(*)->n')

    % Total number of students in the database
    aggr(U(), university.Student, 'count(*)->n')
    ```

The result of aggregation on a universal set is restricted to the
entities with matches in the aggregated table, such as `Student` in the
example above. In other words, `X.aggr(A, ...)` is interpreted as
`(X & A).aggr(A, ...)` for universal set `X`. All attributes of a
universal set are considered primary.

Universal sets should be used sparingly when no suitable base tables
already exist. In some cases, defining a new base table can make queries
clearer and more semantically constrained.
