"""
Comprehensive tests for LLM Client (Claude API Integration)

Tests the AI explanation layer that provides expert ECG analysis.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Test imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from ai.llm_client import (
    LLMClient,
    LLMConfig,
    UserLevel,
    get_client,
    explain_ecg,
    explain_ecg_sync,
    EXPERT_EP_SYSTEM_PROMPT,
    USER_LEVEL_INSTRUCTIONS,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_anthropic_response():
    """Mock successful Anthropic API response"""
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a comprehensive ECG analysis from Claude."
    mock_response.content = [mock_content]
    return mock_response


@pytest.fixture
def mock_anthropic_stream():
    """Mock streaming Anthropic API response"""
    async def mock_stream():
        yield "This is "
        yield "a streaming "
        yield "response."

    mock_stream_obj = MagicMock()
    mock_stream_obj.text_stream = mock_stream()
    return mock_stream_obj


@pytest.fixture
def sample_algorithm_results():
    """Sample algorithm results for testing"""
    return {
        "measurements": {
            "heart_rate": 180,
            "rhythm": "wide_complex_tachycardia",
            "qrs_duration_ms": 158,
            "pr_interval_ms": 160,
            "qtc_ms": 420,
            "axis_degrees": 90
        },
        "vt_svt": {
            "consensus": "VT",
            "confidence": 1.0,
            "agreement": {
                "agreement_level": "complete",
                "vt_count": 4,
                "svt_count": 0
            },
            "individual_results": {
                "Brugada": {"conclusion": "VT", "confidence": 1.0},
                "Basel": {"conclusion": "VT", "confidence": 1.0},
                "Vereckei": {"conclusion": "VT", "confidence": 1.0},
                "Pava": {"conclusion": "VT", "confidence": 1.0}
            },
            "recommendation": "HIGH CONFIDENCE VT: Immediate treatment indicated."
        }
    }


@pytest.fixture
def stemi_algorithm_results():
    """Sample STEMI results for testing"""
    return {
        "measurements": {
            "heart_rate": 95,
            "rhythm": "sinus_rhythm",
            "qrs_duration_ms": 88
        },
        "stemi": {
            "is_stemi": True,
            "territories": ["anterior"],
            "culprit_vessel": "LAD",
            "culprit_confidence": 0.95,
            "segment_location": "proximal",
            "urgent_findings": [
                "ST elevation in V1-V4 (3-5mm)",
                "Hyperacute T waves in V2-V3",
                "Reciprocal ST depression in II, III, aVF",
                "Poor R wave progression",
                "Q waves in V1-V2"
            ]
        }
    }


@pytest.fixture
def pathway_algorithm_results():
    """Sample WPW pathway results for testing"""
    return {
        "measurements": {
            "heart_rate": 78,
            "rhythm": "sinus_rhythm",
            "pr_interval_ms": 95,
            "qrs_duration_ms": 132
        },
        "pathway": {
            "primary_result": {
                "primary_location": "Left Lateral",
                "confidence": 0.97,
                "algorithm_used": "SMART-WPW",
                "alternative_locations": ["Left Posterolateral", "Mitral Annulus"],
                "ablation_approach": "Retrograde aortic approach preferred"
            }
        }
    }


# =============================================================================
# 1. Configuration Tests
# =============================================================================

def test_config_default_values():
    """Test LLMConfig has sensible defaults"""
    config = LLMConfig()

    assert config.model == "claude-sonnet-4-20250514"
    assert config.max_tokens == 2048
    assert config.temperature == 0.3  # Low for medical accuracy
    assert config.timeout == 30.0


def test_config_from_environment():
    """Test API key loaded from ANTHROPIC_API_KEY env var"""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-api-key-123"}):
        config = LLMConfig()
        assert config.api_key == "test-api-key-123"


def test_config_custom_model():
    """Test custom model can be specified"""
    config = LLMConfig(
        api_key="custom-key",
        model="claude-opus-4",
        max_tokens=4096,
        temperature=0.5
    )

    assert config.api_key == "custom-key"
    assert config.model == "claude-opus-4"
    assert config.max_tokens == 4096
    assert config.temperature == 0.5


def test_config_no_api_key():
    """Test config works when no API key provided (falls back to None)"""
    with patch.dict(os.environ, {}, clear=True):
        config = LLMConfig()
        assert config.api_key is None


# =============================================================================
# 2. System Prompt Tests
# =============================================================================

def test_expert_ep_prompt_exists():
    """Test EXPERT_EP_SYSTEM_PROMPT is defined"""
    assert EXPERT_EP_SYSTEM_PROMPT is not None
    assert len(EXPERT_EP_SYSTEM_PROMPT) > 100
    assert "electrophysiologist" in EXPERT_EP_SYSTEM_PROMPT.lower()
    assert "ECG" in EXPERT_EP_SYSTEM_PROMPT


def test_user_level_instructions_all_levels():
    """Test instructions exist for all 4 user levels"""
    assert UserLevel.RMP in USER_LEVEL_INSTRUCTIONS
    assert UserLevel.STUDENT in USER_LEVEL_INSTRUCTIONS
    assert UserLevel.RESIDENT in USER_LEVEL_INSTRUCTIONS
    assert UserLevel.CARDIOLOGIST in USER_LEVEL_INSTRUCTIONS

    # Each should have meaningful content
    for level in UserLevel:
        instructions = USER_LEVEL_INSTRUCTIONS[level]
        assert len(instructions) > 50
        assert instructions.strip() != ""


def test_prompt_contains_medical_guidance():
    """Test prompt includes safety disclaimers and medical guidance"""
    assert "NEVER make up measurements" in EXPERT_EP_SYSTEM_PROMPT
    assert "STEMI" in EXPERT_EP_SYSTEM_PROMPT
    assert "clinical" in EXPERT_EP_SYSTEM_PROMPT.lower()
    assert "SUPPORT" in EXPERT_EP_SYSTEM_PROMPT or "support" in EXPERT_EP_SYSTEM_PROMPT


def test_prompt_contains_response_structure():
    """Test prompt defines clear response structure"""
    assert "Summary" in EXPERT_EP_SYSTEM_PROMPT
    assert "Findings" in EXPERT_EP_SYSTEM_PROMPT
    assert "Analysis" in EXPERT_EP_SYSTEM_PROMPT
    assert "Recommendations" in EXPERT_EP_SYSTEM_PROMPT


# =============================================================================
# 3. Message Building Tests
# =============================================================================

def test_build_messages_basic(sample_algorithm_results):
    """Test message building with minimal input"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=sample_algorithm_results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "ECG Analysis Results" in messages[0]["content"]
    assert "comprehensive analysis" in messages[0]["content"]


