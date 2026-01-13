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

## External Storage Credentials

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `external.aws_access_key_id` | `DJ_AWS_ACCESS_KEY_ID` | — | AWS access key |
| `external.aws_secret_access_key` | `DJ_AWS_SECRET_ACCESS_KEY` | — | AWS secret key |

## Stores Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `stores.<name>.protocol` | — | Storage protocol: `file`, `s3`, `gcs`, `azure` |
| `stores.<name>.location` | — | Base path or prefix |
| `stores.<name>.endpoint` | — | S3-compatible endpoint URL |
| `stores.<name>.bucket` | — | Bucket name (S3, GCS) |
| `stores.<name>.container` | — | Container name (Azure) |
| `stores.<name>.access_key` | — | Access key for cloud storage |
| `stores.<name>.secret_key` | — | Secret key for cloud storage |
| `stores.<name>.secure` | `True` | Use HTTPS |
| `stores.<name>.subfolding` | `(2, 2)` | Directory nesting for hash-addressed files |

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

Named object stores can be configured under `object_storage.stores.<name>.*`.

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

### datajoint.json

```json
{
    "database.host": "mysql.example.com",
    "database.port": 3306,
    "stores": {
        "main": {
            "protocol": "s3",
            "endpoint": "s3.amazonaws.com",
            "bucket": "my-data-bucket"
        }
    },
    "jobs": {
        "add_job_metadata": true
    }
}
```

### Environment Variables

```bash
export DJ_HOST=mysql.example.com
export DJ_USER=analyst
export DJ_PASS=secret
```

### Secrets Directory

```
.secrets/
├── database.user      # Contains: analyst
├── database.password  # Contains: secret
└── aws.access_key_id  # Contains: AKIA...
```

## API Reference

See [Settings API](../api/datajoint/settings.md) for programmatic access.
