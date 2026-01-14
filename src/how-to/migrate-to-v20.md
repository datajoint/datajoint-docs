# Migrate from DataJoint 0.14.6 to 2.0

This guide shows how to safely migrate existing DataJoint 0.14.6 pipelines to DataJoint 2.0 using **parallel schemas**. Production remains completely untouched until the final cutover.

## Migration Strategy

```
Production (0.14.6):     my_pipeline        → runs unchanged
Testing (2.0):           my_pipeline_v20    → test migration here
                              ↓
                         validate everything
                              ↓
Final Cutover:          rename/migrate schemas (one-time event)
```

### Key Principle: Zero Production Risk

Your production schemas are never modified until you've thoroughly tested the migration in parallel `_v20` schemas. This approach:

- **Eliminates risk** - production continues unchanged during testing
- **Enables practice** - run migration multiple times until perfect
- **Simplifies rollback** - just drop `_v20` schemas, no data loss
- **Allows validation** - compare old vs new side-by-side

## Prerequisites

- DataJoint 0.14.6 currently running in production
- Disk space for schema copies (recommended: 2x current database size)
- Database backup capabilities
- Access to create new schemas on production database

## Phase 1: Setup Parallel Schemas

Create `_v20` copies of your schemas for testing without touching production.

### Install DataJoint 2.0

```bash
# Create separate environment (keep 0.14.6 for production)
conda create -n dj20 python=3.12
conda activate dj20
pip install datajoint==2.0.0  # or latest 2.0 version
```

### Configure 2.0 Client

Create configuration for testing:

```python
import datajoint as dj

# Point to same database, different schemas
dj.config['database.host'] = 'production-host'
dj.config['database.user'] = 'migration-user'

# Configure unified stores (2.0 format)
dj.config['stores.default'] = 'test_store'
dj.config['stores.test_store'] = {
    'protocol': 'file',
    'location': '/data/migration_test',
}

# Save configuration
dj.config.save('.secrets/datajoint_v20.json')
```

### Create Parallel Schema

For each production schema, create a `_v20` copy:

```python
from datajoint.migrate import create_parallel_schema

# Production schema: my_pipeline (0.14.6)
# Test schema:       my_pipeline_v20 (2.0)

result = create_parallel_schema(
    source='my_pipeline',
    dest='my_pipeline_v20',
    copy_data=False  # Just structure, no data yet
)

print(f"Created {result['tables_created']} tables")
```

### Verify

```python
# Check production is untouched
import datajoint as dj

conn = dj.conn()

# Count production tables
prod_tables = conn.query(
    "SELECT COUNT(*) FROM information_schema.TABLES "
    "WHERE TABLE_SCHEMA='my_pipeline'"
).fetchone()[0]

# Count test tables
test_tables = conn.query(
    "SELECT COUNT(*) FROM information_schema.TABLES "
    "WHERE TABLE_SCHEMA='my_pipeline_v20'"
).fetchone()[0]

print(f"Production: {prod_tables} tables")
print(f"Test copy: {test_tables} tables")
assert prod_tables == test_tables, "Schema copy incomplete"
```

✅ **Production remains completely untouched**

## Phase 2: Update Code for 2.0

Modify Python code to use 2.0 API patterns and point to `_v20` schemas.

### Schema Connection

Update schema declarations:

```python
# OLD (0.14.6 production code)
schema = dj.schema('my_pipeline')

# NEW (2.0 test code)
schema = dj.schema('my_pipeline_v20')  # Point to test schema
```

### API Updates

#### Fetch API

```python
# 0.14.6
data = table.fetch()
data = table.fetch(as_dict=True)
data = table.fetch('attr1', 'attr2')

# 2.0
data = table.to_arrays()
data = table.to_dicts()
data = table.to_arrays('attr1', 'attr2')
```

#### Update Method

```python
# 0.14.6
(table & key)._update('attr', value)

# 2.0
table.update1({**key, 'attr': value})
```

#### Join Operator

```python
# 0.14.6
result = table1 @ table2

# 2.0
result = table1.join(table2, semantic_check=False)
```

### Table Definitions

Update type syntax:

```python
# 0.14.6
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int unsigned
    ---
    signal : external-raw
    sampling_rate : float
    """

# 2.0
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <blob@raw>
    sampling_rate : float32
    """
```

### Type Syntax Reference

| 0.14.6 | 2.0 |
|--------|-----|
| `int unsigned` | `uint32` |
| `int` | `int32` |
| `smallint unsigned` | `uint16` |
| `tinyint unsigned` | `uint8` |
| `float` | `float32` |
| `double` | `float64` |
| `longblob` | `<blob>` |
| `external-store` | `<blob@store>` |
| `attach@store` | `<attach@store>` |
| `filepath@store` | `<filepath@store>` |

### Configuration

```python
# 0.14.6 (production)
{
  "external": {
    "protocol": "file",
    "location": "/data/external"
  }
}

# 2.0 (test)
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/migration_test"
    }
  }
}
```

