"""
ECG Guru - Clinical Algorithms

Implementation of validated clinical algorithms for ECG analysis:
- VT vs SVT differentiation (Brugada, Vereckei, Basel, Pava)
- Accessory pathway localization (SMART-WPW)
- STEMI detection and culprit vessel determination
- SVT classification

These are programmatic implementations of peer-reviewed algorithms,
NOT AI/ML models. Each algorithm produces deterministic, explainable results.
"""

from .vt_svt import (
    AlgorithmResult,
    StepResult,
    BrugadaAlgorithm,
    VereckeiAlgorithm,
    BaselAlgorithm,
    PavaAlgorithm,
    VTSVTEnsemble,
)

from .stemi import (
    STEMIDetector,
    STEMILocalizer,
    STEMIResult,
    STEMITerritory,
    CulpritVessel,
    analyze_stemi,
)

from .pathway import (
    PathwayResult,
    PathwayLocation,
    AblationApproach,
    SMARTWPWAlgorithm,
    ArrudaAlgorithm,
    PathwayLocalizer,
    quick_pathway_localization,
    detailed_pathway_analysis,
)

__all__ = [
    # VT/SVT algorithms
    "AlgorithmResult",
    "StepResult",
    "BrugadaAlgorithm",
    "VereckeiAlgorithm",
    "BaselAlgorithm",
    "PavaAlgorithm",
    "VTSVTEnsemble",
    # STEMI algorithms
    "STEMIDetector",
    "STEMILocalizer",
    "STEMIResult",
    "STEMITerritory",
    "CulpritVessel",
    "analyze_stemi",
    # Pathway localization algorithms
    "PathwayResult",
    "PathwayLocation",
    "AblationApproach",
    "SMARTWPWAlgorithm",
    "ArrudaAlgorithm",
    "PathwayLocalizer",
    "quick_pathway_localization",
    "detailed_pathway_analysis",
]
