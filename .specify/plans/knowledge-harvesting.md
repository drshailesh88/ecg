# Knowledge Harvesting & Embedding Technical Plan

## Overview

This document details the technical approach for:
1. Extracting content from textbooks (PDFs/EPUBs)
2. Scraping and structuring LITFL content
3. Embedding everything into ChromaDB for RAG

---

## Part 1: Textbook Processing Pipeline

### Tools & Libraries

```python
# requirements.txt additions
PyMuPDF==1.23.0          # PDF extraction (better than PyPDF2)
ebooklib==0.18            # EPUB extraction
pytesseract==0.3.10       # OCR for scanned PDFs
pdf2image==1.16.3         # Convert PDF pages to images for OCR
unstructured==0.10.0      # Document parsing
langchain==0.1.0          # Text chunking utilities
chromadb==0.4.0           # Vector storage
sentence-transformers==2.2.2  # Embeddings
```

### PDF Processing Pipeline

```python
import fitz  # PyMuPDF
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class TextbookChapter:
    source: str
    volume: str
    chapter_number: int
    title: str
    content: str
    figures: List[str]
    tables: List[str]
    page_range: tuple

@dataclass
class TextChunk:
    text: str
    source: str
    chapter: str
    page: int
    chunk_index: int
    metadata: dict

class PDFTextbookProcessor:
    """Extract and structure textbook content from PDF"""

    def __init__(self, pdf_path: Path, source_name: str):
        self.pdf_path = pdf_path
        self.source_name = source_name
        self.doc = fitz.open(pdf_path)

    def extract_text_with_structure(self) -> List[TextbookChapter]:
        """Extract text preserving chapter structure"""

        chapters = []
        current_chapter = None
        current_content = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    text = "".join(span["text"] for span in line["spans"])
                    font_size = line["spans"][0]["size"] if line["spans"] else 12

                    # Detect chapter headings (typically larger font)
                    if self._is_chapter_heading(text, font_size):
                        if current_chapter:
                            current_chapter.content = "\n".join(current_content)
                            chapters.append(current_chapter)

                        current_chapter = TextbookChapter(
                            source=self.source_name,
                            volume=self._extract_volume(text),
                            chapter_number=self._extract_chapter_num(text),
                            title=self._clean_title(text),
                            content="",
                            figures=[],
                            tables=[],
                            page_range=(page_num, page_num)
                        )
                        current_content = []
                    else:
                        current_content.append(text)

        # Don't forget last chapter
        if current_chapter:
            current_chapter.content = "\n".join(current_content)
            chapters.append(current_chapter)

        return chapters

    def _is_chapter_heading(self, text: str, font_size: float) -> bool:
        """Detect if text is a chapter heading"""
        # Adjust these patterns for specific textbooks
        chapter_patterns = [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+\d+',
            r'^\d+\.\s+[A-Z]',  # "1. ARRHYTHMIAS"
            r'^Case\s+\d+',     # For Podrid cases
        ]
        return (
            font_size > 14 and  # Larger than body text
            any(re.match(p, text.strip()) for p in chapter_patterns)
        )

    def extract_figures_and_ecgs(self) -> List[dict]:
        """Extract ECG images from PDF"""

        ecg_images = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            images = page.get_images()

            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(self.doc, xref)

                # Save image
                img_path = f"extracted/{self.source_name}_p{page_num}_img{img_index}.png"
                pix.save(img_path)

                # Try to find associated caption
                caption = self._find_image_caption(page, img)

                ecg_images.append({
                    "path": img_path,
                    "page": page_num,
                    "caption": caption,
                    "source": self.source_name
                })

        return ecg_images


class PodridProcessor(PDFTextbookProcessor):
    """Specialized processor for Podrid's Real-World ECGs"""

    def extract_cases(self) -> List[dict]:
        """Extract individual case studies"""

        cases = []
        case_pattern = r'Case\s+(\d+[-.]?\d*)'

        for chapter in self.extract_text_with_structure():
            # Each Podrid case follows a structure:
            # Case number -> Clinical context -> ECG -> Analysis -> Teaching points

            case_texts = re.split(case_pattern, chapter.content)

            for i in range(1, len(case_texts), 2):
                case_num = case_texts[i]
                case_content = case_texts[i + 1] if i + 1 < len(case_texts) else ""

                cases.append({
                    "case_id": f"podrid_{chapter.volume}_{case_num}",
                    "volume": chapter.volume,
                    "case_number": case_num,
                    "clinical_context": self._extract_clinical_context(case_content),
                    "ecg_description": self._extract_ecg_description(case_content),
                    "analysis": self._extract_analysis(case_content),
                    "teaching_points": self._extract_teaching_points(case_content),
                    "diagnosis": self._extract_diagnosis(case_content)
                })

        return cases

    def _extract_clinical_context(self, text: str) -> str:
        """Extract the clinical presentation section"""
        # Pattern varies by volume, adjust as needed
        match = re.search(
            r'(Clinical.*?|History.*?|Presentation.*?)(ECG|Electrocardiogram)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        return match.group(1).strip() if match else ""


class MKDasProcessor(PDFTextbookProcessor):
    """Specialized processor for MK Das Electrocardiography of Arrhythmias"""

    def extract_arrhythmia_content(self) -> List[dict]:
        """Extract arrhythmia-specific content with ladder diagrams"""

        arrhythmia_content = []

        # MK Das chapters are organized by arrhythmia type
        chapter_mapping = {
            5: "AVNRT",
            6: "AVRT",
            7: "Atrial Tachycardia",
            8: "Atrial Flutter",
            9: "Atrial Fibrillation",
            # Add more as needed
        }

        for chapter in self.extract_text_with_structure():
            if chapter.chapter_number in chapter_mapping:
                arrhythmia_content.append({
                    "arrhythmia_type": chapter_mapping[chapter.chapter_number],
                    "mechanism_description": self._extract_mechanism(chapter.content),
                    "ecg_features": self._extract_ecg_features(chapter.content),
                    "ep_correlation": self._extract_ep_data(chapter.content),
                    "ladder_diagrams": self._extract_ladder_concepts(chapter.content),
                    "ablation_guidance": self._extract_ablation_info(chapter.content),
                    "full_text": chapter.content
                })

        return arrhythmia_content
```

### EPUB Processing (for digital textbooks)

```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

class EPUBProcessor:
    """Process EPUB format textbooks"""

    def __init__(self, epub_path: Path):
        self.book = epub.read_epub(str(epub_path))

    def extract_chapters(self) -> List[TextbookChapter]:
        """Extract chapters from EPUB"""

        chapters = []

        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')

                # Extract text preserving some structure
                text = soup.get_text(separator='\n')

                # Extract images
                images = [img['src'] for img in soup.find_all('img')]

                chapters.append(TextbookChapter(
                    source=self.book.get_metadata('DC', 'title')[0][0],
                    volume="",
                    chapter_number=len(chapters) + 1,
                    title=self._extract_title(soup),
                    content=text,
                    figures=images,
                    tables=self._extract_tables(soup),
                    page_range=(0, 0)
                ))

        return chapters

    def _extract_tables(self, soup: BeautifulSoup) -> List[str]:
        """Extract tables as structured text"""
        tables = []
        for table in soup.find_all('table'):
            tables.append(table.get_text(separator=' | '))
        return tables
```

---

## Part 2: LITFL Harvesting

### LITFL Scraper Implementation

```python
import httpx
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass
from typing import List, Optional
import json
from pathlib import Path

@dataclass
class LITFLPage:
    url: str
    title: str
    category: str
    content: str
    ecg_features: List[str]
    clinical_pearls: List[str]
    diagnostic_criteria: List[str]
    related_pages: List[str]
    images: List[str]
    last_updated: str

@dataclass
class LITFLCase:
    url: str
    series: str  # "top-100", "ecg-exigency", etc.
    case_number: int
    clinical_scenario: str
    ecg_description: str
    diagnosis: str
    teaching_points: List[str]
    ecg_image_url: str

class LITFLScraper:
    """Respectfully scrape LITFL ECG Library"""

    BASE_URL = "https://litfl.com"
    ECG_LIBRARY_URL = "https://litfl.com/ecg-library/"

    # Rate limiting - be respectful
    REQUEST_DELAY = 2  # seconds between requests

    def __init__(self, cache_dir: Path = Path("./litfl_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.client = httpx.Client(
            headers={
                "User-Agent": "ECG-Guru-Knowledge-Bot/1.0 (Educational Medical App; Contact: ecgguru@example.com)"
            },
            timeout=30
        )

    def get_all_ecg_library_links(self) -> List[dict]:
        """Get all links from ECG Library main page"""

        response = self.client.get(self.ECG_LIBRARY_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        links = []

        # Find the main content area
        content = soup.find('div', class_='entry-content')
        if not content:
            content = soup.find('article')

        # Extract all internal links
        for a in content.find_all('a', href=True):
            href = a['href']
            if 'litfl.com' in href and '/ecg-' in href.lower():
                links.append({
                    "url": href,
                    "title": a.get_text(strip=True),
                    "category": self._infer_category(href)
                })

        return links

    def scrape_diagnostic_page(self, url: str) -> LITFLPage:
        """Scrape a single diagnostic/educational page"""

        # Check cache first
        cache_file = self.cache_dir / f"{self._url_to_filename(url)}.json"
        if cache_file.exists():
            return LITFLPage(**json.loads(cache_file.read_text()))

        # Rate limit
        time.sleep(self.REQUEST_DELAY)

        response = self.client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract main content
        article = soup.find('article') or soup.find('div', class_='entry-content')

        page = LITFLPage(
            url=url,
            title=self._extract_title(soup),
            category=self._infer_category(url),
            content=self._extract_main_content(article),
            ecg_features=self._extract_ecg_features(article),
            clinical_pearls=self._extract_clinical_pearls(article),
            diagnostic_criteria=self._extract_criteria(article),
            related_pages=self._extract_related_links(article),
            images=self._extract_images(article),
            last_updated=self._extract_date(soup)
        )

        # Cache the result
        cache_file.write_text(json.dumps(page.__dict__, indent=2))

        return page

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('h1', class_='entry-title') or soup.find('h1')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _extract_main_content(self, article: BeautifulSoup) -> str:
        """Extract the main text content"""
        if not article:
            return ""

        # Remove navigation, ads, etc.
        for unwanted in article.find_all(['nav', 'aside', 'footer', 'script']):
            unwanted.decompose()

        return article.get_text(separator='\n', strip=True)

    def _extract_ecg_features(self, article: BeautifulSoup) -> List[str]:
        """Extract ECG features/criteria"""
        features = []

        # LITFL often uses bullet points for criteria
        for ul in article.find_all('ul'):
            # Check if this list is about ECG features
            prev_element = ul.find_previous(['h2', 'h3', 'h4', 'p'])
            if prev_element and any(kw in prev_element.get_text().lower()
                                   for kw in ['ecg', 'features', 'criteria', 'findings']):
                for li in ul.find_all('li'):
                    features.append(li.get_text(strip=True))

        return features

    def _extract_clinical_pearls(self, article: BeautifulSoup) -> List[str]:
        """Extract clinical pearls and key points"""
        pearls = []

        # Look for "Key Points", "Clinical Pearls", "Remember" sections
        for heading in article.find_all(['h2', 'h3', 'h4']):
            if any(kw in heading.get_text().lower()
                   for kw in ['key point', 'pearl', 'remember', 'pitfall', 'tip']):
                # Get the following content
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                    if next_elem.name in ['p', 'li']:
                        pearls.append(next_elem.get_text(strip=True))
                    elif next_elem.name == 'ul':
                        for li in next_elem.find_all('li'):
                            pearls.append(li.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()

        return pearls

    def _extract_criteria(self, article: BeautifulSoup) -> List[str]:
        """Extract diagnostic criteria"""
        criteria = []

        # Look for numbered criteria or specific patterns
        for heading in article.find_all(['h2', 'h3', 'h4']):
            if any(kw in heading.get_text().lower()
                   for kw in ['criteria', 'diagnosis', 'definition']):
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                    text = next_elem.get_text(strip=True)
                    if text:
                        criteria.append(text)
                    next_elem = next_elem.find_next_sibling()

        return criteria

    def _extract_images(self, article: BeautifulSoup) -> List[str]:
        """Extract ECG image URLs"""
        images = []
        for img in article.find_all('img'):
            src = img.get('src', '')
            if 'ecg' in src.lower() or 'rhythm' in src.lower():
                images.append(src)
        return images

    def _infer_category(self, url: str) -> str:
        """Infer category from URL"""
        url_lower = url.lower()
        if 'arrhythmia' in url_lower or 'rhythm' in url_lower:
            return "arrhythmia"
        elif 'stemi' in url_lower or 'infarct' in url_lower:
            return "ischemia"
        elif 'block' in url_lower:
            return "conduction"
        elif 'hypertrophy' in url_lower or 'enlargement' in url_lower:
            return "chamber"
        else:
            return "general"

    def scrape_case_series(self, series_name: str) -> List[LITFLCase]:
        """Scrape a case series (Top 100, ECG Exigency, etc.)"""

        series_urls = {
            "top-100": "https://litfl.com/top-100-ecg/",
            "ecg-exigency": "https://litfl.com/ecg-exigency/",
            "cardiovascular-curveball": "https://litfl.com/cardiovascular-curveball/"
        }

        if series_name not in series_urls:
            raise ValueError(f"Unknown series: {series_name}")

        cases = []
        main_page = self.client.get(series_urls[series_name])
        soup = BeautifulSoup(main_page.text, 'html.parser')

        # Get all case links
        case_links = []
        for a in soup.find_all('a', href=True):
            if series_name in a['href'] and a['href'] != series_urls[series_name]:
                case_links.append(a['href'])

        for i, link in enumerate(case_links):
            time.sleep(self.REQUEST_DELAY)

            case_page = self.client.get(link)
            case_soup = BeautifulSoup(case_page.text, 'html.parser')

            cases.append(LITFLCase(
                url=link,
                series=series_name,
                case_number=i + 1,
                clinical_scenario=self._extract_scenario(case_soup),
                ecg_description=self._extract_ecg_description(case_soup),
                diagnosis=self._extract_diagnosis(case_soup),
                teaching_points=self._extract_teaching_points(case_soup),
                ecg_image_url=self._extract_ecg_image(case_soup)
            ))

        return cases

    def harvest_all(self) -> dict:
        """Complete harvest of LITFL ECG content"""

        results = {
            "diagnostic_pages": [],
            "case_series": {}
        }

        # Get all diagnostic pages
        print("Harvesting diagnostic pages...")
        links = self.get_all_ecg_library_links()
        for link in links:
            try:
                page = self.scrape_diagnostic_page(link['url'])
                results["diagnostic_pages"].append(page.__dict__)
                print(f"  Scraped: {page.title}")
            except Exception as e:
                print(f"  Error scraping {link['url']}: {e}")

        # Get case series
        for series in ["top-100", "ecg-exigency", "cardiovascular-curveball"]:
            print(f"Harvesting {series}...")
            try:
                cases = self.scrape_case_series(series)
                results["case_series"][series] = [c.__dict__ for c in cases]
            except Exception as e:
                print(f"  Error with {series}: {e}")

        # Save complete harvest
        output_file = self.cache_dir / "litfl_complete_harvest.json"
        output_file.write_text(json.dumps(results, indent=2))

        return results

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        return url.replace("https://", "").replace("/", "_").replace(".", "_")
```

