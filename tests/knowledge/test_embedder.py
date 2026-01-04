"""
Comprehensive tests for ECGKnowledgeEmbedder

Tests cover:
1. Initialization (3+ tests)
2. ID Generation (3+ tests)
3. Text Chunking (5+ tests)
4. Embedding Methods (15+ tests)
5. Query Interface (5+ tests)
6. Integration (3+ tests)
"""

import pytest
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import asdict

from src.knowledge.embedder import (
    ECGKnowledgeEmbedder,
    EmbeddingStats
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    with patch('src.knowledge.embedder.chromadb.PersistentClient') as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock collections
        collections = {}
        for name in ECGKnowledgeEmbedder.COLLECTIONS.keys():
            coll = MagicMock()
            coll.count.return_value = 0
            coll.upsert.return_value = None
            coll.query.return_value = {
                'ids': [['test_id']],
                'documents': [['test_doc']],
                'metadatas': [[{'test': 'meta'}]],
                'distances': [[0.5]]
            }
            collections[f"ecg_{name}"] = coll

        def get_or_create_collection(name, metadata=None):
            return collections[name]

        client.get_or_create_collection = get_or_create_collection

        yield client, collections


@pytest.fixture
def embedder(temp_dir, mock_chroma_client):
    """Create embedder instance with mocked ChromaDB"""
    client, collections = mock_chroma_client
    embedder = ECGKnowledgeEmbedder(persist_dir=temp_dir / "chroma")
    embedder.collections = {k.replace('ecg_', ''): v for k, v in collections.items()}
    return embedder


@pytest.fixture
def sample_textbook_data():
    """Sample textbook content data"""
    return {
        "chunks": [
            {
                "source": "ECGs Made Easy",
                "chapter": "Chapter 1: Basic Concepts",
                "section": "Introduction",
                "chunk_index": 0,
                "page": 10,
                "text": "The ECG is a graphical representation of cardiac electrical activity.",
                "topics": ["basics", "introduction"]
            },
            {
                "source": "ECGs Made Easy",
                "chapter": "Chapter 1: Basic Concepts",
                "section": "P Wave",
                "chunk_index": 1,
                "page": 12,
                "text": "The P wave represents atrial depolarization.",
                "topics": ["p-wave", "atrial"]
            }
        ]
    }


@pytest.fixture
def sample_teaching_cases():
    """Sample teaching cases data"""
    return {
        "cases": [
            {
                "source": "Podrid",
                "volume": "Volume 1",
                "case_number": 1,
                "clinical_context": "65-year-old with chest pain",
                "ecg_description": "ST elevation in V1-V4",
                "analysis": "Anterior STEMI",
                "diagnosis": "Anterior STEMI",
                "teaching_points": [
                    "ST elevation >1mm in contiguous leads",
                    "LAD territory involvement"
                ],
                "difficulty": "beginner",
                "topics": ["STEMI", "anterior"]
            },
            {
                "source": "LITFL",
                "case_number": 2,
                "case_id": "litfl_case_2",
                "clinical_context": "35-year-old with palpitations",
                "ecg_description": "Delta waves in leads II, III, aVF",
                "analysis": "WPW with posteroseptal pathway",
                "diagnosis": "WPW syndrome",
                "teaching_points": [
                    "Short PR interval",
                    "Delta wave indicating pre-excitation"
                ],
                "difficulty": "intermediate",
                "topics": ["WPW", "pre-excitation"]
            }
        ]
    }


@pytest.fixture
def sample_arrhythmia_data():
    """Sample arrhythmia content data"""
    return {
        "arrhythmia_content": [
            {
                "source": "MK Das",
                "arrhythmia_type": "AVNRT",
                "mechanism": "Reentrant circuit in AV node using slow and fast pathways",
                "ecg_features": [
                    "Narrow QRS tachycardia",
                    "No visible P waves or pseudo-r' in V1",
                    "RP interval <70ms"
                ],
                "differential_diagnosis": [
                    "AVRT",
                    "Atrial tachycardia"
                ],
                "ep_correlation": "Dual AV nodal physiology with slow pathway antegrade conduction",
                "ablation_targets": "Slow pathway modification in posteroseptal right atrium",
                "clinical_pearls": [
                    "Most common regular SVT",
                    "Usually terminates with adenosine"
                ]
            },
            {
                "source": "MK Das",
                "arrhythmia_type": "VT",
                "mechanism": "Reentry, triggered activity, or enhanced automaticity",
                "ecg_features": [
                    "Wide QRS >120ms",
                    "AV dissociation",
                    "Capture/fusion beats"
                ],
                "differential_diagnosis": [
                    "SVT with aberrancy"
                ],
                "clinical_pearls": [
                    "Assume wide complex tachycardia is VT until proven otherwise"
                ]
            }
        ]
    }


@pytest.fixture
def sample_litfl_data():
    """Sample LITFL content data"""
    return {
        "diagnostic_pages": [
            {
                "title": "STEMI",
                "category": "Ischemia",
                "url": "https://litfl.com/stemi",
                "content": "STEMI is characterized by ST elevation in contiguous leads...",
                "ecg_features": [
                    "ST elevation >1mm in limb leads",
                    "ST elevation >2mm in precordial leads"
                ],
                "clinical_pearls": [
                    "Time is muscle",
                    "Door-to-balloon <90 minutes"
                ],
                "key_points": [
                    "Immediate reperfusion therapy indicated"
                ]
            }
        ],
        "case_series": {
            "ECG_Case_Studies": [
                {
                    "case_number": 1,
                    "title": "Anterior STEMI",
                    "clinical_scenario": "55yo male with crushing chest pain",
                    "ecg_description": "ST elevation V1-V4",
                    "diagnosis": "Anterior STEMI",
                    "teaching_points": [
                        "LAD occlusion",
                        "Urgent PCI required"
                    ]
                }
            ]
        }
    }


@pytest.fixture
def sample_algorithms():
    """Sample algorithm definitions"""
    return [
        {
            "name": "Brugada Algorithm",
            "purpose": "VT vs SVT differentiation",
            "year": 1991,
            "accuracy": "89% sensitivity",
            "full_explanation": "Four-step algorithm for wide complex tachycardia differentiation",
            "citation": "Brugada et al. Circulation 1991",
            "steps": [
                {
                    "number": 1,
                    "criterion": "Absence of RS complex in all precordial leads",
                    "explanation": "If no RS in V1-V6, diagnose VT"
                },
                {
                    "number": 2,
                    "criterion": "R to S interval >100ms in any precordial lead",
                    "explanation": "Slow initial activation suggests VT"
                }
            ]
        },
        {
            "name": "SMART-WPW",
            "purpose": "Accessory pathway localization",
            "year": 2025,
            "accuracy": "97%",
            "full_explanation": "Machine learning-based pathway localization",
            "citation": "Recent study 2025",
            "steps": [
                {
                    "number": 1,
                    "criterion": "Assess delta wave polarity in lead I",
                    "explanation": "Positive suggests left-sided pathway"
                }
            ]
        }
    ]


# ============================================================================
# 1. INITIALIZATION TESTS (3+ tests)
# ============================================================================

class TestInitialization:
    """Test embedder initialization"""

    def test_creates_persist_directory(self, temp_dir, mock_chroma_client):
        """Test that persist directory is created"""
        persist_path = temp_dir / "chroma_test"
        assert not persist_path.exists()

        embedder = ECGKnowledgeEmbedder(persist_dir=persist_path)

        assert persist_path.exists()
        assert persist_path.is_dir()

    def test_initializes_chromadb_client(self, temp_dir, mock_chroma_client):
        """Test ChromaDB client initialization"""
        client, _ = mock_chroma_client
        persist_path = temp_dir / "chroma_test"

        embedder = ECGKnowledgeEmbedder(persist_dir=persist_path)

        # Verify client was created with correct settings
        assert embedder.client is not None

    def test_creates_all_collections(self, temp_dir, mock_chroma_client):
        """Test that all 6 collections are created"""
        client, collections_mock = mock_chroma_client

        embedder = ECGKnowledgeEmbedder(persist_dir=temp_dir / "chroma")

        # Should have all 6 collections
        expected_collections = {
            "textbook_content",
            "teaching_cases",
            "arrhythmia",
            "diagnostic_criteria",
            "clinical_pearls",
            "algorithms"
        }

        assert set(embedder.collections.keys()) == expected_collections

    def test_default_persist_directory(self, mock_chroma_client):
        """Test default persist directory is used when not specified"""
        embedder = ECGKnowledgeEmbedder()

        assert embedder.persist_dir == Path("./data/chroma_db")


# ============================================================================
# 2. ID GENERATION TESTS (3+ tests)
# ============================================================================

class TestIDGeneration:
    """Test ID generation for document uniqueness"""

    def test_generates_consistent_hash(self, embedder):
        """Test that same inputs produce same ID"""
        id1 = embedder._generate_id("source1", "chapter1", 0)
        id2 = embedder._generate_id("source1", "chapter1", 0)

        assert id1 == id2
        assert len(id1) == 32  # MD5 hash length

    def test_different_inputs_produce_different_ids(self, embedder):
        """Test that different inputs produce different IDs"""
        id1 = embedder._generate_id("source1", "chapter1", 0)
        id2 = embedder._generate_id("source1", "chapter1", 1)
        id3 = embedder._generate_id("source2", "chapter1", 0)

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_deterministic_generation(self, embedder):
        """Test ID generation is deterministic"""
        # Same inputs should produce same hash every time
        inputs = ("Podrid", "Volume 1", 42)

        ids = [embedder._generate_id(*inputs) for _ in range(10)]

        assert len(set(ids)) == 1  # All IDs should be identical

    def test_handles_various_argument_types(self, embedder):
        """Test ID generation with different argument types"""
        id_str = embedder._generate_id("string", "args")
        id_int = embedder._generate_id(1, 2, 3)
        id_mixed = embedder._generate_id("source", 1, "chapter", 2)

        assert all(len(id_val) == 32 for id_val in [id_str, id_int, id_mixed])
        assert id_str != id_int != id_mixed


# ============================================================================
# 3. TEXT CHUNKING TESTS (5+ tests)
# ============================================================================

class TestTextChunking:
    """Test text chunking functionality"""

    def test_chunk_text_default_parameters(self, embedder):
        """Test chunking with default chunk_size and overlap"""
        text = " ".join([f"word{i}" for i in range(1000)])

        chunks = embedder._chunk_text(text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_respects_chunk_size(self, embedder):
        """Test that chunks respect specified size"""
        text = " ".join([f"word{i}" for i in range(1000)])
        chunk_size = 50
        overlap = 10  # Use smaller overlap to avoid zero step

        chunks = embedder._chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        for chunk in chunks[:-1]:  # Exclude last chunk which may be smaller
            word_count = len(chunk.split())
            assert word_count <= chunk_size

    def test_chunk_text_creates_overlap(self, embedder):
        """Test that chunks have overlap"""
        text = " ".join([f"word{i}" for i in range(200)])
        chunk_size = 50
        overlap = 10

        chunks = embedder._chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        # Check that consecutive chunks share some words
        if len(chunks) >= 2:
            chunk1_words = set(chunks[0].split()[-overlap:])
            chunk2_words = set(chunks[1].split()[:overlap])

            # There should be some overlap
            assert len(chunk1_words.intersection(chunk2_words)) > 0

    def test_empty_text_returns_empty_list(self, embedder):
        """Test that empty text returns empty list"""
        assert embedder._chunk_text("") == []
        assert embedder._chunk_text("   ") == []

    def test_short_text_returns_single_chunk(self, embedder):
        """Test that text shorter than chunk_size returns single chunk"""
        text = "This is a short text with few words"

        chunks = embedder._chunk_text(text, chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_size_one(self, embedder):
        """Test chunking with chunk_size=1"""
        text = "word1 word2 word3 word4 word5"

        chunks = embedder._chunk_text(text, chunk_size=1, overlap=0)

        assert len(chunks) == 5
        assert all(len(chunk.split()) == 1 for chunk in chunks)

    def test_no_overlap(self, embedder):
        """Test chunking with no overlap"""
        text = " ".join([f"word{i}" for i in range(100)])
        chunk_size = 20

        chunks = embedder._chunk_text(text, chunk_size=chunk_size, overlap=0)

        # Should have exactly 5 chunks (100 words / 20 per chunk)
        assert len(chunks) == 5


# ============================================================================
# 4. EMBEDDING METHODS TESTS (15+ tests)
# ============================================================================

class TestEmbeddingMethods:
    """Test individual embedding methods"""

    # ---- Textbook Content ----

    def test_embed_textbook_content_valid_file(self, embedder, temp_dir, sample_textbook_data):
        """Test embedding textbook content from valid file"""
        content_file = temp_dir / "textbook.json"
        content_file.write_text(json.dumps(sample_textbook_data))

        count = embedder.embed_textbook_content(content_file)

        assert count == 2
        assert embedder.collections["textbook_content"].upsert.call_count == 2

    def test_embed_textbook_content_missing_file(self, embedder, temp_dir):
        """Test embedding with non-existent file returns 0"""
        missing_file = temp_dir / "nonexistent.json"

        count = embedder.embed_textbook_content(missing_file)

        assert count == 0
        assert embedder.collections["textbook_content"].upsert.call_count == 0

    def test_embed_textbook_content_metadata(self, embedder, temp_dir, sample_textbook_data):
        """Test that textbook metadata is correctly embedded"""
        content_file = temp_dir / "textbook.json"
        content_file.write_text(json.dumps(sample_textbook_data))

        embedder.embed_textbook_content(content_file)

        # Check first call's metadata
        call_args = embedder.collections["textbook_content"].upsert.call_args_list[0]
        metadata = call_args[1]['metadatas'][0]

        assert metadata['source'] == "ECGs Made Easy"
        assert metadata['chapter'] == "Chapter 1: Basic Concepts"
        assert metadata['section'] == "Introduction"
        assert metadata['page'] == 10
        assert metadata['topics'] == "basics,introduction"

    # ---- Teaching Cases ----

    def test_embed_teaching_cases_valid_cases(self, embedder, temp_dir, sample_teaching_cases):
        """Test embedding teaching cases"""
        cases_file = temp_dir / "cases.json"
        cases_file.write_text(json.dumps(sample_teaching_cases))

        count = embedder.embed_teaching_cases(cases_file)

        assert count == 2
        assert embedder.collections["teaching_cases"].upsert.call_count == 2

    def test_embed_teaching_cases_formats_correctly(self, embedder, temp_dir, sample_teaching_cases):
        """Test that case text is formatted correctly"""
        cases_file = temp_dir / "cases.json"
        cases_file.write_text(json.dumps(sample_teaching_cases))

        embedder.embed_teaching_cases(cases_file)

        # Check first call's document
        call_args = embedder.collections["teaching_cases"].upsert.call_args_list[0]
        case_text = call_args[1]['documents'][0]

        assert "Clinical Context:" in case_text
        assert "65-year-old with chest pain" in case_text
        assert "ECG Description:" in case_text
        assert "ST elevation in V1-V4" in case_text
        assert "Teaching Points:" in case_text
        assert "ST elevation >1mm in contiguous leads" in case_text

    def test_embed_teaching_cases_uses_case_id(self, embedder, temp_dir, sample_teaching_cases):
        """Test that provided case_id is used"""
        cases_file = temp_dir / "cases.json"
        cases_file.write_text(json.dumps(sample_teaching_cases))

        embedder.embed_teaching_cases(cases_file)

        # Second case has explicit case_id
        call_args = embedder.collections["teaching_cases"].upsert.call_args_list[1]
        doc_id = call_args[1]['ids'][0]

        assert doc_id == "litfl_case_2"

    # ---- Arrhythmia Content ----

    def test_embed_arrhythmia_with_ep_correlation(self, embedder, temp_dir, sample_arrhythmia_data):
        """Test embedding arrhythmia content with EP correlation"""
        arrhythmia_file = temp_dir / "arrhythmia.json"
        arrhythmia_file.write_text(json.dumps(sample_arrhythmia_data))

        count = embedder.embed_arrhythmia_content(arrhythmia_file)

        assert count == 2

        # Check first arrhythmia has EP correlation
        call_args = embedder.collections["arrhythmia"].upsert.call_args_list[0]
        metadata = call_args[1]['metadatas'][0]

        assert metadata['has_ep_correlation'] is True
        assert metadata['has_ablation_info'] is True

    def test_embed_arrhythmia_with_ablation_targets(self, embedder, temp_dir, sample_arrhythmia_data):
        """Test that ablation targets are included"""
        arrhythmia_file = temp_dir / "arrhythmia.json"
        arrhythmia_file.write_text(json.dumps(sample_arrhythmia_data))

        embedder.embed_arrhythmia_content(arrhythmia_file)

        # Check document text includes ablation info
        call_args = embedder.collections["arrhythmia"].upsert.call_args_list[0]
        arrhythmia_text = call_args[1]['documents'][0]

        assert "Ablation Targets:" in arrhythmia_text
        assert "Slow pathway modification" in arrhythmia_text

    def test_embed_arrhythmia_without_optional_fields(self, embedder, temp_dir):
        """Test arrhythmia embedding with missing optional fields"""
        minimal_data = {
            "arrhythmia_content": [
                {
                    "source": "Test",
                    "arrhythmia_type": "AF",
                    "ecg_features": ["Irregular rhythm"],
                    "differential_diagnosis": ["AFL"],
                    "clinical_pearls": ["Most common arrhythmia"]
                }
            ]
        }

        arrhythmia_file = temp_dir / "arrhythmia.json"
        arrhythmia_file.write_text(json.dumps(minimal_data))

        count = embedder.embed_arrhythmia_content(arrhythmia_file)

        assert count == 1

        # Check metadata reflects missing fields
        call_args = embedder.collections["arrhythmia"].upsert.call_args_list[0]
        metadata = call_args[1]['metadatas'][0]

        assert metadata['has_ep_correlation'] is False
        assert metadata['has_ablation_info'] is False

    # ---- LITFL Content ----

    def test_embed_litfl_diagnostic_pages(self, embedder, temp_dir, sample_litfl_data):
        """Test embedding LITFL diagnostic pages"""
        litfl_file = temp_dir / "litfl.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        page_count, case_count = embedder.embed_litfl_content(litfl_file)

        assert page_count == 1
        assert embedder.collections["textbook_content"].upsert.call_count >= 1

    def test_embed_litfl_case_series(self, embedder, temp_dir, sample_litfl_data):
        """Test embedding LITFL case series"""
        litfl_file = temp_dir / "litfl.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        page_count, case_count = embedder.embed_litfl_content(litfl_file)

        assert case_count == 1
        # Should be embedded in teaching_cases collection
        assert embedder.collections["teaching_cases"].upsert.call_count >= 1

    def test_embed_litfl_extracts_clinical_pearls(self, embedder, temp_dir, sample_litfl_data):
        """Test that clinical pearls are extracted from LITFL pages"""
        litfl_file = temp_dir / "litfl.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        embedder.embed_litfl_content(litfl_file)

        # Should embed clinical pearls (2) and key points (1) = 3 total
        assert embedder.collections["clinical_pearls"].upsert.call_count == 3

    def test_embed_litfl_ecg_features(self, embedder, temp_dir, sample_litfl_data):
        """Test that ECG features are embedded as diagnostic criteria"""
        litfl_file = temp_dir / "litfl.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        embedder.embed_litfl_content(litfl_file)

        # Should embed 2 ECG features
        assert embedder.collections["diagnostic_criteria"].upsert.call_count == 2

    # ---- Algorithms ----

    def test_embed_algorithms_with_steps(self, embedder, sample_algorithms):
        """Test embedding algorithms with step-by-step content"""
        count = embedder.embed_algorithms(sample_algorithms)

        assert count == 2
        assert embedder.collections["algorithms"].upsert.call_count == 2

    def test_embed_algorithms_formats_correctly(self, embedder, sample_algorithms):
        """Test algorithm text formatting"""
        embedder.embed_algorithms(sample_algorithms)

        # Check first algorithm
        call_args = embedder.collections["algorithms"].upsert.call_args_list[0]
        algo_text = call_args[1]['documents'][0]

        assert "Algorithm: Brugada Algorithm" in algo_text
        assert "Purpose: VT vs SVT differentiation" in algo_text
        assert "Year: 1991" in algo_text
        assert "Accuracy: 89% sensitivity" in algo_text
        assert "Steps:" in algo_text
        assert "1. Absence of RS complex" in algo_text

    # ---- embed_all ----

    def test_embed_all_runs_all_methods(self, embedder, temp_dir, sample_textbook_data,
                                        sample_teaching_cases, sample_arrhythmia_data,
                                        sample_litfl_data, sample_algorithms):
        """Test that embed_all runs all embedding methods"""
        # Setup data directory structure
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()

        content_file = extracted_dir / "extracted_content.json"
        combined_data = {
            "chunks": sample_textbook_data["chunks"],
            "cases": sample_teaching_cases["cases"],
            "arrhythmia_content": sample_arrhythmia_data["arrhythmia_content"]
        }
        content_file.write_text(json.dumps(combined_data))

        litfl_dir = temp_dir / "litfl_cache"
        litfl_dir.mkdir()
        litfl_file = litfl_dir / "litfl_complete.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        algo_file = temp_dir / "algorithms.json"
        algo_file.write_text(json.dumps(sample_algorithms))

        # Run embed_all
        stats = embedder.embed_all(temp_dir)

        assert stats.textbook_chunks == 2
        assert stats.teaching_cases == 2
        assert stats.arrhythmia_content == 2
        assert stats.litfl_pages == 1
        assert stats.litfl_cases == 1
        assert stats.algorithms == 2

    def test_embed_all_populates_stats(self, embedder, temp_dir):
        """Test that EmbeddingStats is populated correctly"""
        # Empty data directory
        (temp_dir / "extracted").mkdir()

        stats = embedder.embed_all(temp_dir)

        assert isinstance(stats, EmbeddingStats)
        assert stats.total_documents == 0
        assert stats.textbook_chunks == 0
        assert stats.teaching_cases == 0


# ============================================================================
# 5. QUERY TESTS (5+ tests)
# ============================================================================

class TestQueryInterface:
    """Test query functionality"""

    def test_query_single_collection(self, embedder):
        """Test querying a single collection"""
        results = embedder.query(
            "What is STEMI?",
            collections=["textbook_content"],
            n_results=5
        )

        assert "textbook_content" in results
        assert len(results) == 1

        # Verify query was called on the collection
        embedder.collections["textbook_content"].query.assert_called_once()

    def test_query_multiple_collections(self, embedder):
        """Test querying multiple collections"""
        results = embedder.query(
            "VT vs SVT differentiation",
            collections=["algorithms", "clinical_pearls"],
            n_results=3
        )

        assert "algorithms" in results
        assert "clinical_pearls" in results
        assert len(results) == 2

    def test_query_with_where_filter(self, embedder):
        """Test querying with metadata filter"""
        results = embedder.query(
            "AVNRT mechanism",
            collections=["arrhythmia"],
            where={"arrhythmia_type": "AVNRT"}
        )

        # Check that where clause was passed
        call_args = embedder.collections["arrhythmia"].query.call_args
        assert call_args[1]["where"] == {"arrhythmia_type": "AVNRT"}

    def test_query_returns_expected_structure(self, embedder):
        """Test that query returns expected result structure"""
        results = embedder.query("test query", collections=["textbook_content"])

        assert isinstance(results, dict)
        assert "textbook_content" in results

        # Result should have ChromaDB structure
        result_data = results["textbook_content"]
        assert "ids" in result_data
        assert "documents" in result_data
        assert "metadatas" in result_data
        assert "distances" in result_data

    def test_query_default_all_collections(self, embedder):
        """Test that query defaults to all collections"""
        results = embedder.query("test query")

        # Should query all 6 collections
        assert len(results) == 6
        assert all(coll in results for coll in ECGKnowledgeEmbedder.COLLECTIONS.keys())

    def test_query_skips_invalid_collections(self, embedder):
        """Test that invalid collection names are skipped"""
        results = embedder.query(
            "test",
            collections=["textbook_content", "invalid_collection", "algorithms"]
        )

        # Should only have valid collections
        assert "textbook_content" in results
        assert "algorithms" in results
        assert "invalid_collection" not in results
        assert len(results) == 2

    def test_get_stats_returns_counts(self, embedder):
        """Test get_stats returns document counts"""
        # Mock counts
        embedder.collections["textbook_content"].count.return_value = 100
        embedder.collections["teaching_cases"].count.return_value = 50
        embedder.collections["algorithms"].count.return_value = 10

        stats = embedder.get_stats()

        assert stats["textbook_content"] == 100
        assert stats["teaching_cases"] == 50
        assert stats["algorithms"] == 10
        assert len(stats) == 6  # All collections


# ============================================================================
# 6. INTEGRATION TESTS (3+ tests)
# ============================================================================

class TestIntegration:
    """Integration tests with realistic scenarios"""

    def test_full_embed_all_with_mock_data(self, embedder, temp_dir,
                                           sample_textbook_data, sample_teaching_cases,
                                           sample_arrhythmia_data, sample_litfl_data,
                                           sample_algorithms):
        """Test complete embedding pipeline"""
        # Setup complete data directory
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()

        content_file = extracted_dir / "extracted_content.json"
        combined_data = {
            "chunks": sample_textbook_data["chunks"],
            "cases": sample_teaching_cases["cases"],
            "arrhythmia_content": sample_arrhythmia_data["arrhythmia_content"]
        }
        content_file.write_text(json.dumps(combined_data))

        litfl_dir = temp_dir / "litfl_cache"
        litfl_dir.mkdir()
        litfl_file = litfl_dir / "litfl_complete.json"
        litfl_file.write_text(json.dumps(sample_litfl_data))

        algo_file = temp_dir / "algorithms.json"
        algo_file.write_text(json.dumps(sample_algorithms))

        # Run full embedding
        stats = embedder.embed_all(temp_dir)

        # Verify comprehensive stats
        # total_documents = textbook(2) + cases(2) + arrhythmia(2) + litfl_page(1) + litfl_cases(1) = 8
        assert stats.total_documents == 8
        assert stats.textbook_chunks == 2
        assert stats.teaching_cases == 2
        assert stats.arrhythmia_content == 2
        assert stats.litfl_pages == 1
        assert stats.litfl_cases == 1
        assert stats.algorithms == 2

        # Verify all collections were used
        assert embedder.collections["textbook_content"].upsert.call_count >= 2
        assert embedder.collections["teaching_cases"].upsert.call_count >= 2
        assert embedder.collections["arrhythmia"].upsert.call_count == 2
        assert embedder.collections["algorithms"].upsert.call_count == 2

    def test_query_after_embedding(self, embedder, temp_dir, sample_textbook_data):
        """Test querying after embedding returns results"""
        # Setup and embed data
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()
        content_file = extracted_dir / "extracted_content.json"
        content_file.write_text(json.dumps(sample_textbook_data))

        embedder.embed_textbook_content(content_file)

        # Query the embedded content
        results = embedder.query(
            "atrial depolarization",
            collections=["textbook_content"],
            n_results=2
        )

        assert "textbook_content" in results

        # Verify query was executed
        embedder.collections["textbook_content"].query.assert_called()
        call_args = embedder.collections["textbook_content"].query.call_args
        assert call_args[1]["query_texts"] == ["atrial depolarization"]
        assert call_args[1]["n_results"] == 2

    def test_upsert_updates_existing_documents(self, embedder, temp_dir, sample_textbook_data):
        """Test that upserting updates existing documents"""
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()
        content_file = extracted_dir / "extracted_content.json"
        content_file.write_text(json.dumps(sample_textbook_data))

        # First embedding
        count1 = embedder.embed_textbook_content(content_file)

        # Modify content
        sample_textbook_data["chunks"][0]["text"] = "Updated text content"
        content_file.write_text(json.dumps(sample_textbook_data))

        # Second embedding (should upsert)
        count2 = embedder.embed_textbook_content(content_file)

        assert count1 == count2 == 2

        # Upsert should be called 4 times total (2 + 2)
        assert embedder.collections["textbook_content"].upsert.call_count == 4

        # Check that same ID was used (deterministic hashing)
        first_call_id = embedder.collections["textbook_content"].upsert.call_args_list[0][1]['ids'][0]
        third_call_id = embedder.collections["textbook_content"].upsert.call_args_list[2][1]['ids'][0]
        assert first_call_id == third_call_id

    def test_handles_partial_data_gracefully(self, embedder, temp_dir):
        """Test that missing data files are handled gracefully"""
        # Only create textbook data, not LITFL or algorithms
        extracted_dir = temp_dir / "extracted"
        extracted_dir.mkdir()

        minimal_data = {"chunks": []}
        content_file = extracted_dir / "extracted_content.json"
        content_file.write_text(json.dumps(minimal_data))

        # Should not crash
        stats = embedder.embed_all(temp_dir)

        assert stats.textbook_chunks == 0
        assert stats.litfl_pages == 0
        assert stats.algorithms == 0
        assert stats.total_documents == 0


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_json_file(self, embedder, temp_dir):
        """Test handling of empty JSON file"""
        content_file = temp_dir / "empty.json"
        content_file.write_text("{}")

        count = embedder.embed_textbook_content(content_file)

        assert count == 0

    def test_malformed_json(self, embedder, temp_dir):
        """Test handling of malformed JSON"""
        content_file = temp_dir / "malformed.json"
        content_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            embedder.embed_textbook_content(content_file)

    def test_missing_required_fields(self, embedder, temp_dir):
        """Test handling of missing required fields in data"""
        incomplete_data = {
            "chunks": [
                {
                    # Missing 'source', 'chapter', 'text'
                    "chunk_index": 0
                }
            ]
        }

        content_file = temp_dir / "incomplete.json"
        content_file.write_text(json.dumps(incomplete_data))

        # Should raise KeyError for missing required fields
        with pytest.raises(KeyError):
            embedder.embed_textbook_content(content_file)

    def test_unicode_content(self, embedder, temp_dir):
        """Test handling of Unicode characters"""
        unicode_data = {
            "chunks": [
                {
                    "source": "Test",
                    "chapter": "Chapter 1",
                    "chunk_index": 0,
                    "text": "ECG showing δ waves and λ patterns with ∆ changes",
                    "topics": ["unicode"]
                }
            ]
        }

        content_file = temp_dir / "unicode.json"
        content_file.write_text(json.dumps(unicode_data, ensure_ascii=False))

        count = embedder.embed_textbook_content(content_file)

        assert count == 1

    def test_very_long_text_chunking(self, embedder):
        """Test chunking of very long text"""
        # Create text with 10,000 words
        long_text = " ".join([f"word{i}" for i in range(10000)])

        chunks = embedder._chunk_text(long_text, chunk_size=500, overlap=50)

        assert len(chunks) > 20
        assert all(len(chunk.split()) <= 500 for chunk in chunks[:-1])
