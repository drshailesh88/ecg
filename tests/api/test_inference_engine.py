"""
Comprehensive tests for InferenceEngine (Orchestration Layer)

Tests the main inference engine that:
- Processes ECG images
- Runs diagnostic algorithms
- Analyzes findings
- Generates LLM-powered interpretations
- Provides chat interface
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from src.api.inference import InferenceEngine
from src.ai.llm_client import LLMConfig, UserLevel as LLMUserLevel


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client to avoid real API calls"""
    mock_client = MagicMock()
    mock_client.analyze_async = AsyncMock(return_value="Mock LLM response with detailed analysis.")
    mock_client.stream_analyze_async = AsyncMock()
    return mock_client


@pytest.fixture
def inference_engine(mock_llm_client):
    """Create inference engine with mocked LLM"""
    engine = InferenceEngine(anthropic_api_key="test-key")
    engine._llm_client = mock_llm_client
    return engine


@pytest.fixture
def stemi_measurements():
    """Measurements indicating STEMI"""
    return {
        "heart_rate": 85,
        "pr_interval_ms": 160,
        "qrs_duration_ms": 95,
        "qt_interval_ms": 400,
        "qtc_ms": 420,
        "axis_degrees": 60,
        "rhythm": "sinus",
        "leads": {
            "I": {"st_elevation_mm": 0.0, "st_depression_mm": 1.5},
            "II": {"st_elevation_mm": 2.5, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 3.5, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVL": {"st_elevation_mm": 0.0, "st_depression_mm": 1.0},
            "aVF": {"st_elevation_mm": 2.8, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 1.8, "st_depression_mm": 0.0},
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
        },
        "patient_sex": "male",
        "patient_age": 65,
    }


@pytest.fixture
def no_stemi_measurements():
    """Normal measurements with no STEMI"""
    return {
        "heart_rate": 75,
        "pr_interval_ms": 160,
        "qrs_duration_ms": 90,
        "qt_interval_ms": 400,
        "qtc_ms": 420,
        "axis_degrees": 45,
        "rhythm": "sinus",
        "leads": {
            "I": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "II": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "III": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVR": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVL": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "aVF": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V1": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V2": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V3": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V4": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V5": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
            "V6": {"st_elevation_mm": 0.0, "st_depression_mm": 0.0},
        },
    }


@pytest.fixture
def vt_measurements():
    """Measurements indicating VT"""
    return {
        "heart_rate": 180,
        "pr_interval_ms": None,
        "qrs_duration_ms": 160,
        "rhythm": "wide_complex_tachycardia",
        "age": 65,
        "has_structural_heart_disease": True,
        "leads": {
            "I": {"has_rs_complex": False},
            "II": {"has_rs_complex": False, "r_peak_time_ms": 65, "time_to_first_peak_ms": 65},
            "III": {"has_rs_complex": False},
            "aVR": {
                "has_rs_complex": False,
                "initial_r_dominant": True,
                "initial_deflection_ms": 50,
                "has_downstroke_notching": False,
                "vi_vt_ratio": 0.8,
                "time_to_first_peak_ms": 55,
            },
            "aVL": {"has_rs_complex": False},
            "aVF": {"has_rs_complex": False},
            "V1": {"has_rs_complex": False, "rs_interval_ms": None},
            "V2": {"has_rs_complex": False, "rs_interval_ms": None},
            "V3": {"has_rs_complex": False, "rs_interval_ms": None},
            "V4": {"has_rs_complex": False, "rs_interval_ms": None},
            "V5": {"has_rs_complex": False, "rs_interval_ms": None},
            "V6": {"has_rs_complex": False, "rs_interval_ms": None},
        },
        "has_av_dissociation": False,
    }


@pytest.fixture
def svt_measurements():
    """Measurements indicating SVT with aberrancy"""
    return {
        "heart_rate": 170,
        "pr_interval_ms": None,
        "qrs_duration_ms": 130,
        "rhythm": "wide_complex_tachycardia",
        "age": 25,
        "has_structural_heart_disease": False,
        "leads": {
            "I": {"has_rs_complex": True},
            "II": {"has_rs_complex": True, "r_peak_time_ms": 35, "time_to_first_peak_ms": 35},
            "III": {"has_rs_complex": True},
            "aVR": {
                "has_rs_complex": True,
                "initial_r_dominant": False,
                "initial_deflection_ms": 25,
                "has_downstroke_notching": False,
                "vi_vt_ratio": 1.2,
                "time_to_first_peak_ms": 30,
            },
            "aVL": {"has_rs_complex": True},
            "aVF": {"has_rs_complex": True},
            "V1": {"has_rs_complex": True, "rs_interval_ms": 80},
            "V2": {"has_rs_complex": True, "rs_interval_ms": 85},
            "V3": {"has_rs_complex": True, "rs_interval_ms": 90},
            "V4": {"has_rs_complex": True, "rs_interval_ms": 85},
            "V5": {"has_rs_complex": True, "rs_interval_ms": 80},
            "V6": {"has_rs_complex": True, "rs_interval_ms": 75},
        },
        "has_av_dissociation": False,
    }


@pytest.fixture
def bradycardia_measurements():
    """Measurements with bradycardia"""
    return {
        "heart_rate": 45,
        "pr_interval_ms": 160,
        "qrs_duration_ms": 90,
        "qt_interval_ms": 450,
        "qtc_ms": 400,
        "axis_degrees": 50,
        "rhythm": "sinus",
    }


@pytest.fixture
def prolonged_qtc_measurements():
    """Measurements with prolonged QTc"""
    return {
        "heart_rate": 75,
        "pr_interval_ms": 160,
        "qrs_duration_ms": 90,
        "qt_interval_ms": 480,
        "qtc_ms": 510,
        "axis_degrees": 45,
        "rhythm": "sinus",
    }


@pytest.fixture
def first_degree_av_block_measurements():
    """Measurements with first-degree AV block"""
    return {
        "heart_rate": 70,
        "pr_interval_ms": 240,
        "qrs_duration_ms": 90,
        "qt_interval_ms": 400,
        "qtc_ms": 420,
        "axis_degrees": 50,
        "rhythm": "sinus",
    }


@pytest.fixture
def short_pr_measurements():
    """Measurements with short PR (pre-excitation)"""
    return {
        "heart_rate": 80,
        "pr_interval_ms": 100,
        "qrs_duration_ms": 130,
        "qt_interval_ms": 380,
        "qtc_ms": 410,
        "axis_degrees": 60,
        "rhythm": "sinus",
    }


@pytest.fixture
def wide_qrs_measurements():
    """Measurements with wide QRS (but not tachycardia)"""
    return {
        "heart_rate": 75,
        "pr_interval_ms": 160,
        "qrs_duration_ms": 135,
        "qt_interval_ms": 420,
        "qtc_ms": 440,
        "axis_degrees": -30,
        "rhythm": "sinus",
    }


# =============================================================================
# 1. Algorithm Execution Tests (15+ tests)
# =============================================================================

@pytest.mark.asyncio
async def test_run_stemi_analysis_with_stemi(inference_engine, stemi_measurements):
    """Test STEMI analysis detects STEMI correctly"""
    result = await inference_engine._run_stemi_analysis(stemi_measurements)

    assert result["is_stemi"] is True
    assert len(result["territories"]) > 0
    assert result["culprit_vessel"] is not None
    assert result["culprit_confidence"] > 0
    assert len(result["urgent_findings"]) > 0
    assert len(result["recommended_actions"]) > 0


@pytest.mark.asyncio
async def test_run_stemi_analysis_no_stemi(inference_engine, no_stemi_measurements):
    """Test STEMI analysis correctly identifies no STEMI"""
    result = await inference_engine._run_stemi_analysis(no_stemi_measurements)

    assert result["is_stemi"] is False
    assert len(result["territories"]) == 0
    assert result["culprit_vessel"] in ["None", "Unknown"]  # Either value is acceptable for no STEMI


@pytest.mark.asyncio
async def test_run_brugada_with_vt(inference_engine, vt_measurements):
    """Test Brugada algorithm detects VT"""
    result = await inference_engine._run_brugada(vt_measurements)

    assert result is not None
    assert "conclusion" in result
    assert "confidence" in result
    assert result["conclusion"] == "VT"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_run_basel_algorithm(inference_engine, vt_measurements):
    """Test Basel algorithm execution"""
    result = await inference_engine._run_basel(vt_measurements)

    assert result is not None
    assert "conclusion" in result
    assert "confidence" in result
    assert result["conclusion"] in ["VT", "SVT", "Indeterminate"]


@pytest.mark.asyncio
async def test_run_vereckei_algorithm(inference_engine, vt_measurements):
    """Test Vereckei algorithm execution"""
    result = await inference_engine._run_vereckei(vt_measurements)

    assert result is not None
    assert "conclusion" in result
    assert "confidence" in result
    assert result["conclusion"] in ["VT", "SVT", "Indeterminate"]


@pytest.mark.asyncio
async def test_run_pava_algorithm(inference_engine, vt_measurements):
    """Test Pava algorithm execution"""
    result = await inference_engine._run_pava(vt_measurements)

    assert result is not None
    assert "conclusion" in result
    assert "confidence" in result
    assert result["conclusion"] in ["VT", "SVT", "Indeterminate"]


@pytest.mark.asyncio
async def test_run_vt_svt_ensemble_vt_consensus(inference_engine, vt_measurements):
    """Test ensemble correctly identifies VT with consensus"""
    result = await inference_engine._run_vt_svt_ensemble(vt_measurements)

    assert result is not None
    assert "consensus" in result
    assert "confidence" in result
    assert result["consensus"] == "VT"
    assert result["confidence"] > 0.75


@pytest.mark.asyncio
async def test_run_vt_svt_ensemble_svt_consensus(inference_engine, svt_measurements):
    """Test ensemble correctly identifies SVT with consensus"""
    result = await inference_engine._run_vt_svt_ensemble(svt_measurements)

    assert result is not None
    assert "consensus" in result
    # SVT measurements should lead to SVT or at least not strong VT
    assert result["consensus"] in ["SVT", "Indeterminate"]


@pytest.mark.asyncio
async def test_run_vt_svt_ensemble_indeterminate(inference_engine):
    """Test ensemble handles indeterminate cases"""
    # Create measurements that are borderline
    measurements = {
        "heart_rate": 150,
        "qrs_duration_ms": 125,
        "rhythm": "wide_complex_tachycardia",
        "age": 45,
        "leads": {
            f"V{i}": {"has_rs_complex": True, "rs_interval_ms": 95}
            for i in range(1, 7)
        },
    }

    result = await inference_engine._run_vt_svt_ensemble(measurements)

    assert result is not None
    assert "consensus" in result
    assert result["consensus"] in ["VT", "SVT", "Indeterminate"]


@pytest.mark.asyncio
async def test_algorithm_selection_based_on_qrs_width(inference_engine, no_stemi_measurements):
    """Test VT/SVT algorithms only run when QRS > 120ms"""
    # Normal QRS, should not run VT/SVT algorithms
    results = await inference_engine._run_algorithms(no_stemi_measurements, ["all"])

    assert "stemi" in results  # STEMI always runs
    assert "vt_svt_ensemble" not in results  # Should not run with narrow QRS
    assert "brugada" not in results
    assert "basel" not in results


@pytest.mark.asyncio
async def test_algorithm_selection_based_on_heart_rate(inference_engine):
    """Test VT/SVT algorithms only run when HR > 100"""
    # Wide QRS but normal heart rate
    measurements = {
        "heart_rate": 80,  # Normal rate
        "qrs_duration_ms": 140,  # Wide QRS
        "rhythm": "sinus",
    }

    results = await inference_engine._run_algorithms(measurements, ["all"])

    assert "stemi" in results
    assert "vt_svt_ensemble" not in results  # Should not run without tachycardia


@pytest.mark.asyncio
async def test_vt_svt_algorithms_run_when_qrs_wide_and_hr_high(inference_engine, vt_measurements):
    """Test VT/SVT algorithms run when QRS > 120ms AND HR > 100"""
    results = await inference_engine._run_algorithms(vt_measurements, ["all"])

    assert "stemi" in results
    assert "vt_svt_ensemble" in results
    assert "brugada" in results
    assert "basel" in results
    assert "vereckei" in results
    assert "pava" in results


@pytest.mark.asyncio
async def test_specific_algorithm_selection(inference_engine, vt_measurements):
    """Test running specific algorithms only"""
    results = await inference_engine._run_algorithms(vt_measurements, ["brugada", "basel"])

    assert "brugada" in results
    assert "basel" in results
    assert "vereckei" not in results
    assert "pava" not in results


@pytest.mark.asyncio
async def test_stemi_always_runs(inference_engine, vt_measurements):
    """Test STEMI analysis always runs even when not explicitly requested"""
    results = await inference_engine._run_algorithms(vt_measurements, ["all"])

    assert "stemi" in results


@pytest.mark.asyncio
async def test_algorithm_results_have_required_fields(inference_engine, vt_measurements):
    """Test all algorithm results have required fields"""
    results = await inference_engine._run_algorithms(vt_measurements, ["all"])

    # Check STEMI result structure
    stemi = results["stemi"]
    assert "is_stemi" in stemi
    assert "territories" in stemi
    assert "culprit_vessel" in stemi

    # Check ensemble result structure
    ensemble = results["vt_svt_ensemble"]
    assert "consensus" in ensemble
    assert "confidence" in ensemble


# =============================================================================
# 2. Findings Analysis Tests (10+ tests)
# =============================================================================

@pytest.mark.asyncio
async def test_analyze_findings_with_critical_stemi(inference_engine, stemi_measurements):
    """Test findings analysis prioritizes STEMI"""
    stemi_result = await inference_engine._run_stemi_analysis(stemi_measurements)
    algorithm_results = {"stemi": stemi_result}

    findings = await inference_engine._analyze_findings(stemi_measurements, algorithm_results)

    assert len(findings) > 0
    # STEMI should be first (highest priority)
    assert findings[0]["category"] == "ischemia"
    assert "STEMI" in findings[0]["finding"]
    assert findings[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_analyze_findings_with_vt(inference_engine, vt_measurements):
    """Test findings analysis detects VT"""
    ensemble_result = await inference_engine._run_vt_svt_ensemble(vt_measurements)
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(vt_measurements),
        "vt_svt_ensemble": ensemble_result
    }

    findings = await inference_engine._analyze_findings(vt_measurements, algorithm_results)

    # Should have VT finding
    vt_finding = next((f for f in findings if f["category"] == "arrhythmia"), None)
    assert vt_finding is not None
    assert "VT" in vt_finding["finding"] or "Tachycardia" in vt_finding["finding"]


@pytest.mark.asyncio
async def test_analyze_findings_with_svt(inference_engine, svt_measurements):
    """Test findings analysis detects SVT"""
    ensemble_result = await inference_engine._run_vt_svt_ensemble(svt_measurements)
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(svt_measurements),
        "vt_svt_ensemble": ensemble_result
    }

    findings = await inference_engine._analyze_findings(svt_measurements, algorithm_results)

    # Should have arrhythmia finding
    arrhythmia_finding = next((f for f in findings if f["category"] == "arrhythmia"), None)
    assert arrhythmia_finding is not None


