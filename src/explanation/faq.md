# Frequently Asked Questions

## Why Does DataJoint Have Its Own Definition and Query Language?

DataJoint provides a custom data definition language and [query algebra](query-algebra.md) rather than using raw SQL or Object-Relational Mapping (ORM) patterns. This design reflects DataJoint's purpose: enabling research teams to build **[relational workflows](relational-workflow-model.md) with embedded computations** with maximum clarity.

### The Definition Language

DataJoint's [definition language](../reference/specs/table-declaration.md) is a standalone scripting language for declaring table schemas — not Python syntax embedded in strings. It is designed for uniform support across multiple host languages (Python, MATLAB, and potentially others). The same definition works identically regardless of which language you use.

### Composite Primary Keys: A Clarity Comparison

Scientific workflows frequently use composite primary keys built from foreign keys. Compare how different approaches handle this common pattern:

```python
# DataJoint - two characters declare dependency, foreign key, and inherit primary key
class Scan(dj.Manual):
    definition = """
    -> Session
    scan_idx : int16
    ---
    depth : float32
    """
```

```python
# SQLAlchemy - verbose, scattered, error-prone
class Scan(Base):
    subject_id = Column(Integer, primary_key=True)
    session_date = Column(Date, primary_key=True)
    scan_idx = Column(SmallInteger, primary_key=True)
    depth = Column(Float)
    __table_args__ = (
        ForeignKeyConstraint(
            ['subject_id', 'session_date'],
            ['session.subject_id', 'session.session_date']
        ),
    )
```

```sql
-- Raw SQL - maximum verbosity
CREATE TABLE scan (
    subject_id INT NOT NULL,
    session_date DATE NOT NULL,
    scan_idx SMALLINT NOT NULL,
    depth FLOAT,
    PRIMARY KEY (subject_id, session_date, scan_idx),
    FOREIGN KEY (subject_id, session_date)
        REFERENCES session(subject_id, session_date)
);
```

The `-> Session` syntax in DataJoint:
- Inherits all primary key attributes from Session
- Declares the foreign key constraint
- Establishes the computational dependency (for `populate()`)
- Documents the data lineage

All in two characters. As pipelines grow to dozens of tables with deep dependency chains, this clarity compounds.

### Why Multiline Strings?

| Aspect | Benefit |
|--------|---------|
| **Readable** | Looks like a specification: `---` separates primary from secondary attributes, `#` for comments |
| **Concise** | `mouse_id : int32` vs `mouse_id = Column(Integer, primary_key=True)` |
| **Database-first** | `table.describe()` shows the same format; virtual schemas reconstruct definitions from database metadata |
| **Language-agnostic** | Same syntax for Python, MATLAB, future implementations |
| **Separation of concerns** | Definition string = structure (what); class = behavior (how: `make()` methods) |

The definition string **is** the specification — a declarative language that describes entities and their relationships, independent of any host language's syntax.

### Why Custom Query Algebra?

DataJoint's operators implement **[semantic matching](../reference/specs/semantic-matching.md)** — joins and restrictions match only on attributes connected through the foreign key graph, not arbitrary columns that happen to share a name. This prevents:
- Accidental Cartesian products
- Joins on unrelated columns
- Silent incorrect results

Every query result has a defined **[entity type](entity-integrity.md)** with a specific [primary key](../reference/specs/primary-keys.md) (algebraic closure). SQL results are untyped bags of rows; DataJoint results are entity sets you can continue to query and compose.

### Object-Augmented Schemas

Object-Relational Mappers treat large objects as opaque binary blobs or leave file management to the application. DataJoint's object store **extends the relational schema** (see [Type System](type-system.md)):

- Relational semantics apply: referential integrity, cascading deletes, query filtering
- Multiple access patterns: lazy `ObjectRef`, streaming via fsspec, explicit download
- Two addressing modes: path-addressed (by primary key) and hash-addressed (deduplicated)

The object store is part of the relational model — queryable and integrity-protected like any other attribute.

### Summary

| Aspect | Raw SQL | Object-Relational Mappers | DataJoint |
|--------|---------|---------------------------|-----------|
| Schema definition | SQL Data Definition Language | Host language classes | Standalone definition language |
| Composite foreign keys | Verbose, repetitive | Verbose, scattered | `-> TableName` |
| Query model | SQL strings | Object navigation | Relational algebra operators |
| Dependencies | Implicit in application | Implicit in application | Explicit in schema |
| Large objects | Binary blobs / manual | Binary blobs / manual | Object-Augmented Schema |
| Computation | External to database | External to database | First-class ([Computed tables](computation-model.md)) |
| Target audience | Database administrators | Web developers | Research teams |

---

## Is DataJoint an ORM?

**Object-Relational Mapping (ORM)** is a technique for interacting with relational databases through object-oriented programming, abstracting direct SQL queries. Popular Python ORMs include SQLAlchemy, Django ORM, and Peewee, often used in web development.

