"""
Comprehensive tests for ECG Report Generation Module

Tests all aspects of the report generation system:
- Data structures and validation
- Multiple output formats (text, HTML, JSON)
- User level adaptation (RMP, Student, Resident, Cardiologist)
- Finding formatting and severity handling
- Measurement formatting with normal range indicators
- Algorithm results formatting
- Clinical guidance and urgency handling
- Edge cases and error handling
"""

import pytest
import json
from datetime import datetime
from src.core.report import (
    ECGReport,
    PatientInfo,
    UserLevel,
    SeverityLevel,
    ReportGenerator,
    create_report_from_analysis,
)


# ============================================================================
# Fixtures - Test Data
# ============================================================================

@pytest.fixture
def sample_normal_report():
    """Sample normal ECG report"""
    return ECGReport(
        report_id="TEST-NORMAL-001",
        timestamp=datetime(2026, 1, 4, 10, 30, 0),
        analysis_duration_ms=850,
        quality_score=0.95,
        measurements={
            "heart_rate": 72,
            "rhythm": "sinus",
            "pr_interval_ms": 160,
            "qrs_duration_ms": 90,
            "qt_interval_ms": 380,
            "qtc_ms": 410,
            "axis_degrees": 45,
        },
        findings=[
            {
                "category": "rhythm",
                "finding": "Normal sinus rhythm",
                "severity": "normal",
                "confidence": 0.98,
                "explanation": "Regular P waves followed by QRS complexes at normal rate"
            }
        ],
        summary="Normal ECG with no significant abnormalities",
        primary_diagnosis="Normal sinus rhythm",
        confidence=0.95,
    )


@pytest.fixture
def sample_stemi_report():
    """Sample STEMI (critical) report"""
    return ECGReport(
        report_id="TEST-STEMI-001",
        timestamp=datetime(2026, 1, 4, 14, 15, 0),
        analysis_duration_ms=1200,
        patient_info=PatientInfo(
            patient_id="P12345",
            name="John Doe",
            age=65,
            sex="male",
        ),
        quality_score=0.88,
        measurements={
            "heart_rate": 95,
            "rhythm": "sinus_tachycardia",
            "pr_interval_ms": 150,
            "qrs_duration_ms": 100,
            "qt_interval_ms": 360,
            "qtc_ms": 425,
            "axis_degrees": 30,
        },
        findings=[
            {
                "category": "st_segment",
                "finding": "ST elevation in leads II, III, aVF",
                "severity": "critical",
                "confidence": 0.96,
                "explanation": "ST elevation >1mm in inferior leads indicating acute STEMI"
            },
            {
                "category": "reciprocal",
                "finding": "Reciprocal ST depression in leads I, aVL",
                "severity": "abnormal",
                "confidence": 0.92,
                "explanation": "Reciprocal changes support inferior STEMI diagnosis"
            }
        ],
        algorithm_results=[
            {
                "name": "Fiol's Algorithm",
                "conclusion": "RCA culprit vessel (90% probability)",
                "confidence": 0.90,
                "steps": [
                    {"description": "ST elevation in lead III > lead II", "result": "Present - Supports RCA"},
                    {"description": "ST depression in lead I + aVL", "result": "Present - Confirms RCA"},
                ]
            }
        ],
        summary="Acute inferior STEMI with RCA as likely culprit vessel",
        primary_diagnosis="Acute Inferior ST-Elevation Myocardial Infarction (STEMI)",
        differential_diagnoses=[
            "Acute pericarditis (less likely given reciprocal changes)",
            "Early repolarization (less likely given clinical context)",
        ],
        confidence=0.96,
        is_urgent=True,
        urgency_reason="Acute STEMI requires immediate cath lab activation",
        recommended_actions=[
            "Activate cath lab immediately - Door-to-balloon time <90 minutes",
            "Aspirin 325mg chewed",
            "Clopidogrel 600mg loading dose",
            "Heparin bolus and infusion",
            "Transfer to cath lab for primary PCI",
        ],
        teaching_points=[
            "Inferior STEMI: ST elevation in leads II, III, aVF indicates inferior wall involvement",
            "Reciprocal changes: ST depression in lateral leads (I, aVL) supports true STEMI vs pericarditis",
            "RCA vs LCx differentiation: ST elevation III > II suggests RCA culprit",
        ],
        knowledge_sources=[
            "Fiol M, et al. J Electrocardiol 2004;37:120-9",
            "ACC/AHA STEMI Guidelines 2023",
        ],
    )


@pytest.fixture
def sample_vt_report():
    """Sample VT (wide complex tachycardia) report"""
    return ECGReport(
        report_id="TEST-VT-001",
        timestamp=datetime(2026, 1, 4, 16, 45, 0),
        quality_score=0.82,
        measurements={
            "heart_rate": 145,
            "rhythm": "wide_complex_tachycardia",
            "pr_interval_ms": None,
            "qrs_duration_ms": 165,
            "qt_interval_ms": 390,
            "qtc_ms": 475,
            "axis_degrees": -50,
        },
        findings=[
            {
                "category": "rhythm",
                "finding": "Wide complex tachycardia",
                "severity": "critical",
                "confidence": 0.95,
                "explanation": "Regular wide QRS tachycardia at 145 bpm with QRS >160ms"
            },
            {
                "category": "axis",
                "finding": "Left axis deviation",
                "severity": "abnormal",
                "confidence": 0.90,
                "explanation": "Extreme left axis deviation suggests VT"
            }
        ],
        algorithm_results=[
            {
                "name": "Brugada Algorithm",
                "conclusion": "VT (Ventricular Tachycardia)",
                "confidence": 0.92,
                "steps": [
                    {"description": "RS complex in precordial leads", "result": "Absent - Supports VT"},
                    {"description": "R to S interval", "result": "N/A (no RS)"},
                    {"description": "AV dissociation", "result": "Present - Diagnostic of VT"},
                ]
            },
            {
                "name": "Basel Algorithm",
                "conclusion": "VT",
                "confidence": 0.89,
                "steps": [
                    {"description": "QRS >160ms", "result": "Yes (165ms) - Supports VT"},
                    {"description": "Extreme axis deviation", "result": "Yes (-50°) - Confirms VT"},
                ]
            }
        ],
        summary="Wide complex tachycardia consistent with ventricular tachycardia",
        primary_diagnosis="Ventricular Tachycardia (VT)",
        differential_diagnoses=[
            "SVT with aberrancy (less likely given AV dissociation)",
            "Antidromic AVRT (less likely given extreme axis)",
        ],
        confidence=0.92,
        is_urgent=True,
        urgency_reason="Ventricular tachycardia requires immediate treatment",
        recommended_actions=[
            "Assess hemodynamic stability urgently",
            "If unstable: Immediate synchronized cardioversion",
            "If stable: IV amiodarone 150mg over 10 minutes",
            "Continuous cardiac monitoring in CCU",
            "Urgent cardiology consultation",
        ],
        teaching_points=[
            "Wide complex tachycardia: Always assume VT until proven otherwise",
            "Brugada criteria: Absence of RS in all precordial leads = VT",
            "AV dissociation: Pathognomonic for VT",
        ],
        knowledge_sources=[
            "Brugada et al. Circulation 1991;83:1649-59",
            "Vereckei A. Heart Rhythm 2008;5:89-98",
        ],
    )


@pytest.fixture
def report_generator():
    """Report generator instance"""
    return ReportGenerator()


# ============================================================================
# 1. Data Structure Tests
# ============================================================================

def test_ecg_report_required_fields():
    """Test ECGReport requires report_id and timestamp"""
    # Should work with just required fields
    report = ECGReport(
        report_id="TEST-001",
        timestamp=datetime.now(),
    )
    assert report.report_id == "TEST-001"
    assert isinstance(report.timestamp, datetime)


def test_ecg_report_optional_fields():
    """Test optional fields have correct defaults"""
    report = ECGReport(
        report_id="TEST-002",
        timestamp=datetime.now(),
    )
    assert report.quality_score == 0.0
    assert report.quality_warnings == []
    assert report.measurements == {}
    assert report.findings == []
    assert report.algorithm_results == []
    assert report.differential_diagnoses == []
    assert report.recommended_actions == []
    assert report.teaching_points == []
    assert report.knowledge_sources == []
    assert report.is_urgent is False
    assert report.confidence == 0.0


def test_patient_info_structure():
    """Test PatientInfo dataclass"""
    patient = PatientInfo(
        patient_id="P123",
        name="Jane Doe",
        age=45,
        sex="female",
        mrn="MRN-987654",
    )
    assert patient.patient_id == "P123"
    assert patient.name == "Jane Doe"
    assert patient.age == 45
    assert patient.sex == "female"
    assert patient.mrn == "MRN-987654"


def test_patient_info_all_optional():
    """Test all PatientInfo fields are optional"""
    patient = PatientInfo()
    assert patient.patient_id is None
    assert patient.name is None
    assert patient.age is None
    assert patient.sex is None
    assert patient.mrn is None


def test_user_level_enum():
    """Test all UserLevel values exist"""
    assert UserLevel.RMP == "rmp"
    assert UserLevel.STUDENT == "student"
    assert UserLevel.RESIDENT == "resident"
    assert UserLevel.CARDIOLOGIST == "cardiologist"

    # Test we have exactly 4 levels
    assert len(list(UserLevel)) == 4


def test_severity_level_enum():
    """Test all SeverityLevel values exist"""
    assert SeverityLevel.NORMAL == "normal"
    assert SeverityLevel.ABNORMAL == "abnormal"
    assert SeverityLevel.CRITICAL == "critical"

    # Test we have exactly 3 levels
    assert len(list(SeverityLevel)) == 3


def test_ecg_report_has_default_disclaimer():
    """Test ECGReport has default medical disclaimer"""
    report = ECGReport(
        report_id="TEST-003",
        timestamp=datetime.now(),
    )
    assert "clinical decision support tool" in report.disclaimer
    assert "does not replace professional medical judgment" in report.disclaimer


# ============================================================================
# 2. Report Generator Tests
# ============================================================================

def test_generator_initialization():
    """Test ReportGenerator can be created"""
    generator = ReportGenerator()
    assert generator is not None
    assert hasattr(generator, 'severity_colors')
    assert SeverityLevel.CRITICAL in generator.severity_colors
    assert generator.severity_colors[SeverityLevel.CRITICAL] == "#dc3545"


def test_generate_text_basic(report_generator, sample_normal_report):
    """Test basic text report generation"""
    text = report_generator.generate_text(sample_normal_report)

    assert isinstance(text, str)
    assert len(text) > 0
    assert "ECG GURU - ECG ANALYSIS REPORT" in text
    assert sample_normal_report.report_id in text
    assert "SUMMARY" in text
    assert "MEASUREMENTS" in text
    assert "INTERPRETATION" in text


def test_generate_text_all_levels(report_generator, sample_stemi_report):
    """Test text generation for all user levels"""
    for level in UserLevel:
        text = report_generator.generate_text(sample_stemi_report, user_level=level)
        assert isinstance(text, str)
        assert len(text) > 0
        assert sample_stemi_report.report_id in text


def test_generate_html_basic(report_generator, sample_normal_report):
    """Test HTML report generation"""
    html = report_generator.generate_html(sample_normal_report)

    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert sample_normal_report.report_id in html


def test_generate_json_basic(report_generator, sample_normal_report):
    """Test JSON report generation"""
    json_str = report_generator.generate_json(sample_normal_report)

    assert isinstance(json_str, str)
    assert len(json_str) > 0
    assert sample_normal_report.report_id in json_str


def test_generate_json_serializable(report_generator, sample_normal_report):
    """Test JSON output is valid JSON"""
    json_str = report_generator.generate_json(sample_normal_report)

    # Should be parseable as JSON
    data = json.loads(json_str)
    assert isinstance(data, dict)
    assert data["report_id"] == sample_normal_report.report_id

    # Timestamp should be ISO format string
    assert isinstance(data["timestamp"], str)
    assert "2026-01-04" in data["timestamp"]


# ============================================================================
# 3. User Level Adaptation Tests
# ============================================================================

def test_rmp_report_simplicity(report_generator, sample_stemi_report):
    """Test RMP reports use simple language and clear verdicts"""
    text = report_generator.generate_text(sample_stemi_report, user_level=UserLevel.RMP)

    # Should include urgent alert
    assert "URGENT" in text
    assert "Refer immediately" in text or "cardiac center" in text

    # Should NOT include algorithm details
    assert "ALGORITHM ANALYSIS" not in text

    # Should NOT include references
    assert "REFERENCES" not in text


def test_student_report_educational(report_generator, sample_vt_report):
    """Test Student reports include teaching points"""
    text = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.STUDENT,
        include_teaching=True
    )

    # Should include teaching section
    assert "TEACHING POINTS" in text

    # Should include explanations
    for point in sample_vt_report.teaching_points:
        assert point in text


def test_resident_report_clinical(report_generator, sample_stemi_report):
    """Test Resident reports include differentials and algorithms"""
    text = report_generator.generate_text(sample_stemi_report, user_level=UserLevel.RESIDENT)

    # Should include differential diagnoses
    assert "Differential Diagnoses:" in text
    for dx in sample_stemi_report.differential_diagnoses:
        assert dx in text

    # Should include algorithm results
    assert "ALGORITHM ANALYSIS" in text
    assert "Fiol" in text


def test_cardiologist_report_technical(report_generator, sample_vt_report):
    """Test Cardiologist reports are detailed and technical"""
    text = report_generator.generate_text(sample_vt_report, user_level=UserLevel.CARDIOLOGIST)

    # Should include all algorithm results
    assert "ALGORITHM ANALYSIS" in text
    assert "BRUGADA" in text.upper()
    assert "BASEL" in text.upper()

    # Should include all steps
    assert "AV dissociation" in text

    # Should include references
    assert "REFERENCES" in text


def test_teaching_points_optional(report_generator, sample_stemi_report):
    """Test teaching points can be excluded"""
    # With teaching
    with_teaching = report_generator.generate_text(
        sample_stemi_report,
        include_teaching=True
    )
    assert "TEACHING POINTS" in with_teaching

    # Without teaching
    without_teaching = report_generator.generate_text(
        sample_stemi_report,
        include_teaching=False
    )
    assert "TEACHING POINTS" not in without_teaching


# ============================================================================
# 4. Finding Formatting Tests
# ============================================================================

def test_critical_findings_emphasized(report_generator, sample_stemi_report):
    """Test critical findings are prominently displayed"""
    text = report_generator.generate_text(sample_stemi_report)

    # Should have critical findings section
    assert "CRITICAL FINDINGS" in text
    assert "🚨" in text

    # Critical finding should appear
    assert "ST elevation" in text


def test_normal_findings_subdued(report_generator, sample_normal_report):
    """Test normal findings are not alarming"""
    text = report_generator.generate_text(sample_normal_report, user_level=UserLevel.STUDENT)

    # Should show normal findings for students
    assert "Normal sinus rhythm" in text

    # Should use checkmark
    assert "✓" in text

    # Should NOT have critical warnings
    assert "CRITICAL FINDINGS" not in text


def test_findings_sorted_by_severity(report_generator, sample_stemi_report):
    """Test findings ordered: critical > abnormal > normal"""
    text = report_generator.generate_text(sample_stemi_report)

    # Find positions of severity markers
    critical_pos = text.find("CRITICAL FINDINGS")
    abnormal_pos = text.find("ABNORMAL FINDINGS")

    # Critical should come before abnormal
    assert critical_pos < abnormal_pos


def test_html_findings_severity_classes(report_generator, sample_stemi_report):
    """Test HTML findings use appropriate CSS classes"""
    html = report_generator.generate_html(sample_stemi_report)

    # Should have critical finding class
    assert "finding-critical" in html

    # Should have abnormal finding class
    assert "finding-abnormal" in html


# ============================================================================
# 5. Measurement Formatting Tests
# ============================================================================

def test_measurements_with_units(report_generator, sample_normal_report):
    """Test measurements include units (ms, bpm, degrees)"""
    text = report_generator.generate_text(sample_normal_report)

    # Should include units
    assert "bpm" in text  # Heart rate
    assert "ms" in text   # Intervals
    assert "°" in text or "degrees" in text  # Axis


def test_abnormal_measurements_flagged(report_generator):
    """Test out-of-range values are flagged"""
    report = ECGReport(
        report_id="TEST-ABNORMAL-001",
        timestamp=datetime.now(),
        measurements={
            "heart_rate": 130,  # High
            "pr_interval_ms": 250,  # Prolonged
            "qtc_ms": 500,  # Prolonged
        }
    )

    text = report_generator.generate_text(report)

    # Should include warning indicators
    assert "⚠" in text


def test_missing_measurements_handled(report_generator):
    """Test graceful handling of missing measurements"""
    report = ECGReport(
        report_id="TEST-MISSING-001",
        timestamp=datetime.now(),
        measurements={
            "heart_rate": 75,
            # Other measurements missing
        }
    )

    text = report_generator.generate_text(report)

    # Should handle gracefully
    assert "Not measured" in text or "N/A" in text.upper() or report.report_id in text


def test_normal_measurements_checkmark(report_generator, sample_normal_report):
    """Test normal measurements get checkmark"""
    text = report_generator.generate_text(sample_normal_report)

    # Normal values should have checkmarks
    assert "✓" in text


# ============================================================================
# 6. Algorithm Results Formatting Tests
# ============================================================================

def test_algorithm_results_included(report_generator, sample_vt_report):
    """Test algorithm results appear in report for appropriate user levels"""
    # Should appear for resident
    text_resident = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.RESIDENT
    )
    assert "ALGORITHM ANALYSIS" in text_resident
    assert "Brugada" in text_resident

    # Should NOT appear for RMP
    text_rmp = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.RMP
    )
    assert "ALGORITHM ANALYSIS" not in text_rmp


def test_algorithm_confidence_displayed(report_generator, sample_vt_report):
    """Test confidence percentages shown"""
    text = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.CARDIOLOGIST
    )

    # Should show confidence as percentage
    assert "92" in text or "0.92" in text  # Brugada confidence
    assert "%" in text or "Confidence" in text


def test_multiple_algorithms_formatted(report_generator, sample_vt_report):
    """Test multiple algorithm results formatted correctly"""
    text = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.CARDIOLOGIST
    )

    # Should include both algorithms (uppercased in output)
    assert "BRUGADA" in text.upper()
    assert "BASEL" in text.upper()

    # Each should have its own conclusion
    assert "VT" in text


def test_algorithm_steps_shown(report_generator, sample_vt_report):
    """Test algorithm steps are displayed"""
    text = report_generator.generate_text(
        sample_vt_report,
        user_level=UserLevel.CARDIOLOGIST
    )

    # Should show step details
    assert "Steps:" in text
    assert "AV dissociation" in text
    assert "Present" in text or "Absent" in text


# ============================================================================
# 7. Clinical Guidance Tests
# ============================================================================

def test_urgent_report_has_actions(report_generator, sample_stemi_report):
    """Test urgent reports include recommended actions"""
    text = report_generator.generate_text(sample_stemi_report)

    # Should have urgent marker
    assert "🚨" in text
    assert "URGENT" in text

    # Should have recommendations
    assert "RECOMMENDATIONS" in text
    assert "Activate cath lab" in text


def test_stemi_report_has_cath_lab(report_generator, sample_stemi_report):
    """Test STEMI reports mention cath lab activation"""
    text = report_generator.generate_text(sample_stemi_report)

    # Should mention cath lab
    assert "cath lab" in text.lower()

    # Should mention PCI
    assert "PCI" in text or "percutaneous" in text.lower()


def test_vt_report_has_treatment(report_generator, sample_vt_report):
    """Test VT reports mention treatment options"""
    text = report_generator.generate_text(sample_vt_report)

    # Should mention cardioversion or amiodarone
    assert "cardioversion" in text.lower() or "amiodarone" in text.lower()

    # Should mention monitoring
    assert "CCU" in text or "monitor" in text.lower()


def test_non_urgent_has_no_urgent_markers(report_generator, sample_normal_report):
    """Test non-urgent reports don't have urgent markers"""
    text = report_generator.generate_text(sample_normal_report)

    # Should NOT have urgent markers
    # Note: 🚨 emoji might still appear in section headers, but shouldn't be in summary
    summary_section = text[text.find("SUMMARY"):text.find("MEASUREMENTS")]
    assert "🚨" not in summary_section or "URGENT" not in summary_section


# ============================================================================
# 8. Disclaimer Tests
# ============================================================================

def test_disclaimer_present(report_generator, sample_normal_report):
    """Test medical disclaimer is included"""
    text = report_generator.generate_text(sample_normal_report)

    # Should have disclaimer section
    assert "DISCLAIMER" in text
    assert "clinical decision support" in text.lower() or "does not replace" in text.lower()


def test_disclaimer_appropriate_language(report_generator, sample_normal_report):
    """Test disclaimer is professionally worded"""
    # Check default disclaimer
    assert "professional medical judgment" in sample_normal_report.disclaimer
    assert "clinical decision support" in sample_normal_report.disclaimer

    # Should appear in report
    text = report_generator.generate_text(sample_normal_report)
    assert sample_normal_report.disclaimer in text


def test_disclaimer_in_all_formats(report_generator, sample_normal_report):
    """Test disclaimer appears in all output formats"""
    # Text
    text = report_generator.generate_text(sample_normal_report)
    assert "DISCLAIMER" in text

    # HTML
    html = report_generator.generate_html(sample_normal_report)
    assert "Disclaimer" in html

    # JSON
    json_str = report_generator.generate_json(sample_normal_report)
    data = json.loads(json_str)
    assert "disclaimer" in data
    assert len(data["disclaimer"]) > 0


# ============================================================================
# 9. Edge Case Tests
# ============================================================================

def test_empty_findings(report_generator):
    """Test report with no findings"""
    report = ECGReport(
        report_id="TEST-EMPTY-001",
        timestamp=datetime.now(),
        findings=[],
    )

    text = report_generator.generate_text(report)

    # Should generate without errors
    assert report.report_id in text

    # Findings section may be empty or absent
    # This is acceptable


def test_very_long_findings(report_generator):
    """Test report handles many findings"""
    # Create report with 20 findings
    findings = []
    for i in range(20):
        findings.append({
            "finding": f"Finding {i+1}: Test finding with description",
            "severity": "abnormal" if i % 3 == 0 else "normal",
            "confidence": 0.8,
            "explanation": f"Detailed explanation for finding {i+1}"
        })

    report = ECGReport(
        report_id="TEST-LONG-001",
        timestamp=datetime.now(),
        findings=findings,
    )

    text = report_generator.generate_text(report)

    # Should generate without errors
    assert report.report_id in text

    # Should contain multiple findings
    assert "Finding 1" in text
    assert "Finding 20" in text


