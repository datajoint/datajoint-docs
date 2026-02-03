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
| `database.backend` | `DJ_BACKEND` | `mysql` | Database backend: `mysql` or `postgresql` *(new in 2.1)* |
| `database.host` | `DJ_HOST` | `localhost` | Database server hostname |
| `database.port` | `DJ_PORT` | `3306`/`5432` | Database server port (auto-detects from backend) |
| `database.user` | `DJ_USER` | — | Database username (required) |
| `database.password` | `DJ_PASS` | — | Database password (required) |
| `database.reconnect` | — | `True` | Auto-reconnect on connection loss |
| `database.use_tls` | `DJ_USE_TLS` | `None` | Enable TLS encryption *(env var new in 2.1)* |
| `database.database_prefix` | `DJ_DATABASE_PREFIX` | `""` | Prefix for database/schema names |
| `database.create_tables` | `DJ_CREATE_TABLES` | `True` | Default for `Schema(create_tables=)`. Set `False` for production mode |

## Connection Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `connection.init_function` | `None` | SQL function to run on connect |
| `connection.charset` | `""` | Character set (pymysql default) |

## Stores Configuration

Unified storage configuration for all in-store types (`<blob@>`, `<attach@>`, `<filepath@>`, `<object@>`, `<npy@>`).

**Default stores:**

DataJoint uses two default settings to reflect the architectural distinction between integrated and reference storage:

| Setting | Default | Description |
|---------|---------|-------------|
| `stores.default` | — | Default store for integrated storage (`<blob@>`, `<attach@>`, `<object@>`, `<npy@>`) |
| `stores.filepath_default` | — | Default store for filepath references (`<filepath@>`) — often different from `stores.default` |

**Why separate defaults?** Hash and schema-addressed storage are integrated into the Object-Augmented Schema (OAS)—DataJoint manages paths, lifecycle, and integrity. Filepath storage is user-managed references to existing files—DataJoint only stores the path. These are architecturally distinct and often use different storage locations.

**Common settings (all protocols):**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.protocol` | Yes | Storage protocol: `file`, `s3`, `gcs`, `azure` |
| `stores.<name>.location` | Yes | Base path or prefix (includes project context) |
| `stores.<name>.hash_prefix` | No | Path prefix for hash-addressed section (default: `"_hash"`) |
| `stores.<name>.schema_prefix` | No | Path prefix for schema-addressed section (default: `"_schema"`) |
| `stores.<name>.filepath_prefix` | No | Required path prefix for filepath section, or `null` for unrestricted (default: `null`) |
| `stores.<name>.subfolding` | No | Directory nesting for hash-addressed storage, e.g., `[2, 2]` (default: no subfolding) |
| `stores.<name>.partition_pattern` | No | Path partitioning for schema-addressed storage, e.g., `"subject_id/session_date"` (default: no partitioning) |
| `stores.<name>.token_length` | No | Random token length for schema-addressed filenames (default: `8`) |

**Storage sections:**

Each store is divided into sections defined by prefix configuration. The `*_prefix` parameters set the path prefix for each storage section:

- **`hash_prefix`**: Defines the hash-addressed section for `<blob@>` and `<attach@>` (default: `"_hash"`)
- **`schema_prefix`**: Defines the schema-addressed section for `<object@>` and `<npy@>` (default: `"_schema"`)
- **`filepath_prefix`**: Optionally restricts the filepath section for `<filepath@>` (default: `null` = unrestricted)

Prefixes must be mutually exclusive (no prefix can be a parent/child of another). This allows mapping DataJoint to existing storage layouts:

```json
{
  "stores": {
    "legacy": {
      "protocol": "file",
      "location": "/data/existing_storage",
      "hash_prefix": "content_addressed",      // Path prefix for hash section
      "schema_prefix": "structured_data",       // Path prefix for schema section
      "filepath_prefix": "raw_files"            // Path prefix for filepath section
    }
  }
}
```

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

- **Hash-addressed** (`<blob@>`, `<attach@>`): `{location}/{hash_prefix}/{schema}/{hash}` with optional subfolding
- **Schema-addressed** (`<object@>`, `<npy@>`): `{location}/{schema_prefix}/{partition}/{schema}/{table}/{key}/{field}.{token}.{ext}` with optional partitioning
- **Filepath** (`<filepath@>`): `{location}/{filepath_prefix}/{user_path}` (user-managed, cannot use hash or schema prefixes)

All storage methods share the same stores and default store. DataJoint reserves the configured `hash_prefix` and `schema_prefix` sections for managed storage; `<filepath@>` references can use any other paths (unless `filepath_prefix` is configured to restrict them).

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

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `display.limit` | — | `12` | Max rows to display |
| `display.width` | — | `14` | Column width |
| `display.show_tuple_count` | — | `True` | Show row count in output |
| `display.diagram_direction` | `DJ_DIAGRAM_DIRECTION` | `LR` | Diagram layout: `LR` (left-right) or `TB` (top-bottom) *(new in 2.1)* |

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
        "filepath_default": "raw_data",
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
        },
        "raw_data": {
            "protocol": "file",
            "location": "/mnt/acquisition",
            "filepath_prefix": "recordings"
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

## Programmatic Access

### Reading and Writing Settings

Access settings using dot notation on `dj.config`:

```python
import datajoint as dj

# Read settings
print(dj.config.database.host)
print(dj.config.display.diagram_direction)

# Write settings
dj.config.database.host = "mysql.example.com"
dj.config.display.diagram_direction = "TB"
```

### Temporary Overrides

Use `dj.config.override()` to temporarily change settings within a context:

```python
with dj.config.override(safemode=False):
    # safemode is False here
    (Table & key).delete()
# safemode is restored to original value
```

**Nested settings syntax:** Since Python doesn't allow dots in keyword argument names, use double underscores (`__`) to access nested settings in `override()`:

```python
# These are equivalent:
dj.config.display.diagram_direction = "TB"  # direct assignment

with dj.config.override(display__diagram_direction="TB"):  # in override()
    ...
```

The double underscore maps to the dot-notation path: `display__diagram_direction` → `display.diagram_direction`.

## API Reference

See [Settings API](../api/datajoint/settings.md/) for programmatic access.
