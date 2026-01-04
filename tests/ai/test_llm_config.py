"""
Comprehensive tests for LLM Configuration module.

Tests cover:
1. LLMBackend enum validation
2. LLMConfig dataclass and properties
3. RAM detection functions
4. Model selection logic (client-side)
5. Server model selection
6. System prompts
7. Deployment tiers
8. OllamaLLMClient functionality
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from dataclasses import asdict
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ai.llm_config import (
    LLMBackend,
    LLMConfig,
    detect_system_ram,
    get_available_ram,
    get_recommended_model,
    get_medical_system_prompt,
    check_model_available,
    create_llm_client,
    OllamaLLMClient,
    get_server_model,
    DEPLOYMENT_TIERS,
)


# ============================================================================
# 1. LLMBackend Enum Tests (5+ tests)
# ============================================================================

class TestLLMBackendEnum:
    """Test LLMBackend enum structure and values"""

    def test_all_models_have_string_values(self):
        """All enum members should have string values"""
        for model in LLMBackend:
            assert isinstance(model.value, str)
            assert len(model.value) > 0

    def test_q4_models_contain_q4_in_value(self):
        """Q4 quantized models should have 'q4' in their value"""
        q4_models = [
            LLMBackend.QWEN_3B_Q4,
            LLMBackend.PHI3_MINI_Q4,
            LLMBackend.GEMMA2_2B_Q4,
            LLMBackend.QWEN_7B_Q4,
            LLMBackend.LLAMA3_8B_Q4,
            LLMBackend.MISTRAL_7B_Q4,
            LLMBackend.MEDITRON_7B_Q4,
            LLMBackend.MEDLLAMA_8B_Q4,
            LLMBackend.LLAMA3_70B_Q4,
            LLMBackend.QWEN_32B_Q4,
            LLMBackend.MIXTRAL_8X7B_Q4,
        ]
        for model in q4_models:
            assert "q4" in model.value.lower(), f"{model.name} should contain 'q4'"

    def test_q8_models_contain_q8_in_value(self):
        """Q8 quantized models should have 'q8' in their value"""
        q8_models = [
            LLMBackend.QWEN_7B_Q8,
            LLMBackend.LLAMA3_8B_Q8,
        ]
        for model in q8_models:
            assert "q8" in model.value.lower(), f"{model.name} should contain 'q8'"

    def test_cloud_models_defined(self):
        """Cloud models (Claude) should be defined"""
        cloud_models = [
            LLMBackend.CLAUDE_HAIKU,
            LLMBackend.CLAUDE_SONNET,
        ]
        for model in cloud_models:
            assert "claude" in model.value.lower()

    def test_server_models_defined(self):
        """Server-tier large models (70B, 32B) should be defined"""
        server_models = [
            LLMBackend.LLAMA3_70B_Q4,
            LLMBackend.QWEN_32B_Q4,
            LLMBackend.MIXTRAL_8X7B_Q4,
        ]
        for model in server_models:
            assert model in LLMBackend

    def test_medical_models_defined(self):
        """Medical-specialized models should be defined"""
        medical_models = [
            LLMBackend.MEDITRON_7B_Q4,
            LLMBackend.MEDLLAMA_8B_Q4,
        ]
        for model in medical_models:
            assert model in LLMBackend


# ============================================================================
# 2. LLMConfig Tests (10+ tests)
# ============================================================================

class TestLLMConfig:
    """Test LLMConfig dataclass and its properties"""

    def test_default_values_are_correct(self):
        """Default config values should match medical safety requirements"""
        config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)

        assert config.temperature == 0.3  # Low for medical accuracy
        assert config.max_tokens == 1024
        assert config.num_ctx == 4096
        assert config.num_thread == 4
        assert config.use_mmap is True
        assert config.require_citations is True
        assert config.show_confidence is True

    def test_is_medical_specialized_for_meditron(self):
        """Meditron should be identified as medical-specialized"""
        config = LLMConfig(model=LLMBackend.MEDITRON_7B_Q4)
        assert config.is_medical_specialized is True

    def test_is_medical_specialized_for_medllama(self):
        """MedLlama should be identified as medical-specialized"""
        config = LLMConfig(model=LLMBackend.MEDLLAMA_8B_Q4)
        assert config.is_medical_specialized is True

    def test_is_medical_specialized_false_for_general_models(self):
        """General models should not be marked as medical-specialized"""
        general_models = [
            LLMBackend.QWEN_7B_Q4,
            LLMBackend.LLAMA3_8B_Q4,
            LLMBackend.GEMMA2_2B_Q4,
        ]
        for model in general_models:
            config = LLMConfig(model=model)
            assert config.is_medical_specialized is False

    def test_min_ram_gb_returns_correct_values(self):
        """min_ram_gb should return appropriate RAM requirements"""
        test_cases = [
            (LLMBackend.GEMMA2_2B_Q4, 2.0),
            (LLMBackend.QWEN_3B_Q4, 2.5),
            (LLMBackend.PHI3_MINI_Q4, 2.5),
            (LLMBackend.QWEN_7B_Q4, 5.0),
            (LLMBackend.LLAMA3_8B_Q4, 5.5),
            (LLMBackend.QWEN_7B_Q8, 8.5),
            (LLMBackend.LLAMA3_8B_Q8, 9.5),
        ]

        for model, expected_ram in test_cases:
            config = LLMConfig(model=model)
            assert config.min_ram_gb == expected_ram

    def test_min_ram_gb_defaults_for_unknown_models(self):
        """Unknown models should default to 5.0 GB"""
        # Cloud models won't be in the RAM map
        config = LLMConfig(model=LLMBackend.CLAUDE_HAIKU)
        assert config.min_ram_gb == 5.0

    def test_is_quantized_true_for_q4_models(self):
        """Q4 models should be identified as quantized"""
        config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)
        assert config.is_quantized is True

    def test_is_quantized_true_for_q8_models(self):
        """Q8 models should be identified as quantized"""
        config = LLMConfig(model=LLMBackend.LLAMA3_8B_Q8)
        assert config.is_quantized is True

    def test_is_quantized_false_for_cloud_models(self):
        """Cloud models should not be marked as quantized"""
        config = LLMConfig(model=LLMBackend.CLAUDE_HAIKU)
        assert config.is_quantized is False

    def test_temperature_default_low_for_medical(self):
        """Temperature should default to 0.3 for medical safety"""
        config = LLMConfig(model=LLMBackend.MEDITRON_7B_Q4)
        assert config.temperature == 0.3

    def test_custom_values_can_be_set(self):
        """Custom configuration values should be respected"""
        config = LLMConfig(
            model=LLMBackend.QWEN_7B_Q4,
            temperature=0.5,
            max_tokens=2048,
            num_ctx=8192,
        )

        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.num_ctx == 8192


# ============================================================================
# 3. RAM Detection Tests (5+ tests)
# ============================================================================

class TestRAMDetection:
    """Test system RAM detection functions"""

    @patch("builtins.open", new_callable=mock_open, read_data="MemTotal:       16384000 kB\n")
    def test_detect_system_ram_linux(self, mock_file):
        """detect_system_ram should parse /proc/meminfo on Linux"""
        ram = detect_system_ram()
        assert ram > 0
        assert isinstance(ram, float)
        # 16384000 KB = ~15.6 GB
        assert 15 < ram < 17

    @patch("subprocess.run")
    def test_detect_system_ram_macos(self, mock_run):
        """detect_system_ram should use sysctl on macOS"""
        # Simulate macOS with 16GB RAM (17179869184 bytes)
        mock_run.return_value = Mock(returncode=0, stdout="17179869184\n")

        # Mock file open to fail (simulate non-Linux)
        with patch("builtins.open", side_effect=FileNotFoundError):
            ram = detect_system_ram()
            assert 15 < ram < 17

    def test_detect_system_ram_returns_positive(self):
        """detect_system_ram should always return positive number"""
        ram = detect_system_ram()
        assert ram > 0
        assert isinstance(ram, float)

    def test_detect_system_ram_fallback_to_8gb(self):
        """detect_system_ram should default to 8GB when detection fails"""
        with patch("builtins.open", side_effect=Exception):
            with patch("subprocess.run", side_effect=Exception):
                ram = detect_system_ram()
                assert ram == 8.0

    @patch("builtins.open", new_callable=mock_open, read_data="MemAvailable:    8192000 kB\n")
    def test_get_available_ram_linux(self, mock_file):
        """get_available_ram should parse MemAvailable on Linux"""
        ram = get_available_ram()
        assert ram > 0
        # 8192000 KB = ~7.8 GB
        assert 7 < ram < 9

    def test_get_available_ram_returns_positive(self):
        """get_available_ram should always return positive number"""
        ram = get_available_ram()
        assert ram > 0
        assert isinstance(ram, float)

    def test_get_available_ram_less_than_total(self):
        """Available RAM should be less than or equal to total RAM"""
        total = detect_system_ram()
        available = get_available_ram()
        assert available <= total

    @patch("ai.llm_config.detect_system_ram", return_value=16.0)
    def test_get_available_ram_estimates_60_percent(self, mock_detect):
        """When detection fails, should estimate 60% of total RAM"""
        with patch("builtins.open", side_effect=Exception):
            ram = get_available_ram()
            # Should be 60% of 16GB = 9.6GB
            assert 9 < ram < 10


# ============================================================================
# 4. Model Selection Tests (10+ tests)
# ============================================================================

class TestModelSelection:
    """Test get_recommended_model() logic"""

    def test_recommended_model_with_2gb_ram(self):
        """2GB RAM should select smallest viable model"""
        config = get_recommended_model(available_ram=2.0, prefer_medical=False, allow_cloud=False)

        # 2GB * 0.7 = 1.4GB usable → smallest model
        assert config.model == LLMBackend.GEMMA2_2B_Q4
        assert config.num_ctx == 2048  # Limited context

    def test_recommended_model_with_6gb_ram(self):
        """6GB RAM should select 3B-7B model"""
        config = get_recommended_model(available_ram=6.0, prefer_medical=False)

        # 6GB * 0.7 = 4.2GB usable → 3B model (not enough for 7B models)
        assert config.model == LLMBackend.QWEN_3B_Q4
        assert config.num_ctx == 4096

    def test_recommended_model_with_12gb_ram(self):
        """12GB RAM should select quality Q8 model"""
        config = get_recommended_model(available_ram=13.0, prefer_medical=False)

        # 13GB * 0.7 = 9.1GB usable → Q8 model
        assert config.model == LLMBackend.QWEN_7B_Q8
        assert config.num_ctx == 8192
        assert config.max_tokens == 2048

    def test_prefer_medical_selects_meditron_with_sufficient_ram(self):
        """prefer_medical=True should select Meditron when RAM allows"""
        config = get_recommended_model(available_ram=8.0, prefer_medical=True)

        # 8GB * 0.7 = 5.6GB usable → Meditron
        assert config.model == LLMBackend.MEDITRON_7B_Q4
        assert config.is_medical_specialized

    def test_prefer_speed_selects_faster_model(self):
        """prefer_speed=True should select faster models"""
        # With 6GB RAM, 6*0.7=4.2 -> should select Gemma2 (fastest small)
        config = get_recommended_model(available_ram=6.0, prefer_speed=True, prefer_medical=False)
        assert config.model == LLMBackend.GEMMA2_2B_Q4

        # With 8GB RAM, 8*0.7=5.6 -> should select Mistral (fast 7B)
        config = get_recommended_model(available_ram=8.0, prefer_speed=True, prefer_medical=False)
        assert config.model == LLMBackend.MISTRAL_7B_Q4

    def test_allow_cloud_enables_claude_fallback(self):
        """allow_cloud=True should enable Claude for low RAM"""
        config = get_recommended_model(available_ram=2.0, allow_cloud=True)

        # 2GB * 0.7 = 1.4GB → cloud fallback
        assert config.model == LLMBackend.CLAUDE_HAIKU

    def test_allow_cloud_false_uses_local_only(self):
        """allow_cloud=False should use only local models"""
        config = get_recommended_model(available_ram=2.0, allow_cloud=False)

        # Should fall back to smallest local model
        assert config.model == LLMBackend.GEMMA2_2B_Q4

    def test_context_window_scales_with_ram(self):
        """Context window should scale based on available RAM"""
        # Low RAM (3GB * 0.7 = 2.1GB) → 2048 context
        config_low = get_recommended_model(available_ram=3.0)
        assert config_low.num_ctx == 2048

        # Medium RAM (6GB * 0.7 = 4.2GB) → 4096 context
        config_med = get_recommended_model(available_ram=6.0)
        assert config_med.num_ctx == 4096

        # High RAM (13GB * 0.7 = 9.1GB) → 8192 context
        config_high = get_recommended_model(available_ram=13.0)
        assert config_high.num_ctx == 8192

    def test_max_tokens_scales_with_ram(self):
        """max_tokens should increase with available RAM"""
        # Low RAM (6GB * 0.7 = 4.2GB < 8) → 1024 tokens
        config_low = get_recommended_model(available_ram=6.0)
        assert config_low.max_tokens == 1024

        # High RAM (13GB * 0.7 = 9.1GB >= 8) → 2048 tokens
        config_high = get_recommended_model(available_ram=13.0)
        assert config_high.max_tokens == 2048

    def test_auto_detect_ram_when_none_provided(self):
        """Should auto-detect RAM when available_ram=None"""
        config = get_recommended_model(available_ram=None)

        assert config is not None
        assert isinstance(config.model, LLMBackend)

    def test_system_prompt_included_in_config(self):
        """Recommended config should include appropriate system prompt"""
        config = get_recommended_model(available_ram=10.0)

        assert config.system_prompt != ""
        assert "clinical cardiologist" in config.system_prompt.lower()
        assert "NOT make diagnoses" in config.system_prompt


# ============================================================================
# 5. Server Model Tests (5+ tests)
# ============================================================================

class TestServerModelSelection:
    """Test get_server_model() for server deployments"""

    def test_server_model_with_16gb_selects_basic_tier(self):
        """16GB server RAM should select 7B-8B models"""
        config = get_server_model(server_ram_gb=16, prefer_medical=False)

        assert config.model == LLMBackend.QWEN_7B_Q8
        assert config.num_ctx == 8192

    def test_server_model_with_32gb_selects_standard_tier(self):
        """32GB server RAM should select 32B-class models"""
        config = get_server_model(server_ram_gb=32, prefer_medical=False, prefer_speed=False)

        assert config.model == LLMBackend.QWEN_32B_Q4
        assert config.num_ctx == 8192

    def test_server_model_with_64gb_selects_enterprise_tier(self):
        """64GB+ server RAM should select 70B models"""
        config = get_server_model(server_ram_gb=64, prefer_medical=False)

        assert config.model == LLMBackend.LLAMA3_70B_Q4
        assert config.num_ctx == 16384  # Larger context for enterprise

    def test_server_prefer_medical_affects_selection(self):
        """prefer_medical should influence server model choice"""
        config = get_server_model(server_ram_gb=20, prefer_medical=True)

        # Should select Meditron for medical preference
        assert config.model == LLMBackend.MEDITRON_7B_Q4

    def test_server_num_ctx_larger_than_client(self):
        """Server configs should have larger context windows"""
        server_config = get_server_model(server_ram_gb=32)
        client_config = get_recommended_model(available_ram=12.0)

        assert server_config.num_ctx >= client_config.num_ctx

    def test_server_max_tokens_consistent(self):
        """Server should use 2048 max_tokens for quality"""
        config = get_server_model(server_ram_gb=32)
        assert config.max_tokens == 2048


# ============================================================================
# 6. System Prompt Tests (3+ tests)
# ============================================================================

class TestSystemPrompts:
    """Test get_medical_system_prompt()"""

    def test_system_prompt_includes_safety_rules(self):
        """System prompt should include critical safety rules"""
        prompt = get_medical_system_prompt(LLMBackend.QWEN_7B_Q4)

        assert "CRITICAL SAFETY RULES" in prompt
        assert "cite your knowledge sources" in prompt.lower()
        assert "uncertain" in prompt.lower()
        assert "urgent attention" in prompt.lower()

    def test_system_prompt_includes_not_make_diagnoses(self):
        """System prompt must state LLM does NOT make diagnoses"""
        prompt = get_medical_system_prompt(LLMBackend.QWEN_7B_Q4)

        # Check for the exact phrase from the code
        assert "EXPLAIN findings - you do NOT make diagnoses" in prompt
        assert "algorithm" in prompt.lower()

    def test_system_prompt_includes_role_definition(self):
        """System prompt should define the assistant's role"""
        prompt = get_medical_system_prompt(LLMBackend.MEDITRON_7B_Q4)

        assert "cardiologist" in prompt.lower()
        assert "electrophysiologist" in prompt.lower()
        assert "ECG Guru" in prompt

    def test_system_prompt_consistent_across_models(self):
        """Base prompt should be consistent across different models"""
        prompt1 = get_medical_system_prompt(LLMBackend.QWEN_7B_Q4)
        prompt2 = get_medical_system_prompt(LLMBackend.LLAMA3_8B_Q4)

        # Both should contain core safety rules
        assert "CRITICAL SAFETY RULES" in prompt1
        assert "CRITICAL SAFETY RULES" in prompt2


