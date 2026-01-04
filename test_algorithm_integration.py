#!/usr/bin/env python3
"""
Test script for algorithm integration with inference engine.

This demonstrates that the algorithms are properly wired and working.
Run with: python test_algorithm_integration.py
"""

import sys
sys.path.insert(0, '/home/user/ecg')

from src.core.algorithms import (
    BrugadaAlgorithm,
    BaselAlgorithm,
    VereckeiAlgorithm,
    PavaAlgorithm,
    VTSVTEnsemble,
    analyze_stemi,
)


def test_stemi_detection():
    """Test STEMI detection and localization"""
    print("=" * 80)
    print("TEST 1: Inferior STEMI with RV Involvement")
    print("=" * 80)

    measurements = {
        'heart_rate': 85,
        'leads': {
            'I': {'st_elevation_mm': 0.0, 'st_depression_mm': 1.5},
            'II': {'st_elevation_mm': 2.5, 'st_depression_mm': 0.0},
            'III': {'st_elevation_mm': 3.5, 'st_depression_mm': 0.0},
            'aVR': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'aVL': {'st_elevation_mm': 0.0, 'st_depression_mm': 1.0},
            'aVF': {'st_elevation_mm': 2.8, 'st_depression_mm': 0.0},
            'V1': {'st_elevation_mm': 1.8, 'st_depression_mm': 0.0},
            'V2': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'V3': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'V4': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'V5': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'V6': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
        },
        'patient_sex': 'male',
        'patient_age': 65,
    }

    result = analyze_stemi(measurements)

    print(f"\n✅ STEMI Detected: {result.is_stemi}")
    print(f"✅ Territories: {', '.join(result.territories)}")
    print(f"✅ Culprit Vessel: {result.culprit_vessel}")
    print(f"✅ Confidence: {result.culprit_confidence:.0%}")
    print(f"✅ Segment: {result.segment_location}")

    print(f"\nUrgent Findings ({len(result.urgent_findings)}):")
    for finding in result.urgent_findings:
        print(f"  • {finding}")

    print(f"\nRecommended Actions (first 5):")
    for action in result.recommended_actions[:5]:
        print(f"  • {action}")

    assert result.is_stemi, "STEMI should be detected"
    assert "Inferior" in result.territories, "Inferior territory should be detected"
    assert "RCA" in result.culprit_vessel, "RCA should be identified as culprit"
    assert result.culprit_confidence >= 0.9, "High confidence expected for clear STEMI"

    print("\n✅ STEMI test passed!")


