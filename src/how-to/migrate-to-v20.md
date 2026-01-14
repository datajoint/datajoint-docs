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

DataJoint 2.0 introduces portable type aliases (`uint32`, `float64`, etc.) that prepare the codebase for **PostgreSQL backend compatibility** in a future release. Migration to core types ensures your schemas will work seamlessly when Postgres support is available.

---

## What's New in 2.0

### 3-Tier Column Type System

DataJoint 2.0 introduces a unified type system with three tiers:

| Tier | Description | Examples | Migration |
|------|-------------|----------|-----------|
| **Native** | Raw MySQL types | `int unsigned`, `tinyint` | Auto-converted to core types |
| **Core** | Standardized portable types | `uint32`, `float64`, `varchar(100)`, `json` | Phase I |
| **Codec** | Serialization to blob or storage | `<blob>`, `<blob@store>`, `<npy@>` | Phase I-III |

**Learn more:** [Type System Concept](../explanation/type-system.md) · [Type System Reference](../reference/specs/type-system.md)

### Codecs

Codecs handle serialization for non-native data types:

| Codec | Description | Storage | Legacy Format | Migration |
|-------|-------------|---------|---------------|-----------|
| `<blob>` | Python object serialization | In-table | `longblob` | Phase I code, Phase III data |
| `<attach>` | Inline file attachments | In-table | `attach` | Phase I code, Phase III data |
| `<blob@store>` | Large blobs, hash-addressed | In-store (hash) | `external-store`, `blob@store` | Phase I code, Phase III data |
| `<attach@store>` | File attachments, hash-addressed | In-store (hash) | `attach@store` | Phase I code, Phase III data |
| `<filepath@store>` | Managed file paths | In-store (filepath) | `filepath@store` | Phase I code, Phase III data |
| `<npy@store>` | NumPy arrays with lazy loading | In-store (schema) | **New in 2.0** | Phase IV adoption |
| `<object@store>` | Object storage (zarr, HDF5, custom) | In-store (schema) | **New in 2.0** | Phase IV adoption |

**Key principles:**

- All codec conversions (in-table and legacy in-store) are implemented in Phase I using test stores
- Production data migration happens in Phase III
- Schema-addressed storage (`<npy@>`, `<object@>`) is new in 2.0 - adopt in Phase IV, no migration needed

**Learn more:** [Codec API Reference](../reference/specs/codec-api.md) · [Custom Codecs](../explanation/custom-codecs.md)

### Unified Stores Configuration

DataJoint 2.0 replaces `external.*` with unified `stores.*` configuration:

**0.14.x (legacy):**
```json
{
  "external": {
    "protocol": "file",
    "location": "/data/external"
  }
}
```

**2.0 (unified stores):**
```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/stores"
    }
  }
}
```

**Learn more:** [Configuration Reference](../reference/configuration.md) · [Configure Object Storage](configure-storage.md)

### Query API Changes

| 0.14.x | 2.0 | Phase |
|--------|-----|-------|
| `table.fetch()` | `table.to_arrays()` or `table.to_dicts()` | I |
| `table.fetch1()` | `table.fetch1()` (unchanged) | — |
| `(table & key)._update('attr', val)` | `table.update1({**key, 'attr': val})` | I |
| `table1 @ table2` | `table1.join(table2, semantic_check=False)` | I |
| `dj.U('attr') * table` | `dj.U('attr') & table` | I |

**Learn more:** [Fetch API Reference](../reference/specs/fetch-api.md) · [Query Operators Reference](../reference/operators.md)

---

## Migration Overview

| Phase | Goal | Code Changes | Schema/Store Changes | Production Impact |
|-------|------|--------------|----------------------|-------------------|
| **I** | Branch & code migration | All API updates, type syntax, **all codecs** (in-table and in-store) | Empty `_v2` schemas + test stores | **None** |
| **II** | Test compatibility | — | Populate `_v2` schemas with sample data, test equivalence | **None** |
| **III** | Migrate production data | — | Multiple migration options | **Varies** |
| **IV** | Adopt new features | Optional enhancements | Optional | Running on 2.0 |

**Key principles:**

- Phase I implements ALL code changes including in-store codecs (using test stores)
- Production runs on 0.14.x undisturbed through Phase II
- Phase III is data migration only—the code is already complete

**Timeline:**

- **Phase I:** ~1-4 hours (with AI assistance)
- **Phase II:** ~1-2 days
- **Phase III:** ~1-7 days (depends on data size and option chosen)
- **Phase IV:** Ongoing feature adoption

---

## Phase I: Branch and Code Migration

**Goal:** Implement complete 2.0 API in code using test schemas and test stores.

**End state:**

- All Python code uses 2.0 API patterns (fetch, types, codecs)
- All codecs implemented (in-table `<blob>`, `<attach>` AND in-store `<blob@>`, legacy only)
- Code points to `schema_v2` databases (empty) and test object stores
- Production continues on main branch with 0.14.x undisturbed

**What's NOT migrated yet:** Production data and production stores (Phase III)

### Step 1: Pin Legacy DataJoint on Main Branch

Ensure production code stays on 0.14.x:

```bash
git checkout main

# Pin legacy version in requirements
echo "datajoint==0.14.6" > requirements.txt

git add requirements.txt
git commit -m "chore: pin datajoint 0.14.6 for production"
git push origin main
```

**Why:** This prevents accidental upgrades to 2.0 in production.

### Step 2: Create Migration Branch

```bash
# Create feature branch
git checkout -b pre/v2.0

# Install DataJoint 2.0
pip install --upgrade pip
pip install "datajoint>=2.0.0"

# Update requirements
echo "datajoint>=2.0.0" > requirements.txt

git add requirements.txt
git commit -m "chore: upgrade to datajoint 2.0"
```