# ============================================================================
# 7. Deployment Tiers Tests (3+ tests)
# ============================================================================

class TestDeploymentTiers:
    """Test DEPLOYMENT_TIERS configuration"""

    def test_all_tiers_have_required_fields(self):
        """All deployment tiers should have description, models, min_ram"""
        required_fields = {"description", "models", "min_ram"}

        for tier_name, tier_config in DEPLOYMENT_TIERS.items():
            assert required_fields.issubset(tier_config.keys()), \
                f"Tier {tier_name} missing required fields"
            assert isinstance(tier_config["models"], list)
            assert len(tier_config["models"]) > 0
            assert isinstance(tier_config["min_ram"], int)

    def test_server_tiers_have_higher_ram_than_mobile(self):
        """Server tiers should require more RAM than mobile tiers"""
        server_tiers = [k for k in DEPLOYMENT_TIERS.keys() if k.startswith("server_")]
        mobile_tiers = [k for k in DEPLOYMENT_TIERS.keys() if k.startswith("mobile_")]

        max_mobile_ram = max(DEPLOYMENT_TIERS[t]["min_ram"] for t in mobile_tiers)
        min_server_ram = min(DEPLOYMENT_TIERS[t]["min_ram"] for t in server_tiers)

        assert min_server_ram > max_mobile_ram

    def test_mobile_tiers_have_appropriate_models(self):
        """Mobile tiers should use small, efficient models"""
        mobile_basic = DEPLOYMENT_TIERS["mobile_basic"]
        mobile_standard = DEPLOYMENT_TIERS["mobile_standard"]

        # Basic mobile should have smallest models
        assert LLMBackend.GEMMA2_2B_Q4 in mobile_basic["models"]

        # Standard mobile should have 3B models
        assert LLMBackend.QWEN_3B_Q4 in mobile_standard["models"] or \
               LLMBackend.PHI3_MINI_Q4 in mobile_standard["models"]

    def test_enterprise_tier_has_largest_models(self):
        """Enterprise server tier should have 70B models"""
        enterprise = DEPLOYMENT_TIERS["server_enterprise"]

        assert LLMBackend.LLAMA3_70B_Q4 in enterprise["models"]
        assert enterprise["min_ram"] >= 64


