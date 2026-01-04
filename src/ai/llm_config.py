"""
LLM Configuration for ECG Guru

REALISTIC HARDWARE ASSUMPTIONS:
- Most Indian doctors use productivity laptops (4-16GB RAM, no dedicated GPU)
- Village RMPs may have basic laptops or phones (4GB RAM)
- Even cardiologists rarely have gaming/workstation hardware
- We optimize for RAM, not VRAM (most run on CPU)

Supports tiered LLM selection based on:
- Available system RAM (not GPU VRAM)
- Quantization level (Q4 for low RAM, Q8 for better quality)
- Medical accuracy requirements

IMPORTANT: The LLM does NOT make diagnoses.
Diagnoses come from validated, coded algorithms (Brugada, Basel, etc.).
The LLM provides:
- Explanations of algorithm results
- Teaching and education
- Conversational interface
- Report generation
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import subprocess
import os


class LLMBackend(Enum):
    """
    Available LLM backends optimized for doctor hardware.

    All models use quantization to run on standard laptops.
    Format: model:quantization (Q4 = 4-bit, smallest; Q8 = 8-bit, better quality)
    """

    # PRIMARY TARGETS: 4-8GB RAM laptops (most doctors)
    QWEN_3B_Q4 = "qwen2.5:3b-instruct-q4_K_M"     # 2GB RAM - phones, 4GB laptops
    PHI3_MINI_Q4 = "phi3:mini-4k-instruct-q4_0"   # 2GB RAM - fast, good reasoning
    GEMMA2_2B_Q4 = "gemma2:2b-instruct-q4_K_M"    # 1.5GB RAM - smallest viable

    # STANDARD: 8-12GB RAM laptops
    QWEN_7B_Q4 = "qwen2.5:7b-instruct-q4_K_M"     # 4.5GB RAM - good balance
    LLAMA3_8B_Q4 = "llama3.1:8b-instruct-q4_K_M"  # 5GB RAM - strong reasoning
    MISTRAL_7B_Q4 = "mistral:7b-instruct-q4_K_M"  # 4.5GB RAM - fast

    # QUALITY: 12-16GB RAM (better quality when available)
    QWEN_7B_Q8 = "qwen2.5:7b-instruct-q8_0"       # 8GB RAM - better quality
    LLAMA3_8B_Q8 = "llama3.1:8b-instruct-q8_0"    # 9GB RAM - best small model

    # MEDICAL SPECIALIZED (when RAM allows)
    # These are fine-tuned on medical data but need more resources
    MEDITRON_7B_Q4 = "meditron:7b-q4_K_M"         # 5GB RAM - medical fine-tuned
    MEDLLAMA_8B_Q4 = "medllama2:8b-q4_K_M"        # 5GB RAM - medical fine-tuned

    # CLOUD FALLBACK (when online, for complex cases)
    CLAUDE_HAIKU = "claude-3-haiku"               # Fast, cheap, good
    CLAUDE_SONNET = "claude-3-sonnet"             # Better quality

    # SERVER-SIDE MODELS (when running on your own server)
    # Since you control the server hardware, you can use larger models
    LLAMA3_70B_Q4 = "llama3.1:70b-instruct-q4_K_M"  # 40GB RAM - best quality
    QWEN_32B_Q4 = "qwen2.5:32b-instruct-q4_K_M"    # 20GB RAM - excellent
    MIXTRAL_8X7B_Q4 = "mixtral:8x7b-instruct-q4_K_M"  # 26GB RAM - fast MoE


@dataclass
class LLMConfig:
    """Configuration for LLM usage"""

    model: LLMBackend
    temperature: float = 0.3  # Low for medical accuracy
    max_tokens: int = 1024    # Reduced for speed on low-end hardware
    system_prompt: str = ""

    # Performance settings for low-end hardware
    num_ctx: int = 4096       # Reduced context for RAM savings
    num_thread: int = 4       # CPU threads (auto-detect better)
    use_mmap: bool = True     # Memory-map for lower RAM usage

    # Medical-specific settings
    require_citations: bool = True
    show_confidence: bool = True

    @property
    def is_medical_specialized(self) -> bool:
        """Check if this is a medical-specialized model"""
        return self.model in [
            LLMBackend.MEDITRON_7B_Q4,
            LLMBackend.MEDLLAMA_8B_Q4,
        ]

    @property
    def min_ram_gb(self) -> float:
        """Minimum RAM required for this model (in GB)"""
        ram_map = {
            # Tiny models (4GB laptops)
            LLMBackend.GEMMA2_2B_Q4: 2.0,
            LLMBackend.QWEN_3B_Q4: 2.5,
            LLMBackend.PHI3_MINI_Q4: 2.5,
            # Standard models (8GB laptops)
            LLMBackend.QWEN_7B_Q4: 5.0,
            LLMBackend.LLAMA3_8B_Q4: 5.5,
            LLMBackend.MISTRAL_7B_Q4: 5.0,
            LLMBackend.MEDITRON_7B_Q4: 5.0,
            LLMBackend.MEDLLAMA_8B_Q4: 5.5,
            # Quality models (12-16GB laptops)
            LLMBackend.QWEN_7B_Q8: 8.5,
            LLMBackend.LLAMA3_8B_Q8: 9.5,
        }
        return ram_map.get(self.model, 5.0)

    @property
    def is_quantized(self) -> bool:
        """Check if using quantized model"""
        return "q4" in self.model.value.lower() or "q8" in self.model.value.lower()


def detect_system_ram() -> float:
    """Detect available system RAM in GB"""
    try:
        # Linux
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    # Value is in KB
                    kb = int(line.split()[1])
                    return kb / (1024 * 1024)
    except:
        pass

    try:
        # macOS
        result = subprocess.run(
            ['sysctl', '-n', 'hw.memsize'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return int(result.stdout.strip()) / (1024 ** 3)
    except:
        pass

    try:
        # Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        c_ulonglong = ctypes.c_ulonglong
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', c_ulonglong),
                ('ullAvailPhys', c_ulonglong),
                ('ullTotalPageFile', c_ulonglong),
                ('ullAvailPageFile', c_ulonglong),
                ('ullTotalVirtual', c_ulonglong),
                ('ullAvailVirtual', c_ulonglong),
                ('ullAvailExtendedVirtual', c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys / (1024 ** 3)
    except:
        pass

    # Default assumption: 8GB (common laptop)
    return 8.0


def get_available_ram() -> float:
    """Get available (free) RAM in GB"""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemAvailable' in line:
                    kb = int(line.split()[1])
                    return kb / (1024 * 1024)
    except:
        pass

    # Estimate: 60% of total RAM available
    return detect_system_ram() * 0.6


def get_recommended_model(
    available_ram: float = None,
    prefer_medical: bool = True,
    prefer_speed: bool = False,
    allow_cloud: bool = False,
) -> LLMConfig:
    """
    Get the recommended LLM configuration based on actual doctor hardware.

    Args:
        available_ram: Available RAM in GB (auto-detect if None)
        prefer_medical: Prefer medical-specialized models when possible
        prefer_speed: Prefer faster responses over quality
        allow_cloud: Allow cloud models as fallback

    Returns:
        LLMConfig with recommended settings
    """
    if available_ram is None:
        available_ram = get_available_ram()

    # Leave headroom for OS and other apps (doctors multitask)
    usable_ram = available_ram * 0.7

    # Build preference order
    selected = None

    if usable_ram >= 8.0:
        # 12-16GB laptop: Use quality models
        if prefer_medical:
            selected = LLMBackend.MEDITRON_7B_Q4
        else:
            selected = LLMBackend.QWEN_7B_Q8

    elif usable_ram >= 5.0:
        # 8-12GB laptop: Standard quantized models
        if prefer_medical:
            selected = LLMBackend.MEDITRON_7B_Q4
        elif prefer_speed:
            selected = LLMBackend.MISTRAL_7B_Q4
        else:
            selected = LLMBackend.QWEN_7B_Q4

    elif usable_ram >= 3.0:
        # 4-8GB laptop: Small models
        if prefer_speed:
            selected = LLMBackend.GEMMA2_2B_Q4
        else:
            selected = LLMBackend.QWEN_3B_Q4

    else:
        # <4GB: Smallest viable or cloud
        if allow_cloud:
            selected = LLMBackend.CLAUDE_HAIKU
        else:
            selected = LLMBackend.GEMMA2_2B_Q4

    # Adjust context window based on RAM
    if usable_ram < 4.0:
        num_ctx = 2048
    elif usable_ram < 8.0:
        num_ctx = 4096
    else:
        num_ctx = 8192

    return LLMConfig(
        model=selected,
        temperature=0.3,
        max_tokens=1024 if usable_ram < 8.0 else 2048,
        num_ctx=num_ctx,
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

    # NOTE: These models are placeholders for future medical-specialized models
    # if model in [LLMBackend.OPENBIOLLM_70B, LLMBackend.OPENBIOLLM_8B]:
    #     return base_prompt + """
    #
    # You are powered by OpenBioLLM, a medical-specialized language model.
    # Use your medical training to provide accurate, detailed explanations."""
    #
    # elif model == LLMBackend.MMEDINS_LLAMA3:
    #     return base_prompt + """
    #
    # You are powered by MMedIns-Llama3, trained on medical instructions.
    # Provide clear, actionable medical explanations."""

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