### Step 3: Configure DataJoint 2.0

Create new configuration files for 2.0.

#### Background: Configuration Changes

DataJoint 2.0 uses:

- **`.secrets/datajoint.json`** for credentials (gitignored)
- **`datajoint.json`** for non-sensitive settings (checked in)
- **`stores.*`** instead of `external.*`

**Learn more:** [Configuration Reference](../reference/configuration.md)

#### Create Configuration Files

```bash
# Create .secrets directory
mkdir -p .secrets
echo ".secrets/" >> .gitignore

# Create template
python -c "import datajoint as dj; dj.config.save_template()"
```

**Edit `.secrets/datajoint.json`:**
```json
{
  "database.host": "your-database-host",
  "database.user": "your-username",
  "database.password": "your-password"
}
```

**Edit `datajoint.json`:**
```json
{
  "loglevel": "INFO",
  "safemode": true,
  "display.limit": 12,
  "display.width": 100,
  "display.show_tuple_count": true
}
```

#### Verify Connection

```python
import datajoint as dj

# Test connection
conn = dj.conn()
print(f"Connected to {conn.conn_info['host']}")
```

### Step 4: Configure Test Object Stores

**Important:** Configure TEST stores for Phase I development and testing. Production stores will be configured in Phase III.

If your pipeline uses in-store codecs (`<blob@>`, `<attach@>`, `<filepath@>`, `<npy@>`, `<object@>`), you'll convert ALL in-store code in Phase I. Set up test stores now for development.

#### Background: Unified Stores

2.0 uses **unified stores** configuration:

- Single `stores.*` config for all storage types
- Named stores with `default` pointer
- Supports multiple stores with different backends

**Learn more:** [Configure Object Storage](configure-storage.md) · [Object Store Configuration Spec](../reference/specs/object-store-configuration.md)

#### Configure Test Stores

**Edit `datajoint.json` to use test directories:**
```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/v2_test_stores/main"
    }
  }
}
```

**Note:** Use separate test locations (e.g., `/data/v2_test_stores/`) to avoid conflicts with production stores.

**For multiple test stores:**
```json
{
  "stores": {
    "default": "main",
    "filepath_default": "raw_data",
    "main": {
      "protocol": "file",
      "location": "/data/v2_test_stores/main"
    },
    "raw_data": {
      "protocol": "file",
      "location": "/data/v2_test_stores/raw"
    }
  }
}
```

**For cloud storage (using test bucket/prefix):**
```json
{
  "stores": {
    "default": "s3_store",
    "s3_store": {
      "protocol": "s3",
      "endpoint": "s3.amazonaws.com",
      "bucket": "my-datajoint-test-bucket",
      "location": "v2-test"
    }
  }
}
```

**Store credentials in `.secrets/stores.s3_store.access_key` and `.secrets/stores.s3_store.secret_key`:**
```bash
echo "YOUR_ACCESS_KEY" > .secrets/stores.s3_store.access_key
echo "YOUR_SECRET_KEY" > .secrets/stores.s3_store.secret_key
```

### Step 5: Convert Table Definitions

Update table definitions in topological order (tables before their dependents).

#### Background: Type Syntax Changes

Convert ALL types and codecs in Phase I:

| 0.14.x | 2.0 | Category |
|--------|-----|----------|
| `int unsigned` | `uint32` | Core type |
| `int` | `int32` | Core type |
| `smallint unsigned` | `uint16` | Core type |
| `tinyint unsigned` | `uint8` | Core type |
| `bigint unsigned` | `uint64` | Core type |
| `float` | `float32` | Core type |
| `double` | `float64` | Core type |
| `longblob` | `<blob>` | Codec (in-table) |
| `attach` | `<attach>` | Codec (in-table) |
| `external-store` / `blob@store` | `<blob@store>` | Codec (in-store) |
| `attach@store` | `<attach@store>` | Codec (in-store) |
| `filepath@store` | `<filepath@store>` | Codec (in-store) |

**Note:** Code for in-store codecs is converted in Phase I using test stores. Production data migration happens in Phase III.

**Learn more:** [Type System Reference](../reference/specs/type-system.md) · [Definition Syntax](../reference/definition-syntax.md)

#### AI Agent Prompt: Convert Table Definitions

Use this prompt with your AI coding assistant:

---

**🤖 AI Agent Prompt: Phase I - Table Definition Conversion**

