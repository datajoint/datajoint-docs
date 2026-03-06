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

This organization makes object storage browsable and self-documenting.

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
# Requires: datajoint>=2.0.0
```

Upgrade DataJoint if needed:

```bash
pip install --upgrade datajoint
```

## Versioning and Backward Compatibility

Plugin codecs evolve over time. Following versioning best practices ensures your data remains accessible across codec updates.

### Built-in vs Plugin Codec Versioning

**Built-in codecs** (`<blob>`, `<npy@>`, `<object@>`, etc.) are versioned with DataJoint:
- ✅ Shipped with datajoint-python
- ✅ Versioned by DataJoint release (2.0.0, 2.1.0, 3.0.0)
- ✅ Upgraded when you upgrade DataJoint
- ✅ Stability guaranteed by DataJoint's semantic versioning
- ❌ **No explicit codec_version field needed** - DataJoint version is the codec version

**Plugin codecs** (dj-zarr-codecs, dj-photon-codecs, etc.) have independent lifecycles:
- ✅ Installed separately from DataJoint
- ✅ Independent version numbers (0.1.0 → 1.0.0 → 2.0.0)
- ✅ Users choose when to upgrade
- ✅ **Must include explicit codec_version field** for backward compatibility

**Why the difference?**

Plugin codecs evolve independently and need to handle data encoded by different plugin versions. Built-in codecs are part of DataJoint's API surface and evolve with the framework itself. When you upgrade DataJoint 2.0 → 3.0, you expect potential breaking changes. When you upgrade a plugin 1.0 → 2.0 while keeping DataJoint 2.0, backward compatibility is critical.

**How built-in codecs handle versioning:**

Built-in formats have **intrinsic versioning** - the format version is embedded in the data itself:

- `<blob>` — Protocol header (`mYm\0` or `dj0\0`) at start of blob
- `<npy@>` — NumPy format version in `.npy` file header
- `<object@>` — Self-describing directory structure
- `<attach>` — Filename + content (format-agnostic)

When DataJoint needs to change a built-in codec's format, it can detect the old format from the embedded version information and handle migration transparently. This is why built-in codecs don't need an explicit `codec_version` field in database metadata.

### Version Strategy

**Two version numbers matter for plugin codecs:**

1. **Package version** (semantic versioning: `0.1.0`, `1.0.0`, `2.0.0`)
   - For codec package releases
   - Follows standard semantic versioning

2. **Data format version** (stored with each encoded value)
   - Tracks storage format changes
   - Enables decode() to handle multiple formats

### Implementing Versioning

**Include version in encoded metadata:**

```python
def encode(self, value, *, key=None, store_name=None):
    # ... encoding logic ...

    return {
        "path": path,
        "store": store_name,
        "codec_version": "1.0",  # Data format version
        "shape": list(value.shape),
        "dtype": str(value.dtype),
    }
```

**Handle multiple versions in decode:**

```python
def decode(self, stored, *, key=None):
    version = stored.get("codec_version", "1.0")  # Default for old data

    if version == "2.0":
        return self._decode_v2(stored)
    elif version == "1.0":
        return self._decode_v1(stored)
    else:
        raise DataJointError(f"Unsupported codec version: {version}")
```

### When to Bump Versions

**Bump data format version when:**
- ✅ Changing storage structure or encoding algorithm
- ✅ Modifying metadata schema
- ✅ Changing compression parameters that affect decode

**Don't bump for:**
- ❌ Bug fixes that don't affect stored data format
- ❌ Performance improvements to encode/decode logic
- ❌ Adding new optional features (store version in attributes instead)

### Backward Compatibility Patterns

**Pattern 1: Version dispatch in decode()**

```python
class MyCodec(SchemaCodec):
    name = "mycodec"
    CURRENT_VERSION = "2.0"

    def encode(self, value, *, key=None, store_name=None):
        # Always encode with current version
        metadata = {
            "codec_version": self.CURRENT_VERSION,
            # ... other metadata ...
        }
        return metadata

    def decode(self, stored, *, key=None):
        version = stored.get("codec_version", "1.0")

        if version == "2.0":
            # Current version - optimized path
            return self._decode_current(stored)
        elif version == "1.0":
            # Legacy version - compatibility path
            return self._decode_legacy_v1(stored)
        else:
            raise DataJointError(
                f"Cannot decode {self.name} version {version}. "
                f"Upgrade codec package or migrate data."
            )
```

**Pattern 2: Zarr attributes for feature versions**

For codecs using Zarr (like dj-zarr-codecs, dj-photon-codecs):

```python
def encode(self, value, *, key=None, store_name=None):
    # ... write to Zarr ...

    z = zarr.open(store_map, mode="r+")
    z.attrs["codec_version"] = "2.0"
    z.attrs["codec_name"] = self.name
    z.attrs["feature_flags"] = ["compression", "chunking"]

    return {
        "path": path,
        "store": store_name,
        "codec_version": "2.0",  # Also in DB for quick access
    }