# ============================================================================
# Server-Side Model Selection
# ============================================================================

def get_server_model(
    server_ram_gb: float = 32,
    prefer_medical: bool = True,
    prefer_speed: bool = False,
) -> LLMConfig:
    """
    Get recommended model for SERVER deployment.

    Since you control the server hardware, you can use larger, better models.
    Users access via web/mobile - they don't need local resources.

    Recommended server specs:
    - Basic: 16GB RAM → 7B models (good for small clinics)
    - Standard: 32GB RAM → 13B-32B models (most deployments)
    - High-end: 64GB+ RAM → 70B models (hospital/enterprise)
    """

    if server_ram_gb >= 48:
        # High-end server: Use the best
        if prefer_medical:
            selected = LLMBackend.MEDITRON_7B_Q4  # Would use medical 70B if available
        else:
            selected = LLMBackend.LLAMA3_70B_Q4
        num_ctx = 16384

    elif server_ram_gb >= 24:
        # Standard server: 32B class models
        selected = LLMBackend.QWEN_32B_Q4 if not prefer_speed else LLMBackend.MIXTRAL_8X7B_Q4
        num_ctx = 8192

    elif server_ram_gb >= 16:
        # Basic server: 7B-8B models
        if prefer_medical:
            selected = LLMBackend.MEDITRON_7B_Q4
        elif prefer_speed:
            selected = LLMBackend.MISTRAL_7B_Q4
        else:
            selected = LLMBackend.QWEN_7B_Q8
        num_ctx = 8192

    else:
        # Minimal server: Small models
        selected = LLMBackend.QWEN_7B_Q4
        num_ctx = 4096

    return LLMConfig(
        model=selected,
        temperature=0.3,
        max_tokens=2048,
        num_ctx=num_ctx,
        system_prompt=get_medical_system_prompt(selected),
    )