See [Configuration Guide](../reference/configuration.md) for details.

✅ **Production code still uses 0.14.6 - continues working**

## Phase 3: Migrate Test Data

Copy data from production to `_v20` schemas for testing.

### Choose Migration Scope

**Option A: Full Copy** (recommended for small/medium pipelines)
- Copy all data
- Best validation coverage

**Option B: Sample Copy** (for large pipelines)
- Copy representative subset
- Faster testing

**Option C: Minimal Copy** (for very large pipelines)
- Copy just enough to test all code paths
- Requires careful selection

### Copy Manual Tables

```python
from datajoint.migrate import copy_table_data

# Copy all data
result = copy_table_data(
    source_schema='my_pipeline',
    dest_schema='my_pipeline_v20',
    table='Mouse',
    limit=None  # Copy all
)

print(f"Copied {result['rows_copied']} rows")

# Or copy sample
result = copy_table_data(
    source_schema='my_pipeline',
    dest_schema='my_pipeline_v20',
    table='Session',
    limit=100,
    where_clause="session_date >= '2024-01-01'"
)
```

### Migrate External Storage

For tables with external attributes:

```python
from datajoint.migrate import migrate_external_to_v20

# Convert BINARY(16) UUID → JSON metadata
result = migrate_external_to_v20(
    schema='my_pipeline_v20',
    table='Recording',
    attribute='signal',
    source_store='external-raw',  # 0.14.6 store
    dest_store='raw',  # 2.0 store
    copy_files=True
)

print(f"Migrated {result['rows_migrated']} external attributes")
print(f"Copied {result['files_copied']} files")
```

### Populate Computed Tables

```python
# Load _v20 schema with 2.0 code
from my_pipeline_v20 import ActivityStats

# Populate using 2.0 code
ActivityStats.populate(display_progress=True)

# Verify counts
print(f"Rows: {len(ActivityStats())}")
```

✅ **Production data remains read-only**

## Phase 4: Validate Side-by-Side

Compare production and test to verify correctness.

### Query Comparison

```python
# Production query (0.14.6)
prod_result = dj.schema('my_pipeline').connection.query(
    "SELECT * FROM my_pipeline.neuron WHERE mouse_id=0"
).fetchall()

# Test query (2.0)
from my_pipeline_v20 import Neuron
test_result = (Neuron & 'mouse_id=0').to_dicts()

# Compare
assert len(prod_result) == len(test_result)
print(f"✓ Query results match ({len(prod_result)} rows)")
```

### Computation Validation

```python
# Compare computed values
from datajoint.migrate import compare_query_results

result = compare_query_results(
    prod_schema='my_pipeline',
    test_schema='my_pipeline_v20',
    table='activity_stats',
    tolerance=1e-6
)

if result['match']:
    print(f"✓ All {result['row_count']} rows match")
else:
    print(f"✗ Found {len(result['discrepancies'])} discrepancies")
    for disc in result['discrepancies']:
        print(f"  {disc}")
```

### External Storage

```python
from my_pipeline_v20 import Recording

# Verify external data accessible
signal = (Recording & {'recording_id': 1}).fetch1('signal')
assert signal.shape == (1000,), f"Wrong shape: {signal.shape}"
print("✓ External data accessible")
```

### Validation Checklist

- [ ] All queries return same results
- [ ] Computed values match (within tolerance)
- [ ] External data accessible and correct
- [ ] Performance acceptable (< 2x slowdown)
- [ ] No errors in logs
- [ ] Team trained on 2.0 API

✅ **When all checks pass, you're ready for cutover**

## Phase 5: Production Cutover

**CRITICAL: This is the only phase that modifies production.**

### Pre-Cutover Checklist

**Do not proceed until ALL items checked:**

- [ ] Phase 4 validation 100% successful
- [ ] Full database backup completed **and tested**
- [ ] Rollback procedure documented and rehearsed
- [ ] All 0.14.6 clients stopped (verify no processes running)
- [ ] Maintenance window scheduled
- [ ] Team notified and standing by

### Backup Production

```python
from datajoint.migrate import backup_schema

# Create timestamped backup
result = backup_schema(
    schema='my_pipeline',
    backup_name='my_pipeline_backup_20250114'
)

print(f"Backed up {result['tables_backed_up']} tables")
print(f"Location: {result['backup_location']}")

# Test restore procedure (on different schema)
restore_schema(
    backup='my_pipeline_backup_20250114',
    dest='my_pipeline_restore_test'
)
# If successful, drop test: DROP DATABASE my_pipeline_restore_test
```

### Cutover Option A: Rename Schemas (Fastest)

```python
import datajoint as dj

conn = dj.conn()

# Rename production → backup
conn.query("RENAME TABLE `my_pipeline` TO `my_pipeline_old`;")

# Rename test → production
conn.query("RENAME TABLE `my_pipeline_v20` TO `my_pipeline`;")

print("✓ Schema renamed")
```

**Pros:** Fast, all data already migrated
**Cons:** Must continue (schemas altered)