```
You are converting DataJoint 0.14.x table definitions to 2.0 syntax.

TASK: Update all table definitions in this repository to DataJoint 2.0 type syntax.

CONTEXT:
- We are on branch: pre/v2.0
- Production (main branch) remains on 0.14.x
- All schemas will use _v2 suffix (e.g., my_pipeline → my_pipeline_v2)
- Schemas will be created empty for now

SCOPE - PHASE I:
1. Update schema declarations (add _v2 suffix)
2. Convert ALL type syntax to 2.0 core types
3. Convert ALL codecs (in-table AND in-store)
   - In-table: longblob → <blob>, attach → <attach>
   - In-store: blob@store → <blob@store>, filepath@store → <filepath@store>, etc.
4. Code will use TEST stores configured in datajoint.json
5. Production data migration happens in Phase III (code is complete after Phase I)

TYPE CONVERSIONS:

Core Types:
  int unsigned → uint32
  int → int32
  smallint unsigned → uint16
  smallint → int16
  tinyint unsigned → uint8
  tinyint → int8
  bigint unsigned → uint64
  bigint → int64
  float → float32
  double → float64
  decimal(M,D) → decimal(M,D)  # unchanged

In-Table Codecs:
  longblob → <blob>
  attach → <attach>

In-Store Codecs (convert legacy formats):
  external-store → <blob@store>  # Legacy 0.14.x format
  blob@store → <blob@store>  # Already correct syntax
  attach@store → <attach@store>
  filepath@store → <filepath@store>

NEW in 2.0 (optional adoption, not migration):
  <npy@store>  # NumPy arrays with lazy loading
  <object@store>  # Zarr, HDF5, or custom object formats
  # Use these for NEW attributes or to replace custom AdaptedTypes
  # No legacy equivalent - adopt in Phase IV after migration complete

String/Date Types (unchanged):
  varchar(N) → varchar(N)
  date → date
  datetime → datetime
  time → time
  timestamp → timestamp
  enum(...) → enum(...)

SCHEMA DECLARATIONS:
  OLD: schema = dj.schema('my_pipeline')
  NEW: schema = dj.schema('my_pipeline_v2')

PROCESS:
1. Identify all Python files with DataJoint schemas
2. For each schema:
   a. Update schema declaration (add _v2 suffix)
   b. Create schema on database (empty for now)
3. For each table definition in TOPOLOGICAL ORDER:
   a. Convert ALL type syntax (core types + all codecs)
   b. Verify syntax is valid
4. Test that all tables can be declared (run file to create tables)
5. Verify in-store codecs work with test stores

VERIFICATION:
- All schema declarations use _v2 suffix
- All native types converted to core types
- All codecs converted (in-table AND in-store)
- Test stores configured and accessible
- No syntax errors
- All tables create successfully (empty)

EXAMPLE CONVERSION:

# 0.14.x
schema = dj.schema('neuroscience_pipeline')

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : int unsigned
    ---
    sampling_rate : float
    signal : external-raw  # Legacy 0.14.x in-store format
    waveforms : blob@raw  # 0.14.x in-store syntax
    metadata : longblob
    """

# 2.0 (Phase I with test stores)
schema = dj.schema('neuroscience_pipeline_v2')

@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    sampling_rate : float32
    signal : <blob@raw>  # Migrated from external-raw
    waveforms : <blob@raw>  # Migrated from blob@raw
    metadata : <blob>  # Migrated from longblob
    """

# Optional Phase IV: Adopt schema-addressed storage for new features
@schema
class RecordingEnhanced(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    sampling_rate : float32
    signal : <npy@raw>  # NEW: NumPy with lazy loading (adopt in Phase IV)
    metadata : <blob>
    """

REPORT:
- Schemas converted: [list with _v2 suffix]
- Tables converted: [count by schema]
- Type conversions: [count by type]
- Codecs converted:
  - In-table: [count of <blob>, <attach>]
  - In-store: [count of <blob@>, <npy@>, <filepath@>]
- Tables created successfully: [list]
- Test stores configured: [list store names]

COMMIT MESSAGE FORMAT:
"feat(phase-i): convert table definitions to 2.0 syntax

- Update schema declarations to *_v2
- Convert native types to core types (uint32, float64, etc.)
- Convert all codecs (in-table + in-store)
- Configure test stores for development/testing

Tables converted: X
Codecs converted: Y (in-table: Z, in-store: W)"
```

---

### Step 6: Convert Query and Insert Code

Update all DataJoint API calls to 2.0 patterns.

#### Background: API Changes

**Fetch API:**
- `fetch()` → `to_arrays()` (recarray-like) or `to_dicts()` (list of dicts)
- `fetch('attr1', 'attr2')` → `to_arrays('attr1', 'attr2')` (returns tuple)
- `fetch1()` → unchanged (still returns dict for single row)

**Update Method:**
- `(table & key)._update('attr', val)` → `table.update1({**key, 'attr': val})`

**Join Operators:**
- `table1 @ table2` → `table1.join(table2, semantic_check=False)`
- `dj.U('attr') * table` → `dj.U('attr') & table`

**Learn more:** [Fetch API Reference](../reference/specs/fetch-api.md) · [Query Operators](../reference/operators.md)

#### AI Agent Prompt: Convert Query and Insert Code

---

**🤖 AI Agent Prompt: Phase I - Query and Insert Code Conversion**

