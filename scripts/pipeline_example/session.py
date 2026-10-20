"""The experimental record: sessions, scans, and what the scanner reported.

``Session`` depends on ``lab.Subject`` in its primary key and on ``lab.User`` as
a secondary reference — the two foreign keys that the module-level figure bundles
into the single ``lab → session`` edge.
"""

import datajoint as dj

from .lab import Subject, User
from .reference import ScannerModel

schema = dj.Schema("session")


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_date : date
    ---
    -> User
    session_notes : varchar(255)
    """


@schema
class Scan(dj.Manual):
    definition = """
    -> Session
    scan_idx : int32
    ---
    -> ScannerModel
    depth : float64
    """


@schema
class ScanInfo(dj.Imported):
    definition = """
    -> Scan
    ---
    nframes : int32
    fps : float64
    """
