#!/usr/bin/env python3
"""
Generic Documentation Scraper using Crawl4AI

This script scrapes documentation websites and creates a structured mini database
of documentation content for use as LLM context. The script uses crawl4ai to:

1. Discover all documentation pages
2. Extract clean content from each page  
3. Store structured data in JSON format
4. Create embeddings-ready content for LLM context

Usage:
    python docs_scraper.py

Features:
- Deep crawling of documentation sites
- Content cleaning and Markdown extraction
- Structured data storage (JSON + SQLite)
- Progress tracking and error handling
- Resumable crawling with cache
- LLM-optimized content preparation
"""

import asyncio
import json
import logging
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    BFSDeepCrawlStrategy
)
from crawl4ai.content_filter_strategy import PruningContentFilter

# Import configuration (required - no fallback)
try:
    from config import (
        SCRAPER_CONFIG, 
        URL_FILTER_CONFIG, 
        CONTENT_FILTER_CONFIG,
        EXPORT_CONFIG,
        LOGGING_CONFIG
    )
except ImportError as e:
    raise ImportError(
        "Configuration file 'config.py' is required but not found. "
        "Please ensure config.py exists and contains the required configuration variables."
    ) from e


class DocumentationScraper:
    """Main scraper class for documentation websites"""
    
    def __init__(
        self,
        base_url: str = None,
        output_dir: str = None,
        max_depth: int = None,
        max_pages: int = None,
        delay_between_requests: float = None
    ):
        # Use config values as defaults, allow override
        self.base_url = (base_url or SCRAPER_CONFIG["base_url"]).rstrip('/')
        self.output_dir = Path(output_dir or SCRAPER_CONFIG["output_dir"])
        self.max_depth = max_depth or SCRAPER_CONFIG["max_depth"]
        self.max_pages = max_pages or SCRAPER_CONFIG["max_pages"]
        self.delay_between_requests = delay_between_requests or SCRAPER_CONFIG["delay_between_requests"]
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize data storage
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.docs_data: List[Dict] = []
        
        # Database setup
        self.db_path = self.output_dir / "documentation.db"
        self.setup_database()
        
    def setup_logging(self):
        """Configure logging for the scraper"""
        log_file = self.output_dir / "scraper.log"
        
        handlers = []
        if LOGGING_CONFIG.get("log_to_file", True):
            handlers.append(logging.FileHandler(log_file))
        if LOGGING_CONFIG.get("log_to_console", True):
            handlers.append(logging.StreamHandler())
        
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG.get("log_level", "INFO")),
            format=LOGGING_CONFIG.get("log_format", '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=handlers,
            force=True  # Override any existing configuration
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """Setup SQLite database for storing documentation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content TEXT,
                    markdown TEXT,
                    word_count INTEGER,
                    section TEXT,
                    subsection TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_url TEXT NOT NULL,
                    to_url TEXT NOT NULL,
                    anchor_text TEXT,
                    FOREIGN KEY (from_url) REFERENCES pages (url)
                )
            """)
            
            # Create FTS (Full Text Search) virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                    title, markdown, url, section,
                    content='pages',
                    content_rowid='id'
                )
            """)
            
            # Create triggers to keep FTS table in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                    INSERT INTO pages_fts(rowid, title, markdown, url, section)
                    VALUES (new.id, new.title, new.markdown, new.url, new.section);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
                    INSERT INTO pages_fts(pages_fts, rowid, title, markdown, url, section)
                    VALUES('delete', old.id, old.title, old.markdown, old.url, old.section);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
                    INSERT INTO pages_fts(pages_fts, rowid, title, markdown, url, section)
                    VALUES('delete', old.id, old.title, old.markdown, old.url, old.section);
                    INSERT INTO pages_fts(rowid, title, markdown, url, section)
                    VALUES (new.id, new.title, new.markdown, new.url, new.section);
                END
            """)
            
            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_section ON pages(section)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_links_from_url ON links(from_url)")
            
    def extract_page_metadata(self, url: str, content: str, markdown: str) -> Dict:
        """Extract metadata from a documentation page"""
        metadata = {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "word_count": len(markdown.split()) if markdown else 0
        }
        
        # Extract title from markdown or content
        title_match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE) if markdown else None
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        else:
            # Fallback to HTML title extraction
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            metadata["title"] = title_match.group(1).strip() if title_match else "Untitled"
            
        # Extract section and subsection from URL path
        parsed_url = urlparse(url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        
        if len(path_parts) >= 1:
            metadata["section"] = path_parts[0]
        if len(path_parts) >= 2:
            metadata["subsection"] = path_parts[1]
            
        return metadata
        
    def clean_markdown_content(self, markdown: str) -> str:
        """Clean and optimize markdown content for LLM context"""
        if not markdown:
            return ""
            
        # Apply content filtering patterns from config
        for pattern in CONTENT_FILTER_CONFIG.get("remove_patterns", []):
            markdown = re.sub(pattern, '', markdown, flags=re.DOTALL | re.IGNORECASE)
            
        # Clean excessive whitespace if enabled
        if CONTENT_FILTER_CONFIG.get("clean_excessive_whitespace", True):
            max_newlines = CONTENT_FILTER_CONFIG.get("max_consecutive_newlines", 2)
            pattern = r'\n\s*' + r'\n\s*' * (max_newlines - 1) + r'\n+'
            replacement = '\n' * max_newlines
            markdown = re.sub(pattern, replacement, markdown)
        
        return markdown.strip()
        
    def should_crawl_url(self, url: str) -> bool:
        """Determine if a URL should be crawled"""
        parsed = urlparse(url)
        
        # Check allowed domains
        allowed_domains = URL_FILTER_CONFIG.get("allowed_domains", [])
        if allowed_domains and parsed.netloc not in allowed_domains:
            return False
            
        # Skip patterns from config
        skip_patterns = URL_FILTER_CONFIG.get("skip_patterns", [])
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
                
        return True
        
    async def scrape_documentation(self):
        """Main scraping method"""
        self.logger.info(f"Starting documentation scrape from {self.base_url}")
        self.logger.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        # Configure browser for better JS handling 
        browser_config = BrowserConfig(
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            extra_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images"  # Skip images for faster loading
            ]
        )
        
        # Create content filter with optimized settings for documentation
        content_filter = PruningContentFilter(
            threshold=0.48,  # Lower threshold for more content
            threshold_type="fixed", 
            min_word_threshold=10
        )
        
        # Configure markdown generation with content filtering
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        # Configure deep crawling strategy
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=self.max_depth,
            max_pages=self.max_pages,
            include_external=False  # Keep crawling within the same domain
        )
        
        # Configure crawl settings
        cache_mode = CacheMode.BYPASS  # Use BYPASS to ensure fresh content with new settings
        
        run_config = CrawlerRunConfig(
            markdown_generator=markdown_generator,
            deep_crawl_strategy=deep_crawl_strategy,
            cache_mode=cache_mode,
            page_timeout=30000,  # Increased timeout for JS content
            wait_for_images=False,  # Skip image loading for faster crawls
            screenshot=SCRAPER_CONFIG.get("generate_screenshots", False),
            # Better timing for JavaScript content
            delay_before_return_html=3.0,  # Wait 3 seconds for content to load
            word_count_threshold=1  # Accept any content initially
        )
        
        start_time = time.time()
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                self.logger.info("Starting deep crawl...")
                
                # Perform the deep crawl
                results = await crawler.arun(
                    url=self.base_url,
                    config=run_config
                )
                
                self.logger.info(f"Crawl completed. Processing {len(results)} results...")
                
                # Process each crawled page
                for i, result in enumerate(results, 1):
                    if result.success:
                        await self.process_page_result(result)
                        self.logger.info(f"Processed page {i}/{len(results)}: {result.url}")
                        
                        # Rate limiting
                        if self.delay_between_requests > 0:
                            await asyncio.sleep(self.delay_between_requests)
                    else:
                        self.logger.warning(f"Failed to crawl {result.url}: {result.error_message}")
                        self.failed_urls.add(result.url)
                        
        except Exception as e:
            self.logger.error(f"Error during crawling: {str(e)}")
            raise
            
        elapsed_time = time.time() - start_time
        self.logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"Successfully scraped: {len(self.scraped_urls)} pages")
        self.logger.info(f"Failed to scrape: {len(self.failed_urls)} pages")
        
        # Export data
        await self.export_data()
        
    async def process_page_result(self, result):
        """Process a single page crawl result"""
        url = result.url
        
        if url in self.scraped_urls:
            return
            
        # Extract content using the correct CrawlResult API
        html_content = getattr(result, 'cleaned_html', '') or getattr(result, 'html', '') or ""
        
        # Get markdown content
        markdown_content = ""
        if hasattr(result, 'markdown') and result.markdown:
            # Try different markdown attributes based on the API
            if hasattr(result.markdown, 'fit_markdown'):
                markdown_content = result.markdown.fit_markdown
            elif hasattr(result.markdown, 'raw_markdown'):
                markdown_content = result.markdown.raw_markdown
            elif isinstance(result.markdown, str):
                markdown_content = result.markdown
        
        # Clean the markdown
        cleaned_markdown = self.clean_markdown_content(markdown_content)
        
        # Extract metadata
        metadata = self.extract_page_metadata(url, html_content, cleaned_markdown)
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pages 
                (url, title, content, markdown, word_count, section, subsection, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                metadata.get("title", ""),
                html_content,
                cleaned_markdown,
                metadata.get("word_count", 0),
                metadata.get("section", ""),
                metadata.get("subsection", ""),
                json.dumps(metadata)
            ))
            
            # Store links with updated API
            if hasattr(result, 'links') and result.links:
                # Handle both dict and object format for links
                if isinstance(result.links, dict):
                    for link_category in ['internal', 'external']:
                        links = result.links.get(link_category, [])
                        for link in links:
                            # Handle different link formats
                            href = link.get('href') if isinstance(link, dict) else getattr(link, 'href', '')
                            text = link.get('text') if isinstance(link, dict) else getattr(link, 'text', '')
                            conn.execute("""
                                INSERT OR IGNORE INTO links 
                                (from_url, to_url, anchor_text)
                                VALUES (?, ?, ?)
                            """, (url, href, text))
                else:
                    # Handle object-style links
                    for link_category in ['internal', 'external']:
                        links = getattr(result.links, link_category, [])
                        for link in links:
                            href = getattr(link, 'href', '')
                            text = getattr(link, 'text', '')
                            conn.execute("""
                                INSERT OR IGNORE INTO links 
                                (from_url, to_url, anchor_text)
                                VALUES (?, ?, ?)
                            """, (url, href, text))
        
        # Add to in-memory collection
        self.docs_data.append({
            "url": url,
            "title": metadata.get("title", ""),
            "markdown": cleaned_markdown,
            "section": metadata.get("section", ""),
            "subsection": metadata.get("subsection", ""),
            "word_count": metadata.get("word_count", 0),
            "scraped_at": metadata.get("scraped_at", "")
        })
        
        self.scraped_urls.add(url)
        
    async def export_data(self):
        """Export scraped data to various formats"""
        self.logger.info("Exporting scraped data...")
        
        # Export to JSON if enabled
        if EXPORT_CONFIG.get("generate_json", True):
            json_file = self.output_dir / "documentation.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.docs_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Exported JSON data to {json_file}")
        
        # Export LLM-ready context if enabled
        if EXPORT_CONFIG.get("generate_llm_context", True):
            await self.create_llm_context()
        
        # Generate summary statistics if enabled
        if EXPORT_CONFIG.get("generate_summary", True):
            await self.generate_summary()
        
    async def create_llm_context(self):
        """Create LLM-optimized context files"""
        context_dir = self.output_dir / "llm_context"
        context_dir.mkdir(exist_ok=True)
        
        # Group content by sections
        sections = {}
        for doc in self.docs_data:
            section = doc.get("section", "general")
            if section not in sections:
                sections[section] = []
            sections[section].append(doc)
        
        # Create section-based context files if enabled
        if EXPORT_CONFIG.get("create_section_files", True):
            for section, docs in sections.items():
                section_file = context_dir / f"{section}.md"
                
                with open(section_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Documentation: {section.title()}\n\n")
                    f.write(f"Generated on: {datetime.now().isoformat()}\n")
                    f.write(f"Total pages: {len(docs)}\n\n")
                    f.write("---\n\n")
                    
                    for doc in sorted(docs, key=lambda x: x.get("title", "")):
                        f.write(f"## {doc.get('title', 'Untitled')}\n\n")
                        f.write(f"**URL:** {doc['url']}\n\n")
                        if doc.get("subsection"):
                            f.write(f"**Subsection:** {doc['subsection']}\n\n")
                        f.write(doc.get("markdown", "") + "\n\n")
                        f.write("---\n\n")
        
        # Create master context file if enabled
        if EXPORT_CONFIG.get("create_master_file", True):
            master_file = context_dir / "documentation_complete.md"
            with open(master_file, 'w', encoding='utf-8') as f:
                f.write("# Documentation - Complete Reference\n\n")
                f.write(f"Generated on: {datetime.now().isoformat()}\n")
                f.write(f"Total pages: {len(self.docs_data)}\n")
                f.write(f"Base URL: {self.base_url}\n\n")
                
                # Table of contents
                f.write("## Table of Contents\n\n")
                for section in sorted(sections.keys()):
                    f.write(f"- [{section.title()}](#{section.lower().replace(' ', '-')})\n")
                f.write("\n---\n\n")
                
                # Full content organized by sections
                for section, docs in sorted(sections.items()):
                    f.write(f"# {section.title()}\n\n")
                    for doc in sorted(docs, key=lambda x: x.get("title", "")):
                        f.write(f"## {doc.get('title', 'Untitled')}\n\n")
                        f.write(f"**URL:** {doc['url']}\n\n")
                        f.write(doc.get("markdown", "") + "\n\n")
                    f.write("\n---\n\n")
        
        self.logger.info(f"Created LLM context files in {context_dir}")
        
    async def generate_summary(self):
        """Generate summary statistics"""
        summary = {
            "scrape_completed_at": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_pages_scraped": len(self.scraped_urls),
            "total_pages_failed": len(self.failed_urls),
            "sections": {},
            "total_words": sum(doc.get("word_count", 0) for doc in self.docs_data),
            "config_used": {
                "max_depth": self.max_depth,
                "max_pages": self.max_pages,
                "delay_between_requests": self.delay_between_requests
            }
        }
        
        # Analyze by sections
        for doc in self.docs_data:
            section = doc.get("section", "general")
            if section not in summary["sections"]:
                summary["sections"][section] = {
                    "page_count": 0,
                    "word_count": 0,
                    "subsections": set()
                }
            
            summary["sections"][section]["page_count"] += 1
            summary["sections"][section]["word_count"] += doc.get("word_count", 0)
            if doc.get("subsection"):
                summary["sections"][section]["subsections"].add(doc["subsection"])
        
        # Convert sets to lists for JSON serialization
        for section_data in summary["sections"].values():
            section_data["subsections"] = list(section_data["subsections"])
            section_data["subsection_count"] = len(section_data["subsections"])
        
        # Save summary
        summary_file = self.output_dir / "scrape_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Generated summary: {summary_file}")
        self.logger.info(f"Total words scraped: {summary['total_words']:,}")
        self.logger.info(f"Sections found: {list(summary['sections'].keys())}")


async def main():
    """Main entry point"""
    print("🚀 Documentation Scraper")
    print("=" * 50)
    
    # Configuration - you can override defaults here
    scraper = DocumentationScraper(
        # Uncomment and modify to override config.py settings:
        # base_url="https://docs.example.com/",
        # output_dir="docs_db", 
        # max_depth=3,
        # max_pages=200,
        # delay_between_requests=0.5
    )
    
    try:
        await scraper.scrape_documentation()
        print("\n✅ Scraping completed successfully!")
        print(f"📁 Data saved to: {scraper.output_dir}")
        print(f"📊 Database: {scraper.db_path}")
        print(f"🤖 LLM context: {scraper.output_dir}/llm_context/")
        print(f"\n💡 Use a query tool to explore the scraped data!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        raise


if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import crawl4ai
    except ImportError:
        print("❌ crawl4ai not found. Please install it first:")
        print("pip install crawl4ai")
        exit(1)
        
    asyncio.run(main()) 