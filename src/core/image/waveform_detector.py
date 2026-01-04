"""
ECG Waveform Detector

Detects P, QRS, and T waves in digitized ECG signals.

Key features to detect:
- P wave: Atrial depolarization
- QRS complex: Ventricular depolarization (Q, R, S waves)
- T wave: Ventricular repolarization
- U wave: (optional) Late repolarization

Fiducial points:
- P onset, P peak, P offset
- Q onset (QRS onset), R peak, S offset (QRS offset)
- T onset, T peak, T offset
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from scipy import signal as scipy_signal
from .signal_extractor import ECGSignal


@dataclass
class WaveformPoint:
    """A detected point on the ECG waveform"""
    time_ms: float
    voltage_mv: float
    point_type: str  # e.g., "R_peak", "P_onset", "T_peak"
    confidence: float = 1.0


@dataclass
class QRSComplex:
    """A detected QRS complex"""
    q_onset: Optional[WaveformPoint] = None
    q_nadir: Optional[WaveformPoint] = None
    r_peak: Optional[WaveformPoint] = None
    s_nadir: Optional[WaveformPoint] = None
    s_offset: Optional[WaveformPoint] = None

    @property
    def onset_time(self) -> Optional[float]:
        return self.q_onset.time_ms if self.q_onset else None

    @property
    def offset_time(self) -> Optional[float]:
        return self.s_offset.time_ms if self.s_offset else None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.q_onset and self.s_offset:
            return self.s_offset.time_ms - self.q_onset.time_ms
        return None

    @property
    def r_amplitude_mv(self) -> Optional[float]:
        return self.r_peak.voltage_mv if self.r_peak else None


@dataclass
class PWave:
    """A detected P wave"""
    onset: Optional[WaveformPoint] = None
    peak: Optional[WaveformPoint] = None
    offset: Optional[WaveformPoint] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.onset and self.offset:
            return self.offset.time_ms - self.onset.time_ms
        return None


@dataclass
class TWave:
    """A detected T wave"""
    onset: Optional[WaveformPoint] = None
    peak: Optional[WaveformPoint] = None
    offset: Optional[WaveformPoint] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.onset and self.offset:
            return self.offset.time_ms - self.onset.time_ms
        return None


@dataclass
class Beat:
    """A single cardiac beat with all waveforms"""
    p_wave: Optional[PWave] = None
    qrs: Optional[QRSComplex] = None
    t_wave: Optional[TWave] = None
    rr_interval_ms: Optional[float] = None  # To previous beat

    @property
    def pr_interval_ms(self) -> Optional[float]:
        """PR interval: P onset to QRS onset"""
        if self.p_wave and self.p_wave.onset and self.qrs and self.qrs.q_onset:
            return self.qrs.q_onset.time_ms - self.p_wave.onset.time_ms
        return None

    @property
    def qt_interval_ms(self) -> Optional[float]:
        """QT interval: QRS onset to T offset"""
        if self.qrs and self.qrs.q_onset and self.t_wave and self.t_wave.offset:
            return self.t_wave.offset.time_ms - self.qrs.q_onset.time_ms
        return None


@dataclass
class WaveformAnnotations:
    """All detected waveforms in a signal"""
    lead_name: str
    beats: List[Beat] = field(default_factory=list)
    quality_score: float = 0.0

    @property
    def num_beats(self) -> int:
        return len(self.beats)

    @property
    def heart_rate(self) -> Optional[float]:
        """Calculate heart rate from R-R intervals"""
        rr_intervals = [b.rr_interval_ms for b in self.beats if b.rr_interval_ms]
        if not rr_intervals:
            return None
        mean_rr_ms = np.mean(rr_intervals)
        return 60000 / mean_rr_ms  # bpm

    def get_mean_pr_interval(self) -> Optional[float]:
        """Mean PR interval across all beats"""
        pr_intervals = [b.pr_interval_ms for b in self.beats if b.pr_interval_ms]
        return np.mean(pr_intervals) if pr_intervals else None

    def get_mean_qrs_duration(self) -> Optional[float]:
        """Mean QRS duration across all beats"""
        qrs_durations = [b.qrs.duration_ms for b in self.beats if b.qrs and b.qrs.duration_ms]
        return np.mean(qrs_durations) if qrs_durations else None

    def get_mean_qt_interval(self) -> Optional[float]:
        """Mean QT interval across all beats"""
        qt_intervals = [b.qt_interval_ms for b in self.beats if b.qt_interval_ms]
        return np.mean(qt_intervals) if qt_intervals else None


class WaveformDetector:
    """
    Detects P, QRS, and T waves in ECG signals.

    Uses a combination of:
    1. R-peak detection (Pan-Tompkins-like algorithm)
    2. Template matching for P and T waves
    3. Derivative-based boundary detection
    """

    def __init__(
        self,
        sample_rate_hz: float = 500.0,
        r_peak_threshold: float = 0.5,  # Relative to max amplitude
    ):
        self.sample_rate = sample_rate_hz
        self.r_peak_threshold = r_peak_threshold

    def detect(self, ecg_signal: ECGSignal) -> WaveformAnnotations:
        """
        Detect all waveforms in an ECG signal.

        Args:
            ecg_signal: Digitized ECG signal

        Returns:
            WaveformAnnotations with all detected beats
        """
        time_ms = ecg_signal.time_ms
        voltage = ecg_signal.voltage_mv

        # Step 1: Detect R peaks
        r_peaks = self._detect_r_peaks(voltage, ecg_signal.sample_rate_hz)

        # Step 2: For each R peak, find surrounding waves
        beats = []
        for i, r_idx in enumerate(r_peaks):
            beat = self._analyze_beat(time_ms, voltage, r_idx, r_peaks, i)
            beats.append(beat)

        # Calculate quality score
        quality = self._estimate_quality(beats)

        return WaveformAnnotations(
            lead_name=ecg_signal.lead_name,
            beats=beats,
            quality_score=quality,
        )

    def _detect_r_peaks(
        self,
        voltage: np.ndarray,
        sample_rate: float
    ) -> np.ndarray:
        """
        Detect R peaks using derivative-based method.

        Simplified Pan-Tompkins approach:
        1. Bandpass filter (5-15 Hz)
        2. Differentiate
        3. Square
        4. Moving average
        5. Peak detection with refractory period
        """
        # Bandpass filter
        nyq = sample_rate / 2
        low = 5 / nyq
        high = min(15 / nyq, 0.99)

        if high > low:
            b, a = scipy_signal.butter(2, [low, high], btype='band')
            filtered = scipy_signal.filtfilt(b, a, voltage)
        else:
            filtered = voltage

        # Differentiate
        diff = np.diff(filtered)

        # Square
        squared = diff ** 2

        # Moving average
        window_size = int(0.15 * sample_rate)  # 150ms window
        if window_size > 1:
            kernel = np.ones(window_size) / window_size
            smoothed = np.convolve(squared, kernel, mode='same')
        else:
            smoothed = squared

        # Find peaks
        threshold = np.max(smoothed) * self.r_peak_threshold

        # Minimum distance between R peaks (refractory period ~200ms)
        min_distance = int(0.2 * sample_rate)

        peaks, _ = scipy_signal.find_peaks(
            smoothed,
            height=threshold,
            distance=min_distance
        )

        # Refine peak positions using original signal
        refined_peaks = []
        search_window = int(0.05 * sample_rate)  # ±50ms

        for peak in peaks:
            start = max(0, peak - search_window)
            end = min(len(voltage), peak + search_window)
            local_max = start + np.argmax(voltage[start:end])
            refined_peaks.append(local_max)

        return np.array(refined_peaks)

    def _analyze_beat(
        self,
        time_ms: np.ndarray,
        voltage: np.ndarray,
        r_idx: int,
        all_r_peaks: np.ndarray,
        beat_idx: int
    ) -> Beat:
        """Analyze a single beat around an R peak"""

        # R peak
        r_peak = WaveformPoint(
            time_ms=time_ms[r_idx],
            voltage_mv=voltage[r_idx],
            point_type="R_peak",
        )

        # QRS complex
        qrs = self._detect_qrs(time_ms, voltage, r_idx)
        qrs.r_peak = r_peak

        # P wave (before QRS)
        p_wave = self._detect_p_wave(time_ms, voltage, qrs)

        # T wave (after QRS)
        t_wave = self._detect_t_wave(time_ms, voltage, qrs, all_r_peaks, beat_idx)

        # R-R interval
        rr_interval = None
        if beat_idx > 0:
            prev_r_idx = all_r_peaks[beat_idx - 1]
            rr_interval = time_ms[r_idx] - time_ms[prev_r_idx]

        return Beat(
            p_wave=p_wave,
            qrs=qrs,
            t_wave=t_wave,
            rr_interval_ms=rr_interval,
        )

    def _detect_qrs(
        self,
        time_ms: np.ndarray,
        voltage: np.ndarray,
        r_idx: int
    ) -> QRSComplex:
        """Detect QRS complex boundaries around R peak"""

        sample_rate = len(time_ms) / (time_ms[-1] - time_ms[0]) * 1000

        # Search windows
        qrs_width = int(0.12 * sample_rate)  # ~120ms total QRS width

        # Find Q onset (before R peak)
        q_search_start = max(0, r_idx - qrs_width)
        q_region = voltage[q_search_start:r_idx]

        if len(q_region) > 0:
            # Q onset is where signal starts to deviate from baseline
            baseline = np.median(q_region[:len(q_region)//3]) if len(q_region) > 3 else 0
            threshold = baseline + 0.1 * (voltage[r_idx] - baseline)

            q_onset_local = np.where(q_region > threshold)[0]
            if len(q_onset_local) > 0:
                q_onset_idx = q_search_start + q_onset_local[0]
            else:
                q_onset_idx = r_idx - int(0.04 * sample_rate)  # Default 40ms before R

            q_onset = WaveformPoint(
                time_ms=time_ms[max(0, q_onset_idx)],
                voltage_mv=voltage[max(0, q_onset_idx)],
                point_type="Q_onset",
            )
        else:
            q_onset = None

        # Find S offset (after R peak)
        s_search_end = min(len(voltage), r_idx + qrs_width)
        s_region = voltage[r_idx:s_search_end]

        if len(s_region) > 0:
            # S nadir
            s_nadir_local = np.argmin(s_region)
            s_nadir_idx = r_idx + s_nadir_local

            s_nadir = WaveformPoint(
                time_ms=time_ms[s_nadir_idx],
                voltage_mv=voltage[s_nadir_idx],
                point_type="S_nadir",
            )

            # S offset
            post_s = voltage[s_nadir_idx:s_search_end]
            baseline = np.median(post_s[-len(post_s)//3:]) if len(post_s) > 3 else 0
            threshold = baseline + 0.1 * (voltage[s_nadir_idx] - baseline)

            s_offset_local = np.where(post_s > threshold)[0]
            if len(s_offset_local) > 0:
                s_offset_idx = s_nadir_idx + s_offset_local[0]
            else:
                s_offset_idx = r_idx + int(0.06 * sample_rate)

            s_offset = WaveformPoint(
                time_ms=time_ms[min(s_offset_idx, len(time_ms)-1)],
                voltage_mv=voltage[min(s_offset_idx, len(voltage)-1)],
                point_type="S_offset",
            )
        else:
            s_nadir = None
            s_offset = None

        return QRSComplex(
            q_onset=q_onset,
            s_nadir=s_nadir,
            s_offset=s_offset,
        )

    def _detect_p_wave(
        self,
        time_ms: np.ndarray,
        voltage: np.ndarray,
        qrs: QRSComplex
    ) -> Optional[PWave]:
        """Detect P wave before QRS"""

        if qrs.q_onset is None:
            return None

        sample_rate = len(time_ms) / (time_ms[-1] - time_ms[0]) * 1000

        # P wave is typically 120-200ms before QRS onset
        qrs_onset_idx = np.searchsorted(time_ms, qrs.q_onset.time_ms)
        p_search_start = max(0, qrs_onset_idx - int(0.25 * sample_rate))
        p_search_end = max(0, qrs_onset_idx - int(0.04 * sample_rate))

        if p_search_end <= p_search_start:
            return None

        p_region = voltage[p_search_start:p_search_end]

        if len(p_region) < 3:
            return None

        # Find P peak (usually positive deflection)
        p_peak_local = np.argmax(p_region)
        p_peak_idx = p_search_start + p_peak_local

        p_peak = WaveformPoint(
            time_ms=time_ms[p_peak_idx],
            voltage_mv=voltage[p_peak_idx],
            point_type="P_peak",
        )

        # Estimate P onset and offset
        p_onset_idx = max(p_search_start, p_peak_idx - int(0.06 * sample_rate))
        p_offset_idx = min(p_search_end, p_peak_idx + int(0.06 * sample_rate))

        p_onset = WaveformPoint(
            time_ms=time_ms[p_onset_idx],
            voltage_mv=voltage[p_onset_idx],
            point_type="P_onset",
        )

        p_offset = WaveformPoint(
            time_ms=time_ms[p_offset_idx],
            voltage_mv=voltage[p_offset_idx],
            point_type="P_offset",
        )

        return PWave(onset=p_onset, peak=p_peak, offset=p_offset)

    def _detect_t_wave(
        self,
        time_ms: np.ndarray,
        voltage: np.ndarray,
        qrs: QRSComplex,
        all_r_peaks: np.ndarray,
        beat_idx: int
    ) -> Optional[TWave]:
        """Detect T wave after QRS"""

        if qrs.s_offset is None:
            return None

        sample_rate = len(time_ms) / (time_ms[-1] - time_ms[0]) * 1000

        # T wave is typically 100-400ms after QRS
        qrs_offset_idx = np.searchsorted(time_ms, qrs.s_offset.time_ms)
        t_search_start = qrs_offset_idx + int(0.08 * sample_rate)

        # Don't search past next R peak
        if beat_idx < len(all_r_peaks) - 1:
            next_r = all_r_peaks[beat_idx + 1]
            t_search_end = min(next_r - int(0.1 * sample_rate), qrs_offset_idx + int(0.5 * sample_rate))
        else:
            t_search_end = min(len(voltage), qrs_offset_idx + int(0.5 * sample_rate))

        if t_search_end <= t_search_start:
            return None

        t_region = voltage[t_search_start:t_search_end]

        if len(t_region) < 3:
            return None

        # Find T peak (usually positive, but can be inverted)
        # Check which is larger: max or min
        max_val = np.max(t_region)
        min_val = np.min(t_region)

        if abs(max_val) > abs(min_val):
            t_peak_local = np.argmax(t_region)
        else:
            t_peak_local = np.argmin(t_region)

        t_peak_idx = t_search_start + t_peak_local

        t_peak = WaveformPoint(
            time_ms=time_ms[t_peak_idx],
            voltage_mv=voltage[t_peak_idx],
            point_type="T_peak",
        )

        # Estimate T onset and offset
        t_onset_idx = max(t_search_start, t_peak_idx - int(0.1 * sample_rate))
        t_offset_idx = min(t_search_end, t_peak_idx + int(0.12 * sample_rate))

        t_onset = WaveformPoint(
            time_ms=time_ms[t_onset_idx],
            voltage_mv=voltage[t_onset_idx],
            point_type="T_onset",
        )

        t_offset = WaveformPoint(
            time_ms=time_ms[min(t_offset_idx, len(time_ms)-1)],
            voltage_mv=voltage[min(t_offset_idx, len(voltage)-1)],
            point_type="T_offset",
        )

        return TWave(onset=t_onset, peak=t_peak, offset=t_offset)

    def _estimate_quality(self, beats: List[Beat]) -> float:
        """Estimate detection quality"""
        if not beats:
            return 0.0

        # Check consistency of measurements
        rr_intervals = [b.rr_interval_ms for b in beats if b.rr_interval_ms]
        qrs_durations = [b.qrs.duration_ms for b in beats if b.qrs and b.qrs.duration_ms]

        score = 0.0

        # R-R regularity
        if len(rr_intervals) > 1:
            rr_cv = np.std(rr_intervals) / np.mean(rr_intervals)
            score += 0.4 * max(0, 1 - rr_cv)

        # QRS detection rate
        qrs_rate = sum(1 for b in beats if b.qrs and b.qrs.r_peak) / max(len(beats), 1)
        score += 0.3 * qrs_rate

        # QRS duration consistency
        if len(qrs_durations) > 1:
            qrs_cv = np.std(qrs_durations) / np.mean(qrs_durations)
            score += 0.3 * max(0, 1 - qrs_cv)

        return float(np.clip(score, 0, 1))
