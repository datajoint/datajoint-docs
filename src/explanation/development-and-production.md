# Development and Production

A DataJoint pipeline is worked on in two different ways over its life. While it is
being built, its developers change it freely: they declare a table, populate it,
look at the results, change the definition, drop the table, and declare it again.
Once others depend on it, the same freedom becomes a hazard: a change made in
passing reaches everyone who reads its data or computes from it.

This page derives the two ways of working, **development** and **production**, from
what a pipeline holds. The lifecycle that connects them, and the recommendations for
each, are specified in
[Pipeline Lifecycle and Deployment](../reference/specs/deploy-operations.md).

## Definition and data

A pipeline holds two kinds of state.

Its **definition** says what the pipeline is:

- the tables, their attributes, keys and dependencies, as declared in code;
- the `make()` method of each auto-populated table, which says how its rows are
  computed;
- the contents of its Lookup tables, which the standard below treats as part of the
  code (a Lookup's `contents`), because the rest of the pipeline's code depends on
  those values.

Its **data** is what the pipeline holds at a given moment: the rows of its Manual,
Imported and Computed tables and their parts.

In SQL terms, changing the definition is mostly **DDL** (declaring, altering and
dropping tables), and changing data is **DML** (inserting and deleting rows). The
correspondence is not exact. Writing a Lookup table's rows is DML, but the standard
counts it as a change to the definition. Changing a `make()` method runs no SQL at
all, yet it changes what every row of its table means.

## Why the two are kept apart

DataJoint's guarantees connect data to definition. A computed row is valid because
it was computed by its table's `make()` from rows that still exist, under the
definition that declared them. When a row upstream is deleted, the delete cascades
to everything computed from it, so the pipeline never holds a result whose inputs
are gone.

Changes to the definition don't reach existing rows that way:

- Changing a `make()` leaves every row computed by the old code in place. By
  default, nothing on a row tells old rows from new ones.
- Adding a Lookup row, or changing a non-key value in one, leaves the rows computed
  from the old values as they were.
- Altering an attribute's type rewrites stored values. Dropping a table deletes its
  rows and everything that depends on them.
- Tables are declared when their classes are decorated, usually at import. Renaming
  a class in the code therefore declares a new, empty table instead of failing.

While only the developers use the pipeline, these effects are what they want: they
are the fast loop of change, populate and compare, which makes DataJoint productive.
Once others depend on the pipeline, the same effects reach them unannounced, in the
middle of their work. People entering data, jobs computing results, and readers of
reported results each see the pipeline change underneath them.

## Two ways of working

What separates the two modes is **when the definition may change, and by whom**.

In **development**, the definition and the data may change together, from any
process. This suits a pipeline that only its developers depend on, and it is how
DataJoint behaves on its own: tables are declared as their classes are decorated,
`alter()` and `drop()` change the definition directly, and `delete()` asks before
committing.

In **production**, the definition changes only in a **deployment step**, planned and
applied as one, before the code that needs the change starts. Everything else that
uses the pipeline, which the specification calls **run time** (workers, notebooks,
dashboards, scripts), changes only data. Computed tables are populated only by
dedicated **workers** running a fresh, clean checkout of the deployed commit, so the code
version recorded with each computed row is exactly the code that computed it.

A change to a production pipeline is designed on a temporary **development
pipeline**, declared from production's deployed code for that change: in a separate
database, on a copy-on-write branch of the production database (a copy that shares
production's stored data until either side changes it), or in memory, where the
tooling supports it. There the definition and the data change together, as in any
development work. Its product is verified code, not data: the change is reviewed and
merged, released once each `make()` is checked against the reproducibility contract,
and applied to production by a deployment step, the only step that runs DDL there.

Data moves mostly one way. Production rows may be copied into a development pipeline
to try a change on real data. Computed rows from development are never copied into
production, because nothing on them says which code computed them, or whether that
code ever shipped; production computes its own rows, in workers, from the deployed
commit. Manual rows are different: they hold data entered from outside, and a
development pipeline, even one that keeps running, can serve production as an outside
source, entered through production's entry path with the source recorded. The
specification lists what to watch for when doing so.

The mode belongs to a **target**, one database that a pipeline runs on, not to the
code, and a target keeps its mode for as long as it exists. The same code can run in
development on a scratch database and in production on the pipeline's production
target. A development pipeline therefore never becomes the production pipeline: the
production pipeline is declared empty, from the committed code, by its first
deployment step, and fills only through production's own paths, under production's
controls from its first row.

Changes to a production pipeline come in two kinds. An **additive** change extends
the pipeline without touching what exists, such as a new table, so running code
keeps working and no existing row changes. A **revising** change alters what
exists, such as a dropped attribute, a changed `make()` or a changed Lookup row, so
it is reviewed, and the work that depends on it is paused while it is applied. In
development, both kinds are simply applied. The two kinds, and how provenance, the
`make()` reproducibility contract and Lookup seeding differ between the modes, are
specified in [Pipeline Lifecycle and Deployment](../reference/specs/deploy-operations.md#additive-and-revising-changes).

## How the modes are upheld

DataJoint is designed to uphold the two modes. Everything it does on its own suits
development, and everything it does at run time can be prepared for ahead of time,
so that a production target needs no privilege at run time beyond changing data.
Enforcement comes from the database's privileges, not from a DataJoint setting: a
run-time login that cannot change the definition keeps it from changing, whatever
code runs.

Development is what DataJoint does by default, and it is how most DataJoint
pipelines have been operated, including many that others depend on. The production
conventions are new, and nothing requires a pipeline to adopt them. A pipeline may
stay in development for its whole life, as long as those who use it accept that its
definition may change underneath them and that its rows carry none of production's
guarantees. A pipeline that wants those guarantees gets them in a new production
pipeline, declared from its code; it is not converted in place.

The recommendations are a standard that individual deployments can vary. A team
serving many users may add review, approval and scheduled windows to its deployment
step.

## See also

- [Pipeline Lifecycle and Deployment](../reference/specs/deploy-operations.md): the
  rule, the lifecycle, the recommendations and the deployment step
- [Deploy to Production](../how-to/deploy-production.md): configuration for a
  production target
- [Delete Data](../how-to/delete-data.md): previewing a delete, and the prompt that
  holds its transaction open
- [Alter Tables](../how-to/alter-tables.md): changing a table's definition
- [Computation Model](computation-model.md): how computed rows depend on their
  inputs and their `make()`
