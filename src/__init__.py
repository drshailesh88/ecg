"""
ECG Guru - AI-Powered ECG Analysis Platform

Modules:
- knowledge: Knowledge base extraction, embedding, and advanced RAG
- ai: LLM configuration with tiered medical model support
- core: ECG processing and algorithm engine (TODO)
- ui: Flet user interface (TODO)
- integrations: EMR, Dora, and other integrations (TODO)

Architecture:
- Layer 1: Image Processing (specialized CNN, not LLM)
- Layer 2: Diagnosis (programmatic algorithms - Brugada, Basel, etc.)
- Layer 3: Reasoning (LLM + RAG for explanation and teaching)

The LLM NEVER makes diagnoses - validated algorithms do.
The LLM provides explanations, teaching, and conversational interface.
"""

__version__ = "0.1.0"
