# ECG Guru Advanced Requirements

## Overview
Post-MVP requirements that deliver the differentiating features - the capabilities that transform ECG Guru from "another ECG app" to "an electrophysiologist in your pocket."

## Target Users for Advanced Features
- **Primary**: Cardiology residents and practicing cardiologists
- **Secondary**: Electrophysiology fellows and practicing EPs
- **Tertiary**: Emergency medicine physicians handling arrhythmias

---

## Phase 2: Core Intelligence

### FR-10: Lead Extraction and Digitization
**Priority**: Must Have for Phase 2

10.1 The system shall extract individual leads from ECG image:
- Detect and separate all 12 leads
- Handle various ECG layouts (3x4, 6x2, continuous)
- Identify rhythm strip

10.2 The system shall digitize waveforms:
- Convert pixel data to voltage-time series
- Calibrate using grid lines
- Handle skewed or rotated images

10.3 The system shall enable lead-by-lead analysis:
- Zoom into individual leads
- Compare corresponding leads (I, aVL grouping etc.)
- Measure intervals on digitized data

### FR-11: Chamber Analysis
**Priority**: Must Have for Phase 2

11.1 The system shall detect left ventricular hypertrophy:
- Sokolow-Lyon criteria
- Cornell criteria
- Additional voltage criteria

11.2 The system shall detect right ventricular hypertrophy:
- R/S ratio in V1
- Right axis deviation
- Supporting criteria

11.3 The system shall detect atrial abnormalities:
- Left atrial abnormality (P mitrale)
- Right atrial abnormality (P pulmonale)
- Biatrial abnormality

### FR-12: Ischemia Analysis
**Priority**: Must Have for Phase 2

12.1 The system shall localize STEMI:
- Anterior (V1-V4)
- Lateral (I, aVL, V5-V6)
- Inferior (II, III, aVF)
- Posterior (reciprocal V1-V3, V7-V9)
- Right ventricular (V4R)

12.2 The system shall identify STEMI mimics:
- Benign early repolarization
- LVH with strain
- Pericarditis
- Brugada pattern
- Hyperkalemia

12.3 The system shall detect NSTEMI patterns:
- ST depression
- T wave inversions
- Wellens' patterns
- de Winter pattern

### FR-13: Conduction Abnormalities
**Priority**: Must Have for Phase 2

13.1 The system shall classify bundle branch blocks:
- Complete RBBB vs incomplete
- Complete LBBB vs incomplete
- Rate-dependent BBB

13.2 The system shall detect fascicular blocks:
- Left anterior fascicular block
- Left posterior fascicular block
- Bifascicular blocks
- Trifascicular pattern

13.3 The system shall analyze AV conduction:
- First degree AV block
- Second degree Type I (Wenckebach)
- Second degree Type II
- 2:1 AV block (distinguish type)
- Third degree (complete) AV block
- AV dissociation

---

## Phase 3: Advanced Arrhythmia Analysis (The Differentiator)

### FR-20: Wide Complex Tachycardia Analysis
**Priority**: Must Have for Phase 3

20.1 The system shall differentiate VT vs SVT with aberrancy:
- Apply Brugada algorithm
- Apply Vereckei algorithm (aVR)
- Apply Pava algorithm (lead II)
- Morphology analysis (RBBB vs LBBB patterns)
- Provide confidence score for each

20.2 The system shall explain the differentiation:
- Which criteria favor VT
- Which criteria favor SVT
- Why one diagnosis is more likely
- What additional information would help

20.3 The system shall provide clinical context:
- "In a patient with known heart disease, probability of VT is higher"
- Risk stratification based on diagnosis
- Urgency level

### FR-21: SVT Classification
**Priority**: Must Have for Phase 3

21.1 The system shall differentiate SVT mechanisms:
- AVNRT (typical and atypical)
- AVRT (orthodromic and antidromic)
- Atrial tachycardia
- Atrial flutter
- Atrial fibrillation with rapid ventricular response

21.2 The system shall analyze P wave relationship:
- RP interval analysis
- Short RP vs long RP tachycardia
- P wave location relative to QRS
- P wave morphology in tachycardia

21.3 The system shall suggest EP study findings:
- Expected findings for each SVT type
- Mapping and ablation targets
- Accessory pathway location hints

