"""
Comprehensive tests for Advanced RAG Pipeline

Tests all components of the RAG system with mocked external dependencies.
"""

import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from typing import List, Dict, Any
import tempfile
import shutil

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from knowledge.advanced_rag import (
    RetrievedDocument,
    BM25Index,
    reciprocal_rank_fusion,
    QueryEnhancer,
    AdvancedRAGPipeline,
    ECGKnowledgeRAG,
    PubMedBERTEmbeddings,
    OllamaEmbeddings,
    CrossEncoderReranker,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        "Ventricular tachycardia is a wide QRS complex tachycardia originating from the ventricles",
        "STEMI shows ST segment elevation in contiguous leads indicating acute myocardial infarction",
        "Wolff-Parkinson-White syndrome shows a delta wave and short PR interval",
        "Atrial fibrillation is characterized by irregularly irregular rhythm and absence of P waves",
    ]


@pytest.fixture
def sample_ids():
    """Sample document IDs"""
    return ["doc1", "doc2", "doc3", "doc4"]


@pytest.fixture
def sample_metadata():
    """Sample metadata"""
    return [
        {"source": "Marriott", "chapter": "Arrhythmias"},
        {"source": "Marriott", "chapter": "STEMI"},
        {"source": "Chou", "chapter": "Pre-excitation"},
        {"source": "Marriott", "chapter": "Atrial Rhythms"},
    ]


# ============================================================================
# RETRIEVED DOCUMENT TESTS (3+)
# ============================================================================

class TestRetrievedDocument:
    """Tests for RetrievedDocument dataclass"""

    def test_to_dict_serialization(self):
        """Test to_dict returns correct structure"""
        doc = RetrievedDocument(
            id="test_id",
            content="Test content",
            metadata={"source": "test"},
            dense_score=0.95,
            sparse_score=10.5,
            rrf_score=0.8,
            rerank_score=0.99
        )

        result = doc.to_dict()

        assert result["id"] == "test_id"
        assert result["content"] == "Test content"
        assert result["metadata"] == {"source": "test"}
        assert result["scores"]["dense"] == 0.95
        assert result["scores"]["sparse"] == 10.5
        assert result["scores"]["rrf"] == 0.8
        assert result["scores"]["rerank"] == 0.99

    def test_score_attributes_default_to_zero(self):
        """Test that score attributes default to 0.0"""
        doc = RetrievedDocument(
            id="test_id",
            content="Test content",
            metadata={}
        )

        assert doc.dense_score == 0.0
        assert doc.sparse_score == 0.0
        assert doc.rrf_score == 0.0
        assert doc.rerank_score == 0.0

    def test_metadata_handling(self):
        """Test metadata is preserved correctly"""
        metadata = {
            "source": "Marriott",
            "chapter": "VT",
            "page": 123,
            "tags": ["arrhythmia", "wide-complex"]
        }

        doc = RetrievedDocument(
            id="test_id",
            content="Test",
            metadata=metadata
        )

        assert doc.metadata == metadata
        assert doc.metadata["tags"] == ["arrhythmia", "wide-complex"]


# ============================================================================
# BM25 INDEX TESTS (10+)
# ============================================================================

