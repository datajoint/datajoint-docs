# Branch Resolution: draft tables beside a pipeline's own — Specification

This document specifies how a DataJoint session bound to a **branch** declares new tables into a draft schema beside the pipeline's own, while the pipeline's declared tables stay where they are and behave as they always have.

!!! version-added "New in DataJoint 2.3.4"
    A session with `database.branch` unset behaves exactly as it did before. Every rule below is reached only when a branch is set; §6 states that invariant and how it is tested.

The motivating use is an agent proposing new structure on a git branch: it declares new tables, populates a bounded sample, and opens a pull request. Nothing it declares may alter, drop, or block anything the pipeline already holds.

For the operations this changes, see [Cascade](cascade.md), [AutoPopulate](autopopulate.md), and [Table Declaration](table-declaration.md).

## Why this exists

New structure has to be tried somewhere before it merges. The obvious places all cost something:

- **Declaring into the pipeline's own schema** leaves tables behind that no committed code describes — the drift direction that cannot self-heal, because a deploy creates tables that code declares but never removes tables it does not.
- **Declaring into a separate draft schema named in the code** puts a temporary binding in the customer's source file, so what was tested is not what merges, and every difference between them is a place the test stops meaning anything.
- **Copying the pipeline** pays for the ancestors' object payloads, which do not travel free across a schema boundary, and it is branching by another name.

Branch resolution removes the *elsewhere*. On a branch, `dj.Schema('proj_ephys')` resolves to the pipeline's schema and to a draft schema holding what this branch adds. The source file is byte-identical on the branch and on `main` after the merge:

```python
# ephys_analysis.py — unchanged by the branch, unchanged by the merge
schema = dj.Schema('proj_ephys')

@schema
class ArtifactScore(dj.Computed):
    definition = """
    -> Recording
    -> ArtifactParams
    ---
    score : float
    """
```

## Concepts

### The logical schema, and the physical schemas that realize it

What the user names is a **logical schema**. On a branch it is realized by two **physical schemas**, partitioned by provenance:

| physical schema | holds |
|---|---|
| `proj_ephys` | the tables the pipeline has declared |
| `br_a1b2c3_proj_ephys` | the tables this branch adds |

The partition has no overlap. A table is in exactly one side of it, so the draft is never a mirror or a copy — calling it a shadow invites re-implementing it as one.

Off a branch there is one physical schema and the distinction does not arise.

### The branch is the unit, not the person

A draft schema is keyed by branch. Two branches never collide; two people on one branch share a draft on purpose, because that is what lets a reviewer check the branch out and materialize the same tables at the same commit. The library enforces nothing about who may hold a branch — that is the platform's, and §8 draws the line.

### Additive only

The partition works because a branch adds tables and modifies none. Structure that changes an existing table — a new attribute on a populated table, a changed type — needs the same table in two versions, which a partition cannot express. This release is additive only, and §9 records it as a limit.

## 1. The `database.branch` setting

### 1.1 Declaration

`DatabaseSettings` gains one field:

```python
branch: str | None = Field(
    default=None,
    validation_alias="DJ_BRANCH",
    description="Branch identifier. None means the session is not on a branch.",
)
```

with the matching `ENV_VAR_MAPPING` entry `"database.branch": "DJ_BRANCH"`. Precedence follows every other database setting: environment variable over config file over default.

```python
dj.config.database.branch = "a1b2c3"      # or DJ_BRANCH=a1b2c3 in the environment
```

### 1.2 The setting is per connection, not per process

`branch` lives on `DatabaseSettings` and is read through `Connection._config`, which accepts a per-connection override. One process may therefore hold a branch connection and a trunk connection at the same time, which promotion checks and diff tooling need. A module-level global would force the process into one branch.

### 1.3 Validation

The library validates only what it must: that the value yields a legal identifier. It accepts `[A-Za-z0-9_]+` and rejects a value that would push a derived name past the backend's identifier limit, naming the schema that would overflow.

Everything else about the identifier — that it is six characters, that it starts with a digit, that `br_` is reserved as an organization-name prefix — belongs to whatever creates branches. The library does not generate branch identifiers and does not parse meaning out of them.

### 1.4 The setting is read at activation and then frozen

`Schema.activate()` reads `branch` once and stores the result. Changing `branch` on a connection that has already registered a schema raises: table classes are bound to a resolved physical schema at decoration time, and a mid-session change would leave them bound to the previous one with no signal that anything moved.

## 2. Physical name derivation

### 2.1 The derived name

```
branch set    →  br_{branch_id}_{schema}
branch unset  →  {schema}
```

