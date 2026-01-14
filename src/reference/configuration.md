# Configuration Reference

DataJoint configuration options and settings.

## Configuration Sources

Configuration is loaded in priority order:

1. **Environment variables** (highest priority)
2. **Secrets directory** (`.secrets/`)
3. **Config file** (`datajoint.json`)
4. **Defaults** (lowest priority)

## Database Settings

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `database.host` | `DJ_HOST` | `localhost` | MySQL server hostname |
| `database.port` | `DJ_PORT` | `3306` | MySQL server port |
| `database.user` | `DJ_USER` | — | Database username |
| `database.password` | `DJ_PASS` | — | Database password |
| `database.reconnect` | — | `True` | Auto-reconnect on connection loss |
| `database.use_tls` | — | `None` | Enable TLS encryption |

## Connection Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `connection.init_function` | `None` | SQL function to run on connect |
| `connection.charset` | `""` | Character set (pymysql default) |

## Stores Configuration

Unified storage configuration for all external storage types (`<blob@>`, `<attach@>`, `<filepath@>`, `<object@>`, `<npy@>`).

**Default store:**

| Setting | Default | Description |
|---------|---------|-------------|
| `stores.default` | — | Name of the default store (used by `<blob@>`, `<object@>`, etc.) |

**Common settings (all protocols):**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.protocol` | Yes | Storage protocol: `file`, `s3`, `gcs`, `azure` |
| `stores.<name>.location` | Yes | Base path or prefix (includes project context) |
| `stores.<name>.subfolding` | No | Directory nesting for hash-addressed storage, e.g., `[2, 2]` (default: no subfolding) |
| `stores.<name>.partition_pattern` | No | Path partitioning for schema-addressed storage, e.g., `"subject_id/session_date"` (default: no partitioning) |
| `stores.<name>.token_length` | No | Random token length for schema-addressed filenames (default: `8`) |

**S3-specific settings:**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.endpoint` | Yes | S3 endpoint URL (e.g., `s3.amazonaws.com`) |
| `stores.<name>.bucket` | Yes | Bucket name |
| `stores.<name>.access_key` | Yes | S3 access key ID |
| `stores.<name>.secret_key` | Yes | S3 secret access key |
| `stores.<name>.secure` | No | Use HTTPS (default: `True`) |

**GCS-specific settings:**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.bucket` | Yes | GCS bucket name |
| `stores.<name>.token` | Yes | Authentication token path |
| `stores.<name>.project` | No | GCS project ID |

**Azure-specific settings:**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.container` | Yes | Azure container name |
| `stores.<name>.account_name` | Yes | Storage account name |
| `stores.<name>.account_key` | Yes | Storage account key |
| `stores.<name>.connection_string` | No | Alternative to account_name + account_key |

**How storage methods use stores:**

- **Hash-addressed** (`<blob@>`, `<attach@>`): `{location}/_hash/{schema}/{hash}` with optional subfolding
- **Schema-addressed** (`<object@>`, `<npy@>`): `{location}/_schema/{partition}/{schema}/{table}/{key}/{field}.{token}.{ext}` with optional partitioning
- **Filepath** (`<filepath@>`): `{location}/{user_path}` (user-managed, cannot use `_hash/` or `_schema/`)

All storage methods share the same stores and default store. DataJoint reserves `_hash/` and `_schema/` sections for managed storage; `<filepath@>` references can use any other paths.

**Path structure examples:**

Without partitioning:
```
{location}/_hash/{schema}/ab/cd/abcd1234...                    # hash-addressed with subfolding
{location}/_schema/{schema}/{table}/{key}/data.x8f2a9b1.zarr   # schema-addressed, no partitioning
```

With `partition_pattern: "subject_id/session_date"`:
```
{location}/_schema/subject_id=042/session_date=2024-01-15/{schema}/{table}/{remaining_key}/data.x8f2a9b1.zarr
```

If table lacks partition attributes, it follows normal path structure.

**Credentials should be stored in secrets:**

```
.secrets/
├── stores.main.access_key
├── stores.main.secret_key
├── stores.archive.access_key
└── stores.archive.secret_key
```

## Jobs Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `jobs.auto_refresh` | `True` | Auto-refresh job queue on populate |
| `jobs.keep_completed` | `False` | Retain success records in jobs table |
| `jobs.stale_timeout` | `3600` | Seconds before stale job cleanup |
| `jobs.default_priority` | `5` | Default priority (0-255, lower = more urgent) |
| `jobs.version_method` | `None` | Version tracking: `git`, `none`, or `None` (disabled) |
| `jobs.add_job_metadata` | `False` | Add hidden metadata to computed tables |
| `jobs.allow_new_pk_fields_in_computed_tables` | `False` | Allow non-FK primary key fields |

## Display Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `display.limit` | `12` | Max rows to display |
| `display.width` | `14` | Column width |
| `display.show_tuple_count` | `True` | Show row count in output |

## Top-Level Settings

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `loglevel` | `DJ_LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `safemode` | — | `True` | Require confirmation for destructive operations |
| `enable_python_native_blobs` | — | `True` | Allow Python-native blob serialization |
| `cache` | — | `None` | Path for query result cache |
| `query_cache` | — | `None` | Path for compiled query cache |
| `download_path` | — | `.` | Download location for attachments/filepaths |

## Example Configuration

### datajoint.json (Non-sensitive settings)

```json
{
    "database.host": "mysql.example.com",
    "database.port": 3306,
    "stores": {
        "default": "main",
        "main": {
            "protocol": "s3",
            "endpoint": "s3.amazonaws.com",
            "bucket": "datajoint-bucket",
            "location": "neuroscience-lab/production",
            "partition_pattern": "subject_id/session_date",
            "token_length": 8
        },
        "archive": {
            "protocol": "s3",
            "endpoint": "s3.amazonaws.com",
            "bucket": "archive-bucket",
            "location": "neuroscience-lab/long-term",
            "subfolding": [2, 2]
        }
    },
    "jobs": {
        "add_job_metadata": true
    }
}
```

### .secrets/ (Credentials - never commit!)

```
.secrets/
├── database.user                      # analyst
├── database.password                  # dbpass123
├── stores.main.access_key             # AKIAIOSFODNN7EXAMPLE
├── stores.main.secret_key             # wJalrXUtnFEMI/K7MDENG...
├── stores.archive.access_key          # AKIAIOSFODNN8EXAMPLE
└── stores.archive.secret_key          # xKbmsYVuoGFNJ/L8NEOH...
```

Add `.secrets/` to `.gitignore`:

```bash
echo ".secrets/" >> .gitignore
```

### Environment Variables (Alternative to .secrets/)

```bash
# Database
export DJ_HOST=mysql.example.com
export DJ_USER=analyst
export DJ_PASS=secret
```

**Note:** Per-store credentials must be configured in `datajoint.json` or `.secrets/` — environment variable overrides are not supported for nested store configurations.

## API Reference

See [Settings API](../api/datajoint/settings.md) for programmatic access.
