"""
Advanced RAG Pipeline for ECG Guru

Implements state-of-the-art retrieval techniques:
- Hybrid retrieval: Dense (PubMedBERT) + Sparse (BM25)
- Reciprocal Rank Fusion (RRF) for result merging
- Multi-query generation for comprehensive coverage
- HyDE (Hypothetical Document Embeddings)
- Cross-encoder reranking for precision
"""

import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import re
from pathlib import Path
import hashlib


@dataclass
class RetrievedDocument:
    """A retrieved document with metadata and scores"""
    id: str
    content: str
    metadata: Dict[str, Any]
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "scores": {
                "dense": self.dense_score,
                "sparse": self.sparse_score,
                "rrf": self.rrf_score,
                "rerank": self.rerank_score,
            }
        }


class EmbeddingModel(ABC):
    """Abstract base class for embedding models"""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


class PubMedBERTEmbeddings(EmbeddingModel):
    """
    Medical-domain embeddings using PubMedBERT.

    Options:
    - NeuML/pubmedbert-base-embeddings (recommended)
    - pritamdeka/S-PubMedBert-MS-MARCO (sentence-level, 29% more precise)
    """

    def __init__(self, model_name: str = "NeuML/pubmedbert-base-embeddings"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self._dimension = self.model.get_sentence_embedding_dimension()
            self.model_name = model_name
        except ImportError:
            raise ImportError(
                "sentence-transformers required. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        embedding = self.model.encode([query], show_progress_bar=False)
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dimension


class OllamaEmbeddings(EmbeddingModel):
    """
    Embeddings via Ollama for fully offline operation.
    Uses nomic-embed-text or similar.
    """

    def __init__(self, model_name: str = "nomic-embed-text"):
        try:
            import ollama
            self.client = ollama
            self.model_name = model_name
            # Get dimension by embedding a test string
            test = self.client.embeddings(model=model_name, prompt="test")
            self._dimension = len(test["embedding"])
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ollama embeddings: {e}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = self.client.embeddings(model=self.model_name, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        response = self.client.embeddings(model=self.model_name, prompt=query)
        return response["embedding"]

    @property
    def dimension(self) -> int:
        return self._dimension


class BM25Index:
    """
    BM25 sparse retrieval index.
    Simple implementation for hybrid search.
    """

    def __init__(self):
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.doc_metadata: List[Dict] = []
        self.index = None

    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict] = None
    ):
        """Add documents to the BM25 index"""
        self.documents.extend(documents)
        self.doc_ids.extend(ids)
        self.doc_metadata.extend(metadatas or [{} for _ in documents])
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the BM25 index"""
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [self._tokenize(doc) for doc in self.documents]
            self.index = BM25Okapi(tokenized)
        except ImportError:
            # Fallback to simple TF-IDF-like scoring
            self.index = None

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def search(self, query: str, k: int = 20) -> List[Tuple[str, str, Dict, float]]:
        """
        Search the index.
        Returns: List of (doc_id, content, metadata, score)
        """
        if not self.index or not self.documents:
            return []

        query_tokens = self._tokenize(query)
        scores = self.index.get_scores(query_tokens)

        # Get top k
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((
                    self.doc_ids[idx],
                    self.documents[idx],
                    self.doc_metadata[idx],
                    float(scores[idx])
                ))

        return results

    def save(self, path: Path):
        """Save index to disk"""
        data = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "doc_metadata": self.doc_metadata,
        }
        path.write_text(json.dumps(data))

    def load(self, path: Path):
        """Load index from disk"""
        if path.exists():
            data = json.loads(path.read_text())
            self.documents = data["documents"]
            self.doc_ids = data["doc_ids"]
            self.doc_metadata = data["doc_metadata"]
            self._rebuild_index()


class CrossEncoderReranker:
    """
    Neural reranking using cross-encoder models.

    Options:
    - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, general)
    - cross-encoder/ms-marco-MiniLM-L-12-v2 (better accuracy)
    - For medical: Consider fine-tuning on medical QA pairs
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.model_name = model_name
        except ImportError:
            raise ImportError(
                "sentence-transformers required. Install with: "
                "pip install sentence-transformers"
            )

    def rerank(
        self,
        query: str,
        documents: List[RetrievedDocument],
        top_k: int = 10
    ) -> List[RetrievedDocument]:
        """Rerank documents using cross-encoder"""
        if not documents:
            return []

        # Create pairs for cross-encoder
        pairs = [(query, doc.content) for doc in documents]

        # Get scores
        scores = self.model.predict(pairs)

        # Add scores to documents
        for doc, score in zip(documents, scores):
            doc.rerank_score = float(score)

        # Sort by rerank score and return top_k
        sorted_docs = sorted(documents, key=lambda x: x.rerank_score, reverse=True)
        return sorted_docs[:top_k]