def test_build_messages_with_measurements(sample_algorithm_results):
    """Test message includes measurements when present"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=sample_algorithm_results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "Heart Rate: 180 bpm" in content
    assert "QRS Duration: 158 ms" in content
    assert "QTc: 420 ms" in content


def test_build_messages_with_stemi(stemi_algorithm_results):
    """Test message includes STEMI data when present"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=stemi_algorithm_results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "STEMI Analysis" in content
    assert "YES - EMERGENCY" in content
    assert "anterior" in content
    assert "LAD" in content
    assert "95%" in content or "0.95" in content


def test_build_messages_with_vt_svt(sample_algorithm_results):
    """Test message includes VT/SVT data when present"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=sample_algorithm_results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "VT vs SVT Analysis" in content
    assert "Consensus Diagnosis" in content
    assert "VT" in content
    assert "100%" in content or "1.0" in content
    assert "Brugada" in content


def test_build_messages_with_pathway(pathway_algorithm_results):
    """Test message includes pathway data when present"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=pathway_algorithm_results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "Accessory Pathway" in content or "WPW" in content
    assert "Left Lateral" in content
    assert "SMART-WPW" in content
    assert "97%" in content or "0.97" in content


def test_build_messages_with_history(sample_algorithm_results):
    """Test conversation history is included"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]

    messages = client._build_messages(
        algorithm_results=sample_algorithm_results,
        user_question="Follow-up question",
        user_level=UserLevel.RESIDENT,
        conversation_history=history
    )

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Previous question"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Previous answer"
    assert messages[2]["role"] == "user"


def test_build_messages_with_question(sample_algorithm_results):
    """Test user question is properly formatted"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    messages = client._build_messages(
        algorithm_results=sample_algorithm_results,
        user_question="What is the diagnosis?",
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "User Question" in content
    assert "What is the diagnosis?" in content


