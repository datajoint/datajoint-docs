# Upstream Trace: `Diagram.trace` and `self.upstream` — Specification

This document specifies two interlocking features that give DataJoint a first-class **upstream read surface** — a way to query, from any set of rows, the exact ancestor rows they were derived from:

1. **`Diagram.trace(table_expr)`** — the upstream mirror of `Diagram.cascade()`; selects every row the seed's rows depend on.
2. **`self.upstream`** — a property on `AutoPopulate` tables that exposes the trace for the current `key` during `make()` execution.

The two are designed as a unit. `trace` is the underlying graph operation; `self.upstream` is the ergonomic surface for `make()`. Together they make the "read from declared upstream" convention easy to follow and to inspect — which is what makes a `make()` reproducible and statically verifiable (see the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract)).

!!! version-added "New in DataJoint 2.3"
    Introduced together. Existing code that does not use these features is unaffected.

A trace is the `up` case of `Diagram.expand`: `Diagram.trace(seed)` equals `Diagram.expand(seed, "up")`. The rows it selects are defined once, in the [Diagram specification's Operations](diagram.md#operations); this page specifies the upstream-specific behavior and the `self.upstream` surface. For the downstream case, see the [Cascade Specification](cascade.md). For `make()` itself, see the [AutoPopulate Specification](autopopulate.md).

## Why this exists

A computed row's reproducibility rests on the convention that `make(self, key)` reads only from its declared upstream dependencies. Making that convention easy to follow — and its result easy to inspect — requires two pieces working together:

1. A way to **construct** the upstream view as a query object: `Diagram.trace()`.
2. A way to **expose** that view ergonomically inside `make()` so users naturally do the right thing: `self.upstream`.

Without (1), downstream tools that need row-level lineage (data-lineage viewers, CDC publishers, audit logs) have to reimplement the foreign-key walk themselves — repeatedly, with subtly different bugs. Without (2), even users who follow the convention write awkward boilerplate (`(Upstream & key).fetch1(...)` everywhere).

## Concepts

### Trace as the upstream mirror of cascade

`Diagram.cascade()` walks **downstream** from a restricted seed and answers *"what is affected if these rows are deleted?"* `Diagram.trace()` walks **upstream** and answers *"what contributed to these rows?"* They are the two directions of one traversal, `expand`, over the same dependency graph and the same rules:

| Method | `expand` direction | Rows | Question answered |
|---|---|---|---|
| `Diagram.cascade(expr, part_integrity="cascade")` | `down` | `D(S)` | What's affected if these rows are deleted? |
| `Diagram.trace(expr)` | `up` | `U(S)` | What contributed to these rows? |

`U(S)` is the smallest set of rows that contains the seed rows `S`, the rows each of its rows references through a foreign key, and the whole master-part instance of each of its rows. It is consistent on its own: every foreign key of its rows resolves inside it, and every instance in it is whole ([T5](diagram.md#derived-results)).

The two directions are exact mirrors ([T3](diagram.md#derived-results)): a row `y` depends on a row `x` exactly when deleting `x` would delete `y`. Results combine by union: an ancestor contributes if it is reachable through *any* foreign-key path, and there is no intersection.

### The rules upstream

`trace` crosses each foreign key upward by **restriction**: the parent is restricted to the rows referenced by at least one restricted child row, `parent & child_restricted.proj(...)`, with renamed attributes mapped back through the foreign key's `attr_map`. A condition on the child is never copied to the parent, because it describes child rows ([R1](diagram.md#r1-the-edge-rule)). A child row whose foreign key has a NULL column references nothing through it.

The group rule ([R2](diagram.md#r2-the-group-rule)) applies upward as it does downward: a part row brings its master and all of its master's part rows, and a master row brings all its part rows. Parallel foreign keys are each crossed on their own.

### The `make()` read/write boundary

DataJoint's `make(self, key)` convention has always been:

```
Read from self's declared upstream dependencies; write to self (and its Parts).
```

This is the **read/write boundary**: data flows in from declared ancestors and out to the target table and its Parts. Anything that crosses this boundary in another direction undermines reproducibility — a `fetch` from an undeclared table makes that dependency invisible to the foreign-key graph; an `insert` into another table sneaks rows past it. (The full rule set is the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract).)

`self.upstream` makes the read side of this boundary the path of least resistance:

- **`self.upstream`** is the recommended read channel. Reading through it keeps every dependency visible to the foreign-key graph and pre-restricted to the current `key`.
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
| `table_expr` | `QueryExpression` | The seed: one table with any restriction (see [Seeds](diagram.md#seeds)). |

Returns an expanded `Diagram` in the `up` direction. Its nodes are the seed's table and every table reachable upward from it, across all loaded schemas, including the parts of every master reached. Each node holds that table's rows in `U(S)`, possibly none.

### Behavior

1. Load the dependency graph via `connection.dependencies.load_all_upstream()`, the upstream analog of `load_all_downstream` ([#1423](https://github.com/datajoint/datajoint-python/issues/1423)). It discovers every schema reachable through foreign keys from the seed's schema, including schemas the current process has not activated.
2. Compute `U(S)` in one pass over the tables in reverse topological order: each table is restricted by its seed and by the restricted rows of its children; each master-part group by the masters its members reach, after which each part takes all part rows of those masters ([Computation](diagram.md#computation)).
3. Keep the seed's table and the tables reachable upward, with groups taken whole. Descendants of the seed and unrelated tables are not included.

The trace stays symbolic: no rows are read until a node is indexed, counted, or fetched. The one exception is a group whose internal foreign key renames the master's key, which is evaluated while the trace is built ([groups that iterate](diagram.md#groups-that-iterate)).

!!! version-changed "Changed in 2.4"
    A trace includes all parts of every master it reaches, and the ancestors of those parts ([#1481](https://github.com/datajoint/datajoint-python/issues/1481)). In 2.3 it included a part only if the part lay on a foreign-key path to the seed. Upward crossings are always restrictions; 2.3 copied some conditions upward, which is correct only for keys of existing child rows.

### Indexing: `trace[T]`

The primary user-facing operation. Returns the table pre-restricted to its rows in the trace.

```python
trace = dj.Diagram.trace(MyChild & key)
session = trace[Session]              # QueryExpression: Session restricted to the rows MyChild & key depends on
session.fetch1("session_date")
trace[ExtractTraces].to_arrays("trace")
```

The argument may be:

- **A Table subclass** (e.g. `Session`) — convenient when the class is in scope.
- **A string** giving a table's fully-qualified or class name (e.g. `"experiment.Session"` or `"Session"`) — for when it isn't.

In both cases the result is a full `QueryExpression`, so every query operator and the fetch API apply.

Requesting a table that is not a node of the trace raises `DataJointError`. A node with zero rows, such as a part of an ancestor master that has no rows for this seed, returns an empty expression.

### Other methods

| Method | Behavior |
|---|---|
| `trace.counts()` | `dict[str, int]` mapping each node's full table name (e.g. `` `imaging`.`subject` ``) to its row count. Includes the seed. Mirror of `cascade.counts()`. |
| `iter(trace)` | Iterate over pre-restricted `FreeTable`s in topological order (parents first). |
| `trace.prune()` | Remove nodes with zero rows. Allowed on traces, unlike cascades (new in 2.4). |
| `trace1 + trace2` | For two traces, the union of their rows, table by table (new in 2.4). |

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

For a renamed foreign key, the restriction maps the attributes back through `attr_map`, so `trace[Ancestor]` returns the ancestor with its own column names however the seed's columns are named ([S4](traversal-shapes.md#s4-renamed-foreign-key)).

For a **merge table** — a master whose parts each reference a different upstream table — the trace from a downstream row reaches the merge master, its part row, and the upstream table that part names ([G5](traversal-shapes.md#g5-merge-table)):

```python
trace = dj.Diagram.trace(Analysis & {"recording_id": 1})
trace[Recording.Ephys]     # the part row of recording 1
trace[EphysSource]         # the source that produced recording 1
```

## 2. `self.upstream` inside `make()`

### Where it's set

Before invoking `make(self, key)`, the framework records the current key but defers constructing the trace. The trace is built the first time `make()` accesses `self.upstream`, and memoized for the rest of the call; `make()` implementations that never read `self.upstream` never build it. Both the key and the memoized trace are cleared after `make()` returns (including when it raises).

The row for `key` does not exist yet while `make()` runs, so `self.upstream` cannot be a trace of `self & key`, which selects nothing. It is built from the parents that row will have: for each foreign key `e` in the table's primary key, the parent row `P_e & relabel_e(key)` (the key's values renamed onto `P_e`'s primary key), and

```
self.upstream = ⋃ over primary foreign keys e of  Diagram.trace(P_e & relabel_e(key))
```

the table-by-table union of those traces. Foreign keys outside the primary key are not included, because their values are not known before the insert. See [`self.upstream`](diagram.md#operations) in the Diagram specification.

!!! version-changed "Changed in 2.4"
    In 2.3, `self.upstream` was `Diagram.trace(self & key)`, which returned the parents only because the engine copied the key's condition upward. The 2.4 construction starts from the parent rows directly, and adds the parts of ancestor masters and their ancestors.

Once built, the trace is reused for the remainder of the call. The underlying SQL is not issued until the user indexes into an ancestor: `self.upstream[Session]` builds a `QueryExpression`, and `.fetch1()` on that expression triggers a SELECT. Fetch results are not cached — each `self.upstream[T]` access returns a fresh `QueryExpression`, so reading the same ancestor twice issues two SELECTs.

### What it returns

`self.upstream[T]` returns the ancestor table `T` pre-restricted to the rows that the current `key` depends on. All `QueryExpression` operators work; the standard fetch API (`fetch`, `fetch1`, `to_arrays`, `to_dicts`, `to_pandas`) is fully supported.

### Allowed table set

`self.upstream` exposes:

- all ancestors of `self` reached through its primary foreign keys (transitively, including renamed foreign keys);
- **all parts of every ancestor master**, and their ancestors. By the group rule, a master-part group is one entity: once an ancestor master is in the trace, its whole group comes with it, not only those parts that happen to lie on a foreign-key path to `self`. This is the upstream mirror of `part_integrity="cascade"` treating the group as one.

Requesting any table outside this set raises `DataJointError` — including tables that exist in the schema but are not ancestors of `self`. A table's own parts are descendants, not ancestors; read them directly as `self.PartName`.

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

In 2.4, traces and `self.upstream` also include the parts of ancestor masters and their ancestors. Code that relied on `trace[T]` raising for such a table now receives its rows.

## What is not in this specification

- **Enforcement of the `make()` contract.** `trace` and `self.upstream` make the contract easy to follow and to inspect, but the open-source framework does not check it at runtime. Confirming that a `make()` reads only from its declared ancestors and writes only to its target, across every access path, is a code-inspection problem — performed by the DataJoint platform's code-deployment CI/CD (static analysis where sound, agentic review for the dynamic cases), backed by commit-pinned governed execution. See the [make() reproducibility contract](autopopulate.md#43-the-make-reproducibility-contract).
- **Row-level lineage metadata in storage**. The features here provide the *graph operation* and the *per-`make()` read surface*; persisting per-row upstream projections (the dj-delta-style silver-layer features) is a downstream consumer concern, tracked separately.

## References

- Source: `src/datajoint/diagram.py` (`Diagram.expand`, `Diagram.trace`), `src/datajoint/autopopulate.py` (`AutoPopulate.upstream`). First implemented in [#1471](https://github.com/datajoint/datajoint-python/pull/1471) (trace) and [#1473](https://github.com/datajoint/datajoint-python/pull/1473) (self.upstream).
- Issues: [#1423](https://github.com/datajoint/datajoint-python/issues/1423) (Diagram.trace), [#1424](https://github.com/datajoint/datajoint-python/issues/1424) (self.upstream), [#1481](https://github.com/datajoint/datajoint-python/issues/1481) (parts of ancestor masters).
- [Diagram Specification](diagram.md#traversal-specification) — the definitions of `U` and the rules it is computed by.
- [Traversal Shape Catalog](traversal-shapes.md) — worked examples, with the rows each trace returns.
- [Cascade Specification](cascade.md) — the downstream case of the same traversal.
- [AutoPopulate Specification](autopopulate.md) — `make()` execution model and the make() reproducibility contract.
- [Entity Integrity](../../explanation/entity-integrity.md) — schema dimensions and foreign-key semantics.