---

## Part 3: Embedding Pipeline

### ChromaDB Embedding

```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import hashlib

class ECGKnowledgeEmbedder:
    """Embed harvested content into ChromaDB"""

    def __init__(self, persist_dir: str = "./chroma_db"):
        # Use a medical-optimized embedding model if available
        # Fallback to general-purpose model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # For better medical embeddings, consider:
        # self.embedder = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')

        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir
        ))

        # Create collections
        self.collections = {
            "textbook_content": self.client.get_or_create_collection(
                name="textbook_content",
                metadata={"description": "Textbook chapters and sections"}
            ),
            "teaching_cases": self.client.get_or_create_collection(
                name="teaching_cases",
                metadata={"description": "Teaching cases from all sources"}
            ),
            "diagnostic_criteria": self.client.get_or_create_collection(
                name="diagnostic_criteria",
                metadata={"description": "Diagnostic criteria and ECG features"}
            ),
            "clinical_pearls": self.client.get_or_create_collection(
                name="clinical_pearls",
                metadata={"description": "Clinical pearls and key points"}
            ),
            "algorithms": self.client.get_or_create_collection(
                name="algorithms",
                metadata={"description": "ECG interpretation algorithms"}
            )
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
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def embed_textbook_chapter(self, chapter: dict, source: str):
        """Embed a textbook chapter"""

        chunks = self.chunk_text(chapter['content'])

        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{source}_{chapter['title']}_{i}".encode()).hexdigest()

            self.collections["textbook_content"].add(
                documents=[chunk],
                metadatas=[{
                    "source": source,
                    "chapter": chapter['title'],
                    "volume": chapter.get('volume', ''),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }],
                ids=[doc_id]
            )

    def embed_litfl_page(self, page: dict):
        """Embed a LITFL diagnostic page"""

        # Main content
        chunks = self.chunk_text(page['content'])
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"litfl_{page['title']}_{i}".encode()).hexdigest()

            self.collections["textbook_content"].add(
                documents=[chunk],
                metadatas=[{
                    "source": "LITFL",
                    "title": page['title'],
                    "category": page['category'],
                    "url": page['url'],
                    "chunk_index": i
                }],
                ids=[doc_id]
            )

        # ECG features as separate entries
        for feature in page.get('ecg_features', []):
            doc_id = hashlib.md5(f"litfl_feature_{page['title']}_{feature[:50]}".encode()).hexdigest()

            self.collections["diagnostic_criteria"].add(
                documents=[feature],
                metadatas=[{
                    "source": "LITFL",
                    "condition": page['title'],
                    "type": "ecg_feature"
                }],
                ids=[doc_id]
            )

        # Clinical pearls
        for pearl in page.get('clinical_pearls', []):
            doc_id = hashlib.md5(f"litfl_pearl_{page['title']}_{pearl[:50]}".encode()).hexdigest()

            self.collections["clinical_pearls"].add(
                documents=[pearl],
                metadatas=[{
                    "source": "LITFL",
                    "condition": page['title'],
                    "type": "clinical_pearl"
                }],
                ids=[doc_id]
            )

    def embed_teaching_case(self, case: dict, source: str):
        """Embed a teaching case"""

        # Combine relevant case elements for embedding
        case_text = f"""
        Clinical Scenario: {case.get('clinical_context', case.get('clinical_scenario', ''))}

        ECG Description: {case.get('ecg_description', '')}

        Diagnosis: {case.get('diagnosis', '')}

        Teaching Points: {' '.join(case.get('teaching_points', []))}

        Analysis: {case.get('analysis', '')}
        """

        doc_id = hashlib.md5(f"{source}_{case.get('case_id', case.get('case_number', ''))}".encode()).hexdigest()

        self.collections["teaching_cases"].add(
            documents=[case_text],
            metadatas=[{
                "source": source,
                "case_id": case.get('case_id', str(case.get('case_number', ''))),
                "diagnosis": case.get('diagnosis', ''),
                "difficulty": case.get('difficulty', 'intermediate'),
                "series": case.get('series', '')
            }],
            ids=[doc_id]
        )

    def embed_algorithm(self, algorithm: dict):
        """Embed an algorithm explanation"""

        # Full algorithm explanation
        doc_id = hashlib.md5(f"algo_{algorithm['name']}".encode()).hexdigest()

        self.collections["algorithms"].add(
            documents=[algorithm['full_explanation']],
            metadatas=[{
                "name": algorithm['name'],
                "purpose": algorithm['purpose'],
                "accuracy": algorithm.get('accuracy', ''),
                "year": algorithm.get('year', ''),
                "citation": algorithm.get('citation', '')
            }],
            ids=[doc_id]
        )

        # Individual steps
        for step in algorithm.get('steps', []):
            step_id = hashlib.md5(f"algo_{algorithm['name']}_step_{step['number']}".encode()).hexdigest()

            self.collections["algorithms"].add(
                documents=[step['explanation']],
                metadatas=[{
                    "algorithm": algorithm['name'],
                    "step_number": step['number'],
                    "criterion": step.get('criterion', '')
                }],
                ids=[step_id]
            )

    def query_for_diagnosis(
        self,
        diagnosis: str,
        n_results: int = 5
    ) -> Dict[str, List]:
        """Query all collections for a diagnosis"""

        results = {}

        for name, collection in self.collections.items():
            results[name] = collection.query(
                query_texts=[diagnosis],
                n_results=n_results
            )

        return results

    def query_for_teaching(
        self,
        topic: str,
        difficulty: str = None,
        n_results: int = 3
    ) -> Dict:
        """Query for teaching content"""

        where_filter = {}
        if difficulty:
            where_filter["difficulty"] = difficulty

        # Get cases
        cases = self.collections["teaching_cases"].query(
            query_texts=[topic],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        # Get pearls
        pearls = self.collections["clinical_pearls"].query(
            query_texts=[topic],
            n_results=n_results
        )

        return {
            "cases": cases,
            "pearls": pearls
        }
```

