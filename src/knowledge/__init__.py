"""
ECG Guru Knowledge Base Module

Components:
- textbook_processor: Extract content from PDF textbooks
- litfl_scraper: Harvest content from LITFL ECG Library
- embedder: Embed content into ChromaDB for RAG
- rag_pipeline: Query knowledge for reasoning
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
    # Embedding
    "ECGKnowledgeEmbedder",
    "EmbeddingStats",
]
