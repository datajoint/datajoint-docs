# Migrate to DataJoint 2.0

Upgrade existing pipelines from legacy DataJoint (pre-2.0) to DataJoint 2.0.

> **This guide is optimized for AI coding assistants.** Point your AI agent at this
> document and it will execute the migration with your oversight.

## Requirements

### System Requirements

| Component | Legacy (0.14.x) | DataJoint 2.0 |
|-----------|-----------------|---------------|
| **Python** | 3.8+ | **3.10+** |
| **MySQL** | 5.7+ | **8.0+** |

**Action required:** Upgrade your Python environment and MySQL server before installing DataJoint 2.0.

### License Change

DataJoint 2.0 is licensed under **Apache 2.0** (previously LGPL-2.1).

- More permissive for commercial and academic use
- Compatible with broader ecosystem of tools
- Clearer patent grant provisions

No action required—the new license is more permissive.

### Future Backend Support

DataJoint 2.0 introduces portable type aliases (`uint32`, `float64`, etc.) that prepare the codebase for **PostgreSQL backend compatibility** in a future release. Migration to core types (Phase 2) ensures your schemas will work seamlessly when Postgres support is available.

---

## Overview

| Phase | Code Changes | Schema Changes | Legacy Works? |
|-------|--------------|----------------|---------------|
| 1 | Settings, fetch API, queries | None | Yes |
| 2 | Table definitions | Column comments, `~lineage` | Yes |
| 3 | — | Add `_v2` columns for external storage | Yes |
| 4 | — | Remove legacy external columns | **No** |
| 5 | Adopt new features | Optional | No |
| 6 | — | Drop `~log`, `~jobs`, `~external_*` | No |

**After Phase 1:** Simple queries work. Blobs and complex queries may not work until Phase 2.

**After Phase 2:** 2.0 clients can use all column types except legacy external storage and AdaptedTypes.

**Most users stop after Phase 2.** Phases 3-4 only apply to schemas using legacy external storage (`external-*`, `attach@*`, `filepath@*`) or AdaptedTypes. Phase 6 is optional cleanup.

---

## What's New in 2.0

### 3-Tier Column Type System

DataJoint 2.0 introduces a unified type system with three tiers:

| Tier | Description | Examples | Migration |
|------|-------------|----------|-----------|
| **Native** | Raw MySQL types | `int unsigned`, `tinyint` | Auto-converted to core types |
| **Core** | Standardized portable types | `uint32`, `float64`, `varchar(100)`, `json` | Column comment only |
| **Codec** | Serialization to blob or external store | `<blob>`, `<blob@store>`, `<attach@store>` | Varies (see below) |

**Migration:** Phase 2 converts most native types to corresponding core types automatically (e.g., `int unsigned` → `uint32`). Warnings are only emitted when declaring *new* tables with native types—use core types for portability and clarity.

**Learn more:** [Type System Concept](../explanation/type-system.md) · [Type System Reference](../reference/specs/type-system.md)

### Codecs

Codecs handle serialization for non-native data types:

| Codec | Description | Store | Compatibility |
|-------|-------------|-------|---------------|
| `<blob>` | DataJoint serialization of Python objects | In-table (was `longblob`) | Column comment only |
| `<blob@store>` | Large blobs, deduplicated by hash | Hash-addressed | Requires migration |
| `<attach@store>` | File attachments, deduplicated by hash | Hash-addressed | Requires migration |
| `<filepath@store>` | Managed file paths | Schema-addressed | Requires migration |
| `<object@store>` | General object storage interface (zarr, HDF5, custom) | Schema-addressed | New in 2.0 |
| `<npy@store>` | NumPy arrays via object storage | Schema-addressed | New in 2.0 |
| `<zarr@store>` | Zarr arrays (plugin, coming soon) | Schema-addressed | New in 2.0 |
| `<tiff@store>` | TIFF images (plugin, coming soon) | Schema-addressed | New in 2.0 |
| Custom | User-defined serialization | Any | New feature |

**Legacy AdaptedTypes:** Replaced by custom codecs. Users who implemented AdaptedTypes can convert them to the new codec API.

**Learn more:** [Codec API Reference](../reference/specs/codec-api.md) · [Custom Codecs Concept](../explanation/custom-codecs.md) · [Create Custom Codec](create-custom-codec.md)

### AutoPopulate 2.0

Per-table job management replaces the schema-level `~jobs` table:

| Aspect | Legacy (`~jobs`) | 2.0 (`~~table_name`) |
|--------|------------------|----------------------|
| Scope | One table per schema | One table per Computed/Imported |
| Table name | `~jobs` | `~~analysis`, `~~spike_sorting`, etc. |
| Key storage | Hashed (opaque) | Native primary key (readable) |
| Statuses | `reserved`, `error`, `ignore` | + `pending`, `success` |
| Priority | Not supported | `priority` column (lower = more urgent) |
| Scheduling | Not supported | `scheduled_time` for delayed jobs |
| Job metadata | Not supported | `_job_start_time`, `_job_duration`, `_job_version` |
| Semantic matching | Not supported | `~lineage` table for join validation |

**Migration:** Legacy `~jobs` continues to work. New `~~table_name` tables are created automatically when using `populate(reserve_jobs=True)`. Drop `~jobs` in Phase 4.

**Learn more:** [AutoPopulate Reference](../reference/specs/autopopulate.md) · [Computation Tutorial](../tutorials/basics/05-computation.ipynb)

### Fetch API Changes

The `fetch()` method is replaced with explicit output methods:

| Legacy | 2.0 | Returns |
|--------|-----|---------|
| `table.fetch()` | `table.to_arrays()` | NumPy record array |
| `table.fetch('a', 'b')` | `table.to_arrays('a', 'b')` | Tuple of arrays |
| `table.fetch("KEY", 'a', 'b')` | `table.to_arrays('a', 'b', include_key=True)` | Tuple: (key array, a, b) |
| `table.fetch(as_dict=True)` | `table.to_dicts()` | List of dicts |
| `table.fetch(format='frame')` | `table.to_pandas()` | DataFrame |
| `table.fetch("KEY")` | `table.keys()` | List of primary key dicts |
| `table.fetch(dj.key)` | `table.keys()` | List of primary key dicts |
| `table.fetch1()` | `table.fetch1()` | Single dict (unchanged) |
| `table.fetch1('a', 'b')` | `table.fetch1('a', 'b')` | Tuple of values (unchanged) |