```
You are converting DataJoint 0.14.x query and insert code to 2.0 API.

TASK: Update all query, fetch, and insert code to use DataJoint 2.0 API patterns.

CONTEXT:
- Branch: pre/v2.0
- Schema declarations already updated to _v2 suffix
- Table definitions already converted
- Production code on main branch unchanged

API CONVERSIONS:

1. Fetch API (always convert):
   OLD: data = table.fetch()
   NEW: data = table.to_arrays()  # recarray-like

   OLD: data = table.fetch(as_dict=True)
   NEW: data = table.to_dicts()  # list of dicts

   OLD: data = table.fetch('attr1', 'attr2')
   NEW: data = table.to_arrays('attr1', 'attr2')  # returns tuple

   OLD: row = table.fetch1()
   NEW: row = table.fetch1()  # UNCHANGED

   OLD: key = table.fetch1('KEY')
   NEW: key = table.fetch1('KEY')  # UNCHANGED

2. Update Method (always convert):
   OLD: (table & key)._update('attr', value)
   NEW: table.update1({**key, 'attr': value})

3. Join Operator (always convert):
   OLD: result = table1 @ table2
   NEW: result = table1.join(table2, semantic_check=False)

   Note: semantic_check=False maintains legacy behavior
         semantic_check=True enables lineage validation (new in 2.0)

4. Universal Set (always convert):
   OLD: result = dj.U('attr') * table
   NEW: result = dj.U('attr') & table

5. Insert/Delete (unchanged):
   table.insert(data)  # unchanged
   table.insert1(row)  # unchanged
   (table & key).delete()  # unchanged
   (table & restriction).delete()  # unchanged

PROCESS:
1. Find all Python files with DataJoint code
2. For each file:
   a. Search for fetch patterns
   b. Replace with 2.0 equivalents
   c. Search for update patterns
   d. Replace with update1()
   e. Search for @ and dj.U() * patterns
   f. Replace with join() and & operators
3. Run syntax checks
4. Run existing tests if available

VERIFICATION:
- No .fetch() calls remaining (except fetch1)
- No ._update() calls remaining
- No @ operator between tables
- No dj.U() * patterns
- All tests pass (if available)

COMMON PATTERNS:

Pattern 1: Fetch all as dicts
OLD: sessions = Session.fetch(as_dict=True)
NEW: sessions = Session.to_dicts()

Pattern 2: Fetch specific attributes
OLD: mouse_ids, dobs = Mouse.fetch('mouse_id', 'dob')
NEW: mouse_ids, dobs = Mouse.to_arrays('mouse_id', 'dob')

Pattern 3: Fetch single row
OLD: row = (Mouse & key).fetch1()  # unchanged
NEW: row = (Mouse & key).fetch1()  # unchanged

Pattern 4: Update attribute
OLD: (Session & key)._update('experimenter', 'Alice')
NEW: Session.update1({**key, 'experimenter': 'Alice'})

Pattern 5: Natural join without semantic check
OLD: result = Neuron @ Session
NEW: result = Neuron.join(Session, semantic_check=False)

Pattern 6: Universal set
OLD: all_dates = dj.U('session_date') * Session
NEW: all_dates = dj.U('session_date') & Session

REPORT:
- Files modified: [list]
- fetch() → to_arrays/to_dicts: [count]
- _update() → update1(): [count]
- @ → join(): [count]
- U() * → U() &: [count]
- Tests passed: [yes/no]

COMMIT MESSAGE FORMAT:
"feat(phase-i): convert query and insert code to 2.0 API

- Replace fetch() with to_arrays()/to_dicts()
- Replace _update() with update1()
- Replace @ operator with join()
- Replace dj.U() * with dj.U() &

API conversions: X fetch, Y update, Z join"
```

---

### Step 7: Convert Populate Methods

Update `make()` methods in Computed and Imported tables.

#### AI Agent Prompt: Convert Populate Methods

---

**🤖 AI Agent Prompt: Phase I - Populate Method Conversion**

```
You are converting populate/make methods in Computed and Imported tables.

TASK: Update make() methods to use 2.0 API patterns.

CONTEXT:
- Focus on dj.Computed and dj.Imported tables
- make() methods contain computation logic
- Often use fetch, insert, and query operations

CONVERSIONS NEEDED:
1. Apply all fetch API conversions from previous step
2. Apply all update conversions
3. Apply all join conversions
4. No changes to insert operations

COMMON PATTERNS IN make():

Pattern 1: Fetch dependency data
OLD:
def make(self, key):
    data = (DependencyTable & key).fetch(as_dict=True)

NEW:
def make(self, key):
    data = (DependencyTable & key).to_dicts()

Pattern 2: Fetch arrays for computation
OLD:
def make(self, key):
    signal = (Recording & key).fetch1('signal')

NEW:
def make(self, key):
    signal = (Recording & key).fetch1('signal')  # unchanged for single attr

Pattern 3: Fetch multiple attributes
OLD:
def make(self, key):
    signals, rates = (Recording & key).fetch('signal', 'sampling_rate')

NEW:
def make(self, key):
    signals, rates = (Recording & key).to_arrays('signal', 'sampling_rate')

Pattern 4: Join dependencies
OLD:
def make(self, key):
    data = (Neuron @ Session & key).fetch()

NEW:
def make(self, key):
    data = (Neuron.join(Session, semantic_check=False) & key).to_arrays()

PROCESS:
1. Find all dj.Computed and dj.Imported classes
2. For each class with make() method:
   a. Apply API conversions
   b. Verify logic unchanged
   c. Test if possible
3. Commit changes by module or table

VERIFICATION:
- All make() methods use 2.0 API
- Computation logic unchanged
- Insert logic unchanged
- No syntax errors

REPORT:
- Computed tables updated: [count]
- Imported tables updated: [count]
- make() methods converted: [count]

COMMIT MESSAGE FORMAT:
"feat(phase-i): convert populate methods to 2.0 API

- Update make() methods in Computed tables
- Update make() methods in Imported tables
- Apply fetch/join API conversions

Tables updated: X Computed, Y Imported"
```

---

### Step 8: Verify Phase I Complete

#### Checklist

- [ ] `pre/v2.0` branch created
- [ ] DataJoint 2.0 installed (`pip list | grep datajoint`)
- [ ] Configuration files created (`.secrets/`, `datajoint.json`)
- [ ] Stores configured (if using in-store codecs)
- [ ] All schema declarations use `_v2` suffix
- [ ] All table definitions use 2.0 type syntax
- [ ] All in-table codecs converted (`<blob>`, `<attach>`)
- [ ] All in-store codecs converted (`<blob@>`, `<npy@>`, `<filepath@>`)
- [ ] All `fetch()` calls converted (except `fetch1()`)
- [ ] All `._update()` calls converted
- [ ] All `@` operators converted
- [ ] All `dj.U() *` patterns converted
- [ ] All populate methods updated
- [ ] No syntax errors
- [ ] All `_v2` schemas created (empty)

#### Test Schema Creation