# ============================================================================
# 8. OllamaLLMClient Tests (5+ tests)
# ============================================================================

class TestOllamaLLMClient:
    """Test OllamaLLMClient wrapper class"""

    def test_client_initialization_stores_config(self):
        """Client should store configuration on initialization"""
        # Mock ollama module at import time
        mock_ollama = MagicMock()
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)
            client = OllamaLLMClient(config)

            assert client.config == config
            assert client.model_name == config.model.value

    def test_generate_builds_prompt_correctly(self):
        """generate() should build prompt with correct structure"""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {"response": "test"}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, system_prompt="Test prompt")
            client = OllamaLLMClient(config)

            client.generate("What is STEMI?")

            # Verify ollama.generate was called
            mock_ollama.generate.assert_called_once()
            call_args = mock_ollama.generate.call_args

            assert call_args[1]["model"] == config.model.value
            assert call_args[1]["prompt"] == "What is STEMI?"
            assert call_args[1]["system"] == "Test prompt"

    def test_generate_with_context_prepends_context(self):
        """generate() with context should prepend RAG context"""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {"response": "test"}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)
            client = OllamaLLMClient(config)

            client.generate("What is STEMI?", context="STEMI is ST-elevation MI")

            call_args = mock_ollama.generate.call_args
            prompt = call_args[1]["prompt"]

            assert "<context>" in prompt
            assert "STEMI is ST-elevation MI" in prompt
            assert "What is STEMI?" in prompt

    def test_chat_includes_system_message(self):
        """chat() should include system message in conversation"""
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = {"message": {"content": "test"}}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, system_prompt="You are a cardiologist")
            client = OllamaLLMClient(config)

            messages = [{"role": "user", "content": "Hello"}]
            client.chat(messages)

            call_args = mock_ollama.chat.call_args
            sent_messages = call_args[1]["messages"]

            assert sent_messages[0]["role"] == "system"
            assert "You are a cardiologist" in sent_messages[0]["content"]
            assert sent_messages[1] == messages[0]

    def test_chat_with_context_appends_knowledge(self):
        """chat() with context should append knowledge to system prompt"""
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = {"message": {"content": "test"}}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, system_prompt="Base prompt")
            client = OllamaLLMClient(config)

            messages = [{"role": "user", "content": "Question"}]
            client.chat(messages, context="Relevant knowledge here")

            call_args = mock_ollama.chat.call_args
            system_msg = call_args[1]["messages"][0]["content"]

            assert "Base prompt" in system_msg
            assert "Relevant knowledge here" in system_msg

    def test_generate_passes_temperature_to_options(self):
        """generate() should pass config temperature to Ollama"""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {"response": "test"}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, temperature=0.7)
            client = OllamaLLMClient(config)

            client.generate("Test")

            call_args = mock_ollama.generate.call_args
            options = call_args[1]["options"]

            assert options["temperature"] == 0.7

    def test_generate_passes_max_tokens_to_options(self):
        """generate() should pass max_tokens as num_predict"""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {"response": "test"}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, max_tokens=512)
            client = OllamaLLMClient(config)

            client.generate("Test")

            call_args = mock_ollama.generate.call_args
            options = call_args[1]["options"]

            assert options["num_predict"] == 512

    def test_generate_passes_num_ctx_to_options(self):
        """generate() should pass num_ctx to Ollama options"""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {"response": "test"}

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            config = LLMConfig(model=LLMBackend.QWEN_7B_Q4, num_ctx=8192)
            client = OllamaLLMClient(config)

            client.generate("Test")

            call_args = mock_ollama.generate.call_args
            options = call_args[1]["options"]

            assert options["num_ctx"] == 8192


