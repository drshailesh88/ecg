# ECG Guru: Algorithm and Knowledge Base Specification

## Philosophy: Code What Can Be Coded, AI What Needs Intelligence

**Critical Insight from Research**: General-purpose vision LLMs (GPT-4o, Gemini, Claude) achieve only **30-66% accuracy** on ECG diagnosis, while specialized ECG AI achieves **97%+**.

We cannot rely on vision LLMs alone. Our approach:
1. **Programmatic Algorithms**: Implement validated algorithms as code (not AI prompts)
2. **Specialized Models**: Use/train ECG-specific vision models for waveform extraction
3. **LLM for Intelligence Layer**: Use LLMs for reasoning, explanation, conversation - not primary diagnosis
4. **Knowledge Base (RAG)**: Feed clinical knowledge into the reasoning layer

---

## Part 1: Validated Algorithms to Implement

### VT vs SVT (Wide Complex Tachycardia)

We implement ALL major validated algorithms programmatically:

| Algorithm | Accuracy | Year | Key Features |
|-----------|----------|------|--------------|
| **Brugada** | 89% sens, 59% spec | 1991 | 4-step, precordial analysis |
| **Vereckei (aVR)** | 69-94% | 2008 | Single lead (aVR) focused |
| **Basel** | 91-93% | 2022 | Fastest (36s), 3 simple criteria |
| **Pava (Lead II)** | 85%+ | 2010 | R-wave peak time in lead II |
| **Prelocalization Series** | 90% | 2025 | Newest, highest accuracy |

**Implementation Strategy**:
```python
class WCTDifferentiator:
    """Run all validated VT vs SVT algorithms"""

    def analyze(self, ecg_data: ECGData) -> WCTResult:
        results = {
            'brugada': self.run_brugada_algorithm(ecg_data),
            'vereckei': self.run_vereckei_algorithm(ecg_data),
            'basel': self.run_basel_algorithm(ecg_data),
            'pava': self.run_pava_algorithm(ecg_data),
            'prelocalization': self.run_prelocalization_algorithm(ecg_data),
        }

        # Ensemble scoring with weights based on validation strength
        vt_votes = sum(1 for r in results.values() if r.diagnosis == 'VT')
        confidence = self.calculate_ensemble_confidence(results)

        return WCTResult(
            diagnosis='VT' if vt_votes >= 3 else 'SVT_with_aberrancy',
            confidence=confidence,
            algorithm_details=results,
            clinical_guidance=self.generate_guidance(results)
        )
```

#### Brugada Algorithm (4 Steps)
```
Step 1: Absence of RS complex in all precordial leads? → VT
Step 2: RS interval >100ms in any precordial lead? → VT
Step 3: AV dissociation present? → VT
Step 4: Morphology criteria in V1/V2 and V6 for RBBB/LBBB patterns? → VT vs SVT
```

#### Vereckei aVR Algorithm (4 Steps)
```
Step 1: Initial dominant R wave in aVR? → VT
Step 2: Initial r or q >40ms in aVR? → VT
Step 3: Notching on initial downstroke in aVR? → VT
Step 4: Vi/Vt ratio ≤1 in aVR? → VT
```

#### Basel Algorithm (2022 - Fastest)
```
VT if ≥2 of:
1. Clinical high-risk features (age >55, known structural heart disease)
2. Lead II: time to first peak >40ms
3. Lead aVR: time to first peak >40ms
```

#### Pava Algorithm (Lead II R-wave Peak Time)
```
R-wave peak time in lead II:
- ≥50ms → VT
- <50ms → SVT with aberrancy
```

---

### SVT Classification and Localization

#### RP Interval Analysis
```python
class SVTClassifier:
    def classify(self, ecg_data: ECGData) -> SVTResult:
        rp_interval = self.measure_rp_interval(ecg_data)
        pr_interval = self.measure_pr_interval(ecg_data)

        if rp_interval < 70:  # milliseconds
            # Short RP tachycardia
            if self.detect_pseudo_r_prime_v1(ecg_data):
                return SVTResult('Typical AVNRT', confidence=0.85)
            else:
                return SVTResult('AVNRT vs AVRT', confidence=0.6)

        elif rp_interval < pr_interval:
            # Intermediate RP
            return SVTResult('Orthodromic AVRT likely', confidence=0.7)

        else:
            # Long RP tachycardia
            candidates = ['Atypical AVNRT', 'Atrial Tachycardia', 'PJRT']
            return SVTResult(candidates, confidence=0.5)
```