`Schema` keeps both names:

| attribute | value on a branch | value off a branch |
|---|---|---|
| `schema.database` | `proj_ephys` | `proj_ephys` |
| `schema.branch_database` | `br_a1b2c3_proj_ephys` | `None` |

`schema.database` remains what the caller typed, so every existing use of it — diagram selection, lineage, error messages — keeps meaning the logical schema.

### 2.2 Both names register on the connection

`Connection.register()` keys `connection.schemas` by name, and `Dependencies.load()` builds its graph over `set(connection.schemas)`. A branch therefore registers **both** names, which is what puts the draft's tables and the pipeline's tables in one dependency graph. Without it, `populate` on a draft table cannot see its parents.

### 2.3 The draft schema is created on first declaration into it

Off a branch, `activate()` creates a missing schema when `create_schema=True`. On a branch it defers: the draft schema is created when a table first resolves to it, not when the module is imported. A branch that imports ten modules and extends one leaves one draft schema, not ten empty ones.

Creating a schema is a higher privilege than writing inside one, and it is the privilege that cannot be scoped uniformly across backends — PostgreSQL cannot restrict `CREATE SCHEMA` by name. Where the session's login may not create the draft schema, the failure names the draft schema and says it must be provisioned before use, rather than reporting a generic permission error.

## 3. Declaration-time binding

### 3.1 Where a table binds

A table binds to the **branch schema if it exists in neither physical schema**, and to the **logical schema if it already exists there**.

| the table exists in | binds to | declared by this session? |
|---|---|---|
| the logical schema | the logical schema | no — it is already declared |
| the branch schema only | the branch schema | no — it is already declared |
| neither | the branch schema | yes |

One lookup, at decoration time only. There is no read-time resolution: once `Recording` is bound to `proj_ephys.recording`, every query against it is an ordinary query, `full_table_name` is its real name in its real schema, and part naming is untouched.

### 3.2 Why declaration-time resolution is required

`Schema._decorate_table()` assigns `table_class.database` and then declares the table when it is not already declared. `Table.is_declared` queries only the **bound** database. Deriving a physical name without this rule therefore binds every class in the module to the branch schema, finds none of them declared there, and re-creates the whole pipeline — `Subject`, `Session`, `Recording` — empty in the branch schema, from the branch's own definitions. The new tables then hang off empty parents, `key_source` is empty, and `populate` does nothing while reporting success.

The resolution has to precede the assignment for the same reason: after binding, there is no longer a way to ask whether the table exists in the logical schema.

### 3.3 What the lookup costs

One query per schema at activation, listing the logical schema's table names, cached on the `Schema` object. Off a branch the lookup does not run and no query is issued.

### 3.4 A part binds where its master binds

`Schema._decorate_master()` decorates a master and its parts with one schema object. Parts do **not** resolve independently: a part binds to whatever its master resolved to.

The rule matters for a new part under an existing master. Resolved independently it would exist in neither schema and land in the draft, giving a part in `br_a1b2c3_proj_ephys` whose master is in `proj_ephys`. A master and its parts are associated by **name prefix within one schema**, in four independent places, and splitting them across schemas breaks all four: the dependency loader reconstructs a master's name inside the same quoted schema and would look for one that does not exist; `Table.parts()` matches on the master's `full_table_name` prefix; `Diagram.add_parts` requires the two to share a schema outright; and the master–part integrity checks in `delete` and `drop` key on the same extraction. Bound with its master the part resolves to the logical schema, where this release cannot declare it, and raises the error in §7.

**A new master declared with its own parts is a different case, and it works.** Master and parts resolve together into the draft schema, so the prefix invariant holds inside it exactly as it does in any other schema. Only a part added under a master that already lives in the logical schema is refused.

### 3.5 A name collision raises

A branch declaring a class whose name already exists in the logical schema binds to the existing table. Where the class's `definition` differs from what is declared there, this raises: the alternative is that the caller believes it created a table it in fact adopted, which is worse than a refusal. Where the definitions agree, it binds without declaring, exactly as an ordinary re-import does.

A separate draft namespace cannot produce this failure, because there a collision yields a second table. Resolution to the same logical schema has to refuse it explicitly.

### 3.6 Interaction with `create_tables`

The resolution runs whatever `create_tables` is set to; only the declaration that follows is gated. With `create_tables=False` on a branch, a table existing in neither schema resolves to the branch schema and is not declared.

