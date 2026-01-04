#!/usr/bin/env python3
"""
ECG Guru - VT vs SVT Clinical Scenarios

Real-world examples demonstrating algorithm usage in clinical scenarios.
These represent typical cases an ECG Guru user might encounter.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.algorithms.vt_svt import VTSVTEnsemble, detailed_vt_svt_analysis


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_result(result):
    """Print formatted analysis result."""
    print(f"CONSENSUS DIAGNOSIS: {result['consensus']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Agreement: {result['agreement']['agreement_level'].upper()} "
          f"({result['agreement']['agreement_percentage']}%)")

    print("\n--- Individual Algorithm Results ---")
    for name in ["Basel", "Brugada", "Vereckei", "Pava"]:
        if name in result['individual_results']:
            algo = result['individual_results'][name]
            status = "✓" if algo['conclusion'] != "Indeterminate" else "?"
            print(f"{status} {name:12s}: {algo['conclusion']:15s} (confidence: {algo['confidence']:.0%})")

    print("\n--- Clinical Recommendation ---")
    print(result['recommendation'])

    if any(result['individual_results'][name]['missing_data']
           for name in result['individual_results']):
        print("\n--- Data Completeness ---")
        for name in result['individual_results']:
            missing = result['individual_results'][name]['missing_data']
            if missing:
                print(f"  {name}: Missing {len(missing)} measurements")


def scenario_1_obvious_vt():
    """
    Scenario 1: 65-year-old with prior MI, wide complex tachycardia
    Clinical context strongly suggests VT
    """
    print_section("SCENARIO 1: Post-MI Patient with Wide Complex Tachycardia")

    print("CLINICAL CONTEXT:")
    print("  Patient: 65-year-old male")
    print("  History: Prior anterior MI 2 years ago")
    print("  Presentation: Chest pain, wide complex tachycardia at 180 bpm")
    print("  ECG: Wide QRS (160ms), northwest axis, AV dissociation visible")

    measurements = {
        "age": 65,
        "has_structural_heart_disease": True,  # Prior MI
        "heart_rate": 180,
        "qrs_duration_ms": 160,
        "has_av_dissociation": True,  # Pathognomonic for VT
        "leads": {
            # Brugada criteria: No RS in all precordial leads
            "V1": {"has_rs_complex": False},
            "V2": {"has_rs_complex": False},
            "V3": {"has_rs_complex": False},
            "V4": {"has_rs_complex": False},
            "V5": {"has_rs_complex": False},
            "V6": {"has_rs_complex": False},

            # Vereckei: Positive for VT
            "aVR": {
                "initial_r_dominant": True,  # Step 1 positive
                "initial_deflection_ms": 55,
                "has_downstroke_notching": False,
                "vi_vt_ratio": 0.7,
                "time_to_first_peak_ms": 60
            },

            # Pava & Basel
            "II": {
                "r_peak_time_ms": 70,  # Well over 50ms
                "time_to_first_peak_ms": 65
            }
        }
    }

    result = detailed_vt_svt_analysis(measurements)
    print_result(result)

    print("\n--- Teaching Point ---")
    print("AV dissociation (P waves marching independently of QRS) is virtually")
    print("diagnostic of VT. In this case, all 4 algorithms correctly identify VT.")
    print("The patient needs immediate treatment with antiarrhythmics or cardioversion.")


def scenario_2_young_patient_svt():
    """
    Scenario 2: 25-year-old with palpitations, likely SVT with aberrancy
    """
    print_section("SCENARIO 2: Young Patient with Palpitations")

    print("CLINICAL CONTEXT:")
    print("  Patient: 25-year-old female")
    print("  History: Recurrent palpitations since teens, otherwise healthy")
    print("  Presentation: Sudden onset palpitations, wide complex tachycardia at 170 bpm")
    print("  ECG: Wide QRS (130ms), right axis, rapid but regular")

    measurements = {
        "age": 25,
        "has_structural_heart_disease": False,
        "heart_rate": 170,
        "qrs_duration_ms": 130,
        "has_av_dissociation": False,
        "leads": {
            # Brugada: All steps negative, morphology suggests SVT
            "V1": {
                "has_rs_complex": True,
                "rs_interval_ms": 75,  # <100ms
                "vt_morphology_criteria_met": False
            },
            "V2": {"has_rs_complex": True, "rs_interval_ms": 70},
            "V3": {"has_rs_complex": True, "rs_interval_ms": 65},
            "V4": {"has_rs_complex": True, "rs_interval_ms": 60},
            "V5": {"has_rs_complex": True, "rs_interval_ms": 55},
            "V6": {
                "has_rs_complex": True,
                "rs_interval_ms": 50,
                "vt_morphology_criteria_met": False
            },

            # Vereckei: All steps negative
            "aVR": {
                "initial_r_dominant": False,
                "initial_deflection_ms": 30,  # <40ms
                "has_downstroke_notching": False,
                "vi_vt_ratio": 1.5,  # >1.0
                "time_to_first_peak_ms": 35
            },

            # Pava & Basel: Both suggest SVT
            "II": {
                "r_peak_time_ms": 40,  # <50ms
                "time_to_first_peak_ms": 38
            }
        }
    }

    result = detailed_vt_svt_analysis(measurements)
    print_result(result)

    print("\n--- Teaching Point ---")
    print("Young patient, no structural heart disease, all algorithms suggest SVT.")
    print("However, note the recommendation still maintains clinical caution.")
    print("In a stable patient, adenosine could be diagnostic and therapeutic.")


def scenario_3_borderline_case():
    """
    Scenario 3: Ambiguous case with mixed algorithm results
    """
    print_section("SCENARIO 3: Borderline Case - Diagnostic Uncertainty")

    print("CLINICAL CONTEXT:")
    print("  Patient: 45-year-old male")
    print("  History: Hypertension, unknown cardiac status")
    print("  Presentation: Wide complex tachycardia at 160 bpm")
    print("  ECG: Incomplete data, some leads unclear")

    measurements = {
        "age": 45,  # Not >55
        "has_structural_heart_disease": None,  # Unknown
        "heart_rate": 160,
        "qrs_duration_ms": 145,
        "has_av_dissociation": None,  # Unable to determine
        "leads": {
            # Limited precordial data
            "V1": {"has_rs_complex": True, "rs_interval_ms": 95},
            "V2": {"has_rs_complex": True, "rs_interval_ms": 105},  # Slightly >100
            "V6": {"has_rs_complex": True, "rs_interval_ms": 80},

            # aVR partially visible
            "aVR": {
                "initial_r_dominant": False,
                "initial_deflection_ms": 42,  # Just over 40ms
                "has_downstroke_notching": None,  # Can't assess
                "vi_vt_ratio": None,  # Can't calculate
                "time_to_first_peak_ms": 43
            },

            # Lead II clear
            "II": {
                "r_peak_time_ms": 52,  # Just over 50ms
                "time_to_first_peak_ms": 50
            }
        }
    }

    result = detailed_vt_svt_analysis(measurements)
    print_result(result)

    print("\n--- Teaching Point ---")
    print("Borderline measurements and missing data create uncertainty.")
    print("Note how algorithms may disagree (V2 RS interval 105ms is borderline).")
    print("In such cases, the recommendation defaults to treating as VT for safety.")
    print("This follows the principle: 'Treat all WCT as VT until proven otherwise.'")


def scenario_4_minimal_data():
    """
    Scenario 4: Minimal data - only bedside quick measurement available
    Real-world scenario in resource-limited setting
    """
    print_section("SCENARIO 4: Resource-Limited Setting - Minimal Data")

    print("CLINICAL CONTEXT:")
    print("  Setting: Rural clinic with basic ECG machine")
    print("  Patient: 55-year-old with palpitations")
    print("  Available: Single-lead ECG strip (lead II only)")
    print("  Question: Is this VT? Does patient need urgent referral?")

    measurements = {
        "leads": {
            "II": {
                "r_peak_time_ms": 65  # Only measurement available
            }
        }
    }

    result = detailed_vt_svt_analysis(measurements)
    print_result(result)

    print("\n--- Teaching Point ---")
    print("Even with minimal data (just Pava algorithm), system provides guidance.")
    print("R-wave peak time >50ms in lead II alone suggests VT.")
    print("This single measurement can guide urgent referral decisions in")
    print("resource-limited settings - exactly ECG Guru's Tier 1 user scenario.")


def scenario_5_ensemble_disagreement():
    """
    Scenario 5: Algorithms disagree - demonstrates ensemble value
    """
    print_section("SCENARIO 5: Algorithm Disagreement - Ensemble Resolution")

    print("CLINICAL CONTEXT:")
    print("  Patient: 52-year-old with dilated cardiomyopathy")
    print("  Presentation: Wide complex tachycardia, hemodynamically stable")
    print("  Challenge: Some features suggest VT, others suggest SVT")

    measurements = {
        "age": 52,
        "has_structural_heart_disease": True,  # Basel +1
        "has_av_dissociation": False,
        "leads": {
            # Brugada Step 1: Negative (RS present)
            # Brugada Step 2: POSITIVE (RS interval >100 in one lead)
            "V1": {"has_rs_complex": True, "rs_interval_ms": 115},  # VT per Brugada
            "V2": {"has_rs_complex": True, "rs_interval_ms": 85},
            "V3": {"has_rs_complex": True, "rs_interval_ms": 80},
            "V4": {"has_rs_complex": True, "rs_interval_ms": 75},
            "V5": {"has_rs_complex": True, "rs_interval_ms": 70},
            "V6": {"has_rs_complex": True, "rs_interval_ms": 65},

            # Vereckei: Mixed results
            "aVR": {
                "initial_r_dominant": False,
                "initial_deflection_ms": 38,  # <40ms (negative)
                "has_downstroke_notching": True,  # Step 3 POSITIVE
                "vi_vt_ratio": 1.1,  # >1.0 (SVT)
                "time_to_first_peak_ms": 36
            },

            # Basel: 1 point only (age <55, but SHD present, aVR <40ms)
            # Pava: Borderline
            "II": {
                "r_peak_time_ms": 48,  # <50ms (SVT per Pava)
                "time_to_first_peak_ms": 35
            }
        }
    }

    result = detailed_vt_svt_analysis(measurements)
    print_result(result)

    print("\n--- Teaching Point ---")
    print("When algorithms disagree, the ensemble uses weighted voting:")
    print("  - Basel (newest, 2022) gets highest weight")
    print("  - Confidence scores reflect measurement quality")
    print("  - Clinical context (structural heart disease) influences final recommendation")
    print("\nThis case shows why using multiple algorithms is superior to any single one.")


def main():
    """Run all clinical scenarios."""
    print("\n" + "="*80)
    print("  ECG GURU - VT vs SVT ALGORITHM CLINICAL SCENARIOS")
    print("="*80)
    print("\nThese scenarios demonstrate real-world usage across ECG Guru's 4 user tiers:")
    print("  Tier 1 (RMP): Scenarios 4 - Simple referral decision with minimal data")
    print("  Tier 2 (MBBS): Scenarios 1, 2 - Learning ECG interpretation")
    print("  Tier 3 (MD Cardio): Scenarios 3, 5 - Complex differential diagnosis")
    print("  Tier 4 (EP): Scenario 5 - Algorithm comparison and understanding")

    scenarios = [
        ("1", scenario_1_obvious_vt),
        ("2", scenario_2_young_patient_svt),
        ("3", scenario_3_borderline_case),
        ("4", scenario_4_minimal_data),
        ("5", scenario_5_ensemble_disagreement),
    ]

    for num, scenario in scenarios:
        scenario()
        input(f"\nPress Enter to continue to next scenario...")

    print_section("SUMMARY")
    print("These 5 scenarios demonstrate:")
    print("  ✓ Handling of obvious VT (high agreement, high confidence)")
    print("  ✓ Identification of likely SVT in appropriate clinical context")
    print("  ✓ Safety-first approach in borderline/uncertain cases")
    print("  ✓ Utility even with minimal data (resource-limited settings)")
    print("  ✓ Ensemble resolution of algorithm disagreements")
    print("\nKey Principles:")
    print("  1. Always provide a recommendation, even with limited data")
    print("  2. Default to VT treatment in uncertain cases (safety first)")
    print("  3. Consider clinical context (age, structural heart disease)")
    print("  4. Explain step-by-step reasoning for educational value")
    print("  5. Multiple algorithms > single algorithm (ensemble superiority)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScenario demonstration interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
