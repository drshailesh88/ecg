"""
Test cases and examples for VT vs SVT differentiation algorithms.

These tests demonstrate:
1. How to structure measurement input
2. Expected algorithm behavior with different data scenarios
3. Handling of missing/incomplete data
4. Ensemble analysis
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from core.algorithms.vt_svt import (
    BrugadaAlgorithm,
    VereckeiAlgorithm,
    BaselAlgorithm,
    PavaAlgorithm,
    VTSVTEnsemble,
    quick_vt_svt_check,
    detailed_vt_svt_analysis
)


def test_brugada_vt_scenario():
    """Test Brugada algorithm with classic VT pattern."""
    print("\n" + "="*70)
    print("TEST 1: Brugada Algorithm - Classic VT Pattern")
    print("="*70)

    measurements = {
        "leads": {
            "V1": {
                "has_rs_complex": False,  # Absent RS in all precordial -> VT
                "rs_interval_ms": None,
            },
            "V2": {
                "has_rs_complex": False,
            },
            "V3": {
                "has_rs_complex": False,
            },
            "V4": {
                "has_rs_complex": False,
            },
            "V5": {
                "has_rs_complex": False,
            },
            "V6": {
                "has_rs_complex": False,
            },
        },
        "has_av_dissociation": None
    }

    algo = BrugadaAlgorithm()
    result = algo.evaluate(measurements)

    print(f"\nConclusion: {result.conclusion}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"\nStep-by-step reasoning:")
    for step in result.steps:
        print(f"\nStep {step.step_number}: {step.criterion}")
        print(f"  Measured: {step.measured_value}")
        print(f"  Result: {step.result}")
        print(f"  Reasoning: {step.reasoning}")

    assert result.conclusion == "VT", "Should diagnose VT when no RS complex in any precordial lead"
    assert result.supports_vt == True
    print("\n✓ Test passed!")


def test_brugada_rs_interval():
    """Test Brugada algorithm with prolonged RS interval."""
    print("\n" + "="*70)
    print("TEST 2: Brugada Algorithm - Prolonged RS Interval")
    print("="*70)

    measurements = {
        "leads": {
            "V1": {
                "has_rs_complex": True,
                "rs_interval_ms": 120,  # >100ms -> VT
            },
            "V2": {
                "has_rs_complex": True,
                "rs_interval_ms": 95,
            },
            "V3": {
                "has_rs_complex": True,
                "rs_interval_ms": 90,
            },
            "V4": {
                "has_rs_complex": True,
                "rs_interval_ms": 85,
            },
            "V5": {
                "has_rs_complex": True,
                "rs_interval_ms": 80,
            },
            "V6": {
                "has_rs_complex": True,
                "rs_interval_ms": 75,
            },
        },
        "has_av_dissociation": False
    }

    algo = BrugadaAlgorithm()
    result = algo.evaluate(measurements)

    print(f"\nConclusion: {result.conclusion}")
    print(f"Confidence: {result.confidence:.1%}")

    for step in result.steps:
        if step.result in ["positive", "negative"]:
            print(f"\nStep {step.step_number}: {step.criterion}")
            print(f"  Result: {step.result} - {step.reasoning}")

    assert result.conclusion == "VT", "Should diagnose VT when RS interval >100ms in V1"
    print("\n✓ Test passed!")


def test_vereckei_avr():
    """Test Vereckei aVR algorithm."""
    print("\n" + "="*70)
    print("TEST 3: Vereckei aVR Algorithm - VT Pattern")
    print("="*70)

    measurements = {
        "leads": {
            "aVR": {
                "initial_r_dominant": False,
                "initial_deflection_ms": 50,  # >40ms -> VT
                "has_downstroke_notching": False,
                "vi_vt_ratio": 1.2
            }
        }
    }

    algo = VereckeiAlgorithm()
    result = algo.evaluate(measurements)

    print(f"\nConclusion: {result.conclusion}")
    print(f"Confidence: {result.confidence:.1%}")

    for step in result.steps:
        print(f"\nStep {step.step_number}: {step.criterion}")
        print(f"  Measured: {step.measured_value}")
        print(f"  Result: {step.result}")

    assert result.conclusion == "VT", "Should diagnose VT with initial deflection >40ms"
    print("\n✓ Test passed!")


def test_basel_scoring():
    """Test Basel algorithm scoring system."""
    print("\n" + "="*70)
    print("TEST 4: Basel Algorithm - High Risk Patient")
    print("="*70)

    measurements = {
        "age": 65,  # >55 = +1
        "has_structural_heart_disease": True,  # Also counts as +1 (but age already gives point)
        "leads": {
            "II": {
                "time_to_first_peak_ms": 45  # >40ms = +1
            },
            "aVR": {
                "time_to_first_peak_ms": 35  # ≤40ms = 0
            }
        }
    }

    algo = BaselAlgorithm()
    result = algo.evaluate(measurements)

    print(f"\nConclusion: {result.conclusion}")
    print(f"Confidence: {result.confidence:.1%}")

    for step in result.steps:
        print(f"\nStep {step.step_number}: {step.criterion}")
        print(f"  Result: {step.result} - {step.reasoning}")

    assert result.conclusion == "VT", "Should diagnose VT with ≥2 points (age + lead II)"
    print("\n✓ Test passed!")


def test_pava_simple():
    """Test Pava algorithm - simplest single measurement."""
    print("\n" + "="*70)
    print("TEST 5: Pava Algorithm - Simple R-wave Peak Time")
    print("="*70)

    # VT case
    measurements_vt = {
        "leads": {
            "II": {
                "r_peak_time_ms": 55  # ≥50ms -> VT
            }
        }
    }

    algo = PavaAlgorithm()
    result_vt = algo.evaluate(measurements_vt)

    print(f"\nVT Case:")
    print(f"  R-peak time: 55ms")
    print(f"  Conclusion: {result_vt.conclusion}")
    assert result_vt.conclusion == "VT"

    # SVT case
    measurements_svt = {
        "leads": {
            "II": {
                "r_peak_time_ms": 40  # <50ms -> SVT
            }
        }
    }

    result_svt = algo.evaluate(measurements_svt)

    print(f"\nSVT Case:")
    print(f"  R-peak time: 40ms")
    print(f"  Conclusion: {result_svt.conclusion}")
    assert result_svt.conclusion == "SVT"

    print("\n✓ Test passed!")


def test_ensemble_agreement():
    """Test ensemble with all algorithms agreeing."""
    print("\n" + "="*70)
    print("TEST 6: Ensemble - Strong Agreement for VT")
    print("="*70)

    measurements = {
        "age": 60,
        "has_structural_heart_disease": True,
        "has_av_dissociation": True,  # Strong VT indicator
        "leads": {
            # Brugada data
            "V1": {"has_rs_complex": True, "rs_interval_ms": 110},  # >100ms
            "V2": {"has_rs_complex": True, "rs_interval_ms": 95},
            "V3": {"has_rs_complex": True, "rs_interval_ms": 90},
            "V4": {"has_rs_complex": True, "rs_interval_ms": 85},
            "V5": {"has_rs_complex": True, "rs_interval_ms": 80},
            "V6": {"has_rs_complex": True, "rs_interval_ms": 75},

            # Vereckei data
            "aVR": {
                "initial_r_dominant": False,
                "initial_deflection_ms": 50,  # >40ms
                "has_downstroke_notching": False,
                "vi_vt_ratio": 0.8,  # ≤1.0
                "time_to_first_peak_ms": 50  # For Basel
            },

            # Pava & Basel data
            "II": {
                "r_peak_time_ms": 60,  # ≥50ms
                "time_to_first_peak_ms": 55  # >40ms
            }
        }
    }

    ensemble = VTSVTEnsemble()
    result = ensemble.evaluate(measurements)

    print(f"\nConsensus: {result['consensus']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"\nAgreement Analysis:")
    print(f"  Level: {result['agreement']['agreement_level']}")
    print(f"  VT count: {result['agreement']['vt_count']}")
    print(f"  SVT count: {result['agreement']['svt_count']}")
    print(f"\nIndividual Results:")
    for name, res in result['individual_results'].items():
        print(f"  {name}: {res['conclusion']} (conf: {res['confidence']:.1%})")

    print(f"\nRecommendation:")
    print(f"  {result['recommendation']}")

    print(f"\n{result['summary']}")

    assert result['consensus'] == "VT", "All algorithms should agree on VT"
    assert result['agreement']['agreement_level'] in ["complete", "strong"]
    print("\n✓ Test passed!")


def test_missing_data_handling():
    """Test graceful handling of missing data."""
    print("\n" + "="*70)
    print("TEST 7: Missing Data Handling")
    print("="*70)

    # Very minimal data
    measurements = {
        "leads": {
            "II": {
                "r_peak_time_ms": 55
            }
        }
    }

    ensemble = VTSVTEnsemble()
    result = ensemble.evaluate(measurements)

    print(f"\nWith minimal data (only Pava can run):")
    print(f"Consensus: {result['consensus']}")
    print(f"Confidence: {result['confidence']:.1%}")

    print(f"\nIndividual Results:")
    for name, res in result['individual_results'].items():
        print(f"  {name}: {res['conclusion']} (conf: {res['confidence']:.1%})")
        if res['missing_data']:
            print(f"    Missing: {', '.join(res['missing_data'][:2])}...")

    # Should still provide a conclusion, even if based on limited data
    assert result['consensus'] in ["VT", "SVT", "Indeterminate"]
    print("\n✓ Test passed - gracefully handled missing data!")


def test_quick_api():
    """Test quick API function."""
    print("\n" + "="*70)
    print("TEST 8: Quick API - Simple Usage")
    print("="*70)

    measurements = {
        "leads": {
            "II": {"r_peak_time_ms": 60}
        }
    }

    # Quick check
    quick_result = quick_vt_svt_check(measurements)
    print(f"Quick check result: {quick_result}")

    # Detailed analysis
    detailed_result = detailed_vt_svt_analysis(measurements)
    print(f"\nDetailed consensus: {detailed_result['consensus']}")
    print(f"Recommendation: {detailed_result['recommendation']}")

    assert quick_result in ["VT", "SVT", "Indeterminate"]
    print("\n✓ Test passed!")


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*70)
    print("VT vs SVT ALGORITHM TEST SUITE")
    print("="*70)

    tests = [
        test_brugada_vt_scenario,
        test_brugada_rs_interval,
        test_vereckei_avr,
        test_basel_scoring,
        test_pava_simple,
        test_ensemble_agreement,
        test_missing_data_handling,
        test_quick_api
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