#### SVT Mechanism Features
| SVT Type | RP Interval | P-wave Location | Key ECG Features |
|----------|-------------|-----------------|------------------|
| **Typical AVNRT** | <70ms | Buried in QRS or pseudo-R' in V1 | Narrow QRS, pseudo-S in inferior leads |
| **Atypical AVNRT** | >70ms | Before QRS | Long RP tachycardia |
| **Orthodromic AVRT** | 70-120ms | After QRS | Narrow QRS, retrograde P visible |
| **Antidromic AVRT** | Variable | Dissociated or buried | Wide QRS, delta-like |
| **Atrial Tachycardia** | Variable | Before QRS, abnormal axis | P-wave morphology localizes focus |

---

### Accessory Pathway Localization (WPW)

Based on research, newer algorithms significantly outperform classics:

| Algorithm | Accuracy | Notes |
|-----------|----------|-------|
| **Arruda** | 53-75% | Classic, widely cited |
| **Taguchi** | ~60% | R/S ratio based |
| **Fitzpatrick** | 44-65% | Historical |
| **EASY-WPW** | 94% | 2023, superior to Arruda |
| **SMART-WPW** | 97% | 2025, best for adults & children |
| **AI-based (locAP)** | 95%+ | Deep learning approach |

**We implement SMART-WPW (2025) as primary, Arruda as secondary:**

```python
class PathwayLocalizer:
    def localize(self, ecg_data: ECGData) -> PathwayResult:
        # Primary: SMART-WPW (highest accuracy)
        smart_result = self.run_smart_wpw(ecg_data)

        # Secondary: Arruda (widely known, for reference)
        arruda_result = self.run_arruda_algorithm(ecg_data)

        # Tertiary: EASY-WPW
        easy_result = self.run_easy_wpw(ecg_data)

        return PathwayResult(
            primary_location=smart_result.location,
            confidence=smart_result.confidence,
            anatomical_region=self.map_to_anatomy(smart_result),
            ablation_guidance=self.generate_ablation_hints(smart_result),
            algorithm_comparison={
                'SMART-WPW': smart_result,
                'Arruda': arruda_result,
                'EASY-WPW': easy_result,
            }
        )
```

#### Pathway Location Categories
```
10-Location Model (Standard):
├── Left Lateral (LL)
├── Left Posterolateral (LPL)
├── Left Posterior (LP)
├── Left Posteroseptal (LPS)
├── Posteroseptal (PS)
├── Right Posteroseptal (RPS)
├── Right Posterior (RP)
├── Right Lateral (RL)
├── Right Anterolateral (RAL)
└── Anteroseptal (AS)

Simplified 5-Region Model:
├── Left Free Wall
├── Posteroseptal
├── Right Free Wall
├── Anteroseptal
└── Midseptal
```

---

### STEMI Localization and Culprit Vessel

#### Territory Localization
```python
class STEMILocalizer:
    def localize(self, ecg_data: ECGData) -> STEMIResult:
        st_elevations = self.detect_st_elevation(ecg_data)
        st_depressions = self.detect_st_depression(ecg_data)

        territory = self.determine_territory(st_elevations, st_depressions)
        culprit = self.predict_culprit_vessel(ecg_data, territory)

        return STEMIResult(
            territory=territory,
            culprit_vessel=culprit,
            confidence=culprit.confidence,
            high_risk_features=self.detect_high_risk(ecg_data),
            recommended_actions=self.generate_actions(territory)
        )
```

#### STEMI Territory Mapping
| Territory | ST Elevation Leads | Culprit Vessel | Key Differentiators |
|-----------|-------------------|----------------|---------------------|
| **Anterior** | V1-V4 | Proximal/Mid LAD | V1 ST↑ suggests proximal |
| **Anteroseptal** | V1-V3 | Septal branches | Isolated septal |
| **Anterolateral** | V1-V4, I, aVL | LAD or LCx | Lateral involvement |
| **Lateral** | I, aVL, V5-V6 | LCx or Diagonal | Isolated lateral rare |
| **Inferior** | II, III, aVF | RCA (70-90%) or LCx | See below |
| **Posterior** | V7-V9 (reciprocal V1-V3) | RCA or LCx | Tall R in V1-V2 |
| **RV** | V4R | Proximal RCA | With inferior STEMI |