@pytest.mark.asyncio
async def test_analyze_findings_with_bradycardia(inference_engine, bradycardia_measurements):
    """Test findings analysis detects bradycardia"""
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(bradycardia_measurements)
    }

    findings = await inference_engine._analyze_findings(bradycardia_measurements, algorithm_results)

    # Should have bradycardia finding
    brady_finding = next((f for f in findings if "Bradycardia" in f["finding"]), None)
    assert brady_finding is not None
    assert brady_finding["severity"] in ["abnormal", "critical"]


@pytest.mark.asyncio
async def test_analyze_findings_with_tachycardia(inference_engine):
    """Test findings analysis detects tachycardia"""
    measurements = {
        "heart_rate": 120,
        "qrs_duration_ms": 90,
        "rhythm": "sinus",
    }
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(measurements)
    }

    findings = await inference_engine._analyze_findings(measurements, algorithm_results)

    # Should have tachycardia finding
    tachy_finding = next((f for f in findings if "Tachycardia" in f["finding"]), None)
    assert tachy_finding is not None


@pytest.mark.asyncio
async def test_analyze_findings_with_prolonged_qtc(inference_engine, prolonged_qtc_measurements):
    """Test findings analysis detects prolonged QTc"""
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(prolonged_qtc_measurements)
    }

    findings = await inference_engine._analyze_findings(prolonged_qtc_measurements, algorithm_results)

    # Should have prolonged QTc finding
    qtc_finding = next((f for f in findings if "QTc" in f["finding"]), None)
    assert qtc_finding is not None
    assert qtc_finding["category"] == "repolarization"
    assert "torsades" in qtc_finding["explanation"].lower()


