# Migrate from DataJoint 0.14.6 to 2.0

This guide shows how to safely migrate existing DataJoint 0.14.6 pipelines to DataJoint 2.0 using **git branches** and **parallel schemas**.

## Migration Strategy

Use git branches to separate legacy and 2.0 code:

```
main branch (0.14.6):      my_pipeline     → production (pinned to dj 0.14.6)
migration branch (2.0):    my_pipeline_v2  → testing (uses dj 2.0)
                                ↓
                           validate & test
                                ↓
                           merge to main
```

### Key Principles

1. **Standard git workflow** - branch, test, merge
2. **Parallel schemas** - `_v2` schemas for testing
3. **Agentic code migration** - ~1 hour with AI assistance
4. **Deferred external storage** - migrate later if needed
5. **Flexible data approach** - fresh data or copy from production

## Prerequisites

- Git repository for your pipeline
- Python 3.10+ (DataJoint 2.0 requirement)
- MySQL 8.0+ (recommended)
- Database access to create schemas

## Phase 1: Code Migration (~1 hour)

Migrate your Python codebase to DataJoint 2.0 API using AI assistance.

### Step 1: Pin Legacy DataJoint on Main

On your `main` branch, pin the legacy version:

```bash
git checkout main

# Update requirements.txt or pyproject.toml
echo "datajoint==0.14.6" >> requirements.txt

git add requirements.txt
git commit -m "chore: pin datajoint 0.14.6 for legacy support"
git push origin main
```

### Step 2: Create Migration Branch

```bash
# Create new branch for migration
git checkout -b migrate-to-v2

# Install DataJoint 2.0
pip install datajoint==2.0.0  # or latest 2.0.x

# Update requirements
echo "datajoint>=2.0.0" > requirements.txt

git add requirements.txt
git commit -m "chore: upgrade to datajoint 2.0"
```

### Step 3: Agentic Code Migration

Use AI assistance to migrate your code. Provide this prompt to your AI agent:

---

#### 🤖 AI Agent Prompt: DataJoint 2.0 Code Migration

```
You are migrating a DataJoint 0.14.6 pipeline to 2.0.

TASK: Update all Python files in this repository to use DataJoint 2.0 API.

PHASE 1 SCOPE:
- Update schema connections (add _v2 suffix)
- Update API patterns (fetch → to_dicts/to_arrays, etc.)
- Update type syntax in definitions
- Do NOT migrate external storage yet (blob@, attach@, filepath@)

CHANGES REQUIRED:

1. Schema Declarations (add _v2 suffix):
   OLD: schema = dj.schema('my_pipeline')
   NEW: schema = dj.schema('my_pipeline_v2')

2. Fetch API:
   OLD: data = table.fetch()
   OLD: data = table.fetch(as_dict=True)
   OLD: data = table.fetch('attr1', 'attr2')
   OLD: row = table.fetch1()

   NEW: data = table.to_arrays()
   NEW: data = table.to_dicts()
   NEW: data = table.to_arrays('attr1', 'attr2')
   NEW: row = table.fetch1()  # unchanged

3. Update Method:
   OLD: (table & key)._update('attr', value)
   NEW: table.update1({**key, 'attr': value})

4. Join Operator:
   OLD: result = table1 @ table2
   NEW: result = table1.join(table2, semantic_check=False)

5. Universal Set:
   OLD: result = dj.U('attr') * table
   NEW: result = dj.U('attr') & table

6. Type Syntax in Table Definitions:
   OLD: int unsigned → NEW: uint32
   OLD: int → NEW: int32
   OLD: smallint unsigned → NEW: uint16
   OLD: tinyint unsigned → NEW: uint8
   OLD: float → NEW: float32
   OLD: double → NEW: float64
   OLD: longblob → NEW: <blob>

   DEFER (Phase 2):
   - Do NOT change: blob@store, attach@store, filepath@store
   - Leave these for Phase 2 external storage migration

PROCESS:
1. Find all Python files with DataJoint code
2. For each file:
   - Update schema declarations
   - Replace deprecated API patterns
   - Update type syntax
   - Run syntax check
3. Create git commit for each file or module
4. Report summary of changes

VERIFICATION:
- All imports work
- No syntax errors
- Schema connections use _v2 suffix
- All fetch() calls replaced
- All type syntax updated (except external)

REPORT:
- Files modified: [list]
- API patterns replaced: [counts]
- Type syntax updates: [counts]
- Remaining issues: [list]

Time estimate: ~1 hour with agentic assistance.
```