#### Inferior STEMI: RCA vs LCx Differentiation
```python
def differentiate_rca_vs_lcx(ecg_data: ECGData) -> CulpritResult:
    """
    Best algorithms for RCA vs LCx in inferior STEMI:
    - Lead III ST > Lead II ST → RCA (PPV ~90%)
    - Lead I ST depression → RCA
    - Lead I ST elevation → LCx
    - Lead V1 ST elevation → RCA
    - Lead V1 ST depression → LCx

    New algorithm (2021): "III-II-I+aVF+V1>0.1mV" → 86% accuracy
    """

    st_iii = measure_st(ecg_data, 'III')
    st_ii = measure_st(ecg_data, 'II')
    st_i = measure_st(ecg_data, 'I')
    st_v1 = measure_st(ecg_data, 'V1')

    # Primary criteria
    if st_iii > st_ii:
        rca_score += 2
    if st_i < -0.05:  # ST depression in I
        rca_score += 1
    if st_v1 > 0.05:  # ST elevation in V1
        rca_score += 1

    return CulpritResult(
        vessel='RCA' if rca_score >= 2 else 'LCx',
        confidence=calculate_confidence(rca_score),
        criteria_used=criteria
    )
```

---

## Part 2: AI and Knowledge Architecture

### The Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ECG GURU AI STACK                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Layer 1: Image Processing (Specialized Vision)                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ECG Image → Lead Extraction → Waveform Digitization           │ │
│  │  (OpenCV + specialized ECG CNN, NOT general vision LLM)        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│  Layer 2: Signal Analysis (Programmatic Algorithms)                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Rate/Rhythm │ Intervals │ VT/SVT │ Pathway │ STEMI            │ │
│  │  (Code implementation of validated algorithms)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│  Layer 3: Clinical Reasoning (LLM + RAG)                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Algorithm Results + Knowledge Base → Clinical Interpretation   │ │
│  │  (Qwen/Ollama for explanation, teaching, conversation)         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│  Layer 4: User Interface (Flet)                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Chat Interface │ Visual Annotations │ Reports │ Teaching      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Approach?

| Component | Why Not General Vision LLM | Our Approach |
|-----------|---------------------------|--------------|
| **Lead Extraction** | GPT-4o can't reliably identify leads | OpenCV + CNN trained on ECG layouts |
| **Waveform Digitization** | LLMs hallucinate measurements | Signal processing algorithms |
| **Interval Measurement** | LLMs achieve ~66% accuracy | Digital caliper on extracted signal |
| **VT vs SVT** | LLMs don't apply algorithms correctly | Brugada/Vereckei/Basel in code |
| **Explanation/Teaching** | LLMs excel at this | Qwen with RAG |
| **Conversation** | LLMs excel at this | Qwen with context |

---

## Part 3: Knowledge Base Architecture

### Knowledge Sources to Embed

#### 1. Textbook Knowledge (RAG Embeddings)
```yaml
sources:
  textbooks:
    - "Marriott's Practical Electrocardiography"
    - "Chou's Electrocardiography in Clinical Practice"
    - "ECGs Made Easy"
    - "The ECG in Emergency Medicine"
    - "Arrhythmias (Josephson)"

  guidelines:
    - "ACC/AHA ECG Interpretation Guidelines"
    - "ESC Guidelines on SVT Management 2019"
    - "ESC Guidelines on Ventricular Arrhythmias 2022"

  algorithms:
    - "Brugada WCT Algorithm (1991)"
    - "Vereckei aVR Algorithm (2008)"
    - "Basel Algorithm (2022)"
    - "SMART-WPW Algorithm (2025)"
    - "Fiol's STEMI Localization"
```

#### 2. Structured Algorithm Database
```python
# algorithms.json - Machine-readable algorithm definitions
{
    "brugada_wct": {
        "name": "Brugada Algorithm for WCT",
        "year": 1991,
        "citation": "Brugada P, et al. Circulation 1991;83:1649-59",
        "sensitivity": 0.89,
        "specificity": 0.59,
        "steps": [
            {
                "number": 1,
                "question": "Is there absence of RS complex in all precordial leads?",
                "if_yes": "VT",
                "if_no": "proceed_to_step_2",
                "visual_hint": "Look at V1-V6 for any RS pattern"
            },
            # ... more steps
        ]
    }
}
```

