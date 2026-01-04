"""
ECG Guru - Core Engine

This module contains the core ECG analysis engine including:
- Image processing: preprocessing, lead detection, signal extraction
- Waveform detection: P, QRS, T wave identification
- Measurement extraction: intervals, axis, ST segments
- Clinical algorithms: VT/SVT, pathway localization, STEMI
"""

__version__ = "0.1.0"

from . import algorithms
from . import image

# Convenience imports
from .image import ECGImagePipeline, ECGMeasurements, quick_analyze

__all__ = [
    "algorithms",
    "image",
    "ECGImagePipeline",
    "ECGMeasurements",
    "quick_analyze",
]