Decoration itself still succeeds, which is today's behavior and does not change. The error arrives at first heading access — *the table `<database>`.`<table_name>` is not defined* — and because the class is bound to the draft, that message names the draft schema without any new code. No eager check is added: one would change what `create_tables=False` does for every session that is not on a branch.

## 4. Symbolic references

### 4.1 The reference is recorded in DataJoint, not in the database

**A table declared into a branch schema declares no foreign key in the database.** Not only the references that cross into the pipeline's schema — all of them, including references between two draft tables. One rule with no predicate.

The reference itself is unchanged in the definition. `-> Recording` means the same thing on the branch and after the merge; only the emitted SQL differs. There is no definition-level marker and no `[SYMBOLIC]` option, because a marker in the definition would put a branch artifact in the customer's source file, which is what §Why this exists rules out.

### 4.2 What declaration emits

Foreign-key compilation has two halves, and a branch runs the first only.

| half | on a branch |
|---|---|
| copy the parent's primary-key columns into the child, with their types, comments and `:type:` markers | unchanged |
| fill the lineage mapping `child_attr → (parent_table, parent_attr)` | unchanged |
| emit the supporting index on the referencing columns | unchanged |
| emit `FOREIGN KEY (…) REFERENCES … ON UPDATE CASCADE ON DELETE RESTRICT` | **omitted** |

The index is kept. It is not the constraint, and on PostgreSQL DataJoint emits it because the server never indexes referencing columns and offers no setting to make it — dropping it would change join performance for nothing.

Because the lineage mapping is filled either way, [semantic matching](semantic-matching.md) is unaffected: joins and restrictions match on attribute lineage, which comes from that mapping and never from the constraint.

### 4.3 The `~edge` table

The reference is recorded in a hidden table in the schema that holds the referencing table, following the convention of `~lineage` and `~jobs`:

| column | meaning |
|---|---|
| `constraint_name` | identifier for the reference, unique within the schema |
| `referencing_table` | fully qualified child table name |
| `referenced_table` | fully qualified parent table name |
| `column_name` | child-side attribute |
| `referenced_column_name` | parent-side attribute |

One row per referencing column, which is the shape the dependency loader already consumes from the catalog. The table is created on first declaration into the branch schema and rewritten per table at each re-declaration, so a branch that drops and re-declares its draft carries no stale rows.

**`~edge` holds plain columns and declares no foreign key of its own.** The two backends exclude hidden tables from the foreign-key graph on opposite sides — MySQL filters the referenced table, PostgreSQL the referencing one — so a `~` table that declared a constraint would enter the graph on one backend and stay out of it on the other, and where it entered it would arrive as a node with an empty primary key. No hidden table declares one today, and this one does not become the first.

Three alternatives were considered and rejected. Column comments cannot carry it: the heading parser reads exactly one leading `:marker:`, and a foreign-key column already inherits the parent's comment, which may itself carry one. `~lineage` cannot carry it: it records where an attribute was *first* defined, and the origin of a twice-inherited attribute is not its immediate parent. Holding the edge only in the declaring process cannot carry it either, because catalog-driven readers — the diagram, any tool that did not import the module — would not see it.

### 4.4 How the dependency graph reads `~edge`

On a branch, `Dependencies.load()` unions `~edge` rows into the same structure it fills from the catalog, keyed as catalog edges are: by the tuple of child-side attribute names, which identifies a parallel edge without depending on a database-internal constraint name. Edge properties are derived identically — `attr_map` from the column pairs, `aliased` where any pair differs, `primary` where the child-side attributes fall inside the child's own primary key, `multi` where they are not the whole of it. The child's primary key comes from the catalog, so `primary` and `multi` are as accurate as they are for a real constraint.

Acyclicity is still checked, over a graph carrying the symbolic edges.

**The union happens inside `load()`, never as a layer applied afterwards.** The graph is a multigraph whose edges are keyed by that attribute tuple, and adding an edge under a key that is already present merges into it rather than sitting beside it. `load()` also rebuilds from empty every time, and registering a schema or declaring a table both discard the graph — so edges added after a load would be silently replaced or silently dropped. A symbolic edge and a catalog edge can never collide on the same key, because the referencing table is either in a draft schema or it is not.

Everything downstream then works unchanged: `parents()`, `children()`, `descendants()`, `key_source`, `Diagram`, `describe()`, `alter()`, and the cascade walk all read one graph. `describe()` is the sharpest case — it reconstructs a table's `->` lines from its parents in the graph rather than from stored SQL, so a branch table with no database constraint still describes with its references intact. If any of these needs an edit to accommodate a symbolic edge, the edge has been recorded in the wrong place.