```python
# Run your main module to create all tables
import your_pipeline_v2

# Verify schemas exist
import datajoint as dj
conn = dj.conn()

schemas = conn.query("SHOW DATABASES LIKE '%_v2'").fetchall()
print(f"Created {len(schemas)} _v2 schemas:")
for schema in schemas:
    print(f"  - {schema[0]}")

# Verify tables created
for schema_name in [s[0] for s in schemas]:
    tables = conn.query(
        f"SELECT COUNT(*) FROM information_schema.TABLES "
        f"WHERE TABLE_SCHEMA='{schema_name}'"
    ).fetchone()[0]
    print(f"{schema_name}: {tables} tables")
```

#### Commit Phase I

```bash
# Review all changes
git status
git diff

# Commit
git add .
git commit -m "feat: complete Phase I migration to DataJoint 2.0

Summary:
- Created _v2 schemas (empty)
- Converted all table definitions to 2.0 syntax
- Converted all query/insert code to 2.0 API
- Converted all populate methods
- Configured test stores for in-store codecs
- Production data migration deferred to Phase III

Schemas: X
Tables: Y
Code files: Z"

git push origin pre/v2.0
```

✅ **Phase I Complete!**

**You now have:**
- 2.0-compatible code on `pre/v2.0` branch
- Empty `_v2` schemas ready for testing
- Production still running on `main` branch with 0.14.x

**Next:** Phase II - Test with sample data

---

## Phase II: Test Compatibility and Equivalence

**Goal:** Validate that the 2.0 pipeline produces equivalent results to the legacy pipeline.

**End state:**

- 2.0 pipeline runs correctly with sample data in `_v2` schemas and test stores
- Results are equivalent to running legacy pipeline on same data
- Confidence that migration is correct before touching production
- Production still untouched

**Key principle:** Test with identical data in both legacy and v2 schemas to verify equivalence.

### Step 1: Insert Test Data

```python
from your_pipeline_v2 import schema, Mouse, Session, Neuron

# Insert manual tables
Mouse.insert([
    {'mouse_id': 0, 'dob': '2024-01-01', 'sex': 'M'},
    {'mouse_id': 1, 'dob': '2024-01-15', 'sex': 'F'},
])

Session.insert([
    {'mouse_id': 0, 'session_date': '2024-06-01', 'experimenter': 'Alice'},
    {'mouse_id': 0, 'session_date': '2024-06-05', 'experimenter': 'Alice'},
    {'mouse_id': 1, 'session_date': '2024-06-03', 'experimenter': 'Bob'},
])

# Verify
print(f"Inserted {len(Mouse())} mice")
print(f"Inserted {len(Session())} sessions")
```

### Step 2: Test Populate

```python
# Populate imported/computed tables
Neuron.populate(display_progress=True)

# Verify
print(f"Generated {len(Neuron())} neurons")
```

### Step 3: Test Queries

```python
# Test basic queries
mice = Mouse.to_dicts()
print(f"Fetched {len(mice)} mice")

# Test joins
neurons_with_sessions = Neuron.join(Session, semantic_check=False)
print(f"Join result: {len(neurons_with_sessions)} rows")

# Test restrictions
alice_sessions = Session & 'experimenter="Alice"'
print(f"Alice's sessions: {len(alice_sessions)}")

# Test fetch variants
mouse_ids, dobs = Mouse.to_arrays('mouse_id', 'dob')
print(f"Arrays: {len(mouse_ids)} ids, {len(dobs)} dobs")
```

### Step 4: Test New Features (Optional)

If you converted any tables to use new codecs:

```python
# Test object storage (if using <npy@> or <object@>)
from your_pipeline_v2 import Recording

# Insert with object storage
Recording.insert1({
    'recording_id': 0,
    'signal': np.random.randn(1000, 64),  # Stored in object store
})

# Fetch with lazy loading
ref = (Recording & {'recording_id': 0}).fetch1('signal')
print(f"NpyRef: shape={ref.shape}, loaded={ref.is_loaded}")

# Load when needed
signal = ref.load()
print(f"Loaded: shape={signal.shape}")
```

### Step 5: Compare with Legacy Schema (Equivalence Testing)

**Critical:** Run identical data through both legacy and v2 pipelines to verify equivalence.

#### Option A: Side-by-Side Comparison

```python
# compare_legacy_v2.py
import datajoint as dj
import numpy as np

# Import both legacy and v2 modules
import your_pipeline as legacy  # 0.14.x on main branch (checkout to test)
import your_pipeline_v2 as v2  # 2.0 on pre/v2.0 branch

def compare_results():
    """Compare query results between legacy and v2."""

    # Insert same data into both schemas
    test_data = [
        {'mouse_id': 0, 'dob': '2024-01-01', 'sex': 'M'},
        {'mouse_id': 1, 'dob': '2024-01-15', 'sex': 'F'},
    ]

    legacy.Mouse.insert(test_data, skip_duplicates=True)
    v2.Mouse.insert(test_data, skip_duplicates=True)

    # Compare query results
    legacy_mice = legacy.Mouse.fetch(as_dict=True)  # 0.14.x syntax
    v2_mice = v2.Mouse.to_dicts()  # 2.0 syntax

    assert len(legacy_mice) == len(v2_mice), "Row count mismatch!"

    # Compare values (excluding fetch-specific artifacts)
    for leg, v2_row in zip(legacy_mice, v2_mice):
        for key in leg.keys():
            if leg[key] != v2_row[key]:
                print(f"MISMATCH: {key}: {leg[key]} != {v2_row[key]}")
                return False

    print("✓ Query results are equivalent!")
    return True

def compare_populate():
    """Compare populate results."""

    # Populate both
    legacy.Neuron.populate(display_progress=True)
    v2.Neuron.populate(display_progress=True)

    # Compare counts
    legacy_count = len(legacy.Neuron())
    v2_count = len(v2.Neuron())

    assert legacy_count == v2_count, f"Count mismatch: {legacy_count} != {v2_count}"

    print(f"✓ Populate generated same number of rows: {v2_count}")

    # Compare computed values (if numeric)
    for key in (legacy.Neuron & 'neuron_id=0').fetch1('KEY'):
        leg_val = (legacy.Neuron & key).fetch1('activity')
        v2_val = (v2.Neuron & key).fetch1('activity')

        if isinstance(leg_val, np.ndarray):
            assert np.allclose(leg_val, v2_val, rtol=1e-9), "Array values differ!"
        else:
            assert leg_val == v2_val, f"Value mismatch: {leg_val} != {v2_val}"

    print("✓ Populate results are equivalent!")
    return True

if __name__ == '__main__':
    print("Comparing legacy and v2 pipelines...")
    compare_results()
    compare_populate()
    print("\n✓ All equivalence tests passed!")
```

