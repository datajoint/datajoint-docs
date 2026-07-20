# Update Data

DataJoint treats stored records as immutable artifacts of a workflow: the normal
way to change data is to **delete and reinsert**, not to update in place. Updates
exist only as a **surgical correction** for a mistake in already-entered data —
rare and deliberate, never part of a routine workflow.

!!! note "If you update often, look at the schema"
    A well-normalized workflow schema rarely needs updates. Frequent updates
    usually mean a table mixes data created at different workflow steps — see
    [Normalization](../explanation/normalization.md).

## Prefer delete + reinsert

To replace a Manual entity's data, delete the row and insert the corrected one.
Because foreign keys cascade, this keeps every dependent record consistent:

```python
(Subject & "subject_id=1001").delete()
Subject.insert1({"subject_id": 1001, "species": "mouse", "date_of_birth": "2026-01-15"})
```

For a **computed** result, never edit it in place — delete it and recompute so
the value stays traceable to its declared inputs:

```python
(Segmentation & key).delete()   # cascades to anything downstream
Segmentation.populate(key)      # recompute from the upstream cone
```

## Surgical corrections with `update1()`

When you must correct a **secondary** attribute of a single existing row without
disturbing its dependents, use `update1()`. It rewrites exactly one row,
identified by its full primary key:

```python
# Fix a mistyped genotype on one subject
Subject.update1({"subject_id": 1001, "genotype": "wild-type"})
```

`update1()` is deliberately narrow:

- It changes **one row**; the primary key in the argument must match an existing row.
- It **cannot change primary-key attributes** — keys are immutable. To re-key an
  entity, delete and reinsert (see [Design Primary Keys](design-primary-keys.md)).
- It does **not** re-run downstream computations. If a corrected value feeds
  computed tables, delete and recompute those instead.

## What you cannot change

- **Primary keys** — immutable after insertion; delete and reinsert.
- **Computed / Imported results** — produced by `make()`; delete and recompute
  rather than update. See
  [Insert Data → What Not to Insert](insert-data.md#what-not-to-insert).

## See also

- [Insert Data](insert-data.md) — adding rows
- [Delete Data](delete-data.md) — removing rows (cascades to dependents)
- [Run Computations](run-computations.md) — recomputing after a change
- [Normalization](../explanation/normalization.md) — why updates are rare in a workflow schema
