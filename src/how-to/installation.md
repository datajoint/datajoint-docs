# Installation

Install DataJoint Python and set up your environment.

## Install DataJoint 2.0

```bash
pip install datajoint
```

**With optional dependencies:**

```bash
# For diagram visualization (matplotlib, ipython)
pip install datajoint[viz]

# For polars DataFrame support
pip install datajoint[polars]

# For the PostgreSQL backend (psycopg2-binary) — added in 2.1
pip install datajoint[postgres]

# For cloud storage backends
pip install datajoint[s3]    # AWS S3
pip install datajoint[gcs]   # Google Cloud Storage
pip install datajoint[azure] # Azure Blob Storage
```

!!! note "Upgrading from 0.14.x?"

    See the [Migration Guide](migrate-to-v20.md) for breaking changes and upgrade instructions.
    Legacy documentation for 0.14.x is available at [datajoint.github.io](https://datajoint.github.io/datajoint-python).

## Verify Installation

Check your installed version:

```python
import datajoint as dj
print(dj.__version__)
```

**Expected output for this documentation:**

- `2.0.0` or higher — You're ready to follow this documentation
- `0.14.x` or lower — You have the stable version, use [legacy docs](https://datajoint.github.io/datajoint-python) instead

### If You Have an Older Version

| Your Situation | Action |
|----------------|--------|
| Installed 0.14.x, want to upgrade | `pip install --upgrade datajoint` |
| Have existing 0.14.x pipeline to upgrade | Follow [Migration Guide](migrate-to-v20.md) |

## Database Server

DataJoint connects to either MySQL or PostgreSQL. MySQL has been supported since the original release; PostgreSQL support was added in **2.1**, and the `database.name` setting for selecting a non-default PostgreSQL database was added in **2.2.1**. See [Configure Database Connection](configure-database.md#postgresql-backend) for the full configuration reference.

### Local Development (Docker)

```bash
# MySQL
docker run -d \
  --name datajoint-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=simple \
  mysql:8.0
```

```bash
# PostgreSQL (added in 2.1)
docker run -d \
  --name datajoint-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=simple \
  postgres:15
```

### DataJoint.com (Recommended)

[DataJoint.com](https://datajoint.com) provides fully managed infrastructure for scientific data pipelines—cloud or on-premises—with comprehensive support, automatic backups, object storage, and team collaboration features.

### Self-Managed Cloud Databases

- **Amazon RDS** — MySQL, Aurora MySQL, PostgreSQL, or Aurora PostgreSQL
- **Google Cloud SQL** — MySQL or PostgreSQL
- **Azure Database** — MySQL or PostgreSQL

See [Configure Database Connection](configure-database.md) for connection setup.

## Requirements

- Python 3.10+
- MySQL 8.0.13+ or PostgreSQL 15+
- Network access to database server

## Troubleshooting

### `pymysql` connection errors

```bash
pip install pymysql --force-reinstall
```

### `psycopg2` connection errors

```bash
pip install datajoint[postgres] --force-reinstall
```

The PostgreSQL backend (added in 2.1) requires the `postgres` extra, which installs `psycopg2-binary`.

### SSL/TLS connection issues

Set `use_tls=False` for local development:

```python
dj.config['database.use_tls'] = False
```

### Permission denied

Ensure your database user has appropriate privileges:

```sql
-- MySQL
GRANT ALL PRIVILEGES ON `your_schema%`.* TO 'username'@'%';
```

```sql
-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE my_db TO username;
```