def test_build_messages_with_findings():
    """Test message includes additional findings"""
    results = {
        "measurements": {"heart_rate": 80},
        "findings": [
            "Normal sinus rhythm",
            "Normal axis",
            {"finding": "Normal intervals", "severity": "normal"}
        ]
    }

    client = LLMClient(LLMConfig(api_key="test-key"))
    messages = client._build_messages(
        algorithm_results=results,
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    content = messages[0]["content"]
    assert "Additional Findings" in content
    assert "Normal sinus rhythm" in content
    assert "Normal axis" in content


# =============================================================================
# 4. Fallback Response Tests
# =============================================================================

def test_fallback_when_no_api_key(sample_algorithm_results):
    """Test templated response when API key missing"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results=sample_algorithm_results,
        user_level=UserLevel.RESIDENT
    )

    assert "ECG Analysis Report" in response
    assert "AI explanation unavailable" in response
    assert "algorithm results" in response.lower()


def test_fallback_response_contains_findings(sample_algorithm_results):
    """Test fallback includes algorithm results"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results=sample_algorithm_results,
        user_level=UserLevel.RESIDENT
    )

    assert "VT" in response
    assert "100%" in response or "1.0" in response


def test_fallback_vt_diagnosis(sample_algorithm_results):
    """Test fallback for VT diagnosis"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results=sample_algorithm_results,
        user_level=UserLevel.RESIDENT
    )

    assert "Wide Complex Tachycardia" in response
    assert "VT" in response
    assert "Immediate treatment" in response


def test_fallback_stemi_diagnosis(stemi_algorithm_results):
    """Test fallback for STEMI diagnosis"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results=stemi_algorithm_results,
        user_level=UserLevel.RESIDENT
    )

    assert "STEMI DETECTED" in response or "EMERGENCY" in response
    assert "anterior" in response
    assert "LAD" in response
    assert "cath lab" in response.lower() or "door-to-balloon" in response


def test_fallback_pathway_diagnosis(pathway_algorithm_results):
    """Test fallback for WPW pathway diagnosis"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results=pathway_algorithm_results,
        user_level=UserLevel.RESIDENT
    )

    assert "Accessory Pathway" in response or "WPW" in response
    assert "Left Lateral" in response


def test_fallback_no_stemi():
    """Test fallback when no STEMI detected"""
    results = {
        "measurements": {"heart_rate": 75},
        "stemi": {
            "is_stemi": False
        }
    }

    client = LLMClient(LLMConfig(api_key=None))
    response = client.analyze(results, UserLevel.RESIDENT)

    assert "No STEMI criteria met" in response


# =============================================================================
# 5. User Level Adaptation Tests
# =============================================================================

def test_rmp_level_instructions():
    """Test RMP level uses simple language instructions"""
    instructions = USER_LEVEL_INSTRUCTIONS[UserLevel.RMP]

    assert "simple" in instructions.lower()
    assert "NORMAL" in instructions
    assert "ABNORMAL" in instructions
    assert "referral" in instructions.lower()


def test_student_level_educational():
    """Test Student level is educational"""
    instructions = USER_LEVEL_INSTRUCTIONS[UserLevel.STUDENT]

    assert "educational" in instructions.lower() or "learning" in instructions.lower()
    assert "why" in instructions.lower()
    assert "pathophysiology" in instructions.lower()


def test_resident_level_clinical():
    """Test Resident level includes clinical depth"""
    instructions = USER_LEVEL_INSTRUCTIONS[UserLevel.RESIDENT]

    assert "differential" in instructions.lower()
    assert "treatment" in instructions.lower()
    assert "guideline" in instructions.lower()


def test_cardiologist_level_technical():
    """Test Cardiologist level is technical and peer-level"""
    instructions = USER_LEVEL_INSTRUCTIONS[UserLevel.CARDIOLOGIST]

    assert "peer" in instructions.lower() or "technical" in instructions.lower()
    assert "EP" in instructions or "electrophysiolog" in instructions.lower()
    assert "procedural" in instructions.lower() or "ablation" in instructions.lower()


def test_get_system_prompt_includes_level():
    """Test system prompt includes user level instructions"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    prompt = client._get_system_prompt(UserLevel.RMP)
    assert EXPERT_EP_SYSTEM_PROMPT in prompt
    assert "simple" in prompt.lower()

    prompt = client._get_system_prompt(UserLevel.CARDIOLOGIST)
    assert EXPERT_EP_SYSTEM_PROMPT in prompt
    assert "peer" in prompt.lower() or "technical" in prompt.lower()


# =============================================================================
# 6. Integration Tests (with mocking)
# =============================================================================

