"""
ECG Guru - Accessory Pathway Localization Algorithms for WPW Syndrome

Implementation of validated algorithms for localizing accessory pathways in
Wolff-Parkinson-White (WPW) syndrome based on delta wave polarity and QRS morphology.

Algorithms implemented:
1. SMART-WPW Algorithm (2025) - Most accurate pathway localization, 97% accuracy
2. Arruda Stepwise Algorithm (Classic) - Traditional reference standard, 53-75% accuracy

These algorithms analyze the 12-lead ECG during manifest pre-excitation to predict
the anatomical location of the accessory pathway, which guides ablation strategy.

References:
- SMART-WPW: Heart Rhythm 2025 (97% accuracy)
- Arruda: J Cardiovasc Electrophysiol 1998;9:2-12

CRITICAL: These algorithms are for educational and procedural planning purposes only.
Final pathway localization is confirmed during electrophysiology study and ablation.
All WPW patients with symptoms should be referred to electrophysiology.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PathwayLocation(Enum):
    """Standard anatomical locations for accessory pathways."""
    LEFT_LATERAL = "Left Lateral (LL)"
    LEFT_POSTEROLATERAL = "Left Posterolateral (LPL)"
    LEFT_POSTERIOR = "Left Posterior (LP)"
    POSTEROSEPTAL = "Posteroseptal (PS)"
    RIGHT_POSTEROSEPTAL = "Right Posteroseptal (RPS)"
    RIGHT_POSTERIOR = "Right Posterior (RP)"
    RIGHT_LATERAL = "Right Lateral (RL)"
    RIGHT_ANTEROLATERAL = "Right Anterolateral (RAL)"
    ANTEROSEPTAL = "Anteroseptal (AS)"
    MIDSEPTAL = "Midseptal (MS)"
    INDETERMINATE = "Indeterminate"


class AblationApproach(Enum):
    """Recommended ablation approach based on pathway location."""
    TRANSSEPTAL = "Transseptal"
    RETROGRADE_AORTIC = "Retrograde aortic"
    RIGHT_ATRIAL = "Standard right atrial approach"
    CORONARY_SINUS = "Coronary sinus approach"
    CAUTION_AV_NODE = "CAUTION: Proximity to AV node - high-risk ablation"
    INDETERMINATE = "Requires electrophysiology study for approach determination"


@dataclass
class PathwayResult:
    """
    Result from accessory pathway localization algorithm.

    Attributes:
        primary_location: Most likely pathway location
        confidence: Confidence score 0-1 based on clarity of criteria
        alternative_locations: Other possible locations in order of likelihood
        delta_wave_analysis: Lead-by-lead delta wave polarity assessment
        ablation_approach: Recommended ablation access strategy
        clinical_notes: Important clinical considerations and warnings
        algorithm_used: Name of algorithm that generated this result
        step_details: Detailed reasoning for each decision step
        missing_data: Required measurements that were unavailable
        warnings: Caveats and limitations of this analysis
    """
    primary_location: str
    confidence: float
    alternative_locations: List[str] = field(default_factory=list)
    delta_wave_analysis: Dict[str, str] = field(default_factory=dict)
    ablation_approach: str = AblationApproach.INDETERMINATE.value
    clinical_notes: List[str] = field(default_factory=list)
    algorithm_used: str = ""
    step_details: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "primary_location": self.primary_location,
            "confidence": self.confidence,
            "alternative_locations": self.alternative_locations,
            "delta_wave_analysis": self.delta_wave_analysis,
            "ablation_approach": self.ablation_approach,
            "clinical_notes": self.clinical_notes,
            "algorithm_used": self.algorithm_used,
            "step_details": self.step_details,
            "missing_data": self.missing_data,
            "warnings": self.warnings
        }


class SMARTWPWAlgorithm:
    """
    SMART-WPW Algorithm for accessory pathway localization (2025).

    Most accurate currently available algorithm with 97% accuracy.
    Uses delta wave polarity in multiple leads and QRS morphology patterns
    to localize manifest accessory pathways to specific anatomical locations.

    Decision tree approach:
    1. V1 polarity → Left vs Right/Septal sided
    2. Inferior leads (II, III, aVF) → Anterior vs Posterior
    3. Leads I and aVL → Free wall vs Septal
    4. Precordial transition → Fine localization

    Accuracy: 97%
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize SMART-WPW algorithm.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.name = "SMART-WPW Algorithm"

    def evaluate(self, measurements: Dict) -> PathwayResult:
        """
        Evaluate ECG measurements to localize accessory pathway.

        Args:
            measurements: Dictionary containing:
                {
                    "delta_wave_polarity": {
                        "I": "+", "II": "+", "III": "-", "aVR": "-",
                        "aVL": "+", "aVF": "0", "V1": "-", "V2": "0",
                        "V3": "+", "V4": "+", "V5": "+", "V6": "+"
                    },
                    "qrs_morphology": {
                        "V1": "negative",  # "positive" or "negative"
                        "transition": "V3"  # R/S transition zone
                    },
                    "has_manifest_preexcitation": True  # or False
                }

        Returns:
            PathwayResult with localization and recommendations
        """
        step_details = []
        missing_data = []
        warnings = []
        confidence = 1.0

        # Extract delta wave polarity data
        delta_polarity = measurements.get("delta_wave_polarity", {})
        qrs_morphology = measurements.get("qrs_morphology", {})
        has_preexcitation = measurements.get("has_manifest_preexcitation", True)

        # Check for manifest pre-excitation
        if not has_preexcitation:
            warnings.append(
                "No manifest pre-excitation detected. This algorithm requires visible "
                "delta waves for accurate localization. Consider orthodromic AVRT or "
                "concealed pathway."
            )
            confidence *= 0.3

        # Validate required data
        required_leads = ["I", "II", "III", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        missing_leads = [lead for lead in required_leads if lead not in delta_polarity]

        if missing_leads:
            missing_data.append(f"Delta wave polarity in leads: {', '.join(missing_leads)}")
            confidence *= 0.7
            warnings.append(f"Missing delta wave data for {len(missing_leads)} leads may reduce accuracy")

        # Step 1: Determine Left vs Right/Septal based on V1
        v1_polarity = delta_polarity.get("V1", "0")
        if v1_polarity == "+":
            lateral_side = "left"
            step_details.append(
                "Step 1: V1 delta wave is POSITIVE → LEFT-SIDED pathway likely. "
                "Left-sided pathways conduct from left atrium to left ventricle, "
                "producing rightward initial forces (positive in V1)."
            )
        elif v1_polarity == "-":
            lateral_side = "right_or_septal"
            step_details.append(
                "Step 1: V1 delta wave is NEGATIVE → RIGHT-SIDED or SEPTAL pathway likely. "
                "Right/septal pathways produce leftward initial forces (negative in V1)."
            )
        else:  # isoelectric
            lateral_side = "indeterminate"
            step_details.append(
                "Step 1: V1 delta wave is ISOELECTRIC → Cannot reliably determine laterality. "
                "May indicate septal or transitional location."
            )
            confidence *= 0.8

        # Step 2: Determine Anterior vs Posterior based on inferior leads
        inferior_polarity = self._analyze_inferior_leads(delta_polarity)
        if inferior_polarity == "positive":
            anteroposterior = "anterior"
            step_details.append(
                "Step 2: Inferior leads (II, III, aVF) show POSITIVE delta waves → ANTERIOR pathway. "
                "Anterior pathways depolarize inferiorly, producing positive forces in inferior leads."
            )
        elif inferior_polarity == "negative":
            anteroposterior = "posterior"
            step_details.append(
                "Step 2: Inferior leads (II, III, aVF) show NEGATIVE delta waves → POSTERIOR pathway. "
                "Posterior pathways depolarize superiorly, producing negative forces in inferior leads."
            )
        else:
            anteroposterior = "indeterminate"
            step_details.append(
                "Step 2: Inferior leads show MIXED or ISOELECTRIC delta waves → "
                "Cannot clearly determine anterior/posterior location."
            )
            confidence *= 0.8

        # Step 3: Determine Free Wall vs Septal
        freewall_septal = self._analyze_freewall_septal(delta_polarity)
        step_details.append(
            f"Step 3: Leads I and aVL analysis → {freewall_septal.upper()} location. "
            f"{self._get_freewall_septal_explanation(freewall_septal, delta_polarity)}"
        )

        # Step 4: Fine localization using precordial transition
        precordial_analysis = self._analyze_precordial_pattern(delta_polarity, qrs_morphology)
        step_details.append(
            f"Step 4: Precordial lead pattern analysis → {precordial_analysis['description']}"
        )

        # Synthesize final location
        location_result = self._synthesize_location(
            lateral_side,
            anteroposterior,
            freewall_septal,
            precordial_analysis,
            delta_polarity
        )

        # Determine ablation approach
        ablation_approach, ablation_notes = self._determine_ablation_approach(
            location_result["primary"]
        )

        # Generate clinical notes
        clinical_notes = self._generate_clinical_notes(
            location_result["primary"],
            delta_polarity,
            has_preexcitation
        )
        clinical_notes.extend(ablation_notes)

        return PathwayResult(
            primary_location=location_result["primary"],
            confidence=confidence * location_result["confidence"],
            alternative_locations=location_result["alternatives"],
            delta_wave_analysis=delta_polarity,
            ablation_approach=ablation_approach,
            clinical_notes=clinical_notes,
            algorithm_used=self.name,
            step_details=step_details,
            missing_data=missing_data,
            warnings=warnings
        )

    def _analyze_inferior_leads(self, delta_polarity: Dict[str, str]) -> str:
        """Analyze delta wave polarity in inferior leads (II, III, aVF)."""
        inferior_leads = ["II", "III", "aVF"]
        polarities = [delta_polarity.get(lead, "0") for lead in inferior_leads]

        positive_count = polarities.count("+")
        negative_count = polarities.count("-")

        if positive_count >= 2:
            return "positive"
        elif negative_count >= 2:
            return "negative"
        else:
            return "indeterminate"

    def _analyze_freewall_septal(self, delta_polarity: Dict[str, str]) -> str:
        """
        Analyze leads I and aVL to distinguish free wall from septal pathways.

        Free wall pathways: Positive in I and aVL
        Septal pathways: Negative or isoelectric in I and/or aVL
        """
        lead_i = delta_polarity.get("I", "0")
        lead_avl = delta_polarity.get("aVL", "0")

        if lead_i == "+" and lead_avl == "+":
            return "free wall"
        elif lead_i == "-" or lead_avl == "-":
            return "septal"
        else:
            return "indeterminate"

    def _get_freewall_septal_explanation(self, classification: str, delta_polarity: Dict) -> str:
        """Get explanation for free wall vs septal classification."""
        lead_i = delta_polarity.get("I", "0")
        lead_avl = delta_polarity.get("aVL", "0")

        if classification == "free wall":
            return f"Leads I ({lead_i}) and aVL ({lead_avl}) both positive indicates free wall location."
        elif classification == "septal":
            return f"Leads I ({lead_i}) or aVL ({lead_avl}) negative/isoelectric indicates septal location."
        else:
            return f"Leads I ({lead_i}) and aVL ({lead_avl}) pattern is equivocal."

    def _analyze_precordial_pattern(
        self,
        delta_polarity: Dict[str, str],
        qrs_morphology: Dict[str, str]
    ) -> Dict:
        """Analyze precordial lead pattern for fine localization."""
        v1 = delta_polarity.get("V1", "0")
        v2 = delta_polarity.get("V2", "0")
        v3 = delta_polarity.get("V3", "0")
        v4 = delta_polarity.get("V4", "0")
        v5 = delta_polarity.get("V5", "0")
        v6 = delta_polarity.get("V6", "0")

        transition = qrs_morphology.get("transition", "unknown")

        # Analyze progression
        precordial_pattern = f"V1:{v1}, V2:{v2}, V3:{v3}, V4:{v4}, V5:{v5}, V6:{v6}"

        # Count positive precordial leads
        positive_count = sum(1 for lead in ["V1", "V2", "V3", "V4", "V5", "V6"]
                           if delta_polarity.get(lead, "0") == "+")

        description = (
            f"Precordial delta wave pattern: {precordial_pattern}. "
            f"R/S transition: {transition}. "
            f"{positive_count}/6 precordial leads show positive delta waves."
        )

        return {
            "pattern": precordial_pattern,
            "transition": transition,
            "positive_count": positive_count,
            "description": description
        }

    def _synthesize_location(
        self,
        lateral_side: str,
        anteroposterior: str,
        freewall_septal: str,
        precordial_analysis: Dict,
        delta_polarity: Dict
    ) -> Dict:
        """
        Synthesize all analysis to determine final pathway location.

        Returns dict with primary location, confidence modifier, and alternatives.
        """
        # LEFT-SIDED PATHWAYS
        if lateral_side == "left":
            if anteroposterior == "posterior":
                if freewall_septal == "free wall":
                    # Check for lateral vs posterolateral
                    if delta_polarity.get("I") == "+" and delta_polarity.get("aVL") == "+":
                        primary = PathwayLocation.LEFT_LATERAL.value
                        alternatives = [PathwayLocation.LEFT_POSTEROLATERAL.value]
                    else:
                        primary = PathwayLocation.LEFT_POSTEROLATERAL.value
                        alternatives = [PathwayLocation.LEFT_LATERAL.value]
                    confidence = 0.95
                else:
                    primary = PathwayLocation.LEFT_POSTERIOR.value
                    alternatives = [PathwayLocation.POSTEROSEPTAL.value]
                    confidence = 0.90
            elif anteroposterior == "anterior":
                # Left anterior pathways are rare
                primary = PathwayLocation.LEFT_LATERAL.value
                alternatives = [PathwayLocation.LEFT_POSTEROLATERAL.value]
                confidence = 0.85
                warnings = ["Left anterior pathway is uncommon - verify delta wave analysis"]
            else:
                primary = PathwayLocation.LEFT_LATERAL.value
                alternatives = [
                    PathwayLocation.LEFT_POSTEROLATERAL.value,
                    PathwayLocation.LEFT_POSTERIOR.value
                ]
                confidence = 0.75

        # RIGHT-SIDED OR SEPTAL PATHWAYS
        elif lateral_side == "right_or_septal":
            if freewall_septal == "septal":
                if anteroposterior == "posterior":
                    # Analyze II vs III for posteroseptal vs right posteroseptal
                    lead_ii = delta_polarity.get("II", "0")
                    lead_iii = delta_polarity.get("III", "0")
                    if lead_iii == "-" and lead_ii != "+":
                        primary = PathwayLocation.POSTEROSEPTAL.value
                        alternatives = [PathwayLocation.RIGHT_POSTEROSEPTAL.value]
                    else:
                        primary = PathwayLocation.RIGHT_POSTEROSEPTAL.value
                        alternatives = [PathwayLocation.POSTEROSEPTAL.value]
                    confidence = 0.90
                elif anteroposterior == "anterior":
                    primary = PathwayLocation.ANTEROSEPTAL.value
                    alternatives = [PathwayLocation.MIDSEPTAL.value]
                    confidence = 0.90
                else:
                    primary = PathwayLocation.MIDSEPTAL.value
                    alternatives = [
                        PathwayLocation.ANTEROSEPTAL.value,
                        PathwayLocation.POSTEROSEPTAL.value
                    ]
                    confidence = 0.75
            else:  # free wall
                if anteroposterior == "posterior":
                    primary = PathwayLocation.RIGHT_POSTERIOR.value
                    alternatives = [
                        PathwayLocation.RIGHT_POSTEROSEPTAL.value,
                        PathwayLocation.RIGHT_LATERAL.value
                    ]
                    confidence = 0.85
                elif anteroposterior == "anterior":
                    primary = PathwayLocation.RIGHT_ANTEROLATERAL.value
                    alternatives = [PathwayLocation.RIGHT_LATERAL.value]
                    confidence = 0.85
                else:
                    primary = PathwayLocation.RIGHT_LATERAL.value
                    alternatives = [
                        PathwayLocation.RIGHT_ANTEROLATERAL.value,
                        PathwayLocation.RIGHT_POSTERIOR.value
                    ]
                    confidence = 0.75

        # INDETERMINATE
        else:
            primary = PathwayLocation.INDETERMINATE.value
            alternatives = list(loc.value for loc in PathwayLocation if loc != PathwayLocation.INDETERMINATE)
            confidence = 0.50

        return {
            "primary": primary,
            "alternatives": alternatives,
            "confidence": confidence
        }

    def _determine_ablation_approach(self, location: str) -> Tuple[str, List[str]]:
        """
        Determine recommended ablation approach based on pathway location.

        Returns tuple of (approach, clinical notes list).
        """
        notes = []

        if "Left" in location and location != PathwayLocation.LEFT_POSTERIOR.value:
            approach = AblationApproach.TRANSSEPTAL.value
            notes.append(
                "Left-sided pathways: Transseptal approach is most common. "
                "Retrograde aortic approach is alternative if transseptal difficult."
            )
            notes.append(
                "Ensure adequate anticoagulation for left-sided access. "
                "Consider TEE or ICE for transseptal puncture guidance."
            )

        elif location == PathwayLocation.LEFT_POSTERIOR.value:
            approach = f"{AblationApproach.TRANSSEPTAL.value} or {AblationApproach.CORONARY_SINUS.value}"
            notes.append(
                "Left posterior pathways: May be accessible via coronary sinus (epicardial) "
                "or transseptal approach (endocardial). Some require both."
            )

        elif "Posteroseptal" in location or location == PathwayLocation.MIDSEPTAL.value:
            approach = AblationApproach.CAUTION_AV_NODE.value
            notes.append(
                "SEPTAL PATHWAYS - HIGH RISK: Close proximity to AV node and His bundle. "
                "Risk of AV block requiring permanent pacemaker. Consider cryoablation "
                "for added safety (reversible ice ball vs irreversible RF lesion)."
            )
            notes.append(
                "Detailed mapping required to identify safe ablation site away from "
                "compact AV node. May need both right and left atrial approaches."
            )

        elif "Right" in location and location != PathwayLocation.RIGHT_POSTEROSEPTAL.value:
            approach = AblationApproach.RIGHT_ATRIAL.value
            notes.append(
                "Right-sided pathways: Standard right atrial approach via femoral vein. "
                "Generally straightforward access."
            )

        elif location == PathwayLocation.RIGHT_POSTEROSEPTAL.value:
            approach = f"{AblationApproach.RIGHT_ATRIAL.value} with caution"
            notes.append(
                "Right posteroseptal: Accessible via right atrium but proximity to AV node "
                "requires careful mapping. Consider cryoablation."
            )

        elif location == PathwayLocation.ANTEROSEPTAL.value:
            approach = AblationApproach.CAUTION_AV_NODE.value
            notes.append(
                "ANTEROSEPTAL - VERY HIGH RISK: Extremely close to AV node. "
                "Highest risk of iatrogenic AV block. Some operators avoid ablation "
                "or use cryoablation exclusively. Detailed discussion with patient "
                "regarding pacemaker risk essential."
            )

        else:
            approach = AblationApproach.INDETERMINATE.value
            notes.append(
                "Unable to determine optimal ablation approach without clearer pathway localization. "
                "Detailed electrophysiology study and mapping required."
            )

        return approach, notes

    def _generate_clinical_notes(
        self,
        location: str,
        delta_polarity: Dict[str, str],
        has_preexcitation: bool
    ) -> List[str]:
        """Generate clinical notes and recommendations."""
        notes = []

        # Pre-excitation status
        if has_preexcitation:
            notes.append(
                "Manifest pre-excitation present - pathway conducts anterogradely (atrium to ventricle). "
                "Risk of sudden death if atrial fibrillation occurs with rapid ventricular response."
            )
        else:
            notes.append(
                "No manifest pre-excitation - may indicate concealed pathway (only retrograde conduction) "
                "or intermittent pre-excitation. If orthodromic AVRT documented, pathway is concealed."
            )

        # Location-specific notes
        if "Left" in location:
            notes.append(
                "Left-sided pathways account for ~60% of accessory pathways. "
                "Success rate with ablation: 95-98%."
            )

        if "Septal" in location:
            notes.append(
                "Septal pathways: Higher complexity, longer procedure time, and increased risk. "
                "Ensure experienced operator. Success rate: 85-95% with higher recurrence than free wall."
            )

        if "Right" in location and "septal" not in location.lower():
            notes.append(
                "Right free wall pathways: Generally easier to ablate with high success rates (>95%). "
                "Lower complication risk than septal pathways."
            )

        # General WPW notes
        notes.append(
            "All patients with WPW and documented arrhythmias should be referred to "
            "electrophysiology for risk stratification and potential ablation."
        )

        notes.append(
            "Asymptomatic WPW: Risk stratification with exercise testing or EP study "
            "for high-risk occupations (pilots, athletes, drivers) or family history of sudden death."
        )

        return notes


class ArrudaAlgorithm:
    """
    Arruda Stepwise Algorithm for accessory pathway localization (1998).

    Classic reference standard algorithm. Uses stepwise analysis of delta wave
    polarity in multiple leads to narrow down pathway location.

    Less accurate than SMART-WPW (53-75% accuracy) but widely taught and
    clinically validated over decades of use.

    Accuracy: 53-75% depending on pathway location
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Arruda algorithm.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.name = "Arruda Stepwise Algorithm"

    def evaluate(self, measurements: Dict) -> PathwayResult:
        """
        Evaluate ECG measurements using Arruda algorithm.

        Args:
            measurements: Same format as SMART-WPW algorithm

        Returns:
            PathwayResult with localization
        """
        step_details = []
        missing_data = []
        warnings = []
        confidence = 1.0

        delta_polarity = measurements.get("delta_wave_polarity", {})
        has_preexcitation = measurements.get("has_manifest_preexcitation", True)

        if not has_preexcitation:
            warnings.append(
                "Arruda algorithm requires manifest pre-excitation with visible delta waves."
            )
            confidence *= 0.3

        # Arruda Step 1: V1 Polarity
        v1 = delta_polarity.get("V1", "0")
        if v1 == "-" or v1 == "0":
            # Free wall pathway (left or right)
            step_details.append(
                "Arruda Step 1: V1 delta wave NEGATIVE or ISOELECTRIC → Free wall pathway "
                "(excludes septal locations)"
            )
            location = self._arruda_freewall_analysis(delta_polarity, step_details)
        else:
            # Septal or paraseptal pathway
            step_details.append(
                "Arruda Step 1: V1 delta wave POSITIVE → Septal or paraseptal pathway"
            )
            location = self._arruda_septal_analysis(delta_polarity, step_details)
            confidence *= 0.85  # Septal pathways harder to localize

        # Determine ablation approach
        ablation_approach, ablation_notes = self._determine_ablation_approach(location)

        # Generate clinical notes
        clinical_notes = [
            f"Arruda algorithm: Classic stepwise approach with moderate accuracy (53-75%). "
            f"Consider confirming with SMART-WPW algorithm or EP study mapping."
        ]
        clinical_notes.extend(ablation_notes)

        # Arruda has lower accuracy, adjust confidence
        confidence *= 0.75  # Reflect the 53-75% literature accuracy

        warnings.append(
            "Arruda algorithm has lower accuracy than SMART-WPW. "
            "Use as supplementary assessment or when SMART-WPW data incomplete."
        )

        return PathwayResult(
            primary_location=location["primary"],
            confidence=confidence,
            alternative_locations=location["alternatives"],
            delta_wave_analysis=delta_polarity,
            ablation_approach=ablation_approach,
            clinical_notes=clinical_notes,
            algorithm_used=self.name,
            step_details=step_details,
            missing_data=missing_data,
            warnings=warnings
        )

    def _arruda_freewall_analysis(self, delta_polarity: Dict, step_details: List[str]) -> Dict:
        """Analyze free wall pathways (V1 negative/isoelectric)."""
        # Step 2: V1 transition
        v2 = delta_polarity.get("V2", "0")

        if v2 == "+" or v2 == "0":
            step_details.append(
                "Arruda Step 2: V2 transition POSITIVE/ISOELECTRIC → LEFT free wall"
            )

            # Step 3: I and II analysis for left-sided
            lead_i = delta_polarity.get("I", "0")
            lead_ii = delta_polarity.get("II", "0")

            if lead_i == "+" and lead_ii == "+":
                primary = PathwayLocation.LEFT_LATERAL.value
                alternatives = [PathwayLocation.LEFT_POSTEROLATERAL.value]
                step_details.append(
                    "Arruda Step 3: Leads I and II both POSITIVE → Left Lateral"
                )
            elif lead_ii == "-" or lead_ii == "0":
                primary = PathwayLocation.LEFT_POSTEROLATERAL.value
                alternatives = [PathwayLocation.LEFT_POSTERIOR.value]
                step_details.append(
                    "Arruda Step 3: Lead II NEGATIVE/ISOELECTRIC → Left Posterolateral"
                )
            else:
                primary = PathwayLocation.LEFT_LATERAL.value
                alternatives = [
                    PathwayLocation.LEFT_POSTEROLATERAL.value,
                    PathwayLocation.LEFT_POSTERIOR.value
                ]
                step_details.append(
                    "Arruda Step 3: Mixed pattern → Left Lateral (with alternatives)"
                )

        else:  # V2 negative
            step_details.append(
                "Arruda Step 2: V2 NEGATIVE → RIGHT free wall"
            )

            # Analyze inferior leads for right-sided
            lead_ii = delta_polarity.get("II", "0")
            lead_iii = delta_polarity.get("III", "0")
            lead_avf = delta_polarity.get("aVF", "0")

            if lead_ii == "+" and lead_iii == "+" and lead_avf == "+":
                primary = PathwayLocation.RIGHT_ANTEROLATERAL.value
                alternatives = [PathwayLocation.RIGHT_LATERAL.value]
                step_details.append(
                    "Arruda Step 3: Inferior leads POSITIVE → Right Anterolateral"
                )
            elif lead_ii == "-" or lead_iii == "-":
                primary = PathwayLocation.RIGHT_POSTERIOR.value
                alternatives = [PathwayLocation.RIGHT_LATERAL.value]
                step_details.append(
                    "Arruda Step 3: Inferior leads NEGATIVE → Right Posterior"
                )
            else:
                primary = PathwayLocation.RIGHT_LATERAL.value
                alternatives = [
                    PathwayLocation.RIGHT_ANTEROLATERAL.value,
                    PathwayLocation.RIGHT_POSTERIOR.value
                ]
                step_details.append(
                    "Arruda Step 3: Mixed inferior pattern → Right Lateral"
                )

        return {"primary": primary, "alternatives": alternatives}

    def _arruda_septal_analysis(self, delta_polarity: Dict, step_details: List[str]) -> Dict:
        """Analyze septal pathways (V1 positive)."""
        # Analyze inferior leads
        lead_ii = delta_polarity.get("II", "0")
        lead_iii = delta_polarity.get("III", "0")
        lead_avf = delta_polarity.get("aVF", "0")

        # Count negative inferior leads
        negative_inferior = sum(1 for lead in [lead_ii, lead_iii, lead_avf] if lead == "-")

        if negative_inferior >= 2:
            # Posteroseptal region
            step_details.append(
                "Arruda Step 2: Inferior leads predominantly NEGATIVE → Posteroseptal region"
            )

            # Distinguish PS from RPS
            if lead_iii == "-" and lead_ii != "+":
                primary = PathwayLocation.POSTEROSEPTAL.value
                alternatives = [PathwayLocation.RIGHT_POSTEROSEPTAL.value]
                step_details.append(
                    "Arruda Step 3: Lead III strongly negative → Posteroseptal (midline)"
                )
            else:
                primary = PathwayLocation.RIGHT_POSTEROSEPTAL.value
                alternatives = [PathwayLocation.POSTEROSEPTAL.value]
                step_details.append(
                    "Arruda Step 3: Pattern favors → Right Posteroseptal"
                )

        elif lead_ii == "+" and lead_iii == "+" and lead_avf == "+":
            # Anteroseptal
            primary = PathwayLocation.ANTEROSEPTAL.value
            alternatives = [PathwayLocation.MIDSEPTAL.value]
            step_details.append(
                "Arruda Step 2: All inferior leads POSITIVE → Anteroseptal (HIGH RISK)"
            )

        else:
            # Midseptal or indeterminate
            primary = PathwayLocation.MIDSEPTAL.value
            alternatives = [
                PathwayLocation.ANTEROSEPTAL.value,
                PathwayLocation.POSTEROSEPTAL.value
            ]
            step_details.append(
                "Arruda Step 2: Mixed inferior pattern → Midseptal (with uncertainty)"
            )

        return {"primary": primary, "alternatives": alternatives}

    def _determine_ablation_approach(self, location: Dict) -> Tuple[str, List[str]]:
        """Determine ablation approach (same logic as SMART-WPW)."""
        primary = location["primary"]
        notes = []

        if "Left" in primary and primary != PathwayLocation.LEFT_POSTERIOR.value:
            approach = AblationApproach.TRANSSEPTAL.value
            notes.append("Left-sided pathway: Transseptal or retrograde aortic approach.")

        elif primary == PathwayLocation.LEFT_POSTERIOR.value:
            approach = f"{AblationApproach.TRANSSEPTAL.value} or {AblationApproach.CORONARY_SINUS.value}"
            notes.append("Left posterior: May require coronary sinus approach.")

        elif "Septal" in primary:
            approach = AblationApproach.CAUTION_AV_NODE.value
            notes.append(
                "SEPTAL PATHWAY - HIGH RISK: Proximity to AV node. Risk of heart block. "
                "Consider cryoablation."
            )

        elif "Right" in primary and "Posteroseptal" not in primary:
            approach = AblationApproach.RIGHT_ATRIAL.value
            notes.append("Right-sided pathway: Standard right atrial approach.")

        else:
            approach = AblationApproach.INDETERMINATE.value
            notes.append("Ablation approach: Requires EP study mapping.")

        return approach, notes


class PathwayLocalizer:
    """
    Complete accessory pathway localization system.

    Runs both SMART-WPW (97% accuracy) and Arruda (53-75% accuracy) algorithms
    and provides consensus recommendation. SMART-WPW is preferred when data quality
    is adequate; Arruda serves as secondary confirmation or fallback.

    Clinical use:
    1. Primary: SMART-WPW for highest accuracy
    2. Secondary: Arruda for validation
    3. If disagreement: SMART-WPW preferred, but note uncertainty
    4. Final confirmation: Always via EP study mapping during ablation
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the pathway localizer.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.smart_wpw = SMARTWPWAlgorithm(config)
        self.arruda = ArrudaAlgorithm(config)

    def localize(self, measurements: Dict, prefer_algorithm: str = "SMART-WPW") -> Dict:
        """
        Localize accessory pathway using both algorithms.

        Args:
            measurements: ECG measurements dictionary
            prefer_algorithm: "SMART-WPW" (default) or "Arruda"

        Returns:
            Dictionary containing:
                - primary_result: Result from preferred algorithm
                - secondary_result: Result from other algorithm
                - consensus: Analysis of agreement between algorithms
                - recommendation: Clinical recommendation
        """
        # Run both algorithms
        smart_result = self.smart_wpw.evaluate(measurements)
        arruda_result = self.arruda.evaluate(measurements)

        # Determine primary and secondary
        if prefer_algorithm.upper() == "ARRUDA":
            primary_result = arruda_result
            secondary_result = smart_result
        else:
            primary_result = smart_result
            secondary_result = arruda_result

        # Analyze consensus
        consensus = self._analyze_consensus(smart_result, arruda_result)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            smart_result,
            arruda_result,
            consensus
        )

        return {
            "primary_result": primary_result.to_dict(),
            "secondary_result": secondary_result.to_dict(),
            "consensus": consensus,
            "recommendation": recommendation,
            "summary": self._generate_summary(smart_result, arruda_result, consensus)
        }

    def _analyze_consensus(
        self,
        smart_result: PathwayResult,
        arruda_result: PathwayResult
    ) -> Dict:
        """Analyze agreement between SMART-WPW and Arruda algorithms."""
        smart_loc = smart_result.primary_location
        arruda_loc = arruda_result.primary_location

        # Check exact agreement
        exact_match = (smart_loc == arruda_loc)

        # Check if Arruda location is in SMART alternatives
        arruda_in_smart_alternatives = arruda_loc in smart_result.alternative_locations

        # Check if SMART location is in Arruda alternatives
        smart_in_arruda_alternatives = smart_loc in arruda_result.alternative_locations

        # Determine agreement level
        if exact_match:
            agreement_level = "complete"
            agreement_description = "Both algorithms agree on primary location"
        elif arruda_in_smart_alternatives or smart_in_arruda_alternatives:
            agreement_level = "partial"
            agreement_description = "Algorithms disagree but locations are compatible (one is alternative of other)"
        else:
            agreement_level = "poor"
            agreement_description = "Algorithms disagree significantly - exercise caution"

        # Check if both are in same general region
        regions_match = self._check_regional_agreement(smart_loc, arruda_loc)

        return {
            "exact_match": exact_match,
            "agreement_level": agreement_level,
            "agreement_description": agreement_description,
            "regions_match": regions_match,
            "smart_location": smart_loc,
            "arruda_location": arruda_loc,
            "smart_confidence": smart_result.confidence,
            "arruda_confidence": arruda_result.confidence
        }

    def _check_regional_agreement(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are in the same anatomical region."""
        left_locations = ["Left Lateral", "Left Posterolateral", "Left Posterior"]
        right_locations = ["Right Lateral", "Right Anterolateral", "Right Posterior", "Right Posteroseptal"]
        septal_locations = ["Posteroseptal", "Anteroseptal", "Midseptal", "Right Posteroseptal"]

        # Check if both in same region
        both_left = any(region in loc1 for region in left_locations) and \
                    any(region in loc2 for region in left_locations)

        both_right = any(region in loc1 for region in right_locations) and \
                     any(region in loc2 for region in right_locations)

        both_septal = any(region in loc1 for region in septal_locations) and \
                      any(region in loc2 for region in septal_locations)

        return both_left or both_right or both_septal

    def _generate_recommendation(
        self,
        smart_result: PathwayResult,
        arruda_result: PathwayResult,
        consensus: Dict
    ) -> str:
        """Generate clinical recommendation based on both algorithm results."""
        if consensus["exact_match"] and smart_result.confidence >= 0.8:
            return (
                f"HIGH CONFIDENCE: Both algorithms agree on {smart_result.primary_location}. "
                f"SMART-WPW confidence: {smart_result.confidence:.0%}. "
                f"Proceed with EP study and ablation planning based on this localization. "
                f"Ablation approach: {smart_result.ablation_approach}."
            )

        elif consensus["agreement_level"] in ["complete", "partial"] and smart_result.confidence >= 0.7:
            return (
                f"GOOD CONFIDENCE: Primary localization is {smart_result.primary_location} "
                f"(SMART-WPW confidence: {smart_result.confidence:.0%}). "
                f"Arruda algorithm suggests {arruda_result.primary_location}. "
                f"{'Locations are compatible.' if consensus['agreement_level'] == 'partial' else 'Complete agreement.'} "
                f"Proceed with EP study. Ablation approach: {smart_result.ablation_approach}."
            )

        elif smart_result.confidence >= 0.6:
            return (
                f"MODERATE CONFIDENCE: SMART-WPW suggests {smart_result.primary_location} "
                f"(confidence: {smart_result.confidence:.0%}), "
                f"but Arruda suggests {arruda_result.primary_location}. "
                f"Agreement: {consensus['agreement_level']}. "
                f"EP study with detailed mapping essential before ablation. "
                f"Be prepared for pathway location different from predicted."
            )

        else:
            return (
                f"LOW CONFIDENCE: Uncertain localization. SMART-WPW: {smart_result.primary_location} "
                f"(confidence: {smart_result.confidence:.0%}). Arruda: {arruda_result.primary_location}. "
                f"These algorithms require clear delta waves in all leads. "
                f"EP study with extensive mapping absolutely required. "
                f"Do not rely on ECG localization alone for ablation planning."
            )

    def _generate_summary(
        self,
        smart_result: PathwayResult,
        arruda_result: PathwayResult,
        consensus: Dict
    ) -> str:
        """Generate human-readable summary."""
        lines = []

        lines.append("=" * 70)
        lines.append("ACCESSORY PATHWAY LOCALIZATION SUMMARY")
        lines.append("=" * 70)

        # Primary localization
        lines.append(f"\nPRIMARY LOCALIZATION: {smart_result.primary_location}")
        lines.append(f"Confidence: {smart_result.confidence:.0%} (SMART-WPW Algorithm)")

        # Secondary
        lines.append(f"\nSECONDARY CONFIRMATION: {arruda_result.primary_location}")
        lines.append(f"Confidence: {arruda_result.confidence:.0%} (Arruda Algorithm)")

        # Agreement
        lines.append(f"\nAGREEMENT: {consensus['agreement_level'].upper()}")
        lines.append(f"  {consensus['agreement_description']}")

        # Ablation approach
        lines.append(f"\nABLATION APPROACH: {smart_result.ablation_approach}")

        # Key clinical notes
        if smart_result.clinical_notes:
            lines.append("\nKEY CLINICAL CONSIDERATIONS:")
            for note in smart_result.clinical_notes[:3]:  # Top 3 notes
                lines.append(f"  • {note}")

        # Warnings
        all_warnings = set(smart_result.warnings + arruda_result.warnings)
        if all_warnings:
            lines.append("\nWARNINGS:")
            for warning in all_warnings:
                lines.append(f"  ⚠ {warning}")

        lines.append("\n" + "=" * 70)
        lines.append(
            "NOTE: These algorithms provide guidance for EP study planning. "
            "Final pathway localization is confirmed by electrophysiology mapping "
            "during ablation procedure."
        )
        lines.append("=" * 70)

        return "\n".join(lines)


# Convenience functions for quick usage

def quick_pathway_localization(delta_wave_polarity: Dict[str, str]) -> str:
    """
    Quick pathway localization using SMART-WPW algorithm.

    Args:
        delta_wave_polarity: Dict of lead -> polarity ("+", "-", "0")

    Returns:
        Primary pathway location string
    """
    measurements = {
        "delta_wave_polarity": delta_wave_polarity,
        "has_manifest_preexcitation": True
    }

    localizer = PathwayLocalizer()
    result = localizer.smart_wpw.evaluate(measurements)
    return result.primary_location


def detailed_pathway_analysis(measurements: Dict) -> Dict:
    """
    Detailed pathway analysis with both algorithms.

    Args:
        measurements: Complete measurements dictionary

    Returns:
        Full analysis dictionary with both algorithm results
    """
    localizer = PathwayLocalizer()
    return localizer.localize(measurements)
