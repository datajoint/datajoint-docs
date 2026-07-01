# Spark Adapters and Silver-Layer Publishing

This page explains how DataJoint codecs interact with downstream typed-query systems — specifically, how `<blob@>`-style opaque columns differ from codecs that adapt to Spark, and why pipeline authors who want their data accessible to Spark SQL, BI tools, or Delta Sharing should choose typed codecs over generic blobs.

For the normative protocol contract, see [SparkAdapter Protocol Specification](../reference/specs/spark-adapter.md). For the base `Codec` interface, see [Codec API](../reference/specs/codec-api.md).

!!! version-added "New in DataJoint 2.3"
    The `SparkAdapter` Protocol ships in 2.3. SparkAdapter codec implementations are out-of-tree plugins that opt in by implementing the `to_spark()` method.

## The Bronze/Silver layer model

DataJoint pipelines are operational stores. When the same data is published to a downstream analytic system, two layers commonly appear:

| Layer | What it is | How blobs surface |
|---|---|---|
| **Bronze** | A mirror of the operational tables, captured via change-data-capture (CDC). Schema follows the source; rows match the source 1:1. | Blob columns land as opaque `BINARY` — the bytes are preserved but the analytic system can't see inside them. |
| **Silver** | Curated, consumer-facing tables. Schemas optimized for analytic queries. Used by Spark SQL, BI dashboards, Delta Sharing recipients, ML feature stores. | Blob columns must be **rendered** to typed shapes — `ARRAY<DOUBLE>`, `STRUCT<...>`, `MAP<K,V>` — so consumers can query them natively. No opaque `BINARY`. |

The bronze layer needs nothing from DataJoint beyond what CDC already provides — Lakehouse Sync (or Debezium, or any other CDC tool) mirrors the operational tables, blobs included. The silver layer needs more: the framework has to expose **structure** for the columns whose values aren't already primitives.

## Why `<blob@>` is bronze-only

`<blob@>` and `<hash@>` are **general-purpose**: they accept any picklable / mYm-serializable Python value. A numpy array, a list of dicts, a custom object — all become an opaque byte sequence. That generality is the right call for most pipeline work; it lets `make()` write whatever the computation produces without each codec having to anticipate the shape.

But generality is the problem at the silver-layer boundary:

- A query engine can't know whether a 4 KB blob is a 1D float array, a 2D image, a serialized dict, or a Pickle stream.
- A schema inferencer can't generate a Spark `StructType` for "could be anything."
- A SQL filter (`WHERE blob_col[0] > 0.5`) can't be evaluated.

So `<blob@>` rows make it to bronze (the bytes are there) but not to silver (the analytic system can't unpack them). This is the right tradeoff: `<blob@>` keeps pipelines flexible; the silver-layer cost is paid by users who want analytic access, not by every user.

## Typed codecs that adapt to Spark

The path to silver eligibility is to **choose a typed codec for the column** in the schema definition. A typed codec knows its value shape and can map decoded values to a Spark-native return — primitives, lists, dicts of the same.

```python
@schema
class Recording(dj.Imported):
    definition = """
    -> Session
    ---
    signal : <float_array@>     # 1D float array — adapts to Spark ARRAY<DOUBLE>
    metadata : <labeled_struct@>  # structured record — adapts to Spark STRUCT<...>
    raw_dump : <blob@>            # arbitrary Python value — bronze-only
    """
```

The codec implementations (`<float_array@>`, `<labeled_struct@>`, etc.) live in plugin packages, not in `datajoint-python` itself. Each plugin is independently versioned and can target a specific domain — neuroscience array shapes, imaging types, time-series layouts, etc.

## Why a Protocol, not a Codec method

The natural-seeming design — "add a `to_spark()` method to the `Codec` base class" — was the first proposal ([#1457](https://github.com/datajoint/datajoint-python/issues/1457)). It was rejected for three reasons.

**Generic codecs can't render meaningfully.** Forcing `<blob@>` to implement `to_spark` would mean enumerating the type taxonomy of mYm-tagged binary content inside the framework — exactly the structural knowledge that `<blob@>` exists to avoid. The clean answer is: `<blob@>` does not implement the protocol. Pipeline authors who want silver migrate to a typed codec.

**Codec authors shouldn't have to acknowledge a feature they don't support.** An abstract method requires `NotImplementedError` stubs everywhere; that's noise. The Protocol pattern lets typed codecs add the method only when they're ready, leaving non-typed codecs untouched.

**Plugin codecs already in the wild stay valid.** Existing third-party codecs (`dj-zarr-codecs`, `dj-photon-codecs`, lab-specific packages) work unchanged through 2.3 and beyond. They opt into silver eligibility by adding a `to_spark()` method in a future release of their choosing.

The decisive factor is the **opt-in shape** of the contract. Protocol checking via `isinstance(codec, SparkAdapter)` is structural — codec authors implement when they're ready, consumers detect support per-column at runtime. No coordination between codec releases and framework releases.

## What the protocol does not specify

This is a small contract, deliberately. It says **how** a codec exposes Spark-native rendering; it does not say:

- **What Spark-adapter codecs exist.** Specific codec types ship downstream. The framework only provides the protocol.
- **How the consumer publishes to silver.** Delta table writes, branch-namespace management, Lakehouse Sync hooks — all consumer concerns. The framework provides the eligibility check; the pipeline is built on top.
- **How to round-trip back.** Spark consumers query rendered columns directly; reverse-direction decode is not a framework concern.
- **What to do with columns that don't adapt.** Consumers decide: skip, raise, fall back to bronze. The framework doesn't impose a policy.

This is the typical small-Protocol pattern in Python. `__iter__`, `__len__`, `__hash__` — each is one method that opts a type into a category of consumers. `SparkAdapter` follows the same shape.

## Choosing codecs for a new pipeline

Two questions, in order:

1. **Do you need analytic access?** Will downstream consumers (Spark SQL, BI tools, Delta Sharing) query this column? If yes, choose a typed codec that implements `SparkAdapter`. If no, `<blob@>` is fine and simpler.
2. **Is there a published codec for your value shape?** Check the [available codec plugins list](../how-to/use-plugin-codecs.md). If yes, use it. If no, implement one — the [Create Custom Codecs](../how-to/create-custom-codec.md) how-to covers the framework side; add a `to_spark()` method to make it silver-eligible.

For pipelines that are predominantly internal (no analytic publish), `<blob@>` everywhere is the right default. For pipelines that publish to a shared lake, choose typed codecs from the start — retroactive migration is painful.

## Related

- Spec: [SparkAdapter Protocol](../reference/specs/spark-adapter.md) — the normative protocol.
- Spec: [Codec API](../reference/specs/codec-api.md) — the base `Codec` interface.
- How-to: [Use Plugin Codecs](../how-to/use-plugin-codecs.md) — installing and registering codec plugins.
- How-to: [Create Custom Codecs](../how-to/create-custom-codec.md) — writing your own codec.
- Strategic background: Databricks integration's Linked Delta Tables — covered in `datajoint-databricks/DECISIONS.md` (internal repo; summary on request).