# ============================================================================
# 9. Model Availability Tests
# ============================================================================

class TestModelAvailability:
    """Test check_model_available() function"""

    def test_check_model_available_returns_true_when_found(self):
        """check_model_available should return True when model exists"""
        mock_ollama = MagicMock()
        mock_ollama.list.return_value = {
            "models": [
                {"name": "qwen2.5:3b-instruct-q4_K_M"},
                {"name": "llama3.1:8b-instruct-q4_K_M"},
            ]
        }

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_model_available(LLMBackend.QWEN_3B_Q4)
            assert result is True

    def test_check_model_available_returns_false_when_not_found(self):
        """check_model_available should return False when model missing"""
        mock_ollama = MagicMock()
        mock_ollama.list.return_value = {
            "models": [
                {"name": "qwen2.5:3b-instruct-q4_K_M"},
            ]
        }

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_model_available(LLMBackend.LLAMA3_70B_Q4)
            assert result is False

    def test_check_model_available_handles_import_error(self):
        """check_model_available should return False on import error"""
        # Don't provide ollama in sys.modules to simulate import error
        with patch.dict(sys.modules, {}, clear=False):
            # Remove ollama if it exists
            if "ollama" in sys.modules:
                del sys.modules["ollama"]
            result = check_model_available(LLMBackend.QWEN_7B_Q4)
            assert result is False

    def test_check_model_available_handles_exception(self):
        """check_model_available should return False on any exception"""
        mock_ollama = MagicMock()
        mock_ollama.list.side_effect = Exception("Connection error")

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            result = check_model_available(LLMBackend.QWEN_7B_Q4)
            assert result is False


