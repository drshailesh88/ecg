"""
LLM Client for ECG Guru

Provides intelligent ECG analysis explanations using Claude API.
Designed to feel like consulting with a senior electrophysiologist.

Architecture:
- Primary: Claude API (Sonnet) for best quality
- Fallback: Templated responses from report generator
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import httpx

# Try to import anthropic, but don't fail if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class UserLevel(str, Enum):
    """User expertise level - determines explanation depth"""
    RMP = "rmp"                    # Village practitioner - simple verdicts
    STUDENT = "student"            # MBBS student - educational
    RESIDENT = "resident"          # MD/DM resident - clinical detail
    CARDIOLOGIST = "cardiologist"  # Expert - full technical


@dataclass
class LLMConfig:
    """LLM configuration"""
    api_key: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2048
    temperature: float = 0.3  # Lower for medical accuracy
    timeout: float = 30.0

    def __post_init__(self):
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")


# =============================================================================
# Expert EP System Prompt
# =============================================================================

EXPERT_EP_SYSTEM_PROMPT = """You are an expert cardiac electrophysiologist with 20+ years of experience interpreting ECGs. You are helping medical professionals analyze ECGs through the ECG Guru app.

## Your Expertise
- Fellowship-trained in cardiac electrophysiology
- Expert in arrhythmia diagnosis and management
- Extensive experience with complex ECG interpretation
- Published researcher in cardiac electrophysiology

## Your Role
You receive structured algorithm results from validated ECG analysis algorithms (Brugada, Basel, Vereckei, SMART-WPW, etc.) and provide expert clinical interpretation.

## Communication Style
- Clear, confident, but never arrogant
- Explain your reasoning step-by-step
- Use appropriate medical terminology for the user's level
- Always acknowledge uncertainty when present
- Provide actionable clinical guidance

## Critical Rules
1. NEVER make up measurements or findings - only use what's provided
2. ALWAYS include appropriate disclaimers for serious findings
3. For STEMI: Emphasize urgency and time-to-treatment
4. For VT: Stress hemodynamic assessment and treatment options
5. Be educational - help users learn, not just get answers

## Response Format
Structure your responses with:
1. **Summary** - One-line clinical impression
2. **Key Findings** - Bulleted list of important observations
3. **Analysis** - Detailed explanation appropriate to user level
4. **Clinical Implications** - What this means for patient care
5. **Recommendations** - Specific next steps

## User Levels
- RMP (Rural Medical Practitioner): Use simple language, focus on "normal vs abnormal" and "refer vs don't refer"
- STUDENT: Educational focus, explain the "why" behind findings
- RESIDENT: Clinical detail, differential diagnoses, treatment considerations
- CARDIOLOGIST: Full technical analysis, subtle findings, EP-level discussion

Remember: You are a clinical decision SUPPORT tool. Always recommend correlation with clinical context and physician judgment."""


# =============================================================================
# User-Level Specific Instructions
# =============================================================================

USER_LEVEL_INSTRUCTIONS = {
    UserLevel.RMP: """
The user is a Rural Medical Practitioner (RMP) or village doctor.

Communication guidelines:
- Use simple, clear language (avoid complex medical jargon)
- Focus on: Is this NORMAL or ABNORMAL?
- Clear YES/NO on: Does this patient need URGENT referral?
- Use analogies when helpful
- Provide specific referral guidance
- Red flags should be VERY clear

Example phrasing:
- "This ECG shows a SERIOUS problem. The patient needs to go to a hospital with a cath lab RIGHT NOW."
- "This is a NORMAL ECG. No urgent action needed."
- "This could be dangerous. Please refer to a cardiologist within 24 hours."
""",

    UserLevel.STUDENT: """
The user is an MBBS medical student learning ECG interpretation.

Communication guidelines:
- Educational tone - explain the "why" behind each finding
- Connect findings to underlying pathophysiology
- Teach pattern recognition
- Reference standard criteria and algorithms
- Encourage systematic approach
- Include learning points

Example phrasing:
- "Notice how the ST elevation in V1-V4 with reciprocal depression in II, III, aVF indicates anterior STEMI. This pattern occurs because..."
- "The Brugada algorithm helps us differentiate VT from SVT. Let's walk through each step..."
- "Teaching point: In WPW, the delta wave represents early ventricular activation via the accessory pathway..."
""",

    UserLevel.RESIDENT: """
The user is an MD/DM Cardiology resident.

Communication guidelines:
- Clinical depth appropriate for residency training
- Discuss differential diagnoses
- Include treatment considerations
- Reference current guidelines (ACC/AHA, ESC)
- Discuss clinical decision-making
- Mention relevant clinical trials when applicable