**For AI agents:** Apply these substitutions mechanically. The conversion is straightforward.

### Removed API Components

The following legacy API components have been removed in 2.0:

| Legacy | Replacement | Notes |
|--------|-------------|-------|
| `dj.schema(...)` | `dj.Schema(...)` | Use capitalized class name |
| `dj.ERD(...)` | `dj.Diagram(...)` | ERD alias removed |
| `dj.Di(...)` | `dj.Diagram(...)` | Di alias removed |
| `dj.key` | `table.keys()` | Use keys() method instead |
| `dj.key_hash(...)` | — | Removed (was for legacy job debugging) |

**For AI agents:** Search and replace these patterns:

```python
# Schema alias
dj.schema(  →  dj.Schema(

# Diagram aliases
dj.ERD(  →  dj.Diagram(
dj.Di(   →  dj.Diagram(

# Key access (magic string and constant)
.fetch("KEY")   →  .keys()
.fetch(dj.key)  →  .keys()
```

### Semantic Matching

DataJoint 2.0 uses **semantic matching** for joins instead of classic natural joins. Rather than matching attributes solely by name, DataJoint validates that attributes share common lineage (origin) before allowing binary operations (`*`, `&`, `-`).

**Why this matters:** In classic natural joins, two attributes named `session_id` would be matched even if they refer to different entities. Semantic matching prevents this by ensuring attributes have the same semantic meaning through their foreign key relationships.

**Impact:** A small number of existing queries may fail if they join tables on attributes that have the same name but different origins. Phase 2 builds the `~lineage` table that tracks attribute origins through foreign key relationships.

**If a query fails semantic checking:** This indicates the join is likely malformed. Review the query to ensure:

- Attributes being matched represent the same entity (share lineage)
- You're not accidentally joining on attributes that happen to have the same name
- The tables have a logical relationship through foreign keys

If you genuinely need to join on attributes with the same name but different lineage (rare), you can bypass the check:

```python
# Only if intentionally joining on name-matched but semantically unrelated attributes
result = TableA.join(TableB, semantic_check=False)
```

**Learn more:** [Semantic Matching Specification](../reference/specs/semantic-matching.md) · [Query Algebra](../explanation/query-algebra.md)

---

## Phase 1: Run DataJoint 2.0 on Existing Databases

**Goal:** Get DataJoint 2.0 Python code working with existing legacy databases without any schema modifications.

### 1.1 Configure and Verify Settings

**First step:** Migrate configuration from `dj_local_conf.json` to 2.0 format.

#### Configuration File Migration

```bash
# legacy location
dj_local_conf.json

# 2.0 locations (priority order)
.secrets/              # Credentials (gitignored)
datajoint.json         # Non-sensitive settings
environment variables  # DJ_HOST, DJ_USER, etc.
```

#### Migration Steps

```python
import datajoint as dj

# Step 1: Create template configuration
dj.config.save_template()  # Creates datajoint.json template

# Step 2: Move credentials to .secrets/
# Create .secrets/datajoint.json with:
# {
#   "database.host": "your-host",
#   "database.user": "your-user",
#   "database.password": "your-password"
# }

# Step 3: Verify connection
dj.conn()  # Should connect successfully

# Step 4: Verify store configuration (if using external storage)
from datajoint.migrate import check_store_configuration
check_store_configuration(schema)
```

#### AI Agent Prompt (Phase 1 - Configuration)

```
You are setting up DataJoint 2.0 configuration for an existing project.

TASK: Migrate from dj_local_conf.json to 2.0 configuration format.

STEPS:
1. Read existing dj_local_conf.json (if present)
2. Create datajoint.json with non-sensitive settings
3. Create .secrets/datajoint.json with credentials
4. Add .secrets/ to .gitignore if not present
5. Verify connection: dj.conn()
6. If external stores configured, verify: check_store_configuration(schema)

CONFIGURATION MAPPING:
- database.host → .secrets/datajoint.json or DJ_HOST env var
- database.user → .secrets/datajoint.json or DJ_USER env var
- database.password → .secrets/datajoint.json or DJ_PASS env var
- stores.* → datajoint.json (paths) + .secrets/ (credentials)

VERIFICATION:
- dj.conn() succeeds
- dj.config shows expected values
- External stores accessible (if configured)

DO NOT commit credentials to version control.
```

### 1.2 Breaking API Changes

The following legacy patterns must be updated in Python code:

#### Fetch API (Removed)

```python
# legacy (REMOVED)
data = table.fetch()
data = table.fetch('attr1', 'attr2')
data = table.fetch(as_dict=True)
row = table.fetch1()

# 2.0 Replacements
data = table.to_arrays()                    # recarray-like
data = table.to_arrays('attr1', 'attr2')    # tuple of arrays
data = table.to_dicts()                     # list of dicts
row = table.fetch1()                        # unchanged for single row
keys = table.keys()                         # primary keys as dicts
df = table.to_pandas()                      # NEW: DataFrame output
```

#### Update Method (Removed)

```python
# legacy (REMOVED)
(table & key)._update('attr', value)

# 2.0 Replacement
table.update1({**key, 'attr': value})
```

#### Join Operators (Changed)

```python
# legacy (REMOVED)
result = table1 @ table2           # natural join without semantic check
result = dj.U('attr') * table      # universal set multiplication

# 2.0 Replacements
result = table1 * table2           # try natural join first (with semantic check)
# If semantic check fails, review the join - it may be malformed
# Only use semantic_check=False if the bypass is truly needed:
result = table1.join(table2, semantic_check=False)

result = table                     # U(...) * table is just table
```

**Learn more:** [Query Algebra](../explanation/query-algebra.md) · [Query Algebra Specification](../reference/specs/query-algebra.md)

#### Insert Method (Changed)

