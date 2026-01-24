# Deploy to Production

Configure DataJoint for production environments with controlled schema changes and project isolation.

## Overview

Development and production environments have different requirements:

| Concern | Development | Production |
|---------|-------------|------------|
| Schema changes | Automatic table creation | Controlled, explicit changes only |
| Naming | Ad-hoc schema names | Consistent project prefixes |
| Configuration | Local settings | Environment-based |

DataJoint 2.0 provides settings to enforce production discipline.

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
|--------|-------------------|-------------------|
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

## Use Schema Prefixes

When multiple projects share a database server, use prefixes to avoid naming collisions and organize schemas.

### Configure Project Prefix

```python
import datajoint as dj

dj.config.database.schema_prefix = 'myproject_'
```

Or via environment variable:

```bash
export DJ_SCHEMA_PREFIX=myproject_
```

Or in `datajoint.json`:

```json
{
  "database": {
    "schema_prefix": "myproject_"
  }
}
```

### Apply Prefix to Schemas

Use the prefix when creating schemas:

```python
import datajoint as dj

prefix = dj.config.database.schema_prefix  # 'myproject_'

# Schema names include prefix
subject_schema = dj.Schema(prefix + 'subject')   # myproject_subject
session_schema = dj.Schema(prefix + 'session')   # myproject_session
ephys_schema = dj.Schema(prefix + 'ephys')       # myproject_ephys
```

### Benefits

- **Isolation**: Multiple projects coexist without conflicts
- **Visibility**: Easy to identify which schemas belong to which project
- **Permissions**: Grant access by prefix pattern (`myproject_*`)
- **Cleanup**: Drop all project schemas by prefix

### Database Permissions by Prefix

```sql
-- Grant access to all schemas with prefix
GRANT ALL PRIVILEGES ON `myproject\_%`.* TO 'developer'@'%';

-- Read-only access to another project
GRANT SELECT ON `otherproject\_%`.* TO 'developer'@'%';
```

## Environment-Based Configuration

Use different configurations for development, staging, and production.

### Configuration Hierarchy

DataJoint loads settings in priority order:

1. **Environment variables** (highest priority)
2. **Secrets directory** (`.secrets/`)
3. **Config file** (`datajoint.json`)
4. **Defaults** (lowest priority)

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
export DJ_SCHEMA_PREFIX=myproject_

# Disable interactive prompts
export DJ_SAFEMODE=false
```

### Docker/Kubernetes Example

```yaml
# docker-compose.yaml
services:
  worker:
    image: my-pipeline:latest
    environment:
      - DJ_HOST=db.example.com
      - DJ_USER_FILE=/run/secrets/db_user
      - DJ_PASS_FILE=/run/secrets/db_password
      - DJ_CREATE_TABLES=false
      - DJ_SCHEMA_PREFIX=prod_
    secrets:
      - db_user
      - db_password
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
export DJ_SCHEMA_PREFIX=prod_
export DJ_SAFEMODE=false

# Logging
export DJ_LOG_LEVEL=WARNING
```

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

    # Check schema prefix is set
    if not dj.config.database.schema_prefix:
        errors.append("schema_prefix should be set in production")

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
|---------|-------------|------------|
| `database.create_tables` | `true` | `false` |
| `database.schema_prefix` | `""` or `dev_` | `prod_` |
| `safemode` | `true` | `false` (automated) |
| `loglevel` | `DEBUG` | `WARNING` |

## See Also

- [Manage Pipeline Project](manage-pipeline-project.md) — Project organization
- [Configuration Reference](../reference/configuration.md) — All settings
- [Manage Secrets](manage-secrets.md) — Credential management