@pytest.mark.asyncio
async def test_analyze_findings_with_first_degree_av_block(inference_engine, first_degree_av_block_measurements):
    """Test findings analysis detects first-degree AV block"""
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(first_degree_av_block_measurements)
    }

    findings = await inference_engine._analyze_findings(first_degree_av_block_measurements, algorithm_results)

    # Should have AV block finding
    av_finding = next((f for f in findings if "AV block" in f["finding"]), None)
    assert av_finding is not None
    assert av_finding["category"] == "conduction"


@pytest.mark.asyncio
async def test_analyze_findings_with_short_pr(inference_engine, short_pr_measurements):
    """Test findings analysis detects short PR (pre-excitation)"""
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(short_pr_measurements)
    }

    findings = await inference_engine._analyze_findings(short_pr_measurements, algorithm_results)

    # Should have short PR finding
    pr_finding = next((f for f in findings if "Short PR" in f["finding"]), None)
    assert pr_finding is not None
    assert "WPW" in pr_finding["explanation"] or "pre-excitation" in pr_finding["explanation"]


@pytest.mark.asyncio
async def test_analyze_findings_with_wide_qrs(inference_engine, wide_qrs_measurements):
    """Test findings analysis detects wide QRS"""
    algorithm_results = {
        "stemi": await inference_engine._run_stemi_analysis(wide_qrs_measurements)
    }

    findings = await inference_engine._analyze_findings(wide_qrs_measurements, algorithm_results)

    # Should have wide QRS finding
    qrs_finding = next((f for f in findings if "Wide QRS" in f["finding"]), None)
    assert qrs_finding is not None
    assert "bundle branch block" in qrs_finding["explanation"].lower()


