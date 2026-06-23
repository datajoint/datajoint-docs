# Renderable Codec Protocol Specification

This document specifies the `Renderable` Protocol — an opt-in contract that codecs can implement to declare that their decoded values can be expressed as Spark-native types (primitives, lists, dicts, and nested combinations).

The Protocol is intentionally small: a single method, no inheritance, no abstract-method surface area on the existing `Codec` base class. Consumers detect support via `isinstance(codec, Renderable)`.

!!! version-added "New in DataJoint 2.3"
    Introduced for the Databricks Linked Delta Tables ("silver layer") integration. Independent of any consumer: any codec author can implement `render_spark()` and any downstream tool can check for it.

For the `Codec` base class itself, see [Codec API Specification](codec-api.md). For background on why the protocol is needed, see [Renderable Codecs and Silver-Layer Publishing](../../explanation/renderable-codecs.md).

## Why this exists

DataJoint's `<blob@>` codec stores arbitrary Python values — numpy arrays, lists, dicts, custom objects — as serialized binary. That generality is the right call for most use cases, but it makes the column **opaque** to consumers that need typed access at query time: SQL engines, dataframe libraries, BI tools, federated query systems. Such consumers can only treat blob columns as `BINARY` and rely on the application to decode.

The downstream concrete case is **Databricks Linked Delta Tables** (the "silver layer"): every column must render to Spark-native types so the data is queryable with Spark SQL, exposed through Delta Sharing, and usable by Genie / BI without round-tripping through DataJoint. A `BINARY` blob doesn't qualify.

`Renderable` is the minimum framework-side contract to make typed rendering possible **without** forcing every codec to support it. Generic codecs (`<blob@>`, `<hash@>`) remain non-renderable by design. Typed codecs (`<float_array@>`, `<image_2d@>`, future shapes) opt in by implementing the method.

## The protocol

```python
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    """
    A codec that can render its decoded values to Spark-native types.

    Opt-in. Codecs implementing this method declare that their decoded
    values can be expressed as primitives, lists, or dicts of the same —
    i.e., shapes that map cleanly to Spark's StructType / ArrayType / MapType.
    """

    def render_spark(self, decoded: Any, *, key: dict | None = None) -> Any: ...
```

Defined in `datajoint.rendering` and re-exported at the top level as `dj.Renderable`.

### Signature

| Parameter | Type | Description |
|---|---|---|
| `decoded` | `Any` | The Python value produced by the codec's `decode()`. The protocol does not constrain this beyond requiring that the codec can map it to a Spark-native shape. |
| `key` | `dict \| None` | Optional context dict — same shape as `Codec.encode`'s `key` parameter. Codecs may use it to resolve per-row context (rare; most codecs ignore it). |

### Return value

A value composed entirely of:

- **Primitives**: `bool`, `int`, `float`, `str`, `bytes`, `None`, `datetime.date`, `datetime.datetime`.
- **Lists**: `list[T]` where `T` is any allowed shape. Maps to Spark `ArrayType`.
- **Dicts with string keys**: `dict[str, T]` where `T` is any allowed shape. Maps to Spark `StructType` (uniform key types per row) or `MapType` (uniform value types per row) — the consumer decides based on schema inference.

Numpy scalars (`np.int32`, `np.float64`, etc.) are accepted but consumers may coerce to native Python types. Numpy arrays must be converted to lists before return — Spark has no representation for `np.ndarray`.

No tuples, no sets, no custom objects, no callables. The output must be JSON-shaped (plus the binary/date/datetime primitives listed above).

### Why a Protocol, not an abstract method on `Codec`