```python
# legacy (DEPRECATED) - positional insert
table.insert1((1, 'subject_name', '2024-01-15'))
table.insert([(1, 'name1', '2024-01-15'), (2, 'name2', '2024-01-16')])

# 2.0 - key-value maps required
table.insert1({'subject_id': 1, 'name': 'subject_name', 'dob': '2024-01-15'})
table.insert([
    {'subject_id': 1, 'name': 'name1', 'dob': '2024-01-15'},
    {'subject_id': 2, 'name': 'name2', 'dob': '2024-01-16'},
])
```

**Why:** Positional inserts are fragile—they break silently when columns are added or reordered. Key-value maps are explicit and self-documenting.

#### Download Path for External Storage (Changed)

```python
# legacy - download_path parameter in fetch
data = table.fetch('attachment_col', download_path='/data/downloads')
filepath = (table & key).fetch1('filepath_col', download_path='/data/downloads')

# 2.0 - use configuration context manager
with dj.config.override(download_path='/data/downloads'):
    data = table.to_arrays('attachment_col')
    filepath = (table & key).fetch1('filepath_col')

# Or set globally
dj.config['download_path'] = '/data/downloads'
data = table.to_arrays('attachment_col')
```

**Why:** Separating download location from fetch calls simplifies the API and allows consistent configuration across multiple fetches.

### 1.3 Code Migration Checklist

For each Python module using DataJoint:

- [ ] Replace all `.fetch()` calls with appropriate 2.0 method
- [ ] Replace `._update()` with `.update1()`
- [ ] Replace `@` operator with `*` (review if semantic check fails)
- [ ] Replace `dj.U(...) * table` with just `table`
- [ ] Replace positional inserts with key-value dicts
- [ ] Replace `download_path=` parameter with `dj.config.override()`
- [ ] Update imports if using deprecated modules

### 1.4 AI Agent Prompt (Phase 1 - Code Migration)

```
You are migrating DataJoint code from legacy to 2.0.

TASK: Update Python code to use 2.0 API patterns.

CHANGES REQUIRED:

Fetch API:
1. Replace table.fetch() → table.to_arrays() or table.to_dicts()
2. Replace table.fetch(as_dict=True) → table.to_dicts()
3. Replace table.fetch('a', 'b') → table.to_arrays('a', 'b')
4. Replace table.fetch("KEY", 'a', 'b') → table.to_arrays('a', 'b', include_key=True)
5. Replace table.fetch("KEY") → table.keys()
6. Replace table.fetch(dj.key) → table.keys()
7. Replace fetch('col', download_path='/path') → with dj.config.override(download_path='/path'): to_arrays('col')

Removed API:
8. Replace dj.schema( → dj.Schema(
9. Replace dj.ERD( → dj.Diagram(
10. Replace dj.Di( → dj.Diagram(
11. Remove dj.key_hash() calls (no replacement needed)

Query operators:
12. Replace (table & key)._update('attr', val) → table.update1({**key, 'attr': val})
13. Replace table1 @ table2 → table1 * table2 (if semantic check fails, review join)
14. Replace dj.U(...) * table → table (universal set * table is just table)

Insert patterns:
15. Replace positional inserts with key-value dicts:
    - table.insert1((val1, val2)) → table.insert1({'col1': val1, 'col2': val2})
    - table.insert([(v1, v2), ...]) → table.insert([{'c1': v1, 'c2': v2}, ...])

DO NOT modify table definitions or database schema.
```

---

## Phase 2: Schema Metadata Updates

**Goal:** Update database metadata (column comments) to enable 2.0 type recognition while maintaining full legacy compatibility.

### 2.0 Backup Before Schema Changes

**Create a full database backup before proceeding.** Phase 2 modifies column comments and creates hidden tables. While these changes are designed to be backward-compatible, a backup ensures you can recover if anything goes wrong.

```bash
# Full database dump (all schemas)
mysqldump -u root -p --all-databases --routines --triggers > backup_pre_phase2.sql

# Or specific schemas
mysqldump -u root -p --databases lab subject session ephys > backup_pre_phase2.sql

# Compressed backup for large databases
mysqldump -u root -p --all-databases | gzip > backup_pre_phase2.sql.gz
```

**For managed databases (AWS RDS, Azure, etc.):** Use your cloud provider's snapshot feature.

**Verify your backup** before proceeding:
```bash
# Check backup file size (should be non-trivial)
ls -lh backup_pre_phase2.sql*

# Optionally restore to a test database to verify
mysql -u root -p test_restore < backup_pre_phase2.sql
```

### 2.1 Column Type Labels

DataJoint 2.0 uses column comments to identify types. Migration adds type labels to:

**Numeric columns:**
```sql
-- legacy
COLUMN_TYPE = 'smallint unsigned'
COLUMN_COMMENT = 'trial number'

-- 2.0: Comment prefixed with core type
COLUMN_TYPE = 'smallint unsigned'
COLUMN_COMMENT = ':uint16:trial number'
```

**Blob columns:**
```sql
-- legacy
COLUMN_TYPE = 'longblob'
COLUMN_COMMENT = 'neural waveform data'

-- 2.0: Comment prefixed with codec
COLUMN_TYPE = 'longblob'
COLUMN_COMMENT = ':<blob>:neural waveform data'
```

**Why safe:** Legacy clients ignore the `:type:` prefix in comments—they read the MySQL column type directly.

### 2.2 Lineage Tables

DataJoint 2.0 tracks **attribute lineage**—the origin of each attribute through foreign key relationships. This enables:

- **Semantic matching:** Validates that join operands share common ancestors before allowing binary operations (`*`, `&`, `-`)
- **Query optimization:** Uses lineage to determine optimal join paths
- **Data provenance:** Traces how derived data relates to source data

Lineage is stored in a hidden `~lineage` table in each schema. The migration builds this table by analyzing foreign key relationships.

```sql
-- ~lineage table structure
CREATE TABLE `~lineage` (
    table_name VARCHAR(64) NOT NULL COMMENT 'table name within the schema',
    attribute_name VARCHAR(64) NOT NULL COMMENT 'attribute name',
    lineage VARCHAR(255) NOT NULL COMMENT 'origin: schema.table.attribute',
    PRIMARY KEY (table_name, attribute_name)
);
```