@pytest.mark.asyncio
async def test_findings_priority_ordering(inference_engine, stemi_measurements):
    """Test findings are prioritized correctly (STEMI first, then VT/SVT, then intervals)"""
    # Add wide QRS and tachycardia to trigger VT/SVT analysis
    stemi_measurements["qrs_duration_ms"] = 140
    stemi_measurements["heart_rate"] = 120

    stemi_result = await inference_engine._run_stemi_analysis(stemi_measurements)
    ensemble_result = await inference_engine._run_vt_svt_ensemble(stemi_measurements)

    algorithm_results = {
        "stemi": stemi_result,
        "vt_svt_ensemble": ensemble_result
    }

    findings = await inference_engine._analyze_findings(stemi_measurements, algorithm_results)

    # STEMI should be first if present
    if stemi_result["is_stemi"]:
        assert findings[0]["category"] == "ischemia"
        assert "STEMI" in findings[0]["finding"]


# =============================================================================
# 3. Interpretation Generation Tests (5+ tests)
# =============================================================================

@pytest.mark.asyncio
async def test_generate_interpretation_with_urgent_findings(inference_engine, stemi_measurements):
    """Test interpretation generation marks urgent findings correctly"""
    stemi_result = await inference_engine._run_stemi_analysis(stemi_measurements)
    findings = [{
        "category": "ischemia",
        "finding": "ACUTE STEMI",
        "severity": "critical",
        "confidence": 0.98,
    }]

    interpretation = await inference_engine._generate_interpretation(
        measurements=stemi_measurements,
        findings=findings,
        algorithm_results={"stemi": stemi_result},
        user_level="resident"
    )

    assert interpretation["is_urgent"] is True
    assert interpretation["urgency_reason"] is not None
    assert "STEMI" in interpretation["urgency_reason"]
    assert len(interpretation["actions"]) > 0


