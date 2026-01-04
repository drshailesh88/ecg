"""
ECG Guru FastAPI Server

Server-side architecture for mobile/web clients.
Since LLM runs on server, we can use powerful models regardless of client device.

Deployment options:
1. Self-hosted: Run on your own server/VM
2. Cloud: Deploy to Railway, Render, Fly.io
3. Hospital: On-premises for data privacy

The server handles:
- ECG image processing
- Algorithm execution (Brugada, Basel, etc.)
- LLM inference for explanations
- RAG for knowledge retrieval
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import base64
import io
from datetime import datetime
import asyncio


# ============================================================================
# Request/Response Models
# ============================================================================

class UserLevel(str, Enum):
    """User expertise level for appropriate explanations"""
    RMP = "rmp"                    # Village practitioner - simple verdicts
    STUDENT = "student"            # MBBS student - educational
    RESIDENT = "resident"          # MD/DM resident - detailed analysis
    CARDIOLOGIST = "cardiologist"  # Expert - full technical detail


class ECGAnalysisRequest(BaseModel):
    """Request for ECG analysis"""
    image_base64: Optional[str] = Field(None, description="Base64 encoded ECG image")
    image_url: Optional[str] = Field(None, description="URL to ECG image")
    user_level: UserLevel = Field(default=UserLevel.STUDENT)
    include_teaching: bool = Field(default=True, description="Include educational content")
    run_algorithms: List[str] = Field(
        default=["all"],
        description="Algorithms to run: brugada, basel, vereckei, pava, smart_wpw, or 'all'"
    )
    clinical_context: Optional[str] = Field(
        None,
        description="Clinical context (symptoms, history) for better analysis"
    )


class AlgorithmResult(BaseModel):
    """Result from a specific algorithm"""
    name: str
    conclusion: str
    confidence: float  # 0-1
    steps: List[Dict[str, Any]]  # Step-by-step execution
    supports_vt: Optional[bool] = None
    supports_svt: Optional[bool] = None


class ECGMeasurements(BaseModel):
    """Extracted ECG measurements"""
    heart_rate: Optional[int] = None
    pr_interval_ms: Optional[int] = None
    qrs_duration_ms: Optional[int] = None
    qt_interval_ms: Optional[int] = None
    qtc_ms: Optional[int] = None
    axis_degrees: Optional[int] = None
    rhythm: Optional[str] = None


class Finding(BaseModel):
    """A single ECG finding"""
    category: str  # "rhythm", "morphology", "ischemia", "conduction", etc.
    finding: str
    severity: str  # "normal", "abnormal", "critical"
    confidence: float
    explanation: str
    teaching_point: Optional[str] = None


class ECGAnalysisResponse(BaseModel):
    """Complete ECG analysis response"""
    # Metadata
    analysis_id: str
    timestamp: datetime
    processing_time_ms: int

    # Core analysis
    summary: str  # One-line summary appropriate for user level
    measurements: ECGMeasurements
    findings: List[Finding]
    algorithm_results: List[AlgorithmResult]

    # Interpretation
    primary_diagnosis: str
    differential_diagnoses: List[str]
    confidence: float

    # Clinical guidance
    is_urgent: bool
    urgency_reason: Optional[str] = None
    recommended_actions: List[str]

    # Educational (if requested)
    teaching_content: Optional[str] = None
    similar_cases: Optional[List[Dict[str, Any]]] = None

    # Sources
    knowledge_sources: List[str]


class ChatRequest(BaseModel):
    """Request for chat about ECG"""
    analysis_id: Optional[str] = Field(None, description="Previous analysis to reference")
    message: str
    user_level: UserLevel = Field(default=UserLevel.STUDENT)
    conversation_history: List[Dict[str, str]] = Field(default=[])


class ChatResponse(BaseModel):
    """Response from ECG chat"""
    response: str
    sources: List[str]
    suggested_questions: List[str]


# ============================================================================
# FastAPI Application
# ============================================================================

def create_app(
    llm_model: str = "qwen2.5:7b",
    enable_cors: bool = True,
    allowed_origins: List[str] = None,
) -> FastAPI:
    """
    Create the ECG Guru FastAPI application.

    Args:
        llm_model: Ollama model to use for inference
        enable_cors: Enable CORS for web clients
        allowed_origins: List of allowed origins for CORS

    Returns:
        FastAPI application
    """

    app = FastAPI(
        title="ECG Guru API",
        description="AI-powered ECG analysis and teaching platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS for web/mobile clients
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Initialize inference engine (lazy load)
    inference_engine = None

    def get_engine():
        nonlocal inference_engine
        if inference_engine is None:
            from .inference import InferenceEngine
            inference_engine = InferenceEngine(llm_model=llm_model)
        return inference_engine

    # ========================================================================
    # Health & Info
    # ========================================================================

    @app.get("/")
    async def root():
        return {
            "service": "ECG Guru API",
            "version": "0.1.0",
            "status": "healthy",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy", "llm_model": llm_model}

    # ========================================================================
    # ECG Analysis
    # ========================================================================

    @app.post("/analyze", response_model=ECGAnalysisResponse)
    async def analyze_ecg(request: ECGAnalysisRequest):
        """
        Analyze an ECG image.

        Accepts base64-encoded image or URL.
        Returns comprehensive analysis with algorithm results.
        """
        engine = get_engine()

        if not request.image_base64 and not request.image_url:
            raise HTTPException(400, "Must provide image_base64 or image_url")

        try:
            result = await engine.analyze(
                image_base64=request.image_base64,
                image_url=request.image_url,
                user_level=request.user_level,
                include_teaching=request.include_teaching,
                algorithms=request.run_algorithms,
                clinical_context=request.clinical_context,
            )
            return result
        except Exception as e:
            raise HTTPException(500, f"Analysis failed: {str(e)}")

    @app.post("/analyze/upload")
    async def analyze_ecg_upload(
        file: UploadFile = File(...),
        user_level: UserLevel = UserLevel.STUDENT,
        include_teaching: bool = True,
    ):
        """
        Analyze an uploaded ECG image file.

        Accepts JPEG, PNG, or PDF files.
        """
        engine = get_engine()

        # Read and encode file
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')

        try:
            result = await engine.analyze(
                image_base64=image_base64,
                user_level=user_level,
                include_teaching=include_teaching,
            )
            return result
        except Exception as e:
            raise HTTPException(500, f"Analysis failed: {str(e)}")

    # ========================================================================
    # Chat Interface
    # ========================================================================

    @app.post("/chat", response_model=ChatResponse)
    async def chat_about_ecg(request: ChatRequest):
        """
        Chat about an ECG or cardiology topic.

        Can reference a previous analysis or be a general question.
        """
        engine = get_engine()

        try:
            response = await engine.chat(
                message=request.message,
                analysis_id=request.analysis_id,
                user_level=request.user_level,
                history=request.conversation_history,
            )
            return response
        except Exception as e:
            raise HTTPException(500, f"Chat failed: {str(e)}")

    @app.post("/chat/stream")
    async def chat_stream(request: ChatRequest):
        """
        Streaming chat response for real-time display.
        """
        engine = get_engine()

        async def generate():
            async for chunk in engine.chat_stream(
                message=request.message,
                analysis_id=request.analysis_id,
                user_level=request.user_level,
                history=request.conversation_history,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    # ========================================================================
    # Algorithms
    # ========================================================================

    @app.get("/algorithms")
    async def list_algorithms():
        """List available ECG analysis algorithms"""
        return {
            "vt_vs_svt": [
                {"name": "brugada", "description": "Brugada 4-step algorithm", "accuracy": "89%"},
                {"name": "vereckei", "description": "Vereckei aVR algorithm", "accuracy": "69-94%"},
                {"name": "basel", "description": "Basel 3-criteria algorithm", "accuracy": "91-93%"},
                {"name": "pava", "description": "Pava lead II R-peak time", "accuracy": "85%+"},
            ],
            "pathway_localization": [
                {"name": "smart_wpw", "description": "SMART-WPW algorithm", "accuracy": "97%"},
                {"name": "easy_wpw", "description": "EASY-WPW algorithm", "accuracy": "94%"},
                {"name": "arruda", "description": "Arruda stepwise algorithm", "accuracy": "53-75%"},
            ],
            "stemi": [
                {"name": "stemi_localization", "description": "STEMI territory localization"},
                {"name": "culprit_vessel", "description": "RCA vs LCx differentiation", "accuracy": "86%"},
            ],
            "svt_classification": [
                {"name": "rp_interval", "description": "RP interval analysis for SVT subtype"},
            ],
        }

    @app.post("/algorithms/{algorithm_name}")
    async def run_algorithm(
        algorithm_name: str,
        image_base64: str = None,
        measurements: ECGMeasurements = None,
    ):
        """
        Run a specific algorithm on ECG data.

        Can provide either image or pre-extracted measurements.
        """
        engine = get_engine()

        try:
            result = await engine.run_algorithm(
                algorithm_name=algorithm_name,
                image_base64=image_base64,
                measurements=measurements,
            )
            return result
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, f"Algorithm failed: {str(e)}")

    # ========================================================================
    # Teaching Mode
    # ========================================================================

    @app.get("/teach/cases")
    async def get_teaching_cases(
        diagnosis: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 10,
    ):
        """Get teaching cases for learning"""
        engine = get_engine()
        return await engine.get_teaching_cases(
            diagnosis=diagnosis,
            difficulty=difficulty,
            limit=limit,
        )

    @app.get("/teach/topics")
    async def get_teaching_topics():
        """Get available teaching topics"""
        return {
            "basic": [
                "P wave identification",
                "PR interval measurement",
                "QRS complex analysis",
                "ST segment evaluation",
                "T wave assessment",
                "Axis determination",
            ],
            "intermediate": [
                "Chamber enlargement",
                "Bundle branch blocks",
                "Ischemic changes",
                "Electrolyte abnormalities",
            ],
            "advanced": [
                "VT vs SVT differentiation",
                "Accessory pathway localization",
                "Brugada pattern",
                "ARVC criteria",
            ],
        }

    @app.post("/teach/explain")
    async def explain_topic(
        topic: str,
        user_level: UserLevel = UserLevel.STUDENT,
    ):
        """Get educational explanation of a topic"""
        engine = get_engine()
        return await engine.explain_topic(topic, user_level)

    return app


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Run the server directly"""
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="ECG Guru API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama model")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")

    args = parser.parse_args()

    app = create_app(llm_model=args.model)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
