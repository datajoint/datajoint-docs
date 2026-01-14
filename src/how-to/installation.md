# Installation

Install DataJoint Python and set up your environment.

!!! warning "DataJoint 2.0+ Required"

    This documentation is for **DataJoint 2.0 and later**. The PyPI and conda releases for DataJoint 2.0 are currently in preparation.

    **If you install now, you may get an older version (0.14.x).** After installation, verify you have version 2.0 or later before following the tutorials and guides.

## Basic Installation

```bash
pip install datajoint
```

## With Optional Dependencies

```bash
# For polars DataFrame support
pip install datajoint[polars]

# For PyArrow support
pip install datajoint[arrow]

# For all optional dependencies
pip install datajoint[all]
```

## Development Installation

To install the latest pre-release version:

```bash
git clone -b pre/v2.0 https://github.com/datajoint/datajoint-python.git
cd datajoint-python
pip install -e ".[dev]"
```

## Verify Installation

**Important:** Check that you have DataJoint 2.0 or later:

```python
import datajoint as dj
print(dj.__version__)
```

**Expected output:** `2.0.0` or higher

!!! danger "Version Mismatch"

    If you see version `0.14.x` or lower, you have the legacy version of DataJoint. This documentation will not match your installed version.

    **Options:**

    1. **Upgrade to 2.0 (pre-release):** Install from the `pre/v2.0` branch (see Development Installation above)
    2. **Use legacy documentation:** Visit [datajoint.github.io/datajoint-python](https://datajoint.github.io/datajoint-python)
    3. **Migrate existing pipeline:** Follow the [Migration Guide](migrate-to-v20.md)

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