The `lineage` column stores the origin as a dot-separated string: `schema.table.attribute`. For example, `subject.subject.subject_id` indicates the attribute originated in the `subject` table of the `subject` schema.

**Why safe:** Legacy clients ignore tables prefixed with `~`.

**Learn more:** [Semantic Matching Specification](../reference/specs/semantic-matching.md) · [Query Algebra](../explanation/query-algebra.md) · [Entity Integrity Concept](../explanation/entity-integrity.md)

### 2.3 Migration Commands

```python
import datajoint as dj
from datajoint.migrate import migrate_columns

schema = dj.Schema('my_database')

# Step 1: Preview what needs migration
result = migrate_columns(schema, dry_run=True)
for col in result['columns']:
    print(f"{col['table']}.{col['column']}: {col['native_type']} → {col['core_type']}")

# Step 2: Apply migration (adds type labels to column comments)
result = migrate_columns(schema, dry_run=False)
print(f"Migrated {result['columns_migrated']} columns")

# Step 3: Build lineage table
schema.rebuild_lineage()
```

**Important:** When migrating multiple schemas, process them in **topological order** (upstream schemas first). For each schema, complete both database migration AND Python code updates before moving to the next schema.

If you process out of order, `rebuild_lineage()` raises a `DataJointError` identifying the missing upstream schema:

```
DataJointError: Cannot rebuild lineage for `session`.`session`:
referenced attribute `subject`.`subject`.`subject_id` has no lineage.
Rebuild lineage for schema `subject` first.
```

**Recovery:** Simply re-run in correct order—each `rebuild_lineage()` clears and rebuilds, so it's safe to retry.

```python
# Example: multi-schema pipeline
# Process each schema fully before moving to the next

# Schema 1: lab (no dependencies)
schema = dj.Schema('lab')
migrate_columns(schema, dry_run=False)
schema.rebuild_lineage()
# Now update src/pipeline/lab.py table definitions → core types

# Schema 2: subject (depends on lab)
schema = dj.Schema('subject')
migrate_columns(schema, dry_run=False)
schema.rebuild_lineage()
# Now update src/pipeline/subject.py table definitions → core types

# Schema 3: session (depends on subject)
schema = dj.Schema('session')
migrate_columns(schema, dry_run=False)
schema.rebuild_lineage()
# Now update src/pipeline/session.py table definitions → core types

# Schema 4: ephys (depends on session)
schema = dj.Schema('ephys')
migrate_columns(schema, dry_run=False)
schema.rebuild_lineage()
# Now update src/pipeline/ephys.py table definitions → core types
```

The database migration updates these column types:

- Numeric: `int unsigned` → `:uint32:`, `smallint` → `:int16:`, etc.
- Blobs: `longblob` → `:<blob>:`
- Attachments: `longblob` with attach comment → `:<attach>:`

External storage columns (`external-*`, `attach@*`, `filepath@*`) are **not** migrated here—they require Phase 3-4.

After the database migration for each schema, update the corresponding Python module(s) to use core types (see section 2.4).

### 2.4 Update Table Definitions

After migrating each schema's database metadata (section 2.3), update the corresponding Python module(s) to use core types instead of native MySQL types.

**Important:** Do this for each schema immediately after its database migration, maintaining topological order. This keeps the Python code in sync with the database as you progress through the pipeline.

#### Type Replacements

| Native Type (Legacy) | Core Type (2.0) |
|---------------------|-----------------|
| `tinyint` | `int8` |
| `tinyint unsigned` | `uint8` |
| `smallint` | `int16` |
| `smallint unsigned` | `uint16` |
| `int` | `int32` |
| `int unsigned` | `uint32` |
| `bigint` | `int64` |
| `bigint unsigned` | `uint64` |
| `float` | `float32` |
| `double` | `float64` |
| `longblob` | `<blob>` |

#### Special Cases

**Boolean attributes:**

Legacy DataJoint allowed `bool` or `boolean` in definitions, but MySQL converted these to `tinyint(1)`. DataJoint 2.0 has an explicit `bool` core type.

When migrating, the agent should infer intent from context:
- If the attribute stores true/false values → use `bool`
- If it stores small integers (0-255) → use `uint8`

```python
# Legacy: was this meant to be boolean or integer?
is_valid : tinyint(1)     # Likely boolean → bool
error_code : tinyint(1)   # Likely integer → uint8

# Ask user to confirm ambiguous cases
```

**Datetime and timestamp attributes:**

DataJoint 2.0 supports `datetime` with UTC only—no timezone support. Existing `timestamp` columns need review:

| Legacy Type | 2.0 Handling |
|-------------|--------------|
| `datetime` | Keep as `datetime` (UTC assumed) |
| `timestamp` | Convert to `datetime` (review timezone handling) |
| `date` | Keep as `date` (no change) |
| `time` | Keep as `time` (no change) |

For `timestamp` columns, the agent should ask the user:
- Was this storing UTC times? → Convert to `datetime`
- Was this using MySQL's auto-update behavior? → Review application logic

```python
# Legacy
created_at : timestamp    # Review: convert to datetime?
session_date : date       # No change needed

# 2.0
created_at : datetime     # UTC assumed
session_date : date       # Unchanged
```

**Enum attributes:**

`enum` is a core type in DataJoint 2.0—no changes required.

```python
# No change needed
sex : enum('M', 'F', 'U')
```

#### Example

```python
# Legacy definition
@schema
class Trial(dj.Manual):
    definition = """
    -> Session
    trial_num : smallint unsigned   # trial number
    ---
    start_time : float              # seconds
    duration : float                # seconds
    stimulus : longblob             # stimulus parameters
    """

# 2.0 definition
@schema
class Trial(dj.Manual):
    definition = """
    -> Session
    trial_num : uint16              # trial number
    ---
    start_time : float32            # seconds
    duration : float32              # seconds
    stimulus : <blob>               # stimulus parameters
    """
```

**Why update definitions?**

