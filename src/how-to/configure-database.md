# Configure Database Connection

Set up your DataJoint database connection.

> **Tip:** [DataJoint.com](https://datajoint.com) handles database configuration automatically with fully managed infrastructure and support.

> **Example:** See [lcms-demo](https://github.com/datajoint/lcms-demo) for a complete DataJoint project with configuration examples.

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

Store credentials as one plain-text file per setting:

```bash
mkdir -p .secrets
echo "myuser"     > .secrets/database.user
echo "mypassword" > .secrets/database.password
chmod 600 .secrets/*
```

Only `database.user`, `database.password`, and `stores.<name>.<attr>` are read from this
directory — see [Manage Secrets](manage-secrets.md#option-1-secrets-directory-recommended-for-development).

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

An environment variable takes precedence over `datajoint.json` for every setting that has one.
The table below names each setting's variable.

!!! version-changed "Changed in 2.3.7"
    Before 2.3.7, a value in `datajoint.json` replaced the environment variable for some settings,
    among them `database.use_tls` (`DJ_USE_TLS`), `database.reconnect` (`DJ_RECONNECT`) and
    `safemode` (`DJ_SAFEMODE`). A deployment that relied on the file to override one of these
    variables should unset the variable. See
    [Configuration Sources](../reference/configuration.md#configuration-sources).

## Configuration Settings

| Setting | Environment | Default | Description |
| --------- | ------------- | --------- | ------------- |
| `database.host` | `DJ_HOST` | `localhost` | Database server hostname |
| `database.port` | `DJ_PORT` | Auto | Database server port (3306 for MySQL, 5432 for PostgreSQL) |
| `database.user` | `DJ_USER` | — | Database username |
| `database.password` | `DJ_PASS` | — | Database password |
| `database.backend` | `DJ_BACKEND` | `mysql` | Database backend: `mysql` or `postgresql` |
| `database.name` | `DJ_DATABASE_NAME` | `None` | Database name (PostgreSQL only). Defaults to `"postgres"` |
| `database.use_tls` | `DJ_USE_TLS` | `None` | Use TLS encryption: unset (`None`) uses TLS when the server offers it, `true` requires it, `false` turns it off. See [TLS Configuration](#tls-configuration) |
| `database.reconnect` | `DJ_RECONNECT` | `True` | Auto-reconnect on timeout |
| `safemode` | `DJ_SAFEMODE` | `True` | Prompt before destructive operations |

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
3. `datajoint.json`
4. `.secrets/`
5. Default values (lowest priority)

## TLS Configuration

TLS encrypts the connection between DataJoint and the database server, so that others on the
network cannot read the data or the password. The `use_tls` option takes four forms:

| Value | Effect |
| ------- | -------- |
| `None` (default) | Use TLS if the server offers it. Connect without TLS only if the server does not offer TLS or, on PostgreSQL, does not accept TLS connections from this client. The server's certificate is not verified. |
| `True` | Require TLS. If TLS cannot be set up, the connection fails before the user name and password are sent. The server's certificate is not verified. |
| `False` | Do not use TLS. A server that accepts only encrypted connections refuses the connection. |
| dict | Require TLS with the options in the dict. With `"ca"`, the server's certificate is verified. |

!!! version-changed "Changed in 2.3.6"
    `True` and a dict now require TLS, and `False` now turns TLS off. The default no longer
    retries without TLS after a failed TLS setup or a failed login. `dj.Instance` and
    `dj.Connection` now follow `database.use_tls`. See
    [Changes in 2.3.6](../about/whats-new-23.md#changes-in-236).

In `datajoint.json` or `DJ_USE_TLS`, set `true` or `false`, or leave the setting out for the
default. To require TLS:

```json
{
  "database.use_tls": true
}
```

For a local development server without TLS:

```json
{
  "database.use_tls": false
}
```

### Verify the Server's Certificate

`True` encrypts the connection but does not check that the server is the one you meant to
reach. To check that, pass a dict with `"ca"`: the path to the certificate of the authority
that signed the server's certificate (the CA certificate, usually a `.pem` file from your
database administrator or cloud provider). A dict cannot be stored in `datajoint.json`, so pass
it in code:

```python
import datajoint as dj

conn = dj.conn(use_tls={"ca": "/path/to/ca.pem"})
```

With `"ca"`, DataJoint checks both the certificate and that its name matches the host you
connect to. A self-signed certificate often has a name that does not match the host. In that
case, add `"check_hostname": False`. The certificate is still checked against `"ca"`; only the
name check is skipped:

```python
inst = dj.Instance(
    host="db.example.com",
    user="analyst",
    password=password,
    use_tls={"ca": "/path/to/ca.pem", "check_hostname": False},
)
```

For a server that asks for a client certificate, add `"cert"` and `"key"` (the paths to your
certificate and its private key). On PostgreSQL, a dict may hold `"ca"`, `"cert"`, `"key"`,
`"password"` (for an encrypted key) and `"check_hostname"`; other keys are ignored with a
warning.

### Which Calls Use the Setting

`dj.conn()`, `dj.Instance` and `dj.Connection` use `database.use_tls` (or `DJ_USE_TLS`) when
you do not pass `use_tls`. A `use_tls` argument overrides the configuration for that
connection.

`dj.conn()` returns the existing connection when there is one. `dj.conn(use_tls=True)` or
`dj.conn(use_tls={...})` reconnects it with that setting, unless it already meets it: a
connection made with a dict meets `True`, and a dict is met only by a connection made with the
same dict. Inside a transaction, the reconnect raises `DataJointError`. `dj.conn(use_tls=False)`
does not change an existing connection; use `dj.conn(use_tls=False, reset=True)`.

## PostgreSQL Backend

!!! version-added "New in 2.1"
    PostgreSQL is supported as a peer database backend alongside MySQL.

DataJoint supports both MySQL and PostgreSQL backends. To use PostgreSQL:

### Configuration File

```json
{
  "database": {
    "host": "localhost",
    "backend": "postgresql"
  }
}
```

The port defaults to `5432` when `backend` is set to `postgresql`.

### Database Name

!!! version-added "New in 2.2.1"
    The `database.name` setting specifies which PostgreSQL database to connect to.

PostgreSQL requires connecting to a specific database. By default, DataJoint connects to the `postgres` database. To use a different database:

```json
{
  "database": {
    "host": "localhost",
    "backend": "postgresql",
    "name": "my_database"
  }
}
```

Or via environment variable:

```bash
export DJ_DATABASE_NAME=my_database
```

Or programmatically:

```python
dj.config['database.name'] = 'my_database'
```

This setting only applies to PostgreSQL. Setting it with the MySQL backend emits a warning.

### Environment Variable

```bash
export DJ_BACKEND=postgresql
export DJ_HOST=localhost
export DJ_USER=postgres
export DJ_PASS=password
export DJ_DATABASE_NAME=my_database  # optional, defaults to "postgres"
```

### Programmatic Configuration

```python
import datajoint as dj

dj.config['database.backend'] = 'postgresql'
dj.config['database.host'] = 'localhost'
dj.config['database.name'] = 'my_database'  # optional
```

### Docker Compose for Local Development

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_USER=postgres
      - POSTGRES_DB=test
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      timeout: 30s
      retries: 5
```

### Backend Compatibility

DataJoint's core types and query operators work identically on both backends. Table definitions, queries, and computations are portable between MySQL and PostgreSQL without code changes.

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

## Instance-Based Connections

!!! version-added "New in 2.2"
    `dj.Instance` provides isolated connections independent of global config.

For applications that need multiple connections or thread safety, use `dj.Instance` instead of global config:

```python
import datajoint as dj

inst = dj.Instance(host="db.example.com", user="myuser", password="mypassword")
schema = inst.Schema("my_schema")
```

Each Instance has its own config and connection. This is useful for:

- **Web servers**: One Instance per request or tenant
- **Testing**: Isolated databases per test
- **Multi-database**: Connect to production and staging simultaneously
- **Thread safety**: Set `DJ_THREAD_SAFE=true` to enforce Instance usage

```python
# Multiple simultaneous connections
prod = dj.Instance(host="prod.example.com", user="analyst", password="...")
staging = dj.Instance(host="staging.example.com", user="dev", password="...")
```

See [Use Isolated Instances](use-instances.md/) for a complete guide.
