# Deploy to Production

Configure DataJoint for production environments with controlled schema changes and project isolation.

## Overview

Development and production environments have different requirements:

| Concern | Development | Production |
| --------- | ------------- | ------------ |
| Schema changes | Automatic table creation | Controlled, explicit changes only |
| Naming | Ad-hoc schema names | Consistent project prefixes |
| Configuration | Local settings | Environment-based |

DataJoint 2.0+ provides settings to enforce production discipline.

## Prevent Automatic Table Creation

By default, DataJoint creates tables automatically when you first access them. This is convenient during development but dangerous in production—a typo or code bug could create unintended tables.

### Enable Production Mode

Set `create_tables=False` to prevent automatic table creation:

```python
import datajoint as dj

# Production mode: no automatic table creation
dj.config.database.create_tables = False
```

Or via environment variable:

```bash
export DJ_CREATE_TABLES=false
```

Or in `datajoint.json`:

```json
{
  "database": {
    "create_tables": false
  }
}
```

### What Changes

With `create_tables=False`:

| Action | Development (True) | Production (False) |
| -------- | ------------------- | ------------------- |
| Access existing table | Works | Works |
| Access missing table | Creates it | **Raises error** |
| Explicit `Schema(create_tables=True)` | Creates | Creates (override) |

### Example: Production Safety

```python
import datajoint as dj

dj.config.database.create_tables = False
schema = dj.Schema('myproject_ephys')

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int
    ---
    path : varchar(255)
    """

# If table doesn't exist in database:
Recording()  # Raises DataJointError: Table not found
```

### Override for Migrations

When you need to create tables during a controlled migration:

```python
# Explicit override for this schema only
schema = dj.Schema('myproject_ephys', create_tables=True)

@schema
class NewTable(dj.Manual):
    definition = """..."""

NewTable()  # Creates the table
```

## Use Schema Name Prefixes

When multiple projects share a database server, give the schemas of each project a common prefix to avoid naming collisions and organize schemas.

### Name Schemas with the Prefix

Write the prefix into the name passed to `dj.Schema`. DataJoint uses the name as given:

```python
import datajoint as dj

subject_schema = dj.Schema('myproject_subject')
session_schema = dj.Schema('myproject_session')
ephys_schema = dj.Schema('myproject_ephys')
```

To keep the prefix in one place, define it once in the pipeline code. A pipeline that runs against several targets with different prefixes can read it from a variable of its own:

```python
import os

import datajoint as dj

# MYPROJECT_SCHEMA_PREFIX is the pipeline's own variable, not a DataJoint setting
SCHEMA_PREFIX = os.environ.get('MYPROJECT_SCHEMA_PREFIX', 'myproject_')

subject_schema = dj.Schema(SCHEMA_PREFIX + 'subject')   # myproject_subject
session_schema = dj.Schema(SCHEMA_PREFIX + 'session')   # myproject_session
ephys_schema = dj.Schema(SCHEMA_PREFIX + 'ephys')       # myproject_ephys
```

!!! version-deprecated "Deprecated in 2.2.1"
    The `database.database_prefix` setting (`DJ_DATABASE_PREFIX`) is deprecated and will be
    removed in a future release. It is not applied to schema names. While it is set, activating a
    schema issues a `DeprecationWarning`. Do not use it in production configuration. To select a
    PostgreSQL database, use `database.name`.

### Benefits

- **Isolation**: Multiple projects coexist without conflicts
- **Visibility**: Easy to identify which schemas belong to which project
- **Permissions**: Grant access by prefix pattern (`myproject_*`)
- **Cleanup**: Drop all project schemas by prefix

### Database Permissions by Prefix

```sql
-- Grant access to all schemas with prefix
GRANT ALL PRIVILEGES ON `myproject_%`.* TO 'developer'@'10.0.0.%';

-- Read-only access to another project
GRANT SELECT ON `otherproject_%`.* TO 'developer'@'10.0.0.%';
```

!!! warning "Restrict Host Access"
    Avoid using `'%'` for the host in production GRANT statements—this allows
    connections from any IP address. Use specific IP addresses or subnet patterns
    like `'10.0.0.%'` to limit access to your internal network.

## Environment-Based Configuration

Use different configurations for development, staging, and production.

### Configuration Hierarchy

DataJoint loads settings in priority order:

1. **Environment variables** (highest priority)
2. **Config file** (`datajoint.json`)
3. **Secrets directory** (`.secrets/`)
4. **Defaults** (lowest priority)

