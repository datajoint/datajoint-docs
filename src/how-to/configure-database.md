# Configure Database Connection

Set up your DataJoint database connection.

> **Tip:** [DataJoint.com](https://datajoint.com) handles database configuration automatically with fully managed infrastructure and support.

## Configuration Structure

DataJoint separates configuration into two parts:

1. **`datajoint.json`** — Non-sensitive settings (checked into version control)
2. **`.secrets/` directory** — Credentials and secrets (never committed)

## Project Configuration (`datajoint.json`)

Create `datajoint.json` in your project root for non-sensitive settings:

```json
{
  "database.host": "db.example.com",
  "database.port": 3306,
  "database.use_tls": true,
  "safemode": true
}
```

This file should be committed to version control.

## Secrets Directory (`.secrets/`)

Store credentials in `.secrets/datajoint.json`:

```json
{
  "database.user": "myuser",
  "database.password": "mypassword"
}
```

**Important:** Add `.secrets/` to your `.gitignore`:

```gitignore
.secrets/
```

## Environment Variables

For CI/CD and production, use environment variables:

```bash
export DJ_HOST=db.example.com
export DJ_USER=myuser
export DJ_PASS=mypassword
```

Environment variables take precedence over config files.

## Configuration Settings

| Setting | Environment | Default | Description |
|---------|-------------|---------|-------------|
| `database.host` | `DJ_HOST` | `localhost` | Database server hostname |
| `database.port` | `DJ_PORT` | `3306` | Database server port |
| `database.user` | `DJ_USER` | — | Database username |
| `database.password` | `DJ_PASS` | — | Database password |
| `database.use_tls` | `DJ_TLS` | `True` | Use TLS encryption |
| `database.reconnect` | — | `True` | Auto-reconnect on timeout |
| `safemode` | — | `True` | Prompt before destructive operations |

## Test Connection

```python
import datajoint as dj

# Connects using configured credentials
conn = dj.conn()
print(f"Connected to {conn.host}")
```

## Programmatic Configuration

For scripts, you can set configuration programmatically:

```python
import datajoint as dj

dj.config['database.host'] = 'localhost'
# Credentials from environment or secrets file
```

## Temporary Override

```python
with dj.config.override(database={'host': 'test-server'}):
    # Uses test-server for this block only
    conn = dj.conn()
```

## Configuration Precedence

1. Programmatic settings (highest priority)
2. Environment variables
3. `.secrets/datajoint.json`
4. `datajoint.json`
5. Default values (lowest priority)

## TLS Configuration

For production, always use TLS:

```json
{
  "database.use_tls": true
}
```

For local development without TLS:

```json
{
  "database.use_tls": false
}
```

## Connection Lifecycle

### Persistent Connection (Default)

DataJoint uses a persistent singleton connection by default:

```python
import datajoint as dj

# First call establishes connection
conn = dj.conn()

# Subsequent calls return the same connection
conn2 = dj.conn()  # Same as conn

# Reset to create a new connection
conn3 = dj.conn(reset=True)  # New connection
```

This is ideal for interactive sessions and notebooks.

### Context Manager (Explicit Cleanup)

For serverless environments (AWS Lambda, Cloud Functions) or when you need explicit connection lifecycle control, use the context manager:

```python
import datajoint as dj

with dj.Connection(host, user, password) as conn:
    schema = dj.Schema('my_schema', connection=conn)
    MyTable().insert(data)
# Connection automatically closed when exiting the block
```

The connection closes automatically even if an exception occurs:

```python
try:
    with dj.Connection(**creds) as conn:
        schema = dj.Schema('my_schema', connection=conn)
        MyTable().insert(data)
        raise SomeError()
except SomeError:
    pass
# Connection is still closed properly
```

### Manual Close

You can also close a connection explicitly:

```python
conn = dj.conn()
# ... do work ...
conn.close()
```

