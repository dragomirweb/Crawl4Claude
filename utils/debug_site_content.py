#!/usr/bin/env python3
"""Debug script to examine content extraction from documentation sites"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Import configuration
try:
    from config import (
        SCRAPER_CONFIG, 
        DEBUG_CONFIG, 
        BROWSER_CONFIG as CONFIG_BROWSER,
    )
except ImportError as e:
    raise ImportError(
        "Configuration file 'config.py' is required but not found. "
        "Please ensure config.py exists in the root directory and contains the required configuration variables."
    ) from e


async def debug_content_extraction():
    """Debug what content we're actually getting from the documentation site"""
    
    base_url = SCRAPER_CONFIG.get("base_url", "https://docs.example.com/")
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    print(f"🔍 Debugging content extraction for {domain_name}...")
    
    # Get test URLs from config
    test_urls = DEBUG_CONFIG.get("test_urls", [base_url])
    validation_keywords = DEBUG_CONFIG.get("content_validation_keywords", ["documentation"])
    preview_length = DEBUG_CONFIG.get("preview_length", 500)
    verbose = DEBUG_CONFIG.get("verbose_output", True)
    
    # If test URLs are still example URLs, use base URL instead
    if all("example.com" in url for url in test_urls):
        test_urls = [base_url, base_url.rstrip('/') + '/getting-started/']
        print(f"⚠️  Using base URL as test URLs are not configured for {domain_name}")
    
    # Configure browser from config
    browser_config = BrowserConfig(
        headless=CONFIG_BROWSER.get("headless", True),
        user_agent=CONFIG_BROWSER.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        extra_args=CONFIG_BROWSER.get("extra_args", ["--no-sandbox", "--disable-dev-shm-usage", "--disable-images"])
    )
    
    # Simple run config for debugging - no filtering
    run_config = CrawlerRunConfig(
        page_timeout=SCRAPER_CONFIG.get("page_timeout", 30000),
        js_code=["window.scrollTo(0, document.body.scrollHeight);"],  # Scroll to trigger content
        word_count_threshold=1,  # Accept any content
        delay_before_return_html=3.0,  # Wait for content to load
        screenshot=False,
        verbose=verbose
    )
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}/{len(test_urls)}: {test_url}")
        print(f"{'='*60}")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=test_url, config=run_config)
            
            if result.success:
                print(f"✅ Success! Status: {result.status_code}")
                print(f"📄 Raw HTML length: {len(result.html):,} characters")
                print(f"📝 Cleaned HTML length: {len(result.cleaned_html) if result.cleaned_html else 0:,} characters")
                print(f"📚 Markdown length: {len(result.markdown) if result.markdown else 0:,} characters")
                
                # Show HTML preview
                if verbose and result.html:
                    print(f"\n🔍 HTML Preview (first {preview_length} chars):")
                    print(result.html[:preview_length])
                    print("..." if len(result.html) > preview_length else "")
                
                # Show cleaned HTML preview
                if verbose and result.cleaned_html:
                    print(f"\n🧹 Cleaned HTML Preview (first {preview_length} chars):")
                    print(result.cleaned_html[:preview_length])
                    print("..." if len(result.cleaned_html) > preview_length else "")
                
                # Show markdown preview
                if verbose and result.markdown:
                    print(f"\n📚 Markdown Preview (first {preview_length} chars):")
                    markdown_str = str(result.markdown)
                    print(markdown_str[:preview_length])
                    print("..." if len(markdown_str) > preview_length else "")
                
                # Check for title
                if result.metadata:
                    title = result.metadata.get('title', 'No title found')
                    print(f"\n📋 Page Title: {title}")
                
                # Analyze content quality
                await analyze_content_quality(result, validation_keywords, domain_name)
                
                # Link analysis
                await analyze_links(result)
                
                # Media analysis  
                await analyze_media(result)
                
                # Save debug files if enabled
                if DEBUG_CONFIG.get("save_debug_files", False):
                    await save_debug_files(result, test_url, i)
                
            else:
                print(f"❌ Failed: {result.error_message}")
                print(f"🔍 Status Code: {getattr(result, 'status_code', 'Unknown')}")


