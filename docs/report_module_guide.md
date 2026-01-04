# ECG Report Generation Module Guide

## Overview

The ECG Report Generation module (`src/core/report.py`) provides professional, multi-format report generation for ECG analysis results. It adapts content complexity based on user expertise level and supports Text, HTML, JSON, and PDF output formats.

## Key Features

### 1. **User Level Adaptation**
Reports automatically adapt to the reader's expertise:

| User Level | Target Audience | Report Style |
|------------|----------------|--------------|
| **RMP** | Rural Medical Practitioners | Simple verdicts, red flags, clear referral advice |
| **Student** | MBBS Students | Educational with teaching points and explanations |
| **Resident** | MD/DM Cardiology Residents | Detailed clinical analysis with algorithms and differentials |
| **Cardiologist** | Practicing Cardiologists/EPs | Full technical detail with algorithm step-by-step breakdowns |

### 2. **Multiple Output Formats**
- **Text**: Terminal/console display, printable plain text
- **HTML**: Professional web view with print-optimized CSS
- **JSON**: API responses and data interchange
- **PDF**: Clinical documentation (requires weasyprint or reportlab)

### 3. **Color-Coded Severity**
- 🟢 **Normal** (Green): Within normal limits
- 🟡 **Abnormal** (Yellow/Orange): Requires attention
- 🔴 **Critical** (Red): Urgent intervention needed

### 4. **Comprehensive Content**
- Patient demographics
- ECG quality assessment
- Measurements with normal range indicators
- Categorized findings
- Algorithm results with step-by-step execution
- Clinical interpretation
- Actionable recommendations
- Teaching points (when enabled)
- References and knowledge sources
- Medical-legal disclaimer

## Installation

The report module requires minimal dependencies:

```bash
# Basic functionality (text, HTML, JSON)
# No additional packages required

# For PDF generation (optional)
pip install weasyprint  # Recommended - better quality
# OR
pip install reportlab   # Fallback option
```

## Quick Start

### Basic Usage

```python
from datetime import datetime
from src.core.report import ECGReport, PatientInfo, ReportGenerator, UserLevel

# Create report data
report = ECGReport(
    report_id="ECG-2026-001",
    timestamp=datetime.now(),
    patient_info=PatientInfo(name="John Doe", age=65, sex="male"),
    quality_score=0.85,
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
            "explanation": "Regular rhythm at 75 bpm",
        }
    ],
    summary="Normal ECG",
    primary_diagnosis="Normal ECG",
    confidence=0.98,
    is_urgent=False,
    recommended_actions=["Routine follow-up"],
)

# Generate reports
generator = ReportGenerator()

# Text report
text = generator.generate_text(report, user_level=UserLevel.STUDENT)
print(text)

# HTML report (can be opened in browser)
html = generator.generate_html(report, user_level=UserLevel.CARDIOLOGIST)
with open("report.html", "w") as f:
    f.write(html)

# JSON for API
json_str = generator.generate_json(report)

# PDF (if libraries installed)
pdf_bytes = generator.generate_pdf(report, output_path="report.pdf")
```

## Integration with ECG Analysis Pipeline

### From ECGAnalysisResponse (API Server)

```python
from src.core.report import create_report_from_analysis, PatientInfo

# Get analysis result from ECG analysis pipeline
analysis_result = {
    "analysis_id": "ECG-001",
    "timestamp": datetime.now(),
    "processing_time_ms": 1250,
    "summary": "Wide complex tachycardia",
    "measurements": {...},
    "findings": [...],
    "algorithm_results": [...],
    "primary_diagnosis": "Ventricular Tachycardia",
    "differential_diagnoses": ["SVT with aberrancy"],
    "confidence": 0.92,
    "is_urgent": True,
    "urgency_reason": "VT requires immediate intervention",
    "recommended_actions": [...],
    "knowledge_sources": [...],
}

# Create report
patient = PatientInfo(name="Jane Smith", age=58, sex="female")
report = create_report_from_analysis(analysis_result, patient_info=patient)

# Generate in desired format
generator = ReportGenerator()
html_report = generator.generate_html(report, user_level=UserLevel.RESIDENT)
```

## Report Sections

### 1. Header
- Report ID and timestamp
- Analysis duration
- Patient information (if provided)

### 2. ECG Quality
- Quality score (0-100%)
- Warning messages (baseline wander, noise, etc.)

### 3. Summary
- One-line verdict appropriate for user level
- Urgent alerts (if critical findings present)

### 4. Measurements Table
- Heart rate, PR, QRS, QT, QTc, Axis
- Normal range indicators (✓ or ⚠)

### 5. Findings
- Grouped by severity (Critical → Abnormal → Normal)
- Category, finding, explanation
- Teaching points (for Students/Residents)

### 6. Algorithm Results
- Step-by-step algorithm execution
- Conclusions and confidence scores
- Shown for Resident and Cardiologist levels

### 7. Interpretation
- Primary diagnosis
- Differential diagnoses
- Diagnostic confidence

### 8. Recommendations
- Actionable clinical steps
- Treatment protocols
- Referral guidance