- **Clarity:** Core types are explicit about size and signedness
- **Portability:** Core types map consistently across database backends
- **Forward compatibility:** New tables should use core types; updating existing definitions maintains consistency

### 2.5 AI Agent Prompt (Phase 2)

```
You are migrating a DataJoint schema from legacy to 2.0.

TASK: Update database metadata AND corresponding Python module code.

CRITICAL: For multi-schema pipelines, process schemas in TOPOLOGICAL ORDER
(upstream first). Each rebuild_lineage() assumes upstream schemas are done.
For EACH schema, you must migrate both the database AND the Python code before
moving to the next schema.

WORKFLOW:
1. Identify all schemas and their dependencies (upstream → downstream)
2. For each schema in topological order:

   A. MIGRATE DATABASE:
      a. Connect: schema = dj.Schema('database_name')
      b. Preview: result = migrate_columns(schema, dry_run=True)
      c. Review columns needing migration
      d. Apply: migrate_columns(schema, dry_run=False)
      e. Build lineage: schema.rebuild_lineage()

   B. UPDATE PYTHON CODE:
      a. Identify Python module(s) defining this schema's tables
         (Look for @schema decorator or schema.context references)
      b. Open each module file
      c. Update table definition strings to use core types (see TYPE MAPPING below)
      d. Save and commit changes

   C. VERIFY before proceeding to next schema:
      - schema.rebuild_lineage() succeeded
      - Python code uses core types
      - Can import and instantiate tables with 2.0 client

TYPE MAPPING (for Python definition strings):
- tinyint unsigned → uint8
- smallint unsigned → uint16
- int unsigned → uint32
- bigint unsigned → uint64
- tinyint → int8
- smallint → int16
- int → int32
- bigint → int64
- float → float32
- double → float64
- longblob → <blob>
- enum → enum (no change)

SPECIAL CASES (ask user to confirm):
- tinyint(1) / bool / boolean: Infer intent from context.
  If stores true/false → bool. If stores integers → uint8.
- timestamp: Convert to datetime. DataJoint 2.0 uses UTC only.
  Ask user about timezone handling if unclear.

EXAMPLE WORKFLOW:
Schema: lab (no dependencies)
  → migrate_columns('lab')
  → rebuild_lineage()
  → Update src/pipeline/lab.py table definitions
  → Verify: import lab; lab.User()

Schema: subject (depends on lab)
  → migrate_columns('subject')
  → rebuild_lineage()
  → Update src/pipeline/subject.py table definitions
  → Verify: import subject; subject.Subject()

FINAL VERIFICATION:
- All schemas migrated in topological order
- All Python modules updated
- Legacy clients still work (ignore comment prefixes)
- 2.0 client recognizes all types (except legacy external storage and AdaptedTypes - see Phase 3)
- All ~lineage tables exist
```

### 2.6 Validation

After Phase 2:

- [ ] Legacy clients can still read/write all data
- [ ] 2.0 clients recognize all column types except:
  - Legacy external storage (`external-*`, `attach@*`, `filepath@*`) - requires Phase 3-4
  - Legacy AdaptedTypes - requires Phase 3 conversion to Codecs
- [ ] `~lineage` table exists and is populated for each schema
- [ ] Python definition strings updated to use core types
- [ ] No data format changes occurred

**Why safe:** Legacy ignores `~lineage` tables (prefixed with `~`). Definition string changes don't affect the database.

**Next steps:** If your schema uses legacy external storage or AdaptedTypes, proceed to Phase 3. Otherwise, your migration is complete and you can skip to Phase 5 to learn about new features.

---

## Phase 3: External Storage Migration

**Goal:** Create dual attributes for external storage columns, enabling both APIs to coexist safely during cross-testing.

**Skip this phase** if your schema does not use legacy external storage (`external-*`, `attach@*`, `filepath@*`).

### 3.1 Create Per-Table Job Tables (Optional)

Jobs 2.0 uses per-table job tracking. These are created automatically when using `populate(reserve_jobs=True)`, but you can create them explicitly:

```python
# For each Computed/Imported table
MyComputedTable.jobs.refresh()  # Creates ~~my_computed_table if missing
```

**Why safe:** Legacy ignores tables prefixed with `~~`. The legacy `~jobs` table remains functional.

### 3.2 Add Job Metadata Columns (Optional)

```python
from datajoint.migrate import add_job_metadata_columns

# Preview
result = add_job_metadata_columns(schema, dry_run=True)

# Apply (adds _job_start_time, _job_duration, _job_version)
result = add_job_metadata_columns(schema, dry_run=False)
```

**Why safe:** Legacy ignores columns prefixed with `_` (hidden attributes).

### 3.3 Migrate Legacy AdaptedAttributes

**Skip this section** if you did not create custom `dj.AttributeAdapter` subclasses.

Legacy DataJoint allowed advanced users to define custom column types via `AttributeAdapter`. In DataJoint 2.0, this is replaced by the **[Codec API](../reference/specs/codec-api.md)**.

#### Migration Steps

1. **Identify existing adapters** in your codebase:
   ```bash
   grep -r "AttributeAdapter\|dj.AttributeAdapter" --include="*.py" .
   ```

2. **For each adapter found**, point your AI agent to the [Codec API Specification](../reference/specs/codec-api.md) to rewrite it as a codec.

3. **Update table definitions** to use the new codec syntax instead of adapter type names.

#### Example Transformation

```python
# Legacy AttributeAdapter
@schema
class MyAdapter(dj.AttributeAdapter):
    attribute_type = 'longblob'

    def put(self, obj):
        return pickle.dumps(obj)

    def get(self, value):
        return pickle.loads(value)

# 2.0 Codec (see Codec API Spec for full details)
@dj.codec('my_type')
class MyCodec:
    dtype = 'bytes'  # Use bytes since pickle already serializes

    def encode(self, obj):
        return pickle.dumps(obj)

    def decode(self, value):
        return pickle.loads(value)
```

#### AI Agent Prompt (AdaptedAttribute Migration)