# ============================================================================
# Deployment Tiers
# ============================================================================

DEPLOYMENT_TIERS = {
    # For server deployments (web app backend)
    "server_basic": {
        "description": "Basic server - small clinic (16GB RAM)",
        "models": [LLMBackend.QWEN_7B_Q8, LLMBackend.MEDITRON_7B_Q4],
        "min_ram": 16,
    },
    "server_standard": {
        "description": "Standard server - hospital (32GB RAM)",
        "models": [LLMBackend.QWEN_32B_Q4, LLMBackend.MIXTRAL_8X7B_Q4],
        "min_ram": 32,
    },
    "server_enterprise": {
        "description": "Enterprise server - large hospital (64GB+ RAM)",
        "models": [LLMBackend.LLAMA3_70B_Q4],
        "min_ram": 64,
    },

    # For offline mobile app (on-device inference)
    "mobile_basic": {
        "description": "Basic phones - village RMP (4GB RAM)",
        "models": [LLMBackend.GEMMA2_2B_Q4],
        "min_ram": 4,
    },
    "mobile_standard": {
        "description": "Standard phones - most users (6-8GB RAM)",
        "models": [LLMBackend.QWEN_3B_Q4, LLMBackend.PHI3_MINI_Q4],
        "min_ram": 6,
    },
}