class QueryEnhancer:
    """
    Query enhancement techniques:
    - Multi-query: Generate query variations
    - HyDE: Hypothetical Document Embeddings
    """

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: Ollama client or similar for query generation
        """
        self.llm_client = llm_client

    def generate_multi_query(self, query: str, n_queries: int = 3) -> List[str]:
        """Generate query variations for better recall"""
        if not self.llm_client:
            # Fallback: simple variations
            return self._simple_variations(query)

        prompt = f"""Generate {n_queries} different versions of this medical/ECG question.
Each version should ask the same thing but with different wording.
Return only the questions, one per line.

Original question: {query}

Variations:"""

        try:
            response = self.llm_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.7}
            )
            variations = response["response"].strip().split("\n")
            variations = [v.strip().lstrip("0123456789.-) ") for v in variations if v.strip()]
            return [query] + variations[:n_queries]
        except:
            return self._simple_variations(query)

    def _simple_variations(self, query: str) -> List[str]:
        """Simple query variations without LLM"""
        variations = [query]

        # Add medical synonyms
        medical_synonyms = {
            "heart attack": "myocardial infarction",
            "MI": "myocardial infarction",
            "STEMI": "ST elevation myocardial infarction",
            "VT": "ventricular tachycardia",
            "SVT": "supraventricular tachycardia",
            "AF": "atrial fibrillation",
            "AFib": "atrial fibrillation",
            "WPW": "Wolff-Parkinson-White",
        }

        query_lower = query.lower()
        for abbrev, full in medical_synonyms.items():
            if abbrev.lower() in query_lower:
                variations.append(query_lower.replace(abbrev.lower(), full))
            elif full.lower() in query_lower:
                variations.append(query_lower.replace(full.lower(), abbrev))

        return variations[:4]

    def generate_hyde(self, query: str) -> str:
        """
        Generate a hypothetical answer document for better retrieval.
        The embedding of this hypothetical answer often matches
        relevant documents better than the query itself.
        """
        if not self.llm_client:
            return query

        prompt = f"""You are an expert cardiologist and electrophysiologist.
Write a detailed answer to this ECG/cardiology question as if from a medical textbook.
Be specific and technical.

Question: {query}

Answer:"""

        try:
            response = self.llm_client.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                options={"temperature": 0.3, "num_predict": 300}
            )
            return response["response"].strip()
        except:
            return query


def reciprocal_rank_fusion(
    result_lists: List[List[Tuple[str, float]]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion to combine multiple ranked lists.

    Args:
        result_lists: List of (doc_id, score) tuples for each retrieval method
        k: RRF constant (default 60)

    Returns:
        Fused list of (doc_id, rrf_score) sorted by score
    """
    rrf_scores: Dict[str, float] = {}

    for results in result_lists:
        for rank, (doc_id, _) in enumerate(results):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
            rrf_scores[doc_id] += 1.0 / (k + rank + 1)

    # Sort by RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


