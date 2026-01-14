# Documentation Versioning

This page explains how version information is indicated throughout the DataJoint documentation.

## Documentation Scope

**This documentation covers DataJoint 2.0 and later.** All code examples and tutorials use DataJoint 2.0+ syntax and APIs.

**DataJoint 2.0 is the baseline.** Features and APIs introduced in 2.0 are documented without version markers, as they are the standard for this documentation.

If you're using legacy DataJoint (version 0.14.x or earlier), please visit the [legacy documentation](https://datajoint.github.io/datajoint-python) or follow the [Migration Guide](../how-to/migrate-to-v20.md) to upgrade.

## Version Indicators

### Global Indicators

**Site-wide banner:** Every page displays a banner indicating you're viewing documentation for DataJoint 2.0+, with a link to the migration guide for legacy users.

### Feature-Level Indicators

Version admonitions are used for features introduced **after 2.0** (i.e., version 2.1 and later):

#### New Features

!!! version-added "New in 2.1"

    This indicates a feature that was introduced after the 2.0 baseline.

**Example usage:**

!!! version-added "New in 2.1"

    The `dj.Top` operator with ordering support was introduced in DataJoint 2.1.

**Note:** Features present in DataJoint 2.0 (the baseline) are not marked with version indicators.

#### Changed Behavior

!!! version-changed "Changed in 2.1"

    This indicates behavior that changed in a post-2.0 release.

**Example usage:**

!!! version-changed "Changed in 2.1"

    The `populate()` method now supports priority-based scheduling by default.

    Use `priority=50` to control execution order when using `reserve_jobs=True`.

#### Deprecated Features

!!! version-deprecated "Deprecated in 2.1, removed in 3.0"

    This indicates features that are deprecated and will be removed in future versions.

**Example usage:**

!!! version-deprecated "Deprecated in 2.1, removed in 3.0"

    The `allow_direct_insert` parameter is deprecated. Use `dj.config['safemode']` instead.

**Note:** Features deprecated at the 2.0 baseline (coming from pre-2.0) are documented in the [Migration Guide](../how-to/migrate-to-v20.md) rather than with admonitions, since this documentation assumes 2.0 as the baseline.

### Inline Version Badges

For features introduced **after 2.0**, inline version badges may appear in API reference:

- `dj.Top()` <span class="version-badge">v2.1+</span> - Top N restriction with ordering
- `some_method()` <span class="version-badge deprecated">deprecated</span> - Legacy method

**Note:** Methods and features present in DataJoint 2.0 (the baseline) do not have version badges.

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
