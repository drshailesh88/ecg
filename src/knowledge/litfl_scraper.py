"""
LITFL ECG Library Scraper

Respectfully scrape and structure content from Life in the Fast Lane ECG Library.
https://litfl.com/ecg-library/

License: CC BY-NC-SA 4.0 - Must attribute, non-commercial, share-alike
"""

import httpx
from bs4 import BeautifulSoup
import time
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Generator
from urllib.parse import urljoin, urlparse
import hashlib


@dataclass
class LITFLPage:
    """A diagnostic or educational page from LITFL"""
    url: str
    title: str
    category: str
    content: str
    ecg_features: List[str]
    diagnostic_criteria: List[str]
    clinical_pearls: List[str]
    key_points: List[str]
    related_pages: List[str]
    images: List[str]
    last_scraped: str

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def id(self) -> str:
        return hashlib.md5(self.url.encode()).hexdigest()


@dataclass
class LITFLCase:
    """A teaching case from LITFL (Top 100, ECG Exigency, etc.)"""
    url: str
    series: str
    case_number: int
    title: str
    clinical_scenario: str
    ecg_description: str
    questions: List[str]
    answers: List[str]
    diagnosis: str
    teaching_points: List[str]
    ecg_image_url: str

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def id(self) -> str:
        return hashlib.md5(f"{self.series}_{self.case_number}".encode()).hexdigest()


