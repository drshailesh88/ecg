"""
ECG Report Generation Module

Generates professional ECG analysis reports in multiple formats:
- Plain text (for terminal/console)
- HTML (for web/print)
- JSON (for API/integration)
- PDF (for clinical documentation)

Reports adapt to user expertise level (RMP, Student, Resident, Cardiologist).
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


# ============================================================================
# Report Data Structure
# ============================================================================

@dataclass
class PatientInfo:
    """Optional patient demographic information"""
    patient_id: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None  # "male", "female"
    mrn: Optional[str] = None  # Medical record number


@dataclass
class ECGReport:
    """
    Complete ECG analysis report.

    This is the comprehensive data structure that can be rendered
    in multiple formats (text, HTML, PDF, JSON).
    """
    # Metadata
    report_id: str
    timestamp: datetime
    analysis_duration_ms: Optional[int] = None

    # Patient information (optional)
    patient_info: Optional[PatientInfo] = None

    # ECG Quality
    quality_score: float = 0.0
    quality_warnings: List[str] = field(default_factory=list)

    # Measurements (from measurement extractor)
    measurements: Dict[str, Any] = field(default_factory=dict)

    # Findings (categorized)
    findings: List[Dict[str, Any]] = field(default_factory=list)

    # Algorithm results (Brugada, Basel, SMART-WPW, etc.)
    algorithm_results: List[Dict[str, Any]] = field(default_factory=list)

    # Interpretation
    summary: str = ""
    primary_diagnosis: str = ""
    differential_diagnoses: List[str] = field(default_factory=list)
    confidence: float = 0.0

    # Clinical guidance
    is_urgent: bool = False
    urgency_reason: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)

    # Educational content (if requested)
    teaching_points: List[str] = field(default_factory=list)
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)

    # Knowledge sources
    knowledge_sources: List[str] = field(default_factory=list)

    # Disclaimer
    disclaimer: str = (
        "This ECG analysis is a clinical decision support tool and does not "
        "replace professional medical judgment. All findings should be "
        "correlated with clinical context and confirmed by a qualified physician."
    )


class UserLevel(str, Enum):
    """User expertise level"""
    RMP = "rmp"                    # Village practitioner
    STUDENT = "student"            # MBBS student
    RESIDENT = "resident"          # MD/DM resident
    CARDIOLOGIST = "cardiologist"  # Expert


class SeverityLevel(str, Enum):
    """Finding severity for color coding"""
    NORMAL = "normal"          # Green
    ABNORMAL = "abnormal"      # Yellow/Orange
    CRITICAL = "critical"      # Red


# ============================================================================
# Report Generator
# ============================================================================

class ReportGenerator:
    """
    Generates ECG reports in multiple formats.

    Adapts content complexity based on user expertise level.
    """

    def __init__(self):
        """Initialize report generator"""
        self.severity_colors = {
            SeverityLevel.NORMAL: "#28a745",    # Green
            SeverityLevel.ABNORMAL: "#ffc107",  # Yellow
            SeverityLevel.CRITICAL: "#dc3545",  # Red
        }

    # ========================================================================
    # Format: Plain Text
    # ========================================================================

    def generate_text(
        self,
        report: ECGReport,
        user_level: UserLevel = UserLevel.STUDENT,
        include_teaching: bool = True,
    ) -> str:
        """
        Generate plain text report.

        Args:
            report: ECG report data
            user_level: Target user expertise level
            include_teaching: Include educational content

        Returns:
            Formatted plain text report
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("ECG GURU - ECG ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Timestamp
        lines.append(f"Report ID: {report.report_id}")
        lines.append(f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        if report.analysis_duration_ms:
            lines.append(f"Analysis time: {report.analysis_duration_ms}ms")
        lines.append("")

        # Patient info (if provided)
        if report.patient_info:
            lines.append("PATIENT INFORMATION")
            lines.append("-" * 80)
            if report.patient_info.name:
                lines.append(f"Name: {report.patient_info.name}")
            if report.patient_info.patient_id:
                lines.append(f"Patient ID: {report.patient_info.patient_id}")
            if report.patient_info.age:
                lines.append(f"Age: {report.patient_info.age} years")
            if report.patient_info.sex:
                lines.append(f"Sex: {report.patient_info.sex.capitalize()}")
            lines.append("")

        # ECG Quality
        lines.append("ECG QUALITY")
        lines.append("-" * 80)
        lines.append(f"Quality Score: {report.quality_score:.1%}")
        if report.quality_warnings:
            lines.append("Warnings:")
            for warning in report.quality_warnings:
                lines.append(f"  ⚠ {warning}")
        lines.append("")

        # Summary (adapted to user level)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        if report.is_urgent:
            lines.append(f"🚨 URGENT: {report.urgency_reason}")
            lines.append("")
        lines.append(self._adapt_summary(report.summary, user_level))
        lines.append("")

        # Measurements
        lines.append("MEASUREMENTS")
        lines.append("-" * 80)
        lines.extend(self._format_measurements_text(report.measurements))
        lines.append("")

        # Findings
        if report.findings:
            lines.append("FINDINGS")
            lines.append("-" * 80)
            lines.extend(self._format_findings_text(report.findings, user_level))
            lines.append("")

        # Algorithm Results (for Resident & Cardiologist)
        if report.algorithm_results and user_level in [UserLevel.RESIDENT, UserLevel.CARDIOLOGIST]:
            lines.append("ALGORITHM ANALYSIS")
            lines.append("-" * 80)
            lines.extend(self._format_algorithms_text(report.algorithm_results))
            lines.append("")

        # Interpretation
        lines.append("INTERPRETATION")
        lines.append("-" * 80)
        lines.append(f"Primary Diagnosis: {report.primary_diagnosis}")
        if report.differential_diagnoses:
            lines.append("\nDifferential Diagnoses:")
            for i, dx in enumerate(report.differential_diagnoses, 1):
                lines.append(f"  {i}. {dx}")
        lines.append(f"\nDiagnostic Confidence: {report.confidence:.1%}")
        lines.append("")

        # Recommendations
        if report.recommended_actions:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for i, action in enumerate(report.recommended_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")

        # Teaching Points (if requested)
        if include_teaching and report.teaching_points:
            lines.append("TEACHING POINTS")
            lines.append("-" * 80)
            for i, point in enumerate(report.teaching_points, 1):
                lines.append(f"\n{i}. {point}")
            lines.append("")

        # Sources
        if report.knowledge_sources and user_level != UserLevel.RMP:
            lines.append("REFERENCES")
            lines.append("-" * 80)
            for source in report.knowledge_sources:
                lines.append(f"• {source}")
            lines.append("")

        # Disclaimer
        lines.append("DISCLAIMER")
        lines.append("-" * 80)
        lines.append(report.disclaimer)
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    # ========================================================================
    # Format: HTML
    # ========================================================================

    def generate_html(
        self,
        report: ECGReport,
        user_level: UserLevel = UserLevel.STUDENT,
        include_teaching: bool = True,
    ) -> str:
        """
        Generate HTML report (printable).

        Args:
            report: ECG report data
            user_level: Target user expertise level
            include_teaching: Include educational content

        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECG Analysis Report - {report.report_id}</title>
    <style>
        {self._get_html_styles()}
    </style>
</head>
<body>
    <div class="report-container">
        {self._generate_html_header(report)}
        {self._generate_html_patient_info(report)}
        {self._generate_html_quality(report)}
        {self._generate_html_summary(report, user_level)}
        {self._generate_html_measurements(report)}
        {self._generate_html_findings(report, user_level)}
        {self._generate_html_algorithms(report, user_level)}
        {self._generate_html_interpretation(report)}
        {self._generate_html_recommendations(report)}
        {self._generate_html_teaching(report, include_teaching)}
        {self._generate_html_sources(report, user_level)}
        {self._generate_html_disclaimer(report)}
    </div>
    <script>
        // Print functionality
        window.print = function() {{
            window.print();
        }};
    </script>
</body>
</html>"""
        return html

    # ========================================================================
    # Format: JSON
    # ========================================================================

    def generate_json(self, report: ECGReport) -> str:
        """
        Generate JSON report (for API/integration).

        Args:
            report: ECG report data

        Returns:
            JSON string
        """
        data = asdict(report)

        # Convert datetime to ISO format
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()

        return json.dumps(data, indent=2, default=str)

    # ========================================================================
    # Format: PDF
    # ========================================================================

    def generate_pdf(
        self,
        report: ECGReport,
        user_level: UserLevel = UserLevel.STUDENT,
        include_teaching: bool = True,
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate PDF report.

        Args:
            report: ECG report data
            user_level: Target user expertise level
            include_teaching: Include educational content
            output_path: Optional path to save PDF file

        Returns:
            PDF bytes
        """
        try:
            from weasyprint import HTML

            # Generate HTML first
            html_content = self.generate_html(report, user_level, include_teaching)

            # Convert to PDF
            pdf_bytes = HTML(string=html_content).write_pdf()

            # Save if path provided
            if output_path:
                Path(output_path).write_bytes(pdf_bytes)

            return pdf_bytes

        except ImportError:
            # Fallback: Try reportlab
            return self._generate_pdf_reportlab(report, user_level, include_teaching, output_path)

    # ========================================================================
    # Helper Methods: Text Format
    # ========================================================================

    def _format_measurements_text(self, measurements: Dict[str, Any]) -> List[str]:
        """Format measurements as text table"""
        lines = []

        if not measurements:
            lines.append("No measurements available")
            return lines

        # Format key measurements
        items = [
            ("Heart Rate", measurements.get("heart_rate"), "bpm"),
            ("Rhythm", measurements.get("rhythm"), ""),
            ("PR Interval", measurements.get("pr_interval_ms"), "ms"),
            ("QRS Duration", measurements.get("qrs_duration_ms"), "ms"),
            ("QT Interval", measurements.get("qt_interval_ms"), "ms"),
            ("QTc", measurements.get("qtc_ms"), "ms"),
            ("Axis", measurements.get("axis_degrees"), "°"),
        ]

        for label, value, unit in items:
            if value is not None:
                # Add normal range indicators
                normal_indicator = self._get_normal_indicator(label, value)
                lines.append(f"  {label:.<30} {value} {unit} {normal_indicator}")
            else:
                lines.append(f"  {label:.<30} Not measured")

        return lines

    def _format_findings_text(
        self,
        findings: List[Dict[str, Any]],
        user_level: UserLevel
    ) -> List[str]:
        """Format findings as text"""
        lines = []

        # Group by severity
        critical = [f for f in findings if f.get("severity") == "critical"]
        abnormal = [f for f in findings if f.get("severity") == "abnormal"]
        normal = [f for f in findings if f.get("severity") == "normal"]

        # Critical findings first
        if critical:
            lines.append("🚨 CRITICAL FINDINGS:")
            for finding in critical:
                lines.append(f"  • {finding.get('finding')}")
                if user_level != UserLevel.RMP:
                    lines.append(f"    {finding.get('explanation', '')}")
                lines.append("")

        # Abnormal findings
        if abnormal:
            lines.append("⚠ ABNORMAL FINDINGS:")
            for finding in abnormal:
                lines.append(f"  • {finding.get('finding')}")
                if user_level != UserLevel.RMP:
                    lines.append(f"    {finding.get('explanation', '')}")
                lines.append("")

        # Normal findings (brief for non-students)
        if normal and user_level in [UserLevel.STUDENT, UserLevel.RESIDENT]:
            lines.append("✓ NORMAL FINDINGS:")
            for finding in normal:
                lines.append(f"  • {finding.get('finding')}")

        return lines

    def _format_algorithms_text(self, algorithm_results: List[Dict[str, Any]]) -> List[str]:
        """Format algorithm results as text"""
        lines = []

        for algo in algorithm_results:
            lines.append(f"\n{algo.get('name', 'Unknown').upper()}")
            lines.append(f"  Conclusion: {algo.get('conclusion', 'N/A')}")
            lines.append(f"  Confidence: {algo.get('confidence', 0):.1%}")

            # Show steps
            steps = algo.get('steps', [])
            if steps:
                lines.append("  Steps:")
                for i, step in enumerate(steps, 1):
                    step_desc = step.get('description', '')
                    step_result = step.get('result', '')
                    lines.append(f"    {i}. {step_desc}: {step_result}")

        return lines

    def _get_normal_indicator(self, label: str, value: Any) -> str:
        """Get normal range indicator for a measurement"""
        # Normal ranges
        ranges = {
            "Heart Rate": (60, 100),
            "PR Interval": (120, 200),
            "QRS Duration": (80, 120),
            "QTc": (340, 450),  # Simplified
            "Axis": (-30, 90),
        }

        if label not in ranges or value is None:
            return ""

        min_val, max_val = ranges[label]

        try:
            value = float(value)
            if min_val <= value <= max_val:
                return "✓"
            else:
                return "⚠"
        except (ValueError, TypeError):
            return ""

    def _adapt_summary(self, summary: str, user_level: UserLevel) -> str:
        """Adapt summary based on user level"""
        # For RMP: Keep it simple
        if user_level == UserLevel.RMP:
            if "STEMI" in summary or "critical" in summary.lower():
                return f"🚨 URGENT: {summary}\n\nACTION: Refer immediately to nearest cardiac center."
            elif "abnormal" in summary.lower():
                return f"ABNORMAL ECG detected. Recommend cardiology consultation."
            else:
                return summary

        # For others: Return as-is
        return summary

    # ========================================================================
    # Helper Methods: HTML Format
    # ========================================================================

    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        @media print {
            body { margin: 0; }
            .no-print { display: none; }
            .page-break { page-break-after: always; }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }

        .report-container {
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1, h2, h3 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }

        h1 {
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }

        h2 {
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #3498db;
            margin-bottom: 10px;
        }

        .header .metadata {
            color: #7f8c8d;
            font-size: 14px;
        }

        .section {
            margin-bottom: 30px;
        }

        .urgent-alert {
            background: #dc3545;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: bold;
            font-size: 18px;
        }

        .quality-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }

        .quality-high { background: #28a745; }
        .quality-medium { background: #ffc107; color: #333; }
        .quality-low { background: #dc3545; }

        .measurements-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        .measurements-table th,
        .measurements-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }

        .measurements-table th {
            background: #3498db;
            color: white;
            font-weight: bold;
        }

        .measurements-table tr:hover {
            background: #f8f9fa;
        }

        .finding {
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid;
            border-radius: 4px;
        }

        .finding-critical {
            background: #f8d7da;
            border-color: #dc3545;
        }

        .finding-abnormal {
            background: #fff3cd;
            border-color: #ffc107;
        }

        .finding-normal {
            background: #d4edda;
            border-color: #28a745;
        }

        .finding-title {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .finding-explanation {
            color: #666;
            font-size: 14px;
        }

        .algorithm-result {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }

        .algorithm-name {
            font-weight: bold;
            color: #3498db;
            font-size: 16px;
            margin-bottom: 8px;
        }

        .algorithm-steps {
            margin-top: 10px;
            padding-left: 20px;
        }

        .algorithm-step {
            margin: 5px 0;
            font-size: 14px;
        }

        .confidence-bar {
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }

        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #3498db);
            transition: width 0.3s;
        }

        .recommendations {
            background: #e7f3ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }

        .recommendations ol {
            margin: 10px 0;
            padding-left: 20px;
        }

        .recommendations li {
            margin: 8px 0;
        }

        .teaching-section {
            background: #fff9e6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .teaching-point {
            margin: 15px 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }

        .disclaimer {
            background: #f8f9fa;
            padding: 15px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 12px;
            color: #666;
            margin-top: 30px;
        }

        .footer {
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
        }

        @media print {
            .report-container {
                box-shadow: none;
                padding: 0;
            }
        }
        """

    def _generate_html_header(self, report: ECGReport) -> str:
        """Generate HTML header section"""
        return f"""
        <div class="header">
            <h1>ECG GURU - ECG Analysis Report</h1>
            <div class="metadata">
                <p><strong>Report ID:</strong> {report.report_id}</p>
                <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                {f'<p><strong>Analysis Time:</strong> {report.analysis_duration_ms}ms</p>' if report.analysis_duration_ms else ''}
            </div>
        </div>
        """

    def _generate_html_patient_info(self, report: ECGReport) -> str:
        """Generate HTML patient information section"""
        if not report.patient_info:
            return ""

        info = report.patient_info
        return f"""
        <div class="section">
            <h2>Patient Information</h2>
            <table class="measurements-table">
                {f'<tr><td><strong>Name</strong></td><td>{info.name}</td></tr>' if info.name else ''}
                {f'<tr><td><strong>Patient ID</strong></td><td>{info.patient_id}</td></tr>' if info.patient_id else ''}
                {f'<tr><td><strong>Age</strong></td><td>{info.age} years</td></tr>' if info.age else ''}
                {f'<tr><td><strong>Sex</strong></td><td>{info.sex.capitalize()}</td></tr>' if info.sex else ''}
                {f'<tr><td><strong>MRN</strong></td><td>{info.mrn}</td></tr>' if info.mrn else ''}
            </table>
        </div>
        """

    def _generate_html_quality(self, report: ECGReport) -> str:
        """Generate HTML quality section"""
        quality = report.quality_score
        badge_class = "quality-high" if quality >= 0.7 else "quality-medium" if quality >= 0.4 else "quality-low"

        warnings_html = ""
        if report.quality_warnings:
            warnings_html = "<ul>" + "".join([f"<li>{w}</li>" for w in report.quality_warnings]) + "</ul>"

        return f"""
        <div class="section">
            <h2>ECG Quality</h2>
            <span class="quality-badge {badge_class}">{quality:.1%}</span>
            {warnings_html}
        </div>
        """

    def _generate_html_summary(self, report: ECGReport, user_level: UserLevel) -> str:
        """Generate HTML summary section"""
        urgent_html = ""
        if report.is_urgent:
            urgent_html = f'<div class="urgent-alert">🚨 URGENT: {report.urgency_reason}</div>'

        summary = self._adapt_summary(report.summary, user_level)

        return f"""
        <div class="section">
            <h2>Summary</h2>
            {urgent_html}
            <p>{summary}</p>
        </div>
        """

    def _generate_html_measurements(self, report: ECGReport) -> str:
        """Generate HTML measurements section"""
        if not report.measurements:
            return ""

        m = report.measurements
        rows = []

        items = [
            ("Heart Rate", m.get("heart_rate"), "bpm"),
            ("Rhythm", m.get("rhythm"), ""),
            ("PR Interval", m.get("pr_interval_ms"), "ms"),
            ("QRS Duration", m.get("qrs_duration_ms"), "ms"),
            ("QT Interval", m.get("qt_interval_ms"), "ms"),
            ("QTc", m.get("qtc_ms"), "ms"),
            ("Axis", m.get("axis_degrees"), "°"),
        ]

        for label, value, unit in items:
            if value is not None:
                indicator = self._get_normal_indicator(label, value)
                rows.append(f"<tr><td><strong>{label}</strong></td><td>{value} {unit}</td><td>{indicator}</td></tr>")

        return f"""
        <div class="section">
            <h2>Measurements</h2>
            <table class="measurements-table">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """

    def _generate_html_findings(self, report: ECGReport, user_level: UserLevel) -> str:
        """Generate HTML findings section"""
        if not report.findings:
            return ""

        findings_html = []

        # Group by severity
        for finding in sorted(report.findings, key=lambda x: {"critical": 0, "abnormal": 1, "normal": 2}.get(x.get("severity", "normal"), 3)):
            severity = finding.get("severity", "normal")
            finding_text = finding.get("finding", "")
            explanation = finding.get("explanation", "")

            # Skip normal findings for RMP
            if severity == "normal" and user_level == UserLevel.RMP:
                continue

            findings_html.append(f"""
            <div class="finding finding-{severity}">
                <div class="finding-title">{finding_text}</div>
                {f'<div class="finding-explanation">{explanation}</div>' if explanation and user_level != UserLevel.RMP else ''}
            </div>
            """)

        return f"""
        <div class="section">
            <h2>Findings</h2>
            {''.join(findings_html)}
        </div>
        """

    def _generate_html_algorithms(self, report: ECGReport, user_level: UserLevel) -> str:
        """Generate HTML algorithm results section"""
        if not report.algorithm_results or user_level not in [UserLevel.RESIDENT, UserLevel.CARDIOLOGIST]:
            return ""

        algorithms_html = []

        for algo in report.algorithm_results:
            name = algo.get("name", "Unknown")
            conclusion = algo.get("conclusion", "N/A")
            confidence = algo.get("confidence", 0)
            steps = algo.get("steps", [])

            steps_html = ""
            if steps:
                steps_items = [f'<li class="algorithm-step">{s.get("description", "")}: {s.get("result", "")}</li>' for s in steps]
                steps_html = f'<ol class="algorithm-steps">{"".join(steps_items)}</ol>'

            algorithms_html.append(f"""
            <div class="algorithm-result">
                <div class="algorithm-name">{name.upper()}</div>
                <p><strong>Conclusion:</strong> {conclusion}</p>
                <p><strong>Confidence:</strong> {confidence:.1%}</p>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {confidence*100}%"></div>
                </div>
                {steps_html}
            </div>
            """)

        return f"""
        <div class="section">
            <h2>Algorithm Analysis</h2>
            {''.join(algorithms_html)}
        </div>
        """

    def _generate_html_interpretation(self, report: ECGReport) -> str:
        """Generate HTML interpretation section"""
        differentials_html = ""
        if report.differential_diagnoses:
            diff_items = [f"<li>{dx}</li>" for dx in report.differential_diagnoses]
            differentials_html = f'<h3>Differential Diagnoses</h3><ol>{"".join(diff_items)}</ol>'

        return f"""
        <div class="section">
            <h2>Interpretation</h2>
            <p><strong>Primary Diagnosis:</strong> {report.primary_diagnosis}</p>
            {differentials_html}
            <p><strong>Diagnostic Confidence:</strong> {report.confidence:.1%}</p>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {report.confidence*100}%"></div>
            </div>
        </div>
        """

    def _generate_html_recommendations(self, report: ECGReport) -> str:
        """Generate HTML recommendations section"""
        if not report.recommended_actions:
            return ""

        actions = [f"<li>{action}</li>" for action in report.recommended_actions]

        return f"""
        <div class="section">
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ol>{''.join(actions)}</ol>
            </div>
        </div>
        """

    def _generate_html_teaching(self, report: ECGReport, include_teaching: bool) -> str:
        """Generate HTML teaching section"""
        if not include_teaching or not report.teaching_points:
            return ""

        points_html = []
        for i, point in enumerate(report.teaching_points, 1):
            points_html.append(f'<div class="teaching-point"><strong>{i}.</strong> {point}</div>')

        return f"""
        <div class="section">
            <div class="teaching-section">
                <h2>📚 Teaching Points</h2>
                {''.join(points_html)}
            </div>
        </div>
        """

    def _generate_html_sources(self, report: ECGReport, user_level: UserLevel) -> str:
        """Generate HTML sources section"""
        if not report.knowledge_sources or user_level == UserLevel.RMP:
            return ""

        sources = [f"<li>{source}</li>" for source in report.knowledge_sources]

        return f"""
        <div class="section">
            <h2>References</h2>
            <ul>{''.join(sources)}</ul>
        </div>
        """

    def _generate_html_disclaimer(self, report: ECGReport) -> str:
        """Generate HTML disclaimer section"""
        return f"""
        <div class="disclaimer">
            <strong>Disclaimer:</strong> {report.disclaimer}
        </div>
        <div class="footer">
            <p>Generated by ECG Guru | Report ID: {report.report_id}</p>
        </div>
        """

    # ========================================================================
    # Helper Methods: PDF Format (reportlab fallback)
    # ========================================================================

    def _generate_pdf_reportlab(
        self,
        report: ECGReport,
        user_level: UserLevel,
        include_teaching: bool,
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate PDF using reportlab as fallback.

        Note: This is a simplified version. Install weasyprint for better results.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            import io

            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#3498db'),
                spaceAfter=30,
                alignment=1,  # Center
            )
            story.append(Paragraph("ECG GURU - ECG Analysis Report", title_style))
            story.append(Spacer(1, 0.2*inch))

            # Metadata
            story.append(Paragraph(f"<b>Report ID:</b> {report.report_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Generated:</b> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Summary
            story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
            if report.is_urgent:
                story.append(Paragraph(f"<b>URGENT:</b> {report.urgency_reason}", styles['Normal']))
            story.append(Paragraph(report.summary, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            # Measurements
            story.append(Paragraph("<b>Measurements</b>", styles['Heading2']))
            m = report.measurements
            measurements_data = [
                ['Parameter', 'Value', 'Unit'],
                ['Heart Rate', str(m.get('heart_rate', 'N/A')), 'bpm'],
                ['PR Interval', str(m.get('pr_interval_ms', 'N/A')), 'ms'],
                ['QRS Duration', str(m.get('qrs_duration_ms', 'N/A')), 'ms'],
                ['QTc', str(m.get('qtc_ms', 'N/A')), 'ms'],
            ]
            measurements_table = Table(measurements_data)
            measurements_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(measurements_table)
            story.append(Spacer(1, 0.3*inch))

            # Interpretation
            story.append(Paragraph("<b>Interpretation</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>Primary Diagnosis:</b> {report.primary_diagnosis}", styles['Normal']))
            story.append(Paragraph(f"<b>Confidence:</b> {report.confidence:.1%}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            # Recommendations
            if report.recommended_actions:
                story.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
                for i, action in enumerate(report.recommended_actions, 1):
                    story.append(Paragraph(f"{i}. {action}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

            # Disclaimer
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(f"<i>{report.disclaimer}</i>", styles['Normal']))

            # Build PDF
            doc.build(story)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            # Save if path provided
            if output_path:
                Path(output_path).write_bytes(pdf_bytes)

            return pdf_bytes

        except ImportError:
            raise ImportError(
                "PDF generation requires either 'weasyprint' or 'reportlab'. "
                "Install with: pip install weasyprint or pip install reportlab"
            )


# ============================================================================
# Convenience Functions
# ============================================================================

def create_report_from_analysis(
    analysis_response: Dict[str, Any],
    patient_info: Optional[PatientInfo] = None,
) -> ECGReport:
    """
    Create ECGReport from ECGAnalysisResponse.

    Args:
        analysis_response: Dictionary from ECGAnalysisResponse
        patient_info: Optional patient demographics

    Returns:
        ECGReport instance
    """
    return ECGReport(
        report_id=analysis_response.get("analysis_id", ""),
        timestamp=analysis_response.get("timestamp", datetime.now()),
        analysis_duration_ms=analysis_response.get("processing_time_ms"),
        patient_info=patient_info,
        quality_score=0.8,  # Would come from image processor
        quality_warnings=[],
        measurements=analysis_response.get("measurements", {}),
        findings=analysis_response.get("findings", []),
        algorithm_results=analysis_response.get("algorithm_results", []),
        summary=analysis_response.get("summary", ""),
        primary_diagnosis=analysis_response.get("primary_diagnosis", ""),
        differential_diagnoses=analysis_response.get("differential_diagnoses", []),
        confidence=analysis_response.get("confidence", 0.0),
        is_urgent=analysis_response.get("is_urgent", False),
        urgency_reason=analysis_response.get("urgency_reason"),
        recommended_actions=analysis_response.get("recommended_actions", []),
        teaching_points=[],  # Would be extracted from teaching_content
        knowledge_sources=analysis_response.get("knowledge_sources", []),
    )


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example report generation
    from datetime import datetime

    # Create sample report
    report = ECGReport(
        report_id="ECG-2026-0001",
        timestamp=datetime.now(),
        analysis_duration_ms=1250,
        patient_info=PatientInfo(
            name="John Doe",
            age=65,
            sex="male",
        ),
        quality_score=0.85,
        measurements={
            "heart_rate": 140,
            "rhythm": "wide_complex_tachycardia",
            "pr_interval_ms": None,
            "qrs_duration_ms": 160,
            "qt_interval_ms": 380,
            "qtc_ms": 465,
            "axis_degrees": -40,
        },
        findings=[
            {
                "category": "rhythm",
                "finding": "Wide complex tachycardia",
                "severity": "critical",
                "confidence": 0.95,
                "explanation": "Regular wide QRS tachycardia at 140 bpm",
            },
            {
                "category": "morphology",
                "finding": "Left axis deviation",
                "severity": "abnormal",
                "confidence": 0.9,
                "explanation": "QRS axis at -40 degrees suggests left axis deviation",
            },
        ],
        algorithm_results=[
            {
                "name": "Brugada Algorithm",
                "conclusion": "VT (Ventricular Tachycardia)",
                "confidence": 0.92,
                "steps": [
                    {"description": "RS complex in precordial leads", "result": "Absent - Supports VT"},
                    {"description": "R to S interval", "result": "N/A (no RS complex)"},
                    {"description": "AV dissociation", "result": "Present - Confirms VT"},
                ],
            }
        ],
        summary="Wide complex tachycardia consistent with ventricular tachycardia",
        primary_diagnosis="Ventricular Tachycardia (VT)",
        differential_diagnoses=[
            "SVT with aberrancy",
            "Antidromic AVRT",
        ],
        confidence=0.92,
        is_urgent=True,
        urgency_reason="Ventricular tachycardia requires immediate intervention",
        recommended_actions=[
            "Immediate cardioversion if hemodynamically unstable",
            "IV amiodarone if stable",
            "Cardiology consultation urgent",
            "Monitor in CCU",
        ],
        teaching_points=[
            "Wide complex tachycardia: Always assume VT until proven otherwise",
            "Brugada criteria: Absence of RS complex in all precordial leads is diagnostic of VT",
            "AV dissociation: Pathognomonic for VT",
        ],
        knowledge_sources=[
            "Brugada et al. Circulation 1991;83:1649-59",
            "ACC/AHA/ESC Guidelines for Ventricular Arrhythmias",
        ],
    )

    # Generate reports
    generator = ReportGenerator()

    # Text report
    print("=" * 80)
    print("TEXT REPORT")
    print("=" * 80)
    text_report = generator.generate_text(report, user_level=UserLevel.RESIDENT)
    print(text_report)

    # HTML report
    html_report = generator.generate_html(report, user_level=UserLevel.CARDIOLOGIST)
    with open("/tmp/ecg_report.html", "w") as f:
        f.write(html_report)
    print("\nHTML report saved to /tmp/ecg_report.html")

    # JSON report
    json_report = generator.generate_json(report)
    print("\nJSON Report (first 500 chars):")
    print(json_report[:500])
