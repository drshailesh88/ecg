# ECG Guru - AI Development Directives

## Project Identity
**ECG Guru** - An AI-powered ECG analysis and teaching platform that puts a seasoned electrophysiologist in every practitioner's pocket.

## Development Toolkit (ALWAYS USE)

### 1. Spec-Kit (Specification-Driven Development)
- **Repository**: https://github.com/github/spec-kit
- **Install**: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- **Initialize**: `specify init <project-name> --ai claude`
- **Core Commands**:
  - `/speckit.constitution` - Define project principles
  - `/speckit.specify` - Describe requirements
  - `/speckit.plan` - Create technical implementation strategies
  - `/speckit.tasks` - Generate actionable task lists
  - `/speckit.implement` - Execute the full build
- **Philosophy**: Specifications become executable. Write specs first, then generate code.

### 2. Ralph Wiggum (Iterative AI Development)
- **Repository**: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- **Core Commands**:
  - `/ralph-loop "task" --completion-promise "DONE" --max-iterations 50` - Start iterative loop
  - `/cancel-ralph` - Terminate active loop
- **Use For**: Well-defined tasks with automatic verification (tests, linters), greenfield projects requiring iteration
- **Avoid For**: Tasks needing human judgment, production debugging

## Ecosystem Integration

This project integrates with the DocAssist suite:

| Product | Repository | Technology | Integration Point |
|---------|-----------|------------|-------------------|
| **EMR** | github.com/drshailesh88/emr | Python/Flet/Ollama/Chroma | Patient records, RAG context |
| **Appointments** | github.com/drshailesh88/appointment_system | FastAPI/Flet/SQLite | Scheduling, patient registry |
| **Academic Writing** | github.com/drshailesh88/cursor_for_academic_writing | Next.js/Firebase/Vercel AI | Case study documentation |
| **Dora** | github.com/drshailesh88/Dora | Medical RAG | Guidelines, treatment protocols |

### Shared Architecture Principles
1. **Offline-First**: Must work without internet (village RMPs, tier-3 cities)
2. **Local AI**: Ollama with Qwen models for inference
3. **SQLite + Chroma**: Consistent data layer across products
4. **Flet UI**: Cross-platform Python UI framework
5. **Privacy-First**: All patient data stays local

## Target Users (Multi-Tier)

```
Tier 1: RMPs & Village Practitioners
├── Need: Is this normal or abnormal? Does this need referral?
├── Output: Simple verdicts with red flags

Tier 2: MBBS Students & Residents
├── Need: Learn ECG interpretation, understand components
├── Output: Educational explanations, component identification

Tier 3: MD/DM Cardiology Residents
├── Need: Differential diagnosis, arrhythmia analysis
├── Output: Detailed analysis, pathway localization hints

Tier 4: Practicing Cardiologists & Electrophysiologists
├── Need: Complex arrhythmia analysis, pathway localization
├── Output: Expert-level differentials (SVT vs VT, AVRT pathway origin)
```

## ECG Analysis Capabilities (Target)

### Basic Analysis
- [ ] P-wave identification and morphology
- [ ] PR interval measurement
- [ ] QRS complex analysis
- [ ] ST segment evaluation
- [ ] T-wave assessment
- [ ] QT/QTc calculation
- [ ] Axis determination
- [ ] Rate and rhythm identification

### Intermediate Analysis
- [ ] Chamber enlargement detection
- [ ] Bundle branch blocks
- [ ] Ischemic changes (STEMI/NSTEMI patterns)
- [ ] Electrolyte abnormalities
- [ ] Drug effects (digoxin, antiarrhythmics)

### Advanced Analysis (Differentiators)
- [ ] Wide complex tachycardia differentiation (SVT with aberrancy vs VT)
- [ ] SVT subtype classification (AVNRT, AVRT, AT)
- [ ] Accessory pathway localization algorithms
- [ ] Brugada pattern recognition
- [ ] ARVC criteria
- [ ] Pre-excitation patterns
- [ ] Complex arrhythmia mechanism analysis

## Core Features

### 1. ECG Chat ("Talk to your ECG")
- Upload ECG image (photo, scan, PDF)
- Natural language questions about the ECG
- Progressive disclosure based on user level
- Teaching mode with explanations

### 2. Structured Analysis Report
- Systematic component-by-component analysis
- Confidence scores for findings
- Differential diagnoses with reasoning
- Red flags and urgency indicators

### 3. Educational Mode
- Interactive tutorials on ECG interpretation
- Case-based learning with real ECGs
- Progressive difficulty levels
- Spaced repetition for retention