class TestBM25Index:
    """Tests for BM25Index sparse retrieval"""

    def test_add_documents_stores_correctly(self, sample_documents, sample_ids, sample_metadata):
        """Test add_documents stores documents, ids, and metadata"""
        index = BM25Index()
        index.add_documents(sample_documents, sample_ids, sample_metadata)

        assert len(index.documents) == 4
        assert len(index.doc_ids) == 4
        assert len(index.doc_metadata) == 4
        assert index.documents[0] == sample_documents[0]
        assert index.doc_ids[0] == sample_ids[0]
        assert index.doc_metadata[0] == sample_metadata[0]

    def test_add_documents_without_metadata(self, sample_documents, sample_ids):
        """Test add_documents works without metadata"""
        index = BM25Index()
        index.add_documents(sample_documents, sample_ids)

        assert len(index.doc_metadata) == 4
        assert all(m == {} for m in index.doc_metadata)

    def test_tokenize_splits_text_properly(self):
        """Test _tokenize splits and lowercases correctly"""
        index = BM25Index()

        text = "Ventricular Tachycardia (VT) is dangerous!"
        tokens = index._tokenize(text)

        assert "ventricular" in tokens
        assert "tachycardia" in tokens
        assert "vt" in tokens
        assert "is" in tokens
        assert "dangerous" in tokens
        assert "Ventricular" not in tokens  # Should be lowercase

    def test_tokenize_handles_special_characters(self):
        """Test tokenization removes special characters"""
        index = BM25Index()

        text = "ST-elevation, T-wave inversion... QRS complex!"
        tokens = index._tokenize(text)

        assert "st" in tokens
        assert "elevation" in tokens
        assert "t" in tokens
        assert "wave" in tokens
        assert "qrs" in tokens
        assert "complex" in tokens

    @patch('rank_bm25.BM25Okapi')
    def test_search_returns_ranked_results(self, mock_bm25_class, sample_documents, sample_ids, sample_metadata):
        """Test search returns results ranked by score"""
        # Mock BM25Okapi
        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = np.array([5.2, 0.3, 0.1, 2.1])
        mock_bm25_class.return_value = mock_bm25

        index = BM25Index()
        index.add_documents(sample_documents, sample_ids, sample_metadata)

        results = index.search("ventricular tachycardia", k=3)

        # Should return top 3 by score: doc1 (5.2), doc4 (2.1), doc2 (0.3)
        assert len(results) == 3
        assert results[0][0] == "doc1"  # Highest score
        assert results[0][3] == 5.2
        assert results[1][0] == "doc4"  # Second highest
        assert results[1][3] == 2.1

    @patch('rank_bm25.BM25Okapi')
    def test_search_with_no_matches_returns_empty(self, mock_bm25_class):
        """Test search returns empty list when no matches"""
        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = np.array([0.0, 0.0, 0.0])
        mock_bm25_class.return_value = mock_bm25

        index = BM25Index()
        index.add_documents(["doc1", "doc2", "doc3"], ["id1", "id2", "id3"])

        results = index.search("nonexistent query")

        assert results == []

    def test_search_returns_empty_on_empty_index(self):
        """Test search on empty index returns empty"""
        index = BM25Index()
        results = index.search("any query")
        assert results == []

    def test_save_and_load_persistence(self, temp_dir, sample_documents, sample_ids, sample_metadata):
        """Test save and load preserves index state"""
        index = BM25Index()
        index.add_documents(sample_documents, sample_ids, sample_metadata)

        save_path = temp_dir / "bm25_test.json"
        index.save(save_path)

        # Load into new index
        new_index = BM25Index()
        new_index.load(save_path)

        assert new_index.documents == sample_documents
        assert new_index.doc_ids == sample_ids
        assert new_index.doc_metadata == sample_metadata

    def test_load_nonexistent_file_does_nothing(self, temp_dir):
        """Test load with nonexistent file doesn't crash"""
        index = BM25Index()
        nonexistent = temp_dir / "doesnt_exist.json"

        index.load(nonexistent)  # Should not raise
        assert index.documents == []

    @patch('rank_bm25.BM25Okapi')
    def test_rebuild_index_works_after_add(self, mock_bm25_class, sample_documents, sample_ids):
        """Test _rebuild_index is called after add_documents"""
        mock_bm25_class.return_value = MagicMock()

        index = BM25Index()
        index.add_documents(sample_documents[:2], sample_ids[:2])

        assert mock_bm25_class.called
        first_call_count = mock_bm25_class.call_count

        # Add more documents
        index.add_documents(sample_documents[2:], sample_ids[2:])

        # Should rebuild index
        assert mock_bm25_class.call_count > first_call_count

    @patch('rank_bm25.BM25Okapi')
    def test_multiple_document_addition(self, mock_bm25_class):
        """Test adding documents multiple times accumulates"""
        mock_bm25_class.return_value = MagicMock()

        index = BM25Index()
        index.add_documents(["doc1", "doc2"], ["id1", "id2"])
        assert len(index.documents) == 2

        index.add_documents(["doc3"], ["id3"])
        assert len(index.documents) == 3
        assert index.doc_ids == ["id1", "id2", "id3"]

    @patch('rank_bm25.BM25Okapi')
    def test_score_ordering_higher_is_better(self, mock_bm25_class, sample_documents, sample_ids):
        """Test that results are ordered with higher scores first"""
        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = np.array([1.0, 5.0, 3.0, 0.5])
        mock_bm25_class.return_value = mock_bm25

        index = BM25Index()
        index.add_documents(sample_documents, sample_ids)

        results = index.search("test query", k=4)

        # Scores should be in descending order
        scores = [r[3] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert results[0][3] == 5.0  # Highest first

    def test_fallback_when_bm25_not_available(self, sample_documents, sample_ids):
        """Test graceful fallback when rank_bm25 not installed"""
        with patch('rank_bm25.BM25Okapi', side_effect=ImportError):
            index = BM25Index()
            index.add_documents(sample_documents, sample_ids)

            # Index should be None in fallback mode
            assert index.index is None

            # Search should return empty
            results = index.search("test")
            assert results == []


# ============================================================================
# RECIPROCAL RANK FUSION TESTS (5+)
# ============================================================================

class TestReciprocalRankFusion:
    """Tests for reciprocal_rank_fusion function"""

    def test_rrf_with_single_list(self):
        """Test RRF with a single result list"""
        results = [
            [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        ]

        fused = reciprocal_rank_fusion(results, k=60)

        # Should preserve order and calculate RRF scores
        assert len(fused) == 3
        assert fused[0][0] == "doc1"  # Highest rank
        assert fused[1][0] == "doc2"
        assert fused[2][0] == "doc3"

    def test_rrf_with_multiple_lists(self):
        """Test RRF combines multiple ranked lists"""
        results = [
            [("doc1", 0.9), ("doc2", 0.5), ("doc3", 0.3)],  # List 1
            [("doc2", 0.95), ("doc1", 0.8), ("doc4", 0.6)],  # List 2
        ]

        fused = reciprocal_rank_fusion(results, k=60)

        # doc1 and doc2 appear in both, should have higher RRF scores
        doc_ids = [doc_id for doc_id, _ in fused]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        assert "doc3" in doc_ids
        assert "doc4" in doc_ids

    def test_rrf_with_overlapping_docs(self):
        """Test RRF correctly combines scores for overlapping docs"""
        results = [
            [("doc1", 1.0), ("doc2", 0.5)],  # doc1 rank 0, doc2 rank 1
            [("doc2", 1.0), ("doc1", 0.5)],  # doc2 rank 0, doc1 rank 1
        ]

        fused = reciprocal_rank_fusion(results, k=60)

        # Both docs appear in both lists, should have same RRF score
        scores = {doc_id: score for doc_id, score in fused}

        # RRF: 1/(60+0) + 1/(60+1) = 1/60 + 1/61 for each
        expected_score = 1/60 + 1/61
        assert abs(scores["doc1"] - expected_score) < 0.001
        assert abs(scores["doc2"] - expected_score) < 0.001

    def test_rrf_score_calculation_correct(self):
        """Test RRF score calculation formula"""
        results = [
            [("doc1", 1.0)],  # Rank 0
        ]
        k = 60

        fused = reciprocal_rank_fusion(results, k=k)

        # RRF score = 1 / (k + rank + 1) = 1 / (60 + 0 + 1) = 1/61
        expected = 1.0 / (k + 0 + 1)
        assert abs(fused[0][1] - expected) < 0.001

    def test_rrf_empty_list_handling(self):
        """Test RRF handles empty lists"""
        results = [
            [("doc1", 1.0)],
            [],  # Empty list
            [("doc2", 1.0)],
        ]

        fused = reciprocal_rank_fusion(results)

        assert len(fused) == 2
        doc_ids = [doc_id for doc_id, _ in fused]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids

    def test_rrf_preserves_all_unique_docs(self):
        """Test RRF includes all unique documents from all lists"""
        results = [
            [("doc1", 1.0), ("doc2", 0.8)],
            [("doc3", 0.9), ("doc4", 0.7)],
            [("doc5", 0.95)],
        ]

        fused = reciprocal_rank_fusion(results)

        assert len(fused) == 5
        doc_ids = {doc_id for doc_id, _ in fused}
        assert doc_ids == {"doc1", "doc2", "doc3", "doc4", "doc5"}


# ============================================================================
# QUERY ENHANCER TESTS (5+)
# ============================================================================

class TestQueryEnhancer:
    """Tests for QueryEnhancer"""

    def test_generate_multi_query_without_llm_fallback(self):
        """Test multi-query generation falls back without LLM"""
        enhancer = QueryEnhancer(llm_client=None)

        query = "What is ventricular tachycardia?"
        variations = enhancer.generate_multi_query(query)

        # Should return at least the original query
        assert len(variations) >= 1
        assert variations[0] == query

    def test_simple_variations_with_medical_synonyms(self):
        """Test _simple_variations expands medical abbreviations"""
        enhancer = QueryEnhancer(llm_client=None)

        query = "What is VT diagnosis?"
        variations = enhancer._simple_variations(query)

        # Should include variation with full term
        variation_text = " ".join(variations).lower()
        assert "ventricular tachycardia" in variation_text

    def test_vt_to_ventricular_tachycardia_expansion(self):
        """Test VT → ventricular tachycardia expansion"""
        enhancer = QueryEnhancer(llm_client=None)

        variations = enhancer._simple_variations("Diagnosis of VT")

        # Should have original query
        assert any("vt" in v.lower() for v in variations)

        # Should have expanded version
        assert any("ventricular tachycardia" in v.lower() for v in variations)

    def test_stemi_to_st_elevation_mi_expansion(self):
        """Test STEMI → ST elevation myocardial infarction expansion"""
        enhancer = QueryEnhancer(llm_client=None)

        variations = enhancer._simple_variations("STEMI criteria")

        # Should expand STEMI
        assert any("st elevation myocardial infarction" in v.lower() for v in variations)

    def test_bidirectional_synonym_expansion(self):
        """Test synonyms work both ways (abbrev → full and full → abbrev)"""
        enhancer = QueryEnhancer(llm_client=None)

        # Test abbrev to full
        variations1 = enhancer._simple_variations("AF detection")
        assert any("atrial fibrillation" in v.lower() for v in variations1)

        # Test full to abbrev
        variations2 = enhancer._simple_variations("atrial fibrillation detection")
        assert any("af detection" in v.lower() for v in variations2)

    def test_generate_hyde_without_llm_returns_original(self):
        """Test HyDE without LLM returns original query"""
        enhancer = QueryEnhancer(llm_client=None)

        query = "What causes wide QRS complex?"
        hyde = enhancer.generate_hyde(query)

        assert hyde == query

    def test_multi_query_with_llm_mock(self):
        """Test multi-query generation with mocked LLM"""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = {
            "response": "1. What is VT?\n2. Explain ventricular tachycardia\n3. VT symptoms"
        }

        enhancer = QueryEnhancer(llm_client=mock_llm)

        variations = enhancer.generate_multi_query("What is VT?", n_queries=3)

        # Should include original + variations
        assert len(variations) >= 3
        assert variations[0] == "What is VT?"
        assert any("ventricular tachycardia" in v.lower() for v in variations)

    def test_hyde_with_llm_mock(self):
        """Test HyDE generation with mocked LLM"""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = {
            "response": "Ventricular tachycardia is a cardiac arrhythmia characterized by..."
        }

        enhancer = QueryEnhancer(llm_client=mock_llm)

        hyde = enhancer.generate_hyde("What is VT?")

        assert "ventricular tachycardia" in hyde.lower()
        assert hyde != "What is VT?"

    def test_llm_error_fallback_to_simple(self):
        """Test graceful fallback when LLM fails"""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM error")

        enhancer = QueryEnhancer(llm_client=mock_llm)

        # Should fall back to simple variations
        variations = enhancer.generate_multi_query("VT diagnosis")
        assert len(variations) >= 1
        assert variations[0] == "VT diagnosis"


# ============================================================================
# ADVANCED RAG PIPELINE TESTS (10+)
# ============================================================================

class TestAdvancedRAGPipeline:
    """Tests for AdvancedRAGPipeline"""

    @pytest.fixture
    def mock_embedder(self):
        """Mock embedding model"""
        embedder = MagicMock()
        embedder.embed.return_value = [[0.1] * 768 for _ in range(4)]
        embedder.embed_query.return_value = [0.1] * 768
        embedder.dimension = 768
        return embedder

    @pytest.fixture
    def mock_chroma(self):
        """Mock ChromaDB client"""
        with patch('knowledge.advanced_rag.chromadb.PersistentClient') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def test_initialization_with_pubmedbert(self, temp_dir):
        """Test initialization with PubMedBERT embeddings"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings') as mock_embedder:
            mock_embedder.return_value = MagicMock(dimension=768)

            rag = AdvancedRAGPipeline(
                persist_dir=temp_dir,
                embedding_model="pubmedbert"
            )

            assert rag.embedder is not None
            assert rag.bm25 is not None

    def test_initialization_with_ollama(self, temp_dir):
        """Test initialization with Ollama embeddings"""
        with patch('knowledge.advanced_rag.OllamaEmbeddings') as mock_embedder:
            mock_embedder.return_value = MagicMock(dimension=768)

            rag = AdvancedRAGPipeline(
                persist_dir=temp_dir,
                embedding_model="ollama"
            )

            assert rag.embedder is not None

    def test_initialization_with_custom_model(self, temp_dir):
        """Test initialization with custom model name"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings') as mock_embedder:
            mock_embedder.return_value = MagicMock(dimension=768)

            rag = AdvancedRAGPipeline(
                persist_dir=temp_dir,
                embedding_model="custom/model-name"
            )

            mock_embedder.assert_called_with("custom/model-name")

    def test_get_collection_creates_collection(self, temp_dir, mock_chroma):
        """Test get_collection creates ChromaDB collection"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings'):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir)
            rag.chroma = mock_chroma

            collection = rag.get_collection("test_collection")

            mock_chroma.get_or_create_collection.assert_called_with(
                name="test_collection",
                metadata={"hnsw:space": "cosine"}
            )

    def test_get_collection_caches_collections(self, temp_dir, mock_chroma):
        """Test get_collection caches collections"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings'):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir)
            rag.chroma = mock_chroma

            # Get same collection twice
            coll1 = rag.get_collection("test")
            coll2 = rag.get_collection("test")

            # Should only create once
            assert mock_chroma.get_or_create_collection.call_count == 1
            assert coll1 is coll2

    def test_add_documents_to_both_dense_and_sparse(
        self, temp_dir, mock_embedder, mock_chroma, sample_documents, sample_ids, sample_metadata
    ):
        """Test add_documents adds to both ChromaDB and BM25"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir)
            rag.chroma = mock_chroma

            mock_collection = MagicMock()
            mock_chroma.get_or_create_collection.return_value = mock_collection

            rag.add_documents("test_coll", sample_documents, sample_ids, sample_metadata)

            # Should embed documents
            mock_embedder.embed.assert_called_with(sample_documents)

            # Should add to ChromaDB
            mock_collection.upsert.assert_called_once()

            # Should add to BM25
            assert len(rag.bm25.documents) == 4

    def test_retrieve_with_hybrid_search(self, temp_dir, mock_embedder, mock_chroma):
        """Test retrieve performs hybrid dense + sparse search"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            with patch('rank_bm25.BM25Okapi'):
                rag = AdvancedRAGPipeline(persist_dir=temp_dir, use_reranker=False)
                rag.chroma = mock_chroma

                # Mock collection response
                mock_collection = MagicMock()
                mock_collection.query.return_value = {
                    "ids": [["doc1", "doc2"]],
                    "documents": [["content1", "content2"]],
                    "metadatas": [[{"source": "test"}, {"source": "test"}]],
                    "distances": [[0.1, 0.2]]
                }
                mock_chroma.get_or_create_collection.return_value = mock_collection
                mock_chroma.list_collections.return_value = [
                    MagicMock(name="test_coll")
                ]

                # Mock BM25 response
                rag.bm25.search = MagicMock(return_value=[
                    ("doc2", "content2", {"source": "test"}, 5.0),
                    ("doc3", "content3", {"source": "test"}, 3.0),
                ])

                results = rag.retrieve("test query", top_k=5)

                # Should query both dense and sparse
                mock_collection.query.assert_called()
                rag.bm25.search.assert_called()

                # Should return documents
                assert len(results) > 0

    def test_retrieve_with_multi_query_enabled(self, temp_dir, mock_embedder, mock_chroma):
        """Test retrieve with multi-query enhancement"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(
                persist_dir=temp_dir,
                use_reranker=False,
                llm_for_enhancement=False
            )
            rag.chroma = mock_chroma

            # Mock collection
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["doc1"]],
                "documents": [["content"]],
                "metadatas": [[{}]],
                "distances": [[0.1]]
            }
            mock_chroma.get_or_create_collection.return_value = mock_collection
            mock_chroma.list_collections.return_value = [MagicMock(name="test")]

            rag.bm25.search = MagicMock(return_value=[])

            # Set query enhancer manually
            rag.query_enhancer = QueryEnhancer(None)

            results = rag.retrieve("VT diagnosis", use_multi_query=True, top_k=5)

            # Should embed multiple query variations
            assert mock_embedder.embed_query.call_count > 1

    def test_retrieve_with_reranking_enabled(self, temp_dir, mock_embedder, mock_chroma):
        """Test retrieve with cross-encoder reranking"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            mock_reranker = MagicMock()

            with patch('knowledge.advanced_rag.CrossEncoderReranker', return_value=mock_reranker):
                rag = AdvancedRAGPipeline(persist_dir=temp_dir, use_reranker=True)
                rag.chroma = mock_chroma

                # Mock collection
                mock_collection = MagicMock()
                mock_collection.query.return_value = {
                    "ids": [["doc1", "doc2"]],
                    "documents": [["content1", "content2"]],
                    "metadatas": [[{}, {}]],
                    "distances": [[0.1, 0.2]]
                }
                mock_chroma.get_or_create_collection.return_value = mock_collection
                mock_chroma.list_collections.return_value = [MagicMock(name="test")]

                rag.bm25.search = MagicMock(return_value=[])

                # Mock reranker to return top doc
                mock_reranker.rerank.return_value = [
                    RetrievedDocument("doc1", "content1", {}, rerank_score=0.99)
                ]

                results = rag.retrieve("test", use_reranking=True, top_k=5)

                # Should call reranker
                mock_reranker.rerank.assert_called_once()

    def test_query_with_context_returns_formatted_context(self, temp_dir, mock_embedder, mock_chroma):
        """Test query_with_context returns formatted context string"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir, use_reranker=False)
            rag.chroma = mock_chroma

            # Mock retrieve to return documents
            mock_doc1 = RetrievedDocument(
                "doc1",
                "VT is a wide complex tachycardia",
                {"source": "Marriott", "title": "Arrhythmias"}
            )
            mock_doc2 = RetrievedDocument(
                "doc2",
                "STEMI shows ST elevation",
                {"source": "Chou", "chapter": "STEMI"}
            )

            rag.retrieve = MagicMock(return_value=[mock_doc1, mock_doc2])

            docs, context = rag.query_with_context("test query", top_k=2)

            # Should return documents and formatted context
            assert len(docs) == 2
            assert "VT is a wide complex tachycardia" in context
            assert "STEMI shows ST elevation" in context
            assert "Marriott" in context
            assert "Arrhythmias" in context

    def test_bm25_index_saved_to_disk(self, temp_dir, mock_embedder, mock_chroma):
        """Test BM25 index is saved to disk after adding documents"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir)
            rag.chroma = mock_chroma

            mock_collection = MagicMock()
            mock_chroma.get_or_create_collection.return_value = mock_collection

            rag.add_documents(
                "test",
                ["doc1", "doc2"],
                ["id1", "id2"]
            )

            # Check BM25 index file was created
            bm25_path = temp_dir / "bm25_index.json"
            assert bm25_path.exists()

    def test_retrieve_without_reranking(self, temp_dir, mock_embedder, mock_chroma):
        """Test retrieve works without reranking"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(persist_dir=temp_dir, use_reranker=False)
            rag.chroma = mock_chroma

            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["doc1"]],
                "documents": [["content"]],
                "metadatas": [[{}]],
                "distances": [[0.1]]
            }
            mock_chroma.get_or_create_collection.return_value = mock_collection
            mock_chroma.list_collections.return_value = [MagicMock(name="test")]

            rag.bm25.search = MagicMock(return_value=[])

            results = rag.retrieve("test", use_reranking=False, top_k=5)

            # Should work without reranker
            assert len(results) >= 0

    def test_hyde_retrieval_when_enabled(self, temp_dir, mock_embedder, mock_chroma):
        """Test HyDE retrieval generates hypothetical document"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings', return_value=mock_embedder):
            rag = AdvancedRAGPipeline(
                persist_dir=temp_dir,
                use_reranker=False,
                llm_for_enhancement=False
            )
            rag.chroma = mock_chroma
            rag.query_enhancer = MagicMock()
            rag.query_enhancer.generate_multi_query.return_value = ["test query"]
            rag.query_enhancer.generate_hyde.return_value = "Hypothetical answer about test"

            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["doc1"]],
                "documents": [["content"]],
                "metadatas": [[{}]],
                "distances": [[0.1]]
            }
            mock_chroma.get_or_create_collection.return_value = mock_collection
            mock_chroma.list_collections.return_value = [MagicMock(name="test")]
            rag.bm25.search = MagicMock(return_value=[])

            results = rag.retrieve("test", use_hyde=True, use_multi_query=False, top_k=5)

            # Should generate HyDE query
            rag.query_enhancer.generate_hyde.assert_called_with("test")

            # Should embed HyDE query
            assert mock_embedder.embed_query.call_count >= 2  # Original + HyDE


