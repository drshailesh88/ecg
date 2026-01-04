# VT vs SVT Algorithms - Quick Reference

## One-Line Usage

```python
from core.algorithms.vt_svt import quick_vt_svt_check, detailed_vt_svt_analysis

# Quickest way - just get VT/SVT/Indeterminate
result = quick_vt_svt_check(measurements)

# Detailed analysis with all algorithm results
analysis = detailed_vt_svt_analysis(measurements)
```

## Minimal Working Example

```python
# Absolute minimum - just lead II R-wave peak time
measurements = {
    "leads": {
        "II": {"r_peak_time_ms": 60}
    }
}

result = quick_vt_svt_check(measurements)  # Returns "VT"
```

## Complete Example

```python
# Full data for all 4 algorithms
measurements = {
    # Clinical
    "age": 65,
    "has_structural_heart_disease": True,
    "has_av_dissociation": False,

    # ECG leads
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
print(f"{result['consensus']} with {result['confidence']:.0%} confidence")
```

## Individual Algorithm Usage

```python
from core.algorithms.vt_svt import BrugadaAlgorithm, VereckeiAlgorithm, BaselAlgorithm, PavaAlgorithm

# Run just one algorithm
pava = PavaAlgorithm()
result = pava.evaluate(measurements)

print(result.conclusion)  # "VT", "SVT", or "Indeterminate"
print(result.confidence)  # 0.0 to 1.0

# See reasoning
for step in result.steps:
    print(f"{step.criterion}: {step.reasoning}")
```

## Key Output Fields

```python
# From detailed_vt_svt_analysis()
result = {
    "consensus": "VT",                    # Final diagnosis
    "confidence": 0.95,                   # 0-1 confidence
    "recommendation": "HIGH CONFIDENCE VT: ...",  # Clinical advice
    "agreement": {
        "vt_count": 4,                    # Algorithms saying VT
        "svt_count": 0,                   # Algorithms saying SVT
        "agreement_level": "complete"     # complete/strong/moderate/poor
    },
    "individual_results": {
        "Brugada": {...},                 # Each algorithm's result
        "Vereckei": {...},
        "Basel": {...},
        "Pava": {...}
    },
    "summary": "ENSEMBLE CONCLUSION: VT..."  # Human-readable summary
}
```

## Required Data by Algorithm

| Algorithm | Minimal Required Data |
|-----------|----------------------|
| **Pava** | Lead II: r_peak_time_ms |
| **Basel** | age OR has_structural_heart_disease + lead II/aVR time_to_first_peak_ms |
| **Vereckei** | Lead aVR: initial_r_dominant, initial_deflection_ms, has_downstroke_notching, vi_vt_ratio |
| **Brugada** | Leads V1-V6: has_rs_complex, rs_interval_ms |

## Common Measurement Values

```python
# VT-suggesting values
"r_peak_time_ms": 60          # ≥50ms suggests VT (Pava)
"rs_interval_ms": 120          # >100ms suggests VT (Brugada)
"initial_deflection_ms": 50    # >40ms suggests VT (Vereckei)
"time_to_first_peak_ms": 55    # >40ms suggests VT (Basel)
"has_av_dissociation": True    # Virtually diagnostic of VT
"age": 70                      # >55 increases VT probability
"has_structural_heart_disease": True  # Increases VT probability

# SVT-suggesting values
"r_peak_time_ms": 40           # <50ms suggests SVT
"rs_interval_ms": 80           # ≤100ms suggests SVT
"vi_vt_ratio": 1.5             # >1.0 suggests SVT
"age": 25                      # Young age favors SVT
"has_structural_heart_disease": False  # Favors SVT
```

## Integration Pattern

```python
# In your ECG processing pipeline:

# 1. Load and process ECG image
ecg_image = load_ecg("patient_ecg.jpg")

# 2. Extract measurements (your image processing code)
measurements = extract_ecg_measurements(ecg_image)

# 3. Run VT/SVT analysis
from core.algorithms.vt_svt import detailed_vt_svt_analysis
result = detailed_vt_svt_analysis(measurements)

# 4. Display to user (tier-appropriate)
if user_tier == 1:  # RMP
    show_simple_verdict(result['consensus'], result['recommendation'])
elif user_tier == 2:  # MBBS student
    show_educational_breakdown(result['individual_results'])
elif user_tier == 3:  # Cardiology resident
    show_differential_diagnosis(result)
else:  # Electrophysiologist
    show_algorithm_comparison(result)
```

## Error Handling

```python
# Missing data is handled gracefully
measurements = {"leads": {}}  # No data

result = detailed_vt_svt_analysis(measurements)
# Returns: conclusion="Indeterminate", confidence=0.0
# Check: result['individual_results'][algo_name]['missing_data']
```

## Testing

```bash
# Run all tests
python tests/core/algorithms/test_vt_svt.py

# Run clinical scenarios demo
python examples/vt_svt_clinical_scenarios.py
```

## Import Shortcuts

```python
# Everything you need
from core.algorithms.vt_svt import (
    # Quick functions
    quick_vt_svt_check,
    detailed_vt_svt_analysis,

    # Individual algorithms
    BrugadaAlgorithm,
    VereckeiAlgorithm,
    BaselAlgorithm,
    PavaAlgorithm,
    VTSVTEnsemble,

    # Data structures
    AlgorithmResult,
    StepResult
)
```

## File Locations

- **Implementation**: `/home/user/ecg/src/core/algorithms/vt_svt.py`
- **Tests**: `/home/user/ecg/tests/core/algorithms/test_vt_svt.py`
- **Examples**: `/home/user/ecg/examples/vt_svt_clinical_scenarios.py`
- **Docs**: `/home/user/ecg/src/core/algorithms/README.md`
- **Quick Ref**: `/home/user/ecg/src/core/algorithms/QUICK_REFERENCE.md` (this file)
