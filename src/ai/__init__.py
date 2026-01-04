"""
ECG Guru AI Module

Components:
- llm_config: LLM backend configuration and selection
- reasoning: Medical reasoning engine using RAG
"""

from .llm_config import (
    LLMConfig,
    LLMBackend,
    get_recommended_model,
    create_llm_client,
)

__all__ = [
    "LLMConfig",
    "LLMBackend",
    "get_recommended_model",
    "create_llm_client",
]
