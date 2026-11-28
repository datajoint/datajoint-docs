# Data Integrity

**Data integrity** is the ability of a database to represent the real world
faithfully: to accept only valid data states and only valid transitions
between them. Every scientific record encodes rules that hold outside the
database — a mouse has exactly one identifier, a recording belongs to a
session that actually happened, a measurement is a number in a known range.
Data integrity is the discipline of turning those real-world rules into
**database constraints** that the engine enforces automatically.

The distinguishing property of a constraint is that *the database engine
enforces it on every write*. Validation written in application code protects
only the one program that runs it; a second script or a collaborator's
notebook can write straight past it. A constraint declared in the schema is
enforced for every client, on every write, with no cooperation required — the
rule lives with the data, not with any one program that touches it.

DataJoint organizes these guarantees into seven types of integrity. The
first four are classical relational guarantees; the last three extend them
to compositions, concurrency, and computation. Each maps to a specific
feature of a table definition.

## From real-world rules to database constraints

Database design is largely the work of translating a sentence about the
world into a set of enforceable constraints. Consider one lab rule:

> Every mouse has a unique identifier, and every recording session must
> reference a real mouse and record when it started.

That single sentence decomposes into four independent constraints, each a
different type of integrity:

```python
@schema
class Mouse(dj.Manual):
    definition = """
    mouse_id : char(6)          # unique ear-tag identifier
    ---
    date_of_birth : date
    sex : enum('M', 'F', 'U')
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Mouse                    # references a real mouse
    session_idx : int32
    ---
    session_start : datetime    # must be present and a valid timestamp
    """
```

| Fragment of the rule | Constraint | Integrity type |
|---|---|---|
| "a unique identifier" | primary key on `mouse_id` | entity |
| "must reference a real mouse" | foreign key `-> Mouse` | referential |
| "record when it started" (a value is required) | `session_start` is not nullable | completeness |
| "when it started" is a timestamp | `datetime` type on `session_start` | domain |

No procedural code enforces any of this. The declaration *is* the
enforcement.

## The seven types of integrity

### 1. Domain integrity

**Every value falls within the valid set for its attribute.** An attribute's
type restricts what it can hold — a numeric range, a fixed set of categories,
a string length, a calendar date. The database rejects anything outside that
set at insert time.

DataJoint enforces domain integrity through the attribute type declared for
each column: `int32`, `int64`, `float32`, `float64`, `decimal(p, s)`,
`varchar(N)`, `char(N)`, `date`, `datetime`, `uuid`, and `enum(...)` for
closed categorical sets. Choosing `sex : enum('M', 'F', 'U')` instead of a
free-text field means an invalid category can never be stored, and
`decimal(5, 2)` fixes both magnitude and precision.