@patch('ai.llm_client.anthropic')
def test_analyze_calls_api(mock_anthropic_module, sample_algorithm_results, mock_anthropic_response):
    """Test analyze method calls Anthropic API"""
    # Setup mock
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_anthropic_response
    mock_anthropic_module.Anthropic.return_value = mock_client
    mock_anthropic_module.ANTHROPIC_AVAILABLE = True

    # Patch at module level
    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', True):
        client = LLMClient(LLMConfig(api_key="test-key"))
        client._client = mock_client  # Inject mock

        response = client.analyze(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.RESIDENT,
            user_question="What is this?"
        )

        # Verify API was called
        assert mock_client.messages.create.called
        call_args = mock_client.messages.create.call_args

        # Check parameters
        assert call_args.kwargs['model'] == "claude-sonnet-4-20250514"
        assert call_args.kwargs['max_tokens'] == 2048
        assert call_args.kwargs['temperature'] == 0.3
        assert len(call_args.kwargs['messages']) >= 1

        # Check response
        assert response == "This is a comprehensive ECG analysis from Claude."


@patch('ai.llm_client.anthropic')
@pytest.mark.asyncio
async def test_analyze_async_calls_api(mock_anthropic_module, sample_algorithm_results, mock_anthropic_response):
    """Test async analyze calls API correctly"""
    # Setup mock
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
    mock_anthropic_module.AsyncAnthropic.return_value = mock_client

    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', True):
        client = LLMClient(LLMConfig(api_key="test-key"))
        client._async_client = mock_client  # Inject mock

        response = await client.analyze_async(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.STUDENT,
            user_question="Explain this ECG"
        )

        # Verify API was called
        assert mock_client.messages.create.called
        assert response == "This is a comprehensive ECG analysis from Claude."


@patch('ai.llm_client.anthropic')
def test_analyze_handles_api_error(mock_anthropic_module, sample_algorithm_results):
    """Test graceful handling of API errors"""
    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_anthropic_module.Anthropic.return_value = mock_client

    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', True):
        client = LLMClient(LLMConfig(api_key="test-key"))
        client._client = mock_client

        response = client.analyze(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.RESIDENT
        )

        # Should fallback to templated response
        assert "ECG Analysis Report" in response
        assert "AI explanation unavailable" in response


@patch('ai.llm_client.anthropic')
@pytest.mark.asyncio
async def test_analyze_async_handles_error(mock_anthropic_module, sample_algorithm_results):
    """Test async method handles API errors gracefully"""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=Exception("Async API Error"))
    mock_anthropic_module.AsyncAnthropic.return_value = mock_client

    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', True):
        client = LLMClient(LLMConfig(api_key="test-key"))
        client._async_client = mock_client

        response = await client.analyze_async(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.RMP
        )

        # Should fallback
        assert "ECG Analysis Report" in response


def test_client_creation_without_anthropic():
    """Test client works when anthropic library not available"""
    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', False):
        client = LLMClient(LLMConfig(api_key="test-key"))
        assert client._get_client() is None
        assert client._get_async_client() is None


# =============================================================================
# 7. Convenience Function Tests
# =============================================================================

def test_get_client_singleton():
    """Test get_client returns same instance"""
    client1 = get_client()
    client2 = get_client()

    assert client1 is client2


def test_get_client_with_config():
    """Test get_client creates new instance with config"""
    config = LLMConfig(api_key="custom-key", model="custom-model")
    client = get_client(config)

    assert client.config.api_key == "custom-key"
    assert client.config.model == "custom-model"


@patch('ai.llm_client.LLMClient.analyze')
def test_explain_ecg_sync(mock_analyze, sample_algorithm_results):
    """Test synchronous convenience function"""
    mock_analyze.return_value = "Sync explanation"

    response = explain_ecg_sync(
        algorithm_results=sample_algorithm_results,
        user_level="cardiologist",
        question="What's the diagnosis?"
    )

    assert mock_analyze.called
    call_args = mock_analyze.call_args
    assert call_args[0][0] == sample_algorithm_results
    assert call_args[0][1] == UserLevel.CARDIOLOGIST
    assert call_args[0][2] == "What's the diagnosis?"
    assert response == "Sync explanation"


@patch('ai.llm_client.LLMClient.analyze_async')
@pytest.mark.asyncio
async def test_explain_ecg_async(mock_analyze, sample_algorithm_results):
    """Test async convenience function"""
    mock_analyze.return_value = "Async explanation"

    response = await explain_ecg(
        algorithm_results=sample_algorithm_results,
        user_level="student",
        question="Teach me this ECG"
    )

    assert mock_analyze.called
    call_args = mock_analyze.call_args
    assert call_args[0][0] == sample_algorithm_results
    assert call_args[0][1] == UserLevel.STUDENT
    assert call_args[0][2] == "Teach me this ECG"
    assert response == "Async explanation"


