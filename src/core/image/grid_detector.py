"""
ECG Grid Detector

Detects the ECG paper grid for calibration:
- Standard ECG paper: 1mm small squares, 5mm large squares
- 25 mm/s paper speed (1 small square = 0.04s = 40ms)
- 10 mm/mV amplitude (1 small square = 0.1mV)

Grid detection enables accurate measurement of intervals and amplitudes.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, List
import cv2


@dataclass
class GridCalibration:
    """ECG grid calibration parameters"""
    pixels_per_mm: float  # Pixels per millimeter
    pixels_per_small_square: float  # Pixels per 1mm square
    pixels_per_large_square: float  # Pixels per 5mm square

    # Time calibration (horizontal)
    paper_speed_mm_per_s: float = 25.0  # Standard: 25 mm/s
    ms_per_pixel: float = 0.0  # Milliseconds per pixel

    # Amplitude calibration (vertical)
    amplitude_mm_per_mv: float = 10.0  # Standard: 10 mm/mV
    mv_per_pixel: float = 0.0  # Millivolts per pixel

    # Detection confidence
    confidence: float = 0.0
    grid_detected: bool = False

    def __post_init__(self):
        """Calculate derived values"""
        if self.pixels_per_mm > 0:
            # Time: 25 mm/s means 1mm = 40ms
            self.ms_per_pixel = (1.0 / self.pixels_per_mm) * (1000.0 / self.paper_speed_mm_per_s)
            # Amplitude: 10mm/mV means 1mm = 0.1mV
            self.mv_per_pixel = (1.0 / self.pixels_per_mm) / self.amplitude_mm_per_mv

    def pixels_to_ms(self, pixels: float) -> float:
        """Convert horizontal pixels to milliseconds"""
        return pixels * self.ms_per_pixel

    def pixels_to_mv(self, pixels: float) -> float:
        """Convert vertical pixels to millivolts"""
        return pixels * self.mv_per_pixel

    def mm_to_pixels(self, mm: float) -> float:
        """Convert millimeters to pixels"""
        return mm * self.pixels_per_mm


class GridDetector:
    """
    Detects ECG grid pattern for calibration.

    Approach:
    1. Find grid lines using edge detection
    2. Analyze line spacing to find 1mm and 5mm squares
    3. Calculate calibration parameters
    """

    def __init__(
        self,
        expected_paper_speed: float = 25.0,  # mm/s
        expected_amplitude: float = 10.0,  # mm/mV
    ):
        self.expected_paper_speed = expected_paper_speed
        self.expected_amplitude = expected_amplitude

    def detect(self, image: np.ndarray) -> GridCalibration:
        """
        Detect grid and calculate calibration.

        Args:
            image: Preprocessed grayscale ECG image

        Returns:
            GridCalibration with calibration parameters
        """
        # Detect horizontal and vertical lines
        h_spacing = self._detect_line_spacing(image, "horizontal")
        v_spacing = self._detect_line_spacing(image, "vertical")

        # Use the more reliable measurement
        if h_spacing is not None and v_spacing is not None:
            # Average both directions
            small_square_px = (h_spacing + v_spacing) / 2
            confidence = 0.9
        elif h_spacing is not None:
            small_square_px = h_spacing
            confidence = 0.7
        elif v_spacing is not None:
            small_square_px = v_spacing
            confidence = 0.7
        else:
            # Fallback: estimate from image DPI assumption
            small_square_px = self._estimate_from_image_size(image)
            confidence = 0.3

        # Calculate calibration
        pixels_per_mm = small_square_px  # 1 small square = 1mm
        pixels_per_large_square = small_square_px * 5

        calibration = GridCalibration(
            pixels_per_mm=pixels_per_mm,
            pixels_per_small_square=small_square_px,
            pixels_per_large_square=pixels_per_large_square,
            paper_speed_mm_per_s=self.expected_paper_speed,
            amplitude_mm_per_mv=self.expected_amplitude,
            confidence=confidence,
            grid_detected=confidence > 0.5,
        )

        return calibration

    def _detect_line_spacing(
        self,
        image: np.ndarray,
        direction: str
    ) -> Optional[float]:
        """
        Detect grid line spacing in given direction.

        Args:
            image: Grayscale image
            direction: "horizontal" or "vertical"

        Returns:
            Average spacing in pixels, or None if not detected
        """
        # Enhance grid lines
        # Grid lines are typically the lightest (or specific color)
        _, binary = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)

        # Create line detection kernel
        if direction == "horizontal":
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        # Morphological operations to isolate lines
        lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Project to 1D (sum along perpendicular axis)
        if direction == "horizontal":
            projection = np.sum(lines, axis=1)
        else:
            projection = np.sum(lines, axis=0)

        # Find peaks (grid lines)
        peaks = self._find_peaks(projection)

        if len(peaks) < 3:
            return None

        # Calculate spacings between consecutive peaks
        spacings = np.diff(peaks)

        # Filter outliers (spacings should be consistent)
        median_spacing = np.median(spacings)
        valid_spacings = spacings[
            (spacings > median_spacing * 0.5) &
            (spacings < median_spacing * 1.5)
        ]

        if len(valid_spacings) < 2:
            return None

        return float(np.median(valid_spacings))

    def _find_peaks(self, signal: np.ndarray, min_distance: int = 5) -> np.ndarray:
        """Find peaks in 1D signal"""
        # Simple peak detection
        peaks = []
        for i in range(min_distance, len(signal) - min_distance):
            if signal[i] > signal[i - min_distance] and signal[i] > signal[i + min_distance]:
                # Check if local maximum
                window = signal[i - min_distance:i + min_distance + 1]
                if signal[i] == np.max(window):
                    peaks.append(i)

        return np.array(peaks)

    def _estimate_from_image_size(self, image: np.ndarray) -> float:
        """
        Estimate grid size from typical ECG dimensions.

        Standard 12-lead ECG is approximately:
        - Width: 250-300mm (10-12 inches)
        - Height: 150-200mm (6-8 inches)
        """
        width = image.shape[1]
        height = image.shape[0]

        # Assume standard ECG width of ~280mm
        estimated_mm_width = 280
        pixels_per_mm = width / estimated_mm_width

        return pixels_per_mm

    def detect_calibration_marker(
        self,
        image: np.ndarray,
        expected_height_mm: float = 10.0
    ) -> Optional[float]:
        """
        Detect the 1mV calibration pulse at the start of ECG.

        Many ECGs have a calibration square pulse that should be:
        - 10mm tall (1mV at 10mm/mV)
        - At the beginning of the trace

        Returns pixels per mV if detected.
        """
        # Look in left portion of image
        left_portion = image[:, :image.shape[1] // 4]

        # Find vertical edges (calibration pulse edges)
        edges = cv2.Canny(left_portion, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Look for rectangular calibration pulse
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Calibration pulse is typically narrow and tall
            aspect_ratio = h / max(w, 1)
            if aspect_ratio > 3 and w < 50:
                # This might be the calibration pulse
                return h / expected_height_mm

        return None


class GridVisualizer:
    """Visualize detected grid for debugging"""

    @staticmethod
    def overlay_grid(
        image: np.ndarray,
        calibration: GridCalibration,
        color: Tuple[int, int, int] = (0, 255, 0),
        alpha: float = 0.3
    ) -> np.ndarray:
        """
        Overlay detected grid on image.

        Args:
            image: Original image (color)
            calibration: Detected calibration
            color: Grid line color (BGR)
            alpha: Transparency

        Returns:
            Image with grid overlay
        """
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        overlay = image.copy()
        height, width = image.shape[:2]

        spacing = calibration.pixels_per_small_square

        # Draw vertical lines
        x = 0.0
        while x < width:
            cv2.line(overlay, (int(x), 0), (int(x), height), color, 1)
            x += spacing

        # Draw horizontal lines
        y = 0.0
        while y < height:
            cv2.line(overlay, (0, int(y)), (width, int(y)), color, 1)
            y += spacing

        # Blend
        result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

        return result
