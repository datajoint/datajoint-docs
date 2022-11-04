## Referential integrity

Dependencies enforce the desired property of databases known as
**referential integrity**. Referential integrity is the guarantee made
by the data management process that related data across the database
remain present, correctly associated, and mutually consistent.
Guaranteeing referential integrity means enforcing the constraint that
no entity can exist in the database without all the other entities on
which it depends. An entity in table `B` depends on an entity in table
`A` when they belong to them or are computed from them.

## Dependencies with renamed attributes

In most cases, a dependency includes the primary key attributes of the
referenced table as they appear in its table definition. Sometimes it
can be helpful to choose a new name for a foreign key attribute that
better fits the context of the dependent table. DataJoint provides the
following `projection <proj>` syntax to rename the primary key
attributes when they are included in the new table.

The dependency

``` text
->  Table.project(new_attr='old_attr')
```

renames the primary key attribute `old_attr` of `Table` as `new_attr`
before integrating it into the table definition. Any additional primary
key attributes will retain their original names. For example, the table
`Experiment` may depend on table `User` but rename the `user` attribute
into `operator` as follows:

``` text
-> User.proj(operator='user')
```

In the above example, an entity in the dependent table depends on
exactly one entity in the referenced table. Sometimes entities may
depend on multiple entities from the same table. Such a design requires
a way to distinguish between dependent attributes having the same name
in the reference table. For example, a table for `Synapse` may reference
the table `Cell` twice as `presynaptic` and `postsynaptic`. The table
definition may appear as

``` text
## synapse between two cells
-> Cell.proj(presynaptic='cell_id')
-> Cell.proj(postsynaptic='cell_id')
---
connection_strength : double  ## (pA) peak synaptic current
```

If the primary key of `Cell` is (`animal_id`, `slice_id`, `cell_id`),
then the primary key of `Synapse` resulting from the above definition
will be (`animal_id`, `slice_id`, `presynaptic`, `postsynaptic`).
Projection always returns all of the primary key attributes of a table,
so `animal_id` and `slice_id` are included, with their original names.

Note that the design of the `Synapse` table above imposes the constraint
that the synapse can only be found between cells in the same animal and
in the same slice.

Allowing representation of synapses between cells from different slices
requires the renamimg of `slice_id` as well: .. code-block:: text

> \## synapse between two cells -\> Cell(presynaptic_slice='slice_id',
> presynaptic_cell='cell_id') -\> Cell(postsynaptic_slice='slice_id',
> postsynaptic_cell='cell_id') ---connection_strength : double \## (pA)
> peak synaptic current

In this case, the primary key of `Synapse` will be (`animal_id`,
`presynaptic_slice`, `presynaptic_cell`, `postsynaptic_slice`,
`postsynaptic_cell`). This primary key still imposes the constraint that
synapses can only form between cells within the same animal but now
allows connecting cells across different slices.

In the ERD, renamed foreign keys are shown as red lines with an
additional dot node in the middle to indicate that a renaming took
place.

## Foreign key options

Note:Foreign key options are currently in development.

Foreign keys allow the additional options `nullable` and `unique`, which
can be inserted in square brackets following the arrow.

For example, in the following table definition

``` text
rig_id  : char(4)   ## experimental rig
---
-> Person
```

each rig belongs to a person, but the table definition does not prevent
one person owning multiple rigs. With the `unique` option, a person may
only appear once in the entire table, which means that no one person can
own more than one rig.

``` text
rig_id  : char(4)   ## experimental rig
---
-> [unique] Person
```

With the `nullable` option, a rig may not belong to anyone, in which
case the foreign key attributes for `Person` are set to `NULL`:

``` text
rig_id  : char(4)   ## experimental rig
---
-> [nullable] Person
```

Finally with both <span class="title-ref">unique</span> and <span
class="title-ref">nullable</span>, a rig may or may not be owned by
anyone and each person may own up to one rig.

``` text
rig_id  : char(4)   ## experimental rig
---
-> [unique, nullable] Person
```

Foreign keys made from the primary key cannot be nullable but may be
unique.
