# The Fan-Out Ingestion Pattern

Sometimes a single ingestion step reads one external source and produces rows in
several tables at once — for example, parsing one acquisition file into
`Subject`, `Session`, and `Recording` records. This is the **fan-out ingestion**
pattern. It is a deliberate, sanctioned exception to DataJoint's usual dependency
structure. This page explains what it steps outside of, and the responsibility it
carries in return.

## The shape

An ingestion routine — typically an `Imported` table's `make()`, or a manual
loader — reads one source and inserts into several **entry-point tables**
(`Manual` or `Imported`) that are *not* foreign-key children of the ingesting
table:

```python
@schema
class RecordingFile(dj.Manual):        # the source record
    definition = """
    file_id : uuid
    ---
    path    : varchar(255)
    """

@schema
class Ingest(dj.Imported):
    definition = """
    -> RecordingFile
    """
    def make(self, key):
        meta = parse(RecordingFile & key)
        # fan out into several entry-point tables that have no FK back to Ingest
        Subject.insert1({**meta.subject, "source_file": key["file_id"]})
        Session.insert1({**meta.session, "source_file": key["file_id"]})
        Recording.insert1({**meta.recording, "source_file": key["file_id"]})
        self.insert1(key)
```

## It steps outside direct referential integrity — explicitly

Normally every derived row is a foreign-key child of the rows it came from, so
the [dependency graph itself is the record](comparison-to-provenance-systems.md)
of what produced what. In fan-out ingestion, the tables the routine populates
carry **no foreign key back to the ingesting table**. The link from a `Subject`
row to the file it was parsed from is therefore *not* established in the schema
graph — direct referential integrity to the source is deliberately not created.

This is done on purpose, and being explicit is what makes it acceptable. Binding
these entry-point tables by foreign key to a fast-moving ingestion step would
marry the stable domain model to changeable infrastructure — every change to how
data is loaded would become a schema migration, and every row would permanently
carry whichever loader existed when it was created. The pattern avoids that by
*declining* the FK on purpose, rather than letting an undeclared dependency slip
in unnoticed.

## The responsibility it carries: record where the data came from

Because the foreign-key link to the source is absent, the traceability it would
have provided must be supplied another way. **Each table the pattern populates is
responsible for recording its own origin** — the source identity the row was
derived from (file path, checksum, instrument session, operator, timestamp,
external record id). This is the same responsibility every `Manual` and
`Imported` entry-point table already carries: data entering the pipeline from
outside must record where it came from, because the pipeline's own structure
cannot vouch for it.

Recording that origin at the point of entry is all DataJoint asks. Formalizing
and standardizing it beyond that — retention, audit trails, cross-system
exchange — is left to the provenance and governance systems a pipeline
interoperates with; see [Comparison to Provenance Systems](comparison-to-provenance-systems.md).

## When to use it

- **Use fan-out** when one source legitimately populates several independent
  entity tables, and making those tables foreign-key children of the loader would
  distort the domain model or turn every ingestion change into a schema migration.
- **Prefer ordinary foreign-key dependencies** when the produced rows are genuine
  derived results *within* the pipeline — there the structural link is exactly
  what you want, and fan-out would throw away traceability you could have kept.

Reserve fan-out for the ingestion boundary, where the pipeline meets the outside
world; keep everything downstream of that boundary bound by foreign keys.

## See also

- [Computation Model](computation-model.md) — the `make()` contract and `populate()`
- [Comparison to Provenance Systems](comparison-to-provenance-systems.md) — the external-origin concern DataJoint leaves to provenance systems
- [Entity Integrity](entity-integrity.md) — the referential-integrity guarantees fan-out deliberately steps outside