@pytest.mark.asyncio
async def test_generate_interpretation_user_level_rmp(inference_engine, no_stemi_measurements, mock_llm_client):
    """Test interpretation adapts to RMP level"""
    findings = [{"finding": "Normal ECG", "severity": "normal"}]

    interpretation = await inference_engine._generate_interpretation(
        measurements=no_stemi_measurements,
        findings=findings,
        algorithm_results={},
        user_level="rmp"
    )

    # Should call LLM with RMP level
    assert mock_llm_client.analyze_async.called
    call_args = mock_llm_client.analyze_async.call_args
    assert call_args.kwargs["user_level"] == LLMUserLevel.RMP


@pytest.mark.asyncio
async def test_generate_interpretation_user_level_cardiologist(inference_engine, vt_measurements, mock_llm_client):
    """Test interpretation adapts to cardiologist level"""
    findings = [{"finding": "VT", "severity": "critical"}]
    ensemble_result = await inference_engine._run_vt_svt_ensemble(vt_measurements)

    interpretation = await inference_engine._generate_interpretation(
        measurements=vt_measurements,
        findings=findings,
        algorithm_results={"vt_svt_ensemble": ensemble_result},
        user_level="cardiologist"
    )

    # Should call LLM with cardiologist level
    assert mock_llm_client.analyze_async.called
    call_args = mock_llm_client.analyze_async.call_args
    assert call_args.kwargs["user_level"] == LLMUserLevel.CARDIOLOGIST


