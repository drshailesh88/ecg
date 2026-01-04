# Accessory Pathway Localization for WPW Syndrome

## Overview

This module implements validated algorithms for localizing accessory pathways in Wolff-Parkinson-White (WPW) syndrome based on delta wave polarity and QRS morphology analysis from 12-lead ECG.

## Algorithms Implemented

### 1. SMART-WPW Algorithm (2025) - PRIMARY
- **Accuracy**: 97%
- **Reference**: Heart Rhythm 2025
- **Status**: Most accurate currently available algorithm
- **Use**: Primary algorithm for pathway localization

### 2. Arruda Stepwise Algorithm (1998) - SECONDARY
- **Accuracy**: 53-75% (variable by location)
- **Reference**: J Cardiovasc Electrophysiol 1998;9:2-12
- **Status**: Classic reference standard
- **Use**: Secondary validation, historical reference

## Pathway Locations Detected

The algorithms can localize accessory pathways to 10 standard anatomical positions:

### Left-Sided Pathways
- **Left Lateral (LL)** - Most common left-sided location
- **Left Posterolateral (LPL)** - Between lateral and posterior
- **Left Posterior (LP)** - May require coronary sinus approach

### Septal Pathways (HIGH RISK)
- **Posteroseptal (PS)** - Close to AV node, high ablation risk
- **Right Posteroseptal (RPS)** - Right side of septum
- **Midseptal (MS)** - Central septum, very high risk
- **Anteroseptal (AS)** - Extremely high risk, closest to AV node

### Right-Sided Pathways
- **Right Lateral (RL)** - Right free wall
- **Right Anterolateral (RAL)** - Anterior right free wall
- **Right Posterior (RP)** - Posterior right free wall

## Usage Examples

### Quick Localization

```python
from pathway import quick_pathway_localization

# Simple delta wave polarity input
delta_waves = {
    "I": "+",
    "II": "+",
    "III": "+",
    "aVR": "-",
    "aVL": "+",
    "aVF": "+",
    "V1": "+",    # Positive V1 = left-sided
    "V2": "+",
    "V3": "+",
    "V4": "+",
    "V5": "+",
    "V6": "+"
}

location = quick_pathway_localization(delta_waves)
print(f"Pathway location: {location}")
# Output: "Left Lateral (LL)"
```

### Detailed Analysis with Both Algorithms

```python
from pathway import PathwayLocalizer

measurements = {
    "delta_wave_polarity": {
        "I": "+",
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

localizer = PathwayLocalizer()
result = localizer.localize(measurements)

# Access results
print(result["summary"])  # Human-readable summary
print(result["recommendation"])  # Clinical recommendation

# Access detailed data
primary = result["primary_result"]
print(f"Location: {primary['primary_location']}")
print(f"Confidence: {primary['confidence']}")
print(f"Ablation approach: {primary['ablation_approach']}")
print(f"Alternatives: {primary['alternative_locations']}")

# Check algorithm consensus
consensus = result["consensus"]
print(f"Agreement: {consensus['agreement_level']}")
```

### Using Individual Algorithms

```python
from pathway import SMARTWPWAlgorithm, ArrudaAlgorithm

measurements = {
    # ... same as above
}

# SMART-WPW only (recommended)
smart = SMARTWPWAlgorithm()
smart_result = smart.evaluate(measurements)

# Arruda only (for comparison)
arruda = ArrudaAlgorithm()
arruda_result = arruda.evaluate(measurements)

# Access step-by-step reasoning
for step in smart_result.step_details:
    print(step)
```

## Input Format

### Required Fields

```python
{
    "delta_wave_polarity": {
        # All 12 leads with delta wave polarity
        "I": "+",      # "+" = positive, "-" = negative, "0" = isoelectric
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
    }
}
```

### Optional Fields

```python
{
    "qrs_morphology": {
        "V1": "positive",  # "positive" or "negative"
        "transition": "V3"  # R/S transition zone (V1-V6)
    },
    "has_manifest_preexcitation": True  # Default: True
}
```

## Output Structure

### PathwayResult Object

```python
{
    "primary_location": "Left Lateral (LL)",
    "confidence": 0.95,
    "alternative_locations": ["Left Posterolateral (LPL)"],
    "delta_wave_analysis": {
        "I": "+",
        "II": "+",
        # ... all 12 leads
    },
    "ablation_approach": "Transseptal",
    "clinical_notes": [
        "Left-sided pathways: Transseptal approach is most common...",
        "Ensure adequate anticoagulation for left-sided access..."
    ],
    "algorithm_used": "SMART-WPW Algorithm",
    "step_details": [
        "Step 1: V1 delta wave is POSITIVE → LEFT-SIDED pathway likely...",
        "Step 2: Inferior leads (II, III, aVF) show POSITIVE delta waves..."
    ],
    "missing_data": [],
    "warnings": []
}
```

## Clinical Decision Tree

### SMART-WPW Algorithm Steps

1. **Step 1: V1 Polarity**
   - Positive → Left-sided pathway
   - Negative → Right-sided or septal pathway
   - Isoelectric → Septal or indeterminate