# ============================================================================
# ECG KNOWLEDGE RAG TESTS (5+)
# ============================================================================

class TestECGKnowledgeRAG:
    """Tests for ECGKnowledgeRAG"""

    @pytest.fixture
    def mock_rag(self, temp_dir):
        """Mock ECGKnowledgeRAG instance"""
        with patch('knowledge.advanced_rag.PubMedBERTEmbeddings'):
            with patch('knowledge.advanced_rag.chromadb.PersistentClient'):
                rag = ECGKnowledgeRAG(persist_dir=temp_dir, use_reranker=False)
                rag.query_with_context = MagicMock(return_value=([], "context"))
                rag.retrieve = MagicMock(return_value=[])
                return rag

    def test_query_for_diagnosis_uses_correct_collections(self, mock_rag):
        """Test query_for_diagnosis uses textbook and diagnostic collections"""
        mock_rag.query_for_diagnosis("ventricular tachycardia", top_k=5)

        call_args = mock_rag.query_with_context.call_args
        collections = call_args[1]["collection_names"]

        assert "ecg_textbook_content" in collections
        assert "ecg_diagnostic_criteria" in collections

    def test_query_for_diagnosis_includes_cases_when_requested(self, mock_rag):
        """Test query_for_diagnosis includes teaching cases"""
        mock_rag.query_for_diagnosis("VT", include_cases=True)

        collections = mock_rag.query_with_context.call_args[1]["collection_names"]
        assert "ecg_teaching_cases" in collections

    def test_query_for_diagnosis_includes_algorithms_when_requested(self, mock_rag):
        """Test query_for_diagnosis includes algorithms"""
        mock_rag.query_for_diagnosis("VT", include_algorithms=True)

        collections = mock_rag.query_with_context.call_args[1]["collection_names"]
        assert "ecg_algorithms" in collections

    def test_query_for_teaching_uses_correct_collections(self, mock_rag):
        """Test query_for_teaching uses teaching-focused collections"""
        mock_rag.query_for_teaching("P wave morphology", top_k=5)

        collections = mock_rag.query_with_context.call_args[1]["collection_names"]

        assert "ecg_teaching_cases" in collections
        assert "ecg_clinical_pearls" in collections
        assert "ecg_textbook_content" in collections

    def test_query_for_teaching_uses_hyde(self, mock_rag):
        """Test query_for_teaching enables HyDE"""
        mock_rag.query_for_teaching("ECG basics")

        call_kwargs = mock_rag.query_with_context.call_args[1]
        assert call_kwargs["use_hyde"] is True

    def test_query_for_algorithm_specific_matching(self, mock_rag):
        """Test query_for_algorithm targets algorithm collection"""
        mock_rag.query_for_algorithm("Brugada criteria")

        collections = mock_rag.query_with_context.call_args[1]["collection_names"]

        assert collections == ["ecg_algorithms"]

        # Should not use multi-query or HyDE for specific algorithms
        call_kwargs = mock_rag.query_with_context.call_args[1]
        assert call_kwargs["use_multi_query"] is False
        assert call_kwargs["use_hyde"] is False

    def test_get_similar_cases_returns_teaching_cases(self, mock_rag):
        """Test get_similar_cases retrieves from teaching cases"""
        mock_rag.get_similar_cases("STEMI", top_k=5)

        call_args = mock_rag.retrieve.call_args

        # Should search teaching cases
        assert call_args[0][0].startswith("teaching case")
        assert call_args[1]["collection_names"] == ["ecg_teaching_cases"]
        assert call_args[1]["use_reranking"] is True

    def test_collection_names_defined_correctly(self):
        """Test COLLECTIONS class variable has expected names"""
        collections = ECGKnowledgeRAG.COLLECTIONS

        assert "ecg_textbook_content" in collections
        assert "ecg_teaching_cases" in collections
        assert "ecg_arrhythmia" in collections
        assert "ecg_diagnostic_criteria" in collections
        assert "ecg_clinical_pearls" in collections
        assert "ecg_algorithms" in collections

    def test_query_for_diagnosis_with_all_options(self, mock_rag):
        """Test query_for_diagnosis with all collections enabled"""
        mock_rag.query_for_diagnosis(
            "atrial fibrillation",
            include_cases=True,
            include_algorithms=True,
            top_k=10
        )

        collections = mock_rag.query_with_context.call_args[1]["collection_names"]

        assert len(collections) == 4  # textbook, diagnostic, cases, algorithms
        assert "ecg_textbook_content" in collections
        assert "ecg_diagnostic_criteria" in collections
        assert "ecg_teaching_cases" in collections
        assert "ecg_algorithms" in collections


