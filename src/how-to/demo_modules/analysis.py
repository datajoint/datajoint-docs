"""
analysis.py - Analysis tables

This module defines analysis tables that aggregate results across sessions.
Tables are declared but schema must be activated before use.
"""
import datajoint as dj
from . import acquisition, processing

# Create schema without activating - caller must activate before use
schema = dj.Schema()


@schema
class AnalysisParams(dj.Lookup):
    definition = """
    analysis_id : int16
    ---
    method : varchar(50)
    """
    contents = [(1, 'correlation'), (2, 'regression')]


@schema
class SubjectAnalysis(dj.Computed):
    definition = """
    -> acquisition.Subject
    -> AnalysisParams
    ---
    result : float32
    confidence : float32
    """

    def make(self, key):
        self.insert1({**key, 'result': 0.8, 'confidence': 0.95})


@schema
class CrossSessionAnalysis(dj.Computed):
    definition = """
    -> acquisition.Subject
    -> processing.ProcessingParams
    ---
    aggregate_score : float32
    """

    def make(self, key):
        self.insert1({**key, 'aggregate_score': 0.9})
