# ECG Guru Knowledge Base Specification

## Overview

The knowledge base is the foundation of ECG Guru's intelligence. It feeds the RAG pipeline that enables expert-level explanations, teaching, and clinical reasoning.

**Philosophy**: The AI doesn't guess from images. It receives structured algorithm results and uses the knowledge base to explain, teach, and contextualize findings like an expert would.

---

## Primary Knowledge Sources

### 1. Podrid's Real-World ECGs (648 Cases)

**Source**: [Cardiotext Publishing](https://cardiotextpublishing.com/)

The gold standard for systematic ECG education. Dr. Philip Podrid's 35+ years of teaching distilled into case-based learning.

| Volume | Content | Cases | Priority |
|--------|---------|-------|----------|
| **Volume 1** | The Basics | ~80 | HIGH - Foundation |
| **Volume 2** | Myocardial Abnormalities | ~100 | HIGH - STEMI/ischemia |
| **Volume 3** | Conduction Abnormalities | ~100 | HIGH - Blocks, BBB |
| **Volume 4A/4B** | Arrhythmias | 120 | CRITICAL - Core feature |
| **Volume 5A/5B** | Narrow/Wide Complex Tachycardias | ~120 | CRITICAL - VT vs SVT |
| **Volume 6** | Paced, Congenital, Electrolytes | ~128 | MEDIUM |

**How to Use**:
- Extract teaching narratives for RAG embeddings
- Use cases as teaching library (with proper licensing)
- Map case discussions to algorithm steps
- Cross-reference with our VT/SVT algorithm implementation

**Key Features**:
- Systematic approach to each ECG
- Clinical context provided
- Step-by-step interpretation method
- Management discussions

---

### 2. Electrocardiography of Arrhythmias (MK Das & Zipes)

**Source**: [Elsevier](https://www.us.elsevierhealth.com/electrocardiography-of-arrhythmias-a-comprehensive-review-9780323680509.html)

The definitive arrhythmia ECG reference. Companion to Zipes' "Cardiac Electrophysiology: From Cell to Bedside."

| Chapter | Topic | Figures | Our Use |
|---------|-------|---------|---------|
| Ch 5 | AVNRT | 24 | SVT classification |
| Ch 6 | AVRT | 32 | Pathway localization |
| Ch 7 | Atrial Tachycardia | 44 | AT focus localization |
| Ch 8 | Atrial Flutter | 47 | AFL recognition |
| Ch 9 | Atrial Fibrillation | 28 | AF with aberrancy |
| - | VT, Brugada, ARVC | Many | VT algorithms |

**Key Features**:
- Ladder diagrams for mechanism explanation
- CARTO/EP maps correlation
- Anatomical focus localization
- 250 full-color illustrations
- EP lab correlation (critical for pathway localization validation)

**How to Use**:
- Extract ladder diagram concepts for visual teaching
- Use EP correlations to validate our pathway algorithms
- Build mechanism explanation templates
- Reference for complex arrhythmia teaching

**Quote from AHA Review**: "One of the best collections of arrhythmia figures since Pick and Langendorf"

---

### 3. ECG Masters' Collection

Curated ECGs from master teachers around the world. Excellent for:
- Edge cases
- Teaching pearls
- Expert perspective diversity
- Real-world complexity

**How to Use**:
- Advanced teaching cases
- Expert reasoning patterns
- Unusual presentations

---

### 4. LITFL ECG Library (Free, Online)

**Source**: https://litfl.com/ecg-library/

Outstanding free resource with 150+ diagnostic entries.

#### Content Categories

**Basics**:
- ECG Basics (waves, intervals, segments)
- Pediatric interpretation
- Clinical interpretation approach

**Diagnostic A-Z**:
- Complete diagnostic reference
- Eponymous syndromes (Wellens, Brugada, etc.)
- Pattern recognition

**Case Series**:
| Series | Description | Use |
|--------|-------------|-----|
| **Top 100 ECG** | Self-assessment quizzes | Testing/gamification |
| **ECG Exigency** | Challenging diagnostic cases | Advanced teaching |
| **Cardiovascular Curveball** | Complex scenarios | Expert-level cases |
| **Activate or Wait** | Cath lab decisions | STEMI decision support |

**Specialized Topics**:
- Pacemaker function/malfunction
- Pre-excitation syndromes
- Long QT, Brugada
- Metabolic/drug effects

**How to Use**:
- Primary reference for diagnostic criteria
- Case quizzes for learning module
- STEMI decision cases for "Activate or Wait" feature
- Pattern recognition templates

---

### 5. Clinical Guidelines

| Guideline | Year | Use |
|-----------|------|-----|
| **ESC SVT Guidelines** | 2019 | SVT classification, management |
| **ESC Ventricular Arrhythmias** | 2022 | VT management, risk stratification |
| **ACC/AHA ECG Interpretation** | Current | Standard interpretation |
| **AHA STEMI Guidelines** | Current | STEMI detection, management |

---

### 6. Algorithm Papers (Primary Sources)

Each algorithm we implement must be traced to primary literature:

| Algorithm | Citation | Key Figures |
|-----------|----------|-------------|
| **Brugada WCT** | Brugada P, et al. Circulation 1991;83:1649-59 | 4-step flowchart |
| **Vereckei aVR** | Vereckei A, et al. Heart Rhythm 2008;5:89-98 | aVR criteria |
| **Basel Algorithm** | JACC Clin EP 2022 | 3-criteria approach |
| **SMART-WPW** | Heart Rhythm 2025 | Pathway localization |
| **EASY-WPW** | Heart Rhythm 2023 | Simplified pathway |
| **Fiol STEMI** | Multiple papers | Culprit vessel prediction |

---

## Knowledge Base Architecture

### ChromaDB Collections

```python
# Collection structure for ECG Guru knowledge base

collections = {
    # Core diagnostic knowledge
    "ecg_interpretation": {
        "description": "Systematic ECG interpretation guidelines",
        "sources": ["Podrid Vol 1", "LITFL Basics", "ACC/AHA Guidelines"],
        "chunk_size": 500,
        "overlap": 50
    },

    # Arrhythmia-specific
    "arrhythmia_knowledge": {
        "description": "Arrhythmia mechanisms, recognition, management",
        "sources": ["MK Das", "Podrid Vol 4-5", "ESC Guidelines"],
        "chunk_size": 750,
        "overlap": 100
    },

    # Algorithm explanations
    "algorithm_explanations": {
        "description": "Step-by-step algorithm walkthroughs",
        "sources": ["Primary papers", "LITFL", "Teaching narratives"],
        "chunk_size": 400,
        "overlap": 50
    },

    # Case library
    "teaching_cases": {
        "description": "Annotated teaching cases",
        "sources": ["Podrid all volumes", "LITFL Top 100", "ECG Masters"],
        "metadata": ["difficulty", "diagnosis", "teaching_points"],
        "chunk_size": 1000
    },

    # STEMI-specific
    "stemi_knowledge": {
        "description": "STEMI recognition, localization, management",
        "sources": ["LITFL Activate/Wait", "Guidelines", "Podrid Vol 2"],
        "chunk_size": 500
    },

    # Pathway localization
    "pathway_knowledge": {
        "description": "Accessory pathway localization",
        "sources": ["MK Das Ch 6", "Algorithm papers", "EP correlations"],
        "chunk_size": 600
    }
}
```

### Embedding Strategy

```python
class KnowledgeEmbedder:
    """Embed knowledge sources into ChromaDB"""

    def embed_textbook_chapter(self, chapter: TextbookChapter):
        """Process a textbook chapter for embedding"""

        chunks = self.chunk_with_overlap(
            chapter.text,
            chunk_size=chapter.optimal_chunk_size,
            overlap=50
        )

        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                metadatas=[{
                    "source": chapter.source,
                    "chapter": chapter.number,
                    "topic": chapter.topic,
                    "subtopic": self.extract_subtopic(chunk),
                    "difficulty": chapter.difficulty,
                    "chunk_index": i
                }],
                ids=[f"{chapter.id}_{i}"]
            )

    def embed_case(self, case: TeachingCase):
        """Process a teaching case"""

        # Embed the narrative separately from the ECG description
        self.collection.add(
            documents=[case.teaching_narrative],
            metadatas=[{
                "type": "case",
                "source": case.source,
                "diagnosis": case.primary_diagnosis,
                "secondary_diagnoses": case.secondary_diagnoses,
                "difficulty": case.difficulty,
                "teaching_points": case.teaching_points,
                "clinical_context": case.clinical_context
            }],
            ids=[case.id]
        )

    def embed_algorithm(self, algorithm: Algorithm):
        """Process an algorithm explanation"""

        # Full explanation
        self.collection.add(
            documents=[algorithm.full_explanation],
            metadatas=[{
                "type": "algorithm",
                "name": algorithm.name,
                "purpose": algorithm.purpose,
                "accuracy": algorithm.accuracy,
                "year": algorithm.year,
                "citation": algorithm.citation
            }],
            ids=[algorithm.id]
        )

        # Step-by-step breakdown
        for step in algorithm.steps:
            self.collection.add(
                documents=[step.explanation],
                metadatas=[{
                    "type": "algorithm_step",
                    "algorithm": algorithm.name,
                    "step_number": step.number,
                    "criterion": step.criterion
                }],
                ids=[f"{algorithm.id}_step_{step.number}"]
            )
```

---

## RAG Query Pipeline

```python
class ECGKnowledgeRAG:
    """Query knowledge base for clinical reasoning"""

    def query_for_explanation(
        self,
        algorithm_results: AlgorithmResults,
        user_question: str,
        user_level: UserLevel
    ) -> str:
        """Get relevant knowledge for explaining findings"""

        # Build query based on findings
        diagnoses = algorithm_results.get_diagnoses()
        query = self.build_query(diagnoses, user_question)

        # Get relevant knowledge
        results = self.chroma.query(
            query_texts=[query],
            n_results=5,
            where={
                "difficulty": {"$lte": user_level.max_difficulty}
            }
        )

        # Format context for LLM
        context = self.format_context(results)

        return context

    def get_teaching_content(
        self,
        diagnosis: str,
        aspect: str  # "mechanism", "recognition", "management"
    ) -> str:
        """Get teaching content for a specific diagnosis"""

        results = self.chroma.query(
            query_texts=[f"{diagnosis} {aspect}"],
            n_results=3,
            where={"type": {"$in": ["case", "algorithm_explanation"]}}
        )

        return self.format_teaching_content(results)

    def get_similar_cases(
        self,
        current_diagnosis: str,
        difficulty: int
    ) -> List[TeachingCase]:
        """Find similar teaching cases"""

        results = self.chroma.query(
            query_texts=[current_diagnosis],
            n_results=5,
            where={
                "type": "case",
                "difficulty": {"$gte": difficulty - 1, "$lte": difficulty + 1}
            }
        )

        return self.parse_cases(results)
```

---

## Content Processing Pipeline

### From Textbook to Knowledge Base

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  PDF/EPUB   │ ──► │   Extract    │ ──► │   Chunk     │
│  Textbook   │     │   Text       │     │   Content   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  ChromaDB   │ ◄── │   Embed      │ ◄── │  Add        │
│  Storage    │     │   Vectors    │     │  Metadata   │
└─────────────┘     └──────────────┘     └─────────────┘
```

### LITFL Scraping Strategy

```python
class LITFLScraper:
    """Scrape and structure LITFL ECG Library"""

    BASE_URL = "https://litfl.com/ecg-library/"

    def scrape_diagnostic_pages(self):
        """Scrape all diagnostic category pages"""

        for category in self.get_categories():
            for page in category.pages:
                content = self.fetch_page(page.url)
                structured = self.structure_content(content)

                yield LITFLEntry(
                    url=page.url,
                    title=page.title,
                    category=category.name,
                    diagnostic_criteria=structured.criteria,
                    ecg_features=structured.features,
                    clinical_pearls=structured.pearls,
                    related_pages=structured.related
                )

    def scrape_case_series(self):
        """Scrape Top 100, ECG Exigency, etc."""

        for series in ["top-100-ecg", "ecg-exigency", "cardiovascular-curveball"]:
            for case in self.get_series_cases(series):
                yield self.structure_case(case)
```

---

## Quality Assurance

### Knowledge Verification

1. **Medical Accuracy**: All content reviewed by cardiologist
2. **Algorithm Fidelity**: Cross-reference with primary papers
3. **Teaching Quality**: Test explanations with target users
4. **Coverage Completeness**: Ensure all diagnoses have knowledge

### Update Strategy

| Source | Update Frequency | Method |
|--------|-----------------|--------|
| Guidelines | When published | Manual review + re-embed |
| LITFL | Monthly | Automated scrape + diff |
| Textbooks | Edition changes | Manual re-processing |
| Algorithm papers | When published | Add new algorithms |

---

## Licensing Considerations

| Source | License | Commercial Use | Action Required |
|--------|---------|----------------|-----------------|
| **Podrid** | Copyrighted | Requires license | Contact Cardiotext |
| **MK Das** | Copyrighted | Requires license | Contact Elsevier |
| **LITFL** | CC BY-NC-SA | Attribution required | Include citations |
| **Guidelines** | Public | Yes with attribution | Cite properly |
| **Papers** | Various | Fair use for algorithm | Cite sources |

**Recommendation**:
- Start with LITFL (free, CC licensed) for initial development
- Negotiate educational license with Cardiotext for Podrid
- Use algorithm papers under fair use for implementation
- Contact publishers for commercial licensing when approaching launch

---

## Implementation Priority

1. **Phase 1**: LITFL scraping and embedding (free, immediate)
2. **Phase 2**: Algorithm papers and guidelines (fair use)
3. **Phase 3**: Negotiate Podrid licensing
4. **Phase 4**: MK Das for arrhythmia depth
5. **Phase 5**: Custom case curation with EP validation
