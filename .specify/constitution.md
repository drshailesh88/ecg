# ECG Guru Constitution

## Mission Statement

To democratize expert-level ECG interpretation by putting a seasoned electrophysiologist in every practitioner's pocket, serving everyone from village RMPs to practicing cardiologists.

## Core Principles

### 1. Clinical Accuracy Above All
- Medical decisions depend on our analysis. Accuracy is non-negotiable.
- When uncertain, express uncertainty. Never hallucinate findings.
- Every interpretation must be evidence-based and explainable.
- Include appropriate medical disclaimers without being so cautious as to be useless.

### 2. Serve All Levels
- Design for the village RMP needing to know "is this dangerous?"
- Also serve the electrophysiologist asking "where is this accessory pathway?"
- Progressive disclosure: simple answers first, depth available on demand.
- Never talk down to beginners or overwhelm with jargon.

### 3. Offline-First Architecture
- Internet is a luxury in tier-3 cities and villages.
- Core functionality must work completely offline.
- Local AI inference using Ollama/Qwen models.
- Cloud features are enhancements, not requirements.

### 4. Privacy is Sacred
- ECGs are medical data. Treat them accordingly.
- All processing happens locally by default.
- No data leaves the device without explicit user consent.
- No telemetry, no analytics that compromise patient privacy.

### 5. Educational at Heart
- Don't just give answers; teach understanding.
- Every diagnosis should be a learning opportunity.
- Support the journey from student to expert.
- Make complex concepts accessible without dumbing them down.

### 6. Integration-Ready
- Part of the DocAssist ecosystem, not a silo.
- Standard interfaces for EMR, Dora, Appointment System.
- Shared data models with other DocAssist products.
- API-first design for future integrations.

### 7. India-First, Global-Ready
- Primary users are Indian healthcare practitioners.
- Support for Hindi and regional languages planned.
- Understand Indian healthcare context (MBBS, MD, DM paths).
- Designed for resource-constrained environments.

## Technical Principles

### 1. Python Ecosystem
- Primary language: Python 3.11+
- UI Framework: Flet (cross-platform)
- Align with EMR and Appointment System stack

### 2. Local AI Stack
- Ollama for model inference
- Qwen models (1.5B-7B based on device capability)
- ChromaDB for vector storage and RAG
- Vision models for ECG image analysis

### 3. Simple Persistence
- SQLite for structured data
- File system for ECG images and exports
- ChromaDB for embeddings and semantic search

### 4. Modular Architecture
- Separate UI, Core, AI, Knowledge, Integration layers
- Each layer independently testable
- Easy to swap components (e.g., different AI models)

### 5. Spec-Driven Development
- Use spec-kit for all feature development
- Specifications before implementation
- Ralph-loop for iterative refinement

## User Experience Principles

### 1. Speed Matters
- Initial analysis within seconds
- Responsive UI even on modest hardware
- Background processing with immediate feedback

### 2. Trust Through Transparency
- Show reasoning, not just conclusions
- Confidence indicators for findings
- Clear indication of AI vs human analysis

### 3. Context Awareness
- Remember user's expertise level
- Adapt explanations accordingly
- Learn from user interactions over time

### 4. Fail Gracefully
- Poor quality ECG? Help user improve capture.
- Unsupported rhythm? Say so clearly.
- Offline? Work with cached knowledge.

## What We Will Not Do

1. **Replace Clinical Judgment**: We assist, we don't decide.
2. **Store Data Externally**: Without explicit consent, never.
3. **Oversimplify for Experts**: Don't dumb down advanced features.
4. **Overwhelm Beginners**: Progressive disclosure, not information dump.
5. **Work Only Online**: Offline capability is mandatory.
6. **Ignore Integration**: We're part of DocAssist, not standalone.
