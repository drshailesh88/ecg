"""
ECG Guru API Server

The API server runs the LLM and heavy processing, allowing:
- Any device (phone, tablet, web) to use the service
- Powerful models that wouldn't fit on user devices
- Centralized knowledge base and updates
- Offline fallback with PWA/mobile app

Endpoints:
- /analyze: Analyze ECG image
- /chat: Chat about ECG findings
- /teach: Educational mode
- /algorithms: Run specific algorithms (Brugada, Basel, etc.)
"""

from .server import create_app, ECGAnalysisRequest, ECGAnalysisResponse
from .inference import InferenceEngine

__all__ = [
    "create_app",
    "ECGAnalysisRequest",
    "ECGAnalysisResponse",
    "InferenceEngine",
]
