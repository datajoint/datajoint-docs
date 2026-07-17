# Upstream Trace: `Diagram.trace` and `self.upstream` — Specification

This document specifies two interlocking features that give DataJoint a first-class **upstream read surface** — a way to query, from any set of rows, the exact ancestor rows they were derived from:

1. **`Diagram.trace(table_expr)`** — the upstream mirror of `Diagram.cascade()`; walks the FK graph from a restricted table expression to every ancestor.
2. **`self.upstream`** — a property on `AutoPopulate` tables that exposes the trace for the current `key` during `make()` execution.

The two are designed as a unit. `trace` is the underlying graph operation; `self.upstream` is the ergonomic surface for `make()`. Together they make the "read from declared upstream" convention easy to follow and to inspect — which is exactly what makes a `make()` reproducible and statically verifiable (see the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract)).

!!! version-added "New in DataJoint 2.3"
    Introduced together. Existing code that does not use these features is unaffected.

For the related downstream operation, see [Cascade Specification](cascade.md). For `make()` itself, see [AutoPopulate Specification](autopopulate.md).

## Why this exists

A computed row's reproducibility rests on the convention that `make(self, key)` reads only from its declared upstream dependencies. Making that convention easy to follow — and its result easy to inspect — requires two pieces working together:

1. A way to **construct** the upstream view as a query object: `Diagram.trace()`.
2. A way to **expose** that view ergonomically inside `make()` so users naturally do the right thing: `self.upstream`.

Without (1), downstream tools that need row-level lineage (data-lineage viewers, CDC publishers, audit logs) have to reimplement the FK walk themselves — repeatedly, with subtly different bugs. Without (2), even users who follow the convention write awkward boilerplate (`(Upstream & key).fetch1(...)` everywhere).

## Concepts

### Trace as the upstream mirror of cascade

`Diagram.cascade()` walks **downstream** from a restricted seed and answers *"what is affected if these rows are deleted?"* `Diagram.trace()` walks **upstream** and answers *"what contributed to these rows?"*. The two share the same dependency graph (a `MultiDiGraph`), the same edge model, and most of the same propagation machinery — only the direction differs.

| Method | Direction | Convergence | Question answered |
|---|---|---|---|
| `Diagram.cascade(expr)` | downstream | OR — any FK path taints | What's affected if these rows are deleted? |
| `Diagram.restrict(expr)` | downstream | AND — must satisfy all FK paths | What satisfies all of these conditions? |
| `Diagram.trace(expr)` | **upstream** | **OR** — any FK path contributes | What contributed to these rows? |

`trace` uses OR convergence because an ancestor entity contributes to a child row if it appears via *any* FK path. (An AND-flavored upstream analog — "ancestors that contributed via *every* path" — is not provided in 2.3.)

### Reusing the propagation primitives

