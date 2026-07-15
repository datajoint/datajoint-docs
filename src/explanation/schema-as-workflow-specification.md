# Schema as a Workflow Specification

The **Relational Workflow Model** is DataJoint's major innovation — the
central conceptual contribution that distinguishes it from every other
tool in its category. Workflow languages sequence computations.
Catalogs describe data after it lands. Lakehouses optimize analytical
reads. The Relational Workflow Model fuses all four concerns — data
structure, dependency, computation, and integrity — into a single formal
system in which the **schema is the specification of the work**.

This page describes the schema as that formal language. It has a
grammar, a typed semantics, an algebra, and a machine-readable
introspection surface. It is not Python plumbing wrapped around a
database — Python is the host language, but the schema itself is a
declarative specification that the engine reads, validates, and
executes against. Everything substantive about the pipeline — what
entities exist, how they are derived, what types they carry, what
depends on what — is in the schema, not scattered across application
code, configuration files, and external orchestrator manifests.

## Why a formal language matters

A formal specification can be parsed, validated, exported, diffed,
audited, and reasoned about by tools that did not write it. Workflow
fragments expressed in general-purpose code cannot. For interoperability
with external governance systems, for agents that must understand a
pipeline before acting on it, for reviewers reconstructing what a
result means months later, and for the engine itself enforcing
consistency, the schema needs to be a declarative artifact with stable
semantics.

## Grammar

A DataJoint schema is declared as a set of table definitions. Each
table carries a tier — `Manual`, `Lookup`, `Imported`, or `Computed` —
and a `definition` string that uses a compact DDL. The DDL distinguishes
primary key attributes (above `---`) from secondary attributes (below
`---`), declares attribute types, and writes foreign keys as
`-> ReferencedTable`. A faithful excerpt from a calcium-imaging
pipeline:

```python
@schema
class Scan(dj.Manual):
    definition = """
    -> Session
    scan_idx     : int32          # scan within session
    ---
    depth_um     : float32        # cortical depth
    nframes      : int32
    """

@schema
class AverageFrame(dj.Imported):
    definition = """
    -> Scan
    ---
    avg_frame    : <npy@raw>      # mean fluorescence frame
    """

    def make(self, key):
        ...

@schema
class SegmentationParam(dj.Lookup):
    definition = """
    param_set_id : int32
    ---
    method       : enum('cellpose', 'suite2p')
    diameter_um  : float32
    """

@schema
class Segmentation(dj.Computed):
    definition = """
    -> AverageFrame
    -> SegmentationParam
    ---
    n_cells      : int32
    masks        : <object@raw>   # cell masks, lazy reference
    """

    def make(self, key):
        ...
```

Every element of this excerpt is part of the formal language. The
tier (`dj.Computed`) is a semantic decoration: the engine will populate
this table automatically by invoking `make()` for every upstream key.
The arrows are typed foreign keys that inherit the referenced table's
primary key into the current one — they are simultaneously referential
integrity constraints and execution-order edges in the dependency DAG.
The `---` separator partitions identifying attributes from descriptive
ones. Type expressions (`float32`, `enum(...)`, `<npy@raw>`,
`<object@raw>`) bind each column to a codec in the type system. The
diamond fan-in on `Segmentation` — depending on both `AverageFrame`
and `SegmentationParam` — declares that every average frame is to be
segmented with every parameter set, automatically, without an external
manifest.

## Semantics

A row in `Segmentation` exists if and only if three conditions hold:

1. The upstream key exists — both an `AverageFrame` row and a
   `SegmentationParam` row, identified by the inherited primary key
   attributes.
2. `Segmentation.make(key)` has run to completion and inserted the row.
3. The inserted row satisfies the declared types and constraints.

The `make()` method is the typed function the schema declares from
upstream key to artifact: it receives the primary key of one entity,
fetches its inputs by query, produces the result, and inserts exactly
one row. Each inserted row records the git hash of the `make()` source
that produced it — the identity of the code that produced each row is part of
the schema's structural footprint, not an audit artifact bolted on afterward. The
[Computation Model](computation-model.md) page covers the full `make()`
/ `populate()` contract, including the three-part pattern for long
computations.

## The query algebra

