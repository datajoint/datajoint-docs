# Diagram Operations: Cascade, Trace, and Restrict

`dj.Diagram` exposes three operations that traverse the dependency graph —
`cascade`, `trace`, and `restrict` (with `self.upstream` inside `make()` being a
form of `trace`). They are usually met one at a time, in separate contexts —
delete impact, lineage, export — so they can look like three unrelated features.

They are not. All three are **one propagation engine aimed in different
directions**. Their rules — which convergence each uses (`cascade`/`trace` are
OR closures; `restrict` is an AND selection), when the engine walks up from a
part to its master (only when the operation *mutates*), and when a restriction
must be frozen to literal keys (only when the same operation deletes rows it
depends on first) — are all *derived* from two things: the operational meaning of
the master–part relationship, and whether the operation reads or mutates.

That derivation is a low-level design rationale, so it lives with the normative
specification rather than here, and the implementation is re-derived from it:

- **[Diagram spec → Design Rationale](../reference/specs/diagram.md#design-rationale)**
  — the full first-principles derivation (one engine, OR-vs-AND, part→master
  walk, materialization) and its conformance / open items.
- **[Cascade spec](../reference/specs/cascade.md)** — the normative forward
  (F1–F3) and upward (U1–U3) propagation rules, `part_integrity` modes, and
  materialization.
- **[Upstream Trace spec](../reference/specs/trace.md)** — `Diagram.trace` and
  `self.upstream`, the `make()` read/write boundary.
- **[Master-Part spec](../reference/specs/master-part.md)** — structure and the
  principle that a dependency on a master is a dependency on all of its parts.

For the conceptual grounding this rationale builds on, see
[Relational Workflow Model](relational-workflow-model.md) (why foreign keys are
execution order and lineage is structural) and
[Comparison to Provenance Systems](comparison-to-provenance-systems.md).
