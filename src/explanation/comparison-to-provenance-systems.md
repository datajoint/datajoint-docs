# Comparison to Provenance Systems

DataJoint is often compared with data-provenance and data-lineage systems,
since both answer the question *"where did this result come from?"* As with the
[comparison to workflow languages](comparison-to-workflow-languages.md), the
point is not which is best: they address complementary, largely orthogonal
concerns and interoperate rather than compete.

## The landscape

Dedicated provenance systems — the W3C **PROV** model, **OpenLineage** (a widely
adopted open standard for lineage interchange across the data-tooling
ecosystem), and the lineage features built into data catalogs and governance
tools — record provenance as **metadata *about* data**. Derivation is captured during or after
execution and stored alongside the data as logs, tags, or sidecar records;
questions about where a result came from are answered by reading that recorded
metadata.

## Lineage as a structural property

In the [relational workflow model](relational-workflow-model.md), derivation is
not a separate record kept about the data — it is a property of the data
structure itself. Foreign-key dependencies, the table tiers, the
[`make()` reproducibility contract](../reference/specs/autopopulate.md#43-the-make-reproducibility-contract),
and [referential integrity](entity-integrity.md) together mean a computed row
cannot exist unless the upstream rows it derives from are present and valid. The
dependency graph *is* the lineage: it is declared in the schema, upheld by the
database, and queryable directly through the same algebra used for data
(`Diagram.trace`, and `self.upstream` inside `make()`).

Two properties follow:

- **Declared and upheld, not observed after the fact.** Dependencies are
  declared in the schema before computation and maintained by referential
  integrity, rather than reconstructed from logs afterward.
- **Consistent by construction.** Because lineage is structural rather than a
  parallel record, it cannot drift out of step with the data — deleting an input
  cascades to the results derived from it, so the graph always reflects the data
  as it currently is.

This is the same property the reproducibility contract describes: every row is
traceable to the declared inputs it was computed from.

## Complementary and orthogonal

DataJoint and dedicated provenance systems address **orthogonal concerns**, and
they **compose**. DataJoint tracks how results are *derived within* a pipeline —
the structural lineage of the foreign-key graph. A dedicated provenance system
records and standardizes metadata *about* data, including how it first entered
from outside — the file, instrument, API, or upstream system a value came from,
and the operational metadata around that arrival. Neither replaces the other:
within-pipeline derivation and external-origin provenance are different
questions, and a complete record often wants both.

Inside DataJoint, the origin of externally-sourced data is recorded at the
pipeline's entry-point tables — a Manual insert or an Imported `make()` records
the source identity alongside the data, exactly as at any manual data-entry
point. A single ingestion step may populate several such tables that carry no
foreign-key dependency on the loader (the
[fan-out ingestion pattern](fan-out-ingestion.md)), each recording its own origin.

At the boundary, the two integrate **in both directions** — when explicitly
configured:

- **Inbound:** provenance records from upstream systems can be *ingested* into
  the pipeline, so externally-sourced data arrives already carrying its origin.
- **Outbound:** the pipeline's lineage can be *emitted* to downstream provenance,
  catalog, and governance systems in their own terms.

This integration is opt-in and configured explicitly; it is not automatic.

## Interoperability and standards

Interchange in either direction uses the standards the surrounding ecosystem
speaks. DataJoint's lineage is expressed in its own schema; where it is exchanged
with external governance, audit, and cataloging systems, it maps to industry
lineage and provenance standards such as OpenLineage or W3C PROV. Compliance with
industry provenance standards is ensured by the DataJoint Platform.

## See also

- [Relational Workflow Model](relational-workflow-model.md) — the conceptual basis for treating the schema as the pipeline specification
- [Entity Integrity](entity-integrity.md) — the referential-integrity guarantees that make lineage structural
- [Computation Model](computation-model.md) — the `make()` contract and `populate()`
- [Fan-Out Ingestion](fan-out-ingestion.md) — how one source populates several entry-point tables, and where origin is recorded
- [Comparison to Workflow Languages](comparison-to-workflow-languages.md) — the companion comparison for pipeline and orchestration tools