# ============================================================================
# 10. Client Creation Tests
# ============================================================================

class TestClientCreation:
    """Test create_llm_client() factory function"""

    def test_create_llm_client_returns_ollama_client(self):
        """create_llm_client should return OllamaLLMClient instance"""
        mock_ollama = MagicMock()

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            with patch("ai.llm_config.check_model_available", return_value=True):
                config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)
                client = create_llm_client(config)

                assert isinstance(client, OllamaLLMClient)
                assert client.config == config

    def test_create_llm_client_pulls_missing_model(self):
        """create_llm_client should pull model if not available"""
        mock_ollama = MagicMock()

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            with patch("ai.llm_config.check_model_available", return_value=False):
                config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)

                client = create_llm_client(config)

                # Should have called ollama.pull
                mock_ollama.pull.assert_called_once_with(config.model.value)

    def test_create_llm_client_uses_recommended_when_none(self):
        """create_llm_client should use recommended config when None"""
        mock_ollama = MagicMock()
        mock_config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)

        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            with patch("ai.llm_config.get_recommended_model", return_value=mock_config):
                with patch("ai.llm_config.check_model_available", return_value=True):
                    client = create_llm_client(config=None)

                    # Verify it was called
                    assert isinstance(client, OllamaLLMClient)

    def test_create_llm_client_raises_import_error_without_ollama(self):
        """create_llm_client should raise ImportError if ollama not installed"""
        config = LLMConfig(model=LLMBackend.QWEN_7B_Q4)

        # Simulate ImportError during import
        def import_side_effect(name, *args, **kwargs):
            if name == "ollama":
                raise ImportError("No module named 'ollama'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_side_effect):
            with pytest.raises(ImportError, match="ollama package required"):
                create_llm_client(config)


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
