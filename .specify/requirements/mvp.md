# ECG Guru MVP Requirements

## Overview
The Minimum Viable Product delivers core ECG analysis and chat functionality, proving the concept that an AI can provide useful ECG interpretation across skill levels.

## Target Users for MVP
- **Primary**: MBBS students and residents learning ECG interpretation
- **Secondary**: General practitioners needing quick ECG assessment
- **Validation**: Cardiologists to verify accuracy and usefulness

## Functional Requirements

### FR-1: ECG Image Input
**Priority**: Must Have

1.1 The system shall accept ECG images via:
- File upload (JPEG, PNG, PDF)
- Camera capture (mobile devices)
- Clipboard paste (desktop)

1.2 The system shall support standard 12-lead ECG formats:
- Standard grid paper (25mm/s, 10mm/mV)
- Common ECG machine outputs (GE, Philips, etc.)
- Phone photos of paper ECGs

1.3 The system shall provide image quality feedback:
- Detect if image is too blurry
- Detect if leads are cut off or missing
- Suggest improvements for poor captures

### FR-2: Basic ECG Analysis
**Priority**: Must Have

2.1 The system shall identify and report:
- Heart rate (ventricular and atrial if different)
- Rhythm (regular/irregular, sinus/non-sinus)
- Axis (normal, LAD, RAD, extreme)

2.2 The system shall measure intervals:
- PR interval (and note if prolonged/short)
- QRS duration (and note if wide)
- QT/QTc interval (and note if prolonged)

2.3 The system shall identify waveform components:
- P wave presence and morphology
- QRS complex morphology
- ST segment (elevation/depression/normal)
- T wave morphology

### FR-3: Abnormality Detection
**Priority**: Must Have

3.1 The system shall detect common abnormalities:
- Sinus bradycardia/tachycardia
- Atrial fibrillation/flutter
- Bundle branch blocks (RBBB/LBBB)
- ST elevation (STEMI patterns)
- ST depression
- T wave inversions
- Prolonged QT
- First degree AV block

3.2 The system shall provide confidence levels:
- High/Medium/Low confidence for each finding
- Explanation of why confidence is limited when applicable

### FR-4: Chat Interface
**Priority**: Must Have

4.1 The system shall support natural language queries:
- "Is this ECG normal?"
- "What is the heart rate?"
- "Is there any ST elevation?"
- "Could this be a heart attack?"
- "Explain the P waves in this ECG"

4.2 The system shall maintain conversation context:
- Remember what ECG is being discussed
- Follow-up questions without re-uploading
- Reference previous answers in context

4.3 The system shall adapt to user level:
- Simple explanations for general queries
- Technical detail available on request
- Progressive disclosure of complexity

### FR-5: Structured Report
**Priority**: Must Have

5.1 The system shall generate a structured analysis:
```
Rate: XX bpm
Rhythm: [description]
Axis: [description]
Intervals: PR XX ms, QRS XX ms, QTc XX ms
P waves: [description]
QRS: [description]
ST-T changes: [description]
Interpretation: [summary]
Findings:
- [Finding 1] (confidence: high/medium/low)
- [Finding 2] (confidence: high/medium/low)
```

5.2 The system shall categorize urgency:
- Normal
- Abnormal - Non-urgent
- Abnormal - Needs attention
- Abnormal - Urgent/Critical

### FR-6: Educational Content
**Priority**: Should Have

6.1 The system shall explain findings:
- What each abnormality means
- Clinical significance
- What to look for on the ECG

6.2 The system shall provide visual annotations:
- Highlight relevant portions of ECG
- Point to specific waveforms being discussed
- Show measurements on the ECG

### FR-7: Offline Functionality
**Priority**: Must Have

7.1 Core analysis shall work completely offline:
- Local AI model inference
- Local knowledge base for common conditions
- No internet required for basic operation

7.2 Online features (when available):
- Knowledge base updates
- Complex case consultation
- Sync with other DocAssist products

## Non-Functional Requirements

### NFR-1: Performance
- Initial analysis complete within 10 seconds on mid-range device
- Chat responses within 3 seconds
- App startup within 5 seconds

### NFR-2: Accuracy
- >95% accuracy on rate calculation
- >90% accuracy on rhythm classification (sinus vs AF vs other)
- >85% accuracy on common abnormality detection
- Clear uncertainty indication when below thresholds

### NFR-3: Usability
- Usable with one-handed operation on mobile
- Accessible to users with limited technical expertise
- Works on devices with 4GB RAM

### NFR-4: Privacy
- All ECG processing local by default
- No ECG data transmitted without explicit consent
- No persistent storage without user action

### NFR-5: Reliability
- Graceful degradation if AI model fails
- Clear error messages when analysis not possible
- No crashes on malformed input

## Technical Constraints

### TC-1: Technology Stack
- Python 3.11+
- Flet for UI
- Ollama for local LLM
- Vision-capable model for ECG image analysis
- ChromaDB for knowledge base

### TC-2: Device Support
- Desktop: Windows 10+, macOS 11+, Linux
- Mobile: Android 10+, iOS 14+ (via Flet)
- Minimum: 4GB RAM, 2GB storage

### TC-3: Model Size
- Base model: <4GB for wide compatibility
- Optional larger models for capable devices
- Graceful fallback to smaller models

## User Stories

### US-1: Quick Assessment
**As a** general practitioner
**I want to** quickly check if an ECG is normal or abnormal
**So that** I can decide if the patient needs urgent referral

### US-2: Learning ECG
**As an** MBBS student
**I want to** understand what each part of the ECG means
**So that** I can learn ECG interpretation

### US-3: Detailed Analysis
**As a** cardiology resident
**I want to** get detailed measurements and differential diagnosis
**So that** I can present the case accurately

### US-4: Rural Practice
**As a** RMP in a village
**I want to** use ECG analysis without internet
**So that** I can help patients in areas with poor connectivity

### US-5: Second Opinion
**As a** practicing cardiologist
**I want to** cross-check my interpretation with AI analysis
**So that** I don't miss subtle findings

## Acceptance Criteria

### AC-1: MVP Release Criteria
1. Can upload ECG from file, camera, or clipboard
2. Provides accurate rate and rhythm analysis
3. Detects STEMI with >90% sensitivity
4. Chat interface answers basic questions
5. Works completely offline
6. Runs on device with 4GB RAM
7. Tested with 50+ real ECGs
8. Reviewed by at least 2 cardiologists

## Out of Scope for MVP

1. Advanced arrhythmia analysis (VT vs SVT differentiation)
2. Pathway localization
3. Multi-user support
4. EMR integration
5. Hindi/regional language support
6. Waveform digitization (pixel-level extraction)
7. Comparison with previous ECGs
8. Automated reporting to external systems