Example phrasing:
- "The ensemble analysis strongly favors VT (4/4 algorithms concordant). Given the hemodynamic stability, consider procainamide per ACLS guidelines, though electrical cardioversion remains first-line if any deterioration."
- "The SMART-WPW algorithm localizes this to a left lateral pathway. This has implications for ablation approach - typically retrograde aortic access preferred."
""",

    UserLevel.CARDIOLOGIST: """
The user is a practicing cardiologist or electrophysiologist.

Communication guidelines:
- Peer-level technical discussion
- Focus on nuances and subtle findings
- EP-level analysis for arrhythmias
- Discuss procedural implications
- Brief and efficient - they know the basics
- Highlight what's clinically significant

Example phrasing:
- "Classic proximal LAD lesion pattern with ST elevation V1-V4, hyperacute T-waves, and reciprocal inferior changes. Wraparound LAD possible given V5-V6 involvement."
- "Pathway localized to left lateral by SMART-WPW (97% accuracy). Delta polarity pattern consistent with epicardial CS insertion - may need epicardial approach if endo fails."
"""
}


# =============================================================================
# LLM Client
# =============================================================================

class LLMClient:
    """
    Intelligent LLM client for ECG analysis explanations.

    Uses Claude API for high-quality medical explanations.
    Falls back to templated responses when API unavailable.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client: Optional[anthropic.Anthropic] = None
        self._async_client: Optional[anthropic.AsyncAnthropic] = None

    def _get_client(self) -> Optional[anthropic.Anthropic]:
        """Get or create sync Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            return None
        if not self.config.api_key:
            return None
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.config.api_key)
        return self._client

    def _get_async_client(self) -> Optional[anthropic.AsyncAnthropic]:
        """Get or create async Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            return None
        if not self.config.api_key:
            return None
        if self._async_client is None:
            self._async_client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
        return self._async_client

    def _build_messages(
        self,
        algorithm_results: Dict[str, Any],
        user_question: Optional[str],
        user_level: UserLevel,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Build message list for Claude API"""
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Build the analysis context
        context_parts = ["## ECG Analysis Results\n"]

        # Add measurements if present
        if "measurements" in algorithm_results:
            m = algorithm_results["measurements"]
            context_parts.append("### Measurements")
            if m.get("heart_rate"):
                context_parts.append(f"- Heart Rate: {m['heart_rate']} bpm")
            if m.get("rhythm"):
                context_parts.append(f"- Rhythm: {m['rhythm']}")
            if m.get("pr_interval_ms"):
                context_parts.append(f"- PR Interval: {m['pr_interval_ms']} ms")
            if m.get("qrs_duration_ms"):
                context_parts.append(f"- QRS Duration: {m['qrs_duration_ms']} ms")
            if m.get("qtc_ms"):
                context_parts.append(f"- QTc: {m['qtc_ms']} ms")
            if m.get("axis_degrees") is not None:
                context_parts.append(f"- Axis: {m['axis_degrees']}°")
            context_parts.append("")

        # Add VT/SVT analysis if present
        if "vt_svt" in algorithm_results:
            vt = algorithm_results["vt_svt"]
            context_parts.append("### VT vs SVT Analysis (Wide Complex Tachycardia)")
            context_parts.append(f"- **Consensus Diagnosis**: {vt.get('consensus', 'N/A')}")
            context_parts.append(f"- **Confidence**: {vt.get('confidence', 0):.0%}")
            if vt.get('agreement'):
                context_parts.append(f"- **Algorithm Agreement**: {vt['agreement'].get('agreement_level', 'unknown')}")
            if vt.get('individual_results'):
                context_parts.append("- **Individual Algorithm Results**:")
                for algo, res in vt['individual_results'].items():
                    context_parts.append(f"  - {algo}: {res.get('conclusion', 'N/A')} ({res.get('confidence', 0):.0%})")
            if vt.get('recommendation'):
                context_parts.append(f"- **Clinical Recommendation**: {vt['recommendation']}")
            context_parts.append("")

        # Add STEMI analysis if present
        if "stemi" in algorithm_results:
            st = algorithm_results["stemi"]
            context_parts.append("### STEMI Analysis")
            context_parts.append(f"- **STEMI Detected**: {'YES - EMERGENCY' if st.get('is_stemi') else 'No'}")
            if st.get('is_stemi'):
                context_parts.append(f"- **Territories**: {', '.join(st.get('territories', []))}")
                context_parts.append(f"- **Culprit Vessel**: {st.get('culprit_vessel', 'Unknown')}")
                context_parts.append(f"- **Confidence**: {st.get('culprit_confidence', 0):.0%}")
                if st.get('segment_location'):
                    context_parts.append(f"- **Segment**: {st['segment_location']}")
                if st.get('urgent_findings'):
                    context_parts.append("- **URGENT FINDINGS**:")
                    for finding in st['urgent_findings'][:5]:
                        context_parts.append(f"  - {finding}")
            context_parts.append("")

        # Add pathway analysis if present
        if "pathway" in algorithm_results:
            pw = algorithm_results["pathway"]
            context_parts.append("### Accessory Pathway Analysis (WPW)")
            if pw.get('primary_result'):
                pr = pw['primary_result']
                context_parts.append(f"- **Pathway Location**: {pr.get('primary_location', 'Indeterminate')}")
                context_parts.append(f"- **Confidence**: {pr.get('confidence', 0):.0%}")
                context_parts.append(f"- **Algorithm**: {pr.get('algorithm_used', 'Unknown')}")
                if pr.get('alternative_locations'):
                    context_parts.append(f"- **Alternatives**: {', '.join(pr['alternative_locations'][:3])}")
                if pr.get('ablation_approach'):
                    context_parts.append(f"- **Ablation Approach**: {pr['ablation_approach']}")
            context_parts.append("")

        # Add raw findings if present
        if "findings" in algorithm_results:
            context_parts.append("### Additional Findings")
            for finding in algorithm_results["findings"]:
                if isinstance(finding, dict):
                    context_parts.append(f"- {finding.get('finding', finding)}")
                else:
                    context_parts.append(f"- {finding}")
            context_parts.append("")

        analysis_context = "\n".join(context_parts)

        # Build the user message
        if user_question:
            user_content = f"{analysis_context}\n---\n\n**User Question**: {user_question}"
        else:
            user_content = f"{analysis_context}\n---\n\nPlease provide a comprehensive analysis of this ECG."

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages

    def _get_system_prompt(self, user_level: UserLevel) -> str:
        """Get system prompt with user-level specific instructions"""
        return EXPERT_EP_SYSTEM_PROMPT + "\n\n" + USER_LEVEL_INSTRUCTIONS.get(
            user_level,
            USER_LEVEL_INSTRUCTIONS[UserLevel.RESIDENT]
        )

    async def analyze_async(
        self,
        algorithm_results: Dict[str, Any],
        user_level: UserLevel = UserLevel.RESIDENT,
        user_question: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate expert ECG analysis explanation asynchronously.

        Args:
            algorithm_results: Results from ECG algorithms
            user_level: User expertise level
            user_question: Optional specific question from user
            conversation_history: Previous messages in conversation

        Returns:
            Expert analysis explanation
        """
        client = self._get_async_client()

        if client is None:
            # Fallback to templated response
            return self._generate_fallback_response(algorithm_results, user_level)

        messages = self._build_messages(
            algorithm_results,
            user_question,
            user_level,
            conversation_history
        )

        try:
            response = await client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self._get_system_prompt(user_level),
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            # Log error and fallback
            print(f"LLM API error: {e}")
            return self._generate_fallback_response(algorithm_results, user_level)

    def analyze(
        self,
        algorithm_results: Dict[str, Any],
        user_level: UserLevel = UserLevel.RESIDENT,
        user_question: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate expert ECG analysis explanation synchronously.

        Args:
            algorithm_results: Results from ECG algorithms
            user_level: User expertise level
            user_question: Optional specific question from user
            conversation_history: Previous messages in conversation

        Returns:
            Expert analysis explanation
        """
        client = self._get_client()

        if client is None:
            return self._generate_fallback_response(algorithm_results, user_level)

        messages = self._build_messages(
            algorithm_results,
            user_question,
            user_level,
            conversation_history
        )

        try:
            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self._get_system_prompt(user_level),
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            print(f"LLM API error: {e}")
            return self._generate_fallback_response(algorithm_results, user_level)

    async def stream_analyze_async(
        self,
        algorithm_results: Dict[str, Any],
        user_level: UserLevel = UserLevel.RESIDENT,
        user_question: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream expert ECG analysis explanation.

        Yields chunks of the response as they're generated.
        """
        client = self._get_async_client()

        if client is None:
            yield self._generate_fallback_response(algorithm_results, user_level)
            return

        messages = self._build_messages(
            algorithm_results,
            user_question,
            user_level,
            conversation_history
        )

        try:
            async with client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self._get_system_prompt(user_level),
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            print(f"LLM API error: {e}")
            yield self._generate_fallback_response(algorithm_results, user_level)

    def _generate_fallback_response(
        self,
        algorithm_results: Dict[str, Any],
        user_level: UserLevel
    ) -> str:
        """Generate templated response when LLM unavailable"""

        parts = ["## ECG Analysis Report\n"]
        parts.append("*Note: AI explanation unavailable. Showing algorithm results.*\n")

        # VT/SVT
        if "vt_svt" in algorithm_results:
            vt = algorithm_results["vt_svt"]
            parts.append(f"### Wide Complex Tachycardia Analysis")
            parts.append(f"**Diagnosis**: {vt.get('consensus', 'Indeterminate')}")
            parts.append(f"**Confidence**: {vt.get('confidence', 0):.0%}")
            if vt.get('recommendation'):
                parts.append(f"\n**Recommendation**: {vt['recommendation']}")
            parts.append("")

        # STEMI
        if "stemi" in algorithm_results:
            st = algorithm_results["stemi"]
            if st.get('is_stemi'):
                parts.append("### ⚠️ STEMI DETECTED - EMERGENCY")
                parts.append(f"**Territories**: {', '.join(st.get('territories', []))}")
                parts.append(f"**Culprit Vessel**: {st.get('culprit_vessel', 'Unknown')}")
                parts.append("\n**IMMEDIATE ACTION REQUIRED**: Activate cath lab, door-to-balloon < 90 min")
            else:
                parts.append("### STEMI Analysis")
                parts.append("No STEMI criteria met.")
            parts.append("")

        # Pathway
        if "pathway" in algorithm_results:
            pw = algorithm_results["pathway"]
            if pw.get('primary_result'):
                pr = pw['primary_result']
                parts.append("### Accessory Pathway (WPW)")
                parts.append(f"**Location**: {pr.get('primary_location', 'Indeterminate')}")
                parts.append(f"**Confidence**: {pr.get('confidence', 0):.0%}")
            parts.append("")

        # Disclaimer
        parts.append("\n---")
        parts.append("*This analysis is from validated algorithms. For full AI-powered ")
        parts.append("explanation, please ensure API connectivity.*")

        return "\n".join(parts)


# =============================================================================
# Convenience Functions
# =============================================================================

# Global client instance
_default_client: Optional[LLMClient] = None


def get_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Get or create default LLM client"""
    global _default_client
    if _default_client is None or config is not None:
        _default_client = LLMClient(config)
    return _default_client


async def explain_ecg(
    algorithm_results: Dict[str, Any],
    user_level: str = "resident",
    question: Optional[str] = None
) -> str:
    """
    Quick function to get ECG explanation.

    Args:
        algorithm_results: Results from ECG analysis
        user_level: "rmp", "student", "resident", or "cardiologist"
        question: Optional specific question

    Returns:
        Expert explanation
    """
    client = get_client()
    level = UserLevel(user_level.lower())
    return await client.analyze_async(algorithm_results, level, question)


def explain_ecg_sync(
    algorithm_results: Dict[str, Any],
    user_level: str = "resident",
    question: Optional[str] = None
) -> str:
    """Synchronous version of explain_ecg"""
    client = get_client()
    level = UserLevel(user_level.lower())
    return client.analyze(algorithm_results, level, question)


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    import asyncio

    # Test with sample data
    sample_results = {
        "measurements": {
            "heart_rate": 180,
            "rhythm": "wide_complex_tachycardia",
            "qrs_duration_ms": 158
        },
        "vt_svt": {
            "consensus": "VT",
            "confidence": 1.0,
            "agreement": {"agreement_level": "complete", "vt_count": 4},
            "individual_results": {
                "Brugada": {"conclusion": "VT", "confidence": 1.0},
                "Basel": {"conclusion": "VT", "confidence": 1.0},
                "Vereckei": {"conclusion": "VT", "confidence": 1.0},
                "Pava": {"conclusion": "VT", "confidence": 1.0}
            },
            "recommendation": "HIGH CONFIDENCE VT: Immediate treatment indicated."
        }
    }

    async def test():
        print("Testing LLM Client...\n")

        # Check if API key is available
        config = LLMConfig()
        if not config.api_key:
            print("No ANTHROPIC_API_KEY found. Testing fallback mode.\n")

        client = LLMClient(config)

        # Test different user levels
        for level in [UserLevel.RMP, UserLevel.CARDIOLOGIST]:
            print(f"\n{'='*60}")
            print(f"User Level: {level.value.upper()}")
            print('='*60)

            response = await client.analyze_async(
                sample_results,
                level,
                "What is the diagnosis and what should I do?"
            )
            print(response)

    asyncio.run(test())
