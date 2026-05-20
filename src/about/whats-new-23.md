# What's New in DataJoint 2.3

DataJoint 2.3 introduces **env-var-only configuration of storage**, **a public plugin-adapter contract for third-party storage protocols**, and tightens credential loading for files.

> **Upgrading from 2.2?** No breaking changes for projects using `datajoint.json` or `.secrets/`. The new env vars are purely additive.

## Overview

The DataJoint platform — and many production deployments generally — provision configuration entirely from environment variables: there is no `datajoint.json` in the container image and no `.secrets/` directory on disk. Until 2.3, this worked for the database connection (`DJ_HOST`, `DJ_USER`, `DJ_PASS`, …) but **not** for object stores: per-store credentials had to be configured through `datajoint.json` or `.secrets/stores.<name>.<attr>` files.

DataJoint 2.3 closes that gap with two new env vars, both purely additive:

- `DJ_STORES` — a JSON-encoded copy of the entire `stores` dict, in the same shape used in `datajoint.json`.
- `DJ_IGNORE_CONFIG_FILE` — a boolean flag that skips both `datajoint.json` and the secrets directory entirely.

The 2.3 release also formalizes the **storage-adapter plugin contract** (`datajoint.storage` entry-point group), which had been used internally since 2.0 but lacked a published spec. Third-party packages can now register storage protocols (Databricks Unity Catalog Volumes, custom HTTP-based stores, lab-specific archive systems, …) by subclassing `dj.StorageAdapter` and declaring an entry point.

## `DJ_STORES` — JSON-encoded stores configuration

!!! version-added "New in 2.3"
    `DJ_STORES` accepts a JSON object identical to the `stores` block of `datajoint.json`.

A single env var carries the entire `stores` dict. The format matches what users already write in `datajoint.json`, so config can be moved between file and env var by copy-paste — no per-field naming scheme to learn.

```bash
export DJ_STORES='{
  "default": "main",
  "main": {
    "protocol": "s3",
    "endpoint": "s3.amazonaws.com",
    "bucket": "my-bucket",
    "location": "my-project/production",
    "access_key": "AKIA...",
    "secret_key": "wJal..."
  }
}'
```

For plugin-registered adapters, the field names are whatever the adapter defines — `token`, `api_key`, `workspace_url`, etc.:

```bash
export DJ_STORES='{
  "uc": {
    "protocol": "databricks",
    "workspace_url": "https://my-workspace.cloud.databricks.com",
    "volume": "main.default.my_volume",
    "token": "dapibd..."
  }
}'
```

### Precedence

`DJ_STORES`, if set, replaces the `stores` block loaded from `datajoint.json` wholesale. The `.secrets/` directory still runs after `DJ_STORES` and fills in any attributes that `DJ_STORES` omits — useful if a deployment wants to inject only secrets via env vars while leaving non-sensitive store config in a file.

| Source | Priority |
|--------|----------|
| `dj.config["stores"][...]` (programmatic) | 1 (highest) |
| `DJ_STORES` env var | 2 |
| `datajoint.json` `stores` block | 3 |
| `.secrets/stores.<name>.<attr>` files | 4 (fills missing attrs only) |

### Errors

If `DJ_STORES` is set but unparseable, DataJoint raises `ValueError` at config load time with the JSON error, rather than failing later with a confusing `KeyError` from a half-loaded store.

```python
ValueError: DJ_STORES contains invalid JSON: Expecting property name enclosed in double quotes...
```

## `DJ_IGNORE_CONFIG_FILE` — skip files entirely

!!! version-added "New in 2.3"
    Set `DJ_IGNORE_CONFIG_FILE=true` to skip `datajoint.json` and the secrets directory.

For env-var-only deployments — Kubernetes pods, Lambda functions, the DataJoint platform — set:

```bash
export DJ_IGNORE_CONFIG_FILE=true
```

When `true`, DataJoint skips:

- the recursive parent-directory search for `datajoint.json`
- the project `.secrets/` directory
- the Docker/Kubernetes `/run/secrets/datajoint/` directory

Only env vars (`DJ_HOST`, `DJ_USER`, `DJ_PASS`, `DJ_STORES`, …) and defaults apply. This guarantees that no stray file in a container image can leak into config.

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `DJ_IGNORE_CONFIG_FILE` | `true`, `1`, `yes` / `false`, `0`, `no` | `false` | Skip file-based config sources |

## `.secrets/stores.<name>.<attr>` accepts any attribute

!!! version-added "New in 2.3"
    Any `.secrets/stores.<name>.<attr>` file loads into `dj.config["stores"][<name>][<attr>]`, not just `access_key` / `secret_key`.

Previously, only `.secrets/stores.<name>.access_key` and `.secrets/stores.<name>.secret_key` were honored. Plugin-registered adapters often need other field names — a Databricks adapter wants a Bearer `token`, an HTTP adapter might want `api_key`, etc.

In 2.3, any file matching `stores.<name>.<attr>` under the secrets directory is loaded:

```
.secrets/
├── stores.uc.token         # Databricks Bearer token
├── stores.main.access_key  # S3 access key
└── stores.main.secret_key  # S3 secret key
```

Config-file values and `DJ_STORES` still take precedence — secrets only fill attributes that are not already set.

## Storage-adapter plugin contract

!!! version-added "New in 2.3"
    The `datajoint.storage` entry-point group is now part of the public API.

DataJoint's built-in `file`, `s3`, `gcs`, and `azure` protocols are themselves `StorageAdapter` subclasses. Third-party packages can register additional protocols by declaring an entry point:

```toml
# pyproject.toml of a plugin package
[project.entry-points."datajoint.storage"]
databricks = "dj_databricks:DatabricksVolumesAdapter"
```

Once installed, the protocol name (`databricks` in the example) is accepted in any `stores.<name>.protocol` field, and DataJoint will use the adapter to construct the underlying `fsspec` filesystem.

See [Storage Adapter API](../reference/specs/storage-adapter-api.md) for the full plugin contract.

## See Also

- [What's New in 2.2](whats-new-22.md) — Previous release (isolated instances, thread-safe mode, graph-driven cascade)
- [Release Notes (v2.3.0)](https://github.com/datajoint/datajoint-python/releases) — GitHub changelog
- [Manage Secrets](../how-to/manage-secrets.md) — Updated for `DJ_STORES` and `DJ_IGNORE_CONFIG_FILE`
- [Configure Object Storage](../how-to/configure-storage.md) — Env-var-only deployments
- [Storage Adapter API](../reference/specs/storage-adapter-api.md) — Plugin contract
- [Configuration Reference](../reference/configuration.md) — Full env-var table
- [datajoint-python PR #1452](https://github.com/datajoint/datajoint-python/pull/1452) — Implementation
