"""
LLM Configuration for ECG Guru

Supports tiered LLM selection based on:
- Available hardware (GPU VRAM)
- Medical accuracy requirements
- Offline capability needs

IMPORTANT: The LLM does NOT make diagnoses.
Diagnoses come from validated, coded algorithms (Brugada, Basel, etc.).
The LLM provides:
- Explanations of algorithm results
- Teaching and education
- Conversational interface
- Report generation

For safety-critical applications, we use medical-specific LLMs that
understand clinical terminology and reasoning patterns better.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import subprocess
import json


class LLMBackend(Enum):
    """Available LLM backends"""

    # Medical-specialized (highest quality for medical reasoning)
    OPENBIOLLM_70B = "openbiollm:70b"  # Best medical, needs 48GB VRAM
    OPENBIOLLM_8B = "openbiollm:8b"    # Good medical, 12GB VRAM

    # Medical instruction-tuned
    MMEDINS_LLAMA3 = "mmedins-llama3:8b"  # Multilingual medical, 12GB VRAM

    # General purpose with medical capability
    LLAMA3_70B = "llama3.1:70b"   # Strong reasoning, 48GB VRAM
    LLAMA3_8B = "llama3.1:8b"     # Good balance, 12GB VRAM

    # Lightweight (works on most devices)
    QWEN_7B = "qwen2.5:7b"        # Default, 8GB VRAM
    QWEN_3B = "qwen2.5:3b"        # Ultra-light, 4GB VRAM
    PHI3_MINI = "phi3:mini"       # 4GB VRAM, fast

    # Cloud options (when offline not required)
    CLAUDE = "claude-3-sonnet"    # Via API
    GPT4 = "gpt-4-turbo"          # Via API


@dataclass
class LLMConfig:
    """Configuration for LLM usage"""

    model: LLMBackend
    temperature: float = 0.3  # Low for medical accuracy
    max_tokens: int = 2048
    system_prompt: str = ""

    # Performance settings
    num_ctx: int = 8192  # Context window
    num_gpu: int = -1    # GPU layers (-1 = auto)

    # Medical-specific settings
    require_citations: bool = True  # Always cite sources
    show_confidence: bool = True    # Show confidence scores

    @property
    def is_medical_specialized(self) -> bool:
        """Check if this is a medical-specialized model"""
        return self.model in [
            LLMBackend.OPENBIOLLM_70B,
            LLMBackend.OPENBIOLLM_8B,
            LLMBackend.MMEDINS_LLAMA3,
        ]

    @property
    def min_vram_gb(self) -> int:
        """Minimum VRAM required for this model"""
        vram_map = {
            LLMBackend.OPENBIOLLM_70B: 48,
            LLMBackend.LLAMA3_70B: 48,
            LLMBackend.OPENBIOLLM_8B: 12,
            LLMBackend.MMEDINS_LLAMA3: 12,
            LLMBackend.LLAMA3_8B: 12,
            LLMBackend.QWEN_7B: 8,
            LLMBackend.QWEN_3B: 4,
            LLMBackend.PHI3_MINI: 4,
        }
        return vram_map.get(self.model, 8)


def detect_gpu_vram() -> int:
    """Detect available GPU VRAM in GB"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Get total VRAM in MB, convert to GB
            vram_mb = int(result.stdout.strip().split('\n')[0])
            return vram_mb // 1024
    except:
        pass

    # Try ROCm for AMD GPUs
    try:
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram", "--json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Extract VRAM (implementation depends on rocm-smi output format)
            return 8  # Default assumption for ROCm
    except:
        pass

    # No GPU detected, use CPU-friendly models
    return 0


def get_recommended_model(
    available_vram: int = None,
    require_medical: bool = True,
    require_offline: bool = True,
    prefer_speed: bool = False,
) -> LLMConfig:
    """
    Get the recommended LLM configuration based on hardware and requirements.

    Args:
        available_vram: GPU VRAM in GB (auto-detect if None)
        require_medical: Prefer medical-specialized models
        require_offline: Must work offline (via Ollama)
        prefer_speed: Prefer faster responses over quality

    Returns:
        LLMConfig with recommended settings
    """
    if available_vram is None:
        available_vram = detect_gpu_vram()

    # Build preference order based on requirements
    preferences = []

    if require_medical:
        if available_vram >= 48:
            preferences.append(LLMBackend.OPENBIOLLM_70B)
        if available_vram >= 12:
            preferences.append(LLMBackend.OPENBIOLLM_8B)
            preferences.append(LLMBackend.MMEDINS_LLAMA3)

    # General purpose fallbacks
    if available_vram >= 48:
        preferences.append(LLMBackend.LLAMA3_70B)
    if available_vram >= 12:
        preferences.append(LLMBackend.LLAMA3_8B)
    if available_vram >= 8:
        preferences.append(LLMBackend.QWEN_7B)
    if available_vram >= 4 or prefer_speed:
        preferences.append(LLMBackend.QWEN_3B)
        preferences.append(LLMBackend.PHI3_MINI)

    # Default to smallest model if nothing else works
    if not preferences:
        preferences.append(LLMBackend.QWEN_3B)

    selected = preferences[0]

    return LLMConfig(
        model=selected,
        temperature=0.3,
        max_tokens=2048,
        system_prompt=get_medical_system_prompt(selected),
    )


