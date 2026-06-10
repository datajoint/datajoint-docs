# Provenance: Trace, `self.upstream`, and Strict-Provenance `make()` — Specification

This document specifies three interlocking features that together close DataJoint's provenance loop:

1. **`Diagram.trace(table_expr)`** — the upstream mirror of `Diagram.cascade()`; walks the FK graph from a restricted table expression to every ancestor.
2. **`self.upstream`** — a property on `AutoPopulate` tables that exposes the trace for the current `key` during `make()` execution.
3. **`dj.config["strict_provenance"]`** — a runtime flag that enforces the upstream-only convention inside `make()` (read only from `self.upstream`, write only to `self` and its Parts).

The three are designed as a unit. `trace` is the underlying graph operation; `self.upstream` is the ergonomic surface for `make()`; `strict_provenance` is the enforcement layer that turns the convention into a runtime guarantee.

!!! version-added "New in DataJoint 2.3"
    Introduced together. Existing code that does not use these features is unaffected; `strict_provenance` defaults to `False`.

For the related downstream operation, see [Cascade Specification](cascade.md). For `make()` itself, see [AutoPopulate Specification](autopopulate.md).

## Why this exists

DataJoint's provenance guarantee — that every computed row can be traced back to the exact upstream rows it was derived from — rests on the convention that `make(self, key)` only reads from declared upstream dependencies. Today the framework **defines** this convention but does not **enforce** it: a `make()` can `fetch()` from any table, making the undeclared dependency invisible to the FK graph and breaking the provenance claim downstream.

Closing the loop requires three pieces working together:

1. A way to **construct** the upstream view as a query object: `Diagram.trace()`.
2. A way to **expose** that view ergonomically inside `make()` so users naturally do the right thing: `self.upstream`.
3. A way to **enforce** that nothing else is read or written: `strict_provenance`.

Without (1), downstream tools that need row-level provenance (data-lineage viewers, CDC publishers, audit logs) have to reimplement the FK walk themselves — repeatedly, with subtly different bugs. Without (2), even users who follow the convention write awkward boilerplate (`(Upstream & key).fetch1(...)` everywhere). Without (3), the convention can be silently violated and downstream provenance claims become best-effort rather than guarantees.

## Concepts

### Trace as the upstream mirror of cascade

`Diagram.cascade()` walks **downstream** from a restricted seed and answers *"what is affected if these rows are deleted?"* `Diagram.trace()` walks **upstream** and answers *"what contributed to these rows?"*. The two share the same dependency graph, the same alias-node mechanism, and most of the same propagation machinery — only the direction differs.

| Method | Direction | Convergence | Question answered |
|---|---|---|---|
| `Diagram.cascade(expr)` | downstream | OR — any FK path taints | What's affected if these rows are deleted? |
| `Diagram.restrict(expr)` | downstream | AND — must satisfy all FK paths | What satisfies all of these conditions? |
| `Diagram.trace(expr)` | **upstream** | **OR** — any FK path contributes | What contributed to these rows? |

`trace` uses OR convergence because an ancestor entity contributes to a child row if it appears via *any* FK path. (The AND-flavored upstream analog — "ancestors that contributed via *every* path" — is not a useful query and is not provided.)

### Reusing the propagation primitives

