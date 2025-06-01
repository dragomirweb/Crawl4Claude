"""
Configuration file for Documentation Scraper

This file contains all the configuration options that users typically need to customize
when scraping different documentation sites or knowledge bases.
"""

from pathlib import Path
from urllib.parse import urlparse

# Basic scraping configuration
SCRAPER_CONFIG = {
    # Target website - CUSTOMIZE THIS for your documentation site
    "base_url": "https://docs.example.com/",
    
    # Output settings
    "output_dir": "docs_db",
    
    # Crawling limits
    "max_depth": 3,          # How many levels deep to crawl (1-5 recommended)
    "max_pages": 20,        # Maximum pages to scrape
    
    # Rate limiting (be respectful to the target site!)
    "delay_between_requests": 0.5,  # Seconds between requests (0.5-2.0 recommended)
    "page_timeout": 30000,          # Timeout per page in milliseconds
    
    # Browser settings
    "headless": True,               # Run browser in background (True recommended)
    "user_agent": "Documentation-Scraper/1.0 (Educational Purpose)",
    
    # Content processing
    "cache_enabled": True,          # Enable caching for resumable crawls
    "content_filtering": True,      # Remove navigation and boilerplate
    "generate_screenshots": False,  # Don't generate screenshots (saves time/space)
}

# URL filtering rules - CUSTOMIZE these patterns for your target site
URL_FILTER_CONFIG = {
    # Skip these URL patterns (regex patterns)
    "skip_patterns": [
        r'/api/',
        r'/search',
        r'\.pdf$',
        r'\.zip$',
        r'\.tar\.gz$',
        r'/edit/',
        r'/history/',
        r'#',  # Fragment-only URLs
        r'\?',  # Query parameters (usually duplicates)
    ],
    
    # Only crawl these domains - UPDATE this for your target site
    "allowed_domains": ["docs.example.com"],
    
    # Priority sections (crawl these first if using BestFirst strategy)
    # UPDATE these section names for your documentation structure
    "priority_sections": [
        "getting-started",
        "tutorials", 
        "guides",
        "reference"
    ]
}

# Content cleaning patterns - CUSTOMIZE for your site's structure
CONTENT_FILTER_CONFIG = {
    # Patterns to remove from markdown content
    "remove_patterns": [
        r'<!-- .*? -->',                    # HTML comments
        r'\[Edit this page.*?\]',           # Edit links
        r'Table of Contents.*?\n',          # TOC headers
        r'Skip to main content.*?\n',       # Skip links
        r'Previous\s+Next.*?\n',            # Navigation
        r'Improve this doc.*?\n',           # Improvement links
        r'Was this helpful\?.*?\n',         # Feedback sections
        r'Rate this page.*?\n',             # Rating sections
    ],
    
    # Additional cleanup rules
    "clean_excessive_whitespace": True,
    "remove_empty_sections": True,
    "max_consecutive_newlines": 2,
}

# Database and export settings
EXPORT_CONFIG = {
    # Export formats to generate
    "generate_json": True,
    "generate_sqlite": True,
    "generate_llm_context": True,
    "generate_summary": True,
    
    # LLM context options
    "create_master_file": True,          # Single file with all content
    "create_section_files": True,        # Separate files per section
    "max_file_size_mb": 10,             # Split large files
    
    # Content organization
    "sort_by_title": True,
    "include_metadata": True,
    "include_word_counts": True,
}

# Advanced crawling options
ADVANCED_CONFIG = {
    # Deep crawling strategy
    "crawl_strategy": "BFS",  # Options: "BFS" (Breadth-First), "DFS" (Depth-First), "BestFirst"
    
    # For BestFirst strategy - UPDATE keywords for your domain
    "scoring_keywords": ["tutorial", "guide", "documentation", "reference"],
    
    # Browser optimization
    "wait_for_images": False,            # Skip image loading for speed
    "disable_javascript": False,         # Keep JS enabled for SPAs
    "block_resources": ["image", "media", "font"],  # Block these resource types for speed
    
    # Error handling
    "max_retries": 3,
    "retry_delay": 2.0,
    "continue_on_error": True,
}

# Logging configuration
LOGGING_CONFIG = {
    "log_level": "INFO",  # Options: DEBUG, INFO, WARNING, ERROR
    "log_to_file": True,
    "log_to_console": True,
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
}

