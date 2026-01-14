# Installation

Install DataJoint Python and set up your environment.

!!! warning "Pre-Release Documentation"

    This documentation covers **DataJoint 2.0**, which is currently in pre-release.

    - **For production use:** Install the stable version (0.14.x) and use [legacy docs](https://datajoint.github.io/datajoint-python)
    - **For testing 2.0:** Follow the pre-release installation instructions below
    - **For migration:** See the [Migration Guide](migrate-to-v20.md)

## Choose Your Installation

### Pre-Release (2.0) — For Testing and Development

**Note:** DataJoint 2.0 is not yet on PyPI/conda. Install from the pre-release branch:

```bash
git clone -b pre/v2.0 https://github.com/datajoint/datajoint-python.git
cd datajoint-python
pip install -e ".[dev]"
```

**With optional dependencies:**

```bash
# For polars DataFrame support
pip install -e ".[polars]"

# For all optional dependencies
pip install -e ".[all]"
```

### Stable (0.14.x) — For Production Use

```bash
pip install datajoint
```

**Note:** This installs DataJoint 0.14.x. The tutorials and guides in this documentation are written for 2.0 and will not match the stable API. Use [legacy documentation](https://datajoint.github.io/datajoint-python) instead.

## Verify Installation

Check your installed version:

```python
import datajoint as dj
print(dj.__version__)
```

**Expected output for this documentation:**
- `2.0.0` or higher — You're ready to follow this documentation
- `0.14.x` or lower — You have the stable version, use [legacy docs](https://datajoint.github.io/datajoint-python) instead

### If You Have the Wrong Version

| Your Situation | Action |
|----------------|--------|
| Installed 0.14.x but want to test 2.0 | Follow pre-release installation above |
| Installed 2.0 but need production stability | `pip uninstall datajoint && pip install datajoint` |
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
