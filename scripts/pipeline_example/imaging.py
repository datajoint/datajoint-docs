"""Computed results, including two master-part pairs.

``ScanQuality`` depends on ``session.Scan`` and ``MotionCorrection`` on
``session.ScanInfo`` — the two foreign keys bundled into the ``session → imaging``
edge at the module level.
"""

import datajoint as dj

from .reference import SegmentationMethod
from .session import Scan, ScanInfo

schema = dj.Schema("imaging")


@schema
class ScanQuality(dj.Computed):
    definition = """
    -> Scan
    ---
    quality_score : float64
    """


@schema
class MotionCorrection(dj.Computed):
    definition = """
    -> ScanInfo
    ---
    x_shifts : bytes
    y_shifts : bytes
    """


@schema
class Segmentation(dj.Computed):
    definition = """
    -> MotionCorrection
    -> SegmentationMethod
    ---
    num_rois : int32
    """

    class Roi(dj.Part):
        definition = """
        -> master
        roi_idx : int32
        ---
        mask : bytes
        """


@schema
class Fluorescence(dj.Computed):
    definition = """
    -> Segmentation
    ---
    timestamps : bytes
    """

    class Trace(dj.Part):
        definition = """
        -> master
        -> Segmentation.Roi
        ---
        trace : bytes
        """
