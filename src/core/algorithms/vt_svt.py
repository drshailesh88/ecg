"""
ECG Guru - VT vs SVT Differentiation Algorithms

Implementation of validated algorithms for differentiating ventricular tachycardia (VT)
from supraventricular tachycardia (SVT) with aberrant conduction in wide complex
tachycardia.

Algorithms implemented:
1. Brugada Algorithm (1991) - 4-step precordial analysis, 89% sensitivity
2. Vereckei aVR Algorithm (2008) - Single-lead aVR analysis, 69-94% accuracy
3. Basel Algorithm (2022) - Fastest 3-criteria approach, 91-93% accuracy
4. Pava Algorithm (2010) - Lead II R-wave peak time, 85%+ accuracy

References:
- Brugada P, et al. Circulation 1991;83:1649-59
- Vereckei A, et al. Heart Rhythm 2008;5:89-98
- Basel Algorithm: JACC Clin Electrophysiol 2022
- Pava LF, et al. Heart Rhythm 2010

CRITICAL: These algorithms are for educational and decision support purposes only.
They do NOT replace clinical judgment. All wide complex tachycardias should be
treated as VT until proven otherwise in the clinical setting.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class Conclusion(Enum):
    """Algorithm conclusion for VT vs SVT differentiation."""
    VT = "VT"
    SVT = "SVT"
    INDETERMINATE = "Indeterminate"


@dataclass
class StepResult:
    """
    Result of a single step in an algorithm.

    Attributes:
        step_number: Sequential step number (1-indexed)
        criterion: Description of what this step evaluates
        measured_value: The actual value measured/observed (can be any type)
        threshold: The threshold or criteria for decision (can be any type)
        result: Whether this step is positive, negative, or not evaluated
        reasoning: Human-readable explanation of this step's evaluation
    """
    step_number: int
    criterion: str
    measured_value: Any
    threshold: Any
    result: str  # "positive", "negative", "not_evaluated"
    reasoning: str


@dataclass
class AlgorithmResult:
    """
    Complete result from a VT/SVT differentiation algorithm.

    Attributes:
        name: Name of the algorithm (e.g., "Brugada", "Vereckei")
        conclusion: Final diagnosis (VT, SVT, or Indeterminate)
        confidence: Confidence score 0-1 (based on data completeness and clarity)
        supports_vt: Whether this algorithm's result supports VT
        supports_svt: Whether this algorithm's result supports SVT
        steps: List of individual step results showing the evaluation process
        missing_data: List of required measurements that were missing/unavailable
        warnings: Any warnings or caveats about this result
    """
    name: str
    conclusion: str
    confidence: float
    supports_vt: bool
    supports_svt: bool
    steps: List[StepResult] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "supports_vt": self.supports_vt,
            "supports_svt": self.supports_svt,
            "steps": [
                {
                    "step_number": step.step_number,
                    "criterion": step.criterion,
                    "measured_value": step.measured_value,
                    "threshold": step.threshold,
                    "result": step.result,
                    "reasoning": step.reasoning
                }
                for step in self.steps
            ],
            "missing_data": self.missing_data,
            "warnings": self.warnings
        }


class BrugadaAlgorithm:
    """
    Brugada Algorithm for VT vs SVT differentiation (1991).

    This is a stepwise approach examining precordial leads V1-V6.
    If ANY step is positive, the diagnosis is VT.

    Steps:
    1. Absence of RS complex in ALL precordial leads
    2. RS interval > 100ms in ANY precordial lead
    3. AV dissociation present
    4. Morphology criteria for VT in V1/V2 and V6

    Sensitivity: 89% for VT
    Specificity: Variable in external validation
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Brugada algorithm.

        Args:
            config: Optional configuration parameters (reserved for future use)
        """
        self.config = config or {}
        self.name = "Brugada Algorithm"

    def evaluate(self, measurements: Dict) -> AlgorithmResult:
        """
        Evaluate ECG measurements using the Brugada algorithm.

        Args:
            measurements: Dictionary containing ECG measurements with structure:
                {
                    "leads": {
                        "V1": {"has_rs_complex": bool, "rs_interval_ms": float, ...},
                        "V2": {...},
                        ...
                        "V6": {...}
                    },
                    "has_av_dissociation": bool or None,
                    ...
                }

        Returns:
            AlgorithmResult with conclusion and step-by-step reasoning
        """
        steps = []
        missing_data = []
        warnings = []
        confidence = 1.0

        leads_data = measurements.get("leads", {})
        precordial_leads = ["V1", "V2", "V3", "V4", "V5", "V6"]

        # Step 1: Absence of RS complex in ALL precordial leads
        step1_result = self._evaluate_step1(leads_data, precordial_leads)
        steps.append(step1_result)

        if step1_result.measured_value is None:
            missing_data.append("RS complex presence in precordial leads")
            confidence *= 0.7
        elif step1_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 2: RS interval > 100ms in ANY precordial lead
        step2_result = self._evaluate_step2(leads_data, precordial_leads)
        steps.append(step2_result)

        if step2_result.measured_value is None:
            missing_data.append("RS interval measurements in precordial leads")
            confidence *= 0.7
        elif step2_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 3: AV dissociation
        step3_result = self._evaluate_step3(measurements)
        steps.append(step3_result)

        if step3_result.measured_value is None:
            missing_data.append("AV dissociation assessment")
            confidence *= 0.8
        elif step3_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 4: Morphology criteria
        step4_result = self._evaluate_step4(leads_data)
        steps.append(step4_result)

        if step4_result.measured_value is None:
            missing_data.append("Morphology criteria in V1, V2, V6")
            confidence *= 0.6
            conclusion = Conclusion.INDETERMINATE.value
            warnings.append("Insufficient data for morphology criteria evaluation")
        elif step4_result.result == "positive":
            conclusion = Conclusion.VT.value
        else:
            conclusion = Conclusion.SVT.value

        return AlgorithmResult(
            name=self.name,
            conclusion=conclusion,
            confidence=confidence,
            supports_vt=(conclusion == Conclusion.VT.value),
            supports_svt=(conclusion == Conclusion.SVT.value),
            steps=steps,
            missing_data=missing_data,
            warnings=warnings
        )

    def _evaluate_step1(self, leads_data: Dict, precordial_leads: List[str]) -> StepResult:
        """Step 1: Check for absence of RS complex in ALL precordial leads."""
        rs_complex_present = []

        for lead in precordial_leads:
            if lead in leads_data:
                has_rs = leads_data[lead].get("has_rs_complex")
                if has_rs is not None:
                    rs_complex_present.append(has_rs)

        if not rs_complex_present:
            return StepResult(
                step_number=1,
                criterion="Absence of RS complex in ALL precordial leads (V1-V6)",
                measured_value=None,
                threshold="No RS complex in any precordial lead",
                result="not_evaluated",
                reasoning="Cannot evaluate - RS complex data not available for precordial leads"
            )

        # If ANY lead has RS complex, this step is negative
        has_any_rs = any(rs_complex_present)

        if not has_any_rs:
            return StepResult(
                step_number=1,
                criterion="Absence of RS complex in ALL precordial leads (V1-V6)",
                measured_value="No RS complex in any precordial lead",
                threshold="Absence indicates VT",
                result="positive",
                reasoning="No RS complex found in all precordial leads. This indicates abnormal ventricular depolarization consistent with VT."
            )
        else:
            return StepResult(
                step_number=1,
                criterion="Absence of RS complex in ALL precordial leads (V1-V6)",
                measured_value=f"RS complex present in {sum(rs_complex_present)} of {len(rs_complex_present)} leads",
                threshold="Absence indicates VT",
                result="negative",
                reasoning="RS complex is present in at least one precordial lead. Proceed to next step."
            )

    def _evaluate_step2(self, leads_data: Dict, precordial_leads: List[str]) -> StepResult:
        """Step 2: Check for RS interval > 100ms in ANY precordial lead."""
        rs_intervals = []
        max_rs_interval = None
        max_rs_lead = None

        for lead in precordial_leads:
            if lead in leads_data:
                rs_interval = leads_data[lead].get("rs_interval_ms")
                if rs_interval is not None:
                    rs_intervals.append((lead, rs_interval))
                    if max_rs_interval is None or rs_interval > max_rs_interval:
                        max_rs_interval = rs_interval
                        max_rs_lead = lead

        if not rs_intervals:
            return StepResult(
                step_number=2,
                criterion="RS interval > 100ms in ANY precordial lead",
                measured_value=None,
                threshold="100ms",
                result="not_evaluated",
                reasoning="Cannot evaluate - RS interval measurements not available"
            )

        if max_rs_interval > 100:
            return StepResult(
                step_number=2,
                criterion="RS interval > 100ms in ANY precordial lead",
                measured_value=f"{max_rs_interval}ms in {max_rs_lead}",
                threshold="100ms",
                result="positive",
                reasoning=f"RS interval of {max_rs_interval}ms in lead {max_rs_lead} exceeds 100ms threshold. This indicates slow ventricular conduction consistent with VT."
            )
        else:
            return StepResult(
                step_number=2,
                criterion="RS interval > 100ms in ANY precordial lead",
                measured_value=f"Maximum {max_rs_interval}ms in {max_rs_lead}",
                threshold="100ms",
                result="negative",
                reasoning=f"All RS intervals ≤ 100ms (maximum {max_rs_interval}ms). Proceed to next step."
            )

    def _evaluate_step3(self, measurements: Dict) -> StepResult:
        """Step 3: Check for AV dissociation."""
        av_dissociation = measurements.get("has_av_dissociation")

        if av_dissociation is None:
            return StepResult(
                step_number=3,
                criterion="AV dissociation present",
                measured_value=None,
                threshold="Present = VT",
                result="not_evaluated",
                reasoning="Cannot evaluate - AV dissociation not assessed. Look for P waves marching independently of QRS complexes."
            )

        if av_dissociation:
            return StepResult(
                step_number=3,
                criterion="AV dissociation present",
                measured_value="Present",
                threshold="Present = VT",
                result="positive",
                reasoning="AV dissociation is present. This is virtually diagnostic of VT."
            )
        else:
            return StepResult(
                step_number=3,
                criterion="AV dissociation present",
                measured_value="Absent",
                threshold="Present = VT",
                result="negative",
                reasoning="No AV dissociation detected. Proceed to morphology criteria."
            )

    def _evaluate_step4(self, leads_data: Dict) -> StepResult:
        """
        Step 4: Morphology criteria for VT in V1/V2 and V6.

        This is simplified - in production, would need detailed QRS morphology analysis.
        """
        v1_data = leads_data.get("V1", {})
        v2_data = leads_data.get("V2", {})
        v6_data = leads_data.get("V6", {})

        # Check if we have morphology data
        has_morphology_data = (
            "vt_morphology_criteria_met" in v1_data or
            "vt_morphology_criteria_met" in v2_data or
            "vt_morphology_criteria_met" in v6_data
        )

        if not has_morphology_data:
            return StepResult(
                step_number=4,
                criterion="Morphology criteria for VT in V1/V2 and V6",
                measured_value=None,
                threshold="RBBB or LBBB morphology patterns",
                result="not_evaluated",
                reasoning="Cannot evaluate - detailed morphology criteria require manual assessment. Check for: RBBB morphology (R>S in V1, QS in V6) or LBBB morphology (broad R in V1, QR in V6) patterns favoring VT."
            )

        # If morphology criteria data exists, use it
        morphology_met = (
            v1_data.get("vt_morphology_criteria_met", False) or
            v2_data.get("vt_morphology_criteria_met", False) or
            v6_data.get("vt_morphology_criteria_met", False)
        )

        if morphology_met:
            return StepResult(
                step_number=4,
                criterion="Morphology criteria for VT in V1/V2 and V6",
                measured_value="VT morphology criteria present",
                threshold="Specific RBBB or LBBB patterns",
                result="positive",
                reasoning="QRS morphology in V1, V2, or V6 meets criteria for VT."
            )
        else:
            return StepResult(
                step_number=4,
                criterion="Morphology criteria for VT in V1/V2 and V6",
                measured_value="SVT morphology pattern",
                threshold="Specific RBBB or LBBB patterns",
                result="negative",
                reasoning="QRS morphology suggests SVT with aberrant conduction rather than VT."
            )


class VereckeiAlgorithm:
    """
    Vereckei aVR Algorithm for VT vs SVT differentiation (2008).

    Single-lead (aVR only) approach - faster than multi-lead algorithms.
    Sequential 4-step evaluation.

    Steps:
    1. Initial dominant R wave in aVR
    2. Initial r or q wave > 40ms in aVR
    3. Notching on initial downstroke in aVR
    4. Vi/Vt ratio ≤ 1 in aVR

    Accuracy: 69-94% depending on population
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Vereckei algorithm.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.name = "Vereckei aVR Algorithm"

    def evaluate(self, measurements: Dict) -> AlgorithmResult:
        """
        Evaluate ECG measurements using the Vereckei aVR algorithm.

        Args:
            measurements: Dictionary with lead aVR measurements

        Returns:
            AlgorithmResult with conclusion and step-by-step reasoning
        """
        steps = []
        missing_data = []
        warnings = []
        confidence = 1.0

        leads_data = measurements.get("leads", {})
        avr_data = leads_data.get("aVR", {})

        if not avr_data:
            warnings.append("No aVR data available - algorithm cannot be evaluated")
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.INDETERMINATE.value,
                confidence=0.0,
                supports_vt=False,
                supports_svt=False,
                steps=[],
                missing_data=["Lead aVR data"],
                warnings=warnings
            )

        # Step 1: Initial dominant R wave in aVR
        step1_result = self._evaluate_step1(avr_data)
        steps.append(step1_result)

        if step1_result.measured_value is None:
            missing_data.append("Initial R wave dominance in aVR")
            confidence *= 0.7
        elif step1_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 2: Initial r or q wave > 40ms
        step2_result = self._evaluate_step2(avr_data)
        steps.append(step2_result)

        if step2_result.measured_value is None:
            missing_data.append("Initial r/q wave duration in aVR")
            confidence *= 0.7
        elif step2_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 3: Notching on initial downstroke
        step3_result = self._evaluate_step3(avr_data)
        steps.append(step3_result)

        if step3_result.measured_value is None:
            missing_data.append("Notching assessment in aVR")
            confidence *= 0.7
        elif step3_result.result == "positive":
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.VT.value,
                confidence=confidence,
                supports_vt=True,
                supports_svt=False,
                steps=steps,
                missing_data=missing_data,
                warnings=warnings
            )

        # Step 4: Vi/Vt ratio
        step4_result = self._evaluate_step4(avr_data)
        steps.append(step4_result)

        if step4_result.measured_value is None:
            missing_data.append("Vi/Vt ratio in aVR")
            confidence *= 0.6
            conclusion = Conclusion.INDETERMINATE.value
            warnings.append("Insufficient data for Vi/Vt ratio calculation")
        elif step4_result.result == "positive":
            conclusion = Conclusion.VT.value
        else:
            conclusion = Conclusion.SVT.value

        return AlgorithmResult(
            name=self.name,
            conclusion=conclusion,
            confidence=confidence,
            supports_vt=(conclusion == Conclusion.VT.value),
            supports_svt=(conclusion == Conclusion.SVT.value),
            steps=steps,
            missing_data=missing_data,
            warnings=warnings
        )

    def _evaluate_step1(self, avr_data: Dict) -> StepResult:
        """Step 1: Initial dominant R wave in aVR."""
        initial_r_dominant = avr_data.get("initial_r_dominant")

        if initial_r_dominant is None:
            return StepResult(
                step_number=1,
                criterion="Initial dominant R wave in aVR",
                measured_value=None,
                threshold="R wave dominant initially",
                result="not_evaluated",
                reasoning="Cannot evaluate - initial R wave dominance not assessed"
            )

        if initial_r_dominant:
            return StepResult(
                step_number=1,
                criterion="Initial dominant R wave in aVR",
                measured_value="Initial R wave dominant",
                threshold="R wave dominant = VT",
                result="positive",
                reasoning="Initial dominant R wave in aVR indicates initial ventricular activation directed toward aVR, which is abnormal and suggests VT."
            )
        else:
            return StepResult(
                step_number=1,
                criterion="Initial dominant R wave in aVR",
                measured_value="Initial R wave not dominant",
                threshold="R wave dominant = VT",
                result="negative",
                reasoning="Initial R wave is not dominant. Proceed to next step."
            )

    def _evaluate_step2(self, avr_data: Dict) -> StepResult:
        """Step 2: Initial r or q wave > 40ms."""
        initial_deflection_ms = avr_data.get("initial_deflection_ms")

        if initial_deflection_ms is None:
            return StepResult(
                step_number=2,
                criterion="Initial r or q wave > 40ms in aVR",
                measured_value=None,
                threshold="40ms",
                result="not_evaluated",
                reasoning="Cannot evaluate - initial r/q wave duration not measured"
            )

        if initial_deflection_ms > 40:
            return StepResult(
                step_number=2,
                criterion="Initial r or q wave > 40ms in aVR",
                measured_value=f"{initial_deflection_ms}ms",
                threshold="40ms",
                result="positive",
                reasoning=f"Initial r/q wave is {initial_deflection_ms}ms, exceeding 40ms threshold. This indicates slow initial ventricular activation consistent with VT."
            )
        else:
            return StepResult(
                step_number=2,
                criterion="Initial r or q wave > 40ms in aVR",
                measured_value=f"{initial_deflection_ms}ms",
                threshold="40ms",
                result="negative",
                reasoning=f"Initial r/q wave is {initial_deflection_ms}ms, which is ≤ 40ms. Proceed to next step."
            )

    def _evaluate_step3(self, avr_data: Dict) -> StepResult:
        """Step 3: Notching on initial downstroke."""
        has_notching = avr_data.get("has_downstroke_notching")

        if has_notching is None:
            return StepResult(
                step_number=3,
                criterion="Notching on initial downstroke of predominantly negative QRS",
                measured_value=None,
                threshold="Notching present = VT",
                result="not_evaluated",
                reasoning="Cannot evaluate - notching assessment not performed"
            )

        if has_notching:
            return StepResult(
                step_number=3,
                criterion="Notching on initial downstroke of predominantly negative QRS",
                measured_value="Notching present",
                threshold="Notching present = VT",
                result="positive",
                reasoning="Notching on initial downstroke indicates slow, discontinuous ventricular activation typical of VT."
            )
        else:
            return StepResult(
                step_number=3,
                criterion="Notching on initial downstroke of predominantly negative QRS",
                measured_value="No notching",
                threshold="Notching present = VT",
                result="negative",
                reasoning="No notching detected on initial downstroke. Proceed to Vi/Vt ratio."
            )

    def _evaluate_step4(self, avr_data: Dict) -> StepResult:
        """Step 4: Vi/Vt ratio ≤ 1."""
        vi_vt_ratio = avr_data.get("vi_vt_ratio")

        if vi_vt_ratio is None:
            return StepResult(
                step_number=4,
                criterion="Vi/Vt ratio ≤ 1",
                measured_value=None,
                threshold="1.0",
                result="not_evaluated",
                reasoning="Cannot evaluate - Vi/Vt ratio not calculated. Vi = voltage at 40ms from onset, Vt = voltage at 40ms before end."
            )

        if vi_vt_ratio <= 1.0:
            return StepResult(
                step_number=4,
                criterion="Vi/Vt ratio ≤ 1",
                measured_value=f"{vi_vt_ratio:.2f}",
                threshold="1.0",
                result="positive",
                reasoning=f"Vi/Vt ratio is {vi_vt_ratio:.2f} (≤1.0). Initial activation is slower than terminal activation, suggesting VT."
            )
        else:
            return StepResult(
                step_number=4,
                criterion="Vi/Vt ratio ≤ 1",
                measured_value=f"{vi_vt_ratio:.2f}",
                threshold="1.0",
                result="negative",
                reasoning=f"Vi/Vt ratio is {vi_vt_ratio:.2f} (>1.0). This suggests SVT with aberrant conduction."
            )


