"""
Unit tests for STEMI detection and localization algorithms

Tests cover:
- ST elevation detection with age/sex-specific thresholds
- Territory identification
- RCA vs LCx differentiation
- Edge cases and missing data
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.algorithms.stemi import (
    STEMIDetector,
    STEMILocalizer,
    STEMIResult,
    STEMITerritory,
    CulpritVessel,
    analyze_stemi,
)


def test_st_threshold_calculation():
    """Test ST elevation thresholds are calculated correctly"""
    detector = STEMIDetector()

    # Limb leads: 1mm threshold
    assert detector.get_st_threshold('I', 'male') == 1.0
    assert detector.get_st_threshold('II', 'female') == 1.0

    # V2-V3 age/sex specific
    assert detector.get_st_threshold('V2', 'female') == 1.5
    assert detector.get_st_threshold('V3', 'female') == 1.5
    assert detector.get_st_threshold('V2', 'male', 35) == 2.5  # Young male
    assert detector.get_st_threshold('V2', 'male', 45) == 2.0  # Older male

    # Other precordial: 2mm
    assert detector.get_st_threshold('V1', 'male') == 2.0
    assert detector.get_st_threshold('V4', 'female') == 2.0

    print("✓ ST threshold calculation tests passed")


def test_inferior_stemi_rca():
    """Test inferior STEMI from RCA occlusion"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 0.0, "st_depression_mm": 1.5},
            "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 4.0, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.5},
            "aVL": {"st_elevation_mm": 0.0, "st_depression_mm": 0.8},
            "aVF": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 1.5, "st_depression_mm": 0.0},
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == True
    assert "Inferior" in result.territories
    assert result.culprit_vessel == CulpritVessel.RCA.value
    assert result.culprit_confidence >= 0.85
    assert len(result.urgent_findings) > 0
    assert len(result.recommended_actions) > 0

    print("✓ Inferior STEMI (RCA) test passed")


def test_inferior_stemi_lcx():
    """Test inferior STEMI from LCx occlusion"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 1.5, "st_depression_mm": 0.0},
            "II": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 2.0, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.5},
            "aVL": {"st_elevation_mm": 1.0, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 0.0, "st_depression_mm": 2.0},
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 2.5},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 1.5},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 1.5, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 1.8, "st_depression_mm": 0.0},
        },
        "patient_sex": "female",
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == True
    assert "Inferior" in result.territories
    assert "Posterior" in result.territories  # V1-V3 depression
    assert result.culprit_vessel == CulpritVessel.LCX.value
    assert result.culprit_confidence >= 0.70

    print("✓ Inferior STEMI (LCx) test passed")


def test_anterior_stemi():
    """Test anterior STEMI from LAD occlusion"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 2.0, "st_depression_mm": 0.0},
            "II": {"st_elevation_mm": 0.0, "st_depression_mm": 1.5},
            "III": {"st_elevation_mm": 0.0, "st_depression_mm": 2.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVL": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 0.0, "st_depression_mm": 1.8},
            "V1": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "V2": {"st_elevation_mm": 5.5, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 6.0, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 4.5, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
        "patient_age": 52,
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == True
    # Check for anterior territories (Anteroseptal, Anterolateral, or Anterior)
    assert any(t in ["Anteroseptal", "Anterolateral", "Anterior"] for t in result.territories)
    assert result.culprit_vessel == CulpritVessel.LAD.value
    assert result.culprit_confidence >= 0.90
    assert "Proximal LAD" in result.segment_location

    print("✓ Anterior STEMI (LAD) test passed")


def test_no_stemi():
    """Test normal ECG without STEMI"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 0.2, "st_depression_mm": 0.0},
            "II": {"st_elevation_mm": 0.3, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 0.0, "st_depression_mm": 0.1},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.2},
            "aVL": {"st_elevation_mm": 0.1, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 0.2, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 0.5, "st_depression_mm": 0.0},
            "V2": {"st_elevation_mm": 0.8, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 0.6, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 0.4, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 0.2, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 0.1, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
        "patient_age": 35,
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == False
    assert len(result.territories) == 0
    assert result.culprit_vessel == CulpritVessel.UNKNOWN.value

    print("✓ No STEMI test passed")


def test_missing_leads():
    """Test handling of missing lead data"""
    measurements = {
        "leads": {
            "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 2.0, "st_depression_mm": 0.0},
            # Missing other leads
        },
        "patient_sex": "male",
    }

    # Should not crash with missing data
    result = analyze_stemi(measurements)

    # Should still detect inferior STEMI
    assert result.is_stemi == True
    assert "Inferior" in result.territories

    print("✓ Missing leads test passed")


def test_right_ventricular_involvement():
    """Test detection of RV involvement in inferior STEMI"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 0.0, "st_depression_mm": 1.0},
            "II": {"st_elevation_mm": 3.0, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 4.0, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVL": {"st_elevation_mm": 0.0, "st_depression_mm": 0.5},
            "aVF": {"st_elevation_mm": 3.5, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},  # RV involvement
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == True
    assert "Right Ventricle" in result.territories
    # Check for RV warnings in urgent findings or recommendations
    rv_mentioned = (
        any("RV" in finding or "Right ventricular" in finding or "right ventricular" in finding
            for finding in result.urgent_findings) or
        any("nitrates" in action.lower() or "preload" in action.lower() or "RV" in action
            for action in result.recommended_actions)
    )
    assert rv_mentioned

    print("✓ Right ventricular involvement test passed")


def test_posterior_stemi():
    """Test detection of posterior STEMI"""
    measurements = {
        "leads": {
            "I": {"st_elevation_mm": 1.0, "st_depression_mm": 0.0},
            "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 2.0, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVL": {"st_elevation_mm": 0.8, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 2.2, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 0.0, "st_depression_mm": 2.5},
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 3.0},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 2.0},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 1.5, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 1.2, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
    }

    result = analyze_stemi(measurements)

    assert result.is_stemi == True
    assert "Posterior" in result.territories
    assert any("posterior" in action.lower() for action in result.recommended_actions)

    print("✓ Posterior STEMI test passed")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 70)
    print("STEMI DETECTION ALGORITHM TEST SUITE")
    print("=" * 70 + "\n")

    tests = [
        test_st_threshold_calculation,
        test_inferior_stemi_rca,
        test_inferior_stemi_lcx,
        test_anterior_stemi,
        test_no_stemi,
        test_missing_leads,
        test_right_ventricular_involvement,
        test_posterior_stemi,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed.append(test.__name__)

    print("\n" + "=" * 70)
    if not failed:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"FAILED TESTS: {len(failed)}/{len(tests)}")
        for name in failed:
            print(f"  - {name}")
    print("=" * 70 + "\n")

    return len(failed) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
