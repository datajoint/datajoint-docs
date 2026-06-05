# Manage Secrets and Credentials

Secure configuration management for database credentials, storage access keys, and other sensitive settings.

## Overview

DataJoint separates configuration into sensitive and non-sensitive components:

| Component | Location | Purpose | Version Control |
|-----------|----------|---------|-----------------|
| **Non-sensitive** | `datajoint.json` | Project settings, defaults | ✅ Commit to git |
| **Sensitive** | `.secrets/` directory | Credentials, API keys | ❌ Never commit |
| **Dynamic** | Environment variables | CI/CD, production | ⚠️ Context-dependent |

## Configuration Priority

DataJoint loads configuration in this priority order (highest to lowest):

1. **Programmatic settings** — `dj.config['key'] = value`
2. **Environment variables** — `DJ_HOST`, `DJ_USER`, `DJ_STORES`, etc.
3. **Project configuration** — `datajoint.json`
4. **Secrets directory** — `.secrets/stores.<name>.<attr>` (fills attributes the file/env didn't already set)
5. **Default values** — Built-in defaults

Higher priority sources override lower ones. Set `DJ_IGNORE_CONFIG_FILE=true` *(new in 2.2.3)* to skip both `datajoint.json` and the secrets directory entirely — see [Env-var-only deployments](#env-var-only-deployments) below.

## `.secrets/` Directory Structure

Create a `.secrets/` directory in your project root:

```
project/
├── datajoint.json               # Non-sensitive settings (commit)
├── .gitignore                   # Must include .secrets/
├── .secrets/
│   ├── datajoint.json           # Database credentials
│   ├── stores.main.access_key   # S3/cloud storage credentials
│   ├── stores.main.secret_key
│   ├── stores.archive.access_key
│   ├── stores.archive.secret_key
│   └── stores.uc.token          # any stores.<name>.<attr> (new in 2.2.3)
└── ...
```

!!! version-added "New in 2.2.3"
    Any `stores.<name>.<attr>` file is loaded, not only `access_key` / `secret_key`. Plugin-registered storage adapters (e.g. a Databricks Bearer-token adapter) can define their own field names — see [Storage Adapter API](../reference/specs/storage-adapter-api.md).

**Critical:** Add `.secrets/` to `.gitignore`:

```gitignore
# .gitignore
.secrets/
```

## Database Credentials

### Option 1: Secrets Directory (Recommended for Development)

Create `.secrets/datajoint.json`:

```json
{
  "database.user": "myuser",
  "database.password": "mypassword"
}
```

Non-sensitive database settings go in `datajoint.json`:

```json
{
  "database.host": "db.example.com",
  "database.port": 3306,
  "database.use_tls": true,
  "safemode": true
}
```

### Option 2: Environment Variables (Recommended for Production)

For CI/CD and production environments:

```bash
export DJ_HOST=db.example.com
export DJ_USER=myuser
export DJ_PASS=mypassword
export DJ_PORT=3306
export DJ_TLS=true
```

### Option 3: Programmatic Configuration

For scripts and applications:

```python
import datajoint as dj

dj.config['database.host'] = 'localhost'
dj.config['database.user'] = 'myuser'
dj.config['database.password'] = 'mypassword'
```

**Security note:** Only use this when credentials come from secure sources (environment, vault, secrets manager).

## Object Storage Credentials

### File Storage (No Credentials)

Local or network-mounted file systems don't require credentials:

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/my-project"
    }
  }
}
```

### S3/MinIO Storage (With Credentials)

#### Config in `datajoint.json` (non-sensitive):

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-bucket",
      "location": "my-project/data"
    },
    "archive": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "archive-bucket",
      "location": "my-project/archive"
    }
  }
}
```

#### Credentials in `.secrets/` directory:

Create separate files for each store's credentials:

```
.secrets/stores.main.access_key
.secrets/stores.main.secret_key
.secrets/stores.archive.access_key
.secrets/stores.archive.secret_key
```

**File format:** Plain text, one credential per file:

