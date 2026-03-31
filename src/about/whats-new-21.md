# What's New in DataJoint 2.1

DataJoint 2.1 adds **PostgreSQL as a production backend**, **enhanced diagram visualization**, and **singleton tables**.

> **Upgrading from 2.0?** No breaking changes. All existing code continues to work. New features are purely additive.

> **Citation:** Yatsenko D, Nguyen TT. *DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows.* arXiv:2602.16585. 2026. [doi:10.48550/arXiv.2602.16585](https://doi.org/10.48550/arXiv.2602.16585)

## PostgreSQL Backend

DataJoint now supports PostgreSQL 15+ as a production database backend alongside MySQL 8+. The adapter architecture generates backend-specific SQL while maintaining a consistent API — the same table definitions, queries, and pipeline logic work on both backends.

```bash
export DJ_BACKEND=postgresql
export DJ_HOST=localhost
export DJ_PORT=5432
```

Or configure programmatically:

```python
dj.config['database.backend'] = 'postgresql'
```

All core types (`int32`, `float64`, `varchar`, `uuid`, `json`), codec types (`<blob>`, `<attach>`, `<object@>`), query operations, foreign keys, indexes, and auto-populate work identically across backends. Backend-specific differences are handled internally by the adapter layer.

See [Database Backends](../reference/specs/database-backends.md) for the full specification.

## Diagram Enhancements

`dj.Diagram` gains several visualization features for working with complex, multi-schema pipelines.

### Layout Direction

Control the flow direction of diagrams:

```python
# Horizontal layout
dj.config.display.diagram_direction = "LR"

# Or temporarily
with dj.config.override(display__diagram_direction="LR"):
    dj.Diagram(schema).draw()
```

| Value | Description |
|-------|-------------|
| `"TB"` | Top to bottom (default) |
| `"LR"` | Left to right |

### Mermaid Output

Generate [Mermaid](https://mermaid.js.org/) syntax for embedding diagrams in Markdown, GitHub, or web documentation:

```python
print(dj.Diagram(schema).make_mermaid())
```

Save directly to `.mmd` or `.mermaid` files:

```python
dj.Diagram(schema).save("pipeline.mmd")
```

### Schema Grouping

Multi-schema diagrams automatically group tables into visual clusters by database schema. The cluster label shows the Python module name when available, following the DataJoint convention of one module per schema.

```python
combined = dj.Diagram(schema1) + dj.Diagram(schema2)
combined.draw()  # tables grouped by schema
```

### Collapsing Schemas

For high-level pipeline views, collapse entire schemas into single nodes:

```python
# Show schema1 expanded, schema2 as a single node with table count
dj.Diagram(schema1) + dj.Diagram(schema2).collapse()
```

The **"expanded wins" rule** applies: if a table appears in both a collapsed and non-collapsed diagram, it stays expanded. This allows showing specific tables while collapsing the rest:

```python
# Subject is expanded, rest of analysis schema is collapsed
dj.Diagram(Subject) + dj.Diagram(analysis).collapse()
```

See [Diagram Specification](../reference/specs/diagram.md) for the full reference.

## Singleton Tables

A **singleton table** holds at most one row. Declare it with no attributes in the primary key section:

```python
@schema
class Config(dj.Lookup):
    definition = """
    # Global configuration
    ---
    setting1 : varchar(100)
    setting2 : int32
    """
```

| Operation | Result |
|-----------|--------|
| Insert | Works without specifying a key |
| Second insert | Raises `DuplicateError` |
| `fetch1()` | Returns the single row |

Useful for global configuration, pipeline parameters, and summary statistics.

See [Table Declaration](../reference/specs/table-declaration.md#25-singleton-tables-empty-primary-keys) for details.

## See Also

- [Database Backends](../reference/specs/database-backends.md) — Full backend specification
- [Diagram Specification](../reference/specs/diagram.md) — Diagram reference
- [Table Declaration](../reference/specs/table-declaration.md) — Singleton tables
- [Configure Database](../how-to/configure-database.md) — Connection setup for both backends
- [What's New in 2.0](whats-new-2.md) — Previous release
- [What's New in 2.2](whats-new-22.md) — Next release
- [Release Notes (v2.1.0)](https://github.com/datajoint/datajoint-python/releases/tag/v2.1.0) — GitHub changelog
