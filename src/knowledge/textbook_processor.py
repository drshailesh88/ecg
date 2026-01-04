"""
ECG Guru Knowledge Extraction Pipeline
Extract and process ECG knowledge from textbooks and online sources
"""

import fitz  # PyMuPDF
import re
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Generator
from abc import ABC, abstractmethod


@dataclass
class TextChunk:
    """A chunk of text with metadata"""
    text: str
    source: str
    chapter: str
    section: Optional[str]
    page: int
    chunk_index: int
    topics: List[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def id(self) -> str:
        """Generate unique ID for this chunk"""
        content = f"{self.source}_{self.chapter}_{self.page}_{self.chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class TeachingCase:
    """A teaching case from a textbook"""
    case_id: str
    source: str
    volume: str
    case_number: str
    clinical_context: str
    ecg_description: str
    analysis: str
    diagnosis: str
    teaching_points: List[str]
    difficulty: str  # beginner, intermediate, advanced, expert
    topics: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ArrhythmiaContent:
    """Arrhythmia-specific content from MK Das or similar"""
    arrhythmia_type: str
    mechanism: str
    ecg_features: List[str]
    differential_diagnosis: List[str]
    ep_correlation: str
    ablation_targets: str
    clinical_pearls: List[str]
    source: str

    def to_dict(self) -> dict:
        return asdict(self)


class TextbookProcessor(ABC):
    """Base class for textbook processing"""

    def __init__(self, pdf_path: Path, source_name: str):
        self.pdf_path = pdf_path
        self.source_name = source_name
        self.doc = fitz.open(pdf_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.doc.close()

    def extract_text_by_page(self) -> Generator[tuple, None, None]:
        """Extract text page by page"""
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text("text")
            yield page_num, text

    def extract_with_formatting(self) -> Generator[dict, None, None]:
        """Extract text with font information for structure detection"""
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    spans = line["spans"]
                    if not spans:
                        continue

                    text = "".join(span["text"] for span in spans)
                    font_size = spans[0]["size"]
                    font_name = spans[0]["font"]
                    is_bold = "Bold" in font_name or "bold" in font_name

                    yield {
                        "page": page_num,
                        "text": text,
                        "font_size": font_size,
                        "font_name": font_name,
                        "is_bold": is_bold,
                        "bbox": line["bbox"]
                    }

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    @abstractmethod
    def extract_chapters(self) -> List[dict]:
        """Extract chapters - implement in subclass"""
        pass

    @abstractmethod
    def extract_structured_content(self) -> List[TextChunk]:
        """Extract structured content - implement in subclass"""
        pass


class PodridProcessor(TextbookProcessor):
    """
    Process Podrid's Real-World ECGs

    Structure:
    - Each volume has numbered cases
    - Each case: Clinical context → ECG → Analysis → Teaching points
    - Volumes: 1 (Basics), 2 (MI), 3 (Conduction), 4A/4B (Arrhythmias),
               5A/5B (WCT), 6 (Paced/Other)
    """

    CASE_PATTERN = re.compile(r'Case\s+(\d+[-.]?\d*)', re.IGNORECASE)
    SECTION_PATTERNS = {
        'clinical': re.compile(r'(Clinical\s+(?:History|Presentation|Context)|History|Presentation)', re.IGNORECASE),
        'ecg': re.compile(r'(ECG|Electrocardiogram|12-Lead)', re.IGNORECASE),
        'analysis': re.compile(r'(Analysis|Interpretation|Discussion)', re.IGNORECASE),
        'teaching': re.compile(r'(Teaching\s+Points?|Key\s+Points?|Summary|Pearls)', re.IGNORECASE),
    }

    def __init__(self, pdf_path: Path, volume: str = ""):
        super().__init__(pdf_path, f"Podrid_{volume}")
        self.volume = volume or self._detect_volume()

    def _detect_volume(self) -> str:
        """Try to detect volume from filename or content"""
        filename = self.pdf_path.name.lower()

        if "volume1" in filename or "vol1" in filename or "basics" in filename:
            return "Vol1_Basics"
        elif "volume2" in filename or "vol2" in filename or "myocardial" in filename:
            return "Vol2_MI"
        elif "volume3" in filename or "vol3" in filename or "conduction" in filename:
            return "Vol3_Conduction"
        elif "volume4" in filename or "vol4" in filename or "arrhythmia" in filename:
            return "Vol4_Arrhythmias"
        elif "volume5" in filename or "vol5" in filename or "tachycardia" in filename:
            return "Vol5_WCT"
        elif "volume6" in filename or "vol6" in filename or "paced" in filename:
            return "Vol6_Other"
        else:
            return "Unknown"

    def extract_chapters(self) -> List[dict]:
        """Extract chapter structure"""
        chapters = []
        current_chapter = {"title": "", "start_page": 0, "content": []}

        for line_data in self.extract_with_formatting():
            # Detect chapter headings (usually larger font, bold)
            if line_data["font_size"] > 16 and line_data["is_bold"]:
                text = line_data["text"].strip()
                if text and len(text) > 3:
                    if current_chapter["content"]:
                        chapters.append(current_chapter)
                    current_chapter = {
                        "title": text,
                        "start_page": line_data["page"],
                        "content": []
                    }
            else:
                current_chapter["content"].append(line_data["text"])

        if current_chapter["content"]:
            chapters.append(current_chapter)

        return chapters

    def extract_cases(self) -> List[TeachingCase]:
        """Extract individual cases from Podrid"""
        cases = []
        full_text = ""

        # Get all text
        for page_num, text in self.extract_text_by_page():
            full_text += f"\n[PAGE {page_num}]\n{text}"

        # Split by case pattern
        case_splits = self.CASE_PATTERN.split(full_text)

        # Process pairs: case_splits[0] is intro, then alternating case_num, content
        for i in range(1, len(case_splits) - 1, 2):
            case_num = case_splits[i]
            case_content = case_splits[i + 1] if i + 1 < len(case_splits) else ""

            # Extract sections
            clinical = self._extract_section(case_content, 'clinical')
            ecg_desc = self._extract_section(case_content, 'ecg')
            analysis = self._extract_section(case_content, 'analysis')
            teaching = self._extract_section(case_content, 'teaching')

            # Infer diagnosis from analysis
            diagnosis = self._extract_diagnosis(analysis)

            # Infer difficulty
            difficulty = self._infer_difficulty(case_content)

            # Extract topics
            topics = self._extract_topics(case_content)

            case = TeachingCase(
                case_id=f"podrid_{self.volume}_{case_num}",
                source="Podrid",
                volume=self.volume,
                case_number=case_num,
                clinical_context=clinical,
                ecg_description=ecg_desc,
                analysis=analysis,
                diagnosis=diagnosis,
                teaching_points=self._split_teaching_points(teaching),
                difficulty=difficulty,
                topics=topics
            )
            cases.append(case)

        return cases

    def _extract_section(self, text: str, section_type: str) -> str:
        """Extract a section from case text"""
        pattern = self.SECTION_PATTERNS.get(section_type)
        if not pattern:
            return ""

        match = pattern.search(text)
        if not match:
            return ""

        start = match.end()

        # Find where next section starts
        end = len(text)
        for other_type, other_pattern in self.SECTION_PATTERNS.items():
            if other_type == section_type:
                continue
            other_match = other_pattern.search(text[start:])
            if other_match:
                end = min(end, start + other_match.start())

        return text[start:end].strip()

    def _extract_diagnosis(self, analysis: str) -> str:
        """Extract primary diagnosis from analysis"""
        # Look for common diagnosis patterns
        patterns = [
            r'diagnosis[:\s]+([^.]+)',
            r'this\s+(?:is|represents)\s+([^.]+)',
            r'consistent\s+with\s+([^.]+)',
            r'findings\s+(?:of|indicate)\s+([^.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Return first sentence as fallback
        first_sentence = analysis.split('.')[0] if analysis else ""
        return first_sentence[:200]

    def _split_teaching_points(self, teaching_text: str) -> List[str]:
        """Split teaching points into list"""
        if not teaching_text:
            return []

        # Split by bullet points, numbers, or newlines
        points = re.split(r'[\n•●◦\-]\s*|\d+[.)]\s*', teaching_text)
        return [p.strip() for p in points if p.strip() and len(p.strip()) > 10]

    def _infer_difficulty(self, content: str) -> str:
        """Infer difficulty level from content"""
        content_lower = content.lower()

        expert_keywords = ['pathway localization', 'ablation', 'mechanism', 'electrophysiology',
                          'reentry', 'accessory pathway', 'vt origin']
        advanced_keywords = ['wide complex', 'svt', 'avnrt', 'avrt', 'brugada', 'wpw']
        intermediate_keywords = ['st elevation', 'stemi', 'block', 'hypertrophy', 'axis']

        if any(kw in content_lower for kw in expert_keywords):
            return "expert"
        elif any(kw in content_lower for kw in advanced_keywords):
            return "advanced"
        elif any(kw in content_lower for kw in intermediate_keywords):
            return "intermediate"
        else:
            return "beginner"

    def _extract_topics(self, content: str) -> List[str]:
        """Extract relevant topics from content"""
        topics = []
        content_lower = content.lower()

        topic_keywords = {
            'STEMI': ['stemi', 'st elevation', 'myocardial infarction', 'heart attack'],
            'Arrhythmia': ['arrhythmia', 'rhythm', 'tachycardia', 'bradycardia'],
            'VT': ['ventricular tachycardia', 'vt ', 'wide complex'],
            'SVT': ['supraventricular', 'svt', 'narrow complex'],
            'AVNRT': ['avnrt', 'av nodal', 'reentrant'],
            'AVRT': ['avrt', 'accessory pathway', 'wpw', 'pre-excitation'],
            'AF': ['atrial fibrillation', 'afib', 'a-fib'],
            'Block': ['heart block', 'av block', 'bundle branch'],
            'Ischemia': ['ischemia', 'ischemic', 'st depression'],
            'Hypertrophy': ['hypertrophy', 'lvh', 'rvh', 'enlargement'],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)

        return topics

    def extract_structured_content(self) -> List[TextChunk]:
        """Extract all content as structured chunks"""
        chunks = []

        for chapter in self.extract_chapters():
            chapter_text = "\n".join(chapter["content"])
            text_chunks = self.chunk_text(chapter_text)

            for i, chunk_text in enumerate(text_chunks):
                chunk = TextChunk(
                    text=chunk_text,
                    source=self.source_name,
                    chapter=chapter["title"],
                    section=None,
                    page=chapter["start_page"],
                    chunk_index=i,
                    topics=self._extract_topics(chunk_text)
                )
                chunks.append(chunk)

        return chunks


class MKDasProcessor(TextbookProcessor):
    """
    Process MK Das - Electrocardiography of Arrhythmias

    Structure:
    - Chapters organized by arrhythmia type
    - Ch 5: AVNRT, Ch 6: AVRT, Ch 7: AT, Ch 8: AFL, Ch 9: AF
    - Contains ladder diagrams, EP correlations, ablation guidance
    """

    CHAPTER_MAPPING = {
        5: "AVNRT",
        6: "AVRT",
        7: "Atrial_Tachycardia",
        8: "Atrial_Flutter",
        9: "Atrial_Fibrillation",
        10: "VT",
        11: "Brugada",
        12: "Long_QT",
    }

    def __init__(self, pdf_path: Path):
        super().__init__(pdf_path, "MK_Das")

    def extract_chapters(self) -> List[dict]:
        """Extract chapters by detecting chapter headings"""
        chapters = []
        current_chapter = None
        current_content = []

        chapter_pattern = re.compile(r'Chapter\s+(\d+)', re.IGNORECASE)

        for line_data in self.extract_with_formatting():
            text = line_data["text"].strip()

            # Detect chapter heading
            chapter_match = chapter_pattern.search(text)
            if chapter_match and line_data["font_size"] > 14:
                if current_chapter is not None:
                    chapters.append({
                        "number": current_chapter,
                        "title": self.CHAPTER_MAPPING.get(current_chapter, f"Chapter_{current_chapter}"),
                        "content": "\n".join(current_content),
                        "start_page": line_data["page"]
                    })
                current_chapter = int(chapter_match.group(1))
                current_content = []
            else:
                current_content.append(text)

        # Last chapter
        if current_chapter is not None:
            chapters.append({
                "number": current_chapter,
                "title": self.CHAPTER_MAPPING.get(current_chapter, f"Chapter_{current_chapter}"),
                "content": "\n".join(current_content),
                "start_page": 0
            })

        return chapters

    def extract_arrhythmia_content(self) -> List[ArrhythmiaContent]:
        """Extract arrhythmia-specific content"""
        contents = []

        for chapter in self.extract_chapters():
            if chapter["number"] not in self.CHAPTER_MAPPING:
                continue

            arrhythmia_type = self.CHAPTER_MAPPING[chapter["number"]]
            text = chapter["content"]

            content = ArrhythmiaContent(
                arrhythmia_type=arrhythmia_type,
                mechanism=self._extract_mechanism(text),
                ecg_features=self._extract_ecg_features(text),
                differential_diagnosis=self._extract_differential(text),
                ep_correlation=self._extract_ep_correlation(text),
                ablation_targets=self._extract_ablation_info(text),
                clinical_pearls=self._extract_pearls(text),
                source="MK_Das"
            )
            contents.append(content)

        return contents

    def _extract_mechanism(self, text: str) -> str:
        """Extract mechanism description"""
        patterns = [
            r'mechanism[:\s]+([^.]+\.)',
            r'pathophysiology[:\s]+([^.]+\.)',
            r'reentry\s+circuit[:\s]+([^.]+\.)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_ecg_features(self, text: str) -> List[str]:
        """Extract ECG features"""
        features = []

        # Look for feature sections
        feature_section = re.search(
            r'ECG\s+(?:features?|findings?|criteria)[:\s]+(.*?)(?=\n\n|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )

        if feature_section:
            # Split by bullets, numbers, or newlines
            items = re.split(r'[\n•●◦\-]\s*|\d+[.)]\s*', feature_section.group(1))
            features = [item.strip() for item in items if item.strip() and len(item.strip()) > 5]

        return features[:10]  # Limit to 10 features

    def _extract_differential(self, text: str) -> List[str]:
        """Extract differential diagnosis"""
        diff_section = re.search(
            r'differential\s+diagnosis[:\s]+(.*?)(?=\n\n|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )

        if diff_section:
            items = re.split(r'[\n•●◦\-]\s*|\d+[.)]\s*', diff_section.group(1))
            return [item.strip() for item in items if item.strip() and len(item.strip()) > 3]

        return []

    def _extract_ep_correlation(self, text: str) -> str:
        """Extract EP study correlation"""
        patterns = [
            r'EP\s+(?:study|findings?)[:\s]+(.*?)(?=\n\n|\Z)',
            r'electrophysiology[:\s]+(.*?)(?=\n\n|\Z)',
            r'intracardiac[:\s]+(.*?)(?=\n\n|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]

        return ""

    def _extract_ablation_info(self, text: str) -> str:
        """Extract ablation guidance"""
        patterns = [
            r'ablation[:\s]+(.*?)(?=\n\n|\Z)',
            r'target\s+(?:site|location)[:\s]+(.*?)(?=\n\n|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]

        return ""

    def _extract_pearls(self, text: str) -> List[str]:
        """Extract clinical pearls"""
        pearls = []

        pearl_patterns = [
            r'(?:key\s+point|pearl|remember|important)[:\s]+([^.]+\.)',
            r'(?:tip|pitfall)[:\s]+([^.]+\.)',
        ]

        for pattern in pearl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            pearls.extend([m.strip() for m in matches])

        return pearls[:10]

    def extract_structured_content(self) -> List[TextChunk]:
        """Extract all content as structured chunks"""
        chunks = []

        for chapter in self.extract_chapters():
            text_chunks = self.chunk_text(chapter["content"])

            for i, chunk_text in enumerate(text_chunks):
                chunk = TextChunk(
                    text=chunk_text,
                    source=self.source_name,
                    chapter=chapter["title"],
                    section=None,
                    page=chapter.get("start_page", 0),
                    chunk_index=i,
                    topics=[chapter["title"]]
                )
                chunks.append(chunk)

        return chunks


class GenericMedicalPDFProcessor(TextbookProcessor):
    """Generic processor for other medical PDFs (ECG Masters, Marriott, etc.)"""

    def __init__(self, pdf_path: Path, source_name: str = None):
        source = source_name or pdf_path.stem
        super().__init__(pdf_path, source)

    def extract_chapters(self) -> List[dict]:
        """Extract chapters using font-based heuristics"""
        chapters = []
        current_chapter = {"title": "Introduction", "content": [], "start_page": 0}

        for line_data in self.extract_with_formatting():
            # Large, bold text = likely chapter heading
            if line_data["font_size"] > 14 and line_data["is_bold"]:
                text = line_data["text"].strip()
                if len(text) > 3 and len(text) < 100:
                    if current_chapter["content"]:
                        chapters.append(current_chapter)
                    current_chapter = {
                        "title": text,
                        "content": [],
                        "start_page": line_data["page"]
                    }
                    continue

            current_chapter["content"].append(line_data["text"])

        if current_chapter["content"]:
            chapters.append(current_chapter)

        return chapters

    def extract_structured_content(self) -> List[TextChunk]:
        """Extract content as chunks"""
        chunks = []

        for chapter in self.extract_chapters():
            chapter_text = "\n".join(chapter["content"])
            text_chunks = self.chunk_text(chapter_text)

            for i, chunk_text in enumerate(text_chunks):
                chunk = TextChunk(
                    text=chunk_text,
                    source=self.source_name,
                    chapter=chapter["title"],
                    section=None,
                    page=chapter["start_page"],
                    chunk_index=i,
                    topics=[]
                )
                chunks.append(chunk)

        return chunks


def process_all_textbooks(textbook_dir: Path, output_dir: Path) -> dict:
    """Process all textbooks in a directory"""

    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "chunks": [],
        "cases": [],
        "arrhythmia_content": []
    }

    for pdf_file in textbook_dir.glob("*.pdf"):
        print(f"\nProcessing: {pdf_file.name}")

        try:
            # Detect which processor to use
            filename_lower = pdf_file.name.lower()

            if "podrid" in filename_lower:
                with PodridProcessor(pdf_file) as processor:
                    chunks = processor.extract_structured_content()
                    cases = processor.extract_cases()
                    results["chunks"].extend([c.to_dict() for c in chunks])
                    results["cases"].extend([c.to_dict() for c in cases])
                    print(f"  Extracted {len(chunks)} chunks, {len(cases)} cases")

            elif "das" in filename_lower or "arrhythmia" in filename_lower:
                with MKDasProcessor(pdf_file) as processor:
                    chunks = processor.extract_structured_content()
                    arrhythmia = processor.extract_arrhythmia_content()
                    results["chunks"].extend([c.to_dict() for c in chunks])
                    results["arrhythmia_content"].extend([a.to_dict() for a in arrhythmia])
                    print(f"  Extracted {len(chunks)} chunks, {len(arrhythmia)} arrhythmia sections")

            else:
                with GenericMedicalPDFProcessor(pdf_file) as processor:
                    chunks = processor.extract_structured_content()
                    results["chunks"].extend([c.to_dict() for c in chunks])
                    print(f"  Extracted {len(chunks)} chunks")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Save results
    output_file = output_dir / "extracted_content.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_file}")
    print(f"Total: {len(results['chunks'])} chunks, {len(results['cases'])} cases")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python textbook_processor.py <textbook_dir> [output_dir]")
        print("Example: python textbook_processor.py ./data/textbooks ./data/extracted")
        sys.exit(1)

    textbook_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/extracted")

    process_all_textbooks(textbook_dir, output_dir)