#### 3. Case Library with Expert Annotations
```yaml
case_library:
  structure:
    - case_id: unique identifier
    - ecg_image: path to ECG
    - clinical_context: patient demographics, symptoms
    - expert_interpretation: gold-standard diagnosis
    - teaching_points: key learning objectives
    - difficulty_level: beginner/intermediate/advanced/expert
    - tags: [STEMI, inferior, RCA, etc.]

  sources:
    - PhysioNet PTB-XL database (21,837 ECGs with labels)
    - Dr. Smith's ECG Blog cases (curated)
    - ECGpedia teaching cases
    - Custom curated cases with EP validation
```

### How the LLM Learns (RAG Pipeline)

```python
class ECGKnowledgeBase:
    def __init__(self):
        self.chroma = chromadb.Client()
        self.collection = self.chroma.create_collection("ecg_knowledge")

    def embed_knowledge(self):
        """Embed all knowledge sources into vector DB"""

        # Embed textbook chapters
        for chapter in self.load_textbook_chapters():
            self.collection.add(
                documents=[chapter.text],
                metadatas=[{"source": chapter.source, "topic": chapter.topic}],
                ids=[chapter.id]
            )

        # Embed algorithm explanations
        for algo in self.load_algorithms():
            self.collection.add(
                documents=[algo.detailed_explanation],
                metadatas=[{"type": "algorithm", "name": algo.name}],
                ids=[algo.id]
            )

        # Embed case teaching points
        for case in self.load_cases():
            self.collection.add(
                documents=[case.teaching_narrative],
                metadatas=[{"type": "case", "diagnosis": case.diagnosis}],
                ids=[case.id]
            )

    def query(self, question: str, context: dict) -> str:
        """Retrieve relevant knowledge for a question"""

        results = self.collection.query(
            query_texts=[question],
            n_results=5,
            where={"topic": {"$in": context.get("relevant_topics", [])}}
        )

        return self.format_context(results)
```

### Prompt Engineering for Clinical Reasoning

```python
ECG_ANALYSIS_PROMPT = """
You are an expert electrophysiologist with 20 years of experience.
You are helping a {user_level} interpret an ECG.

## ECG Measurements (from algorithm analysis):
{algorithm_results}

## Relevant Clinical Knowledge:
{rag_context}

## User Question:
{user_question}

## Instructions:
1. Base your response on the algorithm results provided - these are accurate measurements
2. Use the clinical knowledge to explain the significance
3. Adjust your explanation depth for a {user_level}:
   - RMP: Simple verdict, red flags, referral guidance
   - MBBS student: Educational explanation with basics
   - Cardiology resident: Differential diagnosis, detailed analysis
   - Cardiologist/EP: Expert-level discussion, nuances
4. If the algorithms disagree, explain the uncertainty
5. Always provide clinical action guidance
6. Never make up measurements - only use what's provided

## Response:
"""
```

---

## Part 4: Vision Model Strategy

### Tiered Approach Based on Research

Given that general vision LLMs achieve only 30-66% accuracy on ECG diagnosis:

#### Tier 1: Primary Analysis (Local, Specialized)
```yaml
purpose: Lead extraction, waveform digitization, measurement
models:
  - Custom CNN for ECG lead detection (train or find pre-trained)
  - OpenCV for grid detection and calibration
  - Signal processing for waveform extraction

why_not_llm:
  - Need pixel-level accuracy
  - LLMs hallucinate measurements
  - Must work offline
```

#### Tier 2: Pattern Recognition (Local, Semi-Specialized)
```yaml
purpose: Initial pattern classification to guide algorithm selection
models:
  - Fine-tuned vision model on ECG patterns
  - Options: Fine-tune Qwen-VL, MiniCPM-V, or CogVLM
  - PTB-XL dataset for training (21,837 labeled ECGs)

why_not_general_llm:
  - Need consistent, reproducible results
  - GPT-4o accuracy too low for clinical use
```

