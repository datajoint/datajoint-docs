"""
processing.py - Data processing tables

This module defines computed tables that process raw acquisition data.
"""
import datajoint as dj
from . import acquisition

schema = dj.Schema('demo_processing')


@schema
class ProcessingParams(dj.Lookup):
    definition = """
    params_id : int
    ---
    filter_cutoff : float
    threshold : float
    """
    contents = [(1, 30.0, 2.5), (2, 50.0, 3.0)]


@schema
class ProcessedSession(dj.Computed):
    definition = """
    -> acquisition.Session
    -> ProcessingParams
    ---
    n_events : int
    quality_score : float
    """

    def make(self, key):
        self.insert1({**key, 'n_events': 100, 'quality_score': 0.95})


@schema
class EventDetection(dj.Computed):
    definition = """
    -> ProcessedSession
    event_id : int
    ---
    event_time : float
    amplitude : float
    """

    def make(self, key):
        pass
