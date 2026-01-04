"""
Simple ECG Report Generation Demo

Direct import of report module without full package dependencies.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src/core to path to import report module directly
# This avoids importing core.__init__ which requires numpy
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

# Direct import of report module (bypassing core.__init__)
import report

ECGReport = report.ECGReport
PatientInfo = report.PatientInfo
ReportGenerator = report.ReportGenerator
UserLevel = report.UserLevel


def main():
    """Run a simple report generation demo"""

    print("=" * 80)
    print("ECG GURU - Report Generation Demo")
    print("=" * 80)
    print()

    # Create a sample STEMI report
    report = ECGReport(
        report_id="DEMO-STEMI-2026-001",
        timestamp=datetime.now(),
        analysis_duration_ms=1850,
        patient_info=PatientInfo(
            name="John Doe",
            age=62,
            sex="male",
            patient_id="P12345",
        ),
        quality_score=0.88,
        quality_warnings=["Slight baseline wander in lead V1"],
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
                "finding": "ST elevation >2mm in leads V2-V5",
                "severity": "critical",
                "confidence": 0.96,
                "explanation": "Marked ST elevation in anterior leads indicating acute anterior wall STEMI",
                "teaching_point": "Anterior STEMI is caused by LAD occlusion and requires immediate intervention",
            },
            {
                "category": "morphology",
                "finding": "Pathological Q waves in V2-V4",
                "severity": "critical",
                "confidence": 0.92,
                "explanation": "Q waves suggest transmural myocardial injury",
                "teaching_point": "Q waves can develop within hours in acute MI or may indicate old infarction",
            },
            {
                "category": "rhythm",
                "finding": "Sinus tachycardia",
                "severity": "abnormal",
                "confidence": 0.94,
                "explanation": "Heart rate 95 bpm - likely compensatory response to MI",
                "teaching_point": "Tachycardia in MI context is often compensatory but monitor for arrhythmias",
            },
        ],
        algorithm_results=[
            {
                "name": "STEMI Localization Algorithm",
                "conclusion": "Anterior STEMI - LAD territory",
                "confidence": 0.95,
                "steps": [
                    {
                        "description": "ST elevation in V2-V5",
                        "result": "Present (3-5mm elevation)",
                        "interpretation": "Anterior wall involvement",
                    },
                    {
                        "description": "Reciprocal changes in inferior leads",
                        "result": "Present (ST depression II, III, aVF)",
                        "interpretation": "Confirms anterior STEMI",
                    },
                    {
                        "description": "Culprit vessel determination",
                        "result": "Left Anterior Descending (LAD)",
                        "interpretation": "Based on V2-V5 distribution",
                    },
                ],
                "supports_vt": None,
                "supports_svt": None,
            }
        ],
        summary="Acute anterior STEMI with LAD occlusion - IMMEDIATE CATH LAB ACTIVATION REQUIRED",
        primary_diagnosis="Anterior ST-Elevation Myocardial Infarction (STEMI)",
        differential_diagnoses=[
            "Pericarditis (less likely - no PR depression, age, risk factors)",
            "Early repolarization (excluded - age inappropriate, ST morphology)",
            "Left ventricular aneurysm (less likely - acute presentation)",
        ],
        confidence=0.95,
        is_urgent=True,
        urgency_reason="ST-Elevation Myocardial Infarction - TIME IS MUSCLE! Door-to-balloon time critical",
        recommended_actions=[
            "🚨 ACTIVATE CATH LAB IMMEDIATELY - Page interventional cardiology STAT",
            "Aspirin 325mg PO (chewed) if not already given",
            "Clopidogrel 600mg OR Ticagrelor 180mg loading dose",
            "Heparin 60 units/kg IV bolus (max 4000 units) + infusion",
            "Morphine 2-4mg IV for pain if needed (caution: may mask symptoms)",
            "High-flow oxygen if SpO2 <90% (avoid hyperoxia)",
            "Establish IV access x2, draw labs (troponin, CBC, BMP, coags, lipids)",
            "Continuous cardiac monitoring for arrhythmias",
            "Target door-to-balloon time: <90 minutes",
            "If PCI not available: Consider fibrinolysis if <120 minutes from symptom onset",
        ],
        teaching_points=[
            "Anterior STEMI: ST elevation in V2-V5 indicates LAD occlusion",
            "LAD supplies the largest myocardial territory - high risk for cardiogenic shock",
            "STEMI criteria: ≥1mm (0.1mV) ST elevation in ≥2 contiguous limb leads OR ≥2mm in precordial leads",
            "Door-to-balloon time is critical: Every 30-minute delay increases 1-year mortality by 7.5%",
            "Reciprocal changes (ST depression in opposite leads) support STEMI diagnosis",
            "Q waves indicate transmural injury - may appear within hours or suggest old MI",
            "Primary PCI is preferred over fibrinolysis (better outcomes, lower bleeding risk)",
            "Antiplatelet therapy: Dual therapy (aspirin + P2Y12 inhibitor) is standard",
        ],
        similar_cases=[
            {
                "id": "CASE-001",
                "diagnosis": "Anterior STEMI",
                "similarity": 0.94,
                "key_features": "LAD occlusion, V2-V5 ST elevation",
            }
        ],
        knowledge_sources=[
            "ACC/AHA STEMI Guidelines 2023",
            "Fiol et al. STEMI Localization Algorithms",
            "ESC Guidelines for Acute Coronary Syndromes 2023",
            "Chou's Electrocardiography in Clinical Practice (6th Ed)",
        ],
    )

    # Generate reports in different formats
    generator = ReportGenerator()

    # 1. Text report for terminal
    print("\n" + "=" * 80)
    print("1. TEXT REPORT (for RMP - Rural Medical Practitioner)")
    print("=" * 80)
    rmp_report = generator.generate_text(report, user_level=UserLevel.RMP, include_teaching=False)
    print(rmp_report)

    # 2. HTML report
    print("\n" + "=" * 80)
    print("2. GENERATING HTML REPORTS...")
    print("=" * 80)

    # Generate for different user levels
    levels = [
        (UserLevel.RMP, "rmp_stemi_report.html"),
        (UserLevel.STUDENT, "student_stemi_report.html"),
        (UserLevel.RESIDENT, "resident_stemi_report.html"),
        (UserLevel.CARDIOLOGIST, "cardiologist_stemi_report.html"),
    ]

    for level, filename in levels:
        html = generator.generate_html(report, user_level=level, include_teaching=True)
        output_path = f"/tmp/{filename}"
        Path(output_path).write_text(html)
        print(f"   ✓ {level.value.upper():15} → {output_path}")

    # 3. JSON report
    print("\n" + "=" * 80)
    print("3. JSON REPORT (for API/Integration)")
    print("=" * 80)
    json_report = generator.generate_json(report)
    json_path = "/tmp/stemi_report.json"
    Path(json_path).write_text(json_report)
    print(f"   ✓ Saved to: {json_path}")
    print(f"\nFirst 500 characters:")
    print(json_report[:500] + "...")

    # 4. PDF report (if weasyprint or reportlab available)
    print("\n" + "=" * 80)
    print("4. PDF REPORT")
    print("=" * 80)
    try:
        pdf_bytes = generator.generate_pdf(
            report,
            user_level=UserLevel.CARDIOLOGIST,
            include_teaching=True,
            output_path="/tmp/stemi_report.pdf"
        )
        print(f"   ✓ PDF generated: /tmp/stemi_report.pdf ({len(pdf_bytes)} bytes)")
    except ImportError as e:
        print(f"   ⚠ PDF generation not available: {e}")
        print("   💡 Install with: pip install weasyprint  OR  pip install reportlab")

    # Summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE - Generated Reports:")
    print("=" * 80)
    print()
    print("HTML Reports (open in browser):")
    print("   • /tmp/rmp_stemi_report.html          (RMP - Simple, actionable)")
    print("   • /tmp/student_stemi_report.html      (Student - Educational)")
    print("   • /tmp/resident_stemi_report.html     (Resident - Clinical detail)")
    print("   • /tmp/cardiologist_stemi_report.html (Expert - Full analysis)")
    print()
    print("Data Formats:")
    print("   • /tmp/stemi_report.json              (JSON for APIs)")
    print("   • /tmp/stemi_report.pdf               (PDF for documentation)")
    print()
    print("📊 Report Features Demonstrated:")
    print("   ✓ User level adaptation (RMP → Cardiologist)")
    print("   ✓ Critical finding alerts (STEMI)")
    print("   ✓ Algorithm results with step-by-step breakdown")
    print("   ✓ Clinical recommendations (actionable)")
    print("   ✓ Teaching points (educational)")
    print("   ✓ Multiple output formats (Text/HTML/JSON/PDF)")
    print("   ✓ Color-coded severity (Normal/Abnormal/Critical)")
    print("   ✓ Printable HTML templates")
    print()


if __name__ == "__main__":
    main()
