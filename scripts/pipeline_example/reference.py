"""Lookup tables: the shared vocabulary the rest of the pipeline refers to."""

import datajoint as dj

schema = dj.Schema("reference")


@schema
class ScannerModel(dj.Lookup):
    definition = """
    scanner_model : varchar(32)
    ---
    manufacturer : varchar(64)
    """


@schema
class SegmentationMethod(dj.Lookup):
    definition = """
    seg_method : varchar(32)
    ---
    method_notes : varchar(255)
    """