class LITFLScraper:
    """
    Scrape LITFL ECG Library with respect and caching.

    Be a good citizen:
    - Rate limit requests (2+ seconds between)
    - Cache results to avoid re-scraping
    - Identify ourselves in User-Agent
    - Don't scrape images directly (just URLs)
    """

    BASE_URL = "https://litfl.com"
    ECG_LIBRARY_URL = "https://litfl.com/ecg-library/"

    # Rate limiting
    REQUEST_DELAY = 2.0  # seconds

    # Categories in ECG Library
    CATEGORIES = {
        "basics": ["ecg-basics", "ecg-interpretation"],
        "arrhythmia": ["arrhythmia", "rhythm", "tachycardia", "bradycardia", "fibrillation", "flutter"],
        "ischemia": ["stemi", "nstemi", "infarction", "ischemia", "acs"],
        "conduction": ["block", "bundle", "fascicular", "av-block"],
        "chamber": ["hypertrophy", "enlargement", "lvh", "rvh"],
        "syndrome": ["brugada", "wpw", "long-qt", "wellens"],
        "metabolic": ["hyperkalaemia", "hypokalaemia", "calcium", "digoxin"],
        "pacemaker": ["pacemaker", "paced"],
    }

    # Case series URLs
    CASE_SERIES = {
        "top-100": "https://litfl.com/ecg-library/100-ecg-quiz/",
        "ecg-exigency": "https://litfl.com/ecg-exigency/",
        "cardiovascular-curveball": "https://litfl.com/cardiovascular-curveball/",
    }

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path("./data/litfl_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.client = httpx.Client(
            headers={
                "User-Agent": "ECG-Guru-Bot/1.0 (Educational Medical App; +https://github.com/drshailesh88/ecg)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30.0,
            follow_redirects=True,
        )

        self._last_request_time = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _rate_limit(self):
        """Ensure we don't request too fast"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get_cached(self, url: str) -> Optional[dict]:
        """Get cached content if available"""
        cache_file = self.cache_dir / f"{self._url_to_filename(url)}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except:
                return None
        return None

    def _save_cache(self, url: str, data: dict):
        """Save content to cache"""
        cache_file = self.cache_dir / f"{self._url_to_filename(url)}.json"
        cache_file.write_text(json.dumps(data, indent=2))

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        # Extract path and create safe filename
        parsed = urlparse(url)
        path = parsed.path.strip("/").replace("/", "_")
        return path if path else "index"

    def _categorize_url(self, url: str) -> str:
        """Infer category from URL"""
        url_lower = url.lower()

        for category, keywords in self.CATEGORIES.items():
            if any(kw in url_lower for kw in keywords):
                return category

        return "general"

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        self._rate_limit()

        try:
            response = self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_ecg_library_links(self) -> List[Dict[str, str]]:
        """Get all links from ECG Library main page"""
        soup = self.fetch_page(self.ECG_LIBRARY_URL)
        if not soup:
            return []

        links = []
        seen_urls = set()

        # Find main content area
        content = soup.find("article") or soup.find("div", class_="entry-content")
        if not content:
            content = soup

        # Extract all ECG-related links
        for a in content.find_all("a", href=True):
            href = a["href"]

            # Normalize URL
            if not href.startswith("http"):
                href = urljoin(self.BASE_URL, href)

            # Skip non-LITFL or already seen
            if "litfl.com" not in href or href in seen_urls:
                continue

            # Skip non-ECG pages
            if not any(x in href.lower() for x in ["ecg", "rhythm", "arrhythmia", "infarction",
                                                    "block", "syndrome", "tachycardia"]):
                continue

            seen_urls.add(href)
            links.append({
                "url": href,
                "title": a.get_text(strip=True),
                "category": self._categorize_url(href)
            })

        return links

    def scrape_diagnostic_page(self, url: str) -> Optional[LITFLPage]:
        """Scrape a single diagnostic/educational page"""

        # Check cache first
        cached = self._get_cached(url)
        if cached:
            return LITFLPage(**cached)

        soup = self.fetch_page(url)
        if not soup:
            return None

        # Extract content
        article = soup.find("article") or soup.find("div", class_="entry-content")
        if not article:
            return None

        page = LITFLPage(
            url=url,
            title=self._extract_title(soup),
            category=self._categorize_url(url),
            content=self._extract_content(article),
            ecg_features=self._extract_ecg_features(article),
            diagnostic_criteria=self._extract_criteria(article),
            clinical_pearls=self._extract_pearls(article),
            key_points=self._extract_key_points(article),
            related_pages=self._extract_related(article),
            images=self._extract_images(article),
            last_scraped=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Cache it
        self._save_cache(url, page.to_dict())

        return page

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try entry-title first (WordPress standard)
        title = soup.find("h1", class_="entry-title")
        if title:
            return title.get_text(strip=True)

        # Fall back to first h1
        title = soup.find("h1")
        if title:
            return title.get_text(strip=True)

        # Fall back to title tag
        title = soup.find("title")
        if title:
            return title.get_text(strip=True).split("|")[0].strip()

        return ""

    def _extract_content(self, article: BeautifulSoup) -> str:
        """Extract main text content"""
        # Clone to avoid modifying original
        content = BeautifulSoup(str(article), "html.parser")

        # Remove unwanted elements
        for tag in content.find_all(["script", "style", "nav", "aside", "footer",
                                     "iframe", "noscript"]):
            tag.decompose()

        # Get text with some structure preserved
        text = content.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def _extract_ecg_features(self, article: BeautifulSoup) -> List[str]:
        """Extract ECG features/findings"""
        features = []

        # Look for lists after ECG-related headings
        for heading in article.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if any(kw in heading_text for kw in ["ecg", "features", "findings", "criteria"]):
                # Get following list
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3", "h4"]:
                    if next_elem.name in ["ul", "ol"]:
                        for li in next_elem.find_all("li"):
                            text = li.get_text(strip=True)
                            if text and len(text) > 5:
                                features.append(text)
                    next_elem = next_elem.find_next_sibling()

        return features[:15]  # Limit

    def _extract_criteria(self, article: BeautifulSoup) -> List[str]:
        """Extract diagnostic criteria"""
        criteria = []

        for heading in article.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if any(kw in heading_text for kw in ["criteria", "diagnosis", "definition"]):
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3", "h4"]:
                    if next_elem.name in ["ul", "ol"]:
                        for li in next_elem.find_all("li"):
                            text = li.get_text(strip=True)
                            if text:
                                criteria.append(text)
                    elif next_elem.name == "p":
                        text = next_elem.get_text(strip=True)
                        if text:
                            criteria.append(text)
                    next_elem = next_elem.find_next_sibling()

        return criteria[:10]

    def _extract_pearls(self, article: BeautifulSoup) -> List[str]:
        """Extract clinical pearls"""
        pearls = []

        for heading in article.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if any(kw in heading_text for kw in ["pearl", "pitfall", "tip", "remember"]):
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3", "h4"]:
                    if next_elem.name in ["ul", "ol"]:
                        for li in next_elem.find_all("li"):
                            pearls.append(li.get_text(strip=True))
                    elif next_elem.name == "p":
                        pearls.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()

        return [p for p in pearls if p and len(p) > 10][:10]

    def _extract_key_points(self, article: BeautifulSoup) -> List[str]:
        """Extract key points"""
        points = []

        for heading in article.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if any(kw in heading_text for kw in ["key point", "summary", "important"]):
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3", "h4"]:
                    if next_elem.name in ["ul", "ol"]:
                        for li in next_elem.find_all("li"):
                            points.append(li.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()

        return [p for p in points if p][:10]

    def _extract_related(self, article: BeautifulSoup) -> List[str]:
        """Extract related page links"""
        related = []

        for a in article.find_all("a", href=True):
            href = a["href"]
            if "litfl.com" in href and "ecg" in href.lower():
                if href not in related:
                    related.append(href)

        return related[:10]

    def _extract_images(self, article: BeautifulSoup) -> List[str]:
        """Extract image URLs (for reference, not download)"""
        images = []

        for img in article.find_all("img"):
            src = img.get("src", "")
            if src and ("ecg" in src.lower() or "rhythm" in src.lower()):
                if not src.startswith("http"):
                    src = urljoin(self.BASE_URL, src)
                images.append(src)

        return images

    def scrape_case_series(self, series_name: str) -> List[LITFLCase]:
        """Scrape a case series (Top 100, ECG Exigency, etc.)"""

        if series_name not in self.CASE_SERIES:
            print(f"Unknown series: {series_name}")
            return []

        series_url = self.CASE_SERIES[series_name]
        cases = []

        # Get series main page
        soup = self.fetch_page(series_url)
        if not soup:
            return []

        # Find all case links
        case_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Case pages typically have numbers or "case" in URL
            if re.search(r"(case|quiz|ecg-\d|answer)", href.lower()):
                if href not in [l["url"] for l in case_links]:
                    case_links.append({
                        "url": href if href.startswith("http") else urljoin(self.BASE_URL, href),
                        "title": a.get_text(strip=True)
                    })

        # Scrape each case
        for i, link in enumerate(case_links[:50]):  # Limit to 50 cases
            print(f"  Scraping case {i+1}/{len(case_links)}: {link['title'][:50]}...")

            case_soup = self.fetch_page(link["url"])
            if not case_soup:
                continue

            article = case_soup.find("article") or case_soup.find("div", class_="entry-content")
            if not article:
                continue

            case = LITFLCase(
                url=link["url"],
                series=series_name,
                case_number=i + 1,
                title=self._extract_title(case_soup),
                clinical_scenario=self._extract_scenario(article),
                ecg_description=self._extract_ecg_description(article),
                questions=self._extract_questions(article),
                answers=self._extract_answers(article),
                diagnosis=self._extract_case_diagnosis(article),
                teaching_points=self._extract_key_points(article),
                ecg_image_url=self._extract_images(article)[0] if self._extract_images(article) else ""
            )
            cases.append(case)

        return cases

    def _extract_scenario(self, article: BeautifulSoup) -> str:
        """Extract clinical scenario from case"""
        # Often in first paragraph or after "Clinical" heading
        for heading in article.find_all(["h2", "h3"]):
            if any(kw in heading.get_text().lower() for kw in ["clinical", "history", "scenario", "presentation"]):
                next_elem = heading.find_next_sibling()
                if next_elem and next_elem.name == "p":
                    return next_elem.get_text(strip=True)

        # Fall back to first paragraph
        first_p = article.find("p")
        if first_p:
            return first_p.get_text(strip=True)

        return ""

    def _extract_ecg_description(self, article: BeautifulSoup) -> str:
        """Extract ECG description"""
        for heading in article.find_all(["h2", "h3"]):
            if any(kw in heading.get_text().lower() for kw in ["ecg", "describe", "interpretation"]):
                content = []
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3"]:
                    if next_elem.name in ["p", "li"]:
                        content.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()
                return "\n".join(content)

        return ""

    def _extract_questions(self, article: BeautifulSoup) -> List[str]:
        """Extract quiz questions"""
        questions = []

        for heading in article.find_all(["h2", "h3"]):
            if "question" in heading.get_text().lower():
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3"]:
                    if next_elem.name in ["p", "li"]:
                        text = next_elem.get_text(strip=True)
                        if "?" in text:
                            questions.append(text)
                    next_elem = next_elem.find_next_sibling()

        return questions

    def _extract_answers(self, article: BeautifulSoup) -> List[str]:
        """Extract quiz answers"""
        answers = []

        for heading in article.find_all(["h2", "h3"]):
            if "answer" in heading.get_text().lower():
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ["h2", "h3"]:
                    if next_elem.name in ["p", "li"]:
                        answers.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()

        return answers

    def _extract_case_diagnosis(self, article: BeautifulSoup) -> str:
        """Extract diagnosis from case"""
        for heading in article.find_all(["h2", "h3"]):
            heading_text = heading.get_text().lower()
            if any(kw in heading_text for kw in ["diagnosis", "answer", "reveal"]):
                next_elem = heading.find_next_sibling()
                if next_elem:
                    return next_elem.get_text(strip=True)[:200]

        return ""

    def harvest_all(self, include_cases: bool = True) -> Dict:
        """Harvest all LITFL ECG content"""

        results = {
            "diagnostic_pages": [],
            "case_series": {},
            "metadata": {
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "LITFL ECG Library",
                "license": "CC BY-NC-SA 4.0",
                "attribution": "Life in the Fast Lane (https://litfl.com)",
            }
        }

        # Get all ECG library links
        print("Getting ECG Library links...")
        links = self.get_ecg_library_links()
        print(f"Found {len(links)} pages to scrape")

        # Scrape each page
        for i, link in enumerate(links):
            print(f"Scraping {i+1}/{len(links)}: {link['title'][:50]}...")
            page = self.scrape_diagnostic_page(link["url"])
            if page:
                results["diagnostic_pages"].append(page.to_dict())

        # Scrape case series
        if include_cases:
            for series_name in self.CASE_SERIES:
                print(f"\nScraping {series_name}...")
                cases = self.scrape_case_series(series_name)
                results["case_series"][series_name] = [c.to_dict() for c in cases]
                print(f"  Got {len(cases)} cases")

        # Save complete harvest
        output_file = self.cache_dir / "litfl_complete.json"
        output_file.write_text(json.dumps(results, indent=2))

        print(f"\nHarvest complete!")
        print(f"  - {len(results['diagnostic_pages'])} diagnostic pages")
        for series, cases in results["case_series"].items():
            print(f"  - {len(cases)} cases from {series}")
        print(f"Saved to {output_file}")

        return results


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape LITFL ECG Library")
    parser.add_argument("--cache-dir", type=Path, default="./data/litfl_cache",
                       help="Directory for caching scraped content")
    parser.add_argument("--no-cases", action="store_true",
                       help="Skip case series (faster)")
    parser.add_argument("--page", type=str, help="Scrape a single page URL")

    args = parser.parse_args()

    with LITFLScraper(cache_dir=args.cache_dir) as scraper:
        if args.page:
            page = scraper.scrape_diagnostic_page(args.page)
            if page:
                print(json.dumps(page.to_dict(), indent=2))
        else:
            scraper.harvest_all(include_cases=not args.no_cases)


if __name__ == "__main__":
    main()
