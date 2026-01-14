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

Hash-addressed storage for `<blob@store>`, `<attach@store>`, `<filepath@store>`.

**Common settings (all protocols):**

| Setting | Required | Description |
|---------|----------|-------------|
| `stores.<name>.protocol` | Yes | Storage protocol: `file`, `s3`, `gcs`, `azure` |
| `stores.<name>.location` | Yes | Base path or prefix |
| `stores.<name>.subfolding` | No | Directory nesting tuple, e.g., `[2, 2]` for `ab/cd/abcd...` |

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

**Credentials should be stored in secrets:**

```
.secrets/
├── stores.main.access_key
├── stores.main.secret_key
├── stores.archive.access_key
└── stores.archive.secret_key
```

## Object Storage Settings

For schema-addressed object storage (`<object@>`, `<npy@>`):

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `object_storage.project_name` | `DJ_OBJECT_STORAGE_PROJECT_NAME` | — | Unique project identifier (required) |
| `object_storage.protocol` | `DJ_OBJECT_STORAGE_PROTOCOL` | — | Storage protocol: `file`, `s3`, `gcs`, `azure` |
| `object_storage.location` | `DJ_OBJECT_STORAGE_LOCATION` | — | Base path or bucket prefix |
| `object_storage.bucket` | `DJ_OBJECT_STORAGE_BUCKET` | — | Bucket name (S3, GCS) |
| `object_storage.container` | `DJ_OBJECT_STORAGE_CONTAINER` | — | Container name (Azure) |
| `object_storage.endpoint` | `DJ_OBJECT_STORAGE_ENDPOINT` | — | S3 endpoint URL |
| `object_storage.access_key` | `DJ_OBJECT_STORAGE_ACCESS_KEY` | — | Access key |
| `object_storage.secret_key` | `DJ_OBJECT_STORAGE_SECRET_KEY` | — | Secret key |
| `object_storage.secure` | `DJ_OBJECT_STORAGE_SECURE` | `True` | Use HTTPS |
| `object_storage.partition_pattern` | — | — | Path pattern with `{attribute}` placeholders |
| `object_storage.token_length` | — | `8` | Random suffix length for filenames |
| `object_storage.default_store` | — | — | Default store name when not specified |

**Named object stores** can be configured under `object_storage.stores.<name>.*` with the same settings as above.

**Credentials** can be stored in `.secrets/` as an alternative to environment variables:

```
.secrets/
├── object_storage.access_key
└── object_storage.secret_key
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
        "main": {
            "protocol": "s3",
            "endpoint": "s3.amazonaws.com",
            "bucket": "my-data-bucket",
            "location": "datajoint/main"
        },
        "archive": {
            "protocol": "s3",
            "endpoint": "s3.amazonaws.com",
            "bucket": "archive-bucket",
            "location": "datajoint/archive"
        }
    },
    "object_storage": {
        "project_name": "neuroscience_lab",
        "protocol": "s3",
        "endpoint": "s3.amazonaws.com",
        "bucket": "objects-bucket",
        "location": "datajoint/objects"
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
├── stores.archive.secret_key          # xKbmsYVuoGFNJ/L8NEOH...
├── object_storage.access_key          # AKIAIOSFODNN9EXAMPLE
└── object_storage.secret_key          # yLcntZWvpHGOK/M9OFPI...
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

# Object Storage (for <object@>, <npy@>)
export DJ_OBJECT_STORAGE_ACCESS_KEY=AKIAIOSFODNN9EXAMPLE
export DJ_OBJECT_STORAGE_SECRET_KEY=yLcntZWvpHGOK/M9OFPI...
```

**Note:** Per-store credentials (for `<blob@>`, `<attach@>`) must be configured in `datajoint.json` or `.secrets/` — environment variable overrides are not supported for nested store configurations.

## API Reference

See [Settings API](../api/datajoint/settings.md) for programmatic access.
