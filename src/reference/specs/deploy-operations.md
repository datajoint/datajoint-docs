# Pipeline Lifecycle and Deployment

This document specifies the lifecycle of a DataJoint pipeline across two modes, **development** and **production**, and the **deployment step** that changes a pipeline's definition in production. It then specifies the `datajoint.deploy` module, which holds operations meant for deployment steps.

DataJoint is designed to uphold these modes. Enforcement comes from database privileges, not from a DataJoint setting: DataJoint has no setting that selects a mode, attempts what the code asks, and the server refuses what the login lacks. Everything DataJoint does at run time can be prepared for in a deployment step, so that a production target needs no privilege at run time beyond changing data. The rule, the lifecycle and the recommendations below are a standard for operating a DataJoint pipeline; individual deployments can vary, for example by adding review, approval or scheduled windows to the deployment step, or by keeping a single-developer pipeline in development for its whole life. For the reasoning behind the two modes, see [Development and Production](../../explanation/development-and-production.md).

## Terms

| Term | Meaning |
|---|---|
| **Definition** | What the pipeline is: its tables, attributes, keys and dependencies; the `make()` method of each auto-populated table; and, under this standard, the contents of its Lookup tables |
| **Data** | The rows of its Manual, Imported and Computed tables and their parts |
| **Target** | One database that a pipeline runs on. The mode is a property of a target, not of the code |
| **Pipeline** | The code and its main target. "A pipeline is in production" means its main target is |
| **Run time** | Every process that uses the pipeline other than a deployment step: populate jobs, notebooks, dashboards, scripts |
| **Deployment step** | The one step that changes a production target's definition, before the code that needs the change starts |
| **Development** | A mode in which the definition and the data may change together, from any process |
| **Production** | A mode in which the definition changes only in a deployment step, and run time changes only data |

## The recommended rule

The standard rests on one rule:

> In development, the definition and the data may change together, in any process.
> In production, the definition changes only in a deployment step, planned and applied as one, and run time changes only data.

Changing the definition is mostly DDL (declaring, altering and dropping tables), and changing data is DML (inserting and deleting rows), but the correspondence is not exact. Writing a Lookup table's rows is treated as a change to the definition, and so is changing a `make()` method, which runs no SQL at all.

## The two modes

| | Development | Production |
|---|---|---|
| Who depends on the data | Only the pipeline's developers | Others: people entering data, jobs, readers of results, other pipelines |
| When the definition changes | Any time, from any process: tables declared as their classes are decorated, `alter()`, `drop()` | Only in a deployment step |
| What run time may do | Change both definition and data | Change data only |
| Lookup contents | Edited as needed | Changed only by deployment, with the code |
| Hidden tables (jobs tables, `~lineage`) | Declared by DataJoint as needed | Declared by deployment, ahead of time |
| Deleting data | Interactively, with a prompt | Previewed, then deleted without a prompt |
| Trying a change | On the target itself | On a development target, then deployed |

Some targets stay in development for as long as they exist: a scratch database, the throwaway database a test suite starts, or a copy of a production pipeline used to try a change. A copy made to try a change is a development target of the same pipeline.

## Lifecycle of a pipeline

![The lifecycle of a pipeline. On the left, a gray box labeled Development: definition and data change together, from any process. An arrow labeled "first deployment step", with the note "one-way under this standard", leads right to a blue box labeled Production: definition changes only in a deployment step; run time changes only data. Below Production, a dashed box labeled Development target, where each change is developed, on a copy or a separate database. An arrow from it up to Production is labeled "deployment step", for each change, after review.](../../images/pipeline-lifecycle.svg)

### 1. Development

A pipeline starts in development. Its developers declare, populate, compare, alter, drop and redeclare as they need to. Everything DataJoint does on its own suits this mode.

### 2. Moving to production

A pipeline moves to production when someone outside its developers starts to depend on it: data entered by others, results read by others, or another pipeline built on it. The move is the pipeline's first deployment step:

1. The definition is recorded as code, under version control, at a known version.
2. Every table is declared on the main target, including the hidden tables: the jobs table of each auto-populated table and each schema's `~lineage` table. Lookup contents are set.
3. Run time switches to logins that can change data only, with automatic table creation turned off (recommendation 3).

### 3. Production

Run time changes only data. The recommendations below hold for as long as the pipeline is in production.

### 4. Changing a production pipeline

A change is developed on a development target, a separate database or a copy of the pipeline with representative data, where the fast loop of change, populate and compare still works. It reaches production only through review and a deployment step.

### 5. Production is one-way

Under this standard, a pipeline does not go back from production to development: once others hold its data, a direct change to its definition would reach them unannounced. If nobody depends on a pipeline any longer, its operators may choose to treat it as being in development again. A new pipeline that starts from a production pipeline's code is a different pipeline, with its own main target, and starts in development.

## Recommendations for production

**1. Change the definition only in a deployment step.** Declarations, alterations, drops, Lookup contents and any data migration that goes with them are applied together, in one step that runs before the new code starts.

**2. Enforce it with database privileges.** Run-time logins hold no privilege to create, alter or drop tables or schemas, and none to insert into or delete from Lookup tables. Only the deployment step uses a login that can change the definition. Privileges hold whatever code runs, including code written outside DataJoint. Keeping Lookup tables read-only differs by backend: PostgreSQL can grant on every table in a schema and then revoke on the Lookup tables, while MySQL cannot narrow a schema-level grant, so the run-time login's write grants are given table by table and renewed in each deployment step that declares tables.

**3. Declare everything ahead of time, and turn off automatic creation.** The deployment step declares every table the code needs, hidden tables included, so run time never needs to declare one. For run time, set `dj.config.database.create_tables` (or `DJ_CREATE_TABLES`) to false, and don't pass `create_tables=True` to `dj.Schema` in run-time code, since an explicit argument overrides the configuration. A missing table is then reported as missing instead of being declared. `dj.Schema` also creates a missing schema unless given `create_schema=False`; with the privileges of recommendation 2, that attempt is refused.

**4. Keep Lookup tables for definition only.** A Lookup table's rows are set by its `contents` and change only with the code. A table whose rows are entered while the pipeline runs is a Manual table (also available as `dj.Entry`), whether a person or an automated process enters them. DataJoint inserts a Lookup's `contents` when the table holds fewer rows than its `contents`, but it never updates or deletes Lookup rows, so a deployment step that changes or removes `contents` values applies those changes itself.

**5. Treat a changed `make()` as a change to the definition.** Deploy it together with a decision about the rows computed by the old code: delete them so that they are computed again, or keep them, knowingly. Recording a version on each computed row (job metadata, with `jobs.add_job_metadata` and a `jobs.version_method`) lets old rows be told apart from new ones.

**6. Preview, then delete.** Preview a delete with `dj.Diagram.cascade(...).counts()`, then run it with `delete(prompt=False)`. An interactive prompt holds the delete's transaction open, and its locks with it, until someone answers. The preview and the delete are separate transactions, so run the delete soon after the preview, and preview again if other processes may have changed the affected rows.

**7. Classify each change before deploying it.**

| Kind | Examples | How to deploy |
|---|---|---|
| **Additive** | A new table; a new secondary attribute that is nullable or has a default, on a Manual table | In a deployment step, without pausing run-time work |
| **Revising** | Changing a type, a key or a dependency; dropping an attribute or a table; changing a `make()` or a Lookup's contents; a new attribute on an auto-populated table, which comes with a changed `make()` | In a deployment step, after review, with the run-time work that depends on what it changes paused while it is applied |

Even an additive change to an existing table takes a brief exclusive lock while it is applied, and waits for open transactions on that table to finish, so it is best applied when no long transactions are running. Processes already running keep the table headings they loaded until they restart.

## The deployment step

A deployment step brings a production target's definition to a new version of the code. It should:

1. **Start from a known version** of the code, under version control.
2. **Compare** the definition in that code with the target's, and list each difference.
3. **Classify** each difference as additive or revising, and review the revising ones.
4. **Pause** the run-time work that depends on what a revising change touches.
5. **Apply** the changes with a login that can change the definition: declarations (hidden tables included), alterations, drops, Lookup contents, data migrations from `datajoint.migrate`, and environment operations from `datajoint.deploy`.
6. **Record** the version of the code the target now matches.
7. **Start** run time on the new code.

A deployment step should be safe to run again after a failure. Operations in `datajoint.deploy` are idempotent; a one-shot migration should check whether it has already been applied.

## What DataJoint does at run time

DataJoint attempts what the code asks, and the server refuses what the login lacks. In production, the deployment step prepares the target so that run time never needs a privilege it lacks.

| Behavior | What happens | Preparation in production |
|---|---|---|
| Decorating a table class with an activated schema (usually at import) | Declares the table if it doesn't exist, unless `create_tables` is false | Deployment declares every table; run time turns `create_tables` off |
| Decorating a Lookup class whose table exists | Inserts its `contents` if the table holds fewer rows, whatever `create_tables` says | Deployment sets the contents first |
| Accessing `Table.jobs`, or `populate(reserve_jobs=True)` | Declares the table's jobs table if it doesn't exist, whatever `create_tables` says | Deployment declares every jobs table first |
| Declaring a table | Declares the schema's `~lineage` table if it doesn't exist | Deployment declares it with the tables |
| `delete()` with `safemode` on | Deletes inside a transaction, shows what was removed, and asks before committing | Preview with `Diagram.cascade()`, then `prompt=False` |
| `drop()` with `safemode` on | Shows what will be dropped and asks before dropping | Dropping is a change to the definition, done in a deployment step |
| A statement the server refuses for lack of privilege | Usually raises `AccessError`; some paths stay silent, for example `alter()` without the privilege does nothing | The refusal is the enforcement working |

## The `datajoint.deploy` module

!!! version-added "New in 2.3"
    The `datajoint.deploy` module is introduced in DataJoint 2.3, beginning with `set_replica_identity` for PostgreSQL CDC integration.

The module holds idempotent, re-runnable operations that configure an existing schema for its environment (CDC tools, replication, role grants, performance tuning). For one-shot schema-evolution operations (column migrations, lineage repair, retroactive job-metadata columns), see `datajoint.migrate` (referenced in the [Data Manipulation Specification](data-manipulation.md)).

### Scope: migration vs. deployment

DataJoint exposes two categories of operational helpers. The distinction matters: applying the wrong one at the wrong time produces inconsistent state. Both are run in a deployment step when the target is in production.

| | `datajoint.migrate` | `datajoint.deploy` |
|---|---|---|
| **Purpose** | Schema/state evolution, fixing legacy | Configure an environment for a consumer's requirements |
| **Cadence** | One-shot transitions | Idempotent, re-runnable in every deployment step |
| **Trigger** | Schema definition changed, or repair needed | Environment changes (new CDC consumer, replication topology) |
| **Examples** | `migrate_columns`, `add_job_metadata_columns`, `rebuild_lineage` | `set_replica_identity` |

A deployment operation must be safe to call repeatedly without accumulating side effects: re-running it brings the environment to the same end state and is a no-op when already there.

### `set_replica_identity`

Apply `ALTER TABLE ... REPLICA IDENTITY DEFAULT|FULL` to every user table in a schema, or to a single table, on PostgreSQL.

#### Signature

```python
def set_replica_identity(
    target: Schema | Table,
    mode: Literal["default", "full"] = "full",
    dry_run: bool = True,
) -> dict
```

#### Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `target` | `Schema` or `Table` (class or instance) | — | Schema (all user tables) or a single table. |
| `mode` | `str` | `"full"` | `"default"` (PK only) or `"full"` (entire old row). |
| `dry_run` | `bool` | `True` | If `True`, collect DDL but do not execute. |

#### Return value

A dict:

| Key | Type | Description |
|---|---|---|
| `tables_analyzed` | `int` | Number of tables considered. |
| `tables_modified` | `int` | Tables on which the ALTER ran. `0` when `dry_run=True`. |
| `ddl` | `list[str]` | DDL statements that were (or would be) executed. |

#### Errors

| Condition | Behavior |
|---|---|
| Connection's adapter is not PostgreSQL | `DataJointError`: `"set_replica_identity is PostgreSQL-only; …"` |
| `mode` is not `"default"` or `"full"` | `DataJointError`: `"mode must be 'default' or 'full'; …"` |
| `target` is not a `Schema` or `Table` | `DataJointError`: `"target must be a Schema or Table class/instance; …"` |

#### Behavior

For each user table in the target (excluding `~`-prefixed hidden tables), the function builds `ALTER TABLE "{schema}"."{table}" REPLICA IDENTITY {MODE}` via the PostgreSQL adapter's `replica_identity_ddl()` and either records it (dry-run) or executes it on the connection.

Both `default` and `full` produce explicit `ALTER` statements. `default` is **not** treated as a no-op — it actively resets the table to PostgreSQL's default, which is the right semantics when reverting from `FULL`.

The underlying ALTER is metadata-only, instant, and idempotent at the PostgreSQL layer (re-applying the same mode is a no-op at the storage layer).

The operation is **not atomic**: tables are altered one at a time, so if execution raises on table _N_ of _M_, the first _N_−1 ALTERs have already committed and the exception propagates without returning a summary — re-run to converge (each ALTER is idempotent).

### Design rationale

Three structural decisions distinguish `dj.deploy` from alternatives that were considered and rejected. Each is informed by the failure modes the alternative would have produced.

#### 1. Migration-only, not auto-emit on `declare()`

[Issue #1447](https://github.com/datajoint/datajoint-python/issues/1447) originally proposed two mechanisms — a `database.replica_identity` config flag applied automatically during `declare()`, plus a utility for existing tables. We collapsed to migration-only. Two mechanisms would produce **mixed state**: a deployment with the config set, applied mid-cycle, would have new tables at `FULL` and old tables at `DEFAULT` until someone remembered to run the migration. One mechanism is the only path that converges.

#### 2. Not in `dj.migrate`

`dj.migrate` covers one-shot schema-evolution operations: fix lineage, add job-metadata columns, transform external store layouts. `set_replica_identity` is not a one-shot transition — a fresh declaration on a development target may need it re-applied, and a deployment step may run it on every release. The cadence and trigger differ, and conflating them in one module obscures the difference.

#### 3. New module for an emerging category

`set_replica_identity` is the first of a category. Plausible siblings, as needs arise:

- Publication membership for PostgreSQL logical replication (`CREATE PUBLICATION … FOR TABLE …`).
- Maintenance: `vacuum_analyze`, `reindex`, table-level autovacuum parameters.
- Role/grant management for shared environments.

Creating `dj.deploy` now — with one inhabitant — gives those future helpers a clear home and keeps `dj.migrate` focused. The cost is one file; the alternative is an indefinite period of "where do I put this?" for every operational helper.

### Idempotency and re-running

Every function in `datajoint.deploy` must be safe to re-run. `set_replica_identity` satisfies this because:

1. The DDL is generated freshly each call.
2. The PostgreSQL ALTER is metadata-only and applying the same mode again is a no-op at the storage layer.
3. The dry-run path produces a complete preview without executing.

A deployment step may call `set_replica_identity(schema, mode="full", dry_run=False)` on every release without accumulating side effects.

## Related

- Explanation: [PostgreSQL CDC and Replica Identity](../../explanation/postgresql-cdc-replication.md)
- Explanation: [Development and Production](../../explanation/development-and-production.md) — why the two modes exist
- Data Manipulation Specification: [Data Manipulation](data-manipulation.md) (insert / update / delete; not deployment-time)
- PostgreSQL: [Logical Replication — Replica Identity](https://www.postgresql.org/docs/current/logical-replication-publication.html)
