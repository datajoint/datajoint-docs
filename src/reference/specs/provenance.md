# Provenance: Trace, `self.upstream`, and Strict-Provenance `make()` — Specification

This document specifies three interlocking features that together close DataJoint's provenance loop:

1. **`Diagram.trace(table_expr)`** — the upstream mirror of `Diagram.cascade()`; walks the FK graph from a restricted table expression to every ancestor.
2. **`self.upstream`** — a property on `AutoPopulate` tables that exposes the trace for the current `key` during `make()` execution.
3. **`dj.config["strict_provenance"]`** — a runtime flag that checks the upstream-only convention inside `make()` (read only from `self.upstream`, write only to `self` and its Parts).

The three are designed as a unit. `trace` is the underlying graph operation; `self.upstream` is the ergonomic surface for `make()`; `strict_provenance` is the enforcement layer that turns the convention from unenforced documentation into an opt-in runtime check — a best-effort guardrail in the open-source core, with comprehensive checking delegated to code inspection in the DataJoint platform's code-deployment CI/CD (see §3).

!!! version-added "New in DataJoint 2.3"
    Introduced together. Existing code that does not use these features is unaffected; `strict_provenance` defaults to `False`.

For the related downstream operation, see [Cascade Specification](cascade.md). For `make()` itself, see [AutoPopulate Specification](autopopulate.md).

## Why this exists

DataJoint's provenance model — that every computed row can be traced back to the exact upstream rows it was derived from — rests on the convention that `make(self, key)` only reads from declared upstream dependencies. Today the framework **defines** this convention but does not **check** it: a `make()` can `fetch()` from any table, making the undeclared dependency invisible to the FK graph and breaking the provenance claim downstream.

Closing the loop requires three pieces working together:

1. A way to **construct** the upstream view as a query object: `Diagram.trace()`.
2. A way to **expose** that view ergonomically inside `make()` so users naturally do the right thing: `self.upstream`.
3. A way to **check** that nothing else is read or written: `strict_provenance`.

Without (1), downstream tools that need row-level provenance (data-lineage viewers, CDC publishers, audit logs) have to reimplement the FK walk themselves — repeatedly, with subtly different bugs. Without (2), even users who follow the convention write awkward boilerplate (`(Upstream & key).fetch1(...)` everywhere). Without (3), the convention can be silently violated and the violation stays invisible until it corrupts a downstream provenance claim.

## Concepts

### Trace as the upstream mirror of cascade

`Diagram.cascade()` walks **downstream** from a restricted seed and answers *"what is affected if these rows are deleted?"* `Diagram.trace()` walks **upstream** and answers *"what contributed to these rows?"*. The two share the same dependency graph, the same alias-node mechanism, and most of the same propagation machinery — only the direction differs.

| Method | Direction | Convergence | Question answered |
|---|---|---|---|
| `Diagram.cascade(expr)` | downstream | OR — any FK path taints | What's affected if these rows are deleted? |
| `Diagram.restrict(expr)` | downstream | AND — must satisfy all FK paths | What satisfies all of these conditions? |
| `Diagram.trace(expr)` | **upstream** | **OR** — any FK path contributes | What contributed to these rows? |

`trace` uses OR convergence because an ancestor entity contributes to a child row if it appears via *any* FK path. (An AND-flavored upstream analog — "ancestors that contributed via *every* path" — is not provided in 2.3.)

### Reusing the propagation primitives

