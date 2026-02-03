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

DataJoint requires a MySQL-compatible database server:

### Local Development (Docker)

```bash
docker run -d \
  --name datajoint-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=simple \
  mysql:8.0
```

### DataJoint.com (Recommended)

[DataJoint.com](https://datajoint.com) provides fully managed infrastructure for scientific data pipelines—cloud or on-premises—with comprehensive support, automatic backups, object storage, and team collaboration features.

### Self-Managed Cloud Databases

- **Amazon RDS** — MySQL or Aurora
- **Google Cloud SQL** — MySQL
- **Azure Database** — MySQL

See [Configure Database Connection](configure-database.md) for connection setup.

## Requirements

- Python 3.10+
- MySQL 8.0+ or MariaDB 10.6+
- Network access to database server

## Troubleshooting

### `pymysql` connection errors

```bash
pip install pymysql --force-reinstall
```

### SSL/TLS connection issues

Set `use_tls=False` for local development:

```python
dj.config['database.use_tls'] = False
```

### Permission denied

Ensure your database user has appropriate privileges:

```sql
GRANT ALL PRIVILEGES ON `your_schema%`.* TO 'username'@'%';
```