```
You are migrating a legacy DataJoint AttributeAdapter to the 2.0 Codec API.

REFERENCE: Read the Codec API Specification for the full codec interface.

TASK:
1. Identify the AttributeAdapter subclass and its put/get methods
2. Create a new codec class with encode/decode methods
3. Register it with @dj.codec('type_name') decorator
4. Update table definitions to use the new codec type

The user will point you to their adapter code. Ask clarifying questions
if the adapter behavior is unclear.
```

**Note:** Existing data stored via AttributeAdapter remains readable—the underlying blob format is unchanged. Only the Python interface changes.

### 3.4 Dual Attributes for External Storage

For tables with external blob/attach/filepath attributes, create **duplicate attributes** that support the 2.0 API while preserving the original for legacy compatibility.

#### Naming Convention

```
Original attribute:  signal        (legacy API - BINARY(16) with :external:)
New attribute:       signal_v2     (2.0 API - JSON with metadata)
```

#### How It Works

1. **Idempotent migration script** scans for columns with `:external*:` in comments
2. For each legacy external attribute, adds a new `<name>_v2` attribute with JSON type
3. Copies data from the `~external_<store>` table into the new JSON field
4. Both attributes coexist - legacy reads `signal`, 2.0 reads `signal_v2`

#### Migration Commands

Two functions handle different external storage types:

| Function | Handles |
|----------|---------|
| `migrate_external()` | `external-*` blobs and `attach@*` attachments |
| `migrate_filepath()` | `filepath@*` managed file paths |

```python
from datajoint.migrate import migrate_external, migrate_filepath

# Step 1: Preview external blobs/attachments
result = migrate_external(schema, dry_run=True)
for col in result['details']:
    print(f"{col['table']}.{col['column']} → {col['column']}_v2")

# Step 2: Preview filepaths
result = migrate_filepath(schema, dry_run=True)
for col in result['details']:
    print(f"{col['table']}.{col['column']} → {col['column']}_v2")

# Step 3: Create dual attributes (idempotent - safe to run multiple times)
migrate_external(schema, dry_run=False)
migrate_filepath(schema, dry_run=False)

# Step 4: Verify data accessible via both APIs
# Legacy: table.fetch('signal')     → reads from BINARY(16) column
# 2.0:    table.fetch1('signal_v2') → reads from JSON column
```

#### Schema Change Example

```sql
-- Before (legacy only)
CREATE TABLE recording (
    recording_id INT UNSIGNED NOT NULL,
    signal BINARY(16) COMMENT ':external-raw:neural signal data',
    PRIMARY KEY (recording_id)
);

-- After Phase 3 (both APIs supported)
CREATE TABLE recording (
    recording_id INT UNSIGNED NOT NULL,
    signal BINARY(16) COMMENT ':external-raw:neural signal data',
    signal_v2 JSON COMMENT ':blob@raw: neural signal data',
    PRIMARY KEY (recording_id)
);
```

#### Table Definition Update (Recommended)

Update Python table definitions to declare both attributes:

```python
@schema
class Recording(dj.Manual):
    definition = '''
    recording_id : int unsigned
    ---
    signal : external-raw          # Legacy API
    signal_v2 : <blob@raw>         # 2.0 API
    '''
```

**Why safe:**

- Legacy reads `signal` (original column)
- 2.0 reads `signal_v2` (new column)
- Each API uses its own column—no interference
- Rollback: simply drop the `*_v2` columns

**Cross-testing:** During this phase, test your pipeline with both APIs to verify data consistency before Phase 4.

### 3.5 AI Agent Prompt (Phase 3)

```
You are creating dual attributes for external storage migration.

TASK: Add _v2 columns for external storage to enable cross-testing.

PREREQUISITE: Phase 2 must be complete (~lineage tables exist).

STEPS:
1. Connect to schema: schema = dj.Schema('database_name')
2. Create dual external attributes:
   - from datajoint.migrate import migrate_external
   - result = migrate_external(schema, dry_run=False)
3. Optionally create job tables:
   - TableClass.jobs.refresh() for Computed/Imported tables

VERIFICATION:
- Fetch from original attribute with LEGACY client → works
- Fetch from *_v2 attribute with 2.0 client → works
- Compare data from both APIs for consistency

REPORT:
- List all *_v2 columns created
- Row counts migrated per column
- Any data mismatches found during cross-testing
```

### 3.6 Phase 3 Checklist

- [ ] Migrate any `AttributeAdapter` subclasses to Codec API
- [ ] Run `migrate_external()` for each schema with external storage
- [ ] Optionally run `Table.jobs.refresh()` for Computed/Imported tables
- [ ] Optionally run `add_job_metadata_columns()`
- [ ] Verify legacy clients can read original external attributes
- [ ] Verify 2.0 clients can read new `*_v2` attributes
- [ ] Cross-test: compare data from both APIs for consistency
- [ ] Update table definitions to declare both attributes

---

## Phase 4: Point of No Return

**WARNING:** After Phase 4, legacy clients will no longer work with the database.

### 4.1 Pre-Flight Checklist

Before proceeding:

- [ ] **All clients upgraded:** Confirm no legacy processes running
- [ ] **Database backup:** Full backup with tested restore procedure
- [ ] **Dual attributes verified:** All `*_v2` attributes have valid data (from Phase 3)
- [ ] **Pipeline quiesced:** No active populate jobs
- [ ] **Team confirmation:** All users aware of cutover

### 4.2 Finalize External Storage Migration

Phase 3 created dual attributes (`signal` + `signal_v2`). Now remove the legacy attributes.

```python
from datajoint.migrate import migrate_external

# Step 1: Verify all *_v2 attributes have data
result = migrate_external(schema, dry_run=True, finalize=True)
for col in result['details']:
    print(f"{col['table']}: {col['column']} → finalize")
    print(f"  Rows migrated: {col['rows']}")

# Step 2: Finalize (renames legacy → _v1, renames _v2 → original name)
result = migrate_external(schema, dry_run=False, finalize=True)

# After finalization:
# - signal renamed to signal_v1 (legacy backup)
# - signal_v2 renamed to signal
# - ~external_* tables can be dropped
```

**Breaking:** Legacy clients cannot read the new JSON-format columns.