`trace` applies the **upward propagation rules** (`U1`, `U2`, `U3`) defined in the [Cascade Specification](cascade.md#upward-propagation-child-parent), which are the symmetric inverses of `cascade`'s forward rules. Renamed FKs (`.proj()`) are reversed via U2; Part-of-Part chains are walked through naturally; parallel FKs between the same pair of tables are handled as distinct edges.

This is why `trace` cannot ship before the upward primitives exist in the codebase. As of DataJoint 2.3, the primitives are in place (added with [#1429's cascade fix](https://github.com/datajoint/datajoint-python/pull/1468)), and `trace` is a direct consumer.

### The `make()` read/write boundary

DataJoint's `make(self, key)` convention has always been:

```
Read from self's declared upstream dependencies; write to self (and its Parts).
```

This is the **read/write boundary**: data flows in from declared ancestors and out to the target table and its Parts. Anything that crosses this boundary in another direction undermines reproducibility — a `fetch` from an undeclared table makes that dependency invisible to the FK graph; an `insert` into another table sneaks rows past it. (The full rule set is the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract).)

`self.upstream` makes the read side of this boundary the path of least resistance:

- **`self.upstream`** is the recommended read channel. Reading through it keeps every dependency visible to the FK graph and pre-restricted to the current `key`.
- **`self`** (and its Parts) is the write target.

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

Before invoking `make(self, key)`, the framework records the current key but defers constructing the trace. `self.upstream = Diagram.trace(self & key)` is built the first time the user accesses `self.upstream` inside `make()` and memoized for the rest of the call; `make()` implementations that never read `self.upstream` never build the trace. Both the key and the memoized trace are cleared after `make()` returns (including when it raises).

Once built, the trace diagram is reused for the remainder of the call. The underlying SQL is not issued until the user indexes into an ancestor: `self.upstream[Session]` builds a `QueryExpression`, and `.fetch1()` on that expression triggers a SELECT. Fetch results are not cached — each `self.upstream[T]` access returns a fresh `QueryExpression`, so reading the same ancestor twice issues two SELECTs.

### What it returns

`self.upstream[T]` returns the same value `dj.Diagram.trace(self & key)[T]` would return — the ancestor table pre-restricted to the rows that contributed to the current `key`. All `QueryExpression` operators work; the standard fetch API (`fetch`, `fetch1`, `to_arrays`, `to_dicts`, `to_pandas`) is fully supported.

### Allowed table set

`self.upstream` exposes:

- All declared ancestors of `self` (transitively, including renamed-FK chains).
- The Parts of ancestors that themselves lie on an FK path to `self` — a Part is included only when it is genuinely reachable through the FK graph, not merely because its master is an ancestor.

Requesting any table outside this set raises `DataJointError` — including tables that exist in the schema but are not ancestors of `self`. This is the same guarantee `Diagram.trace(...)` provides; `self.upstream` is just the per-`make()` instance of it.

### Examples

`self.upstream` is both a convenience and the reproducible-by-construction read channel — the same data is reachable via `(Upstream & key).fetch1(...)`, but reading through `self.upstream` keeps the dependency inside the declared upstream cone:

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

## Integration: trace and upstream together

The two features compose into a single upstream read surface:

1. `Diagram.trace()` defines the upstream view as a first-class query object.
2. `self.upstream` exposes the per-`key` slice of that view inside `make()`.

End-to-end:

```python
import datajoint as dj

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
        # Reads confined to the declared upstream cone
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

Because every read went through `self.upstream`, every column in `Spectrum.fetch1(key)` derives from data reachable via `Diagram.trace(Spectrum & key)` — the row is reproducible from its declared upstream, and downstream tooling (row-level lineage views, CDC publishers, audit logs) can reconstruct its inputs by traversal alone.

## Migration path

Teams adopt the read surface incrementally:

1. **Upgrade to 2.3.** The new APIs are available; existing code is unaffected.
2. **Start using `self.upstream` in new `make()` implementations.** Reads become ergonomic; nothing else changes.
3. **Migrate existing `make()` implementations** as opportunity allows. Replace `(Upstream & key).fetch(...)` with `self.upstream[Upstream].fetch(...)`. No semantic difference — but the read is now visibly confined to the declared upstream.

## What is not in this specification

- **Enforcement of the `make()` contract.** `trace` and `self.upstream` make the contract easy to follow and to inspect, but the open-source framework does not check it at runtime. Confirming that a `make()` reads only from its declared ancestors and writes only to its target, across every access path, is a code-inspection problem — performed by the DataJoint platform's code-deployment CI/CD (static analysis where sound, agentic review for the dynamic cases), backed by commit-pinned governed execution. See the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract).
- **Row-level lineage metadata in storage**. The features here provide the *graph operation* and the *per-`make()` read surface*; persisting per-row upstream projections (the dj-delta-style silver-layer features) is a downstream consumer concern, tracked separately.

## References

- Source (shipped in 2.3): `src/datajoint/diagram.py` (`Diagram.trace`), `src/datajoint/autopopulate.py` (`AutoPopulate.upstream`). Implemented in [#1471](https://github.com/datajoint/datajoint-python/pull/1471) (trace) and [#1473](https://github.com/datajoint/datajoint-python/pull/1473) (self.upstream), building on the cascade rules from [#1468](https://github.com/datajoint/datajoint-python/pull/1468).
- Issues: [#1423](https://github.com/datajoint/datajoint-python/issues/1423) (Diagram.trace), [#1424](https://github.com/datajoint/datajoint-python/issues/1424) (self.upstream).
- [Cascade Specification](cascade.md) — propagation rules (F1/F2/F3 forward, U1/U2/U3 upward) shared with `trace`.
- [AutoPopulate Specification](autopopulate.md) — `make()` execution model and the make() reproducibility contract.
- [Diagram Specification](diagram.md) — graph operations on the dependency graph.
- [Entity Integrity](../../explanation/entity-integrity.md) — schema dimensions and FK semantics.