```bash
# .secrets/stores.main.access_key
AKIAIOSFODNN7EXAMPLE

# .secrets/stores.main.secret_key
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### Alternative: Environment Variables

!!! version-added "New in 2.2.3"
    `DJ_STORES` carries a JSON-encoded copy of the entire `stores` dict, in the same shape as `datajoint.json`. Replaces the `stores` block from the file. `.secrets/stores.<name>.<attr>` files still fill in attributes that `DJ_STORES` omits.

For cloud deployments, put the entire `stores` block in a single env var:

```bash
export DJ_STORES='{
  "default": "main",
  "main": {
    "protocol": "s3",
    "endpoint": "s3.amazonaws.com",
    "bucket": "my-bucket",
    "location": "my-project/data",
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}'
```

For plugin-registered adapters, the field names are whatever the adapter declares — `token`, `api_key`, `workspace_url`, etc. See [Storage Adapter API](../reference/specs/storage-adapter-api.md).

If `DJ_STORES` contains invalid JSON, DataJoint raises `ValueError` at config-load time with the JSON parser's error message.

## Environment Variable Reference

### Database Connections

| Setting | Environment Variable | Description |
|---------|---------------------|-------------|
| `database.host` | `DJ_HOST` | Database hostname |
| `database.port` | `DJ_PORT` | Database port (default: 3306) |
| `database.user` | `DJ_USER` | Database username |
| `database.password` | `DJ_PASS` | Database password |
| `database.use_tls` | `DJ_USE_TLS` | Use TLS encryption (true/false) |

### Object Stores

| Variable | Description |
|----------|-------------|
| `DJ_STORES` | JSON-encoded `stores` dict (same shape as `datajoint.json`). Replaces the `stores` block from the file. *(new in 2.2.3)* |

### Config-Source Control

| Variable | Default | Description |
|----------|---------|-------------|
| `DJ_IGNORE_CONFIG_FILE` | `false` | If `true`, skip `datajoint.json`, the project `.secrets/`, and `/run/secrets/datajoint/`. Only env vars and defaults apply. *(new in 2.2.3)* |

## Env-var-only deployments

!!! version-added "New in 2.2.3"
    `DJ_IGNORE_CONFIG_FILE=true` plus `DJ_STORES` gives a deployment a hard guarantee that no file on disk contributes to config — only env vars do. This is how the DataJoint platform configures pipelines.

For Kubernetes, Lambda, the DataJoint platform, or any deployment where the container image must not carry configuration:

```bash
export DJ_IGNORE_CONFIG_FILE=true
export DJ_HOST=db.example.com
export DJ_USER=$(vault read -field=username secret/datajoint)
export DJ_PASS=$(vault read -field=password secret/datajoint)
export DJ_STORES="$(vault read -format=json -field=stores secret/datajoint)"
```

With `DJ_IGNORE_CONFIG_FILE=true`, DataJoint skips:

- the recursive parent-directory search for `datajoint.json`
- the project `.secrets/` directory
- the Docker/Kubernetes `/run/secrets/datajoint/` directory

Only env vars (`DJ_HOST`, `DJ_USER`, `DJ_PASS`, `DJ_STORES`, …) and built-in defaults apply. No file under any parent directory of the working directory can contribute to config.

## Security Best Practices

### Development Environment

```bash
# 1. Initialize secrets directory
mkdir -p .secrets
chmod 700 .secrets  # Owner-only access

# 2. Create .gitignore
echo ".secrets/" >> .gitignore

# 3. Store credentials in .secrets/
cat > .secrets/datajoint.json <<EOF
{
  "database.user": "dev_user",
  "database.password": "dev_password"
}
EOF

# 4. Set restrictive permissions
chmod 600 .secrets/datajoint.json
```

### Production Environment

```bash
# Use environment variables from secure sources
export DJ_USER=$(vault read -field=username secret/datajoint/db)
export DJ_PASS=$(vault read -field=password secret/datajoint/db)

# Stores: one JSON-encoded env var (new in 2.2.3)
export DJ_STORES=$(vault read -format=json -field=stores secret/datajoint)

# Optional: guarantee no file on disk contributes to config (new in 2.2.3)
export DJ_IGNORE_CONFIG_FILE=true
```

### CI/CD Environment

Use your CI system's secrets management:

**GitHub Actions:**
```yaml
env:
  DJ_HOST: ${{ secrets.DJ_HOST }}
  DJ_USER: ${{ secrets.DJ_USER }}
  DJ_PASS: ${{ secrets.DJ_PASS }}
