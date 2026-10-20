"""Fan-out ingestion, and the origin DataJoint records for it.

One ``make()`` parses a single source file into several entry-point tables that
carry no foreign key back to it.  The dependency graph cannot record those
writes -- that is what makes the pattern a deliberate exception -- so the
question "where did this Subject row come from" has nothing structural to
answer it.

Since 2.3.4 the framework answers it anyway.  Every row written into a Manual
table carries a hidden ``_prov`` attribute, and a row written from inside an
ingesting ``make()`` records the ingesting table and key: exactly the link the
absent foreign key would have carried.  Nothing below asks for that, and nothing
can forge it.

Run with a configured source, the way a deployment would set it::

    DJ_PROVENANCE_SOURCE='{"system": "AcquisitionShare", "root": "/mnt/raw"}' \
        python examples/fan_out_provenance.py
"""

import datajoint as dj

schema = dj.Schema("fan_out_provenance_demo")


@schema
class RecordingFile(dj.Manual):
    """The source record: one row per file the pipeline has been told about."""

    definition = """
    file_id : int32
    ---
    path    : varchar(255)
    """


@schema
class Subject(dj.Manual):
    definition = """
    subject_id  : int32
    ---
    species     : varchar(64)
    source_file : int32       # the RecordingFile this row was parsed from
    """


@schema
class Session(dj.Manual):
    definition = """
    session_id   : int32
    ---
    session_date : date
    source_file  : int32      # the RecordingFile this row was parsed from
    """


@schema
class Ingest(dj.Imported):
    """Parses one file into several entry-point tables that do not depend on it."""

    definition = """
    -> RecordingFile
    ---
    n_entities : int32
    """

    def make(self, key):
        meta = parse(key["file_id"])

        # The fan-out.  Subject and Session have no foreign key back to Ingest,
        # so dj.Diagram renders them as unconnected nodes.  `source_file` is the
        # link the pipeline itself queries; `_prov` is the audit record, written
        # by the framework with this table and key in it.
        Subject.insert1({**meta["subject"], "source_file": key["file_id"]})
        Session.insert1({**meta["session"], "source_file": key["file_id"]})

        self.insert1({**key, "n_entities": 2})


def parse(file_id):
    """Stand-in for a real parser."""
    return {
        "subject": {"subject_id": 100 + file_id, "species": "mouse"},
        "session": {"session_id": 200 + file_id, "session_date": "2026-09-30"},
    }


if __name__ == "__main__":
    RecordingFile.insert1({"file_id": 1, "path": "/mnt/raw/session-001.nwb"})
    Ingest.populate()

    # The hidden attribute is excluded from the heading, so read it explicitly.
    for row in (Subject & "subject_id = 101").proj("_prov").to_dicts():
        print(row["_prov"])
        # {'time': '2026-09-30T14:22:05.481203+00:00',
        #  'agent': {'user': ..., 'host': ..., 'database_name': ...},
        #  'source': {'system': 'AcquisitionShare', 'root': '/mnt/raw'},
        #  'context': {'table': '`fan_out_provenance_demo`.`_ingest`',
        #              'key': {'file_id': 1}}}

    # The audit question the pattern used to leave unanswerable.
    print("rows with no recorded origin:", len(Subject & "_prov IS NULL"))

    schema.drop()