### 4.3 Cleanup Legacy Tables

```python
# Drop legacy jobs table (after confirming populate(reserve_jobs=True) works)
schema.connection.query(f"DROP TABLE IF EXISTS `{schema.database}`.`~jobs`")

# Drop legacy external tracking tables (after external migration finalized)
for store in ['external', 'external_raw', ...]:  # your store names
    schema.connection.query(f"DROP TABLE IF EXISTS `{schema.database}`.`~external_{store}`")
```

### 4.4 Update Table Definitions

Update Python source code to use 2.0 type syntax (remove dual attributes):

```python
# Phase 3 syntax (dual attributes)
definition = '''
    recording_id : int unsigned
    ---
    signal : external-raw          # Legacy API
    signal_v2 : <blob@raw>         # 2.0 API
'''

# Phase 4 syntax (2.0 only)
definition = '''
    recording_id : uint32
    ---
    signal : <blob@raw>            # Single attribute, 2.0 format
'''
```

#### Type Syntax Updates

| Legacy Syntax | 2.0 Syntax |
|---------------|------------|
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

### 4.5 AI Agent Prompt (Phase 4 - Pre-Flight)

```
You are preparing for the point-of-no-return migration phase.

TASK: Verify all prerequisites before breaking legacy compatibility.

PRE-FLIGHT CHECKS:
1. Database backup exists and restore tested
2. No legacy client processes running (check SHOW PROCESSLIST)
3. All *_v2 dual attributes have complete data (from Phase 3)
4. No pending populate jobs
5. Team notified of cutover

VERIFICATION COMMANDS:
- schema.connection.query("SHOW PROCESSLIST") - check for old clients
- from datajoint.migrate import migrate_columns
- result = migrate_columns(schema, dry_run=True) - verify Phase 2 complete (columns should be empty)
- from datajoint.migrate import migrate_external
- result = migrate_external(schema, dry_run=True, finalize=True) - verify Phase 3 data complete

REPORT FORMAT:
- Backup status: [confirmed/missing]
- Active clients: [list any legacy processes]
- Dual attributes: [all complete/rows missing]
- Migration status: [ready/blockers]

DO NOT proceed if any blockers found. Report issues to user.
```

### 4.6 AI Agent Prompt (Phase 4 - Execution)

```
You are finalizing DataJoint 2.0 migration. Legacy support is being removed.

TASK: Finalize external storage and update table definitions.

STEPS:
1. Finalize external migration:
   - from datajoint.migrate import migrate_external
   - migrate_external(schema, dry_run=False, finalize=True)

2. Drop legacy tables:
   - DROP TABLE IF EXISTS `schema`.`~jobs`
   - DROP TABLE IF EXISTS `schema`.`~external_*`

3. Update table definitions to 2.0 syntax:
   - Remove dual attributes (keep only *_v2 version, rename to original)
   - Update type syntax (see TYPE REPLACEMENTS below)

TYPE REPLACEMENTS:
- int unsigned → uint32
- int → int32
- smallint unsigned → uint16
- tinyint unsigned → uint8
- float → float32
- double → float64
- longblob → <blob>
- external-store → <blob@store>
- attach@store → <attach@store>
- filepath@store → <filepath@store>

VERIFICATION:
- All tables accessible via 2.0 client
- All external data fetchable
- No legacy tables remaining
```

### 4.7 Phase 4 Checklist

- [ ] Pre-flight checks passed
- [ ] Database backup verified
- [ ] `migrate_external(finalize=True)` executed successfully
- [ ] Legacy `~jobs` table dropped
- [ ] Legacy `~external_*` tables dropped
- [ ] Table definitions updated to 2.0 syntax
- [ ] All dual attributes consolidated
- [ ] Full functionality verified with 2.0 client only

---

## Phase 5: Adopt New Features

### 5.1 Feature Adoption Order

Recommended order from simplest to most complex:

| Order | Feature | Complexity | Tutorial |
|-------|---------|------------|----------|
| 1 | dj.Top operator | Low | [Query Algebra](../explanation/query-algebra.md) · [Queries Tutorial](../tutorials/basics/04-queries.ipynb) |
| 2 | Core types (uint32, float64) | Low | [Define Tables](define-tables.md) |
| 3 | Configuration system | Low | [Configuration Reference](../reference/configuration.md) |
| 4 | Semantic matching | Medium | [Query Algebra](../explanation/query-algebra.md) · [Semantic Matching Spec](../reference/specs/semantic-matching.md) |
| 5 | Jobs 2.0 | Medium | [Distributed Computing](../tutorials/advanced/distributed.ipynb) |
| 6 | Custom codecs | Medium | [Custom Codecs](../tutorials/advanced/custom-codecs.ipynb) |
| 7 | Object storage | High | [Object Storage Tutorial](../tutorials/basics/06-object-storage.ipynb) |

### 5.2 AI Agent Prompt (Phase 5 - Learning)

```
You are helping a user learn DataJoint 2.0 features after migration.

TASK: Guide adoption of new features based on user's needs.

FEATURE PRIORITY:
1. dj.Top - If user has pagination/ordering queries
2. Semantic matching - If user has complex joins across schemas
3. Jobs 2.0 - If user runs distributed computations
4. Custom codecs - If user has domain-specific data types
5. Object storage - If user has large arrays or files

FOR EACH FEATURE:
1. Assess current usage patterns in user's code
2. Identify where new feature would help
3. Provide minimal example from their codebase context
4. Link to appropriate tutorial document

DO NOT introduce all features at once. Focus on immediate value.
```

### 5.3 Learning Resources

- **Basics**: [Tutorials](../tutorials/index.md) - Start here for core concepts
- **Advanced**: [Advanced Tutorials](../tutorials/advanced/custom-codecs.ipynb) - Codecs, distributed computing
- **How-To**: [How-To Guides](index.md) - Task-oriented guides
- **Concepts**: [Explanation](../explanation/index.md) - Why things work the way they do
- **Reference**: [Reference](../reference/index.md) - Complete API and specification

---

## Phase 6: Cleanup Legacy Tables (Optional)