def decode(self, stored, *, key=None):
    z = zarr.open(store_map, mode="r")
    version = z.attrs.get("codec_version", "1.0")

    # Handle version-specific decoding
    if version == "2.0":
        return z  # Return Zarr array directly
    else:
        return self._migrate_v1_to_v2(z)
```

### Migration Strategies

**Strategy 1: Lazy migration (recommended)**

Old data is migrated when accessed:

```python
def decode(self, stored, *, key=None):
    version = stored.get("codec_version", "1.0")

    if version == "1.0":
        # Decode old format
        data = self._decode_v1(stored)

        # Optionally: re-encode to new format in background
        # (requires database write access)
        return data

    return self._decode_current(stored)
```

**Strategy 2: Explicit migration script**

For breaking changes, provide migration tools:

```python
# migration_tool.py
def migrate_table_to_v2(table, field_name):
    """Migrate all rows to codec version 2.0."""
    for key in table.fetch("KEY"):
        # Fetch with old codec
        data = (table & key).fetch1(field_name)

        # Re-insert with new codec (triggers encode)
        table.update1({**key, field_name: data})
```

**Strategy 3: Deprecation warnings**

```python
def decode(self, stored, *, key=None):
    version = stored.get("codec_version", "1.0")

    if version == "1.0":
        import warnings
        warnings.warn(
            f"Reading {self.name} v1.0 data. Support will be removed in v3.0. "
            f"Please migrate: pip install {self.name}-migrate && migrate-data",
            DeprecationWarning
        )
        return self._decode_v1(stored)
```

### Real-World Example: dj-photon-codecs Evolution

**Version 1.0** (current):
- Stores Anscombe-transformed data
- Fixed compression (Blosc zstd level 5)
- Fixed chunking (100 frames)

**Hypothetical Version 2.0** (backward compatible):
```python
def encode(self, value, *, key=None, store_name=None):
    # New: configurable compression
    compression_level = getattr(self, 'compression_level', 5)

    zarr.save_array(
        store_map,
        transformed,
        compressor=zarr.Blosc(cname="zstd", clevel=compression_level),
    )

    z = zarr.open(store_map, mode="r+")
    z.attrs["codec_version"] = "2.0"
    z.attrs["compression_level"] = compression_level

    return {
        "path": path,
        "codec_version": "2.0",  # <-- NEW
        # ... rest same ...
    }

def decode(self, stored, *, key=None):
    z = zarr.open(store_map, mode="r")
    version = z.attrs.get("codec_version", "1.0")

    # Both versions return zarr.Array - fully compatible!
    if version in ("1.0", "2.0"):
        return z
    else:
        raise DataJointError(f"Unsupported version: {version}")
```

### Testing Version Compatibility

Include tests for version compatibility:

```python
def test_decode_v1_data():
    """Ensure new codec can read old data."""
    # Load fixture with v1.0 data
    old_data = load_v1_fixture()

    # Decode with current codec
    codec = PhotonCodec()
    result = codec.decode(old_data)

    assert result.shape == (1000, 512, 512)
    assert result.dtype == np.float64
```

### Package Version Guidelines

Follow semantic versioning for codec packages:

- **Patch (0.1.0 → 0.1.1)**: Bug fixes, no data format changes
- **Minor (0.1.0 → 0.2.0)**: New features, backward compatible
- **Major (0.1.0 → 1.0.0)**: Breaking changes (may require migration)

**Example changelog:**

```
v2.0.0 (2026-02-01) - BREAKING
  - Changed default compression from zstd-5 to zstd-3
  - Data format v2.0 (can still read v1.0)
  - Migration guide: docs/migration-v2.md

v1.1.0 (2026-01-15)
  - Added configurable chunk sizes (backward compatible)
  - Data format still v1.0

v1.0.1 (2026-01-10)
  - Fixed edge case in Anscombe inverse transform
  - Data format unchanged (v1.0)
```

## Creating Your Own Codecs

If you need a codec that doesn't exist yet, see:

- [Create Custom Codecs](create-custom-codec.md) — Step-by-step guide
- [Codec API Specification](../reference/specs/codec-api.md/) — Technical reference
- [Custom Codecs Explanation](../explanation/custom-codecs.md/) — Design concepts

Consider publishing your codec as a package so others can benefit!

## Best Practices

### 1. Install Codecs with Your Project

Add plugin codecs to your project dependencies:

**requirements.txt:**
```
datajoint>=2.0.0
dj-zarr-codecs>=0.1.0
```

**pyproject.toml:**
```toml
dependencies = [
    "datajoint>=2.0.0",
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
- datajoint>=2.0.0
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
- [Type System](../reference/specs/type-system.md/) — Complete type reference
- [dj-zarr-codecs Repository](https://github.com/datajoint/dj-zarr-codecs) — General Zarr array storage
- [dj-photon-codecs Repository](https://github.com/datajoint/dj-photon-codecs) — Photon-limited movies with compression
