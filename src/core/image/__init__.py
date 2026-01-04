"""
ECG Image Processing Module

Converts ECG images (photos, scans, PDFs) into measurements that algorithms can use.

Pipeline:
1. Preprocessing - Enhance image quality, correct skew
2. Grid Detection - Find grid lines, determine calibration (mm/mV, mm/s)
3. Lead Detection - Identify and isolate 12 leads
4. Signal Extraction - Convert pixel traces to voltage-time data
5. Waveform Detection - Find P, QRS, T waves
6. Measurement - Calculate intervals, axis, rate
"""

from .preprocessor import ECGPreprocessor
from .grid_detector import GridDetector, GridCalibration
from .lead_detector import LeadDetector, DetectedLead
from .signal_extractor import SignalExtractor, ECGSignal
from .waveform_detector import WaveformDetector, WaveformAnnotations
from .measurement_extractor import MeasurementExtractor, ECGMeasurements
from .pipeline import ECGImagePipeline, quick_analyze

__all__ = [
    "ECGPreprocessor",
    "GridDetector",
    "GridCalibration",
    "LeadDetector",
    "DetectedLead",
    "SignalExtractor",
    "ECGSignal",
    "WaveformDetector",
    "WaveformAnnotations",
    "MeasurementExtractor",
    "ECGMeasurements",
    "ECGImagePipeline",
    "quick_analyze",
]
