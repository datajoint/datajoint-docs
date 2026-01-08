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

## Object Storage Settings

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `stores.default` | — | — | Default store name |
| `stores.<name>.protocol` | — | `file` | Storage protocol (file, s3, gs) |
| `stores.<name>.endpoint` | — | — | S3-compatible endpoint URL |
| `stores.<name>.bucket` | — | — | Bucket or root path |

## Jobs Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `jobs.auto_refresh` | `True` | Auto-refresh job queue on populate |
| `jobs.keep_completed` | `False` | Retain success records |
| `jobs.stale_timeout` | `3600` | Seconds before stale job cleanup |
| `jobs.add_job_metadata` | `False` | Add hidden metadata to computed tables |

## Display Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `display.limit` | `12` | Max rows to display |
| `display.width` | `14` | Column width |

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
