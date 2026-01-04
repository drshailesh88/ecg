# VT vs SVT Differentiation Algorithms

Medical-grade implementation of validated algorithms for differentiating Ventricular Tachycardia (VT) from Supraventricular Tachycardia (SVT) with aberrant conduction in wide complex tachycardia.

## Algorithms Implemented

### 1. Brugada Algorithm (1991)
- **Accuracy**: 89% sensitivity for VT
- **Method**: 4-step sequential evaluation of precordial leads
- **Citation**: Brugada P, et al. Circulation 1991;83:1649-59

### 2. Vereckei aVR Algorithm (2008)
- **Accuracy**: 69-94% depending on population
- **Method**: Single-lead (aVR) 4-step analysis
- **Citation**: Vereckei A, et al. Heart Rhythm 2008;5:89-98

### 3. Basel Algorithm (2022)
- **Accuracy**: 91-93%, fastest to apply (median 36 seconds)
- **Method**: 3-criteria scoring system (≥2 = VT)
- **Citation**: JACC Clin Electrophysiol 2022

### 4. Pava Algorithm (2010)
- **Accuracy**: 85%+
- **Method**: Simple R-wave peak time in lead II (≥50ms = VT)
- **Citation**: Pava LF, et al. Heart Rhythm 2010

## Quick Start

### Simple Usage

```python
from core.algorithms.vt_svt import quick_vt_svt_check

# Minimal data - just what you have
measurements = {
    "leads": {
        "II": {
            "r_peak_time_ms": 60  # Measured from ECG
        }
    }
}

result = quick_vt_svt_check(measurements)
print(result)  # "VT", "SVT", or "Indeterminate"
```

### Detailed Analysis

```python
from core.algorithms.vt_svt import detailed_vt_svt_analysis

# More complete data
measurements = {
    "age": 65,
    "has_structural_heart_disease": True,
    "has_av_dissociation": False,
    "leads": {
        "V1": {"has_rs_complex": True, "rs_interval_ms": 110},
        "V2": {"has_rs_complex": True, "rs_interval_ms": 95},
        "V3": {"has_rs_complex": True, "rs_interval_ms": 90},
        "V4": {"has_rs_complex": True, "rs_interval_ms": 85},
        "V5": {"has_rs_complex": True, "rs_interval_ms": 80},
        "V6": {"has_rs_complex": True, "rs_interval_ms": 75},
        "aVR": {
            "initial_r_dominant": False,
            "initial_deflection_ms": 50,
            "has_downstroke_notching": False,
            "vi_vt_ratio": 0.8,
            "time_to_first_peak_ms": 50
        },
        "II": {
            "r_peak_time_ms": 60,
            "time_to_first_peak_ms": 55
        }
    }
}

result = detailed_vt_svt_analysis(measurements)

print(f"Consensus: {result['consensus']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Agreement: {result['agreement']['agreement_level']}")
print(f"\nRecommendation:\n{result['recommendation']}")
print(f"\nSummary:\n{result['summary']}")
```

### Individual Algorithm Usage

```python
from core.algorithms.vt_svt import BrugadaAlgorithm, VereckeiAlgorithm

# Use specific algorithm
brugada = BrugadaAlgorithm()
result = brugada.evaluate(measurements)

print(f"Conclusion: {result.conclusion}")
print(f"Confidence: {result.confidence:.1%}")

# See step-by-step reasoning
for step in result.steps:
    print(f"\nStep {step.step_number}: {step.criterion}")
    print(f"  Result: {step.result}")
    print(f"  Reasoning: {step.reasoning}")
```

## Measurement Input Format

The algorithms expect a dictionary with the following structure:

```python
{
    # Clinical data (optional but improves accuracy)
    "age": 65,  # years
    "has_structural_heart_disease": True/False,

    # Global ECG features
    "heart_rate": 150,  # bpm
    "qrs_duration_ms": 140,
    "has_av_dissociation": True/False/None,

    # Lead-specific measurements
    "leads": {
        # Precordial leads (for Brugada)
        "V1": {
            "has_rs_complex": True/False,
            "rs_interval_ms": 80,  # R onset to S nadir
            "vt_morphology_criteria_met": True/False  # Optional
        },
        "V2": {...},
        "V3": {...},
        "V4": {...},
        "V5": {...},
        "V6": {...},

        # Lead aVR (for Vereckei)
        "aVR": {
            "initial_r_dominant": True/False,
            "initial_deflection_ms": 35,  # Width of initial r or q
            "has_downstroke_notching": True/False,
            "vi_vt_ratio": 1.2,  # Voltage at 40ms from start / voltage at 40ms before end
            "time_to_first_peak_ms": 45  # For Basel
        },

        # Lead II (for Pava and Basel)
        "II": {
            "r_peak_time_ms": 45,  # QRS onset to R peak
            "time_to_first_peak_ms": 50  # QRS onset to first peak (+ or -)
        }
    }
}
```

### Minimal Required Data

Each algorithm requires different minimal data:

- **Pava**: Just lead II R-wave peak time
- **Basel**: Age/SHD + lead II/aVR time to peak
- **Vereckei**: Lead aVR measurements
- **Brugada**: Precordial leads V1-V6 data

The ensemble works best with complete data but gracefully handles missing measurements.

## Handling Missing Data

All algorithms gracefully handle missing data:

```python
# Even with minimal data
measurements = {
    "leads": {
        "II": {"r_peak_time_ms": 55}  # Only Pava can run
    }
}

result = detailed_vt_svt_analysis(measurements)
# Will still provide conclusion based on available algorithms
# Confidence score reflects data completeness
```

## Output Structure

### AlgorithmResult (Individual Algorithm)

```python
{
    "name": "Brugada Algorithm",
    "conclusion": "VT",  # "VT", "SVT", or "Indeterminate"
    "confidence": 0.95,  # 0-1
    "supports_vt": True,
    "supports_svt": False,
    "steps": [
        {
            "step_number": 1,
            "criterion": "Absence of RS complex in ALL precordial leads",
            "measured_value": "RS complex present in 6 of 6 leads",
            "threshold": "Absence indicates VT",
            "result": "negative",
            "reasoning": "RS complex is present..."
        },
        # ... more steps
    ],
    "missing_data": ["AV dissociation assessment"],
    "warnings": []
}
```

### Ensemble Result

```python
{
    "consensus": "VT",
    "confidence": 0.98,
    "individual_results": {
        "Brugada": {...},
        "Vereckei": {...},
        "Basel": {...},
        "Pava": {...}
    },
    "agreement": {
        "vt_count": 4,
        "svt_count": 0,
        "indeterminate_count": 0,
        "agreement_level": "complete",  # complete, strong, moderate, poor, none
        "agreement_percentage": 100
    },
    "recommendation": "HIGH CONFIDENCE VT: Multiple algorithms strongly support...",
    "summary": "ENSEMBLE CONCLUSION: VT (confidence: 98.0%)\n..."
}
```

## Clinical Interpretation

### Confidence Levels

- **>90%**: High confidence in diagnosis
- **70-90%**: Moderate confidence
- **50-70%**: Low confidence, use clinical judgment
- **<50%**: Indeterminate, treat as VT to be safe

### Agreement Levels

- **Complete**: All algorithms agree (100%)
- **Strong**: ≥75% algorithms agree
- **Moderate**: ≥50% algorithms agree
- **Poor**: <50% agreement
- **None**: No conclusive algorithms

### Safety-First Approach

The ensemble follows the clinical principle: **"Treat all wide complex tachycardia as VT until proven otherwise"**

- Ambiguous cases default to VT recommendation
- Confidence <60% triggers VT treatment recommendation
- Even high-confidence SVT diagnosis includes clinical caution

## Integration with Image Processing

This module expects measurements from the image processing pipeline:

```python
# Your image processing code
ecg_image = load_ecg_image("ecg.jpg")
measurements = extract_measurements(ecg_image)  # Your function

# Then run algorithms
result = detailed_vt_svt_analysis(measurements)
```

The image processing pipeline (to be implemented separately) should:
1. Detect and isolate individual leads
2. Digitize waveforms
3. Measure intervals and amplitudes
4. Detect morphological features
5. Format as measurement dictionary

## Testing

Run the comprehensive test suite:

```bash
python tests/core/algorithms/test_vt_svt.py
```

## Medical Disclaimer

**CRITICAL**: These algorithms are for educational and decision support purposes only.

- They do NOT replace clinical judgment
- All wide complex tachycardias should be treated as VT in unstable patients
- Diagnostic certainty requires full clinical context
- When in doubt, treat as VT - it's safer

## References

1. Brugada P, Brugada J, Mont L, et al. A new approach to the differential diagnosis of a regular tachycardia with a wide QRS complex. Circulation. 1991;83(5):1649-1659.

2. Vereckei A, Duray G, Szénási G, et al. Application of a new algorithm in the differential diagnosis of wide QRS complex tachycardia. Eur Heart J. 2007;28(5):589-600.

3. Vereckei A, Duray G, Szénási G, et al. New algorithm using only lead aVR for differential diagnosis of wide QRS complex tachycardia. Heart Rhythm. 2008;5(1):89-98.

4. Brugada P. What to do in patients with suspected wide QRS complex tachycardia. JACC Clin Electrophysiol. 2022. (Basel Algorithm)

5. Pava LF, Perafán P, Badiel M, et al. R-wave peak time at DII: a new criterion for differentiating between wide complex QRS tachycardias. Heart Rhythm. 2010;7(7):922-926.

## Future Enhancements

- [ ] Add morphology criteria auto-detection for Brugada Step 4
- [ ] Implement uncertainty quantification for borderline cases
- [ ] Add visualization of step-by-step evaluation
- [ ] Support for 15-lead ECGs (V3R, V4R, V7-V9)
- [ ] Machine learning ensemble weighting based on validation data
- [ ] Real-time feedback for measurement quality

## Support

For questions or issues with these algorithms:
- Review test cases in `tests/core/algorithms/test_vt_svt.py`
- Check measurement format in examples above
- Ensure clinical data completeness for best results
