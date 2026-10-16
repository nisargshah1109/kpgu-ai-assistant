import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
import time
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional
import logging
import xml.etree.ElementTree as ET
from robotexclusionrulesparser import RobotExclusionRulesParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from app.config import settings

logger = logging.getLogger(__name__)

# Known template/obsolete routes that render 404 in SPA
EXCLUDED_ROUTE_PATTERNS = [
    "/study",
    "/teachers",
    "/admissions/admission-procedure",
    "/admissions/admission-calendar"
]

class CrawlerService:
    def __init__(self, base_url: str = "https://www.kpgu.ac.in/"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.documents: List[Dict] = []
        self.driver: Optional[webdriver.Chrome] = None

        self.rerp = RobotExclusionRulesParser()
        self._robots_parsed = False

    def _ensure_driver(self) -> webdriver.Chrome:
        """Initialize or reuse Selenium Chrome driver"""
        if self.driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--user-agent=KPGU-AI-Assistant-Crawler/2.0 (University Information Ingestion)")
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(25)
        return self.driver

    def close_driver(self):
        """Safely close driver instance"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing Chrome driver: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        self._ensure_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()

    def _ensure_robots_parsed(self):
        if not self._robots_parsed:
            try:
                robots_url = urljoin(self.base_url, "/robots.txt")
                robots_response = requests.get(robots_url, timeout=5)
                if robots_response.status_code == 200:
                    self.rerp.parse(robots_response.text)
            except Exception as e:
                logger.warning(f"Error parsing robots.txt: {e}")
            finally:
                self._robots_parsed = True

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            self._ensure_robots_parsed()
            return self.rerp.is_allowed("*", url)
        except Exception:
            return True

    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc == ""
        except Exception:
            return False

    def normalize_url(self, url: str) -> str:
        """Normalize URL"""
        try:
            parsed = urlparse(url)
            normalized = parsed._replace(fragment="").geturl()
            if normalized.startswith("http://"):
                normalized = normalized.replace("http://", "https://", 1)
            return normalized.rstrip("/")
        except Exception:
            return url

    def categorize_url(self, url: str, title: str = "") -> str:
        """Determine knowledge domain category for URL"""
        norm = url.lower()
        if "/about-us" in norm or "leadership" in norm:
            return "leadership_and_governance"
        elif "/placement" in norm or "placement" in norm or "recruit" in norm:
            return "placements_and_careers"
        elif "/admission" in norm or "scholarship" in norm or "fees" in norm:
            return "admissions_and_scholarships"
        elif "/academics" in norm or "faculty" in norm or "engineering" in norm or "science" in norm:
            return "academics_and_faculties"
        elif "/research" in norm or "patent" in norm or "publication" in norm:
            return "research_and_innovation"
        elif "/campus" in norm or "/hostel" in norm or "/facility" in norm or "sports" in norm or "library" in norm:
            return "campus_and_facilities"
        elif "/centres" in norm or "cell" in norm or "committee" in norm:
            return "committees_and_cells"
        elif "/nirf" in norm:
            return "nirf_and_disclosures"
        elif "/blog" in norm or "/event" in norm:
            return "events_and_news"
        else:
            return "general_university"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for duplicate detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def fetch_sitemap_urls(self, sitemap_url: Optional[str] = None) -> List[str]:
        """Fetch and parse valid URLs from sitemap.xml"""
        if sitemap_url is None:
            sitemap_url = urljoin(self.base_url, "/sitemap.xml")

        try:
            resp = requests.get(sitemap_url, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch sitemap: HTTP {resp.status_code}")
                return []

            root = ET.fromstring(resp.content)
            all_urls = [elem.text.strip() for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]

            valid_urls = []
            for u in all_urls:
                norm_u = self.normalize_url(u)
                if not self.is_same_domain(norm_u):
                    continue
                # Exclude known obsolete/template routes
                if any(excluded in norm_u for excluded in EXCLUDED_ROUTE_PATTERNS):
                    logger.debug(f"Excluding known obsolete route: {norm_u}")
                    continue
                valid_urls.append(norm_u)

            logger.info(f"Fetched {len(valid_urls)} valid candidate URLs from {sitemap_url} (excluded {len(all_urls) - len(valid_urls)} obsolete routes)")
            return valid_urls
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []

    def extract_title(self, soup: BeautifulSoup, driver_title: str = "") -> str:
        """Extract page title"""
        if driver_title and driver_title.strip() and driver_title != "KPGU":
            return driver_title.strip()
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.string:
            return h1_tag.string.strip()
        return "KPGU - Drs. Kiran & Pallavi Patel Global University"

    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract clean content from parsed DOM, removing nav, footer, script tags"""
        for element in soup(["script", "style", "nav", "footer", "noscript", "iframe", "svg"]):
            element.decompose()

        unwanted_selectors = [
            ".menu", ".navigation", ".footer", "#footer",
            ".cookie", ".popup", "#cookie", "#popup"
        ]
        for sel in unwanted_selectors:
            for el in soup.select(sel):
                el.decompose()

        main_elem = soup.find(id="root") or soup.find("main") or soup.body or soup
        text = main_elem.get_text(separator=" ", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)

    def crawl_page(self, url: str) -> Optional[Dict]:
        """Crawl a single page using managed Selenium WebDriver"""
        driver = self._ensure_driver()
        norm_url = self.normalize_url(url)

        try:
            logger.info(f"Crawling URL: {norm_url}")
            driver.get(norm_url)

            # Wait for React SPA to render text inside #root
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_element(By.ID, "root").text.strip()) > 80
                )
            except Exception:
                logger.debug(f"Wait timeout for #root text on {norm_url}, checking available DOM")

            # Check rendered text for 404 status
            root_text = ""
            try:
                root_text = driver.find_element(By.ID, "root").text.strip()
            except Exception:
                root_text = driver.find_element(By.TAG_NAME, "body").text.strip()

            if "ERROR 404" in root_text or "Page Not Found" in root_text or "Oops! That page can’t be found" in root_text:
                logger.warning(f"URL rendered 404 Page Not Found: {norm_url}")
                return None

            if len(root_text) < 100:
                logger.warning(f"Insufficient rendered text ({len(root_text)} chars) for: {norm_url}")
                return None

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            title = self.extract_title(soup, driver_title=driver.title)
            content = self.extract_main_content(soup)

            if len(content.strip()) < 100:
                logger.warning(f"Extracted content too short for {norm_url}")
                return None

            content_hash = self.calculate_content_hash(content)
            category = self.categorize_url(norm_url, title)

            document = {
                "url": norm_url,
                "title": title,
                "category": category,
                "content": content,
                "content_hash": content_hash,
                "crawl_timestamp": time.time(),
                "word_count": len(content.split()),
                "char_count": len(content)
            }

            logger.info(f"Successfully crawled: [{category}] {title} ({len(content)} chars)")
            return document

        except Exception as e:
            logger.error(f"Error crawling {norm_url}: {e}")
            err_msg = str(e).lower()
            if any(term in err_msg for term in ["invalid session id", "session deleted", "disconnected", "no such execution context", "chrome not reachable"]):
                logger.warning(f"Resetting Selenium WebDriver session due to error: {e}")
                self.close_driver()
            return None

    def crawl_sitemap(self, sitemap_url: Optional[str] = None, max_pages: int = 100) -> List[Dict]:
        """Crawl all verified pages listed in sitemap"""
        candidate_urls = self.fetch_sitemap_urls(sitemap_url)
        logger.info(f"Beginning sitemap crawl for up to {min(len(candidate_urls), max_pages)} pages...")

        for idx, url in enumerate(candidate_urls[:max_pages]):
            if url in self.visited_urls:
                continue

            # Periodically recycle driver to prevent Chrome memory accumulation or stalls
            if idx > 0 and idx % 15 == 0:
                logger.info(f"Recycling WebDriver session after {idx} pages...")
                self.close_driver()

            doc = self.crawl_page(url)
            self.visited_urls.add(url)

            if doc:
                self.documents.append(doc)

            time.sleep(1.0)  # Polite crawling delay

        logger.info(f"Sitemap crawl finished: {len(self.documents)} valid documents crawled from {len(self.visited_urls)} URLs")
        return self.documents

    def crawl_website(self, max_pages: int = 100) -> List[Dict]:
        """Crawl starting from sitemap or fallback BFS"""
        try:
            return self.crawl_sitemap(max_pages=max_pages)
        finally:
            self.close_driver()

    def save_documents(self, output_dir: Optional[str] = None):
        """Save crawled documents with content hashes and metadata"""
        if output_dir is None:
            output_dir = settings.DATA_RAW_DIR

        os.makedirs(output_dir, exist_ok=True)

        # Load existing hashes to support incremental updates
        existing_hashes = {}
        for existing_file in os.listdir(output_dir):
            if existing_file.startswith("document_") and existing_file.endswith(".json"):
                try:
                    fpath = os.path.join(output_dir, existing_file)
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "url" in data and "content_hash" in data:
                            existing_hashes[data["url"]] = (data["content_hash"], existing_file)
                except Exception:
                    pass

        saved_count = 0
        file_idx = len(existing_hashes)

        for doc in self.documents:
            url = doc["url"]
            c_hash = doc["content_hash"]

            if url in existing_hashes:
                old_hash, old_filename = existing_hashes[url]
                if old_hash == c_hash:
                    # Content unchanged
                    continue
                else:
                    # Update existing file
                    target_filename = old_filename
            else:
                target_filename = f"document_{file_idx:04d}.json"
                file_idx += 1

            filepath = os.path.join(output_dir, target_filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            saved_count += 1

        metadata = {
            "total_documents": len(self.documents),
            "crawl_timestamp": time.time(),
            "source_domain": self.domain,
            "categories": list(set(d.get("category", "general") for d in self.documents))
        }

        with open(os.path.join(output_dir, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved {saved_count} new/updated documents (total {len(self.documents)}) to {output_dir}")

def crawl_kpgu_website(max_pages: int = 100) -> List[Dict]:
    """Convenience function to crawl KPGU verified sitemap"""
    crawler = CrawlerService()
    try:
        documents = crawler.crawl_website(max_pages=max_pages)
        crawler.save_documents()
        return documents
    finally:
        crawler.close_driver()