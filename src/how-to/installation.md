# Installation

Install DataJoint Python and set up your environment.

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

```bash
git clone https://github.com/datajoint/datajoint-python.git
cd datajoint-python
pip install -e ".[dev]"
```

## Verify Installation

```python
import datajoint as dj
print(dj.__version__)
```

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