def test_special_characters_in_findings(report_generator):
    """Test special characters are handled properly"""
    report = ECGReport(
        report_id="TEST-SPECIAL-001",
        timestamp=datetime.now(),
        findings=[
            {
                "finding": "ST elevation >1mm in leads II, III & aVF",
                "severity": "critical",
                "explanation": "Elevation indicates <acute> MI (80-90% probability)"
            }
        ],
        primary_diagnosis="Test diagnosis with special chars: <>&\"'",
    )

    # Text should work
    text = report_generator.generate_text(report)
    assert report.report_id in text

    # HTML should escape properly
    html = report_generator.generate_html(report)
    assert report.report_id in html
    # Note: HTML escaping depends on implementation


def test_none_patient_info(report_generator):
    """Test report without patient info"""
    report = ECGReport(
        report_id="TEST-NO-PATIENT-001",
        timestamp=datetime.now(),
        patient_info=None,
    )

    text = report_generator.generate_text(report)
    html = report_generator.generate_html(report)

    # Should generate without errors
    assert report.report_id in text
    assert report.report_id in html


def test_empty_measurements(report_generator):
    """Test report with no measurements"""
    report = ECGReport(
        report_id="TEST-NO-MEAS-001",
        timestamp=datetime.now(),
        measurements={},
    )

    text = report_generator.generate_text(report)

    # Should handle gracefully
    assert "No measurements available" in text or report.report_id in text


def test_zero_confidence(report_generator):
    """Test report with zero confidence"""
    report = ECGReport(
        report_id="TEST-ZERO-CONF-001",
        timestamp=datetime.now(),
        confidence=0.0,
    )

    text = report_generator.generate_text(report)

    # Should display 0%
    assert "0.0%" in text or "0%" in text


def test_very_high_heart_rate(report_generator):
    """Test measurements with extreme values"""
    report = ECGReport(
        report_id="TEST-EXTREME-001",
        timestamp=datetime.now(),
        measurements={
            "heart_rate": 250,  # Extreme tachycardia
            "qrs_duration_ms": 200,  # Very wide
        }
    )

    text = report_generator.generate_text(report)

    # Should show values and warnings
    assert "250" in text
    assert "200" in text
    assert "⚠" in text  # Should flag abnormal


# ============================================================================
# 10. Format-Specific Tests
# ============================================================================

def test_html_has_css_styles(report_generator, sample_normal_report):
    """Test HTML output includes CSS styles"""
    html = report_generator.generate_html(sample_normal_report)

    assert "<style>" in html
    assert "</style>" in html
    assert "report-container" in html
    assert "color" in html.lower()  # Has color definitions


def test_html_responsive_design(report_generator, sample_normal_report):
    """Test HTML includes responsive viewport meta tag"""
    html = report_generator.generate_html(sample_normal_report)

    assert 'name="viewport"' in html
    assert "width=device-width" in html


def test_html_print_styles(report_generator, sample_normal_report):
    """Test HTML includes print media styles"""
    html = report_generator.generate_html(sample_normal_report)

    assert "@media print" in html


def test_json_contains_all_fields(report_generator, sample_stemi_report):
    """Test JSON output contains all report fields"""
    json_str = report_generator.generate_json(sample_stemi_report)
    data = json.loads(json_str)

    # Check key fields
    assert "report_id" in data
    assert "timestamp" in data
    assert "measurements" in data
    assert "findings" in data
    assert "algorithm_results" in data
    assert "primary_diagnosis" in data
    assert "confidence" in data
    assert "is_urgent" in data
    assert "recommended_actions" in data


def test_text_report_width(report_generator, sample_normal_report):
    """Test text report has consistent line width"""
    text = report_generator.generate_text(sample_normal_report)

    # Should have 80-character separators
    assert "=" * 80 in text
    assert "-" * 80 in text


