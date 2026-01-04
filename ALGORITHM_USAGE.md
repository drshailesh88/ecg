# Algorithm Usage Guide

Quick reference for using the integrated ECG algorithms.

## Running Tests

```bash
# Test algorithm integration
python test_algorithm_integration.py
```

## Using Algorithms Directly

### STEMI Analysis

```python
from src.core.algorithms import analyze_stemi

measurements = {
    'leads': {
        'I': {'st_elevation_mm': 0.0, 'st_depression_mm': 1.5},
        'II': {'st_elevation_mm': 2.5, 'st_depression_mm': 0.0},
        'III': {'st_elevation_mm': 3.5, 'st_depression_mm': 0.0},
        'aVF': {'st_elevation_mm': 2.8, 'st_depression_mm': 0.0},
        # ... other leads
    },
    'patient_sex': 'male',
    'patient_age': 65,
}

result = analyze_stemi(measurements)

print(f"STEMI: {result.is_stemi}")
print(f"Territories: {result.territories}")
print(f"Culprit: {result.culprit_vessel}")
print(f"Actions: {result.recommended_actions}")
```

### VT/SVT Differentiation (Individual Algorithms)

```python
from src.core.algorithms import (
    BrugadaAlgorithm,
    BaselAlgorithm,
    VereckeiAlgorithm,
    PavaAlgorithm
)

measurements = {
    'age': 65,
    'has_structural_heart_disease': True,
    'leads': {
        'aVR': {
            'initial_r_dominant': True,
            'initial_deflection_ms': 50,
            'has_downstroke_notching': False,
            'vi_vt_ratio': 0.8,
            'time_to_first_peak_ms': 55,
        },
        'II': {
            'r_peak_time_ms': 65,
            'time_to_first_peak_ms': 65,
        },
        # ... other leads
    },
}

# Individual algorithm
brugada = BrugadaAlgorithm()
result = brugada.evaluate(measurements)

print(f"{result.name}: {result.conclusion}")
print(f"Confidence: {result.confidence:.0%}")

# See step-by-step reasoning
for step in result.steps:
    print(f"Step {step.step_number}: {step.criterion}")
    print(f"  Result: {step.result}")
    print(f"  Reasoning: {step.reasoning}")
```

### VT/SVT Ensemble (All 4 Algorithms)

```python
from src.core.algorithms import VTSVTEnsemble

ensemble = VTSVTEnsemble()
result = ensemble.evaluate(measurements)

print(f"Consensus: {result['consensus']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Agreement: {result['agreement']['agreement_level']}")
print(f"\nRecommendation:\n{result['recommendation']}")

# Individual algorithm results
for name, algo_result in result['individual_results'].items():
    print(f"{name}: {algo_result['conclusion']}")
```

## Using Through Inference Engine

```python
from src.api.inference import InferenceEngine
import asyncio

async def analyze_ecg():
    engine = InferenceEngine()

    measurements = {
        'heart_rate': 180,
        'qrs_duration_ms': 160,
        'leads': {...}
    }

    # Run all appropriate algorithms
    algorithm_results = await engine._run_algorithms(measurements, ["all"])

    # STEMI result
    if 'stemi' in algorithm_results:
        stemi = algorithm_results['stemi']
        print(f"STEMI: {stemi['is_stemi']}")

    # VT/SVT result
    if 'vt_svt_ensemble' in algorithm_results:
        vt_svt = algorithm_results['vt_svt_ensemble']
        print(f"VT/SVT: {vt_svt['consensus']}")

    # Get clinical findings
    findings = await engine._analyze_findings(measurements, algorithm_results)

    for finding in findings:
        print(f"{finding['finding']} ({finding['severity']})")
        print(f"  {finding['explanation']}")

# Run
asyncio.run(analyze_ecg())
```

## Measurement Format Reference

### Required for STEMI Analysis

```python
{
    'leads': {
        'I': {'st_elevation_mm': float, 'st_depression_mm': float},
        'II': {...},
        'III': {...},
        'aVR': {...},
        'aVL': {...},
        'aVF': {...},
        'V1': {...},
        'V2': {...},
        'V3': {...},
        'V4': {...},
        'V5': {...},
        'V6': {...},
    },
    'patient_sex': 'male' | 'female',  # Optional but recommended
    'patient_age': int,  # Optional but recommended
}
```

### Required for VT/SVT Analysis

#### Brugada Algorithm
```python
{
    'leads': {
        'V1': {'has_rs_complex': bool, 'rs_interval_ms': float},
        'V2': {...},
        # ... V3-V6 similar
    },
    'has_av_dissociation': bool,  # Optional
}
```