### FR-22: Accessory Pathway Localization
**Priority**: Must Have for Phase 3

22.1 The system shall localize WPW pathways:
- Apply Arruda algorithm
- Apply Taguchi algorithm
- Apply Fitzpatrick algorithm
- Provide probability distribution across locations

22.2 The system shall provide detailed localization:
- Left free wall
- Posteroseptal
- Right free wall
- Anteroseptal
- Midseptal
- Sublocalization where possible

22.3 The system shall identify pathway characteristics:
- Manifest vs concealed
- Delta wave polarity analysis
- R/S ratios in precordial leads
- Transition zone

### FR-23: VT Origin Localization
**Priority**: Should Have for Phase 3

23.1 The system shall localize PVC/VT origin:
- RVOT vs LVOT
- Aortic cusp
- Mitral/tricuspid annulus
- Papillary muscle
- Epicardial vs endocardial hints

23.2 The system shall analyze VT morphology:
- RBBB vs LBBB pattern
- Axis analysis
- Precordial transition
- QRS duration

### FR-24: Complex Arrhythmia Mechanisms
**Priority**: Should Have for Phase 3

24.1 The system shall identify channelopathies:
- Brugada syndrome (Type 1, 2, 3)
- Long QT syndrome (suggest type)
- Short QT syndrome
- CPVT pattern
- Early repolarization syndrome

24.2 The system shall identify cardiomyopathy patterns:
- ARVC criteria
- HCM patterns
- DCM patterns
- Cardiac amyloid hints

---

## Phase 4: Integration and Scale

### FR-30: EMR Integration
**Priority**: Must Have for Phase 4

30.1 The system shall integrate with DocAssist EMR:
- Import patient demographics
- Link ECG to patient record
- Access previous ECGs for comparison
- Store analysis in patient chart

30.2 The system shall support ECG trending:
- Compare current to previous ECG
- Track interval changes over time
- Identify new findings vs known

### FR-31: Dora Integration
**Priority**: Must Have for Phase 4

31.1 The system shall query Dora for:
- Treatment guidelines based on findings
- Relevant clinical context
- Drug dosing for arrhythmias
- Evidence-based recommendations

31.2 The system shall provide:
- Links to relevant guidelines
- Citation of sources
- Risk stratification tools (CHA2DS2-VASc, etc.)

### FR-32: Multi-User and Clinic Features
**Priority**: Should Have for Phase 4

32.1 The system shall support:
- Multiple user profiles
- Different expertise levels per user
- Usage analytics (anonymized)
- Shared case library (opt-in)

### FR-33: Advanced Educational Features
**Priority**: Should Have for Phase 4

33.1 The system shall provide:
- Case-based learning modules
- Spaced repetition quizzes
- Progress tracking
- Competency assessment

33.2 The system shall offer:
- EP board exam preparation mode
- Difficulty-graded case library
- Explanation of classic cases

### FR-34: Localization
**Priority**: Should Have for Phase 4

34.1 The system shall support:
- Hindi interface
- Medical terminology in Hindi
- Regional language support (planned)
- Culturally appropriate examples

---

## Technical Requirements for Advanced Features

### TR-1: AI Model Requirements
- Vision model capable of lead extraction
- Fine-tuned model for ECG-specific features
- Ensemble approach for high-stakes decisions (VT vs SVT)

### TR-2: Knowledge Base
- Structured knowledge of algorithms (Brugada, Vereckei)
- Pathway localization tables
- Guideline database

### TR-3: Performance for Advanced
- Complex analysis within 30 seconds
- Pathway localization within 15 seconds
- Maintain responsiveness during analysis

---

## Success Metrics for Advanced Features

### Phase 2 Metrics
- Lead extraction success rate >95%
- STEMI localization accuracy >90%
- BBB classification accuracy >95%

### Phase 3 Metrics (The Key Differentiators)
- VT vs SVT differentiation accuracy >85%
- Agreement with EP diagnosis >80%
- Pathway localization within 1 segment >70%
- User satisfaction among cardiologists >4/5

### Phase 4 Metrics
- EMR integration adoption >50% of EMR users
- Case library contribution rate
- Educational module completion rate