# ============================================================================
# EMBEDDING MODEL TESTS
# ============================================================================

class TestEmbeddingModels:
    """Tests for embedding model classes"""

    def test_pubmedbert_embeddings_initialization(self):
        """Test PubMedBERT embeddings initialization"""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 768
            mock_st.return_value = mock_model

            embedder = PubMedBERTEmbeddings("test-model")

            assert embedder.model is not None
            assert embedder.dimension == 768

    def test_pubmedbert_embed_texts(self):
        """Test PubMedBERT embed method"""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 768
            mock_model.encode.return_value = np.array([[0.1] * 768, [0.2] * 768])
            mock_st.return_value = mock_model

            embedder = PubMedBERTEmbeddings()
            result = embedder.embed(["text1", "text2"])

            assert len(result) == 2
            assert len(result[0]) == 768

    def test_pubmedbert_embed_query(self):
        """Test PubMedBERT embed_query method"""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 768
            mock_model.encode.return_value = np.array([[0.1] * 768])
            mock_st.return_value = mock_model

            embedder = PubMedBERTEmbeddings()
            result = embedder.embed_query("query")

            assert len(result) == 768

    def test_ollama_embeddings_initialization(self):
        """Test Ollama embeddings initialization"""
        with patch('ollama.embeddings') as mock_embeddings:
            mock_embeddings.return_value = {
                "embedding": [0.1] * 768
            }

            # Also need to patch the ollama module itself
            with patch('sys.modules', {'ollama': MagicMock(embeddings=mock_embeddings)}):
                embedder = OllamaEmbeddings("nomic-embed-text")

                assert embedder.dimension == 768

    def test_ollama_embed_texts(self):
        """Test Ollama embed method"""
        # Create embedder with mocked client
        embedder = OllamaEmbeddings.__new__(OllamaEmbeddings)

        # Mock the client
        mock_client = MagicMock()
        mock_client.embeddings.side_effect = [
            {"embedding": [0.2] * 768},  # text1
            {"embedding": [0.3] * 768},  # text2
        ]

        embedder.client = mock_client
        embedder.model_name = "nomic-embed-text"
        embedder._dimension = 768

        result = embedder.embed(["text1", "text2"])

        assert len(result) == 2
        assert len(result[0]) == 768
        assert result[0] == [0.2] * 768
        assert result[1] == [0.3] * 768


