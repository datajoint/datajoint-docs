# Data Integrity

**Data integrity** is the ability of a database to represent the real world
faithfully: to accept only valid data states and only valid transitions
between them. Every scientific record encodes rules that hold outside the
database — a mouse has exactly one identifier, a recording belongs to a
session that actually happened, a measurement is a number in a known range.
Data integrity is the discipline of turning those real-world rules into
**database constraints** that the engine enforces automatically.

The distinguishing property of a constraint is that it *cannot be bypassed*.
Validation written in application code protects only the one program that
runs it; a second script or a collaborator's notebook can write straight
past it. A constraint declared in the schema is enforced for every client,
on every write, with no cooperation required — the rule lives with the data,
not with any one program that touches it.

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
`decimal(5, 2)` fixes both magnitude and precision. The type system is
extensible: custom codecs attach domain rules to structured and object-backed
attributes as well.

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
commit to *which* entity it is inserting. The other half — reliably binding a
physical entity to its identifier — is a real-world process such as an ear
tag or barcode, which the database mirrors but cannot create. See
[Entity Integrity](entity-integrity.md) for the full treatment.

### 4. Referential integrity

**A reference always points to something that exists.** If one entity refers
to another, the referenced entity must be present; there are no dangling
pointers to records that were never created or have since been removed.

DataJoint declares references with the foreign-key arrow `->`, which inherits
the referenced table's primary key into the dependent table and enforces that
the referenced row exists before a dependent row can be inserted. Removal is
symmetric: deleting an entity **cascades** to everything that depends on it,
so the database never enters a state with orphaned references. This is a
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
maintained by convention (a single transaction). Deletion cascades from master
to parts in either case. See
[Master-Part](../reference/specs/master-part.md).

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
created. `populate()` walks this graph, computing each entity only after its
upstream dependencies exist, and cascade deletes remove downstream results
when their inputs become invalid. The dependency graph and the pipeline are
the same object, which is why results stay traceable to their declared inputs
and remain reproducible. See
[The Relational Workflow Model](relational-workflow-model.md).

## Why declared constraints matter

The seven types share one property that application-level checks cannot
match: they are enforced by the database for every client, always.

- **Unbypassable** — no program can write invalid data, however it connects.
- **Automatic** — the engine checks every write; no developer has to remember
  to call a validator.
- **Concurrent-safe** — the guarantees hold under simultaneous access by many
  users and processes.
- **Self-describing** — the schema states the rules explicitly, so the
  constraints double as documentation that both people and agents can read.

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