---

### Step 4: Test the Migration

```bash
# Run your tests
pytest tests/

# Or manually test key functionality
python -c "from my_pipeline_v2 import schema; print(schema.list_tables())"

# Commit the changes
git add .
git commit -m "feat: migrate pipeline to datajoint 2.0

- Updated schema connections to *_v2
- Replaced fetch() with to_arrays()/to_dicts()
- Updated type syntax to 2.0 conventions
- External storage migration deferred to Phase 2"

git push origin migrate-to-v2
```

### Step 5: Configuration for 2.0

Update your configuration (optional, for new stores):

```python
# config_v2.py
import datajoint as dj

# Configure unified stores (2.0 format)
dj.config['stores.default'] = 'main'
dj.config['stores.main'] = {
    'protocol': 'file',
    'location': '/data/v2_stores',
}

# Save
dj.config.save('.secrets/datajoint_v2.json')
```

✅ **Phase 1 Complete** - You now have 2.0-compatible code on the `migrate-to-v2` branch.

## Phase 2: Testing & Data Migration

Choose one of two approaches:

### Option A: Fresh Data (Recommended for Initial Testing)

Test the pipeline with fresh data to validate the 2.0 migration:

```python
# On migrate-to-v2 branch
from my_pipeline_v2 import schema, Mouse, Session, Neuron

# Insert test data
Mouse.insert([
    {'mouse_id': 0, 'dob': '2024-01-01', 'sex': 'M'},
])

Session.insert([
    {'mouse_id': 0, 'session_date': '2024-06-01', 'experimenter': 'Test'},
])

# Populate computed tables
Neuron.populate()

# Test new OAS features (if using <npy@> or <object@>)
# Your new code can use modern object storage features
```

**Advantages:**
- No production data at risk
- Test new OAS features immediately
- Fast iteration

**Next:** Once validated, proceed to Option B to migrate production data.

### Option B: Copy Production Data

Copy data from production (`my_pipeline`) to test (`my_pipeline_v2`):

#### Copy Manual Tables

```python
from datajoint.migrate import copy_table_data

# Copy manual tables (no external attributes)
copy_table_data(
    source_schema='my_pipeline',
    dest_schema='my_pipeline_v2',
    table='mouse',
)

copy_table_data(
    source_schema='my_pipeline',
    dest_schema='my_pipeline_v2',
    table='session',
)
```

#### Migrate External Storage Pointers (If Needed)

If you have tables with `blob@`, `attach@`, or `filepath@`:

```python
from datajoint.migrate import migrate_external_pointers_v2

# This migrates metadata WITHOUT moving blob files
# Old BINARY(16) UUID → New JSON metadata pointing to same files
result = migrate_external_pointers_v2(
    schema='my_pipeline_v2',
    table='recording',
    attribute='signal',
    source_store='external-raw',  # 0.14.6 store name
    dest_store='raw',  # 2.0 store name
    copy_files=False,  # Keep files in place
)

print(f"Migrated {result['rows_migrated']} pointers")
```

#### Populate Computed Tables

```python
# Use your 2.0 code to populate
from my_pipeline_v2 import Neuron, ActivityStats

# Populate using 2.0 code
ActivityStats.populate(display_progress=True)
```

#### Validate Results

```python
from datajoint.migrate import compare_query_results

# Compare results between production and test
result = compare_query_results(
    prod_schema='my_pipeline',
    test_schema='my_pipeline_v2',
    table='activity_stats',
    tolerance=1e-6,
)

if result['match']:
    print(f"✓ All {result['row_count']} rows match!")
else:
    print("✗ Discrepancies found:")
    for disc in result['discrepancies']:
        print(f"  {disc}")
```

## Phase 3: Production Cutover

Once testing is complete, choose a cutover strategy:

### Option A: Merge Branch & Rename Schemas

**Recommended for most pipelines.**

```bash
# 1. Backup production database
mysqldump my_pipeline > my_pipeline_backup_$(date +%Y%m%d).sql

# 2. Merge migration branch to main
git checkout main
git merge migrate-to-v2
git push origin main

# 3. Rename schemas in production
mysql -e "
  RENAME TABLE my_pipeline TO my_pipeline_old,
               my_pipeline_v2 TO my_pipeline;
"

# 4. Deploy updated code
# Now all code points to my_pipeline (which has 2.0 structure)

# 5. Keep my_pipeline_old for 1-2 weeks as safety net
# Then drop: DROP DATABASE my_pipeline_old;
```

### Option B: Update Main Branch to Use _v2 Schemas

**Alternative: Keep _v2 suffix permanently.**

```bash
# On main branch, update to use _v2 schemas
git checkout main
git merge migrate-to-v2

# Update schema declarations
sed -i '' 's/my_pipeline_v2/my_pipeline/g' **/*.py

# OR: Keep _v2 suffix and update production to use it
# (just deploy migrate-to-v2 branch as-is)
```

### Option C: In-Place Migration (For Large Databases)

**Use only if renaming is impractical due to size.**

```python
from datajoint.migrate import migrate_schema_in_place

# WARNING: Modifies production schema directly
result = migrate_schema_in_place(
    schema='my_pipeline',
    backup=True,  # Creates backup first
    steps=[
        'update_blob_comments',
        'migrate_external_storage',
        'add_lineage_table',
    ]
)
```

## Phase 4: Adopt New Features

After successful migration, gradually adopt 2.0 features:

### 1. Object Storage for Large Arrays

Replace `<blob>` with `<npy@>` for efficient array storage:

```python
# Before
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <blob>  # In database
    """

# After
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <npy@>  # Lazy-loading from object store
    """

# Usage with lazy loading
signal_ref = (Recording & key).fetch1('signal')
print(f"Shape: {signal_ref.shape}")  # No download!
signal = signal_ref.load()  # Download when ready
```

See [Object Storage Tutorial](../tutorials/basics/06-object-storage.md).

### 2. Semantic Matching

Enable automatic join validation:

```python
# Validates lineage compatibility
result = Neuron.join(Session, semantic_check=True)
```

See [Semantic Matching Spec](../reference/specs/semantic-matching.md).

### 3. Jobs 2.0

Better distributed computing with priority queues:

```python
# Monitor per-table job progress
ActivityStats.jobs.progress()

# Priority-based populate
ActivityStats.populate(order='priority DESC')
```

See [Distributed Computing Tutorial](../tutorials/advanced/distributed.ipynb).

### 4. Custom Codecs

Create domain-specific types:

```python
from datajoint.codecs import Codec

class SpikesCodec(Codec):
    """Custom codec for spike train data."""

    def encode(self, obj, context):
        # Custom serialization
        pass

    def decode(self, blob, context):
        # Custom deserialization
        pass
```

See [Custom Codecs Tutorial](../tutorials/advanced/custom-codecs.ipynb).

## Migration Timeline

### Small Pipeline (< 50 files, < 100 GB)

- **Phase 1**: Code migration - **1 hour** (with AI)
- **Phase 2**: Testing with fresh data - **1 day**
- **Phase 3**: Production cutover - **2 hours**
- **Total: ~2 days**

### Medium Pipeline (50-200 files, 100 GB - 1 TB)

- **Phase 1**: Code migration - **2-3 hours** (with AI)
- **Phase 2**: Data migration & validation - **3-5 days**
- **Phase 3**: Production cutover - **4-8 hours**
- **Total: ~1 week**

### Large Pipeline (200+ files, > 1 TB)

- **Phase 1**: Code migration - **1 day** (with AI)
- **Phase 2**: Sample testing - **1 week**
- **Phase 3**: Production cutover - **1-2 days**
- **Total: ~2 weeks**

## Type Syntax Reference

