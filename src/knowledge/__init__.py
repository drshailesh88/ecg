"""
ECG Guru Knowledge Base Module

Components:
- textbook_processor: Extract content from PDF textbooks
- litfl_scraper: Harvest content from LITFL ECG Library
- embedder: Embed content into ChromaDB for RAG
- advanced_rag: State-of-the-art RAG with hybrid retrieval
"""

from .textbook_processor import (
    PodridProcessor,
    MKDasProcessor,
    GenericMedicalPDFProcessor,
    TextChunk,
    TeachingCase,
    ArrhythmiaContent,
    process_all_textbooks,
)

from .litfl_scraper import (
    LITFLScraper,
    LITFLPage,
    LITFLCase,
)

from .embedder import (
    ECGKnowledgeEmbedder,
    EmbeddingStats,
)

from .advanced_rag import (
    # Core classes
    AdvancedRAGPipeline,
    ECGKnowledgeRAG,
    RetrievedDocument,
    # Embedding models
    PubMedBERTEmbeddings,
    OllamaEmbeddings,
    # Retrieval components
    BM25Index,
    CrossEncoderReranker,
    QueryEnhancer,
    # Utilities
    reciprocal_rank_fusion,
)

__all__ = [
    # Textbook processing
    "PodridProcessor",
    "MKDasProcessor",
    "GenericMedicalPDFProcessor",
    "TextChunk",
    "TeachingCase",
    "ArrhythmiaContent",
    "process_all_textbooks",
    # LITFL
    "LITFLScraper",
    "LITFLPage",
    "LITFLCase",
    # Basic Embedding
    "ECGKnowledgeEmbedder",
    "EmbeddingStats",
    # Advanced RAG (recommended)
    "AdvancedRAGPipeline",
    "ECGKnowledgeRAG",
    "RetrievedDocument",
    "PubMedBERTEmbeddings",
    "OllamaEmbeddings",
    "BM25Index",
    "CrossEncoderReranker",
    "QueryEnhancer",
    "reciprocal_rank_fusion",
]