An environment variable takes precedence over `datajoint.json` for every setting that has one, so one committed `datajoint.json` can serve every environment, with the production values set in the environment. The [Configuration Reference](../reference/configuration.md) names each setting's variable.

!!! version-changed "Changed in 2.3.7"
    Before 2.3.7, a value in `datajoint.json` replaced the environment variable for some settings,
    among them `database.reconnect` (`DJ_RECONNECT`), `database.use_tls` (`DJ_USE_TLS`), `safemode`
    (`DJ_SAFEMODE`) and the jobs settings (`DJ_JOBS_*`). A deployment that relied on the file to
    override one of these variables should unset the variable.

### Development Setup

**datajoint.json** (committed):
```json
{
  "database": {
    "host": "localhost",
    "create_tables": true
  }
}
```

**.secrets/database.user**:
```
dev_user
```

### Production Setup

Override via environment:

```bash
# Production database
export DJ_HOST=prod-db.example.com
export DJ_USER=prod_user
export DJ_PASS=prod_password

# Production mode
export DJ_CREATE_TABLES=false

# Disable interactive prompts
export DJ_SAFEMODE=false
```

### Docker/Kubernetes Example

DataJoint automatically loads credentials from `/run/secrets/datajoint/` when that directory exists (standard Docker/Kubernetes secrets mount point).

```yaml
# docker-compose.yaml
services:
  worker:
    image: my-pipeline:latest
    environment:
      - DJ_HOST=db.example.com
      - DJ_CREATE_TABLES=false
    volumes:
      # Mount secrets directory
      - type: bind
        source: ./secrets
        target: /run/secrets/datajoint
        read_only: true
```

Create the secrets directory with credential files:

```bash
mkdir -p secrets
echo "prod_user" > secrets/database.user
echo "prod_password" > secrets/database.password
chmod 600 secrets/*
```

For Kubernetes, use a Secret mounted to `/run/secrets/datajoint/`:

```yaml
# kubernetes deployment
spec:
  containers:
    - name: worker
      volumeMounts:
        - name: dj-secrets
          mountPath: /run/secrets/datajoint
          readOnly: true
  volumes:
    - name: dj-secrets
      secret:
        secretName: datajoint-credentials
```

## Complete Production Configuration

### datajoint.json (committed)

```json
{
  "database": {
    "host": "localhost",
    "port": 3306
  },
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-org-data",
      "location": "myproject"
    }
  }
}
```

### Production Environment Variables

```bash
# Database
export DJ_HOST=prod-mysql.example.com
export DJ_USER=prod_service
export DJ_PASS=<from-secret-manager>

# Production behavior
export DJ_CREATE_TABLES=false
export DJ_SAFEMODE=false

# Logging
export DJ_LOG_LEVEL=WARNING

# Optional (new in 2.3.7): refuse a compressed blob that would expand beyond 2 GiB
export DJ_BLOB_MAX_DECOMPRESSED_SIZE=2147483648
```

`DJ_LOG_LEVEL` can also be set as `loglevel` in `datajoint.json`; from 2.3.7, that value applies from import on. `DJ_BLOB_MAX_DECOMPRESSED_SIZE` bounds the memory that one blob can take when the pipeline reads blobs written by others; see [Blob Settings](../reference/configuration.md#blob-settings).

### Verification Script

```python
#!/usr/bin/env python
"""Verify production configuration before deployment."""
import datajoint as dj

def verify_production_config():
    """Check that production settings are correctly applied."""
    errors = []

    # Check create_tables is disabled
    if dj.config.database.create_tables:
        errors.append("create_tables should be False in production")

    # Check not pointing to localhost
    if dj.config.database.host == 'localhost':
        errors.append("database.host is localhost - expected production host")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return False

    print("Production configuration verified")
    return True

if __name__ == '__main__':
    import sys
    sys.exit(0 if verify_production_config() else 1)
```

## Summary

| Setting | Development | Production |
| --------- | ------------- | ------------ |
| `database.create_tables` | `true` | `false` |
| `safemode` | `true` | `false` (automated) |
| `loglevel` | `DEBUG` | `WARNING` |

## See Also

- [Manage Pipeline Project](manage-pipeline-project.md) — Project organization
- [Configuration Reference](../reference/configuration.md/) — All settings
- [Manage Secrets](manage-secrets.md) — Credential management