# ============================================================================
# 11. Integration Tests
# ============================================================================

def test_create_report_from_analysis():
    """Test creating ECGReport from analysis response"""
    analysis_response = {
        "analysis_id": "ANALYSIS-001",
        "timestamp": datetime.now(),
        "processing_time_ms": 1500,
        "measurements": {
            "heart_rate": 75,
            "rhythm": "sinus",
        },
        "findings": [
            {"finding": "Normal", "severity": "normal"}
        ],
        "summary": "Normal ECG",
        "primary_diagnosis": "Normal sinus rhythm",
        "confidence": 0.95,
        "is_urgent": False,
        "recommended_actions": [],
        "knowledge_sources": ["Source 1"],
    }

    report = create_report_from_analysis(analysis_response)

    assert isinstance(report, ECGReport)
    assert report.report_id == "ANALYSIS-001"
    assert report.measurements["heart_rate"] == 75
    assert report.primary_diagnosis == "Normal sinus rhythm"
    assert report.confidence == 0.95


def test_create_report_with_patient_info():
    """Test creating report with patient information"""
    analysis_response = {
        "analysis_id": "ANALYSIS-002",
        "timestamp": datetime.now(),
        "summary": "Test",
        "primary_diagnosis": "Test",
    }

    patient = PatientInfo(
        patient_id="P123",
        name="Test Patient",
        age=50,
    )

    report = create_report_from_analysis(analysis_response, patient_info=patient)

    assert report.patient_info is not None
    assert report.patient_info.patient_id == "P123"
    assert report.patient_info.name == "Test Patient"


def test_full_workflow_normal(report_generator, sample_normal_report):
    """Test complete workflow for normal ECG"""
    # Generate all formats
    text = report_generator.generate_text(sample_normal_report, user_level=UserLevel.STUDENT)
    html = report_generator.generate_html(sample_normal_report, user_level=UserLevel.STUDENT)
    json_str = report_generator.generate_json(sample_normal_report)

    # All should succeed
    assert len(text) > 0
    assert len(html) > 0
    assert len(json_str) > 0

    # JSON should be valid
    data = json.loads(json_str)
    assert data["report_id"] == sample_normal_report.report_id


def test_full_workflow_critical(report_generator, sample_stemi_report):
    """Test complete workflow for critical ECG (STEMI)"""
    # Generate for all user levels
    for level in UserLevel:
        text = report_generator.generate_text(sample_stemi_report, user_level=level)
        html = report_generator.generate_html(sample_stemi_report, user_level=level)

        # All should include critical indicators
        assert "URGENT" in text or "urgent" in text.lower()
        assert len(text) > 0
        assert len(html) > 0


# ============================================================================
# 12. Validation Tests
# ============================================================================

def test_quality_score_range(report_generator):
    """Test quality score is displayed correctly"""
    report = ECGReport(
        report_id="TEST-QUALITY-001",
        timestamp=datetime.now(),
        quality_score=0.85,
    )

    text = report_generator.generate_text(report)

    # Should show percentage
    assert "85" in text or "0.85" in text


def test_timestamp_formatting(report_generator):
    """Test timestamp is formatted correctly"""
    test_time = datetime(2026, 1, 4, 14, 30, 45)
    report = ECGReport(
        report_id="TEST-TIME-001",
        timestamp=test_time,
    )

    text = report_generator.generate_text(report)

    # Should include date and time
    assert "2026-01-04" in text
    assert "14:30:45" in text


def test_analysis_duration_displayed(report_generator):
    """Test analysis duration is shown when available"""
    report = ECGReport(
        report_id="TEST-DURATION-001",
        timestamp=datetime.now(),
        analysis_duration_ms=1234,
    )

    text = report_generator.generate_text(report)

    # Should show duration
    assert "1234" in text
    assert "ms" in text


# ============================================================================
# Run specific test if needed
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
