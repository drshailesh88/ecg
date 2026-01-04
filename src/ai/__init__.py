"""
ECG Guru AI Module

Components:
- llm_config: LLM backend configuration and selection
- llm_client: Claude API client for expert explanations
- reasoning: Medical reasoning engine using RAG

Architecture:
- Primary: Claude API for best quality explanations
- Fallback: Templated responses from algorithms
"""

from .llm_config import (
    LLMConfig as OllamaLLMConfig,
    LLMBackend,
    get_recommended_model,
    get_server_model,
    create_llm_client,
    detect_system_ram,
    DEPLOYMENT_TIERS,
)

from .llm_client import (
    LLMClient,
    LLMConfig,
    UserLevel,
    get_client,
    explain_ecg,
    explain_ecg_sync,
    EXPERT_EP_SYSTEM_PROMPT,
)

__all__ = [
    # Legacy Ollama config
    "OllamaLLMConfig",
    "LLMBackend",
    "get_recommended_model",
    "get_server_model",
    "create_llm_client",
    "detect_system_ram",
    "DEPLOYMENT_TIERS",
    # New Claude client
    "LLMClient",
    "LLMConfig",
    "UserLevel",
    "get_client",
    "explain_ecg",
    "explain_ecg_sync",
    "EXPERT_EP_SYSTEM_PROMPT",
]
