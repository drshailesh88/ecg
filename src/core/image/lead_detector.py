"""
ECG Lead Detector

Identifies and isolates the 12 leads from an ECG image.

Standard 12-lead ECG layout (most common):
- Row 1: I, II, III (limb leads)
- Row 2: aVR, aVL, aVF (augmented limb leads)
- Row 3: V1, V2, V3 (precordial leads)
- Row 4: V4, V5, V6 (precordial leads)
- Bottom: Rhythm strip (usually Lead II)

Alternative layouts:
- 3x4 with rhythm strip
- 4x3 format
- Single column
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import cv2


@dataclass
class DetectedLead:
    """A detected ECG lead region"""
    name: str  # e.g., "I", "aVR", "V1"
    region: Tuple[int, int, int, int]  # (x, y, width, height)
    image: np.ndarray  # Cropped image of just this lead
    confidence: float  # Detection confidence
    row: int  # Row position in layout
    col: int  # Column position in layout


@dataclass
class LeadLayout:
    """ECG lead layout configuration"""
    name: str
    rows: int
    cols: int
    lead_order: List[List[str]]
    has_rhythm_strip: bool = True
    rhythm_lead: str = "II"


# Common ECG layouts
LAYOUT_3X4 = LeadLayout(
    name="3x4",
    rows=3,
    cols=4,
    lead_order=[
        ["I", "aVR", "V1", "V4"],
        ["II", "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
    ],
    has_rhythm_strip=True,
    rhythm_lead="II",
)

LAYOUT_4X3 = LeadLayout(
    name="4x3",
    rows=4,
    cols=3,
    lead_order=[
        ["I", "II", "III"],
        ["aVR", "aVL", "aVF"],
        ["V1", "V2", "V3"],
        ["V4", "V5", "V6"],
    ],
    has_rhythm_strip=True,
    rhythm_lead="II",
)

LAYOUT_6X2 = LeadLayout(
    name="6x2",
    rows=6,
    cols=2,
    lead_order=[
        ["I", "V1"],
        ["II", "V2"],
        ["III", "V3"],
        ["aVR", "V4"],
        ["aVL", "V5"],
        ["aVF", "V6"],
    ],
    has_rhythm_strip=False,
)


class LeadDetector:
    """
    Detects and extracts individual leads from ECG image.

    Approach:
    1. Find lead labels using OCR or template matching
    2. Or: Segment image based on layout (grid-based)
    3. Extract each lead region
    """

    STANDARD_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

    def __init__(self, default_layout: LeadLayout = LAYOUT_3X4):
        self.default_layout = default_layout

    def detect(
        self,
        image: np.ndarray,
        layout: Optional[LeadLayout] = None
    ) -> List[DetectedLead]:
        """
        Detect all leads in the ECG image.

        Args:
            image: Preprocessed ECG image
            layout: Known layout (if None, will try to detect)

        Returns:
            List of detected leads
        """
        if layout is None:
            layout = self._detect_layout(image)

        # Try OCR-based detection first
        leads = self._detect_with_labels(image)

        if len(leads) >= 10:  # Found most leads via labels
            return leads

        # Fall back to grid-based segmentation
        return self._segment_by_layout(image, layout)

    def _detect_layout(self, image: np.ndarray) -> LeadLayout:
        """
        Detect the ECG layout format.

        Analyzes aspect ratio and content distribution.
        """
        height, width = image.shape[:2]
        aspect_ratio = width / height

        # Most standard ECGs are wider than tall (3:4 ratio)
        if aspect_ratio > 1.5:
            return LAYOUT_3X4
        elif aspect_ratio > 0.8:
            return LAYOUT_4X3
        else:
            return LAYOUT_6X2

    def _detect_with_labels(self, image: np.ndarray) -> List[DetectedLead]:
        """
        Detect leads by finding lead labels in the image.

        Uses template matching or OCR to find "I", "II", "V1", etc.
        """
        leads = []

        # Convert to binary for text detection
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours (potential text regions)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Look for small, dark regions that could be lead labels
        label_candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Lead labels are typically small text
            if 10 < w < 100 and 10 < h < 50:
                # Check aspect ratio (text is usually wider than tall or square)
                if 0.3 < w / h < 3:
                    roi = image[y:y+h, x:x+w]
                    label_candidates.append((x, y, w, h, roi))

        # TODO: Add OCR here to read actual labels
        # For now, return empty list to fall back to grid segmentation

        return leads

    def _segment_by_layout(
        self,
        image: np.ndarray,
        layout: LeadLayout
    ) -> List[DetectedLead]:
        """
        Segment image into leads based on known layout.

        Divides image into grid based on layout configuration.
        """
        height, width = image.shape[:2]
        leads = []

        # Calculate rhythm strip height (typically bottom 15-20% of image)
        if layout.has_rhythm_strip:
            rhythm_height = int(height * 0.15)
            main_height = height - rhythm_height
        else:
            main_height = height
            rhythm_height = 0

        # Calculate cell dimensions
        cell_width = width // layout.cols
        cell_height = main_height // layout.rows

        # Add margin to exclude labels and borders
        margin_x = int(cell_width * 0.05)
        margin_y = int(cell_height * 0.1)

        # Extract each lead
        for row_idx, row_leads in enumerate(layout.lead_order):
            for col_idx, lead_name in enumerate(row_leads):
                x = col_idx * cell_width + margin_x
                y = row_idx * cell_height + margin_y
                w = cell_width - 2 * margin_x
                h = cell_height - 2 * margin_y

                # Ensure within bounds
                x = max(0, min(x, width - 1))
                y = max(0, min(y, main_height - 1))
                w = min(w, width - x)
                h = min(h, main_height - y)

                lead_image = image[y:y+h, x:x+w]

                leads.append(DetectedLead(
                    name=lead_name,
                    region=(x, y, w, h),
                    image=lead_image,
                    confidence=0.7,  # Lower confidence for grid-based
                    row=row_idx,
                    col=col_idx,
                ))

        # Add rhythm strip if present
        if layout.has_rhythm_strip:
            y = main_height
            rhythm_image = image[y:y+rhythm_height, margin_x:width-margin_x]
            leads.append(DetectedLead(
                name=f"Rhythm_{layout.rhythm_lead}",
                region=(margin_x, y, width - 2*margin_x, rhythm_height),
                image=rhythm_image,
                confidence=0.7,
                row=layout.rows,
                col=0,
            ))

        return leads

    def get_lead_by_name(
        self,
        leads: List[DetectedLead],
        name: str
    ) -> Optional[DetectedLead]:
        """Get a specific lead by name"""
        for lead in leads:
            if lead.name == name or lead.name == f"Rhythm_{name}":
                return lead
        return None

    def get_leads_dict(self, leads: List[DetectedLead]) -> Dict[str, DetectedLead]:
        """Convert lead list to dictionary by name"""
        return {lead.name: lead for lead in leads}