@pytest.mark.asyncio
async def test_extract_summary_from_llm_output(inference_engine):
    """Test summary extraction from LLM output"""
    llm_output = "This is a comprehensive analysis of the ECG showing normal sinus rhythm.\nAdditional details follow."

    summary = inference_engine._extract_summary(llm_output)

    assert len(summary) > 0
    assert len(summary) <= 200
    assert "comprehensive" in summary.lower() or "normal" in summary.lower()


@pytest.mark.asyncio
async def test_action_recommendations_for_stemi(inference_engine, stemi_measurements):
    """Test action recommendations are appropriate for STEMI"""
    stemi_result = await inference_engine._run_stemi_analysis(stemi_measurements)
    findings = [{"finding": "ACUTE STEMI", "severity": "critical"}]

    interpretation = await inference_engine._generate_interpretation(
        measurements=stemi_measurements,
        findings=findings,
        algorithm_results={"stemi": stemi_result},
        user_level="resident"
    )

    actions = interpretation["actions"]
    assert len(actions) > 0
    # Should have STEMI-specific actions
    action_text = " ".join(actions).lower()
    assert any(keyword in action_text for keyword in ["cath", "pci", "aspirin", "emergency"])


@pytest.mark.asyncio
async def test_action_recommendations_for_vt(inference_engine, vt_measurements):
    """Test action recommendations are appropriate for VT"""
    ensemble_result = await inference_engine._run_vt_svt_ensemble(vt_measurements)
    findings = [{"finding": "VT", "severity": "critical"}]

    interpretation = await inference_engine._generate_interpretation(
        measurements=vt_measurements,
        findings=findings,
        algorithm_results={"vt_svt_ensemble": ensemble_result},
        user_level="resident"
    )

    actions = interpretation["actions"]
    assert len(actions) > 0
    # Should have VT-specific actions
    action_text = " ".join(actions).lower()
    assert any(keyword in action_text for keyword in ["hemodynamic", "cardioversion", "antiarrhythmic", "cardiology"])


