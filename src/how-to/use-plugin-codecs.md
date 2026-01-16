# Use Plugin Codecs

Install and use plugin codec packages to extend DataJoint's type system.

## Overview

Plugin codecs are distributed as separate Python packages that extend DataJoint's type system. They add support for domain-specific data types without modifying DataJoint itself. Once installed, they register automatically via Python's entry point system and work seamlessly with DataJoint.

**Benefits:**
- Automatic registration via entry points - no code changes needed
- Domain-specific types maintained independently
- Clean separation of core framework from specialized formats
- Easy to share across projects and teams

## Quick Start

### 1. Install the Codec Package

```bash
pip install dj-zarr-codecs
```

### 2. Use in Table Definitions

```python
import datajoint as dj

schema = dj.Schema('my_schema')

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int
    ---
    waveform : <zarr@>  # Automatically available after install
    """
```

That's it! No imports or registration needed. The codec is automatically discovered via Python's entry point system.

## Example: Zarr Array Storage

The `dj-zarr-codecs` package adds support for storing NumPy arrays in Zarr format with schema-addressed paths.

### Installation

```bash
pip install dj-zarr-codecs
```

### Configuration

Configure object storage for external data:

```python
import datajoint as dj

dj.config['stores'] = {
    'mystore': {
        'protocol': 's3',
        'endpoint': 's3.amazonaws.com',
        'bucket': 'my-bucket',
        'location': 'data',
    }
}
```

### Basic Usage

```python
import numpy as np

schema = dj.Schema('neuroscience')

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int
    ---
    waveform : <zarr@mystore>  # Store as Zarr array
    """

# Insert NumPy array
Recording.insert1({
    'recording_id': 1,
    'waveform': np.random.randn(1000, 32),
})

# Fetch returns zarr.Array (read-only)
zarr_array = (Recording & {'recording_id': 1}).fetch1('waveform')

# Use with NumPy
mean_waveform = np.mean(zarr_array, axis=0)

# Access Zarr features
print(zarr_array.shape)   # (1000, 32)
print(zarr_array.chunks)  # Zarr chunking info
print(zarr_array.dtype)   # float64
```

### Storage Structure

Zarr arrays are stored with schema-addressed paths that mirror your database structure:

```
s3://my-bucket/data/
└── neuroscience/           # Schema name
    └── recording/          # Table name
        └── recording_id=1/ # Primary key
            └── waveform.zarr/  # Field name + .zarr extension
                ├── .zarray
                └── 0.0
```

This organization makes external storage browsable and self-documenting.

### When to Use `<zarr@>`

**Use `<zarr@>` when:**
- Arrays are large (> 10 MB)
- You need chunked access patterns
- Compression is beneficial
- Cross-language compatibility matters (any Zarr library can read)
- You want browsable, organized storage paths

**Use `<npy@>` instead when:**
- You need lazy loading with metadata inspection before download
- Memory mapping is important
- Storage format simplicity is preferred

**Use `<blob@>` instead when:**
- Arrays are small (< 10 MB)
- Deduplication of repeated values is important
- Storing mixed Python objects (not just arrays)

## Finding Plugin Codecs

### DataJoint-Maintained Codecs