---

## Part 4: Complete Pipeline

### Master Pipeline Script

```python
#!/usr/bin/env python3
"""
ECG Guru Knowledge Harvesting Pipeline

Usage:
    python harvest_knowledge.py --litfl           # Harvest LITFL only
    python harvest_knowledge.py --textbooks       # Process textbooks only
    python harvest_knowledge.py --all             # Everything
    python harvest_knowledge.py --embed           # Embed harvested content
"""

import argparse
from pathlib import Path

def harvest_litfl():
    """Harvest all LITFL content"""
    print("=" * 50)
    print("Harvesting LITFL ECG Library")
    print("=" * 50)

    scraper = LITFLScraper(cache_dir=Path("./data/litfl_cache"))
    results = scraper.harvest_all()

    print(f"\nHarvested:")
    print(f"  - {len(results['diagnostic_pages'])} diagnostic pages")
    for series, cases in results['case_series'].items():
        print(f"  - {len(cases)} cases from {series}")

    return results

def process_textbooks(textbook_dir: Path):
    """Process all textbooks in directory"""
    print("=" * 50)
    print("Processing Textbooks")
    print("=" * 50)

    results = {
        "chapters": [],
        "cases": []
    }

    for pdf_file in textbook_dir.glob("*.pdf"):
        print(f"\nProcessing: {pdf_file.name}")

        if "podrid" in pdf_file.name.lower():
            processor = PodridProcessor(pdf_file, "Podrid")
            chapters = processor.extract_text_with_structure()
            cases = processor.extract_cases()
            results["chapters"].extend(chapters)
            results["cases"].extend(cases)
            print(f"  Extracted {len(chapters)} chapters, {len(cases)} cases")

        elif "das" in pdf_file.name.lower() or "arrhythmia" in pdf_file.name.lower():
            processor = MKDasProcessor(pdf_file, "MK_Das")
            chapters = processor.extract_text_with_structure()
            arrhythmia_content = processor.extract_arrhythmia_content()
            results["chapters"].extend(chapters)
            print(f"  Extracted {len(chapters)} chapters")

        else:
            processor = PDFTextbookProcessor(pdf_file, pdf_file.stem)
            chapters = processor.extract_text_with_structure()
            results["chapters"].extend(chapters)
            print(f"  Extracted {len(chapters)} chapters")

    return results

def embed_all_content():
    """Embed all harvested content into ChromaDB"""
    print("=" * 50)
    print("Embedding Content into ChromaDB")
    print("=" * 50)

    embedder = ECGKnowledgeEmbedder(persist_dir="./data/chroma_db")

    # Load LITFL harvest
    litfl_file = Path("./data/litfl_cache/litfl_complete_harvest.json")
    if litfl_file.exists():
        import json
        litfl_data = json.loads(litfl_file.read_text())

        print(f"\nEmbedding {len(litfl_data['diagnostic_pages'])} LITFL pages...")
        for page in litfl_data['diagnostic_pages']:
            embedder.embed_litfl_page(page)

        for series, cases in litfl_data['case_series'].items():
            print(f"Embedding {len(cases)} cases from {series}...")
            for case in cases:
                embedder.embed_teaching_case(case, f"LITFL_{series}")

    # Load textbook content
    # (similar pattern for processed textbooks)

    print("\nEmbedding complete!")

def main():
    parser = argparse.ArgumentParser(description="ECG Guru Knowledge Harvesting")
    parser.add_argument("--litfl", action="store_true", help="Harvest LITFL")
    parser.add_argument("--textbooks", type=Path, help="Process textbooks in directory")
    parser.add_argument("--embed", action="store_true", help="Embed content")
    parser.add_argument("--all", action="store_true", help="Do everything")

    args = parser.parse_args()

    if args.all or args.litfl:
        harvest_litfl()

    if args.all or args.textbooks:
        if args.textbooks:
            process_textbooks(args.textbooks)
        else:
            process_textbooks(Path("./data/textbooks"))

    if args.all or args.embed:
        embed_all_content()

if __name__ == "__main__":
    main()
```

---

## Respectful Scraping Guidelines

### LITFL Scraping Ethics

1. **Rate Limiting**: 2+ seconds between requests
2. **User-Agent**: Identify ourselves clearly
3. **Caching**: Don't re-scrape unchanged content
4. **Attribution**: Always cite LITFL in our app (CC BY-NC-SA license)
5. **No Deep Linking**: Link to source, don't embed their images directly
6. **Contact**: Reach out to LITFL team about our use case

### Example Attribution

```
ECG content and clinical pearls adapted from Life in the Fast Lane
(LITFL, https://litfl.com/ecg-library/) under CC BY-NC-SA 4.0 license.
```

---

## Next Steps

1. **Test LITFL scraper** on a few pages
2. **Process one Podrid volume** to validate PDF extraction
3. **Set up ChromaDB** and embed test content
4. **Build RAG query pipeline** for reasoning layer
5. **Validate output quality** with sample queries
