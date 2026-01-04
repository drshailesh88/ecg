"""
ECG Guru AI Module

Components:
- llm_config: LLM backend configuration and selection
- reasoning: Medical reasoning engine using RAG

Architecture:
- Server-side: API runs LLM, clients access via web/mobile
- On-device: For offline capability (village RMPs)
"""

from .llm_config import (
    LLMConfig,
    LLMBackend,
    get_recommended_model,
    get_server_model,
    create_llm_client,
    detect_system_ram,
    DEPLOYMENT_TIERS,
)

__all__ = [
    "LLMConfig",
    "LLMBackend",
    "get_recommended_model",
    "get_server_model",
    "create_llm_client",
    "detect_system_ram",
    "DEPLOYMENT_TIERS",
]