| 0.14.6 | 2.0 | Notes |
|--------|-----|-------|
| `int unsigned` | `uint32` | 32-bit unsigned |
| `int` | `int32` | 32-bit signed |
| `smallint unsigned` | `uint16` | 16-bit unsigned |
| `tinyint unsigned` | `uint8` | 8-bit unsigned |
| `bigint unsigned` | `uint64` | 64-bit unsigned |
| `float` | `float32` | Single precision |
| `double` | `float64` | Double precision |
| `longblob` | `<blob>` | Binary data |
| `blob@store` | `<blob@store>` | **Phase 2** - deferred |
| `attach@store` | `<attach@store>` | **Phase 2** - deferred |
| `filepath@store` | `<filepath@store>` | **Phase 2** - deferred |

## Configuration Migration

### 0.14.6 Configuration

```json
{
  "database.host": "localhost",
  "database.user": "root",
  "external": {
    "protocol": "file",
    "location": "/data/external"
  }
}
```

### 2.0 Configuration (Unified Stores)

```json
{
  "database.host": "localhost",
  "database.user": "root",
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/stores/main"
    }
  }
}
```

**Key changes:**
- `external.*` → `stores.*`
- Named stores with `default` pointer
- Supports multiple stores

See [Configuration Reference](../reference/configuration.md).

## Troubleshooting

### Issue: Import Errors After Migration

**Cause:** Some imports changed in 2.0.

**Solution:**
```python
# All core functionality is in datajoint namespace
import datajoint as dj

# These work in both versions
from datajoint import schema, Manual, Computed, Imported
```

### Issue: Schema Not Found

**Cause:** Forgot to update schema name to `_v2`.

**Solution:**
```python
# Check your schema declaration
schema = dj.schema('my_pipeline_v2')  # Must have _v2 suffix
```

### Issue: Performance Regression

**Cause:** Missing indexes after schema copy.

**Solution:**
```sql
-- Check indexes
SHOW INDEX FROM my_pipeline_v2.neuron;

-- Recreate if missing
CREATE INDEX idx_mouse_session
  ON my_pipeline_v2.neuron (mouse_id, session_date);
```

### Issue: External Storage Not Accessible

**Cause:** Store configuration not updated.

**Solution:**
```python
# Verify stores configured
print(dj.config['stores'])

# Point to existing external files
dj.config['stores.main.location'] = '/data/external'  # Same as 0.14.6
```

## Rollback Procedures

### Before Cutover (Phase 1-2)

**Easy:** Just switch branches

```bash
# Return to legacy code
git checkout main
pip install -r requirements.txt  # Reinstalls dj 0.14.6
```

### After Cutover (Phase 3)

**Restore from backup:**

```bash
# Drop current production
mysql -e "DROP DATABASE my_pipeline;"

# Restore backup
mysql my_pipeline < my_pipeline_backup_20250114.sql

# Revert code
git checkout main
git reset --hard <pre-merge-commit>
git push --force origin main
```

## Best Practices

1. **Test with AI first** - Let AI agents do the code migration (saves hours)
2. **Start with fresh data** - Validate 2.0 features before production data
3. **Keep legacy branch** - Maintain `main` on 0.14.6 during testing
4. **Incremental merge** - Merge migration branch only after full validation
5. **Backup before cutover** - Always have a tested restore procedure
6. **Monitor after deployment** - Watch for errors in first 24-48 hours

## Summary

**Git Branch Workflow:**
1. Pin 0.14.6 on `main`
2. Create `migrate-to-v2` branch with DataJoint 2.0
3. Use AI to migrate code (~1 hour)
4. Test with fresh or copied data
5. Merge to `main` and cutover production

**Advantages:**
- Standard git workflow
- No production risk during testing
- Easy rollback (switch branches)
- Fast AI-assisted migration
- Flexible data migration options

The key insight: **Use git branches to separate legacy and modern code**, then merge when confident.

## See Also

- [Configuration Reference](../reference/configuration.md)
- [Object Storage Tutorial](../tutorials/basics/06-object-storage.md)
- [Custom Codecs](../tutorials/advanced/custom-codecs.ipynb)
- [API Reference](../reference/api/index.md)
- [Example Migration Script](../../examples/migrate_pipeline_v20.py)