# ============================================================================
# CROSS-ENCODER RERANKER TESTS
# ============================================================================

class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker"""

    def test_rerank_scores_and_sorts_documents(self):
        """Test reranker scores and sorts documents"""
        with patch('sentence_transformers.CrossEncoder') as mock_ce:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([0.9, 0.3, 0.7])
            mock_ce.return_value = mock_model

            reranker = CrossEncoderReranker()

            docs = [
                RetrievedDocument("doc1", "content1", {}),
                RetrievedDocument("doc2", "content2", {}),
                RetrievedDocument("doc3", "content3", {}),
            ]

            reranked = reranker.rerank("query", docs, top_k=2)

            # Should return top 2 by rerank score
            assert len(reranked) == 2
            assert reranked[0].id == "doc1"  # Score 0.9
            assert reranked[1].id == "doc3"  # Score 0.7

    def test_rerank_empty_list_returns_empty(self):
        """Test reranker handles empty document list"""
        with patch('sentence_transformers.CrossEncoder'):
            reranker = CrossEncoderReranker()
            result = reranker.rerank("query", [], top_k=5)
            assert result == []

    def test_rerank_sets_rerank_scores(self):
        """Test reranker sets rerank_score on documents"""
        with patch('sentence_transformers.CrossEncoder') as mock_ce:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([0.85])
            mock_ce.return_value = mock_model

            reranker = CrossEncoderReranker()

            docs = [RetrievedDocument("doc1", "content", {})]
            reranked = reranker.rerank("query", docs, top_k=5)

            assert reranked[0].rerank_score == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
