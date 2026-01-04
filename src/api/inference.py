"""
Inference Engine for ECG Guru API

Server-side inference engine that:
- Processes ECG images
- Runs diagnostic algorithms
- Generates explanations via Claude API
- Adapts output to user expertise level

Architecture:
- Algorithms: Validated, deterministic (Brugada, Basel, SMART-WPW)
- LLM: Claude API for expert-level explanations
- Fallback: Templated responses when API unavailable
"""

import asyncio
import base64
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

# Import LLM client (Claude API)
from ..ai.llm_client import (
    LLMClient,
    LLMConfig,
    UserLevel as LLMUserLevel,
    explain_ecg,
)

# Import algorithms
from ..core.algorithms import (
    BrugadaAlgorithm,
    VereckeiAlgorithm,
    BaselAlgorithm,
    PavaAlgorithm,
    VTSVTEnsemble,
    STEMIDetector,
    STEMILocalizer,
    analyze_stemi,
)

# RAG is optional - gracefully handle if not available
try:
    from ..knowledge.advanced_rag import ECGKnowledgeRAG, RetrievedDocument
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    ECGKnowledgeRAG = None
    RetrievedDocument = None


class InferenceEngine:
    """
    Server-side inference engine for ECG analysis.

    Uses:
    - Claude API for expert-level explanations (primary)
    - Validated algorithms for diagnosis (Brugada, Basel, etc.)
    - Optional RAG for knowledge retrieval
    """

    def __init__(
        self,
        llm_model: str = "claude-sonnet-4-20250514",
        knowledge_dir: Path = None,
        anthropic_api_key: str = None,
    ):
        self.llm_model = llm_model
        self.knowledge_dir = knowledge_dir or Path("./data")

        # Initialize Claude client
        config = LLMConfig(api_key=anthropic_api_key, model=llm_model)
        self._llm_client = LLMClient(config)

        # Optional components
        self._rag = None
        self._analysis_cache: Dict[str, Any] = {}

    @property
    def llm(self) -> LLMClient:
        """Get LLM client"""
        return self._llm_client

    @property
    def rag(self):
        """Lazy-load RAG pipeline (optional)"""
        if not RAG_AVAILABLE:
            return None
        if self._rag is None:
            try:
                self._rag = ECGKnowledgeRAG(
                    persist_dir=self.knowledge_dir / "chroma_db",
                    embedding_model="pubmedbert",
                    use_reranker=True,
                )
            except Exception:
                self._rag = None
        return self._rag

    # ========================================================================
    # Main Analysis
    # ========================================================================

    async def analyze(
        self,
        image_base64: str = None,
        image_url: str = None,
        user_level: str = "student",
        include_teaching: bool = True,
        algorithms: List[str] = None,
        clinical_context: str = None,
    ) -> Dict[str, Any]:
        """
        Analyze an ECG image.

        Steps:
        1. Process image (extract leads, digitize signals)
        2. Extract measurements (intervals, axis, rate)
        3. Run diagnostic algorithms
        4. Generate explanation via LLM + RAG
        5. Format for user level
        """
        start_time = datetime.now()
        analysis_id = str(uuid.uuid4())[:8]

        # Get image data
        if image_url:
            image_data = await self._fetch_image(image_url)
        elif image_base64:
            image_data = base64.b64decode(image_base64)
        else:
            raise ValueError("Must provide image_base64 or image_url")

        # Step 1: Process image (placeholder - needs CV implementation)
        # TODO: Implement actual ECG image processing
        processed = await self._process_ecg_image(image_data)

        # Step 2: Extract measurements
        measurements = await self._extract_measurements(processed)

        # Step 3: Run algorithms
        algorithms = algorithms or ["all"]
        algorithm_results = await self._run_algorithms(measurements, algorithms)

        # Step 4: Analyze findings
        findings = await self._analyze_findings(measurements, algorithm_results)

        # Step 5: Generate interpretation via LLM + RAG
        interpretation = await self._generate_interpretation(
            measurements=measurements,
            findings=findings,
            algorithm_results=algorithm_results,
            user_level=user_level,
            clinical_context=clinical_context,
        )

        # Step 6: Get teaching content if requested
        teaching_content = None
        similar_cases = None
        if include_teaching:
            teaching_content, similar_cases = await self._get_teaching_content(
                findings=findings,
                user_level=user_level,
            )

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Build response
        response = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now(),
            "processing_time_ms": processing_time,
            "summary": interpretation["summary"],
            "measurements": measurements,
            "findings": findings,
            "algorithm_results": algorithm_results,
            "primary_diagnosis": interpretation["primary_diagnosis"],
            "differential_diagnoses": interpretation["differentials"],
            "confidence": interpretation["confidence"],
            "is_urgent": interpretation["is_urgent"],
            "urgency_reason": interpretation.get("urgency_reason"),
            "recommended_actions": interpretation["actions"],
            "teaching_content": teaching_content,
            "similar_cases": similar_cases,
            "knowledge_sources": interpretation["sources"],
        }

        # Cache for chat reference
        self._analysis_cache[analysis_id] = response

        return response

    # ========================================================================
    # Image Processing (Placeholder)
    # ========================================================================

    async def _process_ecg_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process ECG image to extract leads and signals.

        TODO: Implement with OpenCV + custom CNN for:
        - Lead detection and isolation
        - Signal digitization
        - Grid detection and calibration
        """
        # Placeholder - return mock data for now
        return {
            "leads_detected": ["I", "II", "III", "aVR", "aVL", "aVF",
                               "V1", "V2", "V3", "V4", "V5", "V6"],
            "quality": "good",
            "calibration": {"mm_per_mV": 10, "mm_per_s": 25},
            "signals": {},  # Would contain digitized waveforms
        }

    async def _extract_measurements(self, processed: Dict) -> Dict[str, Any]:
        """
        Extract ECG measurements from processed data.

        TODO: Implement signal processing for:
        - P wave detection
        - QRS detection
        - T wave detection
        - Interval calculations
        """
        # Placeholder - return mock measurements
        return {
            "heart_rate": 75,
            "pr_interval_ms": 160,
            "qrs_duration_ms": 90,
            "qt_interval_ms": 400,
            "qtc_ms": 420,
            "axis_degrees": 45,
            "rhythm": "sinus",
        }

    # ========================================================================
    # Algorithm Execution
    # ========================================================================

    async def _run_algorithms(
        self,
        measurements: Dict,
        algorithms: List[str],
    ) -> Dict[str, Any]:
        """Run diagnostic algorithms on the measurements"""
        results = {}

        # STEMI analysis (always run - most critical)
        if "all" in algorithms or "stemi" in algorithms:
            results["stemi"] = await self._run_stemi_analysis(measurements)

        # VT/SVT algorithms (run if wide QRS or tachycardia)
        qrs = measurements.get("qrs_duration_ms", 0)
        hr = measurements.get("heart_rate", 0)

        # Only run VT/SVT algorithms if QRS is wide and there's tachycardia
        if qrs > 120 and hr > 100:
            if "all" in algorithms or "vt_svt_ensemble" in algorithms:
                results["vt_svt_ensemble"] = await self._run_vt_svt_ensemble(measurements)

            # Individual algorithms
            if "all" in algorithms or "brugada" in algorithms:
                results["brugada"] = await self._run_brugada(measurements)

            if "all" in algorithms or "basel" in algorithms:
                results["basel"] = await self._run_basel(measurements)

            if "all" in algorithms or "vereckei" in algorithms:
                results["vereckei"] = await self._run_vereckei(measurements)

            if "all" in algorithms or "pava" in algorithms:
                results["pava"] = await self._run_pava(measurements)

        return results

    async def _run_brugada(self, measurements: Dict) -> Dict[str, Any]:
        """
        Brugada 4-step algorithm for VT vs SVT.

        Steps:
        1. Absence of RS complex in all precordial leads → VT
        2. R to S interval >100ms in any precordial lead → VT
        3. AV dissociation → VT
        4. Morphology criteria for VT
        """
        algorithm = BrugadaAlgorithm()
        result = algorithm.evaluate(measurements)
        return result.to_dict()

    async def _run_basel(self, measurements: Dict) -> Dict[str, Any]:
        """
        Basel 3-criteria algorithm (2022) for VT vs SVT.

        Fastest algorithm with 91-93% accuracy.
        """
        algorithm = BaselAlgorithm()
        result = algorithm.evaluate(measurements)
        return result.to_dict()

    async def _run_vereckei(self, measurements: Dict) -> Dict[str, Any]:
        """Vereckei aVR algorithm for VT vs SVT"""
        algorithm = VereckeiAlgorithm()
        result = algorithm.evaluate(measurements)
        return result.to_dict()

    async def _run_pava(self, measurements: Dict) -> Dict[str, Any]:
        """Pava algorithm - R-wave peak time in Lead II"""
        algorithm = PavaAlgorithm()
        result = algorithm.evaluate(measurements)
        return result.to_dict()

    async def _run_vt_svt_ensemble(self, measurements: Dict) -> Dict[str, Any]:
        """Run all VT/SVT algorithms as an ensemble"""
        ensemble = VTSVTEnsemble()
        result = ensemble.evaluate(measurements)
        return result

    async def _run_stemi_analysis(self, measurements: Dict) -> Dict[str, Any]:
        """
        STEMI detection and localization.

        Returns structured STEMI analysis including:
        - Whether STEMI criteria are met
        - Affected territories
        - Culprit vessel identification
        - Urgent findings and recommendations
        """
        result = analyze_stemi(measurements)

        # Convert STEMIResult to dictionary
        return {
            "is_stemi": result.is_stemi,
            "territories": result.territories,
            "culprit_vessel": result.culprit_vessel,
            "culprit_confidence": result.culprit_confidence,
            "segment_location": result.segment_location,
            "st_changes": result.st_changes,
            "urgent_findings": result.urgent_findings,
            "recommended_actions": result.recommended_actions,
            "differential_diagnosis": result.differential_diagnosis,
            "additional_notes": result.additional_notes,
        }

    # ========================================================================
    # Finding Analysis
    # ========================================================================

    async def _analyze_findings(
        self,
        measurements: Dict,
        algorithm_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Analyze measurements and algorithm results to generate findings"""
        findings = []

        # PRIORITY 1: STEMI findings (most critical)
        if "stemi" in algorithm_results:
            stemi = algorithm_results["stemi"]
            if stemi["is_stemi"]:
                findings.append({
                    "category": "ischemia",
                    "finding": "ACUTE STEMI",
                    "severity": "critical",
                    "confidence": 0.98,
                    "explanation": f"STEMI criteria met. Territory: {', '.join(stemi['territories'])}. "
                                   f"Culprit vessel: {stemi['culprit_vessel']} ({stemi['culprit_confidence']:.0%} confidence)",
                    "urgent_actions": stemi["urgent_findings"],
                    "recommended_actions": stemi["recommended_actions"],
                    "details": stemi,
                })

        # PRIORITY 2: VT/SVT differentiation (if wide QRS tachycardia)
        if "vt_svt_ensemble" in algorithm_results:
            ensemble = algorithm_results["vt_svt_ensemble"]
            conclusion = ensemble.get("consensus", "Indeterminate")
            confidence = ensemble.get("confidence", 0.0)
            agreement = ensemble.get("agreement", {})

            if conclusion == "VT":
                findings.append({
                    "category": "arrhythmia",
                    "finding": "Ventricular Tachycardia (VT)",
                    "severity": "critical",
                    "confidence": confidence,
                    "explanation": f"VT diagnosis based on {agreement.get('vt_count', 0)}/{agreement.get('vt_count', 0) + agreement.get('svt_count', 0)} algorithms. "
                                   f"{ensemble.get('recommendation', '')}",
                    "algorithm_details": ensemble["individual_results"],
                })
            elif conclusion == "SVT":
                findings.append({
                    "category": "arrhythmia",
                    "finding": "SVT with aberrant conduction",
                    "severity": "abnormal",
                    "confidence": confidence,
                    "explanation": f"SVT diagnosis based on {agreement.get('svt_count', 0)}/{agreement.get('vt_count', 0) + agreement.get('svt_count', 0)} algorithms. "
                                   f"{ensemble.get('recommendation', '')}",
                    "algorithm_details": ensemble["individual_results"],
                })
            else:
                findings.append({
                    "category": "arrhythmia",
                    "finding": "Wide complex tachycardia - indeterminate",
                    "severity": "critical",
                    "confidence": confidence,
                    "explanation": "Unable to definitively differentiate VT from SVT. TREAT AS VT until proven otherwise.",
                    "algorithm_details": ensemble["individual_results"],
                })

        # PRIORITY 3: Basic rhythm and interval findings

        # Rate analysis
        hr = measurements.get("heart_rate", 0)
        if hr:
            if hr < 60:
                findings.append({
                    "category": "rhythm",
                    "finding": "Bradycardia",
                    "severity": "abnormal" if hr >= 40 else "critical",
                    "confidence": 0.95,
                    "explanation": f"Heart rate of {hr} bpm is below normal (60-100 bpm)",
                })
            elif hr > 100:
                # Only add if not already covered by VT/SVT analysis
                if "vt_svt_ensemble" not in algorithm_results:
                    findings.append({
                        "category": "rhythm",
                        "finding": "Tachycardia",
                        "severity": "abnormal" if hr < 150 else "critical",
                        "confidence": 0.95,
                        "explanation": f"Heart rate of {hr} bpm is above normal (60-100 bpm)",
                    })
            else:
                findings.append({
                    "category": "rhythm",
                    "finding": "Normal heart rate",
                    "severity": "normal",
                    "confidence": 0.95,
                    "explanation": f"Heart rate of {hr} bpm is within normal range",
                })

        # PR interval
        pr = measurements.get("pr_interval_ms", 0)
        if pr:
            if pr > 200:
                findings.append({
                    "category": "conduction",
                    "finding": "First-degree AV block",
                    "severity": "abnormal",
                    "confidence": 0.9,
                    "explanation": f"PR interval of {pr}ms exceeds 200ms",
                })
            elif pr < 120:
                findings.append({
                    "category": "conduction",
                    "finding": "Short PR interval",
                    "severity": "abnormal",
                    "confidence": 0.9,
                    "explanation": f"PR interval of {pr}ms is short. Consider pre-excitation (WPW).",
                })

        # QRS duration
        qrs = measurements.get("qrs_duration_ms", 0)
        if qrs:
            if qrs > 120:
                # Only add if not already covered by VT/SVT analysis
                if "vt_svt_ensemble" not in algorithm_results:
                    findings.append({
                        "category": "conduction",
                        "finding": "Wide QRS complex",
                        "severity": "abnormal",
                        "confidence": 0.9,
                        "explanation": f"QRS duration of {qrs}ms suggests bundle branch block or ventricular conduction abnormality",
                    })

        # QTc
        qtc = measurements.get("qtc_ms", 0)
        if qtc:
            if qtc > 470:  # Male cutoff
                findings.append({
                    "category": "repolarization",
                    "finding": "Prolonged QTc",
                    "severity": "abnormal" if qtc < 500 else "critical",
                    "confidence": 0.9,
                    "explanation": f"QTc of {qtc}ms is prolonged. Risk of torsades de pointes.",
                })

        return findings

    # ========================================================================
    # LLM + RAG Interpretation
    # ========================================================================

    async def _generate_interpretation(
        self,
        measurements: Dict,
        findings: List[Dict],
        algorithm_results: Dict[str, Any],
        user_level: str,
        clinical_context: str = None,
    ) -> Dict[str, Any]:
        """Generate interpretation using Claude API"""

        # Build algorithm results for LLM
        llm_results = {
            "measurements": measurements,
            "findings": [{"finding": f["finding"], "severity": f["severity"]} for f in findings],
        }

        # Add algorithm results
        if "stemi" in algorithm_results:
            llm_results["stemi"] = algorithm_results["stemi"]
        if "vt_svt_ensemble" in algorithm_results:
            llm_results["vt_svt"] = algorithm_results["vt_svt_ensemble"]

        # Map user level to LLM user level
        level_map = {
            "rmp": LLMUserLevel.RMP,
            "student": LLMUserLevel.STUDENT,
            "resident": LLMUserLevel.RESIDENT,
            "cardiologist": LLMUserLevel.CARDIOLOGIST,
        }
        llm_level = level_map.get(user_level, LLMUserLevel.STUDENT)

        # Generate explanation with Claude
        try:
            explanation = await self.llm.analyze_async(
                algorithm_results=llm_results,
                user_level=llm_level,
                user_question=clinical_context,
            )
        except Exception as e:
            # Fallback to basic interpretation
            explanation = f"Analysis complete. {findings[0]['finding'] if findings else 'No significant findings.'}"

        # Determine urgency from findings
        is_urgent = any(f.get("severity") == "critical" for f in findings)
        urgency_reason = None
        if is_urgent:
            critical = [f for f in findings if f.get("severity") == "critical"]
            urgency_reason = f"Critical finding: {critical[0]['finding']}"

        # Build actions based on findings
        actions = ["Correlate with clinical context", "Compare with prior ECGs"]
        if "stemi" in algorithm_results and algorithm_results["stemi"]["is_stemi"]:
            actions = algorithm_results["stemi"]["recommended_actions"][:5]
        elif "vt_svt_ensemble" in algorithm_results:
            vt = algorithm_results["vt_svt_ensemble"]
            if vt.get("consensus") == "VT":
                actions = [
                    "Assess hemodynamic stability immediately",
                    "Prepare for cardioversion if unstable",
                    "Consider antiarrhythmic therapy (procainamide, amiodarone)",
                    "12-lead ECG comparison with prior",
                    "Cardiology consult urgently",
                ]

        return {
            "summary": self._extract_summary(explanation),
            "primary_diagnosis": findings[0]["finding"] if findings else "Normal ECG",
            "differentials": [],
            "confidence": 0.85,
            "is_urgent": is_urgent,
            "urgency_reason": urgency_reason,
            "actions": actions,
            "sources": ["Claude AI Analysis", "Validated ECG Algorithms"],
            "full_explanation": explanation,
        }

    def _format_findings(self, findings: List[Dict]) -> str:
        """Format findings for prompt"""
        lines = []
        for f in findings:
            lines.append(f"- {f['finding']} ({f['severity']}): {f['explanation']}")
        return "\n".join(lines) if lines else "No significant findings"

    def _format_algorithm_results(self, results: Dict[str, Any]) -> str:
        """Format algorithm results for prompt"""
        lines = []

        # STEMI results
        if "stemi" in results:
            stemi = results["stemi"]
            if stemi["is_stemi"]:
                lines.append(f"- STEMI: YES - {', '.join(stemi['territories'])} ({stemi['culprit_vessel']})")
            else:
                lines.append("- STEMI: No STEMI criteria met")

        # VT/SVT ensemble
        if "vt_svt_ensemble" in results:
            ensemble = results["vt_svt_ensemble"]
            lines.append(f"- VT/SVT Analysis: {ensemble.get('consensus', 'Unknown')} (confidence: {ensemble.get('confidence', 0):.0%})")

        # Individual VT/SVT algorithms
        for algo_name in ["brugada", "basel", "vereckei", "pava"]:
            if algo_name in results:
                algo = results[algo_name]
                lines.append(f"- {algo.get('name', algo_name)}: {algo.get('conclusion', 'N/A')}")

        return "\n".join(lines) if lines else "No algorithms run"

    def _extract_summary(self, llm_output: str) -> str:
        """Extract summary from LLM output"""
        # Simple extraction - would need better parsing
        lines = llm_output.strip().split("\n")
        for line in lines:
            if line.strip():
                return line.strip()[:200]
        return "Analysis complete"

    # ========================================================================
    # Teaching Content
    # ========================================================================

    async def _get_teaching_content(
        self,
        findings: List[Dict],
        user_level: str,
    ) -> tuple:
        """Get teaching content related to the findings"""
        if not findings:
            return None, None

        # Query for teaching cases
        primary_finding = findings[0]["finding"]
        docs, context = self.rag.query_for_teaching(
            primary_finding,
            difficulty=user_level,
            top_k=3,
        )

        similar_cases = [
            {
                "title": doc.metadata.get("title", "Case"),
                "source": doc.metadata.get("source", "Unknown"),
                "preview": doc.content[:200] + "...",
            }
            for doc in docs
        ]

        return context, similar_cases

    # ========================================================================
    # Chat Interface
    # ========================================================================

    async def chat(
        self,
        message: str,
        analysis_id: str = None,
        user_level: str = "student",
        history: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Handle chat messages about ECG using Claude"""

        # Get analysis context if available
        algorithm_results = {}
        if analysis_id and analysis_id in self._analysis_cache:
            analysis = self._analysis_cache[analysis_id]
            algorithm_results = {
                "measurements": analysis.get("measurements", {}),
                "findings": analysis.get("findings", []),
            }
            if "algorithm_results" in analysis:
                for result in analysis["algorithm_results"]:
                    if isinstance(result, dict) and "name" in result:
                        algorithm_results[result["name"]] = result

        # Map user level
        level_map = {
            "rmp": LLMUserLevel.RMP,
            "student": LLMUserLevel.STUDENT,
            "resident": LLMUserLevel.RESIDENT,
            "cardiologist": LLMUserLevel.CARDIOLOGIST,
        }
        llm_level = level_map.get(user_level, LLMUserLevel.STUDENT)

        # Convert history to expected format
        conversation_history = None
        if history:
            conversation_history = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in history[-10:]  # Last 10 messages
            ]

        # Generate response with Claude
        try:
            response_text = await self.llm.analyze_async(
                algorithm_results=algorithm_results,
                user_level=llm_level,
                user_question=message,
                conversation_history=conversation_history,
            )
        except Exception as e:
            response_text = f"I apologize, but I encountered an error processing your question. Please try again. Error: {str(e)}"

        # Generate suggested follow-up questions
        suggested = [
            "What are the clinical implications?",
            "What should I look for on serial ECGs?",
            "How does this affect patient management?",
            "Can you explain this in simpler terms?",
        ]

        return {
            "response": response_text,
            "sources": ["Claude AI", "Validated ECG Algorithms"],
            "suggested_questions": suggested,
        }

    async def chat_stream(
        self,
        message: str,
        analysis_id: str = None,
        user_level: str = "student",
        history: List[Dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response using Claude"""
        # Get analysis context if available
        algorithm_results = {}
        if analysis_id and analysis_id in self._analysis_cache:
            analysis = self._analysis_cache[analysis_id]
            algorithm_results = {
                "measurements": analysis.get("measurements", {}),
                "findings": analysis.get("findings", []),
            }

        # Map user level
        level_map = {
            "rmp": LLMUserLevel.RMP,
            "student": LLMUserLevel.STUDENT,
            "resident": LLMUserLevel.RESIDENT,
            "cardiologist": LLMUserLevel.CARDIOLOGIST,
        }
        llm_level = level_map.get(user_level, LLMUserLevel.STUDENT)

        # Stream response from Claude
        try:
            async for chunk in self.llm.stream_analyze_async(
                algorithm_results=algorithm_results,
                user_level=llm_level,
                user_question=message,
            ):
                yield chunk
        except Exception as e:
            yield f"Error: {str(e)}"

    def _generate_suggestions(
        self,
        query: str,
        docs: List = None,
    ) -> List[str]:
        """Generate suggested follow-up questions"""
        return [
            "What are the clinical implications of this finding?",
            "How does this affect management?",
            "What should I look for in serial ECGs?",
            "Can you explain this in simpler terms?",
        ]

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def _fetch_image(self, url: str) -> bytes:
        """Fetch image from URL"""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def run_algorithm(
        self,
        algorithm_name: str,
        image_base64: str = None,
        measurements: Dict = None,
    ) -> Dict[str, Any]:
        """Run a specific algorithm"""
        if measurements is None:
            if image_base64 is None:
                raise ValueError("Must provide measurements or image")
            # Process image first
            image_data = base64.b64decode(image_base64)
            processed = await self._process_ecg_image(image_data)
            measurements = await self._extract_measurements(processed)

        algorithm_map = {
            "brugada": self._run_brugada,
            "basel": self._run_basel,
            "vereckei": self._run_vereckei,
        }

        if algorithm_name not in algorithm_map:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

        return await algorithm_map[algorithm_name](measurements)

    async def get_teaching_cases(
        self,
        diagnosis: str = None,
        difficulty: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get teaching cases from knowledge base"""
        query = diagnosis or "ECG teaching case"
        docs = self.rag.get_similar_cases(query, top_k=limit)

        return [
            {
                "id": doc.id,
                "title": doc.metadata.get("title", "Case"),
                "source": doc.metadata.get("source", "Unknown"),
                "difficulty": doc.metadata.get("difficulty", "intermediate"),
                "preview": doc.content[:300],
            }
            for doc in docs
        ]

    async def explain_topic(
        self,
        topic: str,
        user_level: str = "student",
    ) -> Dict[str, Any]:
        """Get educational explanation of a topic using Claude"""

        # Map user level
        level_map = {
            "rmp": LLMUserLevel.RMP,
            "student": LLMUserLevel.STUDENT,
            "resident": LLMUserLevel.RESIDENT,
            "cardiologist": LLMUserLevel.CARDIOLOGIST,
        }
        llm_level = level_map.get(user_level, LLMUserLevel.STUDENT)

        # Create a teaching-focused request
        teaching_question = f"""Please provide a comprehensive educational explanation of "{topic}" for ECG interpretation.

Include:
1. Definition and overview
2. Key points to remember
3. Clinical significance
4. Common pitfalls and how to avoid them
5. Practical tips for recognition

Make this educational and memorable."""

        try:
            explanation = await self.llm.analyze_async(
                algorithm_results={"topic": topic},
                user_level=llm_level,
                user_question=teaching_question,
            )
        except Exception as e:
            explanation = f"Unable to generate explanation for {topic}. Error: {str(e)}"

        return {
            "topic": topic,
            "explanation": explanation,
            "sources": ["Claude AI", "ECG Education"],
            "related_topics": self._get_related_topics(topic),
        }

    def _get_related_topics(self, topic: str) -> List[str]:
        """Get related ECG topics"""
        topic_map = {
            "stemi": ["NSTEMI", "Coronary anatomy", "Reciprocal changes"],
            "vt": ["SVT with aberrancy", "Brugada algorithm", "WCT differential"],
            "wpw": ["Pre-excitation", "Accessory pathways", "AVRT"],
            "axis": ["Left axis deviation", "Right axis deviation", "Hemiblocks"],
            "block": ["RBBB", "LBBB", "AV blocks"],
        }
        for key, related in topic_map.items():
            if key in topic.lower():
                return related
        return ["ECG basics", "Rhythm analysis", "Interval measurement"]


# ========================================================================
# Test / Demo
# ========================================================================

async def test_algorithms():
    """
    Test algorithm integration with sample ECG measurements.

    This demonstrates that the inference engine can successfully call
    the implemented algorithms and format results.
    """
    print("=" * 80)
    print("ECG Guru Inference Engine - Algorithm Integration Test")
    print("=" * 80)

    # Test Case 1: Inferior STEMI
    print("\n" + "=" * 80)
    print("TEST CASE 1: Inferior STEMI (RCA)")
    print("=" * 80)

    inferior_stemi_measurements = {
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

    engine = InferenceEngine()
    stemi_result = await engine._run_stemi_analysis(inferior_stemi_measurements)

    print(f"\nSTEMI Detected: {stemi_result['is_stemi']}")
    print(f"Territories: {', '.join(stemi_result['territories'])}")
    print(f"Culprit Vessel: {stemi_result['culprit_vessel']} ({stemi_result['culprit_confidence']:.0%} confidence)")
    print(f"Segment: {stemi_result['segment_location']}")
    print("\nUrgent Findings:")
    for finding in stemi_result['urgent_findings']:
        print(f"  - {finding}")
    print("\nRecommended Actions (first 3):")
    for action in stemi_result['recommended_actions'][:3]:
        print(f"  - {action}")

    # Test Case 2: Wide Complex Tachycardia (VT)
    print("\n" + "=" * 80)
    print("TEST CASE 2: Wide Complex Tachycardia (VT)")
    print("=" * 80)

    vt_measurements = {
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

    # Run individual algorithms
    brugada = await engine._run_brugada(vt_measurements)
    basel = await engine._run_basel(vt_measurements)
    vereckei = await engine._run_vereckei(vt_measurements)
    pava = await engine._run_pava(vt_measurements)

    print(f"\nBrugada Algorithm: {brugada['conclusion']} (confidence: {brugada['confidence']:.0%})")
    print(f"Basel Algorithm: {basel['conclusion']} (confidence: {basel['confidence']:.0%})")
    print(f"Vereckei Algorithm: {vereckei['conclusion']} (confidence: {vereckei['confidence']:.0%})")
    print(f"Pava Algorithm: {pava['conclusion']} (confidence: {pava['confidence']:.0%})")

    # Run ensemble
    ensemble = await engine._run_vt_svt_ensemble(vt_measurements)

    print(f"\nENSEMBLE RESULT:")
    print(f"Consensus: {ensemble['consensus']} (confidence: {ensemble['confidence']:.0%})")
    print(f"Agreement: {ensemble['agreement']['agreement_level']} ({ensemble['agreement']['agreement_percentage']}%)")
    print(f"\nRecommendation:\n{ensemble['recommendation']}")

    # Test Case 3: Complete analysis with findings
    print("\n" + "=" * 80)
    print("TEST CASE 3: Complete Findings Analysis")
    print("=" * 80)

    algorithm_results = {
        "stemi": stemi_result,
    }

    findings = await engine._analyze_findings(inferior_stemi_measurements, algorithm_results)

    print(f"\nTotal Findings: {len(findings)}")
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['finding']} ({finding['severity']})")
        print(f"   Category: {finding['category']}")
        print(f"   Confidence: {finding['confidence']:.0%}")
        print(f"   Explanation: {finding['explanation']}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    """
    Run algorithm integration tests.

    Usage:
        python -m src.api.inference
    """
    import asyncio
    asyncio.run(test_algorithms())
