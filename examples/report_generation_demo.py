"""
ECG Report Generation Demo

This example shows how to integrate the report generation module
with the ECG analysis pipeline.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.report import (
    ECGReport,
    PatientInfo,
    ReportGenerator,
    UserLevel,
    create_report_from_analysis,
)


def demo_simple_report():
    """Demo: Create a simple ECG report"""
    print("=" * 80)
    print("DEMO 1: Simple ECG Report")
    print("=" * 80)

    # Create a basic report
    report = ECGReport(
        report_id="ECG-DEMO-001",
        timestamp=datetime.now(),
        patient_info=PatientInfo(
            name="Jane Smith",
            age=45,
            sex="female",
        ),
        quality_score=0.92,
        measurements={
            "heart_rate": 75,
            "rhythm": "sinus",
            "pr_interval_ms": 160,
            "qrs_duration_ms": 95,
            "qt_interval_ms": 380,
            "qtc_ms": 420,
            "axis_degrees": 45,
        },
        findings=[
            {
                "category": "rhythm",
                "finding": "Normal sinus rhythm",
                "severity": "normal",
                "confidence": 0.98,
                "explanation": "Regular rhythm with rate 75 bpm",
            }
        ],
        summary="Normal ECG - no acute abnormalities detected",
        primary_diagnosis="Normal ECG",
        differential_diagnoses=[],
        confidence=0.98,
        is_urgent=False,
        recommended_actions=[
            "No immediate action required",
            "Routine follow-up as per clinical protocol",
        ],
    )

    # Generate text report
    generator = ReportGenerator()
    text_report = generator.generate_text(report, user_level=UserLevel.STUDENT)
    print(text_report)


def demo_critical_findings():
    """Demo: Report with critical findings (STEMI)"""
    print("\n" + "=" * 80)
    print("DEMO 2: Critical Findings - STEMI")
    print("=" * 80)

    report = ECGReport(
        report_id="ECG-STEMI-001",
        timestamp=datetime.now(),
        patient_info=PatientInfo(
            name="John Doe",
            age=62,
            sex="male",
        ),
        quality_score=0.88,
        measurements={
            "heart_rate": 95,
            "rhythm": "sinus_tachycardia",
            "pr_interval_ms": 150,
            "qrs_duration_ms": 100,
            "qt_interval_ms": 360,
            "qtc_ms": 410,
            "axis_degrees": 30,
        },
        findings=[
            {
                "category": "ischemia",
                "finding": "ST elevation in V2-V5 (>2mm)",
                "severity": "critical",
                "confidence": 0.96,
                "explanation": "Anterior wall STEMI pattern - LAD territory",
            },
            {
                "category": "morphology",
                "finding": "Q waves in V2-V4",
                "severity": "critical",
                "confidence": 0.92,
                "explanation": "Suggest ongoing or recent anterior MI",
            },
        ],
        algorithm_results=[
            {
                "name": "STEMI Localization",
                "conclusion": "Anterior STEMI - LAD territory",
                "confidence": 0.95,
                "steps": [
                    {"description": "ST elevation in V2-V5", "result": "Present"},
                    {"description": "Reciprocal changes", "result": "Inferior leads"},
                    {"description": "Culprit vessel", "result": "Left Anterior Descending (LAD)"},
                ],
            }
        ],
        summary="STEMI - Anterior wall myocardial infarction",
        primary_diagnosis="Anterior STEMI (ST-Elevation Myocardial Infarction)",
        differential_diagnoses=[
            "Pericarditis (less likely - no PR depression)",
            "Early repolarization (less likely - age and ST morphology)",
        ],
        confidence=0.95,
        is_urgent=True,
        urgency_reason="ST-Elevation Myocardial Infarction - Time is Muscle!",
        recommended_actions=[
            "ACTIVATE CATH LAB IMMEDIATELY",
            "Aspirin 325mg PO",
            "Clopidogrel 600mg loading dose",
            "Heparin bolus + infusion",
            "Cardiology on-call STAT",
            "Target door-to-balloon time: <90 minutes",
        ],
        teaching_points=[
            "Anterior STEMI: Look for ST elevation in V2-V5",
            "LAD occlusion: Most dangerous - supplies large territory",
            "Door-to-balloon time is critical: Every minute counts",
            "STEMI criteria: >1mm ST elevation in 2 contiguous leads",
        ],
        knowledge_sources=[
            "ACC/AHA STEMI Guidelines 2023",
            "Fiol et al. STEMI Localization Algorithms",
        ],
    )

    # Generate for different user levels
    generator = ReportGenerator()

    # For RMP (Rural Medical Practitioner)
    print("\n--- Report for RMP (Village Practitioner) ---\n")
    rmp_report = generator.generate_text(report, user_level=UserLevel.RMP, include_teaching=False)
    print(rmp_report[:800])  # Print first part
    print("\n[... truncated for demo ...]\n")

    # For Cardiologist
    print("\n--- Report for Cardiologist ---\n")
    cardio_report = generator.generate_text(report, user_level=UserLevel.CARDIOLOGIST)
    # Save full HTML
    html_report = generator.generate_html(report, user_level=UserLevel.CARDIOLOGIST)
    output_path = "/tmp/stemi_report.html"
    Path(output_path).write_text(html_report)
    print(f"Full HTML report saved to: {output_path}")


def demo_from_api_response():
    """Demo: Create report from API response format"""
    print("\n" + "=" * 80)
    print("DEMO 3: Create Report from API Response")
    print("=" * 80)

    # Simulate API response (from server.py ECGAnalysisResponse)
    api_response = {
        "analysis_id": "API-2026-001",
        "timestamp": datetime.now(),
        "processing_time_ms": 2350,
        "summary": "Wide complex tachycardia - likely VT",
        "measurements": {
            "heart_rate": 145,
            "rhythm": "wide_complex_tachycardia",
            "pr_interval_ms": None,
            "qrs_duration_ms": 165,
            "qt_interval_ms": 370,
            "qtc_ms": 480,
            "axis_degrees": -45,
        },
        "findings": [
            {
                "category": "rhythm",
                "finding": "Wide complex regular tachycardia",
                "severity": "critical",
                "confidence": 0.94,
                "explanation": "QRS >120ms with regular rhythm at 145 bpm",
            }
        ],
        "algorithm_results": [
            {
                "name": "Brugada",
                "conclusion": "VT",
                "confidence": 0.89,
                "steps": [
                    {"description": "RS in precordial leads", "result": "Absent"},
                ],
            },
            {
                "name": "Basel",
                "conclusion": "VT",
                "confidence": 0.93,
                "steps": [
                    {"description": "QRS >120ms", "result": "Yes - 165ms"},
                    {"description": "Extreme axis deviation", "result": "Yes - LAD"},
                ],
            },
        ],
        "primary_diagnosis": "Ventricular Tachycardia",
        "differential_diagnoses": ["SVT with aberrancy", "Antidromic AVRT"],
        "confidence": 0.91,
        "is_urgent": True,
        "urgency_reason": "Ventricular tachycardia - immediate intervention required",
        "recommended_actions": [
            "Check patient stability",
            "If unstable: Immediate synchronized cardioversion",
            "If stable: IV amiodarone 150mg over 10 min",
        ],
        "knowledge_sources": ["Brugada Criteria 1991", "Basel Algorithm 2022"],
    }

    # Convert to ECGReport
    patient = PatientInfo(name="Test Patient", age=58, sex="male")
    report = create_report_from_analysis(api_response, patient_info=patient)

    # Generate JSON (useful for API responses)
    generator = ReportGenerator()
    json_report = generator.generate_json(report)

    print("JSON Report (formatted):")
    print(json_report[:1000])
    print("\n[... truncated ...]\n")


def demo_user_level_adaptation():
    """Demo: Show how reports adapt to different user levels"""
    print("\n" + "=" * 80)
    print("DEMO 4: User Level Adaptation")
    print("=" * 80)

    # Create a moderately complex report
    report = ECGReport(
        report_id="ECG-ADAPT-001",
        timestamp=datetime.now(),
        quality_score=0.85,
        measurements={
            "heart_rate": 120,
            "rhythm": "supraventricular_tachycardia",
            "pr_interval_ms": None,
            "qrs_duration_ms": 90,
            "qt_interval_ms": 300,
            "qtc_ms": 380,
        },
        findings=[
            {
                "category": "rhythm",
                "finding": "Narrow complex tachycardia",
                "severity": "abnormal",
                "confidence": 0.92,
                "explanation": "Regular narrow QRS tachycardia at 120 bpm",
            }
        ],
        summary="Narrow complex tachycardia - SVT",
        primary_diagnosis="Supraventricular Tachycardia (SVT)",
        confidence=0.88,
        is_urgent=False,
        recommended_actions=[
            "Vagal maneuvers",
            "Adenosine if vagal maneuvers fail",
        ],
        teaching_points=[
            "SVT: Narrow QRS tachycardia originating above the ventricles",
            "Common subtypes: AVNRT, AVRT, Atrial tachycardia",
            "Vagal maneuvers: Valsalva, carotid massage",
        ],
    )

    generator = ReportGenerator()

    # Show summary adaptation
    for level in [UserLevel.RMP, UserLevel.STUDENT, UserLevel.RESIDENT]:
        print(f"\n--- {level.value.upper()} Level ---")
        print(generator._adapt_summary(report.summary, level))


def main():
    """Run all demos"""
    demo_simple_report()
    demo_critical_findings()
    demo_from_api_response()
    demo_user_level_adaptation()

    print("\n" + "=" * 80)
    print("DEMOS COMPLETE")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - /tmp/ecg_report.html (from module test)")
    print("  - /tmp/stemi_report.html (STEMI demo)")


if __name__ == "__main__":
    main()
