"""
ECG Image Preprocessor

Prepares ECG images for analysis:
- Grayscale conversion
- Noise reduction
- Contrast enhancement
- Skew correction
- Border removal
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
import cv2


@dataclass
class PreprocessingResult:
    """Result of image preprocessing"""
    image: np.ndarray  # Processed image
    original_size: Tuple[int, int]  # (width, height)
    processed_size: Tuple[int, int]
    rotation_angle: float  # Degrees rotated for skew correction
    quality_score: float  # 0-1, estimated image quality


class ECGPreprocessor:
    """
    Preprocesses ECG images for reliable signal extraction.

    Handles common issues:
    - Poor lighting (phone photos)
    - Skewed scans
    - Low contrast
    - Noise from paper texture
    """

    def __init__(
        self,
        target_width: int = 2000,  # Standardize size
        denoise_strength: int = 10,
        enhance_contrast: bool = True,
        correct_skew: bool = True,
    ):
        self.target_width = target_width
        self.denoise_strength = denoise_strength
        self.enhance_contrast = enhance_contrast
        self.correct_skew = correct_skew

    def process(self, image: np.ndarray) -> PreprocessingResult:
        """
        Process an ECG image.

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            PreprocessingResult with processed image and metadata
        """
        original_size = (image.shape[1], image.shape[0])

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Resize to standard width (maintain aspect ratio)
        scale = self.target_width / gray.shape[1]
        new_height = int(gray.shape[0] * scale)
        resized = cv2.resize(gray, (self.target_width, new_height), interpolation=cv2.INTER_CUBIC)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(resized, h=self.denoise_strength)

        # Enhance contrast using CLAHE
        if self.enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
        else:
            enhanced = denoised

        # Detect and correct skew
        rotation_angle = 0.0
        if self.correct_skew:
            rotation_angle = self._detect_skew(enhanced)
            if abs(rotation_angle) > 0.1:  # Only rotate if significant
                enhanced = self._rotate_image(enhanced, rotation_angle)

        # Estimate quality
        quality_score = self._estimate_quality(enhanced)

        processed_size = (enhanced.shape[1], enhanced.shape[0])

        return PreprocessingResult(
            image=enhanced,
            original_size=original_size,
            processed_size=processed_size,
            rotation_angle=rotation_angle,
            quality_score=quality_score,
        )

    def _detect_skew(self, image: np.ndarray) -> float:
        """
        Detect image skew using Hough line detection.

        Returns rotation angle in degrees.
        """
        # Edge detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)

        if lines is None or len(lines) == 0:
            return 0.0

        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            # Only consider near-horizontal lines
            if abs(angle) < 10:
                angles.append(angle)

        if not angles:
            return 0.0

        # Return median angle
        return float(np.median(angles))

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle."""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, rotation_matrix, (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def _estimate_quality(self, image: np.ndarray) -> float:
        """
        Estimate image quality for ECG analysis.

        Factors:
        - Contrast (variance of pixel values)
        - Sharpness (Laplacian variance)
        - Noise level
        """
        # Contrast: normalized standard deviation
        contrast = np.std(image) / 128.0
        contrast_score = min(contrast, 1.0)

        # Sharpness: Laplacian variance
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        sharpness = np.var(laplacian)
        sharpness_score = min(sharpness / 500, 1.0)

        # Combined score
        quality = 0.5 * contrast_score + 0.5 * sharpness_score

        return float(np.clip(quality, 0.0, 1.0))

    def remove_borders(self, image: np.ndarray, margin_percent: float = 0.02) -> np.ndarray:
        """
        Remove dark borders from image.

        Useful for scanned ECGs with black borders.
        """
        height, width = image.shape[:2]
        margin_x = int(width * margin_percent)
        margin_y = int(height * margin_percent)

        # Find content region
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return image

        # Find bounding box of all contours
        all_points = np.vstack(contours)
        x, y, w, h = cv2.boundingRect(all_points)

        # Add margin
        x = max(0, x - margin_x)
        y = max(0, y - margin_y)
        w = min(width - x, w + 2 * margin_x)
        h = min(height - y, h + 2 * margin_y)

        return image[y:y+h, x:x+w]