**Goal:** Remove legacy hidden tables that are no longer needed after full migration to 2.0.

### 6.1 Tables to Remove

| Table | Purpose | When to Drop |
|-------|---------|--------------|
| `~log` | Schema change log | After confirming no tools depend on it |
| `~jobs` | Legacy job reservation | After confirming `populate(reserve_jobs=True)` works |
| `~external_*` | Legacy external storage tracking | After Phase 4 (external migration finalized) |

### 6.2 Cleanup Commands

```python
import datajoint as dj

schema = dj.Schema('my_database')
conn = schema.connection

# Step 1: Verify no legacy processes are using these tables
# Check that all clients are on 2.0

# Step 2: Drop legacy log table
conn.query(f"DROP TABLE IF EXISTS `{schema.database}`.`~log`")

# Step 3: Drop legacy jobs table (after populate(reserve_jobs=True) works)
conn.query(f"DROP TABLE IF EXISTS `{schema.database}`.`~jobs`")

# Step 4: Drop legacy external tracking tables
# List your store names
for store in ['external', 'external_raw', 'external_analysis']:
    conn.query(f"DROP TABLE IF EXISTS `{schema.database}`.`~external_{store}`")
```

### 6.3 Pre-Cleanup Checklist

- [ ] All clients upgraded to DataJoint 2.0
- [ ] No legacy processes running
- [ ] `populate(reserve_jobs=True)` works correctly
- [ ] External storage migration finalized (Phase 4 complete)
- [ ] Database backup taken

### 6.4 AI Agent Prompt (Phase 6)

```
You are cleaning up legacy tables after DataJoint 2.0 migration.

TASK: Remove legacy hidden tables that are no longer needed.

PREREQUISITES:
- Phase 4 must be complete (no legacy clients)
- populate(reserve_jobs=True) must work
- Database backup must exist

TABLES TO DROP:
- ~log: Schema change log (rarely used)
- ~jobs: Legacy job reservation table
- ~external_*: Legacy external storage tracking

STEPS:
1. Verify no legacy processes: SHOW PROCESSLIST
2. Verify job reservation works: test populate(reserve_jobs=True)
3. Drop tables using: DROP TABLE IF EXISTS `schema`.`~table_name`
4. Verify cleanup complete

DO NOT drop tables if any legacy clients are still running.
```

---

## Helper Functions in datajoint.migrate

The migration module focuses on **integrity checks**, **rebuild/restore** utilities, and **idempotent migration scripts**.

### Column Type Migration (Phase 2)

```python
migrate_columns(schema, dry_run=True) -> dict
```

Analyzes and migrates column type labels. Returns dict with:

- `columns`: list of columns to migrate (`table`, `column`, `native_type`, `core_type`)
- `columns_migrated`: count of columns updated (0 if dry_run=True)
- `external_storage`: columns requiring Phase 3-4 (not migrated here)

Use `dry_run=True` to preview, `dry_run=False` to apply. Migrates numeric types, `<blob>`, `<attach>`. Skips external storage (`external-*`, `attach@*`, `filepath@*`).

### External Storage Migration (Phase 3-4)

```python
# Analysis (internal)
_find_external_columns(schema) -> list[dict]
_find_filepath_columns(schema) -> list[dict]

# Migration (idempotent)
migrate_external(schema, dry_run=True, finalize=False) -> dict
migrate_filepath(schema, dry_run=True, finalize=False) -> dict
```

Use `dry_run=True` to preview, `dry_run=False` to execute.
Use `finalize=True` in Phase 4 to complete the migration.

### Job Metadata

```python
add_job_metadata_columns(target, dry_run=True) -> dict
```

### Integrity & Rebuild Functions

```python
def check_store_configuration(schema) -> dict:
    """
    Verify external stores are properly configured.

    Returns dict with:

    - stores_configured: list of store names with valid config
    - stores_missing: list of stores referenced but not configured
    - stores_unreachable: list of stores that failed connection test
    """

def rebuild_lineage(schema, dry_run=True) -> dict:
    """
    Rebuild ~lineage table from current table definitions.
    Use after schema changes or to repair corrupted lineage data.
    """

def verify_external_integrity(schema, store_name=None) -> dict:
    """
    Check that all external references point to existing files.

    Returns dict with:

    - total_references: count of external entries
    - valid: count with accessible files
    - missing: list of entries with inaccessible files
    - stores_checked: list of store names checked
    """
```

---

## Verification Commands

### Per-Phase Verification

```python
import datajoint as dj
from datajoint.migrate import migrate_columns

schema = dj.Schema('my_database')

# Phase 1: Code works (manual testing)
# - Run existing queries with 2.0 client
# - Verify data readable

# Phase 2: Column type labels migrated
result = migrate_columns(schema, dry_run=True)
print(f"Columns to migrate: {len(result['columns'])}")

# Phase 3: Hidden tables exist
has_lineage = schema.connection.query(
    "SELECT COUNT(*) FROM information_schema.TABLES "
    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='~lineage'",
    args=(schema.database,)
).fetchone()[0] > 0
print(f"Lineage table: {'present' if has_lineage else 'missing'}")

# Phase 4: External storage migrated
from datajoint.migrate import _find_external_columns
external = _find_external_columns(schema)
print(f"External columns remaining: {len(external)}")  # Should be 0

# Phase 5: Feature adoption (per-feature testing)
```

---

## Troubleshooting

### "Native type 'int' is used"

Run Phase 2 to add type labels to numeric columns.

### "No codec registered"

Run Phase 2 to add codec labels to blob columns.

### External data not found

Phase 3/4: Store paths don't match legacy paths. Check:

1. Store location in datajoint.json matches original
2. Path structure matches what's in `~external_*` table

### Missing ~lineage table

Run Phase 3 to create the lineage table with `schema.rebuild_lineage()`.

### Dual attributes out of sync

Re-run `migrate_external()` - it's idempotent and will update any missing rows.

---

## See Also

- [What's New in 2.0](../explanation/whats-new-2.md)
- [Type System](../explanation/type-system.md)
- [Configuration Reference](../reference/configuration.md)
