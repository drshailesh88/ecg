# DocAssist Ecosystem Integration Architecture

## Overview

ECG Guru is part of the DocAssist ecosystem - a suite of tools for Indian healthcare practitioners. This document defines how ECG Guru integrates with sibling products.

---

## Ecosystem Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DocAssist Ecosystem                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   DocAssist  │  │   DocAssist  │  │    Dora      │              │
│  │     EMR      │  │ Appointments │  │  (Medical    │              │
│  │              │  │              │  │   RAG)       │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           │                                         │
│                    ┌──────┴───────┐                                 │
│                    │   ECG Guru   │                                 │
│                    │              │                                 │
│                    └──────────────┘                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Shared Infrastructure                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐ │  │
│  │  │  SQLite    │  │  ChromaDB  │  │  Ollama Runtime         │ │  │
│  │  │  (Data)    │  │  (Vectors) │  │  (AI Models)            │ │  │
│  │  └────────────┘  └────────────┘  └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### 1. ECG Guru ↔ EMR Integration

#### Purpose
- Link ECG analyses to patient records
- Access patient history for context
- Store ECG findings in clinical notes

#### Data Flow

```
EMR Database                    ECG Guru
┌─────────────┐                ┌─────────────┐
│ patients    │ ◄───────────── │ Patient     │
│ - id        │   Fetch        │ Context     │
│ - name      │   Patient      │ Loader      │
│ - history   │                │             │
└─────────────┘                └─────────────┘

┌─────────────┐                ┌─────────────┐
│ documents   │ ◄───────────── │ ECG         │
│ - patient_id│   Store        │ Analysis    │
│ - type      │   Analysis     │ Results     │
│ - content   │                │             │
└─────────────┘                └─────────────┘

┌─────────────┐                ┌─────────────┐
│ files       │ ◄───────────── │ ECG         │
│ - document_id   Store        │ Image       │
│ - file_path │   Image        │ Storage     │
└─────────────┘                └─────────────┘
```

#### Interface Contract

```python
# ECG Guru exports
class ECGAnalysisResult:
    ecg_id: str
    timestamp: datetime
    image_path: str
    rate: int
    rhythm: str
    intervals: dict  # PR, QRS, QTc
    findings: list[Finding]
    interpretation: str
    urgency: UrgencyLevel

# EMR provides
class PatientContext:
    patient_id: str
    name: str
    age: int
    gender: str
    cardiac_history: list[str]
    medications: list[str]
    previous_ecgs: list[ECGAnalysisResult]
```

#### Integration Modes

1. **Standalone Mode**: ECG Guru works independently, no EMR needed
2. **Linked Mode**: ECG Guru reads from/writes to EMR when available
3. **Embedded Mode**: ECG Guru UI embedded within EMR interface

### 2. ECG Guru ↔ Dora Integration

#### Purpose
- Fetch relevant guidelines based on ECG findings
- Get treatment recommendations
- Access evidence-based protocols

#### Data Flow

```
Dora Knowledge Base            ECG Guru
┌─────────────┐                ┌─────────────┐
│ Guidelines  │ ◄───────────── │ Guideline   │
│ - topic     │   Query by     │ Query       │
│ - content   │   Finding      │ Engine      │
│ - source    │                │             │
└─────────────┘                └─────────────┘

┌─────────────┐                ┌─────────────┐
│ Treatments  │ ◄───────────── │ Treatment   │
│ - condition │   Fetch        │ Recommender │
│ - protocol  │   Protocol     │             │
│ - evidence  │                │             │
└─────────────┘                └─────────────┘
```

#### Interface Contract

```python
# ECG Guru queries
class GuidelineQuery:
    finding: str  # "STEMI", "Atrial Fibrillation", etc.
    context: str  # "acute management", "long-term treatment"

class GuidelineResponse:
    guideline_title: str
    key_points: list[str]
    source: str
    year: int
    full_content: str

# Dora provides
class TreatmentProtocol:
    condition: str
    first_line: list[Treatment]
    alternatives: list[Treatment]
    contraindications: list[str]
    monitoring: list[str]
```

#### Example Integrations

1. **STEMI Detected** → Query Dora for "STEMI acute management" → Display door-to-balloon time targets
2. **AF Detected** → Query Dora for "AF anticoagulation" → Calculate CHA2DS2-VASc, suggest therapy
3. **Long QT** → Query Dora for "QT prolonging drugs" → Cross-reference patient medications

### 3. ECG Guru ↔ Appointment System Integration

#### Purpose
- Urgent findings trigger appointment scheduling
- ECG status visible in patient queue
- Pre-appointment ECG analysis

#### Data Flow

```
Appointment System             ECG Guru
┌─────────────┐                ┌─────────────┐
│ Appointments│ ◄───────────── │ Urgency     │
│ - patient_id│   Create       │ Trigger     │
│ - urgency   │   Urgent Appt  │             │
│ - notes     │                │             │
└─────────────┘                └─────────────┘

┌─────────────┐                ┌─────────────┐
│ Patient     │ ───────────► │ Pre-Appt    │
│ Queue       │   Notify      │ ECG Ready   │
│             │   ECG Ready   │             │
└─────────────┘                └─────────────┘
```

---

## Shared Infrastructure

### SQLite Database Schema

```sql
-- Shared across DocAssist products
-- Located at: ~/.docassist/docassist.db

-- Patients table (owned by EMR, read by others)
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ECG-specific tables (owned by ECG Guru)
CREATE TABLE ecg_analyses (
    id TEXT PRIMARY KEY,
    patient_id TEXT,  -- nullable for standalone use
    image_path TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE ecg_chats (
    id TEXT PRIMARY KEY,
    ecg_analysis_id TEXT NOT NULL,
    messages_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecg_analysis_id) REFERENCES ecg_analyses(id)
);
```