The earlier framing of this work (#1457, superseded) proposed adding `render_spark()` as an abstract method on `dj.Codec`. The current factoring uses a separate Protocol for four reasons:

1. **Smaller OSS surface.** Adding an abstract method requires `NotImplementedError` stubs on every built-in codec — not just `<blob@>` and `<hash@>` (which can't render) but also every plugin codec retroactively. The Protocol approach adds ~10 lines total.
2. **Cleaner opt-in semantics.** Codec authors implement the method when they want silver-layer eligibility; they don't have to acknowledge it otherwise. Non-renderable codecs are invisible to the contract.
3. **No churn for existing plugins.** Third-party codecs (e.g. `dj-zarr-codecs`, `dj-photon-codecs`) work unchanged. They opt in by adding the method on a future release of their choosing.
4. **Composable with structural typing.** Consumers use `isinstance(codec, Renderable)` (enabled by `@runtime_checkable`) — no inheritance chain or registration step required.

The Protocol pattern matches Python's `Iterable`, `Sized`, `Sequence`, and the `dataclasses.Protocol`-style design — DataJoint follows the language convention rather than inventing a new mechanism.

## Eligibility detection

Consumers determine whether a column is renderable by checking the codec:

```python
import datajoint as dj
from datajoint.rendering import Renderable

attr = table.heading["column_name"]
if attr.codec is not None and isinstance(attr.codec, Renderable):
    # The codec opts in to Spark rendering
    rendered = attr.codec.render_spark(decoded_value)
else:
    # Non-renderable — consumer falls back to bronze-only handling
    ...
```

Because `@runtime_checkable` only verifies that the method **exists** (not its signature), the check is a structural test, not a behavioral guarantee. Codec authors must produce a Spark-native return value as defined above — the framework cannot enforce this statically.

## What's not in this specification

- **Specific renderable codecs.** Codecs like `<float_array@>`, `<int_array@>`, `<image_2d@>`, `<labeled_array@>`, `<timeseries@>`, `<sparse_matrix@>`, `<struct@>` are intentionally **out of scope** of `datajoint-python`. They ship as plugins (registered via the existing codec auto-registration mechanism) so each can evolve independently of the framework. The Protocol is what they implement against.
- **`<blob@>` and `<hash@>` rendering.** These codecs hold arbitrary Python values; their content can't be assumed to have a Spark-native shape. They do **not** implement `Renderable`. Pipeline authors who want silver eligibility migrate columns to a typed codec.
- **Reverse direction (Spark → DataJoint).** Delta consumers query rendered columns via Spark SQL; round-tripping back through DataJoint's codec is not a target of this work. There is no `decode_spark` method.
- **Best-effort `BINARY` fallback.** Codecs either implement `Renderable` (and produce a Spark-native value) or they don't (and remain bronze-only / non-eligible). No automatic blob → bytes-passthrough rendering.
- **Schema inference.** Consumers infer Spark schemas from sample rendered values; the protocol does not transmit type metadata. (A `Codec.render_spark_schema()` companion method may be added in a future release; not in scope here.)
- **Streaming / chunked rendering.** `render_spark()` is invoked per decoded value (per row, per column). Chunked / vectorized rendering is a downstream concern.

## Example: implementing a renderable codec

A plugin codec for 1D float arrays. Shipped in a separate package (e.g. `dj-array-codecs`), registered via the codec entry-point mechanism.

```python
import datajoint as dj
import numpy as np

class FloatArrayCodec(dj.Codec):
    """1D array of float64. Renders to Spark ARRAY<DOUBLE>."""

    name = "float_array"

    def get_dtype(self, is_store: bool) -> str:
        return "longblob" if not is_store else "<hash@>"

    def encode(self, value, *, key=None, store_name=None) -> bytes:
        return np.asarray(value, dtype=np.float64).tobytes()

    def decode(self, stored: bytes, *, key=None) -> np.ndarray:
        return np.frombuffer(stored, dtype=np.float64)

    def render_spark(self, decoded: np.ndarray, *, key=None) -> list[float]:
        return decoded.tolist()
```

`isinstance(FloatArrayCodec(), dj.Renderable)` returns `True` because the method is present. No subclassing required.

A 2D image codec returning a nested list (Spark `ARRAY<ARRAY<DOUBLE>>`):

```python
class Image2DCodec(dj.Codec):
    name = "image_2d"

    def encode(self, value, *, key=None, store_name=None) -> bytes: ...
    def decode(self, stored, *, key=None) -> np.ndarray: ...

    def render_spark(self, decoded: np.ndarray, *, key=None) -> list[list[float]]:
        return decoded.tolist()  # 2D ndarray → nested list
```

A structured codec rendering to Spark `STRUCT<x: DOUBLE, y: DOUBLE, label: STRING>`:

```python
class PointWithLabelCodec(dj.Codec):
    name = "labeled_point"

    def encode(self, value, *, key=None, store_name=None) -> bytes: ...
    def decode(self, stored, *, key=None) -> dict: ...

    def render_spark(self, decoded: dict, *, key=None) -> dict[str, Any]:
        return {
            "x": float(decoded["x"]),
            "y": float(decoded["y"]),
            "label": str(decoded["label"]),
        }
```

## Consumer pattern

A simplified silver-layer publish loop (the actual `datajoint-databricks` consumer is more elaborate):

```python
def publish_row_to_silver(table, key, target_table):
    """Publish one row of `table` (restricted by `key`) to a Spark-renderable target."""
    from datajoint.rendering import Renderable

    row = (table & key).fetch1()
    rendered = {}
    for attr_name, value in row.items():
        attr = table.heading[attr_name]
        if attr.codec is not None and isinstance(attr.codec, Renderable):
            rendered[attr_name] = attr.codec.render_spark(value, key=key)
        elif attr.codec is None:
            # Primitive column (no codec) — pass through
            rendered[attr_name] = value
        else:
            # Non-renderable codec — skip this column for silver, or raise
            raise ValueError(
                f"Column {attr_name!r} uses codec {attr.codec.name!r} which is "
                f"not Renderable; this row is not eligible for silver-layer publish."
            )
    target_table.write(rendered)
```

The framework provides the protocol and the eligibility check. The publish pipeline lives downstream.

## References

- Source: `src/datajoint/rendering.py` (new file in 2.3) — Protocol declaration; re-exported as `dj.Renderable`.
- Issue: [datajoint-python #1458](https://github.com/datajoint/datajoint-python/issues/1458).
- Superseded: [datajoint-python #1457](https://github.com/datajoint/datajoint-python/issues/1457) — earlier framing (abstract method on `Codec`).
- [Codec API Specification](codec-api.md) — the base `Codec` interface that renderable codecs extend (by composition, not inheritance).
- [Renderable Codecs and Silver-Layer Publishing](../../explanation/renderable-codecs.md) — explainer page covering the Bronze/Silver layer model and the rationale for typed codecs.
