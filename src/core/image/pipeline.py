"""
ECG Image Pipeline

Complete pipeline from ECG image to measurements.

Usage:
    from core.image import ECGImagePipeline

    pipeline = ECGImagePipeline()
    result = pipeline.process(image)

    # Get measurements for algorithms
    measurements = result.measurements.to_algorithm_format()

    # Run VT/SVT analysis
    from core.algorithms import VTSVTEnsemble
    ensemble = VTSVTEnsemble()
    diagnosis = ensemble.evaluate(measurements)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import cv2
from pathlib import Path

from .preprocessor import ECGPreprocessor, PreprocessingResult
from .grid_detector import GridDetector, GridCalibration
from .lead_detector import LeadDetector, DetectedLead, LeadLayout
from .signal_extractor import SignalExtractor, ECGSignal
from .waveform_detector import WaveformDetector, WaveformAnnotations
from .measurement_extractor import MeasurementExtractor, ECGMeasurements


@dataclass
class PipelineResult:
    """Result of ECG image processing pipeline"""

    # Final output (what algorithms need)
    measurements: ECGMeasurements

    # Intermediate results (for debugging/visualization)
    preprocessing: Optional[PreprocessingResult] = None
    calibration: Optional[GridCalibration] = None
    leads: List[DetectedLead] = field(default_factory=list)
    signals: Dict[str, ECGSignal] = field(default_factory=dict)
    annotations: Dict[str, WaveformAnnotations] = field(default_factory=dict)

    # Quality and metadata
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "measurements": self.measurements.to_algorithm_format(),
            "quality_score": self.measurements.quality_score,
            "num_leads_detected": len(self.leads),
            "num_beats_analyzed": self.measurements.num_beats_analyzed,
            "errors": self.errors,
            "warnings": self.warnings + self.measurements.warnings,
            "processing_time_ms": self.processing_time_ms,
        }


class ECGImagePipeline:
    """
    Complete pipeline for ECG image analysis.

    Stages:
    1. Preprocessing: Enhance image quality
    2. Grid Detection: Calibrate pixels to mm
    3. Lead Detection: Find and isolate 12 leads
    4. Signal Extraction: Digitize each lead's trace
    5. Waveform Detection: Find P, QRS, T waves
    6. Measurement Extraction: Calculate intervals, axis, etc.
    """

    def __init__(
        self,
        target_width: int = 2000,
        sample_rate: float = 500.0,
        layout: Optional[LeadLayout] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            target_width: Standardize image width for processing
            sample_rate: Target sample rate for digitized signals
            layout: ECG layout (None = auto-detect)
        """
        self.preprocessor = ECGPreprocessor(target_width=target_width)
        self.grid_detector = GridDetector()
        self.lead_detector = LeadDetector()
        self.signal_extractor = SignalExtractor(sample_rate=sample_rate)
        self.waveform_detector = WaveformDetector(sample_rate_hz=sample_rate)
        self.measurement_extractor = MeasurementExtractor()
        self.layout = layout

    def process(
        self,
        image: np.ndarray,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process an ECG image through the complete pipeline.

        Args:
            image: ECG image (BGR or grayscale)
            patient_age: Patient age (for context)
            patient_sex: Patient sex ("male" or "female")

        Returns:
            PipelineResult with measurements and intermediate data
        """
        import time
        start_time = time.time()

        result = PipelineResult(
            measurements=ECGMeasurements(
                patient_age=patient_age,
                patient_sex=patient_sex,
            )
        )

        try:
            # Stage 1: Preprocessing
            preprocessing = self.preprocessor.process(image)
            result.preprocessing = preprocessing

            if preprocessing.quality_score < 0.2:
                result.warnings.append("Very low image quality detected")

            # Stage 2: Grid Detection
            calibration = self.grid_detector.detect(preprocessing.image)
            result.calibration = calibration

            if not calibration.grid_detected:
                result.warnings.append("Grid not detected - using estimated calibration")

            # Stage 3: Lead Detection
            leads = self.lead_detector.detect(preprocessing.image, self.layout)
            result.leads = leads

            if len(leads) < 6:
                result.warnings.append(f"Only {len(leads)} leads detected (expected 12)")

            # Stage 4: Signal Extraction
            signals = {}
            for lead in leads:
                try:
                    signal = self.signal_extractor.extract(
                        lead.image,
                        calibration,
                        lead.name
                    )
                    signals[lead.name] = signal
                except Exception as e:
                    result.warnings.append(f"Failed to extract signal from {lead.name}: {str(e)}")

            result.signals = signals

            # Stage 5: Waveform Detection
            annotations = {}
            for lead_name, signal in signals.items():
                try:
                    ann = self.waveform_detector.detect(signal)
                    annotations[lead_name] = ann
                except Exception as e:
                    result.warnings.append(f"Failed to detect waveforms in {lead_name}: {str(e)}")

            result.annotations = annotations

            # Stage 6: Measurement Extraction
            measurements = self.measurement_extractor.extract(
                annotations,
                patient_age=patient_age,
                patient_sex=patient_sex,
            )
            result.measurements = measurements

        except Exception as e:
            result.success = False
            result.errors.append(f"Pipeline failed: {str(e)}")

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def process_file(
        self,
        file_path: str,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process an ECG image file.

        Args:
            file_path: Path to ECG image file
            patient_age: Patient age
            patient_sex: Patient sex

        Returns:
            PipelineResult
        """
        path = Path(file_path)

        if not path.exists():
            result = PipelineResult(measurements=ECGMeasurements())
            result.success = False
            result.errors.append(f"File not found: {file_path}")
            return result

        # Read image
        image = cv2.imread(str(path))

        if image is None:
            result = PipelineResult(measurements=ECGMeasurements())
            result.success = False
            result.errors.append(f"Failed to read image: {file_path}")
            return result

        return self.process(image, patient_age, patient_sex)

    def process_base64(
        self,
        image_base64: str,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process a base64-encoded ECG image.

        Args:
            image_base64: Base64-encoded image data
            patient_age: Patient age
            patient_sex: Patient sex

        Returns:
            PipelineResult
        """
        import base64

        try:
            # Decode base64
            image_data = base64.b64decode(image_base64)
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                result = PipelineResult(measurements=ECGMeasurements())
                result.success = False
                result.errors.append("Failed to decode image from base64")
                return result

            return self.process(image, patient_age, patient_sex)

        except Exception as e:
            result = PipelineResult(measurements=ECGMeasurements())
            result.success = False
            result.errors.append(f"Failed to process base64 image: {str(e)}")
            return result


def quick_analyze(
    image_path: str,
    patient_age: Optional[int] = None,
    patient_sex: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick analysis of an ECG image.

    Convenience function for simple use cases.

    Args:
        image_path: Path to ECG image
        patient_age: Patient age
        patient_sex: Patient sex

    Returns:
        Dictionary with measurements ready for algorithms
    """
    pipeline = ECGImagePipeline()
    result = pipeline.process_file(image_path, patient_age, patient_sex)
    return result.measurements.to_algorithm_format()


# CLI entry point for testing
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Process ECG image")
    parser.add_argument("image_path", help="Path to ECG image file")
    parser.add_argument("--age", type=int, help="Patient age")
    parser.add_argument("--sex", choices=["male", "female"], help="Patient sex")
    parser.add_argument("--output", help="Output JSON file")

    args = parser.parse_args()

    pipeline = ECGImagePipeline()
    result = pipeline.process_file(args.image_path, args.age, args.sex)

    output = result.to_dict()

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    # Summary
    print("\n--- Summary ---")
    print(f"Success: {result.success}")
    print(f"Leads detected: {len(result.leads)}")
    print(f"Heart rate: {result.measurements.heart_rate} bpm")
    print(f"QRS duration: {result.measurements.qrs_duration_ms} ms")
    print(f"QTc: {result.measurements.qtc_ms} ms")
    print(f"Processing time: {result.processing_time_ms:.0f} ms")

    if result.warnings:
        print("\nWarnings:")
        for w in result.warnings:
            print(f"  - {w}")

    if result.errors:
        print("\nErrors:")
        for e in result.errors:
            print(f"  - {e}")
