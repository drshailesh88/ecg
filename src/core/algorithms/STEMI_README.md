# STEMI Detection and Localization Module

## Overview

This module implements medical-grade STEMI (ST-Elevation Myocardial Infarction) detection and localization using validated clinical criteria from ACC/AHA and ESC guidelines.

**⚠️ MEDICAL DISCLAIMER**: This software is for educational and clinical decision support only. It does NOT replace clinical judgment. All STEMI diagnoses must be confirmed by a qualified physician and correlated with clinical presentation.

## Features

### 1. ST Elevation Detection (`STEMIDetector`)

Detects ST elevation using age and sex-specific thresholds:

- **Limb leads** (I, II, III, aVR, aVL, aVF): ≥1mm elevation
- **Precordial leads** (V1, V4-V6): ≥2mm elevation
- **V2-V3 leads** (age/sex-specific):
  - Women: ≥1.5mm
  - Men ≥40 years: ≥2mm
  - Men <40 years: ≥2.5mm

### 2. Territory Localization (`STEMILocalizer`)

Identifies affected myocardial territories:

| Territory | ECG Leads | Typical Culprit |
|-----------|-----------|-----------------|
| **Anteroseptal** | V1-V3 elevation | Proximal LAD |
| **Anterolateral** | V1-V6, I, aVL elevation | Proximal LAD |
| **Anterior** | V1-V4 elevation | Mid LAD |
| **Inferior** | II, III, aVF elevation | RCA or LCx |
| **Lateral** | I, aVL, V5-V6 elevation | LCx |
| **Posterior** | V1-V3 depression (reciprocal) | LCx or distal RCA |
| **Right Ventricle** | V1 elevation + inferior STEMI | RCA |

### 3. Culprit Vessel Identification

Determines the most likely culprit coronary artery with confidence scores.

#### Inferior STEMI: RCA vs LCx Algorithm (86% accuracy)

Based on Fiol M et al., Circulation 2004:

**RCA indicators:**
- ST elevation III > II (high sensitivity)
- ST depression in lead I (90% sensitivity)
- ST elevation in V1 (RV involvement)

**LCx indicators:**
- ST elevation II ≥ III
- ST elevation in lead I
- ST depression in V1 (posterior involvement)

#### LAD Segment Localization

- **Proximal LAD**: Extensive anterior + lateral involvement (I, aVL)
- **Mid LAD**: V1-V4 elevation
- **Distal LAD**: V3-V4 elevation only

## Usage

### Basic Usage

```python
from core.algorithms.stemi import analyze_stemi

# Prepare ECG measurements
measurements = {
    "leads": {
        "I": {"st_elevation_mm": 0.5, "st_depression_mm": 0},
        "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0},
        "III": {"st_elevation_mm": 3.0, "st_depression_mm": 0},
        "aVR": {"st_elevation_mm": 0, "st_depression_mm": 0.5},
        "aVL": {"st_elevation_mm": 0, "st_depression_mm": 0.8},
        "aVF": {"st_elevation_mm": 2.0, "st_depression_mm": 0},
        "V1": {"st_elevation_mm": 1.5, "st_depression_mm": 0},
        "V2": {"st_elevation_mm": 0, "st_depression_mm": 0},
        "V3": {"st_elevation_mm": 0, "st_depression_mm": 0},
        "V4": {"st_elevation_mm": 0, "st_depression_mm": 0},
        "V5": {"st_elevation_mm": 0, "st_depression_mm": 0},
        "V6": {"st_elevation_mm": 0, "st_depression_mm": 0},
    },
    "patient_sex": "male",  # Optional
    "patient_age": 65       # Optional
}

# Analyze
result = analyze_stemi(measurements)

# Check results
if result.is_stemi:
    print(f"⚠️ STEMI DETECTED")
    print(f"Territories: {', '.join(result.territories)}")
    print(f"Culprit vessel: {result.culprit_vessel}")
    print(f"Confidence: {result.culprit_confidence:.1%}")

    # Urgent findings
    for finding in result.urgent_findings:
        print(finding)

    # Recommended actions
    for action in result.recommended_actions:
        print(action)
```

### Advanced Usage

```python
from core.algorithms.stemi import STEMIDetector, STEMILocalizer

# Initialize
detector = STEMIDetector()
localizer = STEMILocalizer()

# Custom threshold checking
threshold = detector.get_st_threshold('V2', patient_sex='female')
print(f"V2 threshold for female: {threshold}mm")

# Detect elevated leads
st_elevated = detector.detect_st_elevation(measurements, 'male', 52)
print(f"Elevated leads: {[lead for lead, elevated in st_elevated.items() if elevated]}")

# Full analysis
result = localizer.analyze(measurements)
```

## Result Structure

The `STEMIResult` dataclass contains:

```python
@dataclass
class STEMIResult:
    is_stemi: bool                          # STEMI criteria met?
    territories: List[str]                  # Affected territories
    culprit_vessel: str                     # Most likely culprit artery
    culprit_confidence: float               # Confidence 0.0-1.0
    st_changes: Dict[str, float]            # Lead → ST deviation (mm)
    urgent_findings: List[str]              # Critical findings
    recommended_actions: List[str]          # Clinical actions
    segment_location: Optional[str]         # Specific arterial segment
    differential_diagnosis: List[str]       # Alternative diagnoses
    additional_notes: List[str]             # Clinical context
```

## Clinical Examples

### Example 1: Inferior STEMI from RCA

```
Patient: 65-year-old male with chest pain
ECG: ST elevation II, III, aVF (III > II) + ST depression in I + ST elevation V1

Result:
✓ STEMI Detected: Inferior
✓ Culprit: RCA (95% confidence)
✓ Segment: Proximal RCA
✓ Urgent: Right ventricular involvement likely
✓ Action: Activate cath lab, check V4R, avoid nitrates
```

### Example 2: Inferior STEMI from LCx

```
Patient: 58-year-old female with chest pain
ECG: ST elevation II, III, aVF (II ≥ III) + ST elevation I + ST depression V1-V3

Result:
✓ STEMI Detected: Inferior, Posterior
✓ Culprit: LCx (90% confidence)
✓ Segment: Dominant LCx
✓ Urgent: Posterior wall involvement
✓ Action: Activate cath lab, obtain V7-V9 leads
```

### Example 3: Extensive Anterior STEMI

```
Patient: 52-year-old male with crushing chest pain
ECG: Massive ST elevation V1-V6, I, aVL (up to 6mm)

Result:
✓ STEMI Detected: Anteroseptal, Anterolateral
✓ Culprit: LAD (95% confidence)
✓ Segment: Proximal LAD (before D1 diagonal)
✓ Urgent: VERY HIGH RISK for cardiogenic shock
✓ Action: IMMEDIATE cath lab activation
```

## Validation

### Algorithm Sources

- **STEMI Criteria**: ACC/AHA STEMI Guidelines 2013, 2022
- **RCA vs LCx**: Fiol M et al., Circulation 2004 (86% accuracy)
- **Thresholds**: ESC STEMI Guidelines 2017, 2023

### Testing

Run the test suite:

```bash
python tests/test_stemi.py
```

Run examples:

```bash
python src/core/algorithms/stemi_examples.py
```

### Test Coverage

- [x] Age/sex-specific ST thresholds
- [x] Inferior STEMI (RCA vs LCx)
- [x] Anterior STEMI (LAD segments)
- [x] Right ventricular involvement
- [x] Posterior STEMI
- [x] Missing/incomplete lead data
- [x] Non-STEMI patterns
- [x] Edge cases

## Special Patterns Detected

### 1. Right Ventricular Infarction

**Detection**: V1 ST elevation + inferior STEMI

**Clinical significance**:
- High risk of hypotension
- Requires volume resuscitation
- **AVOID nitrates and preload reducers**

**Actions**:
- Obtain V4R lead (most sensitive)
- Aggressive fluid resuscitation if hypotensive
- Maintain preload

### 2. Posterior Wall Involvement

**Detection**: V1-V3 ST depression (reciprocal) with inferior/lateral STEMI

**Clinical significance**:
- Often missed without posterior leads
- Indicates larger infarct size

**Actions**:
- Obtain V7-V9 (posterior leads)
- Consider posterior MI equivalent

### 3. Massive ST Elevation

**Detection**: ST elevation ≥5mm in any lead

**Clinical significance**:
- Very high risk for complications
- Large infarct size
- Higher mortality

**Actions**:
- Expedite reperfusion
- Consider mechanical support

## Integration with ECG Guru

This module integrates with the ECG Guru pipeline:

```
1. Image Upload → ECG Image
2. Image Processing → Lead Detection, Digitization
3. Waveform Analysis → ST Measurement (this module's input)
4. STEMI Algorithm → Territory, Vessel, Recommendations
5. AI Layer → Explanation, Teaching, Conversation
```

**Key principle**: This module performs **diagnostic analysis** using validated algorithms. The AI/LLM layer handles **explanation and conversation**, NOT primary diagnosis.

## Future Enhancements

- [ ] De Winter's T waves detection (LAD occlusion equivalent)
- [ ] Wellens' syndrome detection (critical LAD stenosis)
- [ ] Sgarbossa criteria (STEMI with LBBB)
- [ ] Posterior lead analysis (V7-V9)
- [ ] Integration with troponin levels
- [ ] Risk stratification (TIMI, GRACE scores)

## References

1. O'Gara PT, et al. 2013 ACCF/AHA Guideline for STEMI. Circulation. 2013;127:e362-e425.
2. Ibanez B, et al. 2017 ESC Guidelines for STEMI. Eur Heart J. 2018;39:119-177.
3. Fiol M, et al. New criteria based on ST changes in 12-lead surface ECG to detect proximal vs distal RCA occlusion in inferior STEMI. Circulation. 2004.
4. Thygesen K, et al. Fourth Universal Definition of Myocardial Infarction. Circulation. 2018.

## License

Part of ECG Guru - AI-Powered ECG Analysis Platform
For educational and clinical decision support use only.
