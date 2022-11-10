# Mantra

The *DataJoint Mantra* consists of three main objectives:

- Simplify your data queries through an intuitive [query language](./#query-language).
- Make automated, [reproducible computation](./#reproducible-computation) by integrating
  computation with the data model.
- Ensure validity of your data through [referential integrity](./#referential-integrity).

## Query Language

Writing good, optimized SQL queries can be
difficult and often becomes a barrier for individuals lacking experience in
computer science and programming.
That said, we don't feel this should discourage the use of databases. Databases help to
structure our daily lives which streamlines the time required to glean insights and
build robust applications from truth. SQL is
powerful but requires practice which we feel is the real fault in the language.

To address this, the DataJoint query language serves as a query builder and optimizer
for SQL. It leverages the stack's own operator
precedence and combines it with both operator overloading and 
SQL algebra to achieve a more intuitive experience.
Additionally, interoperability between Python and MATLAB is crucial due to the
diversity of tools available to scientists. So much so that this is a guiding principle
in [FAIR](https://www.go-fair.org/fair-principles/).

Case in point, here is a comparison of equivalent queries:

*SQL*:

```sql
SELECT *
FROM `shapes`.`rectangle`
NATURAL JOIN `shapes`.`area`
WHERE (
    (`shape_area`=8) AND (`shape_height`=2)
);
```

=== "*DataJoint (Python)*"

    ```python
    Rectangle * Area & dict(shape_height=2, shape_area=8)
    ```

=== "*DataJoint (MATLAB)*"

    ```matlab
    shapes.Rectangle * shapes.Area & struct('shape_height', 2, 'shape_area', 8)
    ```

## Reproducible Computation

Reproducibility is a key concept within the scientific community since research is
largely conducted, shared, and reviewed in the public domain. This is necessary to
independently validate discoveries and have others support new findings. Such a
practice is well advocated in the scientific community as open science.

Yet, reliably reproducing computed results of others has proven difficult since there
are many factors that affect the determinism of a process e.g. hardware, software
environment, scripts, input data, seeding, etc.

DataJoint pipelines address these challenges by allowing computation to be defined such
that they are associated *with* an entity. Drawing relationships between many entities
we can create a [DAG](../../glossary#dag) that
describes a compute workflow as an 
[entity-relationship model](https://en.wikipedia.org/wiki/Entity%E2%80%93relationship_model).

For instance, an entity such as `Area` could represent the computed value of a parent
entity, `Rectangle`. Therefore, we feel it should be reasonable when defining `Area` to
include the specification of a computation that automates how `Area` is generated based
on relation to `Rectangle`.

## Referential Integrity

Referential integrity is the concept of keeping all your data consistent and up-to-date.
The goal is to ensure [data pipelines](../../glossary#data-pipeline) always reflect the
truth of how data was created.

In the realm of databases, entities can be related to one another through 
[foreign keys](../../glossary#foreign-key). However, our opinionated view
is that foreign keys on [primary keys](../../glossary#primary-key) should
enforce the contraint.

What this means is that our data model always reflects the truth. When a parent entity
is removed, all child computed values will also be removed since they no longer have
meaning without the subject. There is not a clear way to reproduce the results
otherwise.

An important consequence to note is that deletes take longer as a result since they must
be cascaded down to all the descendants. We believe this to be a feature as it is the
behavior most inline with typical expectations. Deletes should be done cautiously. 