Run comparison:

```bash
python compare_legacy_v2.py
```

#### Option B: Data Copy and Validation

If you can't easily import both modules:

1. Copy sample data from production to both legacy test schema and `_v2` schema
2. Run populate on both
3. Use helper to compare:

```python
from datajoint.migrate import compare_query_results

# Compare table contents
result = compare_query_results(
    prod_schema='my_pipeline',
    test_schema='my_pipeline_v2',
    table='neuron',
    tolerance=1e-6,
)

if result['match']:
    print(f"✓ {result['row_count']} rows match")
else:
    print(f"✗ Discrepancies found:")
    for disc in result['discrepancies']:
        print(f"  {disc}")
```

### Step 6: Run Existing Tests

If you have a test suite:

```bash
# Run tests against _v2 schemas
pytest tests/ -v

# Or specific test modules
pytest tests/test_queries.py -v
pytest tests/test_populate.py -v
```

### Step 7: Validate Results

Create a validation script:

```python
# validate_v2.py
import datajoint as dj
from your_pipeline_v2 import schema

def validate_phase_ii():
    """Validate Phase II migration."""

    issues = []

    # Check schemas exist
    conn = dj.conn()
    schemas_v2 = conn.query("SHOW DATABASES LIKE '%_v2'").fetchall()

    if not schemas_v2:
        issues.append("No _v2 schemas found")
        return issues

    print(f"✓ Found {len(schemas_v2)} _v2 schemas")

    # Check tables populated
    for schema_name in [s[0] for s in schemas_v2]:
        tables = conn.query(
            f"SELECT TABLE_NAME FROM information_schema.TABLES "
            f"WHERE TABLE_SCHEMA='{schema_name}' AND TABLE_NAME NOT LIKE '~%'"
        ).fetchall()

        for table in tables:
            table_name = table[0]
            count = conn.query(
                f"SELECT COUNT(*) FROM `{schema_name}`.`{table_name}`"
            ).fetchone()[0]

            if count > 0:
                print(f"  ✓ {schema_name}.{table_name}: {count} rows")
            else:
                print(f"  ○ {schema_name}.{table_name}: empty (may be expected)")

    # Test basic operations
    try:
        # Test fetch
        data = schema.connection.query(
            f"SELECT * FROM {schema.database} LIMIT 1"
        ).fetchall()
        print("✓ Fetch operations work")
    except Exception as e:
        issues.append(f"Fetch error: {e}")

    return issues

if __name__ == '__main__':
    issues = validate_phase_ii()

    if issues:
        print("\n✗ Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Phase II validation passed!")
```

Run validation:

```bash
python validate_v2.py
```

### Step 7: Document Test Results

Create a test report:

```bash
# test_report.md
cat > test_report.md << 'EOF'
# Phase II Test Report

## Test Date
2025-01-14

## Summary
- Schemas tested: X
- Tables populated: Y
- Tests passed: Z

## Manual Tables
- Mouse: N rows
- Session: M rows

## Computed Tables
- Neuron: K rows
- Analysis: J rows

## Query Tests
- Basic fetch: ✓
- Joins: ✓
- Restrictions: ✓
- Aggregations: ✓

## Populate Tests
- Imported tables: ✓
- Computed tables: ✓
- Error handling: ✓

## New Features Tested
- Object storage: ✓
- Lazy loading: ✓

## Issues Found
- None

## Conclusion
Phase II completed successfully. Ready for Phase III.
EOF

git add test_report.md
git commit -m "docs: Phase II test report"
```

✅ **Phase II Complete!**

**You now have:**
- Validated 2.0 pipeline with sample data
- Confidence in code migration
- Test report documenting success
- Ready to migrate production data

**Next:** Phase III - Migrate production data

---

## Phase III: Migrate Production Data

**Goal:** Migrate production data and configure production stores. Code is complete from Phase I.

**End state:**

- Production data migrated to `_v2` schemas
- Production stores configured (replacing test stores)
- In-store metadata updated (UUID → JSON)
- Ready to switch production to 2.0

**Key principle:** All code changes were completed in Phase I. This phase is DATA migration only.

**Prerequisites:**

- Phase I complete (all code migrated)
- Phase II complete (equivalence validated)
- Production backup created
- Production workloads quiesced

**Options:**

- **Option A:** Copy data, rename schemas (recommended - safest)
- **Option B:** In-place migration (for very large databases)
- **Option C:** Gradual migration with legacy compatibility

Choose the option that best fits your needs.

### Option A: Copy Data and Rename Schemas (Recommended)

**Best for:** Most pipelines, especially < 1 TB

**Advantages:**

- Safe - production unchanged until final step
- Easy rollback
- Can practice multiple times

**Process:**

#### 0. Configure Production Stores

Update `datajoint.json` to point to production stores (not test stores):

```json
{
  "stores": {
    "default": "main",
    "main": {
      "protocol": "file",
      "location": "/data/production_stores/main"  # Production location
    }
  }
}
```

