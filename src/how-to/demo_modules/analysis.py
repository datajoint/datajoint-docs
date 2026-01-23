"""
analysis.py - Analysis tables

This module defines analysis tables that aggregate results across sessions.
"""
import datajoint as dj
from . import acquisition, processing

schema = dj.Schema('demo_analysis')


@schema
class AnalysisParams(dj.Lookup):
    definition = """
    analysis_id : int
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
    result : float
    confidence : float
    """

    def make(self, key):
        self.insert1({**key, 'result': 0.8, 'confidence': 0.95})


@schema
class CrossSessionAnalysis(dj.Computed):
    definition = """
    -> acquisition.Subject
    -> processing.ProcessingParams
    ---
    aggregate_score : float
    """

    def make(self, key):
        self.insert1({**key, 'aggregate_score': 0.9})