# =============================================================================
# 4. Chat Interface Tests (5+ tests)
# =============================================================================

@pytest.mark.asyncio
async def test_chat_with_analysis_context(inference_engine, mock_llm_client):
    """Test chat uses analysis context when available"""
    # Setup analysis in cache
    analysis_id = "test123"
    inference_engine._analysis_cache[analysis_id] = {
        "measurements": {"heart_rate": 75},
        "findings": [{"finding": "Normal", "severity": "normal"}],
    }

    response = await inference_engine.chat(
        message="What does this ECG show?",
        analysis_id=analysis_id,
        user_level="student"
    )

    assert "response" in response
    assert "suggested_questions" in response
    assert mock_llm_client.analyze_async.called


@pytest.mark.asyncio
async def test_chat_without_analysis_context(inference_engine, mock_llm_client):
    """Test chat works without analysis context"""
    response = await inference_engine.chat(
        message="What is a normal heart rate?",
        user_level="student"
    )

    assert "response" in response
    assert "suggested_questions" in response
    assert mock_llm_client.analyze_async.called


@pytest.mark.asyncio
async def test_chat_with_conversation_history(inference_engine, mock_llm_client):
    """Test chat includes conversation history"""
    history = [
        {"role": "user", "content": "What is this rhythm?"},
        {"role": "assistant", "content": "This is sinus rhythm."},
    ]

    response = await inference_engine.chat(
        message="What's the heart rate?",
        user_level="resident",
        history=history
    )

    assert mock_llm_client.analyze_async.called
    call_args = mock_llm_client.analyze_async.call_args
    # Should have conversation history
    assert "conversation_history" in call_args.kwargs


@pytest.mark.asyncio
async def test_chat_user_level_mapping(inference_engine, mock_llm_client):
    """Test chat correctly maps user levels"""
    test_cases = [
        ("rmp", LLMUserLevel.RMP),
        ("student", LLMUserLevel.STUDENT),
        ("resident", LLMUserLevel.RESIDENT),
        ("cardiologist", LLMUserLevel.CARDIOLOGIST),
    ]

    for user_level, expected_llm_level in test_cases:
        await inference_engine.chat(
            message="Test question",
            user_level=user_level
        )

        call_args = mock_llm_client.analyze_async.call_args
        assert call_args.kwargs["user_level"] == expected_llm_level


@pytest.mark.asyncio
async def test_chat_suggested_questions_generation(inference_engine):
    """Test chat generates suggested follow-up questions"""
    response = await inference_engine.chat(
        message="What is this ECG?",
        user_level="student"
    )

    suggested = response["suggested_questions"]
    assert len(suggested) > 0
    assert all(isinstance(q, str) for q in suggested)
    assert all("?" in q for q in suggested)


# =============================================================================
# 5. Integration Tests (5+ tests)
# =============================================================================

@pytest.mark.asyncio
async def test_full_analyze_flow_with_mock_image(inference_engine, mock_llm_client):
    """Test full analyze() flow from image to interpretation"""
    import base64

    # Create minimal test image data
    fake_image = b"fake ECG image data"
    image_base64 = base64.b64encode(fake_image).decode()

    # Mock the image processing and measurement extraction
    with patch.object(inference_engine, '_process_ecg_image') as mock_process:
        with patch.object(inference_engine, '_extract_measurements') as mock_extract:
            mock_process.return_value = {"leads_detected": ["I", "II"]}
            mock_extract.return_value = {
                "heart_rate": 75,
                "pr_interval_ms": 160,
                "qrs_duration_ms": 90,
                "rhythm": "sinus",
            }

            result = await inference_engine.analyze(
                image_base64=image_base64,
                user_level="student",
                include_teaching=False
            )

    # Verify result structure
    assert "analysis_id" in result
    assert "summary" in result
    assert "measurements" in result
    assert "findings" in result
    assert "algorithm_results" in result
    assert "is_urgent" in result
    assert "recommended_actions" in result