class BaselAlgorithm:
    """
    Basel Algorithm for VT vs SVT differentiation (2022).

    Newest and fastest algorithm - 3 simple criteria, median 36 seconds to apply.
    Scoring system: VT if ≥2 of 3 criteria present.

    Criteria (1 point each):
    1. Clinical high-risk features (age >55 OR structural heart disease)
    2. Lead II: Time to first peak > 40ms
    3. Lead aVR: Time to first peak > 40ms

    Accuracy: 91-93%
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Basel algorithm.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.name = "Basel Algorithm"

    def evaluate(self, measurements: Dict) -> AlgorithmResult:
        """
        Evaluate ECG measurements using the Basel algorithm.

        Args:
            measurements: Dictionary with clinical and ECG data

        Returns:
            AlgorithmResult with conclusion and step-by-step reasoning
        """
        steps = []
        missing_data = []
        warnings = []
        confidence = 1.0
        score = 0

        # Step 1: Clinical high-risk features
        step1_result = self._evaluate_step1(measurements)
        steps.append(step1_result)

        if step1_result.measured_value is None:
            missing_data.append("Clinical data (age, structural heart disease)")
            confidence *= 0.8
        elif step1_result.result == "positive":
            score += 1

        # Step 2: Lead II time to first peak
        leads_data = measurements.get("leads", {})
        step2_result = self._evaluate_step2(leads_data)
        steps.append(step2_result)

        if step2_result.measured_value is None:
            missing_data.append("Time to first peak in lead II")
            confidence *= 0.7
        elif step2_result.result == "positive":
            score += 1

        # Step 3: Lead aVR time to first peak
        step3_result = self._evaluate_step3(leads_data)
        steps.append(step3_result)

        if step3_result.measured_value is None:
            missing_data.append("Time to first peak in lead aVR")
            confidence *= 0.7
        elif step3_result.result == "positive":
            score += 1

        # Determine conclusion based on score
        if len(missing_data) >= 2:
            conclusion = Conclusion.INDETERMINATE.value
            warnings.append(f"Insufficient data: missing {len(missing_data)} of 3 criteria")
        elif score >= 2:
            conclusion = Conclusion.VT.value
        else:
            conclusion = Conclusion.SVT.value

        # Add summary step
        summary_step = StepResult(
            step_number=4,
            criterion="Total Score",
            measured_value=f"{score} points",
            threshold="≥2 points = VT",
            result="positive" if score >= 2 else "negative",
            reasoning=f"Basel score: {score}/3 points. {'VT diagnosed (≥2 points)' if score >= 2 else 'SVT with aberrancy (<2 points)'}."
        )
        steps.append(summary_step)

        return AlgorithmResult(
            name=self.name,
            conclusion=conclusion,
            confidence=confidence,
            supports_vt=(conclusion == Conclusion.VT.value),
            supports_svt=(conclusion == Conclusion.SVT.value),
            steps=steps,
            missing_data=missing_data,
            warnings=warnings
        )

    def _evaluate_step1(self, measurements: Dict) -> StepResult:
        """Step 1: Clinical high-risk features."""
        age = measurements.get("age")
        has_structural_heart_disease = measurements.get("has_structural_heart_disease")

        if age is None and has_structural_heart_disease is None:
            return StepResult(
                step_number=1,
                criterion="Clinical high-risk features (age >55 OR structural heart disease)",
                measured_value=None,
                threshold="Present = +1 point",
                result="not_evaluated",
                reasoning="Cannot evaluate - age and structural heart disease data not available"
            )

        high_risk = False
        reasons = []

        if age is not None and age > 55:
            high_risk = True
            reasons.append(f"age {age} years >55")

        if has_structural_heart_disease:
            high_risk = True
            reasons.append("structural heart disease present")

        if high_risk:
            return StepResult(
                step_number=1,
                criterion="Clinical high-risk features (age >55 OR structural heart disease)",
                measured_value=f"High-risk: {', '.join(reasons)}",
                threshold="Present = +1 point",
                result="positive",
                reasoning=f"High-risk clinical features present ({', '.join(reasons)}). +1 point."
            )
        else:
            age_str = f"age {age}" if age is not None else "age unknown"
            shd_str = "no structural heart disease" if has_structural_heart_disease is False else "SHD unknown"
            return StepResult(
                step_number=1,
                criterion="Clinical high-risk features (age >55 OR structural heart disease)",
                measured_value=f"{age_str}, {shd_str}",
                threshold="Present = +1 point",
                result="negative",
                reasoning="No high-risk clinical features. 0 points."
            )

    def _evaluate_step2(self, leads_data: Dict) -> StepResult:
        """Step 2: Lead II time to first peak > 40ms."""
        lead_ii_data = leads_data.get("II", {})
        time_to_peak = lead_ii_data.get("time_to_first_peak_ms")

        if time_to_peak is None:
            return StepResult(
                step_number=2,
                criterion="Lead II: Time to first peak > 40ms",
                measured_value=None,
                threshold="40ms",
                result="not_evaluated",
                reasoning="Cannot evaluate - time to first peak in lead II not measured"
            )

        if time_to_peak > 40:
            return StepResult(
                step_number=2,
                criterion="Lead II: Time to first peak > 40ms",
                measured_value=f"{time_to_peak}ms",
                threshold="40ms",
                result="positive",
                reasoning=f"Time to first peak in lead II is {time_to_peak}ms (>40ms). +1 point."
            )
        else:
            return StepResult(
                step_number=2,
                criterion="Lead II: Time to first peak > 40ms",
                measured_value=f"{time_to_peak}ms",
                threshold="40ms",
                result="negative",
                reasoning=f"Time to first peak in lead II is {time_to_peak}ms (≤40ms). 0 points."
            )

    def _evaluate_step3(self, leads_data: Dict) -> StepResult:
        """Step 3: Lead aVR time to first peak > 40ms."""
        avr_data = leads_data.get("aVR", {})
        time_to_peak = avr_data.get("time_to_first_peak_ms")

        if time_to_peak is None:
            return StepResult(
                step_number=3,
                criterion="Lead aVR: Time to first peak > 40ms",
                measured_value=None,
                threshold="40ms",
                result="not_evaluated",
                reasoning="Cannot evaluate - time to first peak in lead aVR not measured"
            )

        if time_to_peak > 40:
            return StepResult(
                step_number=3,
                criterion="Lead aVR: Time to first peak > 40ms",
                measured_value=f"{time_to_peak}ms",
                threshold="40ms",
                result="positive",
                reasoning=f"Time to first peak in lead aVR is {time_to_peak}ms (>40ms). +1 point."
            )
        else:
            return StepResult(
                step_number=3,
                criterion="Lead aVR: Time to first peak > 40ms",
                measured_value=f"{time_to_peak}ms",
                threshold="40ms",
                result="negative",
                reasoning=f"Time to first peak in lead aVR is {time_to_peak}ms (≤40ms). 0 points."
            )


class PavaAlgorithm:
    """
    Pava Algorithm - R-wave Peak Time in Lead II (2010).

    Simplest algorithm: single measurement approach.
    Measure time from QRS onset to R-wave peak in lead II.

    Criterion: R-wave peak time ≥ 50ms indicates VT

    Accuracy: 85%+
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Pava algorithm.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.name = "Pava Algorithm"

    def evaluate(self, measurements: Dict) -> AlgorithmResult:
        """
        Evaluate ECG measurements using the Pava algorithm.

        Args:
            measurements: Dictionary with lead II measurements

        Returns:
            AlgorithmResult with conclusion and step-by-step reasoning
        """
        steps = []
        missing_data = []
        warnings = []
        confidence = 1.0

        leads_data = measurements.get("leads", {})
        lead_ii_data = leads_data.get("II", {})

        if not lead_ii_data:
            warnings.append("No lead II data available")
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.INDETERMINATE.value,
                confidence=0.0,
                supports_vt=False,
                supports_svt=False,
                steps=[],
                missing_data=["Lead II data"],
                warnings=warnings
            )

        r_peak_time = lead_ii_data.get("r_peak_time_ms")

        if r_peak_time is None:
            missing_data.append("R-wave peak time in lead II")
            return AlgorithmResult(
                name=self.name,
                conclusion=Conclusion.INDETERMINATE.value,
                confidence=0.0,
                supports_vt=False,
                supports_svt=False,
                steps=[StepResult(
                    step_number=1,
                    criterion="R-wave peak time in lead II",
                    measured_value=None,
                    threshold="50ms",
                    result="not_evaluated",
                    reasoning="Cannot evaluate - R-wave peak time not measured in lead II"
                )],
                missing_data=missing_data,
                warnings=warnings
            )

        # Evaluate the criterion
        if r_peak_time >= 50:
            conclusion = Conclusion.VT.value
            result = "positive"
            reasoning = f"R-wave peak time is {r_peak_time}ms (≥50ms). This indicates VT."
        else:
            conclusion = Conclusion.SVT.value
            result = "negative"
            reasoning = f"R-wave peak time is {r_peak_time}ms (<50ms). This suggests SVT with aberrant conduction."

        step = StepResult(
            step_number=1,
            criterion="R-wave peak time ≥ 50ms in lead II",
            measured_value=f"{r_peak_time}ms",
            threshold="50ms",
            result=result,
            reasoning=reasoning
        )
        steps.append(step)

        return AlgorithmResult(
            name=self.name,
            conclusion=conclusion,
            confidence=confidence,
            supports_vt=(conclusion == Conclusion.VT.value),
            supports_svt=(conclusion == Conclusion.SVT.value),
            steps=steps,
            missing_data=missing_data,
            warnings=warnings
        )


