"""
ECG Signal Extractor

Extracts the ECG waveform signal from lead images.

Converts pixel-based trace to voltage-time data:
- Trace detection (find the ECG line)
- Baseline identification
- Signal digitization
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple
import cv2
from .grid_detector import GridCalibration


@dataclass
class ECGSignal:
    """Digitized ECG signal data"""
    lead_name: str
    time_ms: np.ndarray  # Time values in milliseconds
    voltage_mv: np.ndarray  # Voltage values in millivolts
    sample_rate_hz: float  # Effective sample rate
    duration_ms: float  # Total duration
    baseline_mv: float  # Baseline voltage level

    @property
    def num_samples(self) -> int:
        return len(self.time_ms)

    def get_segment(self, start_ms: float, end_ms: float) -> 'ECGSignal':
        """Extract a time segment of the signal"""
        mask = (self.time_ms >= start_ms) & (self.time_ms <= end_ms)
        return ECGSignal(
            lead_name=self.lead_name,
            time_ms=self.time_ms[mask],
            voltage_mv=self.voltage_mv[mask],
            sample_rate_hz=self.sample_rate_hz,
            duration_ms=end_ms - start_ms,
            baseline_mv=self.baseline_mv,
        )


class SignalExtractor:
    """
    Extracts ECG signal from lead image.

    Approach:
    1. Find the ECG trace (typically darkest continuous line)
    2. Identify baseline (isoelectric line)
    3. Convert pixel positions to voltage values
    4. Handle overlapping traces and noise
    """

    def __init__(
        self,
        trace_color: str = "dark",  # "dark" or "colored"
        interpolate: bool = True,
        sample_rate: float = 500.0,  # Target sample rate in Hz
    ):
        self.trace_color = trace_color
        self.interpolate = interpolate
        self.target_sample_rate = sample_rate

    def extract(
        self,
        lead_image: np.ndarray,
        calibration: GridCalibration,
        lead_name: str = "Unknown"
    ) -> ECGSignal:
        """
        Extract ECG signal from a single lead image.

        Args:
            lead_image: Grayscale image of a single lead
            calibration: Grid calibration for pixel-to-unit conversion
            lead_name: Name of the lead

        Returns:
            Digitized ECG signal
        """
        height, width = lead_image.shape[:2]

        # Detect the trace
        trace_y = self._detect_trace(lead_image)

        # Find baseline
        baseline_y = self._find_baseline(trace_y, height)

        # Convert to voltage-time
        time_ms, voltage_mv = self._convert_to_signal(
            trace_y, baseline_y, calibration, width
        )

        # Interpolate to uniform sample rate if needed
        if self.interpolate:
            time_ms, voltage_mv = self._interpolate_signal(
                time_ms, voltage_mv, self.target_sample_rate
            )

        duration_ms = time_ms[-1] - time_ms[0] if len(time_ms) > 0 else 0

        return ECGSignal(
            lead_name=lead_name,
            time_ms=time_ms,
            voltage_mv=voltage_mv,
            sample_rate_hz=self.target_sample_rate if self.interpolate else width / (duration_ms / 1000),
            duration_ms=duration_ms,
            baseline_mv=0.0,  # Baseline is normalized to 0
        )

    def _detect_trace(self, image: np.ndarray) -> np.ndarray:
        """
        Detect the ECG trace in the image.

        For each x-position, find the y-position of the trace.
        Returns array of y-values (one per column).
        """
        height, width = image.shape[:2]

        if self.trace_color == "dark":
            # Trace is the darkest pixels in each column
            # Invert so trace becomes white
            inverted = 255 - image
        else:
            inverted = image

        # Apply threshold to isolate trace
        _, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # For each column, find the trace position
        trace_y = np.zeros(width)

        for x in range(width):
            column = cleaned[:, x]
            nonzero = np.nonzero(column)[0]

            if len(nonzero) > 0:
                # Use center of mass of trace pixels
                trace_y[x] = np.mean(nonzero)
            else:
                # No trace detected, use previous value or center
                trace_y[x] = trace_y[x-1] if x > 0 else height / 2

        # Smooth the trace to reduce noise
        trace_y = self._smooth_trace(trace_y)

        return trace_y

    def _smooth_trace(self, trace_y: np.ndarray, window: int = 5) -> np.ndarray:
        """Apply smoothing to reduce noise in trace detection"""
        kernel = np.ones(window) / window
        smoothed = np.convolve(trace_y, kernel, mode='same')
        return smoothed

    def _find_baseline(self, trace_y: np.ndarray, image_height: int) -> float:
        """
        Find the isoelectric baseline.

        The baseline is typically the most common y-value (mode).
        """
        # Histogram of y-positions
        hist, bins = np.histogram(trace_y, bins=50)

        # Find the mode (most common value)
        mode_idx = np.argmax(hist)
        baseline = (bins[mode_idx] + bins[mode_idx + 1]) / 2

        return baseline

    def _convert_to_signal(
        self,
        trace_y: np.ndarray,
        baseline_y: float,
        calibration: GridCalibration,
        width: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert pixel trace to voltage-time signal.

        Args:
            trace_y: Y-position of trace at each x
            baseline_y: Y-position of baseline
            calibration: Grid calibration
            width: Image width

        Returns:
            (time_ms, voltage_mv) arrays
        """
        # Time: x-position to milliseconds
        time_ms = np.arange(width) * calibration.ms_per_pixel

        # Voltage: y-position relative to baseline, converted to mV
        # Note: In image coordinates, y increases downward
        # In ECG, positive deflection is upward
        voltage_pixels = baseline_y - trace_y  # Flip for correct polarity
        voltage_mv = voltage_pixels * calibration.mv_per_pixel

        return time_ms.astype(np.float64), voltage_mv.astype(np.float64)

    def _interpolate_signal(
        self,
        time_ms: np.ndarray,
        voltage_mv: np.ndarray,
        target_rate_hz: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Interpolate signal to uniform sample rate.
        """
        if len(time_ms) < 2:
            return time_ms, voltage_mv

        duration_ms = time_ms[-1] - time_ms[0]
        num_samples = int(duration_ms * target_rate_hz / 1000)

        new_time_ms = np.linspace(time_ms[0], time_ms[-1], num_samples)
        new_voltage_mv = np.interp(new_time_ms, time_ms, voltage_mv)

        return new_time_ms, new_voltage_mv

    def extract_multiple(
        self,
        lead_images: dict,  # {lead_name: image}
        calibration: GridCalibration
    ) -> dict:
        """
        Extract signals from multiple leads.

        Args:
            lead_images: Dictionary of lead name to lead image
            calibration: Grid calibration

        Returns:
            Dictionary of lead name to ECGSignal
        """
        signals = {}
        for name, image in lead_images.items():
            signals[name] = self.extract(image, calibration, name)
        return signals


class TraceEnhancer:
    """Enhance trace visibility before extraction"""

    @staticmethod
    def enhance_dark_trace(image: np.ndarray) -> np.ndarray:
        """Enhance dark trace on light background"""
        # Invert
        inverted = 255 - image

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(inverted)

        return enhanced

    @staticmethod
    def remove_grid(image: np.ndarray) -> np.ndarray:
        """
        Remove grid lines to isolate trace.

        Grid lines are typically lighter than the ECG trace.
        """
        # Threshold to keep only dark pixels (trace)
        _, binary = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)

        # Morphological operations to connect trace and remove grid
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned
