# ECG Guru Implementation Plan

## Executive Summary

Build ECG Guru in 4 phases over iterative development cycles, using spec-kit for specifications and ralph-loop for implementation. Start with a functional MVP that proves the core value proposition, then layer on the differentiating features that will make this the go-to tool for all ECG practitioners.

---

## Phase 1: Foundation MVP

### Objective
Deliver a working ECG analysis app that accepts ECG images and provides useful interpretation through a chat interface.

### Key Deliverables
1. Flet-based cross-platform UI
2. ECG image upload (file, camera, clipboard)
3. Basic analysis via vision-capable LLM
4. Chat interface for Q&A
5. Structured report generation
6. Complete offline operation

### Technical Approach

#### 1.1 Project Setup
```
Tasks:
- Initialize Python project with pyproject.toml
- Set up Flet application scaffold
- Configure Ollama integration
- Create development environment
- Set up testing framework (pytest)
```

#### 1.2 UI Foundation
```
Tasks:
- Main application window with responsive layout
- ECG upload panel (drag-drop, file picker, camera)
- ECG display panel with zoom/pan
- Chat panel with message history
- Analysis report panel
- Settings/preferences panel
```

#### 1.3 ECG Input Pipeline
```
Tasks:
- Image loading and validation
- Quality assessment (blur, completeness)
- Image preprocessing (rotation correction, contrast)
- Thumbnail generation
- Image caching for session
```

#### 1.4 AI Integration
```
Tasks:
- Ollama client wrapper
- Vision model integration (LLaVA or similar)
- Prompt engineering for ECG analysis
- Response parsing and structuring
- Fallback handling for model failures
```

#### 1.5 Analysis Engine
```
Tasks:
- Structured analysis prompt template
- Rate/rhythm extraction
- Interval measurement parsing
- Abnormality detection
- Confidence scoring
- Report generation
```

#### 1.6 Chat Interface
```
Tasks:
- Conversation state management
- Context injection (ECG + previous responses)
- User level detection/setting
- Response formatting (markdown to UI)
- Follow-up question handling
```

#### 1.7 Offline Capability
```
Tasks:
- Local model serving verification
- Knowledge base embedding in app
- Cache management
- Offline mode detection and UI
```

### Phase 1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flet Application                      │
├──────────────┬──────────────┬──────────────┬────────────┤
│ Upload Panel │ Display Panel │ Chat Panel   │ Report     │
└──────────────┴──────────────┴──────────────┴────────────┘
        │                              │             │
        ▼                              ▼             ▼
┌─────────────────────────────────────────────────────────┐
│                   Core Engine                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │
│  │  Image    │  │  Analysis │  │  Chat             │   │
│  │  Pipeline │  │  Engine   │  │  Manager          │   │
│  └───────────┘  └───────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   AI Layer                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Ollama Client                         │  │
│  │  ┌─────────────┐  ┌──────────────────────────┐   │  │
│  │  │ Vision Model│  │ Language Model (Qwen)     │   │  │
│  │  └─────────────┘  └──────────────────────────┘   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Phase 1 Milestones

| Milestone | Description | Validation |
|-----------|-------------|------------|
| M1.1 | Project scaffolding complete | App launches |
| M1.2 | ECG upload working | Can load and display ECG |
| M1.3 | Basic analysis working | Rate/rhythm reported |
| M1.4 | Chat interface functional | Can ask questions |
| M1.5 | Offline mode verified | Works without internet |
| M1.6 | MVP complete | End-to-end flow works |

---

## Phase 2: Core Intelligence

### Objective
Add sophisticated ECG analysis capabilities: lead extraction, precise measurements, comprehensive abnormality detection.

### Key Deliverables
1. Lead detection and extraction
2. Waveform digitization
3. Precise interval measurements
4. Chamber enlargement detection
5. Ischemia localization
6. Conduction abnormality classification

### Technical Approach

#### 2.1 Lead Detection
```
Tasks:
- Grid line detection using OpenCV
- Lead label recognition (OCR)
- Lead boundary detection
- Layout identification (3x4, 6x2, etc.)
- Rhythm strip identification
```

#### 2.2 Waveform Digitization
```
Tasks:
- Baseline detection
- Waveform tracing
- Grid calibration (time and voltage)
- Noise filtering
- Peak detection (P, Q, R, S, T)
```

#### 2.3 Measurement Engine
```
Tasks:
- PR interval calculation
- QRS duration calculation
- QT/QTc calculation (Bazett, Fridericia)
- Axis calculation from leads I and aVF
- ST segment measurement
```

#### 2.4 Abnormality Detection Models
```
Tasks:
- LVH criteria implementation
- RVH criteria implementation
- Atrial abnormality detection
- STEMI localization algorithms
- BBB classification logic
- AV block classification
```

#### 2.5 Enhanced Knowledge Base
```
Tasks:
- ChromaDB integration
- ECG interpretation guidelines embedding
- Differential diagnosis knowledge
- Clinical context database
```

### Phase 2 Architecture Addition