**For in-store data migration:** You can either:

- **Keep files in place** (recommended): Point to existing 0.14.x store locations
- **Copy to new location**: Configure new production stores and copy files

**Commit this change:**
```bash
git add datajoint.json
git commit -m "config: update stores to production locations"
```

#### 1. Backup Production

```bash
# Full backup
mysqldump --all-databases > backup_$(date +%Y%m%d).sql

# Or schema-specific
mysqldump my_pipeline > my_pipeline_backup_$(date +%Y%m%d).sql
```

#### 2. Copy Manual Table Data

```python
from datajoint.migrate import copy_table_data

# Copy each manual table
tables = ['mouse', 'session', 'experimenter']  # Your manual tables

for table in tables:
    result = copy_table_data(
        source_schema='my_pipeline',
        dest_schema='my_pipeline_v2',
        table=table,
    )
    print(f"{table}: copied {result['rows_copied']} rows")
```

#### 3. Populate Computed Tables

```python
from your_pipeline_v2 import Neuron, Analysis

# Populate using 2.0 code
Neuron.populate(display_progress=True)
Analysis.populate(display_progress=True)
```

#### 4. Migrate In-Store Metadata

**Important:** Your code already handles in-store codecs (converted in Phase I). This step just updates metadata format.

If you have tables using `<blob@>`, `<attach@>`, or `<filepath@>` codecs, migrate the storage metadata from legacy BINARY(16) UUID format to 2.0 JSON format:

```python
from datajoint.migrate import migrate_external_pointers_v2

# Update metadata format (UUID → JSON)
# This does NOT move files—just updates database pointers
result = migrate_external_pointers_v2(
    schema='my_pipeline_v2',
    table='recording',
    attribute='signal',
    source_store='external-raw',  # Legacy 0.14.x store name
    dest_store='raw',  # 2.0 store name (from datajoint.json)
    copy_files=False,  # Keep files in place (recommended)
)

print(f"Migrated {result['rows_migrated']} pointers")
```

**What this does:**

- Reads legacy BINARY(16) UUID pointers from `~external_*` hidden tables
- Creates new JSON metadata with file path, store name, hash
- Writes JSON to the `<blob@store>` column (code written in Phase I)
- Does NOT copy files (unless `copy_files=True`)

**Result:** Files stay in place, but 2.0 code can now access them via the new codec system.

#### 5. Validate Data Integrity

```python
from datajoint.migrate import compare_query_results

# Compare production vs _v2
tables_to_check = ['mouse', 'session', 'neuron', 'analysis']

all_match = True
for table in tables_to_check:
    result = compare_query_results(
        prod_schema='my_pipeline',
        test_schema='my_pipeline_v2',
        table=table,
        tolerance=1e-6,
    )

    if result['match']:
        print(f"✓ {table}: {result['row_count']} rows match")
    else:
        print(f"✗ {table}: discrepancies found")
        for disc in result['discrepancies'][:5]:
            print(f"    {disc}")
        all_match = False

if all_match:
    print("\n✓ All tables validated! Ready for cutover.")
else:
    print("\n✗ Fix discrepancies before proceeding.")
```

#### 6. Schedule Cutover

**Pre-cutover checklist:**
- [ ] Full backup verified
- [ ] All data copied
- [ ] All computed tables populated
- [ ] Validation passed
- [ ] Team notified
- [ ] Maintenance window scheduled
- [ ] All 0.14.x clients stopped

**Execute cutover:**

```sql
-- Rename production → old
RENAME TABLE `my_pipeline` TO `my_pipeline_old`;

-- Rename _v2 → production
RENAME TABLE `my_pipeline_v2` TO `my_pipeline`;
```

**Update code:**

```bash
# On pre/v2.0 branch, update schema names back
sed -i '' 's/_v2//g' your_pipeline/*.py

git add .
git commit -m "chore: remove _v2 suffix for production"

# Merge to main
git checkout main
git merge pre/v2.0
git push origin main

# Deploy updated code
```

#### 7. Verify Production

```python
# Test production after cutover
from your_pipeline import schema, Mouse, Neuron

print(f"Mice: {len(Mouse())}")
print(f"Neurons: {len(Neuron())}")

# Run a populate
Neuron.populate(limit=5, display_progress=True)
```

#### 8. Cleanup (After 1-2 Weeks)

```sql
-- After confirming production stable
DROP DATABASE `my_pipeline_old`;
```

### Option B: In-Place Migration

**Best for:** Very large databases (> 1 TB) where copying is impractical

**Warning:** Modifies production schema directly. Test thoroughly first!

```python
from datajoint.migrate import migrate_schema_in_place

# Backup first
backup_schema('my_pipeline', 'my_pipeline_backup_20250114')

# Migrate in place
result = migrate_schema_in_place(
    schema='my_pipeline',
    backup=True,
    steps=[
        'update_blob_comments',  # Add :<blob>: markers
        'add_lineage_table',  # Create ~lineage
        'migrate_external_storage',  # BINARY(16) → JSON
    ]
)

print(f"Migrated {result['steps_completed']} steps")
```

### Option C: Gradual Migration with Legacy Compatibility

**Best for:** Pipelines that must support both 0.14.x and 2.0 clients simultaneously

**Strategy:** Create dual columns for in-store codecs

#### 1. Add `_v2` Columns

For each in-store attribute, add a corresponding `_v2` column:

```sql
-- Add _v2 column for in-store codec
ALTER TABLE `my_pipeline`.`recording`
  ADD COLUMN `signal_v2` JSON COMMENT ':<blob@raw>:signal data';
```

#### 2. Populate `_v2` Columns

