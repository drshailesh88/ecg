"""
STEMI Detection Examples

This module demonstrates the STEMI detection and localization algorithms
with various clinical scenarios.
"""

from stemi import analyze_stemi, STEMILocalizer


def example_inferior_stemi_rca():
    """
    Classic inferior STEMI from RCA occlusion

    Clinical presentation:
    - 65-year-old male with acute chest pain
    - ECG shows inferior ST elevation with RV involvement
    """
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
        "patient_age": 65
    }

    result = analyze_stemi(measurements)

    print("=" * 80)
    print("EXAMPLE 1: Inferior STEMI from RCA")
    print("=" * 80)
    print(f"\nSTEMI Detected: {result.is_stemi}")
    print(f"Territories: {', '.join(result.territories)}")
    print(f"Culprit Vessel: {result.culprit_vessel}")
    print(f"Confidence: {result.culprit_confidence:.1%}")
    print(f"Segment: {result.segment_location}")

    print("\n🚨 URGENT FINDINGS:")
    for finding in result.urgent_findings:
        print(f"  {finding}")

    print("\n📋 RECOMMENDED ACTIONS:")
    for i, action in enumerate(result.recommended_actions, 1):
        # Skip the number if already present
        if action[0].isdigit():
            print(f"  {action}")
        else:
            print(f"  {i}. {action}")

    print("\n💡 DIFFERENTIAL DIAGNOSIS:")
    for ddx in result.differential_diagnosis:
        print(f"  • {ddx}")

    print("\n")
    return result


def example_inferior_stemi_lcx():
    """
    Inferior STEMI from LCx occlusion

    Clinical presentation:
    - 58-year-old female with chest pain
    - ECG shows inferior ST elevation with lateral extension
    """
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
        "patient_age": 58
    }

    result = analyze_stemi(measurements)

    print("=" * 80)
    print("EXAMPLE 2: Inferior STEMI from LCx")
    print("=" * 80)
    print(f"\nSTEMI Detected: {result.is_stemi}")
    print(f"Territories: {', '.join(result.territories)}")
    print(f"Culprit Vessel: {result.culprit_vessel}")
    print(f"Confidence: {result.culprit_confidence:.1%}")
    print(f"Segment: {result.segment_location}")

    print("\n🚨 URGENT FINDINGS:")
    for finding in result.urgent_findings:
        print(f"  {finding}")

    print("\n")
    return result


def example_anterior_stemi():
    """
    Extensive anterior STEMI from proximal LAD occlusion

    Clinical presentation:
    - 52-year-old male with crushing chest pain
    - ECG shows extensive anterolateral ST elevation
    """
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
        "patient_age": 52
    }

    result = analyze_stemi(measurements)

    print("=" * 80)
    print("EXAMPLE 3: Extensive Anterior STEMI from Proximal LAD")
    print("=" * 80)
    print(f"\nSTEMI Detected: {result.is_stemi}")
    print(f"Territories: {', '.join(result.territories)}")
    print(f"Culprit Vessel: {result.culprit_vessel}")
    print(f"Confidence: {result.culprit_confidence:.1%}")
    print(f"Segment: {result.segment_location}")

    print("\n🚨 URGENT FINDINGS:")
    for finding in result.urgent_findings:
        print(f"  {finding}")

    print("\n📋 RECOMMENDED ACTIONS:")
    for i, action in enumerate(result.recommended_actions[:5], 1):
        if action[0].isdigit():
            print(f"  {action}")
        else:
            print(f"  {i}. {action}")

    print("\n")
    return result


def example_no_stemi():
    """
    Normal ECG - no STEMI

    Clinical presentation:
    - 35-year-old male with atypical chest pain
    - ECG shows no significant ST changes
    """
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
        "patient_age": 35
    }

    result = analyze_stemi(measurements)

    print("=" * 80)
    print("EXAMPLE 4: No STEMI - Normal Variant")
    print("=" * 80)
    print(f"\nSTEMI Detected: {result.is_stemi}")

    if not result.is_stemi:
        print("✓ No STEMI criteria met")
        print("\nST changes detected:")
        for lead, change in result.st_changes.items():
            if abs(change) > 0.1:
                print(f"  {lead}: {change:+.1f}mm")

    print("\n")
    return result


def run_all_examples():
    """Run all STEMI detection examples"""
    print("\n" + "=" * 80)
    print("STEMI DETECTION AND LOCALIZATION EXAMPLES")
    print("ECG Guru - AI-Powered ECG Analysis")
    print("=" * 80 + "\n")

    # Run all examples
    example_inferior_stemi_rca()
    example_inferior_stemi_lcx()
    example_anterior_stemi()
    example_no_stemi()

    print("=" * 80)
    print("All examples completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_examples()