class VTSVTEnsemble:
    """
    Ensemble of all VT vs SVT differentiation algorithms.

    Runs all 4 algorithms (Brugada, Vereckei, Basel, Pava) and provides:
    - Individual results from each algorithm
    - Weighted consensus diagnosis
    - Agreement/disagreement analysis
    - Confidence-weighted final conclusion

    This approach mirrors clinical practice where multiple algorithms
    are considered together for diagnostic certainty.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the ensemble.

        Args:
            config: Optional configuration with algorithm weights
                   Default weights: Basel=1.2 (newest), Brugada=1.0, Vereckei=0.9, Pava=0.8
        """
        self.config = config or {}

        # Algorithm weights (can be customized)
        self.weights = self.config.get("weights", {
            "Basel": 1.2,      # Newest, highest accuracy
            "Brugada": 1.0,    # Classic, well-validated
            "Vereckei": 0.9,   # Single-lead, variable accuracy
            "Pava": 0.8        # Simplest, good screening
        })

        # Initialize algorithms
        self.algorithms = {
            "Brugada": BrugadaAlgorithm(),
            "Vereckei": VereckeiAlgorithm(),
            "Basel": BaselAlgorithm(),
            "Pava": PavaAlgorithm()
        }

    def evaluate(self, measurements: Dict) -> Dict:
        """
        Run all algorithms and produce ensemble result.

        Args:
            measurements: Complete ECG measurements dictionary

        Returns:
            Dictionary containing:
                - individual_results: List of AlgorithmResult from each algorithm
                - consensus: Weighted consensus conclusion
                - confidence: Overall confidence in consensus
                - agreement: Analysis of algorithm agreement
                - recommendation: Clinical recommendation based on results
        """
        # Run all algorithms
        individual_results = {}
        for name, algorithm in self.algorithms.items():
            try:
                result = algorithm.evaluate(measurements)
                individual_results[name] = result
            except Exception as e:
                # Handle gracefully if an algorithm fails
                individual_results[name] = AlgorithmResult(
                    name=name,
                    conclusion=Conclusion.INDETERMINATE.value,
                    confidence=0.0,
                    supports_vt=False,
                    supports_svt=False,
                    steps=[],
                    missing_data=[],
                    warnings=[f"Algorithm failed: {str(e)}"]
                )

        # Calculate weighted consensus
        consensus_data = self._calculate_consensus(individual_results)

        # Analyze agreement
        agreement_analysis = self._analyze_agreement(individual_results)

        # Generate clinical recommendation
        recommendation = self._generate_recommendation(
            consensus_data,
            agreement_analysis,
            individual_results
        )

        return {
            "individual_results": {
                name: result.to_dict()
                for name, result in individual_results.items()
            },
            "consensus": consensus_data["conclusion"],
            "confidence": consensus_data["confidence"],
            "agreement": agreement_analysis,
            "recommendation": recommendation,
            "summary": self._generate_summary(
                individual_results,
                consensus_data,
                agreement_analysis
            )
        }

    def _calculate_consensus(self, results: Dict[str, AlgorithmResult]) -> Dict:
        """Calculate weighted consensus from individual algorithm results."""
        vt_score = 0.0
        svt_score = 0.0
        total_weight = 0.0

        for name, result in results.items():
            weight = self.weights.get(name, 1.0)
            effective_weight = weight * result.confidence

            if result.supports_vt:
                vt_score += effective_weight
            elif result.supports_svt:
                svt_score += effective_weight

            if result.conclusion != Conclusion.INDETERMINATE.value:
                total_weight += effective_weight

        if total_weight == 0:
            return {
                "conclusion": Conclusion.INDETERMINATE.value,
                "confidence": 0.0,
                "vt_score": 0.0,
                "svt_score": 0.0
            }

        # Normalize scores
        vt_probability = vt_score / total_weight if total_weight > 0 else 0
        svt_probability = svt_score / total_weight if total_weight > 0 else 0

        # Determine consensus
        if vt_probability > 0.6:
            conclusion = Conclusion.VT.value
            confidence = vt_probability
        elif svt_probability > 0.6:
            conclusion = Conclusion.SVT.value
            confidence = svt_probability
        else:
            conclusion = Conclusion.INDETERMINATE.value
            confidence = 1.0 - abs(vt_probability - svt_probability)

        return {
            "conclusion": conclusion,
            "confidence": round(confidence, 3),
            "vt_score": round(vt_score, 3),
            "svt_score": round(svt_score, 3),
            "vt_probability": round(vt_probability, 3),
            "svt_probability": round(svt_probability, 3)
        }

    def _analyze_agreement(self, results: Dict[str, AlgorithmResult]) -> Dict:
        """Analyze agreement and disagreement between algorithms."""
        vt_algorithms = []
        svt_algorithms = []
        indeterminate_algorithms = []

        for name, result in results.items():
            if result.conclusion == Conclusion.VT.value:
                vt_algorithms.append(name)
            elif result.conclusion == Conclusion.SVT.value:
                svt_algorithms.append(name)
            else:
                indeterminate_algorithms.append(name)

        total_conclusive = len(vt_algorithms) + len(svt_algorithms)

        if total_conclusive == 0:
            agreement_level = "none"
            agreement_percentage = 0
        elif len(vt_algorithms) == total_conclusive or len(svt_algorithms) == total_conclusive:
            agreement_level = "complete"
            agreement_percentage = 100
        elif max(len(vt_algorithms), len(svt_algorithms)) / total_conclusive >= 0.75:
            agreement_level = "strong"
            agreement_percentage = int((max(len(vt_algorithms), len(svt_algorithms)) / total_conclusive) * 100)
        elif max(len(vt_algorithms), len(svt_algorithms)) / total_conclusive >= 0.5:
            agreement_level = "moderate"
            agreement_percentage = int((max(len(vt_algorithms), len(svt_algorithms)) / total_conclusive) * 100)
        else:
            agreement_level = "poor"
            agreement_percentage = int((max(len(vt_algorithms), len(svt_algorithms)) / total_conclusive) * 100)

        return {
            "vt_count": len(vt_algorithms),
            "svt_count": len(svt_algorithms),
            "indeterminate_count": len(indeterminate_algorithms),
            "vt_algorithms": vt_algorithms,
            "svt_algorithms": svt_algorithms,
            "indeterminate_algorithms": indeterminate_algorithms,
            "agreement_level": agreement_level,
            "agreement_percentage": agreement_percentage
        }

    def _generate_recommendation(
        self,
        consensus: Dict,
        agreement: Dict,
        results: Dict[str, AlgorithmResult]
    ) -> str:
        """Generate clinical recommendation based on ensemble results."""
        conclusion = consensus["conclusion"]
        confidence = consensus["confidence"]
        agreement_level = agreement["agreement_level"]

        # CRITICAL SAFETY: Default to treating as VT in ambiguous cases
        if conclusion == Conclusion.INDETERMINATE.value or confidence < 0.6:
            return (
                "TREAT AS VT: Insufficient certainty for SVT diagnosis. "
                "All wide complex tachycardias should be treated as VT until proven otherwise. "
                "Consider procainamide, amiodarone, or electrical cardioversion as appropriate."
            )

        if conclusion == Conclusion.VT.value:
            if agreement_level in ["complete", "strong"] and confidence >= 0.8:
                return (
                    "HIGH CONFIDENCE VT: Multiple algorithms strongly support VT diagnosis. "
                    "Immediate treatment indicated. Consider antiarrhythmic therapy "
                    "(procainamide, amiodarone) or electrical cardioversion as clinically appropriate."
                )
            elif confidence >= 0.7:
                return (
                    "PROBABLE VT: Algorithms favor VT diagnosis. Treat as VT. "
                    "Consider antiarrhythmic therapy or cardioversion."
                )
            else:
                return (
                    "POSSIBLE VT: Some algorithms support VT. Given the potential severity, "
                    "recommend treating as VT until proven otherwise."
                )

        else:  # SVT
            if agreement_level in ["complete", "strong"] and confidence >= 0.8:
                # Even with high confidence SVT, maintain clinical caution
                return (
                    "PROBABLE SVT WITH ABERRANCY: Multiple algorithms support SVT diagnosis. "
                    "However, maintain clinical vigilance. If patient unstable, treat as VT. "
                    "If stable, consider adenosine (diagnostic and potentially therapeutic) "
                    "or rate control strategies."
                )
            else:
                return (
                    "POSSIBLE SVT: Some algorithms suggest SVT with aberrancy, but certainty is limited. "
                    "If clinical context supports SVT (young patient, no structural heart disease, "
                    "history of SVT), may trial adenosine. Otherwise, treat as VT to be safe."
                )

    def _generate_summary(
        self,
        results: Dict[str, AlgorithmResult],
        consensus: Dict,
        agreement: Dict
    ) -> str:
        """Generate human-readable summary of ensemble analysis."""
        summary_lines = []

        # Overall conclusion
        summary_lines.append(
            f"ENSEMBLE CONCLUSION: {consensus['conclusion']} "
            f"(confidence: {consensus['confidence']:.1%})"
        )

        # Agreement analysis
        summary_lines.append(
            f"ALGORITHM AGREEMENT: {agreement['agreement_level'].upper()} "
            f"({agreement['agreement_percentage']}%)"
        )

        # Individual results
        summary_lines.append("\nINDIVIDUAL ALGORITHMS:")
        for name in ["Basel", "Brugada", "Vereckei", "Pava"]:
            if name in results:
                result = results[name]
                conf_str = f"{result.confidence:.1%}" if result.confidence > 0 else "N/A"
                summary_lines.append(f"  • {name}: {result.conclusion} (confidence: {conf_str})")
                if result.warnings:
                    for warning in result.warnings:
                        summary_lines.append(f"    ⚠ {warning}")

        # Missing data summary
        all_missing = set()
        for result in results.values():
            all_missing.update(result.missing_data)

        if all_missing:
            summary_lines.append("\nMISSING DATA:")
            for item in sorted(all_missing):
                summary_lines.append(f"  • {item}")

        return "\n".join(summary_lines)


# Utility functions for external use

def quick_vt_svt_check(measurements: Dict) -> str:
    """
    Quick VT vs SVT check using ensemble of all algorithms.

    Args:
        measurements: ECG measurements dictionary

    Returns:
        Simple conclusion string: "VT", "SVT", or "Indeterminate"
    """
    ensemble = VTSVTEnsemble()
    result = ensemble.evaluate(measurements)
    return result["consensus"]


def detailed_vt_svt_analysis(measurements: Dict) -> Dict:
    """
    Detailed VT vs SVT analysis with all algorithm results and reasoning.

    Args:
        measurements: ECG measurements dictionary

    Returns:
        Complete ensemble result dictionary
    """
    ensemble = VTSVTEnsemble()
    return ensemble.evaluate(measurements)
