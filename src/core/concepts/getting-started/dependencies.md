# Dependencies

Dependencies, in short, are the links between data tables.

In the context of a broader pipeline, individual tables will be related. Individual
fields in one table will derive some of their meaning from entities in other tables.
For example, a subject identifier in a *Session* table will be associated with more
detailed subject-level information in a *Subject* table.

A **foreign key** defines a **dependency** of entities in one table on entities in
another within a schema. Dependencies provide entities in one table with access to data
in another table and establish certain constraints on entities containing a foreign
key. A DataJoint pipeline, including the dependency relationships established by foreign
keys, can be visualized as a graph with nodes and edges, in a [diagram](../diagrams). 

## Defining a dependency

Foreign keys are defined with arrows `->` in the
[table definition](../table-definitions), pointing to another table.

In the example below, there are three [foreign keys](../../../glossary#foreign-key),
including one within the [primary key](../../../glossary#primary-key) above the `---`.

``` text
## brain slice
-> mp.Subject
slice_id        : smallint       ## slice number within subject
---
-> mp.BrainRegion
-> mp.Plane
slice_date        : date                 ## date of the slicing (not patching)
thickness         : smallint unsigned    ## slice thickness in microns
experimenter      : varchar(20)          ## person who performed this experiment
```

You can examine the resulting table heading with the the following command

=== "Python"

    ``` python
    mp.BrainSlice.heading
    ```

=== "Matlab"

    ``` matlab
    show(mp.BrainSlice)
    ```

The heading of `Slice` may look something like

``` text
subject_id          : char(8)            ## experiment subject id
slice_id            : smallint           ## slice number within subject
---
brain_region        : varchar(12)        ## abbreviated name for brain region
plane               : varchar(12)        ## plane of section
slice_date          : date               ## date of the slicing (not patching)
thickness           : smallint unsigned  ## slice thickness in microns
experimenter        : varchar(20)        ## person who performed this experiment
```

This displayed heading reflects the actual attributes in the table. The foreign keys
have been replaced by the primary key attributes of the referenced tables, including
their data types and comments.

??? Note "How it works under the hood"

    The foreign key `-> A` in the definition of table `B` has the following effects:

    1.  The primary key attributes of `A` are made part of `B`'s definition.
    2.  A referential constraint is created in `B` with reference to `A`.
    3.  If one does not already exist, an index is created to speed up
        searches in `B` for matches to `A`. (The reverse search is already
        fast because it uses the primary key of `A`.)

    A referential constraint means that an entity in `B` cannot exist
    without a matching entity in `A`. **Matching** means attributes in `B`
    that correspond to the primary key of `A` must have the same values. An
    attempt to insert an entity into `B` that does not have a matching
    counterpart in `A` will fail. Conversely, deleting an entity from `A`
    that has matching entities in `B` will result in the deletion of those
    matching entities and so forth, recursively, downstream in the pipeline.

When `B` references `A` with a foreign key, one can say that `B`
**depends** on `A`. In DataJoint terms, `B` is the **dependent table**
and `A` is the **referenced table** with respect to the foreign key from
`B` to `A`.

??? Note "Relational database theory"
    
    The usage of the words "depends" and "dependency" here should not be
    confused with the unrelated concept of *functional dependencies* that is
    used to define normal forms.