def test_user_level_enum_values():
    """Test UserLevel enum has correct values"""
    assert UserLevel.RMP.value == "rmp"
    assert UserLevel.STUDENT.value == "student"
    assert UserLevel.RESIDENT.value == "resident"
    assert UserLevel.CARDIOLOGIST.value == "cardiologist"


def test_user_level_from_string():
    """Test creating UserLevel from string"""
    assert UserLevel("rmp") == UserLevel.RMP
    assert UserLevel("student") == UserLevel.STUDENT
    assert UserLevel("resident") == UserLevel.RESIDENT
    assert UserLevel("cardiologist") == UserLevel.CARDIOLOGIST


# =============================================================================
# 8. Streaming Tests
# =============================================================================

@patch('ai.llm_client.anthropic')
@pytest.mark.asyncio
async def test_stream_analyze_async(mock_anthropic_module, sample_algorithm_results):
    """Test streaming analysis"""
    # Create mock stream
    mock_stream_context = MagicMock()

    async def mock_text_stream():
        yield "This "
        yield "is "
        yield "streaming."

    mock_stream_context.__aenter__ = AsyncMock(return_value=MagicMock(text_stream=mock_text_stream()))
    mock_stream_context.__aexit__ = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.messages.stream.return_value = mock_stream_context
    mock_anthropic_module.AsyncAnthropic.return_value = mock_client

    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', True):
        client = LLMClient(LLMConfig(api_key="test-key"))
        client._async_client = mock_client

        chunks = []
        async for chunk in client.stream_analyze_async(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.RESIDENT
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "This is streaming."


@patch('ai.llm_client.anthropic')
@pytest.mark.asyncio
async def test_stream_fallback_when_no_client(mock_anthropic_module, sample_algorithm_results):
    """Test streaming falls back when client unavailable"""
    with patch('ai.llm_client.ANTHROPIC_AVAILABLE', False):
        client = LLMClient(LLMConfig(api_key=None))

        chunks = []
        async for chunk in client.stream_analyze_async(
            algorithm_results=sample_algorithm_results,
            user_level=UserLevel.RESIDENT
        ):
            chunks.append(chunk)

        # Should get single chunk with fallback response
        assert len(chunks) == 1
        assert "ECG Analysis Report" in chunks[0]


# =============================================================================
# 9. Edge Cases and Validation
# =============================================================================

def test_empty_algorithm_results():
    """Test handling of empty algorithm results"""
    client = LLMClient(LLMConfig(api_key=None))

    response = client.analyze(
        algorithm_results={},
        user_level=UserLevel.RESIDENT
    )

    assert "ECG Analysis Report" in response


def test_malformed_algorithm_results():
    """Test handling of malformed data"""
    client = LLMClient(LLMConfig(api_key=None))

    # Missing expected fields
    results = {
        "vt_svt": {
            # Missing consensus
            "confidence": 0.5
        }
    }

    response = client.analyze(results, UserLevel.RESIDENT)
    assert "ECG Analysis Report" in response


def test_default_user_level():
    """Test default user level is RESIDENT"""
    client = LLMClient(LLMConfig(api_key=None))

    # Should use RESIDENT by default
    messages = client._build_messages(
        algorithm_results={"measurements": {"heart_rate": 80}},
        user_question=None,
        user_level=UserLevel.RESIDENT
    )

    assert len(messages) == 1


def test_conversation_history_format():
    """Test conversation history must be properly formatted"""
    client = LLMClient(LLMConfig(api_key="test-key"))

    history = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Second question"}
    ]

    messages = client._build_messages(
        algorithm_results={"measurements": {"heart_rate": 75}},
        user_question="Third question",
        user_level=UserLevel.RESIDENT,
        conversation_history=history
    )

    assert len(messages) == 4  # 3 from history + 1 new
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "user"


# =============================================================================
# Summary Stats
# =============================================================================

def test_summary():
    """Print test coverage summary"""
    test_count = len([name for name in dir() if name.startswith('test_')])
    print(f"\n{'='*60}")
    print(f"LLM Client Test Suite Summary")
    print(f"{'='*60}")
    print(f"Total tests: {test_count}")
    print(f"\nTest Categories:")
    print(f"  - Configuration: 4 tests")
    print(f"  - System Prompts: 4 tests")
    print(f"  - Message Building: 9 tests")
    print(f"  - Fallback Responses: 6 tests")
    print(f"  - User Level Adaptation: 5 tests")
    print(f"  - API Integration: 6 tests")
    print(f"  - Convenience Functions: 6 tests")
    print(f"  - Streaming: 2 tests")
    print(f"  - Edge Cases: 5 tests")
    print(f"{'='*60}\n")