### 4. Integration APIs
- EMR integration for patient context
- Dora integration for guideline references
- Export to clinical documentation

## Critical AI Architecture Decision

**RESEARCH FINDING**: General vision LLMs (GPT-4o, Gemini, Claude) achieve only **30-66% accuracy** on ECG diagnosis. Specialized ECG AI achieves **97%+**. We cannot rely on general vision LLMs.

### Our Hybrid Approach: Code + Specialized AI + LLM

```
Layer 1: Image Processing (Specialized, NOT General LLM)
├── OpenCV + Custom CNN for lead detection
├── Signal processing for waveform digitization
└── Pixel-level accuracy required

Layer 2: Diagnosis (Programmatic Algorithms in Code)
├── VT vs SVT: Brugada, Vereckei, Basel, Pava (coded)
├── STEMI: Fiol's algorithm, RCA/LCx differentiation (coded)
├── Pathway: SMART-WPW, Arruda (coded)
└── Measurements: Digital caliper on extracted signal

Layer 3: Reasoning (LLM + RAG)
├── Input: Algorithm results (not raw image)
├── Knowledge: RAG from textbooks, guidelines, cases
├── Output: Explanation, teaching, conversation
└── Model: Qwen 2.5 via Ollama (local)
```

## Validated Algorithms to Implement

### VT vs SVT (Wide Complex Tachycardia)
| Algorithm | Accuracy | Year | Implementation |
|-----------|----------|------|----------------|
| **Brugada** | 89% sens | 1991 | 4-step precordial |
| **Vereckei** | 69-94% | 2008 | aVR single-lead |
| **Basel** | 91-93% | 2022 | Fastest, 3 criteria |
| **Pava** | 85%+ | 2010 | Lead II R-peak time |

### Accessory Pathway Localization
| Algorithm | Accuracy | Priority |
|-----------|----------|----------|
| **SMART-WPW** | 97% | Primary (2025, best) |
| **EASY-WPW** | 94% | Secondary (2023) |
| **Arruda** | 53-75% | Reference (classic) |

### STEMI Localization
- Anterior (LAD): V1-V4
- Inferior (RCA/LCx): II, III, aVF + differentiation algorithms
- Lateral (LCx): I, aVL, V5-V6
- RCA vs LCx: "III-II-I+aVF+V1" algorithm (86% accuracy)

