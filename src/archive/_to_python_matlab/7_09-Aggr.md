---
title: Aggr
---

Without the argument `other`, `aggr` and
`proj` are exactly equivalent.

Aggregation functions can only be used in
the definitions of new attributes within the `aggr` operator.

As with `proj`, the output of `aggr` has the same entity class, the same
primary key, and the same number of elements as `tab`. Primary key
attributes are always included in the output and may be renamed, just
like in `proj`.

# Examples

=== "Python"

    ``` python
    # Number of students in each course section
    Section.aggr(Enroll, n="count(*)")
    # Average grade in each course
    Course.aggr(Grade * LetterGrade, avg_grade="avg(points)")
    ```

=== "Matlab"

    ``` matlab
    % Number of students in each course section
    university.Section.aggr(university.Enroll, 'count(*)->n')
    % Average grade in each course
    university.Course.aggr(university.Grade * university.LetterGrade, 'avg(points)->avg_grade')
    ```