The type system is **extensible**, and this is where DataJoint carries domain
integrity beyond the scalar SQL types. Through
[Object-Augmented Schemas](data-pipelines.md#object-augmented-schemas) and the
[codec system](../how-to/create-custom-codec.md), an attribute can hold a
domain-specific datatype — a calcium-imaging movie, a spike-sorting result, a
fitted model — whose contents live in object storage but are addressed and
governed by the schema. A [codec](../reference/specs/codec-api.md) *defines* that
datatype: it can run **arbitrary validation checks** when a value is encoded —
rejecting anything outside the domain's valid set, exactly as `enum` does for a
category — and it exposes **typed access methods** for reading the value back.
The check runs at encode time, *before* anything is written, so an invalid
value is rejected up front and the row that would reference it is never
committed — the same guarantee scalar columns give, extended to object-backed
types. The stored object is integrated with the row's lifecycle rather than
being an opaque side file: it is addressed by the schema and reclaimed by
[garbage collection](../how-to/garbage-collection.md) when no row references it
(object stores are not transactional participants, so a failed insert leaves at
most an unreferenced object, never a bad value in the table).
Domain integrity therefore holds uniformly — from `int32` and `enum` to
arbitrary structured and object-backed types.

### 2. Completeness

**Required information is always present.** An attribute that must have a
value cannot be left empty. This prevents records that are structurally
valid but analytically useless — a session with no start time, a subject
with no species.

In DataJoint, every attribute is required by default: unless an attribute is
explicitly given a default value (including an explicit nullable default), a
value must be supplied on insert. Primary-key attributes are always required.
Completeness is thus the normal case, and optionality is the deliberate
exception you opt into.

### 3. Entity integrity

**Each real-world entity corresponds to exactly one record, and each record
to exactly one entity.** This bidirectional one-to-one correspondence is what
makes a record a trustworthy stand-in for the thing it represents — no
duplicates, no two entities sharing a row.

The **primary key** — the attributes declared above the `---` separator —
enforces the database half of this guarantee by rejecting duplicate keys.
DataJoint requires every table to have a primary key and requires key values
to be supplied explicitly (there is no auto-increment), so a client must
commit to *which* entity it is inserting. The other half is the
identification process that assigns each entity its key, such as an ear tag or
a barcode. It must be stable (the same entity always receives the same key)
and injective (two entities never receive the same key), and the database
mirrors it but cannot create it. A table whose key is inherited whole from a
parent takes its identity from that parent. See
[Entity Integrity](entity-integrity.md) for the full treatment.

### 4. Referential integrity

**A reference always points to something that exists.** If one entity refers
to another, the referenced entity must be present; there are no dangling
pointers to records that were never created or have since been removed.

DataJoint declares references with the foreign-key arrow `->`, which inherits
the referenced table's primary key into the dependent table and enforces that
the referenced row exists before a dependent row can be inserted. Removal is
symmetric: deleting a row **cascades** to everything downstream of it, which
is every row that references it, directly or through other rows, together with
the master and all parts of any master-part entity so reached, subject to the
`part_integrity` mode described under
[compositional integrity](#5-compositional-integrity). The database therefore
never enters a state with orphaned references. This is a
row-level guarantee: objects held in integrated object storage are *not* removed
synchronously with their rows (hash-addressed storage is deduplicated, and
immediate deletion is unsafe under concurrency) — they are reclaimed
asynchronously by garbage collection. See
[Referential Integrity](referential-integrity.md).

### 5. Compositional integrity

**A multi-part entity is stored whole or not at all.** Some entities are
inherently composite: a segmentation and all of its detected cells, an import
and every frame it produced. Storing the container without its parts — or
some parts without others — would leave a partial, misleading entity.

DataJoint expresses this with the **master-part** relationship. The master
represents the composite entity; its part tables hold the components produced
with it. When a master and its parts are populated together by `make()`
(Computed and Imported tables), their insertion is one transaction, so a partial
composite is never committed; for Manual master-part sets this atomicity is
maintained by convention (a single transaction). Deletion keeps the composite
whole in either case. Deleting a master row removes all of its parts. A delete
that would remove part rows and leave their master, whether issued on the part
table or reaching the part through another of its parents, is refused by
default; the default check compares tables, not rows. With
`part_integrity="cascade"` the delete extends to the master and all of its
parts.
See [Master-Part](../reference/specs/master-part.md) and the
[`part_integrity` modes](../reference/specs/cascade.md#part_integrity-modes).

### 6. Consistency

**Concurrent operations never leave the database in an invalid intermediate
state.** With many users and long-running computations writing at once, a
multi-step operation must either complete entirely or leave no trace, and
in-progress work must not be visible to others as if it were final.

DataJoint relies on the backend's **transactions** and ACID guarantees to
enforce this. A group of writes is committed atomically or rolled back as a
unit, and isolation keeps a partially applied change from being seen by a
concurrent reader. Both supported backends — MySQL and PostgreSQL — provide
these guarantees. See [Transactions](transactions.md).

### 7. Workflow integrity

**Entities come into being in a valid order.** This extends referential
integrity along the axis of time. Referential integrity says a recording must
reference a real session; workflow integrity adds that the session must exist
*before* the recording, and that a computed result cannot exist before the
inputs it was derived from.

The same foreign-key graph that enforces referential integrity is a
**directed acyclic graph** (DAG) that prescribes execution order. Because it
is acyclic, there is always a valid sequence in which entities can be
created. Each table's `populate()` computes only the keys whose upstream rows
exist, so populating the tables in dependency order completes the workflow,
apart from keys whose `make()` fails. With job reservation, a failed key is
held in an error state until it is cleared. Cascade deletes remove downstream
results when their inputs are deleted.
The dependency graph and the pipeline are the same object, which is why
results stay traceable to their declared inputs and remain reproducible. See
[The Relational Workflow Model](relational-workflow-model.md).

## Why declared constraints matter

Declared constraints (attribute types, required attributes, primary keys, and
foreign keys) share one property that application-level checks cannot match:
the database engine enforces them for every client, on every write.

- **Enforced by the engine** — a write that violates a declared constraint is
  rejected, whichever program issues it.
- **Automatic** — the engine checks every write; no developer has to remember
  to call a validator.
- **Concurrent-safe** — the guarantees hold under simultaneous access by many
  users and processes.
- **Self-describing** — the schema states the rules explicitly, so the
  constraints double as documentation that both people and agents can read.

The seven types of integrity are built on these constraints, and some need
more than the engine provides. Entity integrity needs an identification
process outside the database. Compositional integrity needs a master and its
parts to be inserted in one transaction, which `populate()` does for Computed
and Imported tables and which is a convention for Manual tables. Codec
validation and cascading deletes run in the DataJoint library, so they cover
the writes made through it. Reproducible results need every `make()` to follow
the `make()` contract of the [computation model](computation-model.md).

A schema that declares its integrity rules is an executable specification of
what valid data looks like: invalid states are refused at the point of entry
rather than discovered later in analysis.

## See also

- [Entity Integrity](entity-integrity.md) — the one-to-one correspondence and the primary key
- [Referential Integrity](referential-integrity.md) — foreign keys and cascading deletes
- [Master-Part](../reference/specs/master-part.md) — compositional integrity through transactional grouping
- [Normalization](normalization.md) — organizing attributes so each describes one entity
- [Transactions](transactions.md) — atomicity and consistency under concurrent access
- [The Relational Workflow Model](relational-workflow-model.md) — the frame in which these guarantees fit together