async def analyze_content_quality(result, validation_keywords, domain_name):
    """Analyze the quality and relevance of extracted content"""
    print(f"\n📊 Content Quality Analysis:")
    
    # Check different content sources
    content_sources = {
        "Raw HTML": result.html,
        "Cleaned HTML": result.cleaned_html,
        "Markdown": str(result.markdown) if result.markdown else ""
    }
    
    for source_name, content in content_sources.items():
        if not content:
            print(f"   {source_name}: ❌ No content")
            continue
            
        content_lower = content.lower()
        
        # Check for validation keywords
        keyword_matches = sum(1 for keyword in validation_keywords if keyword.lower() in content_lower)
        keyword_percentage = (keyword_matches / len(validation_keywords)) * 100 if validation_keywords else 0
        
        # Check for common issues
        issues = []
        if "loading" in content_lower or "skeleton" in content_lower:
            issues.append("Possible JS loading issue")
        if len(content.strip()) < 100:
            issues.append("Very short content")
        if content_lower.count("nav") > 5:
            issues.append("High navigation content")
        
        print(f"   {source_name}: ✅ {len(content):,} chars, {keyword_percentage:.0f}% keyword match")
        if issues:
            print(f"      ⚠️  Issues: {', '.join(issues)}")


async def analyze_links(result):
    """Analyze extracted links"""
    print(f"\n🔗 Link Analysis:")
    
    internal_links = 0
    external_links = 0
    
    if hasattr(result, 'links'):
        if hasattr(result.links, 'internal'):
            internal_links = len(result.links.internal)
            external_links = len(result.links.external)
        elif isinstance(result.links, dict):
            internal_links = len(result.links.get('internal', []))
            external_links = len(result.links.get('external', []))
    
    print(f"   Internal links: {internal_links}")
    print(f"   External links: {external_links}")
    
    if internal_links == 0 and external_links == 0:
        print(f"   ⚠️  No links found - possible extraction issue")


async def analyze_media(result):
    """Analyze extracted media"""
    print(f"\n🖼️  Media Analysis:")
    
    images_count = 0
    if hasattr(result, 'media'):
        if hasattr(result.media, 'images'):
            images_count = len(result.media.images)
        elif isinstance(result.media, dict):
            images_count = len(result.media.get('images', []))
    
    print(f"   Images found: {images_count}")


async def save_debug_files(result, test_url, test_number):
    """Save debug files for further analysis"""
    debug_dir = Path("debug_output")
    debug_dir.mkdir(exist_ok=True)
    
    base_name = f"debug_test_{test_number}"
    
    # Save HTML
    if result.html:
        html_file = debug_dir / f"{base_name}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(result.html)
        print(f"   💾 Saved HTML: {html_file}")
    
    # Save cleaned HTML
    if result.cleaned_html:
        cleaned_file = debug_dir / f"{base_name}_cleaned.html"
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(result.cleaned_html)
        print(f"   💾 Saved cleaned HTML: {cleaned_file}")
    
    # Save markdown
    if result.markdown:
        md_file = debug_dir / f"{base_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(str(result.markdown))
        print(f"   💾 Saved markdown: {md_file}")


async def test_scraper_compatibility():
    """Test compatibility with the main scraper configuration"""
    print(f"\n🔧 Scraper Compatibility Test:")
    
    base_url = SCRAPER_CONFIG.get("base_url")
    max_depth = SCRAPER_CONFIG.get("max_depth", 3)
    max_pages = SCRAPER_CONFIG.get("max_pages", 100)
    
    print(f"   Base URL: {base_url}")
    print(f"   Max depth: {max_depth}")
    print(f"   Max pages: {max_pages}")
    
    # Test if we can connect to the base URL
    browser_config = BrowserConfig(
        headless=True,
        user_agent=CONFIG_BROWSER.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    )
    
    run_config = CrawlerRunConfig(
        page_timeout=10000,  # Quick test
        word_count_threshold=1
    )
    
    print(f"   Testing connection to {base_url}...")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=base_url, config=run_config)
        
        if result.success:
            print(f"   ✅ Connection successful (Status: {result.status_code})")
            print(f"   📄 Content length: {len(result.html):,} characters")
        else:
            print(f"   ❌ Connection failed: {result.error_message}")
            print(f"   💡 Check base_url in config.py")


def main():
    """Main debug function"""
    base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    print(f"🐛 Documentation Content Extraction Debug Tool")
    print(f"📚 Target: {domain_name}")
    print(f"🔧 Config file: config.py")
    print("=" * 60)
    
    try:
        asyncio.run(debug_content_extraction())
        asyncio.run(test_scraper_compatibility())
        
        print(f"\n✅ Debug complete!")
        print(f"\n💡 Tips for better extraction:")
        print(f"   • Update test_urls in DEBUG_CONFIG for your site")
        print(f"   • Adjust content_validation_keywords for your domain")
        print(f"   • Check page_timeout if content isn't loading")
        print(f"   • Enable save_debug_files to examine raw output")
        
    except Exception as e:
        print(f"\n❌ Debug failed: {str(e)}")
        print(f"💡 Check your config.py file and network connection")


if __name__ == "__main__":
    main() 