```python
from datajoint.migrate import populate_v2_columns

result = populate_v2_columns(
    schema='my_pipeline',
    table='recording',
    attribute='signal',
    v2_attribute='signal_v2',
    source_store='external-raw',
    dest_store='raw',
)

print(f"Populated {result['rows']} _v2 columns")
```

#### 3. Update Code to Use `_v2` Columns

```python
# Update table definition
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : blob@raw  # Legacy (0.14.x clients)
    signal_v2 : <blob@raw>  # 2.0 clients
    """
```

**Both APIs work:**
- 0.14.x clients use `signal`
- 2.0 clients use `signal_v2`

#### 4. Final Cutover

Once all clients upgraded to 2.0:

```sql
-- Drop legacy column
ALTER TABLE `my_pipeline`.`recording`
  DROP COLUMN `signal`;

-- Rename _v2 to original name
ALTER TABLE `my_pipeline`.`recording`
  CHANGE COLUMN `signal_v2` `signal` JSON;
```

---

## Phase IV: Adopt New Features

After successful migration, adopt DataJoint 2.0 features:

### 1. Object Storage with Lazy Loading

Replace `<blob>` with `<npy@>` for large arrays:

```python
# Before
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <blob>  # Stored in table
    """

# After
@schema
class Recording(dj.Manual):
    definition = """
    recording_id : uint32
    ---
    signal : <npy@>  # Lazy-loading from object store
    """

# Usage
ref = (Recording & key).fetch1('signal')
print(f"Shape: {ref.shape}, dtype: {ref.dtype}")  # No download!
signal = ref.load()  # Download when ready
```

**Learn more:** [Object Storage Tutorial](../tutorials/basics/06-object-storage.md) · [NPY Codec Spec](../reference/specs/npy-codec.md)

### 2. Partition Patterns

Organize object storage by experimental hierarchy:

```python
# Configure partitioning
dj.config['stores.main.partition_pattern'] = '{mouse_id}/{session_date}'

# Storage structure:
# {store}/mouse_id=0/session_date=2024-06-01/{schema}/{table}/file.npy
```

**Learn more:** [Object Store Configuration](../reference/specs/object-store-configuration.md)

### 3. Semantic Matching

Enable lineage-based join validation:

```python
# Validates lineage compatibility
result = Neuron.join(Session, semantic_check=True)

# Raises error if lineage incompatible
```

**Learn more:** [Semantic Matching Spec](../reference/specs/semantic-matching.md)

### 4. Custom Codecs

Create domain-specific types:

```python
from datajoint.codecs import Codec

class SpikeTrainCodec(Codec):
    """Custom codec for spike trains."""

    def encode(self, obj, context):
        # Compress spike times
        return compressed_data

    def decode(self, blob, context):
        # Decompress spike times
        return spike_times
```

**Learn more:** [Custom Codecs Tutorial](../tutorials/advanced/custom-codecs.ipynb) · [Codec API](../reference/specs/codec-api.md)

### 5. Jobs 2.0

Use per-table job management:

```python
# Monitor job progress
Analysis.jobs.progress()

# Priority-based populate
Analysis.populate(order='priority DESC')

# Job tables: ~~analysis
```

**Learn more:** [Distributed Computing](../tutorials/advanced/distributed.ipynb) · [AutoPopulate Spec](../reference/specs/autopopulate.md)

---

## Troubleshooting

### Import Errors

**Issue:** Module not found after migration

**Solution:**
```python
# Ensure all imports use datajoint namespace
import datajoint as dj
from datajoint import schema, Manual, Computed
```

### Schema Not Found

**Issue:** `Database 'schema_v2' doesn't exist`

**Solution:**
```python
# Ensure schema declared and created
schema = dj.schema('schema_v2')
schema.spawn_missing_classes()
```

### Type Syntax Errors

**Issue:** `Invalid type: 'int unsigned'`

**Solution:** Update to core types
```python
# Wrong
definition = """
id : int unsigned
"""

# Correct
definition = """
id : uint32
"""
```

### External Storage Not Found

**Issue:** Can't access external data after migration

**Solution:**
```python
# Ensure stores configured
dj.config['stores.default'] = 'main'
dj.config['stores.main.location'] = '/data/stores'

# Verify
from datajoint.settings import get_store_spec
print(get_store_spec('main'))
```

---

## Summary

**Phase I:** Branch and code migration (~1-4 hours with AI)
- Create `pre/v2.0` branch
- Update all code to 2.0 API
- Create empty `_v2` schemas

**Phase II:** Test with sample data (~1-2 days)
- Insert test data
- Validate functionality
- Test new features

**Phase III:** Migrate production data (~1-7 days)
- Choose migration option
- Copy or migrate data
- Validate integrity
- Execute cutover

**Phase IV:** Adopt new features (ongoing)
- Object storage
- Semantic matching
- Custom codecs
- Jobs 2.0

**Total timeline:** ~1-2 weeks for most pipelines

---

## See Also

**Core Documentation:**
- [Type System Concept](../explanation/type-system.md)
- [Configuration Reference](../reference/configuration.md)
- [Definition Syntax](../reference/definition-syntax.md)
- [Fetch API Reference](../reference/specs/fetch-api.md)

**Tutorials:**
- [Object Storage](../tutorials/basics/06-object-storage.md)
- [Custom Codecs](../tutorials/advanced/custom-codecs.ipynb)
- [Distributed Computing](../tutorials/advanced/distributed.ipynb)

**Specifications:**
- [Type System Spec](../reference/specs/type-system.md)
- [Codec API Spec](../reference/specs/codec-api.md)
- [Object Store Configuration](../reference/specs/object-store-configuration.md)
- [Semantic Matching](../reference/specs/semantic-matching.md)