def get_medical_system_prompt(model: LLMBackend) -> str:
    """Get the appropriate system prompt for medical reasoning"""

    base_prompt = """You are an expert clinical cardiologist and electrophysiologist assistant for ECG Guru, an AI-powered ECG analysis platform.

CRITICAL SAFETY RULES:
1. You EXPLAIN findings - you do NOT make diagnoses. Diagnoses come from validated algorithms.
2. Always cite your knowledge sources when explaining.
3. If uncertain, say so explicitly. Never guess on safety-critical findings.
4. Always recommend correlation with clinical context.
5. Highlight any findings that require urgent attention.

Your role is to:
- Explain ECG findings in language appropriate for the user's level
- Teach ECG interpretation concepts
- Provide clinical context for algorithm results
- Answer questions about cardiology and electrophysiology
- Generate clear, accurate reports

Remember: Patient safety is paramount. When in doubt, err on the side of caution."""

    if model in [LLMBackend.OPENBIOLLM_70B, LLMBackend.OPENBIOLLM_8B]:
        return base_prompt + """

You are powered by OpenBioLLM, a medical-specialized language model.
Use your medical training to provide accurate, detailed explanations."""

    elif model == LLMBackend.MMEDINS_LLAMA3:
        return base_prompt + """

You are powered by MMedIns-Llama3, trained on medical instructions.
Provide clear, actionable medical explanations."""

    return base_prompt


def check_model_available(model: LLMBackend) -> bool:
    """Check if a model is available in Ollama"""
    try:
        import ollama
        models = ollama.list()
        model_names = [m['name'].split(':')[0] for m in models.get('models', [])]
        target = model.value.split(':')[0]
        return target in model_names
    except:
        return False


def create_llm_client(config: LLMConfig = None):
    """
    Create an LLM client based on configuration.

    Returns an Ollama client configured for the selected model.
    """
    if config is None:
        config = get_recommended_model()

    try:
        import ollama

        # Check if model is available
        if not check_model_available(config.model):
            print(f"Model {config.model.value} not found. Pulling...")
            ollama.pull(config.model.value)

        return OllamaLLMClient(config)
    except ImportError:
        raise ImportError("ollama package required. Install with: pip install ollama")


class OllamaLLMClient:
    """Wrapper for Ollama client with ECG Guru configuration"""

    def __init__(self, config: LLMConfig):
        import ollama
        self.client = ollama
        self.config = config
        self.model_name = config.model.value

    def generate(
        self,
        prompt: str,
        context: str = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Generate a response with optional RAG context"""

        full_prompt = prompt
        if context:
            full_prompt = f"""Use the following context to inform your response:

<context>
{context}
</context>

User question: {prompt}

Provide a detailed, accurate response based on the context above."""

        response = self.client.generate(
            model=self.model_name,
            prompt=full_prompt,
            system=self.config.system_prompt,
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "num_ctx": self.config.num_ctx,
            },
            stream=stream,
        )

        return response

    def chat(
        self,
        messages: list,
        context: str = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Chat interface with conversation history"""

        system_msg = self.config.system_prompt
        if context:
            system_msg += f"\n\nRelevant knowledge:\n{context}"

        full_messages = [{"role": "system", "content": system_msg}] + messages

        response = self.client.chat(
            model=self.model_name,
            messages=full_messages,
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "num_ctx": self.config.num_ctx,
            },
            stream=stream,
        )

        return response


# Tier definitions for user selection
QUALITY_TIERS = {
    "expert": {
        "description": "Highest quality - for cardiologists with high-end GPU (48GB+ VRAM)",
        "models": [LLMBackend.OPENBIOLLM_70B, LLMBackend.LLAMA3_70B],
        "min_vram": 48,
    },
    "standard": {
        "description": "Excellent quality - for most users with decent GPU (12GB+ VRAM)",
        "models": [LLMBackend.OPENBIOLLM_8B, LLMBackend.MMEDINS_LLAMA3],
        "min_vram": 12,
    },
    "lite": {
        "description": "Good quality - works on most devices (8GB+ VRAM)",
        "models": [LLMBackend.QWEN_7B, LLMBackend.LLAMA3_8B],
        "min_vram": 8,
    },
    "ultra_lite": {
        "description": "Basic quality - for low-end devices (4GB+ VRAM or CPU)",
        "models": [LLMBackend.QWEN_3B, LLMBackend.PHI3_MINI],
        "min_vram": 4,
    },
}