**The read is gated on a branch being set.** A session with no branch reads no `~edge` table and issues no query for one. The consequence is deliberate and is the mechanism behind §5.2: an off-branch session cannot see a branch's references, so it can neither traverse into a draft nor be blocked by one.

### 4.5 What the constraint used to buy, and where it is recovered

Two things are given up, and neither is recovered inside the branch.

**Parent existence is no longer checked by the database.** DataJoint relies on the constraint for it. Inside a branch, a `make()` inserting a key outside its key source succeeds quietly rather than being refused.

**Nothing proves the constraints will build.** Collation mismatches, type mismatches and index failures surface when the merged definitions are declared for real.

Both are recovered in the same place and neither is the library's to run: declaring the merged definitions with real foreign keys into a throwaway schema, and dropping it. That is a continuous-integration step against the merged code, which is where declaration is headed regardless.

## 5. What each operation does on a branch

### 5.1 `populate`

Unchanged. `key_source` is the join of the parents reached through `parents(primary=True, …)`, and a symbolic edge is a parent edge like any other. A draft `Computed` table whose references are symbolic computes the same keys it would compute with real constraints.

Job queues are unchanged: `~jobs` lives in the table's own schema, so a draft table's queue lives in the draft schema and disappears with it.

### 5.2 `delete`

**Within a branch session, the cascade follows symbolic edges.** A branch's own references have no constraint behind them, so a cascade that skipped them would leave rows in a draft child referencing a deleted draft parent, with nothing to catch it.

**A session with no branch set never reaches a draft.** `Diagram.cascade` expands through `load_all_downstream()`, which discovers new schemas by reading foreign keys from the catalog. A branch leaves no catalog row, so a branch schema is never discovered, never loaded, and never walked. This holds on every backend and on every access path, including a direct connection from a laptop, because it follows from what is in the catalog rather than from a privilege that could be widened.

The cost is the other half of §4.5: a delete of a pipeline row that a draft references succeeds, and the draft row is left referencing nothing. A draft holds a bounded sample rebuilt whenever the branch is checked out, so it is accepted rather than mitigated.

### 5.3 `drop`

`Table.drop()` expands through the same downstream walk and inherits the same two behaviors: complete within a branch session, and unable to reach a draft from a session with no branch set. Dropping a table the pipeline holds therefore succeeds while a draft references it; the draft's reference fails to resolve at the branch's next checkout, which is where it is legible.

### 5.4 `Diagram`

`Diagram(schema)` selects nodes by matching a physical schema name against fully qualified table names. On a branch it matches **either** physical name, so a diagram built from a branch session shows the pipeline's tables and the branch's additions together, connected by the symbolic edges.

Drawing them as one cluster rather than as two schemas is presentation and is not in this release; §9 records it.

### 5.5 Semantic matching and lineage

Attribute lineage is unaffected for inherited attributes. `_populate_lineage` copies the **parent's** recorded lineage for every foreign-key attribute, so a draft table referencing `Recording` inherits `proj_ephys.recording.session_id` and matches the pipeline's own attributes across joins and restrictions.

An attribute **originating** in a draft table records the draft's physical schema — `br_a1b2c3_proj_ephys.artifact_score.score`. That is deliberate. Recording the logical name would claim an origin in a schema where the attribute does not exist, and a reader inspecting that schema's `~lineage` would not find it. The row lives and dies with the schema holding it, so the value never outlives the physical name it names.

### 5.6 Object storage

Object paths embed the schema the table is in, for both storage schemes — hash-addressed payloads under a per-schema deduplication subtree, schema-addressed payloads under a per-schema, per-table path. On a branch this is the draft's physical schema, with no special case: paths use the schema's name, whatever it is. A branch's payloads therefore live under their own prefix and are identifiable as the branch's.

Garbage collection is where this has to be handled and is not yet: see §9.

### 5.7 Virtual modules and generated classes

A reader that never imported the customer's module reaches a pipeline through `dj.VirtualModule` or `schema.make_classes()`, which build table classes by listing what the schema holds. **On a branch they list both physical schemas**, so a draft's tables become classes alongside the pipeline's, and a draft master's parts reattach to it normally because both are found in the same listing. Off a branch, one schema and one query, unchanged.

This is what §4.3 is for. Recording the reference where the catalog can be read back, rather than holding it in the declaring process, only pays off if a reader that imported nothing can also find the tables the references connect.

`schema.list_tables()` matches both physical names on a branch for the same reason — a listing that disagreed with the generated classes would be worse than either alone.