### 9. Teaching Content (Optional)
- Educational explanations
- Similar cases
- Key learning points

### 10. References
- Knowledge sources
- Guidelines and algorithms used

### 11. Disclaimer
- Medical-legal disclaimer
- Clinical judgment reminder

## User Level Customization Examples

### RMP (Rural Medical Practitioner)
```text
SUMMARY
🚨 URGENT: Heart attack detected - IMMEDIATE REFERRAL REQUIRED

ACTION: Refer immediately to nearest cardiac center.

RECOMMENDATIONS
1. 🚨 ACTIVATE CATH LAB IMMEDIATELY
2. Aspirin 325mg PO (chewed)
3. Call cardiology STAT
```

### Student (MBBS)
```text
SUMMARY
Anterior STEMI - ST elevation in V2-V5 indicates LAD occlusion

TEACHING POINTS
1. STEMI criteria: ≥1mm ST elevation in ≥2 contiguous leads
2. Anterior STEMI is caused by LAD occlusion
3. Door-to-balloon time is critical for outcomes
```

### Cardiologist
```text
ALGORITHM ANALYSIS

BRUGADA ALGORITHM
  Conclusion: VT (Ventricular Tachycardia)
  Confidence: 92%
  Steps:
    1. RS complex in precordial leads: Absent - Supports VT
    2. R to S interval > 100ms: N/A (no RS complex)
    3. AV dissociation: Present - Diagnostic of VT
    4. Morphology criteria: V1 - R/S >1, V6 - QS pattern
```

## HTML Report Features

### Print-Optimized
- Clean, professional layout
- Proper page breaks
- Print-friendly CSS (removes backgrounds, optimizes margins)

