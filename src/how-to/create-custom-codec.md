# Create Custom Codecs

Define domain-specific types for seamless storage and retrieval.

## Overview

Codecs transform Python objects for storage. Create custom codecs for:

- Domain-specific data types (graphs, images, alignments)
- Specialized serialization formats
- Integration with external libraries

## Basic Codec Structure

```python
import datajoint as dj

class GraphCodec(dj.Codec):
    """Store NetworkX graphs."""

    name = "graph"  # Used as <graph> in definitions

    def get_dtype(self, is_external: bool) -> str:
        return "<blob>"  # Delegate to blob for serialization

    def encode(self, value, *, key=None, store_name=None):
        import networkx as nx
        assert isinstance(value, nx.Graph)
        return list(value.edges)

    def decode(self, stored, *, key=None):
        import networkx as nx
        return nx.Graph(stored)
```

## Use in Table Definition

```python
@schema
class Connectivity(dj.Manual):
    definition = """
    conn_id : int
    ---
    network : <graph>           # Uses GraphCodec
    network_large : <graph@>    # External storage
    """
```

## Required Methods

### `get_dtype(is_external)`

Return the storage type:

- `is_external=False`: Internal storage (in database)
- `is_external=True`: Object storage (with `@`)

```python
def get_dtype(self, is_external: bool) -> str:
    if is_external:
        return "<hash>"  # Content-addressed external
    return "bytes"       # Database blob
```

Common return values:

- `"bytes"` — Binary in database
- `"json"` — JSON in database
- `"<blob>"` — Chain to blob codec
- `"<hash>"` — Content-addressed storage

### `encode(value, *, key=None, store_name=None)`

Convert Python object to storable format:

```python
def encode(self, value, *, key=None, store_name=None):
    # value: Python object to store
    # key: Primary key dict (for path construction)
    # store_name: Target store name
    return serialized_representation
```

### `decode(stored, *, key=None)`

Reconstruct Python object:

```python
def decode(self, stored, *, key=None):
    # stored: Data from storage
    # key: Primary key dict
    return python_object
```

## Optional: Validation

Override `validate()` for type checking:

```python
def validate(self, value):
    import networkx as nx
    if not isinstance(value, nx.Graph):
        raise TypeError(f"Expected nx.Graph, got {type(value).__name__}")
```

## Codec Chaining

Codecs can delegate to other codecs:

```python
class ImageCodec(dj.Codec):
    name = "image"

    def get_dtype(self, is_external: bool) -> str:
        return "<blob>"  # Chain to blob codec

    def encode(self, value, *, key=None, store_name=None):
        # Convert PIL Image to numpy array
        # Blob codec handles numpy serialization
        return np.array(value)

    def decode(self, stored, *, key=None):
        from PIL import Image
        return Image.fromarray(stored)
```

## External-Only Codec

Some codecs require external storage:

```python
class ZarrCodec(dj.Codec):
    name = "zarr"

    def get_dtype(self, is_external: bool) -> str:
        if not is_external:
            raise DataJointError("<zarr> requires @store")
        return "<object>"  # Path-addressed storage

    def encode(self, path, *, key=None, store_name=None):
        return path  # Path to zarr directory

    def decode(self, stored, *, key=None):
        return stored  # Returns ObjectRef for lazy access
```

## Auto-Registration

Codecs register automatically when defined:

```python
class MyCodec(dj.Codec):
    name = "mytype"  # Registers as <mytype>
    ...

# Now usable in table definitions:
# my_attr : <mytype>
```

Skip registration for abstract bases:

```python
class BaseCodec(dj.Codec, register=False):
    # Abstract base, not registered
    pass
```

## Complete Example

```python
import datajoint as dj
import SimpleITK as sitk
import numpy as np

class MedicalImageCodec(dj.Codec):
    """Store SimpleITK medical images with metadata."""

    name = "medimage"

    def get_dtype(self, is_external: bool) -> str:
        return "<blob@>" if is_external else "<blob>"

    def encode(self, image, *, key=None, store_name=None):
        return {
            'array': sitk.GetArrayFromImage(image),
            'spacing': image.GetSpacing(),
            'origin': image.GetOrigin(),
            'direction': image.GetDirection(),
        }

    def decode(self, stored, *, key=None):
        image = sitk.GetImageFromArray(stored['array'])
        image.SetSpacing(stored['spacing'])
        image.SetOrigin(stored['origin'])
        image.SetDirection(stored['direction'])
        return image

    def validate(self, value):
        if not isinstance(value, sitk.Image):
            raise TypeError(f"Expected sitk.Image, got {type(value).__name__}")


@schema
class Scan(dj.Manual):
    definition = """
    scan_id : uuid
    ---
    ct_image : <medimage@>      # CT scan with metadata
    """
```

## See Also

- [Use Object Storage](use-object-storage.md) — Storage patterns
- [Manage Large Data](manage-large-data.md) — Working with large objects