```

**GitLab CI:**
```yaml
variables:
  DJ_HOST: $DJ_HOST
  DJ_USER: $DJ_USER
  DJ_PASS: $DJ_PASS
```

### Docker Containers

**Pass as environment variables:**

```bash
docker run -e DJ_HOST=db.example.com \
           -e DJ_USER=myuser \
           -e DJ_PASS=mypassword \
           my-datajoint-app
```

**Or mount secrets as read-only volume:**

```bash
docker run -v $(pwd)/.secrets:/app/.secrets:ro \
           my-datajoint-app
```

**Docker Compose:**

```yaml
services:
  app:
    image: my-datajoint-app
    env_file: .env
    volumes:
      - ./.secrets:/app/.secrets:ro
```

### Cloud Platforms

**AWS Lambda:**
```python
import os
import datajoint as dj

dj.config['database.user'] = os.environ['DJ_USER']
dj.config['database.password'] = os.environ['DJ_PASS']
```

**Google Cloud Functions:**
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/dj-password/versions/latest"
response = client.access_secret_version(request={"name": name})
dj.config['database.password'] = response.payload.data.decode("UTF-8")
```

**Azure Functions:**
```python
import os
import datajoint as dj

dj.config['database.user'] = os.environ['DJ_USER']
dj.config['database.password'] = os.environ['DJ_PASS']
```

## Common Patterns

### Local Development with Secrets Directory

```python
import datajoint as dj

# Config loaded automatically from:
# 1. datajoint.json (project settings)
# 2. .secrets/datajoint.json (credentials)
conn = dj.conn()
```

### Production with Environment Variables

```python
import os
import datajoint as dj

# All configuration from environment
# No files needed
conn = dj.conn()
```

### Multi-Environment Setup

**Structure:**

```
project/
├── datajoint.json               # Shared settings
├── .secrets/
│   ├── datajoint.dev.json      # Development credentials
│   ├── datajoint.staging.json  # Staging credentials
│   └── datajoint.prod.json     # Production credentials (if needed)
└── ...
```

**Load by environment:**

```python
import os
import datajoint as dj

env = os.getenv('ENV', 'dev')
secrets_path = f'.secrets/datajoint.{env}.json'

# Load environment-specific secrets
import json
with open(secrets_path) as f:
    secrets = json.load(f)
    for key, value in secrets.items():
        dj.config[key] = value

conn = dj.conn()
```

## Troubleshooting

### Secrets Not Loading

**Check configuration priority:**

```python
import datajoint as dj

# View current configuration
print(dj.config)

# Check specific setting
print(dj.config['database.user'])

# See where value came from
print(dj.config._config_sources)  # Not a real attribute, just conceptual
```

### Permission Errors

```bash
# Fix .secrets/ permissions
chmod 700 .secrets
chmod 600 .secrets/*
```

### Environment Variables Not Taking Effect

```python
import os
import datajoint as dj

# Check environment variables are set
print(os.getenv('DJ_USER'))
print(os.getenv('DJ_PASS'))

# Force reload configuration
dj.config.clear()
conn = dj.conn(reset=True)
```

### Accidentally Committed Secrets

**Immediate actions:**

1. **Rotate credentials immediately**
2. Remove from git history:

```bash
# Remove file from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .secrets/datajoint.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team!)
git push origin --force --all
```

3. **Verify removal:**

```bash
git log --all --full-history -- .secrets/datajoint.json
```

## Configuration Templates

### Minimal Development Setup

```json
// datajoint.json
{
  "database.host": "localhost",
  "safemode": true
}
```

```json
// .secrets/datajoint.json
{
  "database.user": "root",
  "database.password": "simple"
}
```

### Production with S3 Storage

```json
// datajoint.json
{
  "database.host": "db.example.com",
  "database.port": 3306,
  "database.use_tls": true,
  "safemode": false,
  "stores": {
    "default": "main",
    "main": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-bucket",
      "location": "my-project"
    }
  }
}
```

```
// .secrets/ directory
.secrets/datajoint.json                 # Database credentials
.secrets/stores.main.access_key         # S3 access key
.secrets/stores.main.secret_key         # S3 secret key
```

## See Also

- [Configure Database Connection](configure-database.md) — Database-specific configuration
- [Configure Object Stores](configure-storage.md) — Storage-specific configuration
- [Configuration Reference](../reference/configuration.md/) — Complete configuration options