@pytest.mark.asyncio
async def test_analysis_caching(inference_engine):
    """Test analysis results are cached"""
    import base64

    fake_image = b"fake ECG image"
    image_base64 = base64.b64encode(fake_image).decode()

    with patch.object(inference_engine, '_process_ecg_image'):
        with patch.object(inference_engine, '_extract_measurements') as mock_extract:
            mock_extract.return_value = {
                "heart_rate": 75,
                "qrs_duration_ms": 90,
                "rhythm": "sinus",
            }

            result = await inference_engine.analyze(
                image_base64=image_base64,
                user_level="student",
                include_teaching=False
            )

    # Check analysis is cached
    analysis_id = result["analysis_id"]
    assert analysis_id in inference_engine._analysis_cache
    assert inference_engine._analysis_cache[analysis_id] == result


@pytest.mark.asyncio
async def test_error_handling_when_llm_unavailable(inference_engine):
    """Test graceful handling when LLM is unavailable"""
    # Make LLM fail
    inference_engine._llm_client.analyze_async = AsyncMock(side_effect=Exception("API Error"))

    import base64
    fake_image = b"fake ECG"
    image_base64 = base64.b64encode(fake_image).decode()

    with patch.object(inference_engine, '_process_ecg_image'):
        with patch.object(inference_engine, '_extract_measurements') as mock_extract:
            mock_extract.return_value = {
                "heart_rate": 75,
                "qrs_duration_ms": 90,
                "rhythm": "sinus",
            }

            result = await inference_engine.analyze(
                image_base64=image_base64,
                user_level="student",
                include_teaching=False
            )

    # Should still return result with fallback interpretation
    assert result is not None
    assert "summary" in result
    assert "findings" in result


@pytest.mark.asyncio
async def test_teaching_content_retrieval(inference_engine):
    """Test teaching content is retrieved when requested"""
    import base64

    # Mock RAG to be available
    mock_rag = MagicMock()
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "Teaching Case", "source": "Textbook"}
    mock_doc.content = "This is a teaching case about STEMI..."
    mock_rag.query_for_teaching = MagicMock(return_value=([mock_doc], "Teaching context"))

    inference_engine._rag = mock_rag

    fake_image = b"fake ECG"
    image_base64 = base64.b64encode(fake_image).decode()

    with patch.object(inference_engine, '_process_ecg_image'):
        with patch.object(inference_engine, '_extract_measurements') as mock_extract:
            mock_extract.return_value = {
                "heart_rate": 75,
                "qrs_duration_ms": 90,
                "rhythm": "sinus",
            }

            result = await inference_engine.analyze(
                image_base64=image_base64,
                user_level="student",
                include_teaching=True  # Request teaching content
            )

    # Should have teaching content
    assert "teaching_content" in result
    assert "similar_cases" in result


@pytest.mark.asyncio
async def test_processing_time_tracking(inference_engine):
    """Test processing time is tracked and returned"""
    import base64

    fake_image = b"fake ECG"
    image_base64 = base64.b64encode(fake_image).decode()

    with patch.object(inference_engine, '_process_ecg_image'):
        with patch.object(inference_engine, '_extract_measurements') as mock_extract:
            mock_extract.return_value = {
                "heart_rate": 75,
                "qrs_duration_ms": 90,
                "rhythm": "sinus",
            }

            result = await inference_engine.analyze(
                image_base64=image_base64,
                user_level="student",
                include_teaching=False
            )

    assert "processing_time_ms" in result
    assert isinstance(result["processing_time_ms"], int)
    assert result["processing_time_ms"] >= 0


# =============================================================================
# Summary Stats
# =============================================================================

def test_summary():
    """Print test coverage summary"""
    print("\n" + "="*70)
    print("Inference Engine Test Suite Summary")
    print("="*70)
    print("\nTest Categories:")
    print("  1. Algorithm Execution Tests:       15 tests")
    print("  2. Findings Analysis Tests:         10 tests")
    print("  3. Interpretation Generation:        5 tests")
    print("  4. Chat Interface Tests:             5 tests")
    print("  5. Integration Tests:                5 tests")
    print("\n  TOTAL:                              40 tests")
    print("="*70 + "\n")
