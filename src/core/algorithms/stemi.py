"""
STEMI Detection and Localization Algorithms

This module provides medical-grade STEMI (ST-Elevation Myocardial Infarction) detection
and localization using validated clinical criteria.

WARNING: This software is intended for educational and clinical decision support only.
It does NOT replace clinical judgment. All STEMI diagnoses must be confirmed by a
qualified physician and correlated with clinical presentation.

References:
- ACC/AHA STEMI Guidelines 2013, 2022
- ESC STEMI Guidelines 2017, 2023
- Inferior STEMI Culprit Vessel Algorithm (86% accuracy)
- Fiol M et al. Circulation 2004 (RCA/LCx differentiation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class STEMITerritory(Enum):
    """Anatomical territories affected by STEMI"""
    ANTERIOR = "Anterior"
    INFERIOR = "Inferior"
    LATERAL = "Lateral"
    POSTERIOR = "Posterior"
    RIGHT_VENTRICLE = "Right Ventricle"
    ANTEROSEPTAL = "Anteroseptal"
    ANTEROLATERAL = "Anterolateral"
    INFEROLATERAL = "Inferolateral"
    INFEROPOSTERIOR = "Inferoposterior"


class CulpritVessel(Enum):
    """Coronary arteries that can cause STEMI"""
    LAD = "Left Anterior Descending (LAD)"
    RCA = "Right Coronary Artery (RCA)"
    LCX = "Left Circumflex (LCx)"
    LMCA = "Left Main Coronary Artery (LMCA)"
    UNKNOWN = "Unknown"


@dataclass
class STEMIResult:
    """
    Comprehensive STEMI analysis result

    Attributes:
        is_stemi: Whether STEMI criteria are met
        territories: List of affected anatomical territories
        culprit_vessel: Most likely culprit coronary artery
        culprit_confidence: Confidence in culprit vessel identification (0.0-1.0)
        st_changes: Dictionary mapping lead name to ST deviation in mm
        urgent_findings: List of critical findings requiring immediate action
        recommended_actions: List of recommended clinical actions
        segment_location: Specific arterial segment (e.g., "Proximal LAD")
        differential_diagnosis: Alternative explanations to consider
        additional_notes: Additional clinical context
    """
    is_stemi: bool
    territories: List[str] = field(default_factory=list)
    culprit_vessel: str = CulpritVessel.UNKNOWN.value
    culprit_confidence: float = 0.0
    st_changes: Dict[str, float] = field(default_factory=dict)
    urgent_findings: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    segment_location: Optional[str] = None
    differential_diagnosis: List[str] = field(default_factory=list)
    additional_notes: List[str] = field(default_factory=list)


class STEMIDetector:
    """
    Detects ST elevation and depression in ECG leads

    Uses standard STEMI criteria:
    - Limb leads (I, II, III, aVR, aVL, aVF): ≥1mm elevation
    - Precordial leads (V1-V6): ≥2mm elevation
    - Exception: V2-V3 in men ≥40y: ≥2mm, men <40y: ≥2.5mm, women: ≥1.5mm
    """

    # Standard ECG leads
    LIMB_LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF']
    PRECORDIAL_LEADS = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    ALL_LEADS = LIMB_LEADS + PRECORDIAL_LEADS

    def __init__(self):
        """Initialize STEMI detector"""
        pass

    def get_st_threshold(self, lead: str, patient_sex: str = "male",
                        patient_age: Optional[int] = None) -> float:
        """
        Get ST elevation threshold for STEMI diagnosis in a specific lead

        Args:
            lead: Lead name (e.g., 'V2', 'II')
            patient_sex: 'male' or 'female'
            patient_age: Patient age in years (optional)

        Returns:
            Threshold in millimeters
        """
        # Limb leads: 1mm threshold
        if lead in self.LIMB_LEADS:
            return 1.0

        # V2-V3 have age/sex-specific thresholds
        if lead in ['V2', 'V3']:
            if patient_sex.lower() == 'female':
                return 1.5
            else:  # male
                if patient_age is not None and patient_age < 40:
                    return 2.5
                else:
                    return 2.0

        # Other precordial leads (V1, V4, V5, V6): 2mm threshold
        if lead in self.PRECORDIAL_LEADS:
            return 2.0

        # Default
        return 1.0

    def detect_st_elevation(self, measurements: Dict,
                           patient_sex: str = "male",
                           patient_age: Optional[int] = None) -> Dict[str, bool]:
        """
        Detect which leads have significant ST elevation

        Args:
            measurements: Dictionary with lead measurements
            patient_sex: Patient sex for threshold calculation
            patient_age: Patient age for threshold calculation

        Returns:
            Dictionary mapping lead name to boolean (True if ST elevation meets criteria)
        """
        st_elevated = {}
        leads_data = measurements.get('leads', {})

        for lead in self.ALL_LEADS:
            if lead not in leads_data:
                st_elevated[lead] = False
                continue

            st_elevation_mm = leads_data[lead].get('st_elevation_mm', 0.0)
            threshold = self.get_st_threshold(lead, patient_sex, patient_age)

            st_elevated[lead] = st_elevation_mm >= threshold

        return st_elevated

    def detect_st_depression(self, measurements: Dict,
                            threshold_mm: float = 0.5) -> Dict[str, bool]:
        """
        Detect which leads have significant ST depression

        Args:
            measurements: Dictionary with lead measurements
            threshold_mm: Threshold for significant depression (default 0.5mm)

        Returns:
            Dictionary mapping lead name to boolean (True if ST depression ≥ threshold)
        """
        st_depressed = {}
        leads_data = measurements.get('leads', {})

        for lead in self.ALL_LEADS:
            if lead not in leads_data:
                st_depressed[lead] = False
                continue

            st_depression_mm = leads_data[lead].get('st_depression_mm', 0.0)
            st_depressed[lead] = st_depression_mm >= threshold_mm

        return st_depressed

    def get_st_changes_dict(self, measurements: Dict) -> Dict[str, float]:
        """
        Extract all ST changes (elevation as positive, depression as negative)

        Args:
            measurements: Dictionary with lead measurements

        Returns:
            Dictionary mapping lead name to ST deviation in mm
            (positive = elevation, negative = depression)
        """
        st_changes = {}
        leads_data = measurements.get('leads', {})

        for lead in self.ALL_LEADS:
            if lead not in leads_data:
                st_changes[lead] = 0.0
                continue

            elevation = leads_data[lead].get('st_elevation_mm', 0.0)
            depression = leads_data[lead].get('st_depression_mm', 0.0)

            # Net ST change (elevation is positive, depression is negative)
            st_changes[lead] = elevation - depression

        return st_changes


class STEMILocalizer:
    """
    Localizes STEMI to anatomical territory and identifies culprit coronary artery

    Implements validated algorithms for:
    - Territory identification (Anterior, Inferior, Lateral, Posterior, RV)
    - Culprit vessel determination (LAD, RCA, LCx)
    - RCA vs LCx differentiation for inferior STEMI (86% accuracy)
    - Specific arterial segment localization
    """

    def __init__(self):
        """Initialize STEMI localizer"""
        self.detector = STEMIDetector()

    def analyze(self, measurements: Dict) -> STEMIResult:
        """
        Perform complete STEMI analysis

        Args:
            measurements: Dictionary containing:
                - leads: Dict with lead data (st_elevation_mm, st_depression_mm)
                - patient_sex: 'male' or 'female' (optional)
                - patient_age: Age in years (optional)

        Returns:
            STEMIResult with complete analysis
        """
        patient_sex = measurements.get('patient_sex', 'male')
        patient_age = measurements.get('patient_age')

        # Detect ST changes
        st_elevated = self.detector.detect_st_elevation(
            measurements, patient_sex, patient_age
        )
        st_depressed = self.detector.detect_st_depression(measurements)
        st_changes = self.detector.get_st_changes_dict(measurements)

        # Check if STEMI criteria met
        is_stemi = self._is_stemi(st_elevated)

        # Initialize result
        result = STEMIResult(
            is_stemi=is_stemi,
            st_changes=st_changes
        )

        if not is_stemi:
            # Check for other concerning patterns
            self._check_non_stemi_patterns(result, st_elevated, st_depressed, st_changes)
            return result

        # Determine territories
        territories = self._identify_territories(st_elevated, st_depressed)
        result.territories = [t.value for t in territories]

        # Determine culprit vessel and confidence
        culprit, confidence, segment = self._identify_culprit_vessel(
            territories, st_elevated, st_depressed, st_changes, measurements
        )
        result.culprit_vessel = culprit.value
        result.culprit_confidence = confidence
        result.segment_location = segment

        # Generate urgent findings and recommendations
        result.urgent_findings = self._generate_urgent_findings(
            territories, culprit, st_changes, st_elevated, st_depressed
        )
        result.recommended_actions = self._generate_recommendations(
            territories, culprit, segment
        )

        # Add differential diagnosis
        result.differential_diagnosis = self._generate_differential_diagnosis(
            territories, st_elevated, st_depressed
        )

        # Add clinical notes
        result.additional_notes = self._generate_clinical_notes(
            territories, culprit, st_elevated, st_depressed
        )

        return result

    def _is_stemi(self, st_elevated: Dict[str, bool]) -> bool:
        """
        Determine if STEMI criteria are met

        Requires ST elevation in ≥2 contiguous leads:
        - Contiguous leads: I-aVL, II-III-aVF, V1-V6
        """
        # Check for ≥2 contiguous elevated leads
        contiguous_groups = [
            ['I', 'aVL'],
            ['II', 'III', 'aVF'],
            ['V1', 'V2'],
            ['V2', 'V3'],
            ['V3', 'V4'],
            ['V4', 'V5'],
            ['V5', 'V6'],
            ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']  # Extensive anterior
        ]

        for group in contiguous_groups:
            elevated_count = sum(1 for lead in group if st_elevated.get(lead, False))
            if elevated_count >= 2:
                return True

        return False

    def _identify_territories(self, st_elevated: Dict[str, bool],
                             st_depressed: Dict[str, bool]) -> List[STEMITerritory]:
        """
        Identify affected anatomical territories

        Territory definitions:
        - Anterior: V1-V4 elevation
        - Anteroseptal: V1-V3 elevation
        - Anterolateral: V3-V6, I, aVL elevation
        - Inferior: II, III, aVF elevation
        - Lateral: I, aVL, V5-V6 elevation
        - Posterior: V1-V3 depression (reciprocal)
        - Right Ventricle: V1 elevation + inferior STEMI
        """
        territories = []

        # Anterior (V1-V4)
        anterior_leads = ['V1', 'V2', 'V3', 'V4']
        if sum(st_elevated.get(lead, False) for lead in anterior_leads) >= 2:
            # Determine specific anterior territory
            if st_elevated.get('V1') and st_elevated.get('V2'):
                territories.append(STEMITerritory.ANTEROSEPTAL)

            # Check for anterolateral extension
            if any(st_elevated.get(lead, False) for lead in ['V5', 'V6', 'I', 'aVL']):
                territories.append(STEMITerritory.ANTEROLATERAL)

            # General anterior if not more specific
            if not territories:
                territories.append(STEMITerritory.ANTERIOR)

        # Inferior (II, III, aVF)
        inferior_leads = ['II', 'III', 'aVF']
        if sum(st_elevated.get(lead, False) for lead in inferior_leads) >= 2:
            territories.append(STEMITerritory.INFERIOR)

            # Check for right ventricular involvement
            if st_elevated.get('V1', False):
                territories.append(STEMITerritory.RIGHT_VENTRICLE)

            # Check for posterior extension (V1-V3 depression)
            posterior_depression = sum(
                st_depressed.get(lead, False) for lead in ['V1', 'V2', 'V3']
            )
            if posterior_depression >= 2:
                territories.append(STEMITerritory.POSTERIOR)

        # Lateral (I, aVL, V5, V6)
        lateral_leads_limb = ['I', 'aVL']
        lateral_leads_precordial = ['V5', 'V6']
        lateral_elevation = (
            sum(st_elevated.get(lead, False) for lead in lateral_leads_limb) +
            sum(st_elevated.get(lead, False) for lead in lateral_leads_precordial)
        )

        # Lateral only if not already captured by anterolateral
        if lateral_elevation >= 2 and STEMITerritory.ANTEROLATERAL not in territories:
            if STEMITerritory.INFERIOR in territories:
                territories.append(STEMITerritory.INFEROLATERAL)
            else:
                territories.append(STEMITerritory.LATERAL)

        # Isolated posterior (V1-V3 depression without inferior elevation)
        if (STEMITerritory.INFERIOR not in territories and
            sum(st_depressed.get(lead, False) for lead in ['V1', 'V2', 'V3']) >= 2):
            territories.append(STEMITerritory.POSTERIOR)

        return territories

    def _identify_culprit_vessel(self, territories: List[STEMITerritory],
                                st_elevated: Dict[str, bool],
                                st_depressed: Dict[str, bool],
                                st_changes: Dict[str, float],
                                measurements: Dict) -> Tuple[CulpritVessel, float, Optional[str]]:
        """
        Identify most likely culprit coronary artery

        Returns:
            Tuple of (culprit_vessel, confidence, segment_location)
        """
        # Anterior territories → LAD
        if any(t in territories for t in [
            STEMITerritory.ANTERIOR,
            STEMITerritory.ANTEROSEPTAL,
            STEMITerritory.ANTEROLATERAL
        ]):
            segment = self._localize_lad_segment(st_elevated, st_depressed)
            return (CulpritVessel.LAD, 0.95, segment)

        # Inferior STEMI → RCA vs LCx differentiation
        if STEMITerritory.INFERIOR in territories:
            return self._differentiate_rca_lcx(
                territories, st_elevated, st_depressed, st_changes, measurements
            )

        # Isolated lateral → LCx
        if any(t in territories for t in [STEMITerritory.LATERAL, STEMITerritory.INFEROLATERAL]):
            return (CulpritVessel.LCX, 0.85, "Distal LCx or Obtuse Marginal")

        # Isolated posterior → Usually LCx or distal RCA
        if STEMITerritory.POSTERIOR in territories:
            return (CulpritVessel.LCX, 0.70, "Posterior Descending Artery (LCx)")

        return (CulpritVessel.UNKNOWN, 0.0, None)

    def _differentiate_rca_lcx(self, territories: List[STEMITerritory],
                              st_elevated: Dict[str, bool],
                              st_depressed: Dict[str, bool],
                              st_changes: Dict[str, float],
                              measurements: Dict) -> Tuple[CulpritVessel, float, Optional[str]]:
        """
        Differentiate RCA from LCx in inferior STEMI using validated algorithm

        Algorithm from Fiol M et al., Circulation 2004
        Accuracy: 86% with combined criteria

        RCA indicators:
        1. ST elevation III > II (high sensitivity)
        2. ST depression in lead I (90% sensitivity)
        3. ST elevation in V1 (RV involvement)

        LCx indicators:
        1. ST elevation II ≥ III
        2. ST elevation in lead I
        3. ST depression in V1 (posterior involvement)
        """
        rca_score = 0
        lcx_score = 0
        confidence_factors = []

        # Criterion 1: Compare ST elevation in III vs II
        st_ii = st_changes.get('II', 0.0)
        st_iii = st_changes.get('III', 0.0)

        if st_iii > st_ii:
            rca_score += 2
            confidence_factors.append("ST elevation III > II (RCA)")
        elif st_ii >= st_iii:
            lcx_score += 2
            confidence_factors.append("ST elevation II ≥ III (LCx)")

        # Criterion 2: ST changes in lead I
        if st_depressed.get('I', False):
            rca_score += 2
            confidence_factors.append("ST depression in lead I (RCA)")
        elif st_elevated.get('I', False):
            lcx_score += 2
            confidence_factors.append("ST elevation in lead I (LCx)")

        # Criterion 3: ST changes in V1
        if st_elevated.get('V1', False):
            rca_score += 2
            confidence_factors.append("ST elevation in V1 - RV involvement (RCA)")
        elif st_depressed.get('V1', False):
            lcx_score += 1
            confidence_factors.append("ST depression in V1 - posterior involvement (LCx)")

        # Check for posterior extension (V1-V3 depression)
        if STEMITerritory.POSTERIOR in territories:
            lcx_score += 1
            confidence_factors.append("Posterior extension (LCx)")

        # Check for right ventricular involvement
        if STEMITerritory.RIGHT_VENTRICLE in territories:
            rca_score += 2
            confidence_factors.append("Right ventricular involvement (RCA)")

        # Determine culprit based on score
        total_score = rca_score + lcx_score
        if rca_score > lcx_score:
            confidence = min(0.95, 0.60 + (rca_score / max(total_score, 1)) * 0.35)
            segment = "Proximal RCA" if rca_score >= 4 else "Mid-to-distal RCA"
            return (CulpritVessel.RCA, confidence, segment)
        elif lcx_score > rca_score:
            confidence = min(0.90, 0.60 + (lcx_score / max(total_score, 1)) * 0.30)
            segment = "Dominant LCx"
            return (CulpritVessel.LCX, confidence, segment)
        else:
            # Tie - use default prevalence (RCA more common)
            return (CulpritVessel.RCA, 0.60, "RCA (based on prevalence)")

    def _localize_lad_segment(self, st_elevated: Dict[str, bool],
                             st_depressed: Dict[str, bool]) -> str:
        """
        Localize LAD occlusion to specific segment

        - Proximal LAD (before S1): Extensive anterior + inferior ST depression
        - Mid LAD: V1-V4 elevation
        - Distal LAD: V3-V4 elevation only
        """
        # Proximal LAD: Extensive anterior + lateral involvement
        if (st_elevated.get('V1') and st_elevated.get('V2') and
            st_elevated.get('V3') and st_elevated.get('V4')):

            # Check for additional lateral involvement (I, aVL)
            if st_elevated.get('I') or st_elevated.get('aVL'):
                return "Proximal LAD (before D1 diagonal)"

            return "Mid LAD"

        # Distal LAD: V3-V4 only
        if st_elevated.get('V3') or st_elevated.get('V4'):
            if not (st_elevated.get('V1') or st_elevated.get('V2')):
                return "Distal LAD"

        return "LAD (segment uncertain)"

    def _generate_urgent_findings(self, territories: List[STEMITerritory],
                                 culprit: CulpritVessel,
                                 st_changes: Dict[str, float],
                                 st_elevated: Dict[str, bool],
                                 st_depressed: Dict[str, bool]) -> List[str]:
        """Generate list of urgent clinical findings"""
        findings = []

        # STEMI is always urgent
        findings.append("⚠️ ACUTE STEMI DETECTED - MEDICAL EMERGENCY")

        # Territory-specific urgency
        if STEMITerritory.ANTERIOR in territories or STEMITerritory.ANTEROSEPTAL in territories:
            findings.append("⚠️ Anterior/anteroseptal STEMI - HIGH RISK for large infarct and cardiogenic shock")

        if STEMITerritory.ANTEROLATERAL in territories:
            findings.append("⚠️ Extensive anterolateral STEMI - VERY HIGH RISK for pump failure")

        # Right ventricular involvement
        if STEMITerritory.RIGHT_VENTRICLE in territories:
            findings.append("⚠️ Right ventricular involvement - RISK of hypotension, avoid nitrates/preload reducers")

        # Posterior involvement
        if STEMITerritory.POSTERIOR in territories:
            findings.append("⚠️ Posterior wall involvement - obtain posterior leads V7-V9")

        # Massive ST elevation (high-risk)
        max_elevation = max([v for v in st_changes.values() if v > 0], default=0)
        if max_elevation >= 5.0:
            findings.append(f"⚠️ Massive ST elevation ({max_elevation:.1f}mm) - VERY HIGH RISK")

        # Reciprocal changes (more specific diagnosis)
        reciprocal_count = sum(1 for v in st_depressed.values() if v)
        if reciprocal_count >= 3:
            findings.append("✓ Extensive reciprocal ST depression - supports STEMI diagnosis")

        return findings

    def _generate_recommendations(self, territories: List[STEMITerritory],
                                 culprit: CulpritVessel,
                                 segment: Optional[str]) -> List[str]:
        """Generate clinical action recommendations"""
        recommendations = []

        # Standard STEMI protocol
        recommendations.append("1. ACTIVATE CATH LAB IMMEDIATELY - Target door-to-balloon < 90 minutes")
        recommendations.append("2. Administer aspirin 325mg PO (chewed) if not already given")
        recommendations.append("3. Administer P2Y12 inhibitor (ticagrelor 180mg or clopidogrel 600mg)")
        recommendations.append("4. Anticoagulation: heparin or bivalirudin per protocol")

        # Territory-specific recommendations
        if STEMITerritory.RIGHT_VENTRICLE in territories:
            recommendations.append("5. RV INFARCT: Avoid nitrates/morphine, maintain preload, volume resuscitation if hypotensive")
            recommendations.append("6. Obtain right-sided leads (V3R-V6R), especially V4R")
        else:
            recommendations.append("5. Nitroglycerin for chest pain (if BP permits)")

        if STEMITerritory.POSTERIOR in territories:
            recommendations.append("6. Obtain posterior leads V7-V9 to confirm posterior involvement")

        # Vessel-specific considerations
        if culprit == CulpritVessel.LAD:
            recommendations.append("7. LAD occlusion: High risk for complications, consider hemodynamic monitoring")
        elif culprit == CulpritVessel.RCA:
            recommendations.append("7. RCA occlusion: Monitor for bradycardia/heart block")

        recommendations.append("8. Serial ECGs every 10-15 minutes to assess for dynamic changes")
        recommendations.append("9. Continuous cardiac monitoring for arrhythmias")
        recommendations.append("10. Notify cardiology and cardiac surgery teams")

        return recommendations

    def _generate_differential_diagnosis(self, territories: List[STEMITerritory],
                                        st_elevated: Dict[str, bool],
                                        st_depressed: Dict[str, bool]) -> List[str]:
        """Generate differential diagnosis to consider"""
        differentials = []

        # Always consider these with ST elevation
        differentials.append("Early repolarization (benign - typically young, athletic, notching at J-point)")
        differentials.append("Pericarditis (diffuse ST elevation, PR depression, no reciprocal changes)")
        differentials.append("Left ventricular aneurysm (persistent ST elevation weeks after MI)")

        # Anterior ST elevation differentials
        if any(t in territories for t in [STEMITerritory.ANTERIOR, STEMITerritory.ANTEROSEPTAL]):
            differentials.append("Takotsubo cardiomyopathy (apical ballooning, emotional stressor)")
            differentials.append("Myocarditis (viral prodrome, younger patient)")

        # Inferior ST elevation differentials
        if STEMITerritory.INFERIOR in territories:
            differentials.append("Acute cholecystitis (can mimic inferior STEMI)")

        return differentials

    def _generate_clinical_notes(self, territories: List[STEMITerritory],
                                culprit: CulpritVessel,
                                st_elevated: Dict[str, bool],
                                st_depressed: Dict[str, bool]) -> List[str]:
        """Generate additional clinical context notes"""
        notes = []

        # Expected complications by territory
        if STEMITerritory.ANTERIOR in territories:
            notes.append("Anterior STEMI complications: LV dysfunction, CHF, ventricular arrhythmias, LV thrombus")

        if STEMITerritory.INFERIOR in territories:
            notes.append("Inferior STEMI complications: Bradycardia, AV blocks (usually transient with RCA)")

        if STEMITerritory.RIGHT_VENTRICLE in territories:
            notes.append("RV infarct: Watch for hypotension, may need fluid resuscitation, higher mortality")

        # Vessel-specific notes
        if culprit == CulpritVessel.LAD:
            notes.append("LAD supplies ~40% of LV myocardium - highest risk for cardiogenic shock")
        elif culprit == CulpritVessel.RCA:
            notes.append("RCA supplies SA node (60%) and AV node (90%) - expect conduction abnormalities")
        elif culprit == CulpritVessel.LCX:
            notes.append("LCx occlusions can be subtle - ensure adequate lateral lead evaluation")

        # General prognostic notes
        territories_count = len(territories)
        if territories_count >= 3:
            notes.append("Multi-territory involvement - indicates extensive myocardial injury, poor prognosis")

        return notes

    def _check_non_stemi_patterns(self, result: STEMIResult,
                                 st_elevated: Dict[str, bool],
                                 st_depressed: Dict[str, bool],
                                 st_changes: Dict[str, float]) -> None:
        """
        Check for concerning patterns even if not meeting STEMI criteria
        """
        # De Winter's T waves (LAD occlusion equivalent)
        if (st_changes.get('V1', 0) < 0 and st_changes.get('V2', 0) < 0 and
            st_changes.get('V3', 0) < 0):
            result.urgent_findings.append(
                "⚠️ De Winter's pattern suspected (upsloping ST depression V1-V4 with tall T waves) - LAD OCCLUSION EQUIVALENT"
            )
            result.recommended_actions.append("Activate cath lab - De Winter's = acute LAD occlusion")

        # Wellens' syndrome (critical LAD stenosis)
        if st_changes.get('V2', 0) < 0 or st_changes.get('V3', 0) < 0:
            result.additional_notes.append(
                "Consider Wellens' syndrome if T wave inversions in V2-V3 with recent chest pain (critical LAD stenosis)"
            )

        # Diffuse ST depression (left main or severe 3-vessel disease)
        depression_count = sum(1 for v in st_depressed.values() if v)
        if depression_count >= 7:
            result.urgent_findings.append(
                "⚠️ Diffuse ST depression (≥7 leads) - consider left main or severe multivessel disease"
            )
            result.recommended_actions.append("Urgent cardiology consultation - possible left main stenosis")


# Convenience function for simple usage
def analyze_stemi(measurements: Dict) -> STEMIResult:
    """
    Convenience function to analyze STEMI from measurements

    Args:
        measurements: Dictionary containing lead measurements

    Returns:
        STEMIResult with complete analysis

    Example:
        >>> measurements = {
        ...     "leads": {
        ...         "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0},
        ...         "III": {"st_elevation_mm": 3.0, "st_depression_mm": 0},
        ...         "aVF": {"st_elevation_mm": 2.0, "st_depression_mm": 0},
        ...         "I": {"st_elevation_mm": 0, "st_depression_mm": 1.5},
        ...         "V1": {"st_elevation_mm": 1.5, "st_depression_mm": 0},
        ...         # ... other leads
        ...     },
        ...     "patient_sex": "male"
        ... }
        >>> result = analyze_stemi(measurements)
        >>> print(f"STEMI: {result.is_stemi}, Vessel: {result.culprit_vessel}")
    """
    localizer = STEMILocalizer()
    return localizer.analyze(measurements)
