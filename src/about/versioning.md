# Documentation Versioning

This page explains how version information is indicated throughout the DataJoint documentation.

## Documentation Scope

**This documentation covers DataJoint 2.0 and later.** All code examples and tutorials use DataJoint 2.0+ syntax and APIs.

If you're using legacy DataJoint (version 0.14.x or earlier), please visit the [legacy documentation](https://datajoint.github.io/datajoint-python) or follow the [Migration Guide](../how-to/migrate-to-v20.md) to upgrade.

## Version Indicators

### Global Indicators

**Site-wide banner:** Every page displays a banner indicating you're viewing documentation for DataJoint 2.0+, with a link to the migration guide for legacy users.

**Footer:** The footer shows which version of DataJoint this documentation covers.

### Feature-Level Indicators

For specific features, you'll see version admonitions:

#### New Features

!!! version-added "New in 2.0"

    This indicates a feature that was introduced in DataJoint 2.0.

**Example from documentation:**

!!! version-added "New in 2.0"

    Semantic matching validates joins based on lineage tracking. This feature was introduced in DataJoint 2.0.

#### Changed Behavior

!!! version-changed "Changed in 2.0"

    This indicates behavior that changed from previous versions.

**Example from documentation:**

!!! version-changed "Changed in 2.0"

    The fetch API was redesigned in 2.0. Use `to_dicts()` or `to_arrays()` instead of `fetch()`.

    **Legacy (pre-2.0):** `data = table.fetch()`
    **Current (2.0+):** `data = table.to_dicts()`

#### Deprecated Features

!!! version-deprecated "Deprecated in 2.0, removed in 3.0"

    This indicates features that are deprecated and will be removed in future versions.

**Example from documentation:**

!!! version-deprecated "Deprecated in 2.0, removed in 3.0"

    The `external` storage type is deprecated. Use unified stores with `<blob@store>` syntax instead.

### Inline Version Badges

In API reference documentation, you may see inline version badges:

- `to_dicts()` <span class="version-badge">v2.0+</span> - Retrieve as list of dicts
- `fetch()` <span class="version-badge deprecated">deprecated</span> - Legacy fetch API

## Checking Your Version

To check which version of DataJoint you're using:

```python
import datajoint as dj
print(dj.__version__)
```

- **Version 2.0 or higher:** You're on the current version
- **Version 0.14.x or lower:** You're on legacy DataJoint

## Migration Path

If you're upgrading from legacy DataJoint (pre-2.0):

1. **Review** the [What's New in 2.0](../explanation/whats-new-2.md) page to understand major changes
2. **Follow** the [Migration Guide](../how-to/migrate-to-v20.md) for step-by-step upgrade instructions
3. **Reference** this documentation for updated syntax and APIs

## Legacy Documentation

For DataJoint 0.x documentation, visit:

**[datajoint.github.io/datajoint-python](https://datajoint.github.io/datajoint-python)**

## Version History

| Version | Release Date | Major Changes |
|---------|--------------|---------------|
| 2.0 | 2026 | Redesigned fetch API, unified stores, per-table jobs, semantic matching |
| 0.14.x | 2020-2025 | Legacy version with external storage |
| 0.13.x | 2019 | Legacy version |

For complete version history, see the [changelog](https://github.com/datajoint/datajoint-python/releases).
