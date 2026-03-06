"""
processing.py - Data processing tables

This module defines computed tables that process raw acquisition data.
Tables are declared but schema must be activated before use.
"""
import datajoint as dj
from . import acquisition

# Create schema without activating - caller must activate before use
schema = dj.Schema()


@schema
class ProcessingParams(dj.Lookup):
    definition = """
    params_id : int16
    ---
    filter_cutoff : float32
    threshold : float32
    """
    contents = [(1, 30.0, 2.5), (2, 50.0, 3.0)]


@schema
class ProcessedSession(dj.Computed):
    definition = """
    -> acquisition.Session
    -> ProcessingParams
    ---
    n_events : int32
    quality_score : float32
    """

    def make(self, key):
        self.insert1({**key, 'n_events': 100, 'quality_score': 0.95})


@schema
class EventDetection(dj.Computed):
    definition = """
    -> ProcessedSession
    event_id : int32
    ---
    event_time : float32
    amplitude : float32
    """

    def make(self, key):
        pass
