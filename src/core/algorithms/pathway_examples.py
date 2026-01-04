"""
Example usage and test cases for accessory pathway localization algorithms.

This file demonstrates how to use the SMART-WPW and Arruda algorithms
with real-world WPW ECG patterns.
"""

from pathway import (
    PathwayLocalizer,
    SMARTWPWAlgorithm,
    ArrudaAlgorithm,
    quick_pathway_localization,
    detailed_pathway_analysis,
)


def example_left_lateral_pathway():
    """
    Example: Classic left lateral accessory pathway.

    ECG features:
    - Positive delta in V1 (left-sided)
    - Negative delta in inferior leads (not posterior)
    - Positive in I and aVL (free wall)
    """
    measurements = {
        "delta_wave_polarity": {
            "I": "+",
            "II": "+",
            "III": "+",
            "aVR": "-",
            "aVL": "+",
            "aVF": "+",
            "V1": "+",
            "V2": "+",
            "V3": "+",
            "V4": "+",
            "V5": "+",
            "V6": "+"
        },
        "qrs_morphology": {
            "V1": "positive",
            "transition": "V2"
        },
        "has_manifest_preexcitation": True
    }

    print("=" * 70)
    print("EXAMPLE 1: LEFT LATERAL PATHWAY")
    print("=" * 70)

    localizer = PathwayLocalizer()
    result = localizer.localize(measurements)

    print(result["summary"])
    print("\nRecommendation:")
    print(result["recommendation"])


def example_posteroseptal_pathway():
    """
    Example: Posteroseptal accessory pathway (HIGH RISK).

    ECG features:
    - Positive delta in V1 (septal)
    - Negative delta in inferior leads (posterior)
    - Mixed pattern in I/aVL (septal location)
    """
    measurements = {
        "delta_wave_polarity": {
            "I": "0",
            "II": "-",
            "III": "-",
            "aVR": "-",
            "aVL": "0",
            "aVF": "-",
            "V1": "+",
            "V2": "+",
            "V3": "+",
            "V4": "+",
            "V5": "+",
            "V6": "+"
        },
        "qrs_morphology": {
            "V1": "positive",
            "transition": "V2"
        },
        "has_manifest_preexcitation": True
    }

    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: POSTEROSEPTAL PATHWAY (HIGH RISK)")
    print("=" * 70)

    localizer = PathwayLocalizer()
    result = localizer.localize(measurements)

    print(result["summary"])
    print("\nRecommendation:")
    print(result["recommendation"])


def example_right_lateral_pathway():
    """
    Example: Right lateral accessory pathway.

    ECG features:
    - Negative delta in V1 and V2 (right-sided)
    - Mixed inferior leads (lateral, not purely anterior/posterior)
    - Positive in I and aVL (free wall)
    """
    measurements = {
        "delta_wave_polarity": {
            "I": "+",
            "II": "+",
            "III": "0",
            "aVR": "-",
            "aVL": "+",
            "aVF": "+",
            "V1": "-",
            "V2": "-",
            "V3": "0",
            "V4": "+",
            "V5": "+",
            "V6": "+"
        },
        "qrs_morphology": {
            "V1": "negative",
            "transition": "V3"
        },
        "has_manifest_preexcitation": True
    }

    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: RIGHT LATERAL PATHWAY")
    print("=" * 70)

    localizer = PathwayLocalizer()
    result = localizer.localize(measurements)

    print(result["summary"])
    print("\nRecommendation:")
    print(result["recommendation"])


def example_concealed_pathway():
    """
    Example: Concealed accessory pathway (orthodromic AVRT without manifest pre-excitation).

    Note: Localization algorithms have limited utility without delta waves.
    """
    measurements = {
        "delta_wave_polarity": {
            "I": "0",
            "II": "0",
            "III": "0",
            "aVR": "0",
            "aVL": "0",
            "aVF": "0",
            "V1": "0",
            "V2": "0",
            "V3": "0",
            "V4": "0",
            "V5": "0",
            "V6": "0"
        },
        "qrs_morphology": {
            "V1": "negative",
            "transition": "V4"
        },
        "has_manifest_preexcitation": False
    }

    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: CONCEALED PATHWAY (No Manifest Pre-excitation)")
    print("=" * 70)

    localizer = PathwayLocalizer()
    result = localizer.localize(measurements)

    print(result["summary"])
    print("\nRecommendation:")
    print(result["recommendation"])


def example_quick_localization():
    """
    Example: Quick localization using convenience function.
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE 5: QUICK LOCALIZATION (Convenience Function)")
    print("=" * 70)

    delta_waves = {
        "I": "+",
        "II": "-",
        "III": "-",
        "aVR": "-",
        "aVL": "+",
        "aVF": "-",
        "V1": "+",
        "V2": "+",
        "V3": "+",
        "V4": "+",
        "V5": "+",
        "V6": "+"
    }

    location = quick_pathway_localization(delta_waves)
    print(f"\nQuick localization result: {location}")
    print("\nNote: Use detailed_pathway_analysis() for complete information including")
    print("ablation approach, clinical notes, and algorithm consensus.")


def example_algorithm_comparison():
    """
    Example: Compare SMART-WPW vs Arruda algorithm results.
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE 6: ALGORITHM COMPARISON")
    print("=" * 70)

    measurements = {
        "delta_wave_polarity": {
            "I": "+",
            "II": "+",
            "III": "-",
            "aVR": "-",
            "aVL": "+",
            "aVF": "0",
            "V1": "+",
            "V2": "+",
            "V3": "+",
            "V4": "+",
            "V5": "+",
            "V6": "+"
        },
        "qrs_morphology": {
            "V1": "positive",
            "transition": "V2"
        },
        "has_manifest_preexcitation": True
    }

    smart = SMARTWPWAlgorithm()
    arruda = ArrudaAlgorithm()

    smart_result = smart.evaluate(measurements)
    arruda_result = arruda.evaluate(measurements)

    print("\nSMART-WPW Result:")
    print(f"  Location: {smart_result.primary_location}")
    print(f"  Confidence: {smart_result.confidence:.0%}")
    print(f"  Alternatives: {', '.join(smart_result.alternative_locations)}")

    print("\nArruda Result:")
    print(f"  Location: {arruda_result.primary_location}")
    print(f"  Confidence: {arruda_result.confidence:.0%}")
    print(f"  Alternatives: {', '.join(arruda_result.alternative_locations)}")

    print("\nStep-by-step reasoning (SMART-WPW):")
    for i, step in enumerate(smart_result.step_details, 1):
        print(f"\n{i}. {step}")


def run_all_examples():
    """Run all example cases."""
    example_left_lateral_pathway()
    example_posteroseptal_pathway()
    example_right_lateral_pathway()
    example_concealed_pathway()
    example_quick_localization()
    example_algorithm_comparison()

    print("\n\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nKEY TAKEAWAYS:")
    print("1. SMART-WPW has highest accuracy (97%) - use as primary algorithm")
    print("2. Arruda serves as validation and has lower accuracy (53-75%)")
    print("3. Septal pathways (AS, MS, PS, RPS) are HIGH RISK for AV block")
    print("4. Concealed pathways cannot be localized without manifest delta waves")
    print("5. ALWAYS confirm localization with EP study mapping before ablation")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
