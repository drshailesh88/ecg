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

from .inference import InferenceEngine

# Lazy import server components to avoid fastapi dependency for testing
def __getattr__(name):
    if name in ["create_app", "ECGAnalysisRequest", "ECGAnalysisResponse"]:
        from .server import create_app, ECGAnalysisRequest, ECGAnalysisResponse
        if name == "create_app":
            return create_app
        elif name == "ECGAnalysisRequest":
            return ECGAnalysisRequest
        elif name == "ECGAnalysisResponse":
            return ECGAnalysisResponse
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "create_app",
    "ECGAnalysisRequest",
    "ECGAnalysisResponse",
    "InferenceEngine",
]