`trace` applies the **upward propagation rules** (`U1`, `U2`, `U3`) defined in the [Cascade Specification](cascade.md#upward-propagation-child-parent), which are the symmetric inverses of `cascade`'s forward rules. Renamed FKs (`.proj()`) are reversed via U2; Part-of-Part chains are walked through naturally; alias nodes in the graph are transparent.

This is why `trace` cannot ship before the upward primitives exist in the codebase. As of DataJoint 2.3, the primitives are in place (added with [#1429's cascade fix](https://github.com/datajoint/datajoint-python/pull/1468)), and `trace` is a direct consumer.

### The `make()` provenance boundary

DataJoint's `make(self, key)` convention has always been:

```
Read from self's declared upstream dependencies; write to self (and its Parts).
```

The convention defines the **provenance boundary**: data flows in from declared ancestors and out to the target table and its Parts. Anything that crosses this boundary in another direction breaks the provenance claim — a `fetch` from an undeclared table makes that dependency invisible; an `insert` into another table sneaks rows past the FK graph.

The trinity makes this boundary explicit and (optionally) enforced:

- **`self.upstream`** is the only blessed read channel. Reading from `self.upstream[Ancestor]` is provenance-safe by construction.
- **`self`** (and its Parts) is the only blessed write target.
- **`strict_provenance=True`** enforces both.

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

1. Load the dependency graph via `connection.dependencies.load_all_upstream()` (the upstream analog of `load_all_downstream` — discovers all schemas reachable via reverse FK edges from the seed's schema).
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

- **A Table subclass** (e.g. `Session`) — returns the pre-restricted ancestor table as a `QueryExpression`.
- **A string** giving a table's fully-qualified or class name (e.g. `"experiment.Session"` or `"Session"`) — returns the pre-restricted ancestor as a `FreeTable`.

Requesting a table that is not an ancestor (or the seed itself) of `table_expr` raises `DataJointError`. This is the same guarantee that `cascade` provides for descendants.

### Other methods

| Method | Behavior |
|---|---|
| `trace.counts()` | Dict mapping each ancestor's full table name to the count of contributing rows under the seed's restriction. Mirror of `cascade.counts()`. |
| `trace.heading()` | Aggregated heading across all ancestor tables, grouped by table. Useful for displaying the full provenance schema for a row. |
| `iter(trace)` | Iterate over pre-restricted ancestor `FreeTable`s in topological order (deepest ancestors first). |

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

trace.counts()                                # {Subject: 1, Session: 1, Scan: 1, ExtractTraces: 1, Summary: 1}
```

For a renamed-FK case (paralleling [Cascade Spec §Worked Example 1](cascade.md#example-1-part-of-part-with-renamed-fk)), the upward rules reverse the rename so `trace[Ancestor]` returns the ancestor with its native column names regardless of how the seed's columns are named.

## 2. `self.upstream` inside `make()`

### Where it's set

The framework constructs `self.upstream = Diagram.trace(self & key)` immediately before invoking the user-defined `make(self, key)`. The construction happens once per `make()` call; `self.upstream` is a regular attribute on the bound `self` instance for the duration of the call.

The construction is **lazy** in the sense that the underlying SQL is not issued until the user accesses an ancestor: `self.upstream[Session]` builds a `QueryExpression`, and `.fetch1()` on that expression triggers a SELECT.

### What it returns

`self.upstream[T]` returns the same value `dj.Diagram.trace(self & key)[T]` would return — the ancestor table pre-restricted to the rows that contributed to the current `key`. All `QueryExpression` operators work; the standard fetch API (`fetch`, `fetch1`, `to_arrays`, `to_dicts`, `to_pandas`) is fully supported.

### Allowed table set

`self.upstream` exposes:

- All declared ancestors of `self` (transitively, including renamed-FK chains).
- The Parts of any ancestor included by the FK graph.

Requesting any table outside this set raises `DataJointError` — including tables that exist in the schema but are not ancestors of `self`. This is the same guarantee `Diagram.trace(...)` provides; `self.upstream` is just the per-`make()` instance of it.

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

`make_kwargs` and `key` are unaffected. Existing `make()` implementations that never reference `self.upstream` behave identically to today.

## 3. `dj.config["strict_provenance"]`

### Config key

| Key | Type | Default | Description |
|---|---|---|---|
| `strict_provenance` | `bool` | `False` | When `True`, enforces upstream-only reads and target-only writes inside `make()`. |

The flag is read at the start of each `make()` invocation. Changing it between invocations is supported; concurrent populates with different flag values are not (the value seen depends on thread-local context — see Implementation notes).

### Read enforcement

When `strict_provenance=True` and a `make()` is executing:

| Read attempt | Outcome |
|---|---|
| `self.upstream[Ancestor].fetch(...)` (or any other fetch method) | **Allowed** |
| `self.upstream[Ancestor] & condition` then fetch | **Allowed** |
| `(SomeTable & key).fetch(...)` where `SomeTable` is an ancestor | **Blocked** — raises `DataJointError`. The user must go through `self.upstream`. |
| `(SomeTable & ...).fetch(...)` where `SomeTable` is **not** an ancestor of `self` | **Blocked** |
| Reading `self` or `self.PartName` | **Allowed** — the target's own state may be inspected mid-`make()`. |

The check is at fetch time, not at table-expression construction time. Building a `QueryExpression` is free; executing it (calling `fetch`, `fetch1`, `to_arrays`, etc.) is gated.

### Write enforcement

When `strict_provenance=True` and a `make()` is executing:

| Write attempt | Outcome |
|---|---|
| `self.insert1(row)` | **Allowed** (with key-consistency check, see below) |
| `self.PartName.insert(rows)` | **Allowed** (with key-consistency check) |
| `SomeOtherTable.insert(...)` | **Blocked** — raises `DataJointError`. |
| Reading from `self.upstream[Ancestor]` and writing to `Ancestor` | **Blocked** — `Ancestor` is not `self`. |

### Key consistency

Every row inserted into `self` or `self`'s Parts must have a primary key consistent with the current `key`:

- For attributes that overlap with `key` (i.e. `self`'s primary key attributes that the AutoPopulate framework provided), the row's values must equal `key`'s values.
- For Part-specific PK attributes (additional columns beyond `key`), any value is allowed.

This prevents a `make()` from inserting rows for entities it wasn't called with — closing the last loophole where one entity's `make()` could silently produce data attributed to another.

### Default behavior

`strict_provenance=False` (the default) leaves all `make()` behavior unchanged. No deprecation warning, no soft enforcement, no compatibility shim. Existing pipelines run identically.

### Why opt-in

`strict_provenance` is an **operational** flag — a property of how a deployment runs, not of the schema definition. Teams may want it on in production (where provenance guarantees back downstream claims) and off during development (where ad-hoc `fetch`/`insert` from `make()` is a useful debugging affordance). Opting in is a deliberate deployment choice. Forcing it on would break existing pipelines without giving teams the tools to migrate incrementally.

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

A `make()` that **violates** strict provenance:

```python
def make(self, key):
    # ERROR: reading a table not in self.upstream
    rate = (Recording & key).fetch1("sampling_rate")
    # → DataJointError: Recording is reachable but read outside self.upstream
    #   (strict_provenance=True disallows direct reads from ancestor tables).

    # ERROR: writing to a table that isn't self or self's Parts
    AuditLog.insert1({"event": "populated_spectrum"})
    # → DataJointError: AuditLog is not self or one of self's Parts.

    # ERROR: writing a row whose key doesn't match the current key
    self.insert1({"subject_id": 99, "spectrum": ...})
    # → DataJointError: row primary key {'subject_id': 99} does not match
    #   the current key {'subject_id': key['subject_id'], ...}.
```

## Integration: the full provenance loop

The trinity composes into a single guarantee:

1. `Diagram.trace()` defines the upstream view as a first-class query object.
2. `self.upstream` exposes the per-`key` slice of that view inside `make()`.
3. `strict_provenance` ensures `make()` reads only from that slice and writes only to `self`.

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

Properties guaranteed in strict mode:

- Every column in `Spectrum.fetch1(key)` is derived from data accessible via `Diagram.trace(Spectrum & key)`. No undeclared dependencies.
- Every row in `Spectrum` and `Spectrum.Bin` was inserted by a `make()` whose `key` matched. No misattributed rows.
- Downstream provenance tooling — row-level lineage views, CDC publishers, audit logs — can rely on these properties statically rather than as best-effort.

## Migration path

Teams adopt the trinity incrementally:

1. **Upgrade to 2.3.** The new APIs are available; `strict_provenance` defaults to off. Existing code is unaffected.
2. **Start using `self.upstream` in new `make()` implementations.** Reads become ergonomic; nothing else changes.
3. **Migrate existing `make()` implementations** as opportunity allows. Replace `(Upstream & key).fetch(...)` with `self.upstream[Upstream].fetch(...)`. No semantic difference at this stage.
4. **Enable `strict_provenance=True` in staging.** Identify and fix any undeclared dependencies the runtime check surfaces.
5. **Enable in production.** Provenance guarantees now hold by construction.

Steps (3) and (4) are where most of the work lies — the runtime check is the mechanism that surfaces the actual undeclared dependencies in a pipeline. Teams with clean conventions will find few violations; teams with debugging fetches scattered through `make()` will find more. Either way, the cost is bounded by the size of the existing `make()` surface.

## What is not in this specification

- **Static analysis of `make()`**. The runtime check is the only enforcement mechanism in 2.3; analyzing `make()` bodies offline to flag potential violations is future work.
- **Flipping the default to `True`**. Whether (and when) `strict_provenance` becomes the default is a separate decision for a future major release.
- **Row-level provenance metadata in storage**. The trinity provides the *graph operation* and the *enforcement*; persisting per-row provenance projections (the dj-delta-style silver-layer features) is a downstream consumer concern, tracked separately.

## References

- Source (to land in 2.3, against this spec): `src/datajoint/diagram.py` (`Diagram.trace`), `src/datajoint/autopopulate.py` (`AutoPopulate.upstream`), `src/datajoint/settings.py` (config), `src/datajoint/expression.py` and `src/datajoint/table.py` (runtime gates).
- Issues: [#1423](https://github.com/datajoint/datajoint-python/issues/1423) (Diagram.trace), [#1424](https://github.com/datajoint/datajoint-python/issues/1424) (self.upstream), [#1425](https://github.com/datajoint/datajoint-python/issues/1425) (strict_provenance).
- [Cascade Specification](cascade.md) — propagation rules (F1/F2/F3 forward, U1/U2/U3 upward) shared with `trace`.
- [AutoPopulate Specification](autopopulate.md) — `make()` execution model.
- [Diagram Specification](diagram.md) — graph operations on the dependency graph.
- [Entity Integrity](../../explanation/entity-integrity.md) — schema dimensions and FK semantics.
