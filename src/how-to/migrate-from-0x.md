# Migrate from 0.x

Upgrade existing pipelines from DataJoint 0.x to DataJoint 2.0.

This guide provides a **safe**, **idempotent**, and **reversible** migration path.

## Overview

DataJoint jumped from version 0.14 directly to 2.0 to communicate the significance
of this release. See [What's New in DataJoint 2.0](../explanation/whats-new-2.md)
for a summary of major features.

### Migration Principles

| Principle | Guarantee |
|-----------|-----------|
| **Safe** | Test in isolation before touching production |
| **Idempotent** | Run migration steps multiple times without harm |
| **Reversible** | Rollback to 0.x at any point during migration |

### Compatibility

DataJoint 2.0 can read data written by 0.x. The migration updates:

- Configuration files (not database schema)
- Python code (table definitions, queries)
- Column metadata (blob codec markers)

**No data migration required.** Your existing data remains intact.

---

## Pre-Migration Checklist

Before starting, ensure:

- [ ] Database backup completed
- [ ] Current 0.x version documented (`pip show datajoint`)
- [ ] All pipelines committed to version control
- [ ] Test environment available (separate from production)

```bash
# Document current state
pip show datajoint > migration_baseline.txt
pip freeze > requirements_0x.txt
```

---

## Phase 1: Parallel Installation (Safe)

Install DataJoint 2.0 in a separate environment to test without affecting production.

```bash
# Create isolated environment
python -m venv dj2_migration
source dj2_migration/bin/activate  # Linux/Mac
# or: dj2_migration\Scripts\activate  # Windows

# Install DataJoint 2.0
pip install datajoint>=2.0

# Verify
python -c "import datajoint; print(datajoint.__version__)"
```

**Rollback:** Simply deactivate the virtual environment to return to 0.x.

---

## Phase 2: Configuration Migration

### 2.1 Config File

Create `datajoint.json` alongside your existing `dj_local_conf.json`:

```json
{
  "database": {
    "host": "localhost",
    "user": "datajoint",
    "port": 3306
  },
  "stores": {
    "main": {
      "protocol": "file",
      "location": "/data/store"
    }
  }
}
```

**Idempotent:** Creating this file multiple times has no effect if content is same.

**Reversible:** Delete `datajoint.json` to revert; 0.x ignores this file.

### 2.2 Secrets Directory

Create `.secrets/` for credentials:

```bash
# Create directory (idempotent)
mkdir -p .secrets
chmod 700 .secrets

# Move password (one-time)
echo "your_password" > .secrets/database.password
chmod 600 .secrets/database.password
```

**Reversible:** 0.x still reads from `dj_local_conf.json`; both can coexist.

### 2.3 Environment Variables

| 0.x | 2.0 | Notes |
|-----|-----|-------|
| `DJ_HOST` | `DJ_HOST` | Unchanged |
| `DJ_USER` | `DJ_USER` | Unchanged |
| `DJ_PASS` | `DJ_PASS` | Unchanged |
| — | `DJ_STORES__<name>__*` | New store config |

---

## Phase 3: Code Migration

### 3.1 Analyze Current Definitions

Run the analysis tool to identify changes needed:

```python
import datajoint as dj

# Connect to your database
schema = dj.Schema('your_schema')

# Analyze blob columns
from datajoint.migrate import analyze_schema

report = analyze_schema(schema)
print(report)
```

This produces a report of:
- Blob columns needing codec syntax update
- Query patterns that may need adjustment
- External storage configurations

### 3.2 Update Table Definitions

#### Blob Types

```python
# 0.x syntax (still works, but deprecated)
definition = """
data : longblob
"""

# 2.0 syntax (recommended)
definition = """
data : <blob>
"""
```

**Idempotent:** Definitions are declarative; re-running class definitions is safe.

#### Attach Types

```python
# 0.x
attachment : attach

# 2.0
attachment : <attach>
attachment_ext : <attach@store>
```

#### External Storage

```python
# 0.x
data : blob@store

# 2.0
data : <blob@store>
```

### 3.3 Create Migration Branch

```bash
# Create branch for migration changes
git checkout -b migrate-to-dj2

# Make changes...
git add -A
git commit -m "migrate: Update table definitions for DataJoint 2.0"
```

**Reversible:** `git checkout main` returns to 0.x-compatible code.

---

## Phase 4: Database Metadata Migration

### 4.1 Dry Run

Always test migrations before applying:

```python
from datajoint.migrate import migrate_schema

# Preview changes (no modifications)
changes = migrate_schema(schema, dry_run=True)

for change in changes:
    print(f"{change.table}.{change.column}: {change.description}")
```

### 4.2 Apply Migration

```python
# Apply metadata updates
result = migrate_schema(schema, dry_run=False)

print(f"Migrated {result.tables_updated} tables")
print(f"Updated {result.columns_updated} columns")
```

**Idempotent:** Running migration multiple times detects already-migrated columns
and skips them.

**Reversible:** Metadata changes don't affect data; 0.x can still read the data.

### 4.3 Verify Migration

```python
# Verify all tables accessible
for table_name in schema.list_tables():
    table = schema[table_name]
    count = len(table)
    print(f"{table_name}: {count} rows")

# Test a fetch
sample = (SomeTable & "primary_key = 1").fetch1()
print("Fetch successful:", sample.keys())
```

---

## Phase 5: Query Migration

### 5.1 Universal Set

```python
# 0.x pattern
dj.U() * expression

# 2.0 pattern
dj.U() & expression
```

Search and replace:
```bash
# Find occurrences
grep -rn "dj\.U() \*" --include="*.py"

# Review each case before changing
```

### 5.2 Aggregation

```python
# 0.x
dj.U('group_attr').aggr(Table, n='count(*)')

# 2.0 (same syntax, but verify behavior)
dj.U('group_attr').aggr(Table, n='count(*)')
```

### 5.3 Semantic Matching

DataJoint 2.0 uses lineage-based attribute matching by default. This may change
join behavior if you have:

- Attributes with the same name but different origins
- Renamed foreign key attributes

**Test critical joins:**

```python
# Verify join produces expected results
result_0x = len(A * B)  # Run with 0.x

# After migration
result_2x = len(A * B)  # Run with 2.0

assert result_0x == result_2x, "Join behavior changed!"
```

**Force legacy behavior if needed:**

```python
# Disable semantic checking for specific join
result = A.join(B, semantic_check=False)
```

---

## Phase 6: Production Cutover

### 6.1 Pre-Cutover Checklist

- [ ] All tests pass with DataJoint 2.0
- [ ] Migration branch reviewed and approved
- [ ] Downtime window scheduled (if needed)
- [ ] Rollback procedure documented

### 6.2 Cutover Steps

```bash
# 1. Notify users of maintenance
# 2. Stop running pipelines

# 3. Final backup
mysqldump -u user -p database > backup_pre_dj2.sql

# 4. Update production environment
pip install datajoint>=2.0

# 5. Merge migration branch
git checkout main
git merge migrate-to-dj2

# 6. Run metadata migration
python -c "from datajoint.migrate import migrate_schema; ..."

# 7. Verify
python -c "import your_pipeline; your_pipeline.SomeTable()"

# 8. Resume pipelines
# 9. Notify users
```

### 6.3 Rollback Procedure

If issues are found after cutover:

```bash
# 1. Stop pipelines

# 2. Revert code
git checkout main~1  # or specific commit

# 3. Downgrade package
pip install datajoint==0.14.2

# 4. Restore database (if needed)
mysql -u user -p database < backup_pre_dj2.sql

# 5. Verify
python -c "import your_pipeline; your_pipeline.SomeTable()"

# 6. Resume pipelines
```

---

## Migration Reference

### Type Syntax Changes

| 0.x | 2.0 | Storage |
|-----|-----|---------|
| `longblob` | `<blob>` | In database |
| `blob@store` | `<blob@store>` | External (hash-addressed) |
| `attach` | `<attach>` | In database |
| `attach@store` | `<attach@store>` | External |
| `filepath@store` | `<filepath@store>` | Reference to existing file |
| — | `<object@store>` | Path-addressed (new) |

### Jobs System Changes

```python
# 0.x: Schema-level jobs table
schema.jobs

# 2.0: Per-table jobs
MyComputedTable.jobs           # Job management
MyComputedTable.jobs.pending   # Pending work
MyComputedTable.jobs.errors    # Failed jobs
```

### API Changes

| 0.x | 2.0 | Notes |
|-----|-----|-------|
| `.fetch('KEY')` | `.keys()` | Primary key fetch |
| `.fetch(as_dict=True)` | `.to_dicts()` | Dict format |
| `dj.U() * expr` | `dj.U() & expr` | Universal set |
| `A @ B` | `A.join(B, semantic_check=False)` | Natural join |

---

## Troubleshooting

### "Unknown codec" Error

The column metadata hasn't been migrated:

```python
from datajoint.migrate import migrate_schema
migrate_schema(schema, dry_run=False)
```

### Join Returns Different Results

Semantic matching changed the join. Options:

1. Use explicit `semantic_check=False`
2. Review attribute lineage with `table.heading.attributes`
3. Use projection to rename attributes before join

### External Store Not Found

Update store configuration in `datajoint.json`:

```json
{
  "stores": {
    "old_store_name": {
      "protocol": "file",
      "location": "/path/to/existing/store"
    }
  }
}
```

### Cannot Import After Downgrade

Clear Python cache after version changes:

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md) — Feature overview
- [Configure Object Storage](configure-storage.md) — Storage setup
- [Type System](../explanation/type-system.md) — Codec types
- [Semantic Matching](../reference/specs/semantic-matching.md) — Join behavior