class AdvancedRAGPipeline:
    """
    Production-ready RAG pipeline with advanced techniques.

    Features:
    - Hybrid retrieval (Dense + BM25)
    - Reciprocal Rank Fusion
    - Multi-query generation
    - HyDE (Hypothetical Document Embeddings)
    - Cross-encoder reranking
    """

    def __init__(
        self,
        persist_dir: Path = None,
        embedding_model: str = "pubmedbert",  # "pubmedbert", "ollama", or model name
        use_reranker: bool = True,
        llm_for_enhancement: bool = True,
    ):
        self.persist_dir = persist_dir or Path("./data/chroma_db")
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        if embedding_model == "pubmedbert":
            self.embedder = PubMedBERTEmbeddings("NeuML/pubmedbert-base-embeddings")
        elif embedding_model == "s-pubmedbert":
            self.embedder = PubMedBERTEmbeddings("pritamdeka/S-PubMedBert-MS-MARCO")
        elif embedding_model == "ollama":
            self.embedder = OllamaEmbeddings("nomic-embed-text")
        else:
            self.embedder = PubMedBERTEmbeddings(embedding_model)

        # Initialize ChromaDB for dense retrieval
        self.chroma = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize BM25 for sparse retrieval
        self.bm25 = BM25Index()
        bm25_path = self.persist_dir / "bm25_index.json"
        if bm25_path.exists():
            self.bm25.load(bm25_path)

        # Initialize reranker
        self.reranker = None
        if use_reranker:
            try:
                self.reranker = CrossEncoderReranker()
            except ImportError:
                print("Warning: Cross-encoder not available, skipping reranking")

        # Initialize query enhancer
        self.query_enhancer = None
        if llm_for_enhancement:
            try:
                import ollama
                self.query_enhancer = QueryEnhancer(ollama)
            except:
                self.query_enhancer = QueryEnhancer(None)

        # Collection cache
        self._collections: Dict[str, Any] = {}

    def get_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        if name not in self._collections:
            self._collections[name] = self.chroma.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collections[name]

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict] = None
    ):
        """Add documents to both dense and sparse indexes"""
        metadatas = metadatas or [{} for _ in documents]

        # Add to ChromaDB (dense)
        collection = self.get_collection(collection_name)
        embeddings = self.embedder.embed(documents)

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # Add to BM25 (sparse)
        self.bm25.add_documents(documents, ids, metadatas)

        # Save BM25 index
        self.bm25.save(self.persist_dir / "bm25_index.json")

    def retrieve(
        self,
        query: str,
        collection_names: List[str] = None,
        top_k: int = 10,
        dense_k: int = 20,
        sparse_k: int = 20,
        rrf_k: int = 60,
        use_multi_query: bool = True,
        use_hyde: bool = False,
        use_reranking: bool = True,
    ) -> List[RetrievedDocument]:
        """
        Advanced retrieval with all techniques.

        Args:
            query: User query
            collection_names: Collections to search (None = all)
            top_k: Final number of results
            dense_k: Results from dense retrieval
            sparse_k: Results from sparse retrieval
            rrf_k: RRF fusion constant
            use_multi_query: Generate query variations
            use_hyde: Use hypothetical document embeddings
            use_reranking: Apply cross-encoder reranking
        """
        # Get all collection names if not specified
        if collection_names is None:
            collection_names = [c.name for c in self.chroma.list_collections()]

        # Query enhancement
        queries = [query]
        if use_multi_query and self.query_enhancer:
            queries = self.query_enhancer.generate_multi_query(query)

        hyde_query = None
        if use_hyde and self.query_enhancer:
            hyde_query = self.query_enhancer.generate_hyde(query)

        # Collect results from all queries and methods
        all_dense_results: List[Tuple[str, float]] = []
        all_sparse_results: List[Tuple[str, float]] = []
        doc_cache: Dict[str, RetrievedDocument] = {}

        for q in queries:
            # Dense retrieval
            q_embedding = self.embedder.embed_query(q)

            for coll_name in collection_names:
                collection = self.get_collection(coll_name)
                results = collection.query(
                    query_embeddings=[q_embedding],
                    n_results=dense_k,
                    include=["documents", "metadatas", "distances"]
                )

                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    # Convert distance to similarity (cosine)
                    score = 1 - distance

                    all_dense_results.append((doc_id, score))

                    if doc_id not in doc_cache:
                        doc_cache[doc_id] = RetrievedDocument(
                            id=doc_id,
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i],
                            dense_score=score
                        )
                    else:
                        doc_cache[doc_id].dense_score = max(
                            doc_cache[doc_id].dense_score, score
                        )

            # Sparse retrieval (BM25)
            sparse_results = self.bm25.search(q, k=sparse_k)
            for doc_id, content, metadata, score in sparse_results:
                all_sparse_results.append((doc_id, score))

                if doc_id not in doc_cache:
                    doc_cache[doc_id] = RetrievedDocument(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                        sparse_score=score
                    )
                else:
                    doc_cache[doc_id].sparse_score = max(
                        doc_cache[doc_id].sparse_score, score
                    )

        # HyDE retrieval if enabled
        if hyde_query and hyde_query != query:
            hyde_embedding = self.embedder.embed_query(hyde_query)
            for coll_name in collection_names:
                collection = self.get_collection(coll_name)
                results = collection.query(
                    query_embeddings=[hyde_embedding],
                    n_results=dense_k,
                    include=["documents", "metadatas", "distances"]
                )

                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    score = 1 - distance
                    all_dense_results.append((doc_id, score))

                    if doc_id not in doc_cache:
                        doc_cache[doc_id] = RetrievedDocument(
                            id=doc_id,
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i],
                            dense_score=score
                        )

        # Reciprocal Rank Fusion
        fused_results = reciprocal_rank_fusion(
            [all_dense_results, all_sparse_results],
            k=rrf_k
        )

        # Update RRF scores in documents
        for doc_id, rrf_score in fused_results:
            if doc_id in doc_cache:
                doc_cache[doc_id].rrf_score = rrf_score

        # Get documents sorted by RRF score
        sorted_docs = sorted(
            doc_cache.values(),
            key=lambda x: x.rrf_score,
            reverse=True
        )

        # Reranking
        if use_reranking and self.reranker:
            # Take more candidates for reranking
            candidates = sorted_docs[:min(len(sorted_docs), top_k * 3)]
            final_docs = self.reranker.rerank(query, candidates, top_k=top_k)
        else:
            final_docs = sorted_docs[:top_k]

        return final_docs

    def query_with_context(
        self,
        query: str,
        collection_names: List[str] = None,
        top_k: int = 5,
        **kwargs
    ) -> Tuple[List[RetrievedDocument], str]:
        """
        Retrieve documents and format as context for LLM.

        Returns:
            Tuple of (documents, formatted_context)
        """
        docs = self.retrieve(query, collection_names, top_k, **kwargs)

        # Format context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", doc.metadata.get("chapter", ""))

            context_parts.append(f"""
[Source {i}: {source} - {title}]
{doc.content}
""")

        context = "\n---\n".join(context_parts)

        return docs, context


