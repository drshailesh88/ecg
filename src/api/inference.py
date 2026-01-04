"""
Inference Engine for ECG Guru API

Server-side inference engine that:
- Processes ECG images
- Runs diagnostic algorithms
- Generates explanations via LLM + RAG
- Adapts output to user expertise level

Since this runs on YOUR server, you control the hardware and can use
more powerful models than would be possible on user devices.
"""

import asyncio
import base64
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

from ..knowledge.advanced_rag import ECGKnowledgeRAG, RetrievedDocument


class InferenceEngine:
    """
    Server-side inference engine for ECG analysis.

    Designed to run on a server with:
    - 16-32GB RAM (or more)
    - Optional GPU for faster inference
    - Access to full knowledge base
    """

    def __init__(
        self,
        llm_model: str = "qwen2.5:7b",
        knowledge_dir: Path = None,
        use_gpu: bool = True,
    ):
        self.llm_model = llm_model
        self.knowledge_dir = knowledge_dir or Path("./data")
        self.use_gpu = use_gpu

        # Initialize components lazily
        self._ollama = None
        self._rag = None
        self._analysis_cache: Dict[str, Any] = {}

    @property
    def ollama(self):
        """Lazy-load Ollama client"""
        if self._ollama is None:
            import ollama
            self._ollama = ollama
        return self._ollama

    @property
    def rag(self) -> ECGKnowledgeRAG:
        """Lazy-load RAG pipeline"""
        if self._rag is None:
            self._rag = ECGKnowledgeRAG(
                persist_dir=self.knowledge_dir / "chroma_db",
                embedding_model="pubmedbert",
                use_reranker=True,
            )
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
    ) -> List[Dict[str, Any]]:
        """Run diagnostic algorithms on the measurements"""
        results = []

        if "all" in algorithms or "brugada" in algorithms:
            results.append(await self._run_brugada(measurements))

        if "all" in algorithms or "basel" in algorithms:
            results.append(await self._run_basel(measurements))

        if "all" in algorithms or "vereckei" in algorithms:
            results.append(await self._run_vereckei(measurements))

        # Add more algorithms as implemented

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
        # Placeholder implementation
        return {
            "name": "brugada",
            "conclusion": "Unable to determine - requires signal data",
            "confidence": 0.0,
            "steps": [
                {"step": 1, "criterion": "RS complex in precordials", "result": "not_evaluated"},
                {"step": 2, "criterion": "R to S interval >100ms", "result": "not_evaluated"},
                {"step": 3, "criterion": "AV dissociation", "result": "not_evaluated"},
                {"step": 4, "criterion": "Morphology criteria", "result": "not_evaluated"},
            ],
            "supports_vt": None,
            "supports_svt": None,
        }

    async def _run_basel(self, measurements: Dict) -> Dict[str, Any]:
        """
        Basel 3-criteria algorithm (2022) for VT vs SVT.

        Fastest algorithm with 91-93% accuracy.
        """
        return {
            "name": "basel",
            "conclusion": "Unable to determine - requires signal data",
            "confidence": 0.0,
            "steps": [
                {"step": 1, "criterion": "Predominantly positive QRS in aVR", "result": "not_evaluated"},
                {"step": 2, "criterion": "Initial R >40ms in aVR", "result": "not_evaluated"},
                {"step": 3, "criterion": "Atypical BBB pattern", "result": "not_evaluated"},
            ],
            "supports_vt": None,
            "supports_svt": None,
        }

    async def _run_vereckei(self, measurements: Dict) -> Dict[str, Any]:
        """Vereckei aVR algorithm for VT vs SVT"""
        return {
            "name": "vereckei",
            "conclusion": "Unable to determine - requires signal data",
            "confidence": 0.0,
            "steps": [
                {"step": 1, "criterion": "Initial R wave in aVR", "result": "not_evaluated"},
                {"step": 2, "criterion": "Initial r or q >40ms", "result": "not_evaluated"},
                {"step": 3, "criterion": "Notch on descending limb", "result": "not_evaluated"},
                {"step": 4, "criterion": "Vi/Vt ratio", "result": "not_evaluated"},
            ],
            "supports_vt": None,
            "supports_svt": None,
        }

    # ========================================================================
    # Finding Analysis
    # ========================================================================

    async def _analyze_findings(
        self,
        measurements: Dict,
        algorithm_results: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Analyze measurements to generate findings"""
        findings = []

        # Rate analysis
        hr = measurements.get("heart_rate", 0)
        if hr:
            if hr < 60:
                findings.append({
                    "category": "rhythm",
                    "finding": "Bradycardia",
                    "severity": "abnormal",
                    "confidence": 0.95,
                    "explanation": f"Heart rate of {hr} bpm is below normal (60-100 bpm)",
                })
            elif hr > 100:
                findings.append({
                    "category": "rhythm",
                    "finding": "Tachycardia",
                    "severity": "abnormal",
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
                    "explanation": f"PR interval of {pr}ms is short. Consider pre-excitation.",
                })

        # QRS duration
        qrs = measurements.get("qrs_duration_ms", 0)
        if qrs:
            if qrs > 120:
                findings.append({
                    "category": "conduction",
                    "finding": "Wide QRS complex",
                    "severity": "abnormal",
                    "confidence": 0.9,
                    "explanation": f"QRS duration of {qrs}ms suggests bundle branch block or ventricular origin",
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
        algorithm_results: List[Dict],
        user_level: str,
        clinical_context: str = None,
    ) -> Dict[str, Any]:
        """Generate interpretation using LLM + RAG"""

        # Build query for RAG
        finding_summaries = [f["finding"] for f in findings]
        query = f"ECG interpretation for: {', '.join(finding_summaries)}"

        # Retrieve relevant knowledge
        docs, context = self.rag.query_with_context(
            query,
            top_k=5,
            use_multi_query=True,
            use_reranking=True,
        )

        # Build prompt based on user level
        level_instructions = {
            "rmp": "Explain in very simple terms. Focus on: Is this normal? Is this urgent? Does patient need referral?",
            "student": "Provide educational explanation. Include teaching points about the findings.",
            "resident": "Detailed analysis with differential diagnosis. Include clinical reasoning.",
            "cardiologist": "Expert-level analysis. Include nuances and edge cases.",
        }

        prompt = f"""You are an expert electrophysiologist analyzing an ECG.

{level_instructions.get(user_level, level_instructions['student'])}

ECG Measurements:
- Heart Rate: {measurements.get('heart_rate', 'N/A')} bpm
- PR Interval: {measurements.get('pr_interval_ms', 'N/A')} ms
- QRS Duration: {measurements.get('qrs_duration_ms', 'N/A')} ms
- QTc: {measurements.get('qtc_ms', 'N/A')} ms
- Axis: {measurements.get('axis_degrees', 'N/A')} degrees
- Rhythm: {measurements.get('rhythm', 'N/A')}

Findings:
{self._format_findings(findings)}

Algorithm Results:
{self._format_algorithm_results(algorithm_results)}

{f"Clinical Context: {clinical_context}" if clinical_context else ""}

Knowledge Base Context:
{context}

Provide:
1. A one-line summary
2. Primary diagnosis with confidence
3. Differential diagnoses (top 3)
4. Is this urgent? (Yes/No and why)
5. Recommended actions

Be concise and clinically relevant. Cite sources when possible."""

        # Generate with LLM
        response = self.ollama.generate(
            model=self.llm_model,
            prompt=prompt,
            options={"temperature": 0.3, "num_predict": 1024},
        )

        # Parse response (simplified - would need proper parsing)
        llm_output = response.get("response", "")

        # Determine urgency
        is_urgent = any(f.get("severity") == "critical" for f in findings)
        urgency_reason = None
        if is_urgent:
            critical = [f for f in findings if f.get("severity") == "critical"]
            urgency_reason = f"Critical finding: {critical[0]['finding']}"

        return {
            "summary": self._extract_summary(llm_output),
            "primary_diagnosis": findings[0]["finding"] if findings else "Normal ECG",
            "differentials": [],  # Would parse from LLM output
            "confidence": 0.8,
            "is_urgent": is_urgent,
            "urgency_reason": urgency_reason,
            "actions": ["Correlate with clinical context", "Compare with prior ECGs"],
            "sources": [doc.metadata.get("source", "Unknown") for doc in docs],
        }

    def _format_findings(self, findings: List[Dict]) -> str:
        """Format findings for prompt"""
        lines = []
        for f in findings:
            lines.append(f"- {f['finding']} ({f['severity']}): {f['explanation']}")
        return "\n".join(lines) if lines else "No significant findings"

    def _format_algorithm_results(self, results: List[Dict]) -> str:
        """Format algorithm results for prompt"""
        lines = []
        for r in results:
            lines.append(f"- {r['name']}: {r['conclusion']}")
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
        """Handle chat messages about ECG"""

        # Get analysis context if available
        analysis_context = ""
        if analysis_id and analysis_id in self._analysis_cache:
            analysis = self._analysis_cache[analysis_id]
            analysis_context = f"""
Previous ECG Analysis:
- Summary: {analysis['summary']}
- Diagnosis: {analysis['primary_diagnosis']}
- Findings: {', '.join(f['finding'] for f in analysis['findings'])}
"""

        # Query RAG for relevant knowledge
        docs, rag_context = self.rag.query_with_context(
            message,
            top_k=3,
            use_multi_query=True,
        )

        # Build chat prompt
        history_text = ""
        if history:
            for msg in history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"

        prompt = f"""You are an expert cardiologist and electrophysiologist.
Answer the user's question about ECG or cardiology.

{analysis_context}

Relevant Knowledge:
{rag_context}

{f"Previous conversation:{chr(10)}{history_text}" if history_text else ""}

User Question: {message}

Provide a helpful, accurate answer. Be concise but thorough.
Cite sources when using specific information from the knowledge base."""

        response = self.ollama.generate(
            model=self.llm_model,
            prompt=prompt,
            options={"temperature": 0.4, "num_predict": 512},
        )

        # Generate suggested follow-up questions
        suggested = self._generate_suggestions(message, docs)

        return {
            "response": response.get("response", ""),
            "sources": [doc.metadata.get("source", "Unknown") for doc in docs],
            "suggested_questions": suggested,
        }

    async def chat_stream(
        self,
        message: str,
        analysis_id: str = None,
        user_level: str = "student",
        history: List[Dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response"""
        # Similar to chat() but with streaming
        docs, rag_context = self.rag.query_with_context(message, top_k=3)

        prompt = f"""You are an expert cardiologist. Answer concisely:

Knowledge:
{rag_context}

Question: {message}"""

        response = self.ollama.generate(
            model=self.llm_model,
            prompt=prompt,
            stream=True,
        )

        for chunk in response:
            if "response" in chunk:
                yield chunk["response"]

    def _generate_suggestions(
        self,
        query: str,
        docs: List[RetrievedDocument],
    ) -> List[str]:
        """Generate suggested follow-up questions"""
        suggestions = [
            "What are the clinical implications of this finding?",
            "How does this affect management?",
            "What should I look for in serial ECGs?",
        ]

        # Add topic-specific suggestions based on retrieved docs
        for doc in docs[:2]:
            topic = doc.metadata.get("topic", "")
            if topic:
                suggestions.append(f"Tell me more about {topic}")

        return suggestions[:4]

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
        """Get educational explanation of a topic"""
        docs, context = self.rag.query_for_teaching(topic, top_k=5)

        level_detail = {
            "rmp": "very simple, practical",
            "student": "educational with fundamentals",
            "resident": "detailed with clinical pearls",
            "cardiologist": "expert-level with nuances",
        }

        prompt = f"""Explain "{topic}" for ECG interpretation.
Target audience: {level_detail.get(user_level, 'medical student')}

Use this knowledge:
{context}

Provide:
1. Definition/Overview
2. Key points to remember
3. Clinical significance
4. Common pitfalls

Be accurate and cite sources when possible."""

        response = self.ollama.generate(
            model=self.llm_model,
            prompt=prompt,
            options={"temperature": 0.3, "num_predict": 800},
        )

        return {
            "topic": topic,
            "explanation": response.get("response", ""),
            "sources": [doc.metadata.get("source", "Unknown") for doc in docs],
            "related_topics": [],  # Would extract from docs
        }