```
┌─────────────────────────────────────────────────────────┐
│              Lead Extraction Engine                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │
│  │  Grid     │  │  Lead     │  │  Waveform         │   │
│  │  Detector │  │  Segmenter│  │  Digitizer        │   │
│  └───────────┘  └───────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Measurement Engine                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │
│  │  Interval │  │  Axis     │  │  Morphology       │   │
│  │  Calculator│ │  Calculator│ │  Analyzer         │   │
│  └───────────┘  └───────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 3: Advanced Arrhythmia Analysis

### Objective
Implement the differentiating features: VT vs SVT differentiation, SVT classification, accessory pathway localization.

### Key Deliverables
1. Wide complex tachycardia algorithms
2. SVT mechanism classification
3. Accessory pathway localization
4. VT origin localization
5. Channelopathy detection

### Technical Approach

#### 3.1 WCT Algorithm Implementation
```
Tasks:
- Brugada algorithm (stepwise)
- Vereckei aVR algorithm
- Pava lead II algorithm
- R-wave peak time analysis
- Morphology concordance analysis
- Confidence scoring ensemble
```

#### 3.2 SVT Classification
```
Tasks:
- RP interval measurement
- P wave detection in tachycardia
- P wave morphology analysis
- AVNRT vs AVRT vs AT differentiation
- Flutter wave detection
```

#### 3.3 Pathway Localization
```
Tasks:
- Delta wave polarity mapping
- Arruda algorithm implementation
- Taguchi algorithm implementation
- Probability distribution visualization
- Localization confidence scoring
```

#### 3.4 Advanced Pattern Recognition
```
Tasks:
- Brugada pattern classification
- Long QT detection and typing
- ARVC criteria evaluation
- Fine-tuned model for rare patterns
```

### Phase 3 Architecture Addition

```
┌─────────────────────────────────────────────────────────┐
│           Advanced Arrhythmia Engine                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │              WCT Differentiator                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │ Brugada │ │Vereckei │ │  Pava   │ │Ensemble │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │              SVT Classifier                        │  │
│  │  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │ RP Analysis │  │ Mechanism   │                 │  │
│  │  └─────────────┘  └─────────────┘                 │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Pathway Localizer                     │  │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────────────┐   │  │
│  │  │ Arruda  │ │ Taguchi │ │ Location Mapper   │   │  │
│  │  └─────────┘ └─────────┘ └───────────────────┘   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 4: Integration & Scale

### Objective
Connect ECG Guru to the DocAssist ecosystem and add multi-user, educational, and localization features.

### Key Deliverables
1. EMR integration
2. Dora knowledge base integration
3. Multi-user support
4. Educational modules
5. Hindi localization

### Technical Approach

#### 4.1 EMR Integration
```
Tasks:
- Define integration API
- Patient context loading
- ECG storage in EMR
- Previous ECG comparison
- Analysis history
```

#### 4.2 Dora Integration
```
Tasks:
- Dora API client
- Guideline query integration
- Treatment recommendation linking
- Risk score calculation
```

#### 4.3 Educational System
```
Tasks:
- Case library structure
- Spaced repetition engine
- Progress tracking
- Quiz system
- Difficulty grading
```

### Integration Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     ECG Guru                               │
└─────────────────────────┬─────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │   EMR      │  │   Dora     │  │ Appointment│
   │ (Patient   │  │ (Guidelines│  │  System    │
   │  Context)  │  │  & RAG)    │  │            │
   └────────────┘  └────────────┘  └────────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  Shared Data Layer  │
              │  (SQLite + Chroma)  │
              └─────────────────────┘
```

---

## Development Workflow

### Using Spec-Kit
1. **Before each feature**: Run `/speckit.specify` to clarify requirements
2. **Before implementation**: Run `/speckit.plan` for technical approach
3. **Before coding**: Run `/speckit.tasks` to break into actionable items
4. **During implementation**: Run `/speckit.implement` with ralph-loop

### Using Ralph Wiggum
For well-defined implementation tasks:
```bash
/ralph-loop "Implement [specific feature] with tests" \
  --completion-promise "All tests pass" \
  --max-iterations 20
```

### Testing Strategy
- Unit tests for all algorithms
- Integration tests for analysis pipeline
- E2E tests for critical flows
- Manual validation with real ECGs
- Cardiologist review for accuracy

### Quality Gates
- All tests pass
- Linting clean
- Type checking passes
- Performance benchmarks met
- Cardiologist sign-off on accuracy claims

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vision model accuracy | High | Multiple model evaluation, fallback options |
| ECG image quality variance | Medium | Robust preprocessing, quality feedback |
| Offline model size | Medium | Tiered models based on device capability |
| Algorithm accuracy claims | High | Extensive validation, clear confidence levels |
| User adoption | Medium | Progressive disclosure, excellent UX |

---

## Success Metrics

### Phase 1 (MVP)
- App launches on Windows, macOS, Android
- ECG analysis in <10 seconds
- Chat interface functional
- 10 beta users testing

### Phase 2 (Core Intelligence)
- Lead extraction >95% accuracy
- Interval measurements within 10% of manual
- STEMI detection >90% sensitivity

### Phase 3 (Advanced)
- VT vs SVT differentiation >85% accuracy
- Cardiologist satisfaction >4/5
- Pathway localization useful in >70% cases

### Phase 4 (Integration)
- EMR integration deployed
- Educational content available
- Hindi interface available