### SVT Classification
- RP interval analysis (<70ms = AVNRT, >70ms = AVRT/AT)
- P-wave morphology for AT localization
- Machine learning for mechanism (91.7% AVNRT, 78.4% AVRT sensitivity)

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ECG Guru Application                     │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (Flet)                                            │
│  ├── ECG Upload/Capture                                     │
│  ├── Chat Interface                                         │
│  ├── Analysis Dashboard                                     │
│  └── Learning Module                                        │
├─────────────────────────────────────────────────────────────┤
│  Core Engine (Programmatic - NOT LLM)                       │
│  ├── Image Preprocessing (OpenCV/PIL)                       │
│  ├── Lead Detection (Custom CNN)                            │
│  ├── Waveform Digitization (Signal Processing)              │
│  ├── Interval Measurement (Digital Caliper)                 │
│  └── Algorithm Engine (Brugada, Basel, SMART-WPW, etc.)    │
├─────────────────────────────────────────────────────────────┤
│  AI Layer (LLM for Reasoning Only)                          │
│  ├── Qwen 2.5 via Ollama (reasoning, explanation)          │
│  ├── RAG Pipeline (clinical knowledge)                      │
│  └── NOT used for primary diagnosis                         │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Base (ChromaDB)                                  │
│  ├── Textbooks: Marriott, Chou, ECGs Made Easy             │
│  ├── Guidelines: ACC/AHA, ESC SVT 2019, ESC VA 2022        │
│  ├── Algorithms: Machine-readable definitions               │
│  └── Cases: PTB-XL (21,837), curated teaching cases        │
├─────────────────────────────────────────────────────────────┤
│  Integration Layer                                          │
│  ├── EMR Connector                                          │
│  ├── Dora API                                               │
│  └── Export Services                                        │
└─────────────────────────────────────────────────────────────┘
```

## Vision Model Strategy

**DO NOT use general vision LLMs (GPT-4V, Claude, Gemini) for diagnosis.**

| Task | Approach | Why |
|------|----------|-----|
| Lead Detection | Custom CNN + OpenCV | Pixel-level accuracy needed |
| Measurements | Signal processing | LLMs hallucinate numbers |
| Pattern Classification | Fine-tuned on PTB-XL | Need specialized training |
| Diagnosis | Coded algorithms | Validated, reproducible |
| Explanation | Qwen + RAG | LLMs excel here |

### Training Data Sources
- **PTB-XL**: 21,837 ECGs with multi-label diagnoses
- **PhysioNet MIT-BIH**: Arrhythmia annotations
- **Chapman-Shaoxing**: 10,646 ECGs, 11 rhythms
- **Custom**: EP-correlated pathway cases (partner with EP labs)

## Development Philosophy: Launch to Win

**We don't build MVPs. We build category-defining products.**

Delete "minimum viable" from your vocabulary. We're building the app that:
- Makes PM Cardio look like a toy
- Gets 5-star reviews from day one
- Becomes the recommendation every cardiologist gives their juniors
- Is the app every medical student downloads before their medicine posting

### The "Holy Shit" Moments We're Creating

1. **Instant Expert Analysis**: Not "might be abnormal" but analysis that sounds like a 20-year EP veteran
2. **Algorithm Engine**: Run 5 validated VT/SVT algorithms with step-by-step visual explanation
3. **Pathway Localization**: Map accessory pathways like an EP lab
4. **Teaching That Actually Teaches**: Interactive walkthrough like your favorite professor
5. **Natural Conversation**: Chat like a colleague, not a robot
6. **Critical Alerts**: STEMI detection with action steps, not just labels

### Launch Requirements (Non-Negotiable)

Before launch, ALL must be true:
- [ ] STEMI detection: 99%+ sensitivity (lives depend on this)
- [ ] STEMI localization: Anterior/Inferior/Lateral/Posterior with culprit vessel (LAD/RCA/LCx)
- [ ] VT vs SVT: Brugada, Vereckei, Basel, Pava algorithms (ensemble)
- [ ] SVT classification: AVNRT vs AVRT vs AT with RP interval analysis
- [ ] WPW pathway localization: SMART-WPW (97%) + EASY-WPW + Arruda
- [ ] Photo to analysis: <7 seconds on mid-range phone
- [ ] 50+ curated teaching cases with interactive walkthrough
- [ ] Works completely offline (specialized models, not cloud LLMs)
- [ ] Tested with 500+ real ECGs, reviewed by 3+ cardiologists
- [ ] 4.5+ star rating in beta feedback

## File Structure Convention

```
/home/user/ecg/
├── .specify/                    # Spec-kit specifications
│   ├── constitution.md
│   ├── requirements/
│   ├── plans/
│   └── tasks/
├── src/
│   ├── ui/                      # Flet UI components
│   ├── core/                    # ECG processing engine
│   ├── ai/                      # AI/ML models and pipelines
│   ├── knowledge/               # Knowledge base management
│   └── integrations/            # External system connectors
├── tests/
├── docs/
├── data/
│   ├── sample_ecgs/
│   └── knowledge_base/
├── CLAUDE.md                    # This file (AI directives)
├── README.md
├── requirements.txt
└── pyproject.toml
```

## Quality Standards

1. **Accuracy**: Medical-grade accuracy is paramount. When uncertain, say so.
2. **Safety**: Always include appropriate disclaimers. Never replace clinical judgment.
3. **Explainability**: Every diagnosis must be explainable with evidence.
4. **Accessibility**: Must work on low-end devices, poor connectivity.
5. **Privacy**: Zero data leaves the device without explicit consent.

## Competitive Differentiation vs PM Cardio

| Aspect | PM Cardio | ECG Guru |
|--------|-----------|----------|
| Target | Beginners | All levels (RMP to EP) |
| Depth | Basic interpretation | Pathway localization, mechanism analysis |
| Teaching | Limited | Comprehensive educational mode |
| Integration | Standalone | EMR, Dora, full DocAssist suite |
| Offline | Unknown | Full offline capability |
| Localization | Global | India-first (Hindi support planned) |

## Commands for This Project

When working on ECG Guru, always:
1. Use spec-kit for any new feature specification
2. Use ralph-loop for iterative implementation tasks
3. Maintain offline-first architecture
4. Consider all 4 user tiers in design decisions
5. Integrate with DocAssist ecosystem where applicable

## Remember

> "I want a cardiologist with years of practice of electrophysiology living inside mobile devices of every practitioner that is seeing patients who are coming with their ECGs."

This is the north star. Every feature, every decision should bring us closer to this vision.