DataJoint shares certain ORM characteristics—tables are defined as Python classes, and queries return Python objects. However, DataJoint is fundamentally a **computational database framework** designed for scientific workflows:

| Aspect | Traditional ORMs | DataJoint |
|--------|-----------------|-----------|
| Primary use case | Web applications | Scientific data pipelines |
| Focus | Simplify database CRUD | Data integrity + computation |
| Dependencies | Implicit (application logic) | Explicit (foreign keys define data flow) |
| Computation | External to database | First-class citizen in schema |
| Query model | Object navigation | Relational algebra |

DataJoint can be considered an **ORM specialized for scientific databases**—purpose-built for structured experimental data and computational workflows where reproducibility and [data integrity](entity-integrity.md) are paramount.

## Is DataJoint a Workflow Management System?

Not exactly. DataJoint and workflow management systems (Airflow, Prefect, Flyte, Nextflow, Snakemake) solve related but distinct problems:

| Aspect | Workflow Managers | DataJoint |
|--------|-------------------|-----------|
| Core abstraction | Tasks and DAGs | Tables and dependencies |
| State management | External (files, databases) | Integrated (relational database) |
| Scheduling | Built-in schedulers | External (or manual `populate()`) |
| Distributed execution | Built-in | Via external tools |
| Data model | Unstructured (files, blobs) | Structured (relational schema) |
| Query capability | Limited | Full relational algebra |

**DataJoint excels at:**
- Defining *what* needs to be computed based on data dependencies
- Ensuring computations are never duplicated
- Maintaining referential integrity across pipeline stages
- Querying intermediate and final results

**Workflow managers excel at:**
- Scheduling and orchestrating job execution
- Distributing work across clusters
- Retry logic and failure handling
- Resource management

**They complement each other.** DataJoint formalizes data dependencies so that external schedulers can effectively manage computational tasks. A common pattern:

1. DataJoint defines the pipeline structure and tracks what's computed
2. A workflow manager (or simple cron/SLURM scripts) calls [`populate()`](computation-model.md) on a schedule
3. DataJoint determines what work remains and executes it

## Is DataJoint a Lakehouse?

DataJoint and lakehouses share goals—integrating structured data management with scalable storage and computation. However, they differ in approach:

| Aspect | Lakehouse | DataJoint |
|--------|-----------|-----------|
| Data model | Flexible (structured + semi-structured) | Strict relational schema |
| Schema enforcement | Schema-on-read optional | Schema-on-write enforced |
| Primary use | Analytics on diverse data | Scientific workflows |
| Computation model | SQL/Spark queries | Declarative `make()` methods |
| Dependency tracking | Limited | Explicit via foreign keys |

A **lakehouse** merges data lake flexibility with data warehouse structure, optimized for analytics workloads.

**DataJoint** prioritizes:
- Rigorous schema definitions
- Explicit computational dependencies
- Data integrity and reproducibility
- Traceability within structured scientific datasets

DataJoint can complement lakehouse architectures—using object storage for large files while maintaining relational structure for metadata and provenance.

## Does DataJoint Require SQL Knowledge?

No. DataJoint provides a Python API that abstracts SQL:

| SQL | DataJoint |
|-----|-----------|
| `CREATE TABLE` | Define tables as Python classes |
| `INSERT INTO` | `.insert()` method |
| `SELECT * FROM` | `.to_arrays()`, `.to_dicts()`, `.to_pandas()` |
| `JOIN` | `table1 * table2` |
| `WHERE` | `table & condition` |
| `GROUP BY` | `.aggr()` |

Understanding relational concepts ([primary keys](entity-integrity.md), foreign keys, [normalization](normalization.md)) is helpful but not required to start. The [tutorials](../tutorials/index.md) teach these concepts progressively.

Since DataJoint uses standard database backends (MySQL, PostgreSQL), data remains accessible via SQL for users who prefer it or need integration with other tools.

## How Does DataJoint Handle Large Files?

DataJoint uses a hybrid storage model called **Object-Augmented Schemas (OAS)**:

- **Relational database**: Stores metadata, parameters, and relationships
- **Object storage**: Stores large files (images, recordings, arrays)

The database maintains references to external objects, preserving:
- Referential integrity (files deleted with their parent records)
- Query capability (filter by metadata, join across tables)
- Deduplication (identical content stored once)

See [Object Storage](../how-to/use-object-storage.md) for details.

## Can Multiple Users Share a Pipeline?

Yes. DataJoint pipelines are inherently collaborative:

- **Shared database**: All users connect to the same MySQL/PostgreSQL instance
- **Shared schema**: Table definitions are stored in the database
- **Concurrent access**: ACID transactions prevent conflicts
- **Job reservation**: `populate()` coordinates work across processes

Teams typically:
1. Share pipeline code via Git
2. Connect to a shared database server
3. Run `populate()` from multiple machines simultaneously

See [Distributed Computing](../how-to/distributed-computing.md) for multi-process patterns.