### Cutover Option B: Drop and Recreate (Safer)

```python
# 1. Drop production schema
schema = dj.schema('my_pipeline')
schema.drop(prompt=False)

# 2. Recreate with 2.0 code
from my_pipeline_v20 import *  # Import all table classes

# 3. Copy data from _v20
from datajoint.migrate import copy_all_data
copy_all_data(source='my_pipeline_v20', dest='my_pipeline')
```

**Pros:** Can restore from backup easily
**Cons:** Slower, more steps

### Update Production Code

Point production code to migrated schema:

```python
# my_pipeline.py (production code)
import datajoint as dj

# Now uses production schema (with 2.0 structure)
schema = dj.schema('my_pipeline')

# Use 2.0 API patterns
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <blob@raw>
    sampling_rate : float32
    """
```

### Verify Cutover

```python
from datajoint.migrate import verify_schema_v20

result = verify_schema_v20('my_pipeline')

if result['compatible']:
    print("✓ Schema fully migrated to 2.0")
else:
    print("✗ Issues found:")
    for issue in result['issues']:
        print(f"  {issue}")
```

### Rollback (If Needed)

If something goes wrong:

```python
# Restore from backup
from datajoint.migrate import restore_schema

restore_schema(
    backup='my_pipeline_backup_20250114',
    dest='my_pipeline'
)

# Restart 0.14.6 clients
```

✅ **Production now running on DataJoint 2.0**

## Phase 6: Adopt New Features

Now that you're on 2.0, gradually adopt new features:

### Feature Priorities

| Feature | Complexity | Benefit |
|---------|------------|---------|
| Unified stores config | Low | Cleaner setup |
| Core types (`uint32`) | Low | Type safety |
| `dj.Top` operator | Low | Simpler queries |
| Semantic matching | Medium | Safer joins |
| Jobs 2.0 | Medium | Better scaling |
| Object storage (`<npy@>`) | High | Large data |
| Custom codecs | High | Domain types |

### Example: Object Storage

```python
# Before: Blob in database
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <blob>  # In database
    """

# After: Lazy-loading from object store
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <npy@>  # In object store
    """

# Usage
signal_ref = (Recording & key).fetch1('signal')
print(f"Shape: {signal_ref.shape}")  # No download
signal = signal_ref.load()  # Download when needed
```

See tutorials:
- [Object Storage Tutorial](../tutorials/basics/06-object-storage.md)
- [Custom Codecs](../tutorials/advanced/custom-codecs.md)
- [Distributed Computing](../tutorials/advanced/distributed.md)

## Migration Timeline

### Small Pipeline (< 100 GB)

- Phase 1: Setup - **1 day**
- Phase 2: Code - **1 week**
- Phase 3: Data - **1 day**
- Phase 4: Validate - **1 week**
- Phase 5: Cutover - **4 hours**
- **Total: ~3 weeks**

### Large Pipeline (> 1 TB)

- Phase 1: Setup - **1 week**
- Phase 2: Code - **2 weeks**
- Phase 3: Data - **3 days** (sample)
- Phase 4: Validate - **2 weeks**
- Phase 5: Cutover - **1-2 days**
- **Total: ~6 weeks**

## Troubleshooting

### Issue: Disk Space Insufficient

**Solution:** Use sample copy (Phase 3 Option B):

```python
# Copy only recent data
copy_table_data(
    source_schema='my_pipeline',
    dest_schema='my_pipeline_v20',
    table='Session',
    where_clause="session_date >= '2024-01-01'",
    limit=1000
)
```

### Issue: External Storage Migration Slow

**Solution:** Skip file copying initially, validate metadata only:

```python
migrate_external_to_v20(
    schema='my_pipeline_v20',
    table='Recording',
    attribute='signal',
    source_store='external-raw',
    dest_store='raw',
    copy_files=False  # Skip file copy
)

# Copy files in parallel later
```

### Issue: Query Results Don't Match

**Solution:** Check for floating-point precision issues:

```python
compare_query_results(
    prod_schema='my_pipeline',
    test_schema='my_pipeline_v20',
    table='activity_stats',
    tolerance=1e-5  # Increase tolerance
)
```

### Issue: Performance Degradation

**Solution:** Check for missing indexes:

```sql
-- Compare indexes between schemas
SELECT TABLE_NAME, INDEX_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA='my_pipeline';

SELECT TABLE_NAME, INDEX_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA='my_pipeline_v20';
```

## Summary

The parallel schema approach provides:

1. ✅ **Zero risk** to production during testing
2. ✅ **Unlimited practice** runs
3. ✅ **Easy rollback** at every phase
4. ✅ **Side-by-side validation**
5. ✅ **Independent module migration**

The key insight: **testing migrations is cheap, production failures are expensive**. Take your time with Phases 1-4, then execute Phase 5 confidently.

## See Also

- [Configuration Reference](../reference/configuration.md)
- [Object Storage Tutorial](../tutorials/basics/06-object-storage.md)
- [API Reference](../reference/api/index.md)