#### Tier 3: Reasoning and Explanation (Local LLM)
```yaml
purpose: Clinical reasoning, explanation, conversation
models:
  - Ollama + Qwen 2.5 (7B or 14B based on device)
  - With RAG from knowledge base

why_llm_works_here:
  - Input is structured (algorithm results), not raw image
  - LLMs excel at explanation and teaching
  - Can handle nuance and conversation
```

#### Tier 4: Premium/Online (Optional Enhancement)
```yaml
purpose: Complex cases, second opinion, latest knowledge
models:
  - Claude 3.5 Sonnet or GPT-4o via API
  - For cases where local models are uncertain

constraints:
  - Requires internet
  - User consent for data transmission
  - Never primary diagnosis - only enhancement
```

### Specialized ECG Model Options

Based on research, we should evaluate:

| Model | Type | Accuracy | Notes |
|-------|------|----------|-------|
| **ECG Buddy** | Proprietary | 97% | Reference benchmark |
| **PTB-XL trained CNN** | Open | 80-90% | Can train ourselves |
| **ECG-GPT** | Research | ~85% | ECG-specific LLM |
| **MedViLL** | Research | Variable | Medical vision-language |

**Recommendation**:
1. Start with PTB-XL trained CNN for pattern classification
2. Use programmatic algorithms for measurements
3. Use Qwen + RAG for reasoning
4. Evaluate accuracy, iterate

---

## Part 5: Data Sources for Training/Validation

### Open ECG Databases

| Database | Size | Labels | Use |
|----------|------|--------|-----|
| **PTB-XL** | 21,837 | Multi-label diagnoses | Primary training |
| **PhysioNet MIT-BIH** | 48 | Arrhythmia annotations | Arrhythmia training |
| **Chapman-Shaoxing** | 10,646 | 11 rhythms | Rhythm training |
| **CPSC 2018** | 6,877 | 9 classes | Validation |
| **Georgia** | 10,344 | Multi-label | Validation |

### Custom Curation Required

For advanced features (pathway localization, VT origin), we need:
- EP study correlation data
- Expert-annotated complex arrhythmias
- Pre/post ablation ECG pairs

**Strategy**: Partner with EP labs or use published case series

---

## Implementation Priority

1. **Phase 1**: Programmatic algorithms (VT/SVT, STEMI localization)
2. **Phase 2**: Lead extraction and digitization pipeline
3. **Phase 3**: RAG knowledge base with reasoning LLM
4. **Phase 4**: Specialized ECG pattern recognition model
5. **Phase 5**: Pathway localization with SMART-WPW
6. **Phase 6**: Premium cloud enhancement (optional)

---

## References

### VT vs SVT Algorithms
- [Basel Algorithm (2022) - JACC: Clinical Electrophysiology](https://www.jacc.org/doi/10.1016/j.jacep.2022.03.017)
- [Prelocalization Series Algorithm (2025) - BMC Cardiovascular](https://link.springer.com/article/10.1186/s12872-025-04583-1)
- [WCT Algorithm Review - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4040878/)
- [VT vs SVT - LITFL ECG Library](https://litfl.com/vt-versus-svt-ecg-library/)

### Pathway Localization
- [SMART-WPW Algorithm (2025) - Heart Rhythm](https://www.heartrhythmjournal.com/article/S1547-5271(25)02406-3/fulltext)
- [EASY-WPW Algorithm - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9935024/)
- [Pathway Algorithm Accuracy - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9776491/)
- [AI Pathway Localization - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8509837/)

### STEMI Localization
- [ECG Localization of MI - ECGWaves](https://ecgwaves.com/topic/localization-localize-myocardial-infarction-ischemia-coronary-artery-occlusion-culprit-stemi/)
- [RCA vs LCx Algorithms - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9884921/)
- [Deep Learning STEMI Detection - Frontiers](https://www.frontiersin.org/journals/cardiovascular-medicine/articles/10.3389/fcvm.2022.797207/full)

### Vision Model Performance
- [LLM vs Specialized ECG AI - JMIR AI](https://ai.jmir.org/2025/1/e75910)
- [GPT-4o ECG Performance - JMIR AI](https://ai.jmir.org/2025/1/e74426/)
- [Vision Models Medical Grounding - arXiv](https://arxiv.org/html/2511.19220)
