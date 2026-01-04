"""
ECG Measurement Extractor

Extracts clinical measurements from detected waveforms:
- Heart rate
- Intervals (PR, QRS, QT, QTc)
- Axis calculation
- ST segment analysis
- Morphology features

Output format matches what algorithms expect.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import math

from .waveform_detector import WaveformAnnotations, Beat


@dataclass
class ECGMeasurements:
    """
    Complete ECG measurements ready for algorithm input.

    This format is what the VT/SVT, STEMI, and pathway algorithms expect.
    """
    # Basic measurements
    heart_rate: Optional[int] = None
    rhythm: Optional[str] = None  # "sinus", "afib", "flutter", etc.
    pr_interval_ms: Optional[int] = None
    qrs_duration_ms: Optional[int] = None
    qt_interval_ms: Optional[int] = None
    qtc_ms: Optional[int] = None  # Corrected QT
    axis_degrees: Optional[int] = None

    # Per-lead measurements
    leads: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Clinical context (may come from user input)
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None  # "male", "female"
    has_structural_heart_disease: Optional[bool] = None

    # Detection metadata
    num_beats_analyzed: int = 0
    quality_score: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_algorithm_format(self) -> Dict[str, Any]:
        """Convert to format expected by algorithms"""
        return {
            "heart_rate": self.heart_rate,
            "rhythm": self.rhythm,
            "pr_interval_ms": self.pr_interval_ms,
            "qrs_duration_ms": self.qrs_duration_ms,
            "qt_interval_ms": self.qt_interval_ms,
            "qtc_ms": self.qtc_ms,
            "axis_degrees": self.axis_degrees,
            "leads": self.leads,
            "age": self.patient_age,
            "patient_age": self.patient_age,
            "patient_sex": self.patient_sex,
            "has_structural_heart_disease": self.has_structural_heart_disease,
        }


class MeasurementExtractor:
    """
    Extracts clinical measurements from detected waveforms.

    Aggregates measurements across leads and calculates derived values.
    """

    def __init__(self, qtc_formula: str = "bazett"):
        """
        Args:
            qtc_formula: "bazett", "fridericia", or "framingham"
        """
        self.qtc_formula = qtc_formula

    def extract(
        self,
        annotations: Dict[str, WaveformAnnotations],  # lead_name -> annotations
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> ECGMeasurements:
        """
        Extract measurements from all lead annotations.

        Args:
            annotations: Dictionary of lead name to WaveformAnnotations
            patient_age: Patient age (for context)
            patient_sex: Patient sex (for QTc thresholds)

        Returns:
            ECGMeasurements ready for algorithms
        """
        measurements = ECGMeasurements(
            patient_age=patient_age,
            patient_sex=patient_sex,
        )

        # Aggregate measurements from all leads
        all_pr = []
        all_qrs = []
        all_qt = []
        all_rr = []

        for lead_name, ann in annotations.items():
            # Extract lead-specific measurements
            lead_data = self._extract_lead_measurements(ann)
            measurements.leads[lead_name] = lead_data

            # Collect for averaging
            if ann.get_mean_pr_interval():
                all_pr.append(ann.get_mean_pr_interval())
            if ann.get_mean_qrs_duration():
                all_qrs.append(ann.get_mean_qrs_duration())
            if ann.get_mean_qt_interval():
                all_qt.append(ann.get_mean_qt_interval())

            for beat in ann.beats:
                if beat.rr_interval_ms:
                    all_rr.append(beat.rr_interval_ms)

        # Calculate global measurements
        if all_rr:
            mean_rr = np.mean(all_rr)
            measurements.heart_rate = int(60000 / mean_rr)
            measurements.num_beats_analyzed = len(all_rr) + 1

            # Rhythm analysis
            measurements.rhythm = self._analyze_rhythm(all_rr)

        if all_pr:
            measurements.pr_interval_ms = int(np.median(all_pr))

        if all_qrs:
            measurements.qrs_duration_ms = int(np.median(all_qrs))

        if all_qt:
            measurements.qt_interval_ms = int(np.median(all_qt))

            # Calculate QTc
            if all_rr:
                mean_rr_sec = np.mean(all_rr) / 1000
                measurements.qtc_ms = self._calculate_qtc(
                    measurements.qt_interval_ms,
                    mean_rr_sec
                )

        # Calculate axis
        if "I" in annotations and "aVF" in annotations:
            measurements.axis_degrees = self._calculate_axis(
                annotations["I"], annotations["aVF"]
            )

        # Quality score
        quality_scores = [ann.quality_score for ann in annotations.values()]
        measurements.quality_score = np.mean(quality_scores) if quality_scores else 0.0

        # Add warnings
        measurements.warnings = self._generate_warnings(measurements)

        return measurements

    def _extract_lead_measurements(
        self,
        annotations: WaveformAnnotations
    ) -> Dict[str, Any]:
        """Extract measurements specific to one lead"""
        lead_data = {}

        if not annotations.beats:
            return lead_data

        # R peak amplitude
        r_amplitudes = [
            b.qrs.r_amplitude_mv for b in annotations.beats
            if b.qrs and b.qrs.r_amplitude_mv is not None
        ]
        if r_amplitudes:
            lead_data["r_amplitude_mv"] = float(np.mean(r_amplitudes))

        # QRS morphology features (for VT/SVT algorithms)
        lead_data["has_rs_complex"] = self._check_rs_complex(annotations)
        lead_data["rs_interval_ms"] = self._measure_rs_interval(annotations)

        # R-peak time (for Pava algorithm)
        lead_data["r_peak_time_ms"] = self._measure_r_peak_time(annotations)

        # Time to first peak (for Basel algorithm)
        lead_data["time_to_first_peak_ms"] = self._measure_time_to_first_peak(annotations)

        # ST segment measurements (for STEMI)
        st_data = self._measure_st_segment(annotations)
        lead_data.update(st_data)

        return lead_data

    def _check_rs_complex(self, annotations: WaveformAnnotations) -> bool:
        """Check if lead has RS complex (for Brugada algorithm)"""
        for beat in annotations.beats:
            if beat.qrs:
                if beat.qrs.r_peak and beat.qrs.s_nadir:
                    # Has both R and S waves
                    r_amp = beat.qrs.r_peak.voltage_mv
                    s_amp = beat.qrs.s_nadir.voltage_mv
                    if r_amp > 0 and s_amp < 0:
                        return True
        return False

    def _measure_rs_interval(self, annotations: WaveformAnnotations) -> Optional[float]:
        """Measure RS interval in ms (for Brugada algorithm)"""
        intervals = []
        for beat in annotations.beats:
            if beat.qrs and beat.qrs.r_peak and beat.qrs.s_nadir:
                interval = beat.qrs.s_nadir.time_ms - beat.qrs.r_peak.time_ms
                if interval > 0:
                    intervals.append(interval)
        return float(np.mean(intervals)) if intervals else None

    def _measure_r_peak_time(self, annotations: WaveformAnnotations) -> Optional[float]:
        """Measure R-wave peak time from QRS onset (for Pava algorithm)"""
        times = []
        for beat in annotations.beats:
            if beat.qrs and beat.qrs.r_peak and beat.qrs.q_onset:
                time = beat.qrs.r_peak.time_ms - beat.qrs.q_onset.time_ms
                if time > 0:
                    times.append(time)
        return float(np.mean(times)) if times else None

    def _measure_time_to_first_peak(self, annotations: WaveformAnnotations) -> Optional[float]:
        """Measure time from QRS onset to first peak (for Basel algorithm)"""
        times = []
        for beat in annotations.beats:
            if beat.qrs and beat.qrs.q_onset:
                # First peak could be R or Q
                first_peak_time = None

                if beat.qrs.q_nadir:
                    first_peak_time = beat.qrs.q_nadir.time_ms
                elif beat.qrs.r_peak:
                    first_peak_time = beat.qrs.r_peak.time_ms

                if first_peak_time:
                    time = first_peak_time - beat.qrs.q_onset.time_ms
                    if time > 0:
                        times.append(time)

        return float(np.mean(times)) if times else None

    def _measure_st_segment(self, annotations: WaveformAnnotations) -> Dict[str, float]:
        """Measure ST segment elevation/depression (for STEMI algorithm)"""
        st_data = {
            "st_elevation_mm": 0.0,
            "st_depression_mm": 0.0,
        }

        elevations = []
        depressions = []

        for beat in annotations.beats:
            if beat.qrs and beat.qrs.s_offset and beat.t_wave and beat.t_wave.onset:
                # ST segment is between S offset and T onset
                # Measure at J+60ms or J+80ms (J point = QRS end)
                j_time = beat.qrs.s_offset.time_ms
                baseline = beat.qrs.s_offset.voltage_mv  # Approximate baseline

                # ST level relative to baseline
                if beat.t_wave.onset:
                    st_level = beat.t_wave.onset.voltage_mv - baseline

                    # Convert mV to mm (1mm = 0.1mV at standard calibration)
                    st_mm = st_level * 10

                    if st_mm > 0:
                        elevations.append(st_mm)
                    else:
                        depressions.append(abs(st_mm))

        if elevations:
            st_data["st_elevation_mm"] = float(np.max(elevations))
        if depressions:
            st_data["st_depression_mm"] = float(np.max(depressions))

        return st_data

    def _analyze_rhythm(self, rr_intervals: List[float]) -> str:
        """Analyze rhythm from R-R intervals"""
        if len(rr_intervals) < 2:
            return "undetermined"

        mean_rr = np.mean(rr_intervals)
        std_rr = np.std(rr_intervals)
        cv = std_rr / mean_rr  # Coefficient of variation

        hr = 60000 / mean_rr

        # Regular rhythm if CV < 0.1
        if cv < 0.1:
            if 60 <= hr <= 100:
                return "sinus"
            elif hr < 60:
                return "sinus_bradycardia"
            else:
                return "sinus_tachycardia"
        else:
            # Irregular rhythm
            if cv > 0.3:
                return "irregularly_irregular"  # Likely AFib
            else:
                return "irregular"

    def _calculate_qtc(self, qt_ms: int, rr_sec: float) -> int:
        """Calculate corrected QT interval"""
        qt_sec = qt_ms / 1000

        if self.qtc_formula == "bazett":
            # Bazett: QTc = QT / sqrt(RR)
            qtc_sec = qt_sec / math.sqrt(rr_sec)
        elif self.qtc_formula == "fridericia":
            # Fridericia: QTc = QT / RR^(1/3)
            qtc_sec = qt_sec / (rr_sec ** (1/3))
        elif self.qtc_formula == "framingham":
            # Framingham: QTc = QT + 0.154(1-RR)
            qtc_sec = qt_sec + 0.154 * (1 - rr_sec)
        else:
            qtc_sec = qt_sec / math.sqrt(rr_sec)  # Default to Bazett

        return int(qtc_sec * 1000)

    def _calculate_axis(
        self,
        lead_i: WaveformAnnotations,
        lead_avf: WaveformAnnotations
    ) -> Optional[int]:
        """
        Calculate frontal axis from leads I and aVF.

        Uses net QRS amplitude in each lead.
        """
        # Get net QRS amplitude in Lead I
        net_i = self._get_net_qrs_amplitude(lead_i)
        # Get net QRS amplitude in aVF
        net_avf = self._get_net_qrs_amplitude(lead_avf)

        if net_i is None or net_avf is None:
            return None

        # Calculate axis using arctan
        # Lead I is at 0°, aVF is at +90°
        axis_rad = math.atan2(net_avf, net_i)
        axis_deg = math.degrees(axis_rad)

        # Normalize to -180 to +180
        return int(axis_deg)

    def _get_net_qrs_amplitude(self, annotations: WaveformAnnotations) -> Optional[float]:
        """Calculate net (algebraic sum) QRS amplitude"""
        net_amplitudes = []

        for beat in annotations.beats:
            if beat.qrs:
                r_amp = beat.qrs.r_peak.voltage_mv if beat.qrs.r_peak else 0
                q_amp = beat.qrs.q_nadir.voltage_mv if beat.qrs.q_nadir else 0
                s_amp = beat.qrs.s_nadir.voltage_mv if beat.qrs.s_nadir else 0

                # Net = R - (|Q| + |S|)
                net = r_amp + q_amp + s_amp  # Q and S are negative
                net_amplitudes.append(net)

        return np.mean(net_amplitudes) if net_amplitudes else None

    def _generate_warnings(self, measurements: ECGMeasurements) -> List[str]:
        """Generate warnings about measurements"""
        warnings = []

        if measurements.quality_score < 0.5:
            warnings.append("Low quality signal - measurements may be inaccurate")

        if measurements.num_beats_analyzed < 3:
            warnings.append("Few beats analyzed - measurements may not be representative")

        if measurements.pr_interval_ms and measurements.pr_interval_ms > 200:
            warnings.append("Prolonged PR interval detected")

        if measurements.qrs_duration_ms and measurements.qrs_duration_ms > 120:
            warnings.append("Wide QRS complex detected")

        if measurements.qtc_ms:
            if measurements.patient_sex == "male" and measurements.qtc_ms > 450:
                warnings.append("Prolonged QTc for male patient")
            elif measurements.patient_sex == "female" and measurements.qtc_ms > 470:
                warnings.append("Prolonged QTc for female patient")

        return warnings