The schema's queryable surface is a closed five-operator algebra:
**restrict (`&`)**, **join (`*`)**, **project (`.proj()`)**,
**aggregate (`.aggr()`)**, and **union (`+`)**. The defining property
is *algebraic closure*: every operator takes entity sets to entity sets
with a well-defined primary key, so any expression is itself a valid
operand for the next operator. Entity integrity is preserved under
composition. This is what lets the schema be both a specification and a
queryable object — the same algebra that retrieves data also traces
lineage and derives the key source for the next `populate()`. See
[Query Algebra](query-algebra.md) and
[Semantic Matching](semantic-matching.md) for operator semantics and
the lineage-based join rule that prevents accidental matches on
coincidentally-named columns.

## Types

Attribute types are drawn from a three-layer system: native database
types, portable core types (`int32`, `float64`, `varchar`, `uuid`,
`json`, `bytes`, `datetime`), and a layer of pluggable codecs declared
in angle brackets (`<blob>`, `<npy@store>`, `<object@store>`,
`<attach@store>`, and third-party codecs registered via Python entry
points). Codecs unify in-database storage and object-store references
under one declarative syntax. Lazy references — `NpyRef`, `ObjectRef` —
let a query return metadata (shape, dtype, path) without downloading
payloads, so large scientific objects participate in the schema without
forcing eager I/O. See [Type System](type-system.md).

## Self-healing operational semantics

Workflow orchestrators sequence tasks; the schema specifies states.
`populate()` reads the schema, computes the *key source* — the set of
upstream keys not yet present in a Computed or Imported table — and
invokes `make()` on each missing entity until the table is in
compliance with its declared dependencies. The engine brings the world
into agreement with the specification, not the other way around. Runs
are idempotent by construction: already-populated keys are skipped,
failed jobs are retried, and parallel workers reserve keys atomically
through the Jobs 2.0 mechanism. Deleting an upstream entity cascades
through foreign keys, removing dependent results so the next
`populate()` derives them afresh from valid inputs. The schema, not a
separate scheduler manifest, is the source of execution truth.

## Machine-readability and export

Because the schema is a declarative artifact, it is fully
introspectable. The list of tables, their tiers, attributes, types,
foreign keys, indexes, and the dependency graph itself are queryable
through the same API used for data — `schema.list_tables()`,
`Table().heading`, `Table().describe()`, `dj.Diagram(schema)`. The
dependency graph is a first-class object: tools can traverse it,
restrict it, and reason about it without parsing source code.

Export pathways follow directly:

- **Diagrams** — render to DOT or Mermaid for visual review.
- **Structured spec** — emit the schema as YAML or JSON for tooling
  that does not speak Python.
- **Lineage standards** — map foreign-key edges and `make()` records
  to W3C PROV, OpenLineage, or PROV-O for governance and catalog
  integration. The mapping is a translation, not a reconstruction,
  because the lineage graph is already in the schema.
- **Workflow languages** — CWL, Snakemake, and Nextflow workflows are
  expressible as schema subgraphs with the data-structure layer added;
  conversion is mechanical.

## The schema as control plane

Networking distinguishes the data plane — packets in flight — from the
control plane — the routing tables, ARP tables, and BGP state that
decide where the packets go. The schema is the **control plane of the
data**: a declarative, queryable, enforceable, observable description
of what exists, what depends on what, and what must hold for the system
to be valid. The rows are the data plane; the schema describes and
governs them. The two share one substrate, but the control surface is
explicit, inspectable, and standards-mappable — the property that lets
external systems, human reviewers, and automated agents reason about
the pipeline from a single source of truth.

## See also

- [The Relational Workflow Model](relational-workflow-model.md) — the
  conceptual foundation this page formalizes
- [Computation Model](computation-model.md) — `make()`, `populate()`,
  Jobs 2.0
- [Query Algebra](query-algebra.md) — the five operators and algebraic
  closure
- [Type System](type-system.md) — core types and pluggable codecs
- [Semantic Matching](semantic-matching.md) — lineage-based join
  resolution
- [Entity Integrity](entity-integrity.md) — primary keys and cascading
  guarantees
- [Comparison to Workflow Languages](comparison-to-workflow-languages.md)
  — how the schema relates to CWL, Snakemake, Nextflow, and Airflow
- [Define Tables](../how-to/define-tables.md) — declaring schema
  elements
- [Run Computations](../how-to/run-computations.md) — executing the
  schema

The Relational Workflow Model and the schema language it generates are
formally defined in
[Yatsenko & Nguyen, 2026](https://arxiv.org/abs/2602.16585); the schema
definition language and query algebra were first formalized in
[Yatsenko et al., 2018](https://doi.org/10.48550/arXiv.1807.11104).