# Content extraction settings - FINE-TUNE these for your site's content structure
CONTENT_CONFIG = {
    "content_filter": {
        "type": "PruningContentFilter",
        "threshold": 0.48,  # Lower threshold for more content
        "threshold_type": "fixed",
        "min_word_threshold": 10,  # Lower minimum to capture shorter content
        "sim_threshold": 0.5,
        "always_bypass_local_score_threshold": False,
        "tags_to_exclude": [
            "nav", "footer", "header", "aside", 
            "script", "style", "meta", "noscript",
            ".nav", ".footer", ".header", ".sidebar",
            ".advertisement", ".ad", ".cookie",
            ".search-bar", ".menu", ".breadcrumb"
        ]
    },
    "wait_for_load": True,
    "wait_time": 5000,  # Increased wait time for JS content (5 seconds)
    "js_wait_time": 3000,  # Additional wait for JavaScript execution
    "remove_forms": True,
    "remove_overlay": True,
    "extract_blocks": True,
    "word_count_threshold": 5  # Lower threshold to capture more content
}

# Browser configuration for better JS handling
BROWSER_CONFIG = {
    "headless": True,
    "browser_type": "chromium",
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "extra_args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # Faster loading
        "--disable-javascript-harmony-shipping",
        "--disable-ipc-flooding-protection"
    ],
    "java_script_enabled": True,
    "load_images": False,  # Skip images for faster loading
    "accept_downloads": False,
    "ignore_https_errors": True
}

# Debug and testing configuration
DEBUG_CONFIG = {
    # Test URLs for debugging content extraction - UPDATE these for your site
    "test_urls": [
        # Primary test URL - should be a content-rich page
        "https://docs.example.com/getting-started/",
        # Secondary test URL - should be a different section
        "https://docs.example.com/tutorials/first-tutorial/",
    ],
    
    # Content validation keywords - UPDATE these for your domain
    # These are used to verify that meaningful content was extracted
    "content_validation_keywords": [
        "tutorial", "guide", "documentation", "example", "reference"
    ],
    
    # Debug output settings
    "preview_length": 500,  # Characters to show in preview
    "verbose_output": True,  # Show detailed debug information
    "save_debug_files": False,  # Save debug HTML/markdown to files
}

# MCP (Model Context Protocol) server configuration
MCP_CONFIG = {
    # Server identification
    "server_name": "docs-server",  # Name of the MCP server
    "server_description": "Documentation Search and Retrieval Server",
    
    # Documentation display name (will derive from base_url if None)
    "docs_display_name": None,  # Will derive from base_url if None
    
    # Search and retrieval settings
    "default_search_limit": 10,  # Default number of search results
    "max_search_limit": 50,     # Maximum allowed search results
    "default_section_limit": 20, # Default pages per section
    "max_section_limit": 100,   # Maximum pages per section
    
    # Content settings
    "include_full_urls": True,  # Add full URLs to results
    "snippet_length": 32,       # Words in search snippets
    "enable_fts_fallback": True, # Use LIKE search if FTS unavailable
}

# Helper functions for derived configuration values
def get_database_path():
    """Get the complete database path"""
    output_dir = SCRAPER_CONFIG.get("output_dir", "docs_db")
    return str(Path(output_dir) / "documentation.db")


def get_docs_display_name():
    """Get the display name for the documentation"""
    if MCP_CONFIG.get("docs_display_name"):
        return MCP_CONFIG["docs_display_name"]
    
    base_url = SCRAPER_CONFIG.get("base_url", "")
    if base_url:
        parsed = urlparse(base_url)
        return parsed.netloc or "Documentation"
    
    return "Documentation"


def get_mcp_server_config():
    """Get complete MCP server configuration with derived values"""
    return {
        "db_path": get_database_path(),
        "docs_name": get_docs_display_name(),
        "server_name": MCP_CONFIG.get("server_name", "docs-server"),
        "base_url": SCRAPER_CONFIG.get("base_url", ""),
        "server_description": MCP_CONFIG.get("server_description", "Documentation Server"),
        "search_limit": MCP_CONFIG.get("default_search_limit", 10),
        "max_search_limit": MCP_CONFIG.get("max_search_limit", 50),
        "section_limit": MCP_CONFIG.get("default_section_limit", 20),
        "max_section_limit": MCP_CONFIG.get("max_section_limit", 100),
        "snippet_length": MCP_CONFIG.get("snippet_length", 32),
        "enable_fts_fallback": MCP_CONFIG.get("enable_fts_fallback", True),
        "include_full_urls": MCP_CONFIG.get("include_full_urls", True),
    } 