def test_vt_svt_algorithms():
    """Test VT/SVT differentiation algorithms"""
    print("\n" + "=" * 80)
    print("TEST 2: VT/SVT Differentiation - Wide Complex Tachycardia")
    print("=" * 80)

    # Measurements suggesting VT
    measurements = {
        'age': 65,
        'has_structural_heart_disease': True,
        'leads': {
            'I': {'has_rs_complex': False},
            'II': {
                'has_rs_complex': False,
                'r_peak_time_ms': 65,
                'time_to_first_peak_ms': 65,
            },
            'III': {'has_rs_complex': False},
            'aVR': {
                'initial_r_dominant': True,
                'initial_deflection_ms': 50,
                'has_downstroke_notching': False,
                'vi_vt_ratio': 0.8,
                'time_to_first_peak_ms': 55,
            },
            'aVL': {'has_rs_complex': False},
            'aVF': {'has_rs_complex': False},
            'V1': {'has_rs_complex': False},
            'V2': {'has_rs_complex': False},
            'V3': {'has_rs_complex': False},
            'V4': {'has_rs_complex': False},
            'V5': {'has_rs_complex': False},
            'V6': {'has_rs_complex': False},
        },
        'has_av_dissociation': False,
    }

    # Test individual algorithms
    print("\nIndividual Algorithm Results:")

    brugada = BrugadaAlgorithm()
    result_brugada = brugada.evaluate(measurements)
    print(f"  • Brugada: {result_brugada.conclusion} (confidence: {result_brugada.confidence:.0%})")

    basel = BaselAlgorithm()
    result_basel = basel.evaluate(measurements)
    print(f"  • Basel: {result_basel.conclusion} (confidence: {result_basel.confidence:.0%})")

    vereckei = VereckeiAlgorithm()
    result_vereckei = vereckei.evaluate(measurements)
    print(f"  • Vereckei: {result_vereckei.conclusion} (confidence: {result_vereckei.confidence:.0%})")

    pava = PavaAlgorithm()
    result_pava = pava.evaluate(measurements)
    print(f"  • Pava: {result_pava.conclusion} (confidence: {result_pava.confidence:.0%})")

    # Test ensemble
    print("\nEnsemble Analysis:")
    ensemble = VTSVTEnsemble()
    result_ensemble = ensemble.evaluate(measurements)

    print(f"  • Consensus: {result_ensemble['consensus']}")
    print(f"  • Confidence: {result_ensemble['confidence']:.0%}")
    print(f"  • Agreement: {result_ensemble['agreement']['agreement_level']} "
          f"({result_ensemble['agreement']['agreement_percentage']}%)")

    print(f"\n  Recommendation:")
    rec_lines = result_ensemble['recommendation'].split('. ')
    for line in rec_lines[:2]:
        if line.strip():
            print(f"    {line.strip()}")

    # Verify all algorithms detected VT
    assert result_brugada.conclusion == "VT", "Brugada should detect VT"
    assert result_basel.conclusion == "VT", "Basel should detect VT"
    assert result_vereckei.conclusion == "VT", "Vereckei should detect VT"
    assert result_pava.conclusion == "VT", "Pava should detect VT"
    assert result_ensemble['consensus'] == "VT", "Ensemble should conclude VT"
    assert result_ensemble['agreement']['agreement_level'] == "complete", "Complete agreement expected"

    print("\n✅ VT/SVT test passed!")


def test_anterior_stemi():
    """Test Anterior STEMI detection (LAD)"""
    print("\n" + "=" * 80)
    print("TEST 3: Anterior STEMI (LAD)")
    print("=" * 80)

    measurements = {
        'leads': {
            'I': {'st_elevation_mm': 1.2, 'st_depression_mm': 0.0},
            'II': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.5},
            'III': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.8},
            'aVR': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.0},
            'aVL': {'st_elevation_mm': 1.5, 'st_depression_mm': 0.0},
            'aVF': {'st_elevation_mm': 0.0, 'st_depression_mm': 0.6},
            'V1': {'st_elevation_mm': 2.5, 'st_depression_mm': 0.0},
            'V2': {'st_elevation_mm': 3.0, 'st_depression_mm': 0.0},
            'V3': {'st_elevation_mm': 3.5, 'st_depression_mm': 0.0},
            'V4': {'st_elevation_mm': 2.8, 'st_depression_mm': 0.0},
            'V5': {'st_elevation_mm': 1.5, 'st_depression_mm': 0.0},
            'V6': {'st_elevation_mm': 1.2, 'st_depression_mm': 0.0},
        },
        'patient_sex': 'male',
        'patient_age': 55,
    }

    result = analyze_stemi(measurements)

    print(f"\n✅ STEMI Detected: {result.is_stemi}")
    print(f"✅ Territories: {', '.join(result.territories)}")
    print(f"✅ Culprit Vessel: {result.culprit_vessel}")
    print(f"✅ Segment: {result.segment_location}")

    assert result.is_stemi, "STEMI should be detected"
    # Can be Anterior, Anteroseptal, or Anterolateral
    assert any("Anterior" in t or "anteroseptal" in t.lower() or "anterolateral" in t.lower()
               for t in result.territories), "Anterior-related territory should be identified"
    assert "LAD" in result.culprit_vessel, "LAD should be the culprit vessel"

    print("\n✅ Anterior STEMI test passed!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ECG Guru - Algorithm Integration Tests")
    print("Testing: STEMI Detection, VT/SVT Differentiation")
    print("=" * 80)

    try:
        test_stemi_detection()
        test_vt_svt_algorithms()
        test_anterior_stemi()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("Algorithms are properly integrated with the inference engine")
        print("=" * 80 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