### ChromaDB Collections

```python
# Shared ChromaDB instance at: ~/.docassist/chroma/

# ECG Guru collections
ecg_knowledge = chroma_client.get_or_create_collection(
    name="ecg_knowledge",
    metadata={"description": "ECG interpretation guidelines"}
)

ecg_case_library = chroma_client.get_or_create_collection(
    name="ecg_cases",
    metadata={"description": "Annotated ECG case library"}
)

# Dora collections (read-only for ECG Guru)
medical_guidelines = chroma_client.get_collection(
    name="medical_guidelines"
)
```

### Ollama Model Sharing

```yaml
# Shared Ollama instance
# All DocAssist products use same Ollama server

models:
  # Text generation (all products)
  - qwen2.5:1.5b  # Low RAM devices
  - qwen2.5:7b    # Standard devices
  - qwen2.5:14b   # High-end devices

  # Vision (ECG Guru specific)
  - llava:7b      # ECG image analysis
  - minicpm-v:8b  # Alternative vision model

  # Embeddings (all products)
  - nomic-embed-text:latest
```

---

## API Design

### Inter-Product Communication

```python
# docassist_common/api.py

from abc import ABC, abstractmethod
from typing import Optional

class DocAssistProduct(ABC):
    """Base class for all DocAssist products"""

    @abstractmethod
    def get_product_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this product is installed and running"""
        pass

class ECGGuruAPI:
    """API exposed by ECG Guru for other products"""

    def analyze_ecg(self, image_path: str, patient_id: Optional[str] = None) -> ECGAnalysisResult:
        """Analyze an ECG image, optionally linked to a patient"""
        pass

    def get_analysis(self, ecg_id: str) -> ECGAnalysisResult:
        """Retrieve a previous analysis"""
        pass

    def get_patient_ecgs(self, patient_id: str) -> list[ECGAnalysisResult]:
        """Get all ECGs for a patient"""
        pass

class EMRIntegration:
    """EMR integration used by ECG Guru"""

    def get_patient(self, patient_id: str) -> PatientContext:
        """Get patient information for context"""
        pass

    def store_document(self, patient_id: str, doc_type: str, content: str) -> str:
        """Store analysis as a document in patient record"""
        pass

class DoraIntegration:
    """Dora integration used by ECG Guru"""

    def query_guideline(self, query: GuidelineQuery) -> GuidelineResponse:
        """Query Dora for relevant guidelines"""
        pass

    def get_treatment_protocol(self, condition: str) -> TreatmentProtocol:
        """Get treatment protocol for a condition"""
        pass
```

---

## Deployment Modes

### Mode 1: Standalone ECG Guru
```
User installs only ECG Guru
- Full ECG analysis capability
- No patient linking
- No guideline integration
- Self-contained knowledge base
```

### Mode 2: ECG Guru + EMR
```
User has EMR and ECG Guru
- ECG analysis linked to patients
- Previous ECG comparison
- Findings stored in patient record
- Still no Dora (guidelines)
```

### Mode 3: Full DocAssist Suite
```
User has all products
- Complete patient context
- Guideline-informed analysis
- Treatment recommendations
- Appointment integration
- Unified experience
```

---

## Technical Implementation

### File System Layout

```
~/.docassist/
├── docassist.db              # Shared SQLite database
├── chroma/                   # Shared ChromaDB storage
│   ├── ecg_knowledge/
│   ├── ecg_cases/
│   ├── medical_guidelines/   # From Dora
│   └── patient_embeddings/   # From EMR
├── models/                   # Ollama model storage
├── ecg_guru/
│   ├── config.yaml
│   ├── images/               # Stored ECG images
│   └── exports/              # Generated reports
├── emr/
│   ├── config.yaml
│   └── ...
└── dora/
    ├── config.yaml
    └── ...
```

### Discovery Mechanism

```python
# How products find each other

import os
from pathlib import Path

DOCASSIST_HOME = Path.home() / ".docassist"

def discover_products() -> dict[str, bool]:
    """Discover which DocAssist products are installed"""
    products = {}

    products["emr"] = (DOCASSIST_HOME / "emr" / "config.yaml").exists()
    products["ecg_guru"] = (DOCASSIST_HOME / "ecg_guru" / "config.yaml").exists()
    products["dora"] = (DOCASSIST_HOME / "dora" / "config.yaml").exists()
    products["appointments"] = (DOCASSIST_HOME / "appointments" / "config.yaml").exists()

    return products

def get_shared_db() -> str:
    """Get path to shared database"""
    return str(DOCASSIST_HOME / "docassist.db")

def get_chroma_path() -> str:
    """Get path to shared ChromaDB"""
    return str(DOCASSIST_HOME / "chroma")
```

---

## Migration & Upgrade Path

### Version Compatibility

```yaml
# Each product declares compatibility
# ecg_guru/config.yaml
version: "1.0.0"
docassist_api_version: "1.0"
compatible_with:
  emr: ">=1.0.0"
  dora: ">=1.0.0"
  appointments: ">=1.0.0"
```

### Database Migrations

```python
# Shared migration system
# Run by first product to start

def run_migrations():
    current_version = get_db_version()

    migrations = [
        ("1.0.0", migration_1_0_0),
        ("1.1.0", migration_1_1_0),
        # ...
    ]

    for version, migrate_fn in migrations:
        if version > current_version:
            migrate_fn()
            set_db_version(version)
```