`trace` applies the **upward propagation rules** (`U1`, `U2`, `U3`) defined in the [Cascade Specification](cascade.md#upward-propagation-child-parent), which are the symmetric inverses of `cascade`'s forward rules. Renamed FKs (`.proj()`) are reversed via U2; Part-of-Part chains are walked through naturally; alias nodes in the graph are transparent.

This is why `trace` cannot ship before the upward primitives exist in the codebase. As of DataJoint 2.3, the primitives are in place (added with [#1429's cascade fix](https://github.com/datajoint/datajoint-python/pull/1468)), and `trace` is a direct consumer.

### The `make()` provenance boundary

DataJoint's `make(self, key)` convention has always been:

```
Read from self's declared upstream dependencies; write to self (and its Parts).
```

The convention defines the **provenance boundary**: data flows in from declared ancestors and out to the target table and its Parts. Anything that crosses this boundary in another direction breaks the provenance claim — a `fetch` from an undeclared table makes that dependency invisible; an `insert` into another table sneaks rows past the FK graph.

The trinity makes this boundary explicit and (optionally) checked:

- **`self.upstream`** is the blessed read channel. Reading through it keeps every dependency visible to the FK graph.
- **`self`** (and its Parts) is the only blessed write target.
- **`strict_provenance=True`** checks both at runtime — a best-effort guardrail, not an airtight boundary (see §3).

## 1. `Diagram.trace(table_expr)`

### Signature

```python
@classmethod
def trace(cls, table_expr: QueryExpression) -> Diagram:
    ...
```

| Parameter | Type | Description |
|---|---|---|
| `table_expr` | `QueryExpression` | A (possibly restricted) table expression. The trace propagates this restriction upstream through the FK graph. |

Returns a `Diagram` instance whose nodes are the seed and all of its ancestors (across all loaded schemas), each carrying a restriction derived from the seed.

### Behavior

`trace` mirrors `cascade`:

1. Load the dependency graph via `connection.dependencies.load_all_upstream()` — the upstream analog of `load_all_downstream`, introduced with `Diagram.trace` ([#1423](https://github.com/datajoint/datajoint-python/issues/1423)). It discovers all schemas reachable via reverse FK edges from the seed's schema.
2. Take the seed's restriction and propagate it **upstream** along the FK graph. For each edge `parent → child`, when the child has a restriction, apply the upward rule (`U1`, `U2`, or `U3` per the cascade spec) to derive the parent's restriction.
3. Trim the resulting graph to **seed + ancestors only**. Descendants of the seed and unrelated ancestors are not included.
4. Convergence is **OR**: an ancestor entity is included if reachable through *any* FK path from the seed (consistent with how a child row "comes from" any of its FK parents).

The graph traversal is dual to `cascade`'s. `cascade` walks `seed + descendants(seed)`; `trace` walks `seed + ancestors(seed)`. Both apply rules edge-by-edge; both terminate because the dependency graph is a DAG.

### Indexing: `trace[T]`

The primary user-facing operation. Returns the ancestor's table pre-restricted through the FK join path.

```python
trace = dj.Diagram.trace(MyChild & key)
session = trace[Session]              # QueryExpression: Session restricted to ancestors of MyChild & key
session.fetch1("session_date")
trace[ExtractTraces].to_arrays("trace")
```

The argument may be:

- **A Table subclass** (e.g. `Session`) — convenient when the class is in scope.
- **A string** giving a table's fully-qualified or class name (e.g. `"experiment.Session"` or `"Session"`) — for when it isn't.

In both cases the result is the ancestor pre-restricted through the FK join path, returned as a `FreeTable` (a full `QueryExpression`, so every query operator and the fetch API apply).

Requesting a table that is not an ancestor (or the seed itself) of `table_expr` raises `DataJointError`. This is the same guarantee that `cascade` provides for descendants.

### Other methods

| Method | Behavior |
|---|---|
| `trace.counts()` | `dict[str, int]` mapping each contributing table's full table name (e.g. `` `imaging`.`subject` ``) to its row count under the seed's restriction. Includes the seed alongside its ancestors. Mirror of `cascade.counts()`. |
| `iter(trace)` | Iterate over pre-restricted `FreeTable`s in topological order (parents/roots first). |

All `QueryExpression` operators (`join`, `aggr`, `proj`, `restrict`, `&`, `*`) work on the values returned by `trace[T]`. The trace is a *view* into the graph; the returned `QueryExpression`s are first-class.

### Examples

```python
import datajoint as dj

schema = dj.Schema("imaging")

@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    """

@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_id : int32
    ---
    session_date : date
    """

@schema
class Scan(dj.Imported):
    definition = """
    -> Session
    scan_id : int32
    """

@schema
class ExtractTraces(dj.Computed):
    definition = """
    -> Scan
    ---
    trace : float64
    """

@schema
class Summary(dj.Computed):
    definition = """
    -> ExtractTraces
    ---
    summary_stat : float64
    """
```

Given a populated `Summary` row, the trace reaches every ancestor:

```python
key = {"subject_id": 1, "session_id": 5, "scan_id": 2}
trace = dj.Diagram.trace(Summary & key)

trace[Subject].fetch1("subject_id")           # 1
trace[Session].fetch1("session_date")         # date of session 5
trace[Scan].fetch1("scan_id")                 # 2
trace[ExtractTraces].fetch1("trace")          # the trace that produced this Summary

trace.counts()
# keyed by full table name; the seed (Summary) is included alongside its ancestors:
# {'`imaging`.`subject`': 1, '`imaging`.`session`': 1, '`imaging`.`_scan`': 1,
#  '`imaging`.`__extract_traces`': 1, '`imaging`.`__summary`': 1}
```

For a renamed-FK case (paralleling [Cascade Spec §Worked Example 1](cascade.md#example-1-part-of-part-with-renamed-fk)), the upward rules reverse the rename so `trace[Ancestor]` returns the ancestor with its native column names regardless of how the seed's columns are named.

## 2. `self.upstream` inside `make()`

### Where it's set

The framework constructs `self.upstream = Diagram.trace(self & key)` immediately before invoking the user-defined `make(self, key)`. The construction happens once per `make()` call; `self.upstream` is a regular attribute on the bound `self` instance for the duration of the call.

The construction is **lazy** in the sense that the underlying SQL is not issued until the user accesses an ancestor: `self.upstream[Session]` builds a `QueryExpression`, and `.fetch1()` on that expression triggers a SELECT. The trace diagram is built once per `make()` call, but fetch results are not cached — each `self.upstream[T]` access returns a fresh `QueryExpression`, so reading the same ancestor twice issues two SELECTs.

### What it returns

`self.upstream[T]` returns the same value `dj.Diagram.trace(self & key)[T]` would return — the ancestor table pre-restricted to the rows that contributed to the current `key`. All `QueryExpression` operators work; the standard fetch API (`fetch`, `fetch1`, `to_arrays`, `to_dicts`, `to_pandas`) is fully supported.

### Allowed table set

`self.upstream` exposes:

- All declared ancestors of `self` (transitively, including renamed-FK chains).
- The Parts of ancestors that themselves lie on an FK path to `self` — a Part is included only when it is genuinely reachable through the FK graph, not merely because its master is an ancestor.

Requesting any table outside this set raises `DataJointError` — including tables that exist in the schema but are not ancestors of `self`. This is the same guarantee `Diagram.trace(...)` provides; `self.upstream` is just the per-`make()` instance of it.

`self.upstream` exposes ancestors only; a table's **own** Parts are not reachable via `self.upstream[...]` (they are descendants). Inside `make()`, read your own Parts directly as `self.PartName` — permitted under strict mode.

!!! note "Merge/master-part boundaries"
    Trace (and therefore `self.upstream`) walks ancestor FK edges only. It does **not** descend from an ancestor Master into that Master's Parts — an ancestor's Part is included only when the Part itself lies on the FK path to the seed. In a merge-table shape `Parent → Master.Part → Master → Child`, `trace(Child & key)` reaches `Master` but neither `Master.Part` nor `Parent`.

### Examples

Without `strict_provenance` (the default), `self.upstream` is a convenience — the same data is reachable via `(Upstream & key).fetch1(...)`. The win is ergonomic:

```python
def make(self, key):
    # All upstream reads pre-restricted to the current key
    session_date = self.upstream[Session].fetch1("session_date")
    traces = self.upstream[ExtractTraces].to_arrays("trace")
    summary = compute(traces, session_date)
    self.insert1({**key, "summary_stat": summary})
```

Multi-ancestor reads remain natural:

```python
def make(self, key):
    # Aggregate one ancestor restricted by another, all still pre-keyed
    counts = self.upstream[Session].aggr(
        self.upstream[Scan], n="count(scan_id)"
    ).fetch("n", as_dict=True)
    ...
```

Part tables of ancestors are accessible:

```python
def make(self, key):
    # If an ancestor has Parts, they appear in the trace too
    annotations = self.upstream[Session.Annotation].fetch(as_dict=True)
    ...
```

The `key` argument to `make()` — and any `make_kwargs` optionally forwarded through `populate(..., make_kwargs=...)` — are unaffected. Existing `make()` implementations that never reference `self.upstream` behave identically to today.

## 3. `dj.config["strict_provenance"]`

### Config key

| Key | Type | Default | Description |
|---|---|---|---|
| `strict_provenance` | `bool` | `False` | When `True`, checks upstream-only reads and target-only writes inside `make()`. |

The flag is read from the connection's config (`connection._config`, normally the global `dj.config`) at the start of each `make()` invocation and captured into a per-call enforcement context stored in a `contextvars.ContextVar`, so the active context follows the executing task rather than being shared as global mutable state. Because the config value itself is process-global, concurrent populates in the same process cannot run with different `strict_provenance` values — each `make()` sees whatever the config holds when it begins.

### Enforcement model and its limits

The runtime checks below are a **best-effort development guardrail, not an airtight boundary.** They are wired into DataJoint's Python query and insert paths (`assert_read_allowed` runs from `QueryExpression.cursor`, before SQL is issued; the write check runs on the insert path), so they only observe access that goes **through the DataJoint Python client.** They intentionally catch the common, accidental failure mode — a `make()` that reads an *undeclared* dependency — and are what surfaces real violations when a team enables the flag in staging (see [Migration path](#migration-path)).

They do **not** constitute a security or correctness boundary:

- Raw SQL (`connection.query(...)`), a second client or process, a database console, a BI tool, or a non-Python binding all bypass the checks entirely.
- Within the Python client, the read check currently allows a direct read of a *declared* ancestor just as it allows reads through `self.upstream` — it flags reads of tables *outside* the allowed set, not the channel used to reach one inside it (see the note under [Read enforcement](#read-enforcement)).
- **Existence and count idioms bypass the read gate.** `len(q)`, `bool(q)`, and `item in q` issue their `COUNT`/`EXISTS` SQL directly rather than through the gated fetch path, so a read of an undeclared table via `len(Undeclared & key)`, `bool(Undeclared & cond)`, or `key in Undeclared` is **not** caught. Only the `fetch`/`fetch1`/`to_arrays`/iteration path is gated. The same bypass applies to `Aggregation` and `Union` results (e.g. `len(dj.U(...).aggr(Undeclared, ...))` bypasses the gate even though `.fetch()` on the same expression is gated).
- **Restriction-by-table is not analyzed.** A semijoin restriction such as `Ancestor & Undeclared` renders `Undeclared` as an `IN (subquery)` in the `WHERE` clause, which the gate's base-table analysis does not inspect — so an undeclared table used only as a restriction operand passes. (Joins *are* caught, because they extend the query's support; restrictions are not.)
- **Deletes are not gated.** `delete()` / `delete_quick()` inside `make()` are not intercepted by the runtime checks — a `make()` can delete rows from any table. The write checks cover `insert`/`insert1` and `update1` only.

Comprehensive enforcement — verifying that a `make()` reads only from its declared ancestors and writes only to its target, across every access path — is fundamentally a **code-inspection problem, not a runtime-interception one.** That inspection is performed by the **DataJoint platform's code-deployment CI/CD process — not by the open-source core framework**. When pipeline code is deployed through the platform, its CI/CD **combines these runtime provenance checks with agentic review of the `make()` source** (backed by static analysis where it is sound) to cover the paths the runtime guardrail cannot — including the client-side gaps listed above (existence/count idioms, restriction-by-table, and access outside the Python client). The open-source `strict_provenance` guardrail complements that by catching accidental drift during local development; it does not replace it, and the core framework does not attempt code inspection itself. See [What is not in this specification](#what-is-not-in-this-specification).

### Read enforcement

When `strict_provenance=True` and a `make()` is executing:

| Read attempt | Outcome |
|---|---|
| `self.upstream[Ancestor].fetch(...)` (or any other fetch method) | **Allowed** |
| `self.upstream[Ancestor] & condition` then fetch | **Allowed** |
| `(SomeTable & key).fetch(...)` where `SomeTable` is a declared ancestor | **Allowed** in 2.3 — a direct read of a declared ancestor is not distinguished from a read through `self.upstream` (see note). `self.upstream` remains the recommended, provenance-safe channel. |
| `(SomeTable & ...).fetch(...)` where `SomeTable` is **not** a declared ancestor of `self` | **Blocked** — raises `DataJointError`. |
| Reading `self` or `self.PartName` | **Allowed** — the target's own state may be inspected mid-`make()`. |

The check is at fetch time, not at table-expression construction time. Building a `QueryExpression` is free; executing it (calling `fetch`, `fetch1`, `to_arrays`, etc.) is gated.

!!! note "What the read check does and does not distinguish"
    The check flags reads of tables **outside** the allowed set (declared ancestors, `self`, and `self`'s Parts) — i.e. undeclared dependencies. It does **not** yet distinguish a read that came *through* `self.upstream[Ancestor]` from a direct read of the same ancestor via a plain expression; both are allowed. Tightening this to require the `self.upstream` channel needs an attribution marker propagated through query composition and is deferred to a follow-up. For declared ancestors, treat `self.upstream` as the recommended pattern, not a currently-enforced one.

### Write enforcement

When `strict_provenance=True` and a `make()` is executing:

| Write attempt | Outcome |
|---|---|
| `self.insert1(row)` | **Allowed** (with key-consistency check, see below) |
| `self.PartName.insert(rows)` | **Allowed** (with key-consistency check) |
| `SomeOtherTable.insert(...)` | **Blocked** — raises `DataJointError`. |
| `self.update1(row)` | **Allowed** (with key-consistency check) |
| `SomeOtherTable.update1(...)` | **Blocked** — raises `DataJointError`. |
| Reading from `self.upstream[Ancestor]` and writing to `Ancestor` | **Blocked** — `Ancestor` is not `self`. |

`update1` is gated like insert — the target must be `self` or one of its Parts, and the updated row's key columns must match the current `key`. The blocked-update error reads: `strict_provenance=True: update1 on '<table>' is not permitted inside make() for '<target>'. Only the target table and its Part tables may be written.`

As with reads, the write check is wired into the DataJoint insert path and so shares the same client-side limits described in [Enforcement model and its limits](#enforcement-model-and-its-limits).

### Key consistency

Every row inserted into `self` or `self`'s Parts must have a primary key consistent with the current `key`:

- For attributes that overlap with `key` (i.e. `self`'s primary key attributes that the AutoPopulate framework provided), the row's values must equal `key`'s values.
- For Part-specific PK attributes (additional columns beyond `key`), any value is allowed.

This prevents a `make()` from inserting rows for entities it wasn't called with — closing the last loophole where one entity's `make()` could silently produce data attributed to another.

The key-consistency check applies to **dict-style rows**. Positional rows (tuples, numpy records) carry no attribute names to check against the current `key`, so they pass unchecked — dict inserts are the provenance-safe form under strict mode.

A second exception is server-side inserts: **`INSERT … SELECT` (inserting from a `QueryExpression`) runs entirely server-side; its rows never materialize client-side, so per-row key consistency is not applied on that path** (the target check still governs the destination).

The same key-consistency rule governs updates. For `update1`, a mismatched key raises: `strict_provenance=True: updated row's '<k>'=<v> does not match the current make() key's '<k>'=<v>. Updates must be consistent with the key being populated.`

### Default behavior

`strict_provenance=False` (the default) leaves all `make()` behavior unchanged. No deprecation warning, no soft enforcement, no compatibility shim. Existing pipelines run identically.

### Why opt-in

`strict_provenance` is an **operational** flag — a property of how a deployment runs, not of the schema definition. Teams may want it on in production (where provenance checks back downstream claims) and off during development (where ad-hoc `fetch`/`insert` from `make()` is a useful debugging affordance). Opting in is a deliberate deployment choice. Forcing it on would break existing pipelines without giving teams the tools to migrate incrementally.

A future major release may flip the default; that decision is out of scope for 2.3.

### Examples

A `make()` that complies with strict provenance:

```python
def make(self, key):
    # All reads through self.upstream
    rate = self.upstream[Recording].fetch1("sampling_rate")
    samples = self.upstream[Recording].to_arrays("signal")

    # Compute
    spectrum = compute_spectrum(samples, rate)

    # Write to self only, with key
    self.insert1({**key, "spectrum": spectrum})

    # Part write — also scoped to current key
    for bin_id, energy in enumerate(spectrum):
        self.Bin.insert1({**key, "bin_id": bin_id, "energy": float(energy)})
```

A `make()` that **violates** strict provenance (here `self` is `Spectrum`, whose key is `{"recording_id": 5}`):

```python
def make(self, key):
    # ERROR: reading a table that is not a declared ancestor of self
    label = (UnrelatedTable & key).fetch1("label")
    # → DataJointError: strict_provenance=True: read from undeclared table(s)
    #   ['`analysis`.`unrelated_table`'] is not permitted inside make(). Use
    #   self.upstream[T] for declared ancestors, or declare a foreign-key
    #   dependency on the table you want to read.
    #
    # (A *direct* read of a declared ancestor — e.g. (Recording & key) — is
    #  NOT blocked in 2.3; only undeclared tables are. Prefer self.upstream.)

    # ERROR: writing to a table that isn't self or self's Parts
    AuditLog.insert1({"event": "populated_spectrum"})
    # → DataJointError: strict_provenance=True: insert into '`analysis`.`audit_log`'
    #   is not permitted inside make() for '`analysis`.`__spectrum`'. Only the
    #   target table and its Part tables may be written.

    # ERROR: writing a row whose key doesn't match the current key
    self.insert1({"recording_id": 99, "spectrum": ...})
    # → DataJointError: strict_provenance=True: inserted row's 'recording_id'=99
    #   does not match the current make() key's 'recording_id'=5. Inserts must
    #   be consistent with the key being populated.
```

## Integration: the full provenance loop

The trinity composes into a single provenance story:

1. `Diagram.trace()` defines the upstream view as a first-class query object.
2. `self.upstream` exposes the per-`key` slice of that view inside `make()`.
3. `strict_provenance` checks (best-effort) that `make()` reads only from that slice and writes only to `self`.

End-to-end, with all three engaged:

```python
import datajoint as dj
dj.config["strict_provenance"] = True

@schema
class Spectrum(dj.Computed):
    definition = """
    -> Recording
    ---
    spectrum : longblob
    """

    class Bin(dj.Part):
        definition = """
        -> master
        bin_id : int32
        ---
        energy : float64
        """

    def make(self, key):
        # Pure provenance-safe reads
        rate = self.upstream[Recording].fetch1("sampling_rate")
        samples = self.upstream[Recording].to_arrays("signal")

        # Compute
        spectrum = compute_spectrum(samples, rate)

        # Scoped writes
        self.insert1({**key, "spectrum": spectrum})
        self.Bin.insert([
            {**key, "bin_id": i, "energy": float(e)} for i, e in enumerate(spectrum)
        ])
```

Properties the trinity is designed to uphold in strict mode:

- Every column in `Spectrum.fetch1(key)` should be derived from data accessible via `Diagram.trace(Spectrum & key)` — no undeclared dependencies.
- Every row in `Spectrum` and `Spectrum.Bin` was inserted by a `make()` whose `key` matched — no misattributed rows.

The runtime guardrail makes accidental violations of the first property visible during development, and checks the second (key consistency) on the DataJoint insert path. Neither is an airtight guarantee against out-of-band access (see [Enforcement model and its limits](#enforcement-model-and-its-limits)). Downstream provenance tooling — row-level lineage views, CDC publishers, audit logs — should treat these as strong conventions backed by the core framework's best-effort runtime checks and, where the pipeline is deployed through the DataJoint platform, by the code inspection its deployment CI/CD performs — not as invariants that hold regardless of how the data was written.

## Migration path

Teams adopt the trinity incrementally:

1. **Upgrade to 2.3.** The new APIs are available; `strict_provenance` defaults to off. Existing code is unaffected.
2. **Start using `self.upstream` in new `make()` implementations.** Reads become ergonomic; nothing else changes.
3. **Migrate existing `make()` implementations** as opportunity allows. Replace `(Upstream & key).fetch(...)` with `self.upstream[Upstream].fetch(...)`. No semantic difference at this stage.
4. **Enable `strict_provenance=True` in staging.** Identify and fix any undeclared dependencies the runtime check surfaces.
5. **Enable in production.** The runtime guardrail is active; when pipeline code is deployed through the DataJoint platform, its code-deployment CI/CD adds code inspection for coverage beyond the Python client.

Steps (3) and (4) are where most of the work lies — the runtime check is the mechanism that surfaces the actual undeclared dependencies in a pipeline. Teams with clean conventions will find few violations; teams with debugging fetches scattered through `make()` will find more. Either way, the cost is bounded by the size of the existing `make()` surface.

## What is not in this specification

- **Comprehensive enforcement via code inspection.** The runtime check is the only enforcement mechanism in the open-source core framework, and it is a best-effort client-side guardrail (see [Enforcement model and its limits](#enforcement-model-and-its-limits)). Turning provenance into a property checked across all access paths is a code-inspection problem — static analysis where sound, and agentic review for the dynamic cases — and is performed by the **DataJoint platform's code-deployment CI/CD process**, not the open-source framework. It is out of scope for the open-source `strict_provenance` feature, which does not attempt code inspection.
- **Server-side enforcement.** Scoping database grants, per-`make` views, or row-level security to `{ancestors, self, self.Parts}` for the duration of a `make()` would be a true boundary rather than a guardrail. It is a larger, separate effort and is not part of 2.3.
- **Flipping the default to `True`**. Whether (and when) `strict_provenance` becomes the default is a separate decision for a future major release.
- **Row-level provenance metadata in storage**. The trinity provides the *graph operation* and the *runtime check*; persisting per-row provenance projections (the dj-delta-style silver-layer features) is a downstream consumer concern, tracked separately.

## References

- Source (shipped in 2.3): `src/datajoint/diagram.py` (`Diagram.trace`), `src/datajoint/autopopulate.py` (`AutoPopulate.upstream`), `src/datajoint/settings.py` (config), `src/datajoint/provenance.py` (runtime checks). Implemented in [#1471](https://github.com/datajoint/datajoint-python/pull/1471) (trace), [#1473](https://github.com/datajoint/datajoint-python/pull/1473) (self.upstream), [#1474](https://github.com/datajoint/datajoint-python/pull/1474) (strict_provenance), building on the cascade rules from [#1468](https://github.com/datajoint/datajoint-python/pull/1468).
- Issues: [#1423](https://github.com/datajoint/datajoint-python/issues/1423) (Diagram.trace), [#1424](https://github.com/datajoint/datajoint-python/issues/1424) (self.upstream), [#1425](https://github.com/datajoint/datajoint-python/issues/1425) (strict_provenance).
- [Cascade Specification](cascade.md) — propagation rules (F1/F2/F3 forward, U1/U2/U3 upward) shared with `trace`.
- [AutoPopulate Specification](autopopulate.md) — `make()` execution model.
- [Diagram Specification](diagram.md) — graph operations on the dependency graph.
- [Entity Integrity](../../explanation/entity-integrity.md) — schema dimensions and FK semantics.
