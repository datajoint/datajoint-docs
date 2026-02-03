# Error Reference

DataJoint exception classes and their meanings.

## Exception Hierarchy

```
Exception
└── DataJointError
    ├── LostConnectionError
    ├── QueryError
    │   ├── QuerySyntaxError
    │   ├── AccessError
    │   ├── DuplicateError
    │   ├── IntegrityError
    │   ├── UnknownAttributeError
    │   └── MissingAttributeError
    ├── MissingTableError
    ├── MissingExternalFile
    └── BucketInaccessible
```

## Base Exception

### DataJointError

Base class for all DataJoint-specific errors.

```python
try:
    # DataJoint operation
except dj.DataJointError as e:
    print(f"DataJoint error: {e}")
```

## Connection Errors

### LostConnectionError

Database connection was lost during operation.

**Common causes:**
- Network interruption
- Server timeout
- Server restart

**Resolution:**
- Check network connectivity
- Reconnect with `dj.conn().connect()`

## Query Errors

### QuerySyntaxError

Invalid query syntax.

**Common causes:**
- Malformed restriction string
- Invalid attribute reference
- SQL syntax error in projection

### AccessError

Insufficient database privileges.

**Common causes:**
- User lacks SELECT/INSERT/DELETE privileges
- Schema access not granted

**Resolution:**
- Contact database administrator
- Check user grants

### DuplicateError

Attempt to insert duplicate primary key.

```python
try:
    table.insert1({'id': 1, 'name': 'Alice'})
    table.insert1({'id': 1, 'name': 'Bob'})  # Raises DuplicateError
except dj.errors.DuplicateError:
    print("Entry already exists")
```

**Resolution:**
- Use `insert(..., skip_duplicates=True)`
- Use `insert(..., replace=True)` to update
- Check if entry exists before inserting

### IntegrityError

Foreign key constraint violation.

**Common causes:**
- Inserting row with non-existent parent
- Parent row deletion blocked by children

**Resolution:**
- Insert parent rows first
- Use cascade delete for parent

### UnknownAttributeError

Referenced attribute doesn't exist.

```python
# Raises UnknownAttributeError
table.to_arrays('nonexistent_column')
```

**Resolution:**
- Check `table.heading` for available attributes
- Verify spelling

### MissingAttributeError

Required attribute not provided in insert.

```python
# Raises MissingAttributeError if 'name' is required
table.insert1({'id': 1})  # Missing 'name'
```

**Resolution:**
- Provide all required attributes
- Set default values in definition

## Table Errors

### MissingTableError

Table not declared in database.

**Common causes:**
- Schema not created
- Table class not instantiated
- Database dropped

**Resolution:**
- Check schema exists: `schema.is_activated()`
- Verify table declaration

## Storage Errors

### MissingExternalFile

External file managed by DataJoint is missing.

**Common causes:**
- File manually deleted from store
- Store misconfigured
- Network/permission issues

**Resolution:**
- Check store configuration
- Verify file exists at expected path
- Run garbage collection audit

### BucketInaccessible

S3 bucket cannot be accessed.

**Common causes:**
- Invalid credentials
- Bucket doesn't exist
- Network/firewall issues

**Resolution:**
- Verify AWS credentials
- Check bucket name and region
- Test with AWS CLI

## Handling Errors

### Catching Specific Errors

```python
import datajoint as dj

try:
    table.insert1(data)
except dj.errors.DuplicateError:
    print("Entry exists, skipping")
except dj.errors.IntegrityError:
    print("Parent entry missing")
except dj.DataJointError as e:
    print(f"Other DataJoint error: {e}")
```

### Error Information

```python
try:
    table.insert1(data)
except dj.DataJointError as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Message: {e}")
    print(f"Args: {e.args}")
```

## See Also

- [API: errors module](../api/datajoint/errors.md/)