### Color Coding
- Normal findings: Green (#28a745)
- Abnormal findings: Yellow (#ffc107)
- Critical findings: Red (#dc3545)

### Responsive Design
- Works on desktop, tablet, mobile
- Scales for different screen sizes

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Works without JavaScript (progressive enhancement)

## JSON Schema

```json
{
  "report_id": "string",
  "timestamp": "ISO 8601 datetime",
  "analysis_duration_ms": "integer or null",
  "patient_info": {
    "patient_id": "string or null",
    "name": "string or null",
    "age": "integer or null",
    "sex": "male|female or null",
    "mrn": "string or null"
  },
  "quality_score": "float (0-1)",
  "quality_warnings": ["array of strings"],
  "measurements": {
    "heart_rate": "integer or null",
    "rhythm": "string or null",
    "pr_interval_ms": "integer or null",
    "qrs_duration_ms": "integer or null",
    "qt_interval_ms": "integer or null",
    "qtc_ms": "integer or null",
    "axis_degrees": "integer or null"
  },
  "findings": [
    {
      "category": "rhythm|morphology|ischemia|conduction",
      "finding": "string",
      "severity": "normal|abnormal|critical",
      "confidence": "float (0-1)",
      "explanation": "string",
      "teaching_point": "string or null"
    }
  ],
  "algorithm_results": [
    {
      "name": "string",
      "conclusion": "string",
      "confidence": "float (0-1)",
      "steps": [{"description": "string", "result": "string"}]
    }
  ],
  "summary": "string",
  "primary_diagnosis": "string",
  "differential_diagnoses": ["array of strings"],
  "confidence": "float (0-1)",
  "is_urgent": "boolean",
  "urgency_reason": "string or null",
  "recommended_actions": ["array of strings"],
  "teaching_points": ["array of strings"],
  "knowledge_sources": ["array of strings"]
}
```

## Best Practices

### 1. Always Include Context
```python
# Good
report.urgency_reason = "Anterior STEMI - door-to-balloon time critical"
report.recommended_actions = [
    "ACTIVATE CATH LAB IMMEDIATELY",
    "Aspirin 325mg PO",
    "Target door-to-balloon <90 minutes"
]

# Not as helpful
report.urgency_reason = "Urgent"
report.recommended_actions = ["Cardiology consult"]
```

### 2. Adapt Explanations
```python
# For RMP
"Heart attack detected - transfer immediately"

# For Student
"Anterior STEMI with ST elevation in V2-V5, indicating LAD occlusion"

# For Cardiologist
"Anterior STEMI with 3-5mm ST elevation V2-V5, reciprocal changes II/III/aVF, probable proximal LAD occlusion"
```

### 3. Use Appropriate Teaching Content
```python
# Include teaching points for Students and Residents
if user_level in [UserLevel.STUDENT, UserLevel.RESIDENT]:
    report.teaching_points = [
        "Brugada criteria for VT: Absence of RS in all precordial leads",
        "AV dissociation is pathognomonic for VT",
        "Wide QRS tachycardia: Always assume VT until proven otherwise",
    ]
```

### 4. Quality Checks
```python
# Add quality warnings
report.quality_warnings = [
    "Baseline wander in lead V1 - may affect ST measurements",
    "Low amplitude in limb leads - axis calculation may be imprecise",
]

# Set quality score
report.quality_score = 0.85  # 85%
```

### 5. Evidence-Based Recommendations
```python
# Include guideline-based actions
report.recommended_actions = [
    "Immediate cardioversion if hemodynamically unstable (Class I, LOE B)",
    "IV amiodarone 150mg over 10min if stable (Class IIa, LOE B)",
    "Cardiology consultation urgent (Class I, LOE C)",
]

# Cite sources
report.knowledge_sources = [
    "ACC/AHA/ESC Guidelines for Ventricular Arrhythmias 2022",
    "Brugada et al. Circulation 1991;83:1649-59",
]
```

## Examples

See `examples/simple_report_demo.py` for comprehensive demonstrations:

```bash
# Run the demo
python examples/simple_report_demo.py

# This generates:
# - Text report (terminal output)
# - HTML reports for each user level
# - JSON report
# - PDF report (if libraries available)
```

Generated files:
- `/tmp/rmp_stemi_report.html` - RMP level
- `/tmp/student_stemi_report.html` - Student level
- `/tmp/resident_stemi_report.html` - Resident level
- `/tmp/cardiologist_stemi_report.html` - Cardiologist level
- `/tmp/stemi_report.json` - JSON format
- `/tmp/stemi_report.pdf` - PDF format

## API Integration

### FastAPI Endpoint Example

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from src.core.report import ReportGenerator, create_report_from_analysis

app = FastAPI()

@app.post("/ecg/analyze/report")
async def generate_report(
    analysis_result: dict,
    user_level: str = "student",
    format: str = "html",
):
    """Generate ECG report from analysis result"""
    # Create report
    report = create_report_from_analysis(analysis_result)

    # Generate in requested format
    generator = ReportGenerator()

    if format == "html":
        content = generator.generate_html(report, user_level=user_level)
        return HTMLResponse(content=content)
    elif format == "json":
        content = generator.generate_json(report)
        return JSONResponse(content=json.loads(content))
    elif format == "pdf":
        pdf_bytes = generator.generate_pdf(report, user_level=user_level)
        return Response(content=pdf_bytes, media_type="application/pdf")
    else:
        content = generator.generate_text(report, user_level=user_level)
        return PlainTextResponse(content=content)
```

## Customization

### Custom Styles (HTML)

Override the default CSS by modifying `_get_html_styles()` in `ReportGenerator`:

```python
class CustomReportGenerator(ReportGenerator):
    def _get_html_styles(self) -> str:
        # Return your custom CSS
        return """
        body { font-family: 'Arial', sans-serif; }
        .urgent-alert { background: #ff0000; }
        /* ... your styles ... */
        """
```

### Custom Sections

Add custom sections by extending the generator methods:

```python
class ExtendedReportGenerator(ReportGenerator):
    def generate_html(self, report, user_level, include_teaching):
        # Call parent method
        html = super().generate_html(report, user_level, include_teaching)

        # Insert custom section before closing </body>
        custom_section = """
        <div class="custom-section">
            <h2>Hospital-Specific Protocol</h2>
            <p>Follow XYZ Hospital STEMI protocol...</p>
        </div>
        """
        html = html.replace("</body>", f"{custom_section}</body>")
        return html
```

## Troubleshooting

### PDF Generation Issues

```bash
# If weasyprint installation fails
pip install reportlab  # Use reportlab as fallback

# On Ubuntu/Debian (for weasyprint)
sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

# On macOS (for weasyprint)
brew install pango
```

### Missing Dependencies

```bash
# The report module itself has no external dependencies for text/HTML/JSON
# Only PDF generation requires additional packages

# Check what's available:
python -c "from src.core.report import ReportGenerator; print('✓ Report module working')"
```

### Import Issues

```python
# If getting numpy import errors, import directly:
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/user/ecg/src/core")))
import report

# Then use:
generator = report.ReportGenerator()
```

## Performance

- **Text generation**: < 5ms
- **HTML generation**: < 10ms
- **JSON generation**: < 5ms
- **PDF generation**: 50-200ms (depends on library and content)

## Security Considerations

### Patient Data
- Reports may contain PHI (Protected Health Information)
- Use appropriate access controls
- Encrypt at rest and in transit
- Follow HIPAA/local regulations

### Disclaimer
- Always included automatically
- Cannot be removed (by design)
- Emphasizes clinical judgment requirement

### Data Sanitization
```python
# Sanitize patient data before generating reports
report.patient_info.name = sanitize_name(raw_name)
report.patient_info.patient_id = anonymize_id(raw_id)
```

## Roadmap

Future enhancements planned:
- [ ] Multi-language support (Hindi, Spanish, etc.)
- [ ] Custom templates system
- [ ] Email delivery integration
- [ ] EMR integration helpers
- [ ] Batch report generation
- [ ] Report versioning and audit trail
- [ ] Digital signatures for PDF reports

## Support

For issues, questions, or contributions:
- GitHub: [github.com/drshailesh88/ecg](https://github.com/drshailesh88/ecg)
- Documentation: `/home/user/ecg/docs/`
- Examples: `/home/user/ecg/examples/`

## License

MIT License - See LICENSE file for details

---

**ECG Guru** - Putting a seasoned electrophysiologist in every practitioner's pocket.