**`schema.drop()` refuses on a branch.** It drops the schema it is bound to, which is the logical one, so on a branch the thing a caller can now see would stop being the thing that gets dropped — and the call would take the pipeline's schema out from under a live draft. On a branch it raises, naming both physical schemas. This is the one path by which a branch session could destroy structure the pipeline owns, and dropping a branch's schemas is the caller's operation (§8), not this one's.

## 6. Behavior with no branch set

This is the invariant the feature is built around, and it is stated as behavior rather than as intent because it is what every existing deployment depends on.

With `database.branch` unset:

| surface | behavior |
|---|---|
| name derivation | identity; `activate()` registers one schema |
| declaration-time binding | the lookup does not run; no query is issued |
| `Dependencies.load()` | the same queries as before; no `~edge` read |
| foreign-key compilation | the same constraint and the same index |
| `key_source`, `delete`, `drop`, `Diagram` | unchanged |
| lineage, object paths, job queues | unchanged |

Two of these are the ones a careless implementation breaks, because both would be per-import or per-load round trips paid by every user: the declaration-time existence lookup (§3.3) and the `~edge` union (§4.4). Both are gated on a branch being set, and both are verified by counting queries rather than by reading the code — a module import and a `Dependencies.load()` must issue the same number of queries as before the feature existed.

## 7. Errors

| condition | behavior |
|---|---|
| `branch` contains characters outside `[A-Za-z0-9_]` | raises at activation, naming the offending value |
| a derived physical name exceeds the backend's identifier limit | raises at activation, naming the schema that would overflow |
| `branch` is changed on a connection with a registered schema | raises, naming the registered schema |
| the draft schema does not exist and the login may not create it | raises, naming the draft schema and stating that it must be provisioned |
| a branch declares a class whose name exists in the logical schema with a different definition | raises, naming both the class and the logical schema |
| a branch declares a new part under a master in the logical schema | raises, naming the master and its schema |
| a table resolves to the branch schema with `create_tables=False` | decoration succeeds; the existing error arrives at first heading access and names the draft schema |
| `schema.drop()` is called on a branch | raises, naming both physical schemas |

## 8. Where the library stops, and what the caller owns

The division matters, because it decides how much of a joint code-and-schema lifecycle is a library concern. It is not one.

**Lifecycle.** Checking a commit out, dropping a branch's draft tables, re-declaring them at the new commit, and tearing everything down when the branch is deleted. The library declares and binds; sequencing those acts is the caller's.

**Authorization.** The library does not enforce that a branch may only add. Create-only is a property of the credential the session holds — create inside one draft schema, read on the pipeline's schema — and a library-side flag would be advisory, which is not a boundary. It holds on every access path, including a direct connection, precisely because it is not in the library.

**Branch identity.** Generating branch identifiers, deciding who may hold a branch, reserving name prefixes, enumerating live branches.

**Provisioning.** Creating the draft schema where the session's own login may not (§2.3).

## 9. Limits in this release

**Additive only.** A branch adds tables. Changing an existing table's structure needs the same table in two versions, which the partition cannot express.

**No private draft.** A draft is as visible as the schema-level access that reaches it. The library offers no per-branch read restriction, and none of the common git providers has a per-branch read permission to mirror.

**Draft and pipeline tables draw as two schemas.** The diagram shows both and connects them (§5.4); grouping them into one logical cluster is not implemented.

**No branch-aware teardown in the library.** Dropping a branch's schemas is a caller operation, and `schema.drop()` refuses on a branch rather than guessing which schema was meant (§5.7). A `drop` that knows which tables belong to a branch is a convenience on top of it.

**Garbage collection is not branch-aware.** `GarbageCollector` is bound to a set of schemas when it is constructed, and orphan detection is confined to those schemas. A collection run over the pipeline's schemas alone will read a live branch's payloads as orphans and delete them, because the rows referencing them are in a schema the collector was not given. Until the collector takes branch schemas as part of its schema set, run it over the pipeline's schemas only when no branch is live, or construct it with every active branch's schemas included.

## References

- [Table Declaration Specification](table-declaration.md) — definition grammar, foreign-key syntax, hidden attributes
- [Cascade Specification](cascade.md) — the dependency graph and the propagation rules `delete` and `drop` walk
- [AutoPopulate Specification](autopopulate.md) — `key_source` and the `make()` contract
- [Semantic Matching Specification](semantic-matching.md) — attribute lineage and how joins and restrictions match
- [Diagram Specification](diagram.md) — node selection and rendering
- [Master-Part Specification](master-part.md) — the naming invariant §3.4 preserves
