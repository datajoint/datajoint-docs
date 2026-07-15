# Comparison to Provenance Systems

DataJoint is often compared with data-provenance and data-lineage systems,
since both answer the question *"where did this result come from?"* As with the
[comparison to workflow languages](comparison-to-workflow-languages.md), the
point is not which is best: they take different approaches to the same concern,
and they interoperate rather than compete.

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

This is the same guarantee the reproducibility contract describes: every row is
traceable to the declared inputs it was computed from.

## What DataJoint leaves to provenance systems

DataJoint tracks how results are *derived within* a pipeline. It does not try to
own the separate concern of recording **how data first entered** the pipeline
from outside — the file, instrument, API, or upstream system a value originated
from, and the operational metadata around that arrival. That origin record is
captured at the pipeline's entry-point tables: a Manual insert or an Imported
`make()` records the source identity alongside the data, exactly as at any
manual data-entry point. A single ingestion step may populate several such
tables that carry no foreign-key dependency on the loader (the
[fan-out ingestion pattern](fan-out-ingestion.md)), each recording its own origin.

Formalizing and standardizing that external-origin record — retention, actors,
audit trails, cross-system exchange — is the province of dedicated provenance
and governance systems, and DataJoint stays deliberately neutral there. Many
pipelines run alongside such a system and let it capture origin provenance in
its own terms. DataJoint's part is to provide the structural lineage *within*
the pipeline and a clean surface to interoperate, not to reimplement the
provenance system.

## Interoperability and standards

The two approaches are complementary. DataJoint's lineage is internal to the
pipeline and expressed in its own schema; for interchange with external
governance, audit, and cataloging systems that speak industry lineage and
provenance standards such as OpenLineage or W3C PROV, that lineage can be
exported. Compliance with
industry provenance standards is ensured by the DataJoint Platform.

## See also

- [Relational Workflow Model](relational-workflow-model.md) — the conceptual basis for treating the schema as the pipeline specification
- [Entity Integrity](entity-integrity.md) — the referential-integrity guarantees that make lineage structural
- [Computation Model](computation-model.md) — the `make()` contract and `populate()`
- [Fan-Out Ingestion](fan-out-ingestion.md) — how one source populates several entry-point tables, and where origin is recorded
- [Comparison to Workflow Languages](comparison-to-workflow-languages.md) — the companion comparison for pipeline and orchestration tools
