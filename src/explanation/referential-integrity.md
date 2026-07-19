# Referential Integrity

Where [entity integrity](entity-integrity.md) guarantees that each record
corresponds to exactly one real-world entity, **referential integrity**
guarantees that the *relationships between* entities remain valid. It is what
prevents a session from referencing a subject that was never recorded, or a
computed result from surviving after the input it was derived from has been
deleted.

**Referential integrity is impossible without entity integrity.** You cannot
reliably relate entities until you can reliably identify them. A foreign key
points at a parent's primary key, so the parent must first have a primary key
that uniquely names each of its entities. Identification comes first;
relationships follow. This is why the two guarantees are always discussed in
order — the second is built on the first.

## A foreign key is a logical constraint, not a physical pointer

The most important thing to understand about a foreign key is what it is *not*.
It is not a stored link to a location on disk. Nothing in the child record
holds an address, offset, or path into the parent.

A foreign key is a **logical constraint enforced at runtime**. When you insert
a row into a child table, the database does not follow a pre-existing link. It
performs a *search* of the parent table to verify that a row with the matching
primary-key value already exists. If one does, the insert succeeds; if not, the
insert is rejected. The relationship is re-verified from the actual data every
time it matters, rather than trusted because a pointer was once written down.

This is a genuine departure from file-based data models. In an HDF5 file, or a
tree of files referencing each other by path, a link is a physical thing: a
name or address baked into the data. If the target moves or disappears, the
link silently dangles and nothing notices until something tries to follow it.
The relational model refuses to store such a link at all. Because references
are logical, they cannot dangle: a value either matches an existing key or the
database will not accept it. This is the source of the model's durability — and
it is why DataJoint stores relationships as key values rather than as pointers
into its [internal object store](type-system.md).

## The five effects of a foreign key

Declaring a foreign key — in DataJoint, the arrow `->` — sets five distinct
things in motion. Understanding each explains why a foreign key is a design
decision, not merely a link.

### 1. Schema embedding

The parent's primary-key attributes become attributes of the child, with the
same datatypes and — by default — the same names. The child inherits the
parent's key rather than inventing a parallel one.

```python
@schema
class Session(dj.Manual):
    definition = """
    -> Subject                 # embeds subject_id : varchar(16)
    session_idx : int32
    ---
    session_date : date
    """
```

DataJoint resolves joins by [attribute lineage](semantic-matching.md) rather
than by name — every inherited attribute traces back to the dimension where it
was first defined.

Sharing the parent's attribute name is the common case, not a requirement. A
foreign key can be **renamed** — `-> Person.proj(husband='person_id')` embeds
`person_id` into the child under the name `husband`, which is what lets a table
reference the same parent more than once. A renamed attribute keeps the *same*
lineage under a *different* name, so joins still resolve correctly: it is the
attribute's lineage, not its literal name, that ties it back to its origin. See
[renamed foreign keys](semantic-matching.md) for the full mechanics.

### 2. Insert restriction on the child

A child row can be inserted only if its foreign-key value matches an existing
parent key. This is what prevents *orphaned* records. The restriction falls on
the **child**: you may always add new parents, but you cannot add a child that
references a parent that does not exist.

```python
Session.insert1(('M00142', 1, '2026-03-01'))  # ok if subject M00142 exists
Session.insert1(('M09999', 1, '2026-03-01'))  # IntegrityError: no such subject
```

### 3. Delete restriction on the parent

The mirror of the insert rule: a parent cannot leave dependent children
stranded. Standard SQL rejects a delete that would orphan children. DataJoint
instead **cascades** the delete — removing a parent removes every child that
depends on it, and every child of those children, down the whole hierarchy. It
warns you first, because the reach can be large. The restriction falls on the
**parent**: you may always delete a child, but deleting a parent takes its
descendants with it.

### 4. Update restriction on key values

Key values are not edited in place. DataJoint does not support updating a
primary-key or foreign-key value, because doing so would silently invalidate
every relationship built on it. The intended pattern is to delete the affected
records and reinsert them. In a pipeline this preserves a clean rule: if an
input changes, the results derived from it are removed and recomputed, never
quietly rewritten.

### 5. Automatic index creation

The database automatically creates a secondary index on the child's
foreign-key columns. You never declare it. This index accelerates the delete
check (finding a parent's children), the join (matching child keys to parent
keys), and the insert check (confirming the parent exists). A foreign key thus
carries a performance guarantee as well as an integrity guarantee.

## The dual role: integrity and workflow

In a conventional relational database a foreign key does exactly one job:
referential integrity. In DataJoint it does a second job at the same time. The
same arrow that guarantees a valid reference also declares a **workflow
dependency** — it states that the child cannot be produced until the parent
exists.

Read the insert restriction again through this lens. "The parent must exist
before the child can reference it" is not only an integrity rule; it is an
execution order. The set of foreign keys across a schema therefore defines a
[directed acyclic graph](relational-workflow-model.md) — the pipeline DAG,
which is also the schema diagram. Nothing external schedules the work; the
foreign-key graph itself dictates what may run, what must run first, and what
already exists. Cascade delete acquires the same double meaning: removing an
invalidated input automatically removes every downstream result computed from
it, keeping the pipeline consistent without any audit step. This unification of
constraint and execution order is what makes lineage and reproducibility
[structural properties of the schema](relational-workflow-model.md) rather than
something reconstructed after the fact.

## Modifiers and placement shape the relationship

The default foreign key is a required, many-to-one reference: every child names
exactly one parent, and a parent may be named by many children. Two modifiers
adjust this, and *where* the arrow sits adjusts it further.

- **`-> [nullable] Parent`** makes the reference optional — the child may exist
  with no parent (the key value is left empty). Only a *secondary* foreign key,
  declared below the `---`, can be nullable; a key that is part of the primary
  key must always have a value, because it helps identify the entity.
- **`-> [unique] Parent`** makes the reference one-to-one — at most one child
  may name a given parent.

Placement matters just as much. A foreign key placed *above* the `---` becomes
part of the child's primary key, so the parent's identity is built into the
child's identity — a containment or extension relationship. Placed *below* the
`---`, it is an ordinary secondary reference. And two foreign keys placed
together above the `---` form the composite key of an *association* table,
which is how DataJoint expresses many-to-many relationships. Choosing among
these is a modeling decision with real consequences for cardinality and for how
the relationship appears in a diagram.

These placements and modifiers, and the relationship patterns they build, are
covered in full in the how-to guide — see
[Model Relationships](../how-to/model-relationships.ipynb).

## See also

- [Entity Integrity](entity-integrity.md) — the guarantee referential
  integrity depends on: identifying entities before relating them
- [Data Integrity](data-integrity.md) — how referential integrity fits among
  DataJoint's full set of integrity guarantees
- [Model Relationships](../how-to/model-relationships.ipynb) — the how-to for
  one-to-one, one-to-many, and many-to-many patterns
- [Design Primary Keys](../how-to/design-primary-keys.md) — choosing the keys
  that foreign keys reference
- [Relational Workflow Model](relational-workflow-model.md) — the frame in
  which a foreign key is both a constraint and an execution order