2. **Step 2: Inferior Leads (II, III, aVF)**
   - Positive → Anterior pathway
   - Negative → Posterior pathway
   - Mixed → Lateral or indeterminate

3. **Step 3: Leads I and aVL**
   - Both positive → Free wall pathway
   - Negative/isoelectric → Septal pathway

4. **Step 4: Precordial Pattern**
   - Transition zone and pattern → Fine localization

## Ablation Approaches

### Left-Sided Pathways
- **Primary**: Transseptal puncture
- **Alternative**: Retrograde aortic approach
- **Considerations**: Anticoagulation required, TEE/ICE guidance

### Right-Sided Pathways
- **Approach**: Standard right atrial via femoral vein
- **Considerations**: Straightforward access, high success rate

### Septal Pathways (HIGH RISK)
- **Approach**: Right or left atrial with extreme caution
- **Risk**: AV block requiring permanent pacemaker
- **Recommendation**: Consider cryoablation (reversible vs RF)
- **Special**: Anteroseptal is highest risk location

## Clinical Notes and Warnings

### Septal Pathway Warning
All septal pathways (AS, MS, PS, RPS) carry increased risk:
- Risk of AV block (1-5% depending on location)
- Anteroseptal: VERY HIGH RISK (some operators avoid ablation)
- Consider cryoablation for added safety
- Detailed patient consent regarding pacemaker risk

### Concealed Pathways
Pathways without manifest pre-excitation:
- Cannot be localized by delta wave analysis
- Requires EP study mapping during orthodromic AVRT
- Algorithms return low confidence with warnings

### Algorithm Limitations
- Final localization ALWAYS confirmed by EP mapping
- ECG localization is for planning, not definitive
- Multiple pathways cannot be detected by these algorithms
- Intermittent pre-excitation may reduce accuracy

## Example Cases

See `pathway_examples.py` for detailed examples:

1. **Left Lateral Pathway** - Classic left free wall
2. **Posteroseptal Pathway** - High-risk septal location
3. **Right Lateral Pathway** - Right free wall
4. **Concealed Pathway** - No manifest pre-excitation
5. **Quick Localization** - Using convenience function
6. **Algorithm Comparison** - SMART-WPW vs Arruda

Run examples:
```bash
python3 src/core/algorithms/pathway_examples.py
```

## Integration with ECG Guru

This module integrates into the ECG Guru platform:

```python
from ecg_guru.core.algorithms import (
    PathwayLocalizer,
    quick_pathway_localization,
    detailed_pathway_analysis
)

# Use in analysis pipeline
def analyze_wpw_ecg(ecg_data):
    # Extract delta wave polarities from image processing
    delta_waves = extract_delta_waves(ecg_data)

    # Localize pathway
    result = detailed_pathway_analysis({
        "delta_wave_polarity": delta_waves,
        "has_manifest_preexcitation": True
    })

    # Generate report
    return format_wpw_report(result)
```

## References

1. **SMART-WPW Algorithm**
   - Heart Rhythm 2025
   - 97% accuracy
   - Most recent and accurate algorithm

2. **Arruda Algorithm**
   - J Cardiovasc Electrophysiol 1998;9:2-12
   - Classic reference standard
   - 53-75% accuracy (variable by location)

3. **General WPW References**
   - ESC Guidelines 2019: Supraventricular Tachycardia
   - 2015 ACC/AHA/HRS Guidelines for SVT
   - Blomström-Lundqvist C, et al. Europace 2003

## Safety and Disclaimers

**CRITICAL**: These algorithms are for educational and procedural planning purposes only.

- NOT a replacement for electrophysiology study
- Final pathway localization requires EP mapping
- All symptomatic WPW patients should be referred to EP
- Asymptomatic WPW: Risk stratification indicated for high-risk occupations
- Septal ablations require experienced operators
- Patient consent must include pacemaker risk for septal pathways

## Development Notes

### Code Structure
- `PathwayResult`: Dataclass for algorithm results
- `SMARTWPWAlgorithm`: 97% accuracy, primary algorithm
- `ArrudaAlgorithm`: 53-75% accuracy, reference algorithm
- `PathwayLocalizer`: Ensemble class running both algorithms

### Design Patterns
Follows the same patterns as `vt_svt.py`:
- Dataclass-based results
- Step-by-step reasoning capture
- Confidence scoring
- Missing data tracking
- Clinical warnings system

### Testing
Basic tests included in `pathway_examples.py`. For production:
- Unit tests for each pathway location
- Integration tests with image processing
- Validation against EP study results
- Edge case handling (multiple pathways, intermittent pre-excitation)

## Future Enhancements

1. **EASY-WPW Algorithm** (2023, 94% accuracy)
2. **Machine learning pathway localization** (PTB-XL dataset)
3. **Multiple pathway detection**
4. **Integration with EP study data** for validation
5. **Visual pathway mapping** on anatomical diagrams
6. **Ablation success prediction** based on location and characteristics

## License and Attribution

Part of the ECG Guru project. See main project documentation for license.

Algorithms implemented from peer-reviewed literature with appropriate citations.
