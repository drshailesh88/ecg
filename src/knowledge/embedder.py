"""
ECG Guru Knowledge Embedder

Embed extracted content into ChromaDB for RAG retrieval.
"""

import chromadb
from chromadb.config import Settings
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class EmbeddingStats:
    """Statistics from embedding operation"""
    total_documents: int
    textbook_chunks: int
    teaching_cases: int
    arrhythmia_content: int
    litfl_pages: int
    litfl_cases: int
    clinical_pearls: int
    algorithms: int


class ECGKnowledgeEmbedder:
    """
    Embed ECG knowledge into ChromaDB collections.

    Collections:
    - ecg_textbook_content: Chunked textbook content
    - ecg_teaching_cases: Teaching cases from Podrid, LITFL
    - ecg_arrhythmia: Arrhythmia-specific content from MK Das
    - ecg_diagnostic_criteria: ECG features and criteria
    - ecg_clinical_pearls: Clinical pearls and key points
    - ecg_algorithms: Algorithm explanations and steps
    """

    COLLECTIONS = {
        "textbook_content": "Chunked textbook chapters and sections",
        "teaching_cases": "Teaching cases with diagnoses",
        "arrhythmia": "Arrhythmia mechanisms and features",
        "diagnostic_criteria": "ECG diagnostic criteria",
        "clinical_pearls": "Clinical pearls and key points",
        "algorithms": "ECG interpretation algorithms",
    }

    def __init__(self, persist_dir: Path = None):
        self.persist_dir = persist_dir or Path("./data/chroma_db")
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create/get collections
        self.collections = {}
        for name, description in self.COLLECTIONS.items():
            self.collections[name] = self.client.get_or_create_collection(
                name=f"ecg_{name}",
                metadata={"description": description}
            )

    def _generate_id(self, *args) -> str:
        """Generate unique ID from arguments"""
        content = "_".join(str(a) for a in args)
        return hashlib.md5(content.encode()).hexdigest()

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def embed_textbook_content(self, content_file: Path) -> int:
        """Embed textbook content from extraction JSON"""
        if not content_file.exists():
            print(f"Content file not found: {content_file}")
            return 0

        data = json.loads(content_file.read_text())
        count = 0

        # Embed chunks
        for chunk in data.get("chunks", []):
            doc_id = self._generate_id(chunk["source"], chunk["chapter"], chunk["chunk_index"])

            self.collections["textbook_content"].upsert(
                ids=[doc_id],
                documents=[chunk["text"]],
                metadatas=[{
                    "source": chunk["source"],
                    "chapter": chunk["chapter"],
                    "section": chunk.get("section", ""),
                    "page": chunk.get("page", 0),
                    "topics": ",".join(chunk.get("topics", [])),
                }]
            )
            count += 1

        print(f"Embedded {count} textbook chunks")
        return count

    def embed_teaching_cases(self, content_file: Path) -> int:
        """Embed teaching cases"""
        if not content_file.exists():
            return 0

        data = json.loads(content_file.read_text())
        count = 0

        for case in data.get("cases", []):
            # Create rich case document
            case_text = f"""
Clinical Context: {case.get('clinical_context', '')}

ECG Description: {case.get('ecg_description', '')}

Analysis: {case.get('analysis', '')}

Diagnosis: {case.get('diagnosis', '')}

Teaching Points:
{chr(10).join('- ' + p for p in case.get('teaching_points', []))}
"""
            doc_id = case.get("case_id", self._generate_id(case["source"], case["case_number"]))

            self.collections["teaching_cases"].upsert(
                ids=[doc_id],
                documents=[case_text.strip()],
                metadatas=[{
                    "source": case.get("source", ""),
                    "volume": case.get("volume", ""),
                    "case_number": str(case.get("case_number", "")),
                    "diagnosis": case.get("diagnosis", ""),
                    "difficulty": case.get("difficulty", "intermediate"),
                    "topics": ",".join(case.get("topics", [])),
                }]
            )
            count += 1

        print(f"Embedded {count} teaching cases")
        return count

    def embed_arrhythmia_content(self, content_file: Path) -> int:
        """Embed arrhythmia-specific content"""
        if not content_file.exists():
            return 0

        data = json.loads(content_file.read_text())
        count = 0

        for arrhythmia in data.get("arrhythmia_content", []):
            # Create comprehensive arrhythmia document
            arrhythmia_text = f"""
Arrhythmia Type: {arrhythmia['arrhythmia_type']}

Mechanism: {arrhythmia.get('mechanism', '')}

ECG Features:
{chr(10).join('- ' + f for f in arrhythmia.get('ecg_features', []))}

Differential Diagnosis:
{chr(10).join('- ' + d for d in arrhythmia.get('differential_diagnosis', []))}

EP Correlation: {arrhythmia.get('ep_correlation', '')}

Ablation Targets: {arrhythmia.get('ablation_targets', '')}

Clinical Pearls:
{chr(10).join('- ' + p for p in arrhythmia.get('clinical_pearls', []))}
"""
            doc_id = self._generate_id(arrhythmia["source"], arrhythmia["arrhythmia_type"])

            self.collections["arrhythmia"].upsert(
                ids=[doc_id],
                documents=[arrhythmia_text.strip()],
                metadatas=[{
                    "source": arrhythmia.get("source", ""),
                    "arrhythmia_type": arrhythmia["arrhythmia_type"],
                    "has_ep_correlation": bool(arrhythmia.get("ep_correlation")),
                    "has_ablation_info": bool(arrhythmia.get("ablation_targets")),
                }]
            )
            count += 1

        print(f"Embedded {count} arrhythmia sections")
        return count

    def embed_litfl_content(self, litfl_file: Path) -> tuple:
        """Embed LITFL content"""
        if not litfl_file.exists():
            return 0, 0

        data = json.loads(litfl_file.read_text())
        page_count = 0
        case_count = 0
        pearl_count = 0

        # Embed diagnostic pages
        for page in data.get("diagnostic_pages", []):
            doc_id = self._generate_id("litfl", page["url"])

            # Main content
            self.collections["textbook_content"].upsert(
                ids=[doc_id],
                documents=[page["content"]],
                metadatas=[{
                    "source": "LITFL",
                    "title": page["title"],
                    "category": page["category"],
                    "url": page["url"],
                }]
            )
            page_count += 1

            # ECG features as criteria
            for i, feature in enumerate(page.get("ecg_features", [])):
                feature_id = self._generate_id("litfl_feature", page["title"], i)
                self.collections["diagnostic_criteria"].upsert(
                    ids=[feature_id],
                    documents=[feature],
                    metadatas=[{
                        "source": "LITFL",
                        "condition": page["title"],
                        "type": "ecg_feature",
                    }]
                )

            # Clinical pearls
            for i, pearl in enumerate(page.get("clinical_pearls", []) + page.get("key_points", [])):
                pearl_id = self._generate_id("litfl_pearl", page["title"], i)
                self.collections["clinical_pearls"].upsert(
                    ids=[pearl_id],
                    documents=[pearl],
                    metadatas=[{
                        "source": "LITFL",
                        "condition": page["title"],
                    }]
                )
                pearl_count += 1

        # Embed case series
        for series_name, cases in data.get("case_series", {}).items():
            for case in cases:
                case_text = f"""
Series: {series_name}
Title: {case.get('title', '')}

Clinical Scenario: {case.get('clinical_scenario', '')}

ECG Description: {case.get('ecg_description', '')}

Diagnosis: {case.get('diagnosis', '')}

Teaching Points:
{chr(10).join('- ' + p for p in case.get('teaching_points', []))}
"""
                case_id = self._generate_id("litfl", series_name, case["case_number"])

                self.collections["teaching_cases"].upsert(
                    ids=[case_id],
                    documents=[case_text.strip()],
                    metadatas=[{
                        "source": f"LITFL_{series_name}",
                        "series": series_name,
                        "case_number": str(case["case_number"]),
                        "diagnosis": case.get("diagnosis", ""),
                        "difficulty": "intermediate",  # LITFL cases vary
                    }]
                )
                case_count += 1

        print(f"Embedded {page_count} LITFL pages, {case_count} cases, {pearl_count} pearls")
        return page_count, case_count

    def embed_algorithms(self, algorithms: List[Dict]) -> int:
        """Embed algorithm definitions"""
        count = 0

        for algo in algorithms:
            # Full algorithm explanation
            algo_text = f"""
Algorithm: {algo['name']}
Purpose: {algo.get('purpose', '')}
Year: {algo.get('year', '')}
Accuracy: {algo.get('accuracy', '')}

{algo.get('full_explanation', '')}

Steps:
"""
            for step in algo.get("steps", []):
                algo_text += f"\n{step['number']}. {step.get('criterion', '')}\n   {step.get('explanation', '')}"

            doc_id = self._generate_id("algorithm", algo["name"])

            self.collections["algorithms"].upsert(
                ids=[doc_id],
                documents=[algo_text.strip()],
                metadatas=[{
                    "name": algo["name"],
                    "purpose": algo.get("purpose", ""),
                    "year": str(algo.get("year", "")),
                    "accuracy": algo.get("accuracy", ""),
                    "citation": algo.get("citation", ""),
                }]
            )
            count += 1

        print(f"Embedded {count} algorithms")
        return count

    def embed_all(self, data_dir: Path) -> EmbeddingStats:
        """Embed all available content"""
        stats = EmbeddingStats(
            total_documents=0,
            textbook_chunks=0,
            teaching_cases=0,
            arrhythmia_content=0,
            litfl_pages=0,
            litfl_cases=0,
            clinical_pearls=0,
            algorithms=0,
        )

        # Textbook content
        textbook_file = data_dir / "extracted" / "extracted_content.json"
        if textbook_file.exists():
            stats.textbook_chunks = self.embed_textbook_content(textbook_file)
            stats.teaching_cases = self.embed_teaching_cases(textbook_file)
            stats.arrhythmia_content = self.embed_arrhythmia_content(textbook_file)

        # LITFL content
        litfl_file = data_dir / "litfl_cache" / "litfl_complete.json"
        if litfl_file.exists():
            stats.litfl_pages, stats.litfl_cases = self.embed_litfl_content(litfl_file)

        # Count clinical pearls
        stats.clinical_pearls = self.collections["clinical_pearls"].count()

        # Algorithms (from predefined list)
        algo_file = data_dir / "algorithms.json"
        if algo_file.exists():
            algos = json.loads(algo_file.read_text())
            stats.algorithms = self.embed_algorithms(algos)

        # Total
        stats.total_documents = sum([
            stats.textbook_chunks,
            stats.teaching_cases,
            stats.arrhythmia_content,
            stats.litfl_pages,
            stats.litfl_cases,
        ])

        return stats

    def query(
        self,
        query_text: str,
        collections: List[str] = None,
        n_results: int = 5,
        where: Dict = None
    ) -> Dict[str, Any]:
        """Query one or more collections"""

        collections = collections or list(self.COLLECTIONS.keys())
        results = {}

        for coll_name in collections:
            if coll_name not in self.collections:
                continue

            coll = self.collections[coll_name]

            query_kwargs = {
                "query_texts": [query_text],
                "n_results": n_results,
            }
            if where:
                query_kwargs["where"] = where

            results[coll_name] = coll.query(**query_kwargs)

        return results

    def get_stats(self) -> Dict[str, int]:
        """Get document counts per collection"""
        return {name: coll.count() for name, coll in self.collections.items()}


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Embed ECG knowledge into ChromaDB")
    parser.add_argument("--data-dir", type=Path, default="./data",
                       help="Directory with extracted content")
    parser.add_argument("--persist-dir", type=Path, default="./data/chroma_db",
                       help="ChromaDB persistence directory")
    parser.add_argument("--query", type=str, help="Test query")

    args = parser.parse_args()

    embedder = ECGKnowledgeEmbedder(persist_dir=args.persist_dir)

    if args.query:
        results = embedder.query(args.query)
        print(json.dumps(results, indent=2, default=str))
    else:
        stats = embedder.embed_all(args.data_dir)
        print("\nEmbedding Statistics:")
        print(f"  Total documents: {stats.total_documents}")
        print(f"  Textbook chunks: {stats.textbook_chunks}")
        print(f"  Teaching cases: {stats.teaching_cases}")
        print(f"  Arrhythmia content: {stats.arrhythmia_content}")
        print(f"  LITFL pages: {stats.litfl_pages}")
        print(f"  LITFL cases: {stats.litfl_cases}")
        print(f"  Clinical pearls: {stats.clinical_pearls}")
        print(f"  Algorithms: {stats.algorithms}")


if __name__ == "__main__":
    main()