#### Basel Algorithm
```python
{
    'age': int,
    'has_structural_heart_disease': bool,
    'leads': {
        'II': {'time_to_first_peak_ms': float},
        'aVR': {'time_to_first_peak_ms': float},
    },
}
```

#### Vereckei Algorithm
```python
{
    'leads': {
        'aVR': {
            'initial_r_dominant': bool,
            'initial_deflection_ms': float,
            'has_downstroke_notching': bool,
            'vi_vt_ratio': float,  # Vi/Vt ratio
        },
    },
}
```

#### Pava Algorithm
```python
{
    'leads': {
        'II': {
            'r_peak_time_ms': float,  # Time from QRS onset to R peak
        },
    },
}
```

## Understanding Results

### STEMI Result

```python
{
    'is_stemi': bool,
    'territories': List[str],  # e.g., ['Inferior', 'Right Ventricle']
    'culprit_vessel': str,  # e.g., 'Right Coronary Artery (RCA)'
    'culprit_confidence': float,  # 0.0 to 1.0
    'segment_location': str,  # e.g., 'Proximal RCA'
    'st_changes': Dict[str, float],  # Lead name -> ST deviation in mm
    'urgent_findings': List[str],
    'recommended_actions': List[str],
    'differential_diagnosis': List[str],
    'additional_notes': List[str],
}
```

### VT/SVT Result (Individual Algorithm)

```python
{
    'name': str,  # Algorithm name
    'conclusion': str,  # 'VT', 'SVT', or 'Indeterminate'
    'confidence': float,  # 0.0 to 1.0
    'supports_vt': bool,
    'supports_svt': bool,
    'steps': [
        {
            'step_number': int,
            'criterion': str,
            'measured_value': Any,
            'threshold': Any,
            'result': str,  # 'positive', 'negative', 'not_evaluated'
            'reasoning': str,
        }
    ],
    'missing_data': List[str],
    'warnings': List[str],
}
```

### VT/SVT Ensemble Result

```python
{
    'individual_results': {
        'Brugada': {...},
        'Basel': {...},
        'Vereckei': {...},
        'Pava': {...},
    },
    'consensus': str,  # 'VT', 'SVT', or 'Indeterminate'
    'confidence': float,
    'agreement': {
        'vt_count': int,
        'svt_count': int,
        'indeterminate_count': int,
        'vt_algorithms': List[str],
        'svt_algorithms': List[str],
        'agreement_level': str,  # 'complete', 'strong', 'moderate', 'poor'
        'agreement_percentage': int,
    },
    'recommendation': str,  # Clinical recommendation
    'summary': str,  # Human-readable summary
}
```

## Clinical Safety Notes

1. **STEMI**: Any detected STEMI is marked as CRITICAL urgency
2. **VT**: In ambiguous cases, the ensemble defaults to "TREAT AS VT"
3. **Missing Data**: Algorithms report what data they need and degrade gracefully
4. **Confidence Scoring**: Reduced when data is missing or ambiguous
5. **Warnings**: Algorithms include warnings about limitations

## Example: Complete Workflow

```python
from src.core.algorithms import analyze_stemi, VTSVTEnsemble

# 1. Analyze for STEMI (always)
stemi_result = analyze_stemi(measurements)

if stemi_result.is_stemi:
    print("🚨 STEMI DETECTED - ACTIVATE CATH LAB")
    print(f"Territory: {', '.join(stemi_result.territories)}")
    print(f"Vessel: {stemi_result.culprit_vessel}")
    for action in stemi_result.recommended_actions[:5]:
        print(f"  • {action}")

# 2. Check for wide complex tachycardia
if measurements.get('qrs_duration_ms', 0) > 120 and measurements.get('heart_rate', 0) > 100:
    ensemble = VTSVTEnsemble()
    vt_result = ensemble.evaluate(measurements)

    print(f"\nVT/SVT Analysis: {vt_result['consensus']}")
    print(f"Confidence: {vt_result['confidence']:.0%}")
    print(f"\n{vt_result['recommendation']}")
```

## Files Reference

- **Algorithms**: `/home/user/ecg/src/core/algorithms/`
  - `vt_svt.py`: VT/SVT differentiation algorithms
  - `stemi.py`: STEMI detection and localization
  - `__init__.py`: Exports all algorithms

- **Inference Engine**: `/home/user/ecg/src/api/inference.py`
  - `InferenceEngine` class with algorithm integration

- **Tests**: `/home/user/ecg/test_algorithm_integration.py`
  - Comprehensive test suite with examples

## Quick Test

```bash
# Run comprehensive test
python test_algorithm_integration.py

# Expected output:
# ✅ ALL TESTS PASSED!
# Algorithms are properly integrated with the inference engine
```