class ECGKnowledgeRAG(AdvancedRAGPipeline):
    """
    ECG-specific RAG pipeline with medical knowledge collections.
    """

    COLLECTIONS = [
        "ecg_textbook_content",
        "ecg_teaching_cases",
        "ecg_arrhythmia",
        "ecg_diagnostic_criteria",
        "ecg_clinical_pearls",
        "ecg_algorithms",
    ]

    def query_for_diagnosis(
        self,
        diagnosis: str,
        include_cases: bool = True,
        include_algorithms: bool = True,
        top_k: int = 5
    ) -> Tuple[List[RetrievedDocument], str]:
        """Query knowledge base for a specific diagnosis"""
        collections = ["ecg_textbook_content", "ecg_diagnostic_criteria"]

        if include_cases:
            collections.append("ecg_teaching_cases")
        if include_algorithms:
            collections.append("ecg_algorithms")

        return self.query_with_context(
            diagnosis,
            collection_names=collections,
            top_k=top_k,
            use_multi_query=True,
            use_hyde=False,  # Diagnosis queries are specific
            use_reranking=True
        )

    def query_for_teaching(
        self,
        topic: str,
        difficulty: str = None,
        top_k: int = 5
    ) -> Tuple[List[RetrievedDocument], str]:
        """Query for teaching content on a topic"""
        collections = [
            "ecg_teaching_cases",
            "ecg_clinical_pearls",
            "ecg_textbook_content"
        ]

        return self.query_with_context(
            topic,
            collection_names=collections,
            top_k=top_k,
            use_multi_query=True,
            use_hyde=True,  # HyDE helps for educational queries
            use_reranking=True
        )

    def query_for_algorithm(
        self,
        algorithm_name: str
    ) -> Tuple[List[RetrievedDocument], str]:
        """Query for algorithm details"""
        return self.query_with_context(
            algorithm_name,
            collection_names=["ecg_algorithms"],
            top_k=3,
            use_multi_query=False,
            use_hyde=False,
            use_reranking=False  # Algorithms are specific matches
        )

    def get_similar_cases(
        self,
        diagnosis: str,
        top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Get similar teaching cases for a diagnosis"""
        return self.retrieve(
            f"teaching case {diagnosis}",
            collection_names=["ecg_teaching_cases"],
            top_k=top_k,
            use_multi_query=True,
            use_hyde=False,
            use_reranking=True
        )


def main():
    """Test the advanced RAG pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Advanced RAG Pipeline")
    parser.add_argument("query", type=str, help="Query to test")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-rerank", action="store_true")
    parser.add_argument("--no-multiquery", action="store_true")
    parser.add_argument("--hyde", action="store_true")

    args = parser.parse_args()

    # Initialize pipeline
    rag = ECGKnowledgeRAG(
        persist_dir=Path("./data/chroma_db"),
        embedding_model="pubmedbert",
        use_reranker=not args.no_rerank
    )

    # Query
    docs, context = rag.query_with_context(
        args.query,
        top_k=args.top_k,
        use_multi_query=not args.no_multiquery,
        use_hyde=args.hyde
    )

    print(f"Query: {args.query}")
    print(f"Retrieved {len(docs)} documents\n")

    for i, doc in enumerate(docs, 1):
        print(f"--- Document {i} ---")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Scores: Dense={doc.dense_score:.3f}, Sparse={doc.sparse_score:.3f}, "
              f"RRF={doc.rrf_score:.3f}, Rerank={doc.rerank_score:.3f}")
        print(f"Content: {doc.content[:300]}...")
        print()


if __name__ == "__main__":
    main()