- **[dj-zarr-codecs](https://github.com/datajoint/dj-zarr-codecs)** — Zarr array storage for general numpy arrays
- **[dj-photon-codecs](https://github.com/datajoint/dj-photon-codecs)** — Photon-limited movies with Anscombe transformation and compression

### Community Codecs

Check PyPI for packages with the `datajoint` keyword:

```bash
pip search datajoint codec
```

Or browse GitHub: https://github.com/topics/datajoint

### Domain-Specific Examples

**Neuroscience:**
- Spike train formats (NEO, NWB)
- Neural network models
- Connectivity matrices

**Imaging:**
- Photon-limited movies (calcium imaging, low-light microscopy)
- OME-TIFF, OME-ZARR
- DICOM medical images
- Point cloud data

**Genomics:**
- BAM/SAM alignments
- VCF variant calls
- Phylogenetic trees

## Verifying Installation

Check that a codec is registered:

```python
import datajoint as dj

# List all available codecs
print(dj.list_codecs())
# ['blob', 'attach', 'hash', 'object', 'npy', 'filepath', 'zarr', ...]

# Check specific codec
assert 'zarr' in dj.list_codecs()
```

## How Auto-Registration Works

Plugin codecs use Python's entry point system for automatic discovery. When you install a codec package, it registers itself via `pyproject.toml`:

```toml
[project.entry-points."datajoint.codecs"]
zarr = "dj_zarr_codecs:ZarrCodec"
```

DataJoint discovers these entry points at import time, so the codec is immediately available after `pip install`.

**No manual registration needed** — unlike DataJoint 0.x which required `dj.register_codec()`.

## Troubleshooting

### "Unknown codec: \<zarr\>"

The codec package is not installed or not found. Verify installation:

```bash
pip list | grep dj-zarr-codecs
```

If installed but not working:

```python
# Force entry point reload
import importlib.metadata
importlib.metadata.entry_points().select(group='datajoint.codecs')
```

### Codec Not Found After Installation

Restart your Python session or kernel. Entry points are discovered at import time:

```python
# Restart kernel, then:
import datajoint as dj
print('zarr' in dj.list_codecs())  # Should be True
```

### Version Conflicts

Check compatibility with your DataJoint version:

```bash
pip show dj-zarr-codecs
# Requires: datajoint>=2.0.0a22
```

Upgrade DataJoint if needed:

```bash
pip install --upgrade datajoint
```

## Creating Your Own Codecs

If you need a codec that doesn't exist yet, see:

- [Create Custom Codecs](create-custom-codec.md) — Step-by-step guide
- [Codec API Specification](../reference/specs/codec-api.md) — Technical reference
- [Custom Codecs Explanation](../explanation/custom-codecs.md) — Design concepts

Consider publishing your codec as a package so others can benefit!

## Best Practices

### 1. Install Codecs with Your Project

Add plugin codecs to your project dependencies:

**requirements.txt:**
```
datajoint>=2.0.0a22
dj-zarr-codecs>=0.1.0
```

**pyproject.toml:**
```toml
dependencies = [
    "datajoint>=2.0.0a22",
    "dj-zarr-codecs>=0.1.0",
]
```

### 2. Document Codec Requirements

In your pipeline documentation, specify required codecs:

```python
"""
My Pipeline
===========

Requirements:
- datajoint>=2.0.0a22
- dj-zarr-codecs>=0.1.0  # For waveform storage

Install:
    pip install datajoint dj-zarr-codecs
"""
```

### 3. Pin Versions for Reproducibility

Use exact versions in production:

```
dj-zarr-codecs==0.1.0  # Exact version
```

Use minimum versions in libraries:

```
dj-zarr-codecs>=0.1.0  # Minimum version
```

### 4. Test Codec Availability

Add checks in your pipeline setup:

```python
import datajoint as dj

REQUIRED_CODECS = ['zarr']

def check_requirements():
    available = dj.list_codecs()
    missing = [c for c in REQUIRED_CODECS if c not in available]

    if missing:
        raise ImportError(
            f"Missing required codecs: {missing}\n"
            f"Install with: pip install dj-zarr-codecs"
        )

check_requirements()
```

## See Also

- [Use Object Storage](use-object-storage.md) — Object storage configuration
- [Create Custom Codecs](create-custom-codec.md) — Build your own codecs
- [Type System](../reference/specs/type-system.md) — Complete type reference
- [dj-zarr-codecs Repository](https://github.com/datajoint/dj-zarr-codecs) — General Zarr array storage
- [dj-photon-codecs Repository](https://github.com/datajoint/dj-photon-codecs) — Photon-limited movies with compression
