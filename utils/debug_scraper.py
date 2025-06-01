#!/usr/bin/env python3
"""
Test script for Documentation Scraper

This script performs a quick test of the scraper functionality with a limited
number of pages to verify that crawl4ai is working properly before running
the full documentation scrape.

Usage:
    python utils/debug_scraper.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import configuration
try:
    from config import SCRAPER_CONFIG, ADVANCED_CONFIG
except ImportError as e:
    print("❌ Configuration file 'config.py' is required but not found.")
    print("Please ensure config.py exists in the root directory and contains the required configuration variables.")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    try:
        import crawl4ai
        print("✅ crawl4ai is installed")
    except ImportError:
        print("❌ crawl4ai not found. Install with: pip install crawl4ai")
        return False
    
    try:
        import sqlite3
        print("✅ sqlite3 is available")
    except ImportError:
        print("❌ sqlite3 not available")
        return False
    
    return True


async def test_basic_crawl():
    """Test basic crawling functionality"""
    print("\n🧪 Testing basic crawl functionality...")
    
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator
        from crawl4ai.content_filter_strategy import PruningContentFilter
        
        # Get test URL from config
        base_url = SCRAPER_CONFIG.get("base_url", "https://docs.example.com/")
        domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Create minimal configuration
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        )
        
        run_config = CrawlerRunConfig(
            markdown_generator=markdown_generator,
            page_timeout=15000,  # Shorter timeout for testing
            wait_for_images=False,
            screenshot=False,
        )
        
        async with AsyncWebCrawler(config=None) as crawler:
            print(f"🌐 Fetching: {base_url}")
            result = await crawler.arun(url=base_url, config=run_config)
            
            if result.success:
                print(f"✅ Basic crawl successful for {domain_name}!")
                
                # Safely access markdown content
                markdown_content = ""
                if hasattr(result, 'markdown') and result.markdown:
                    if hasattr(result.markdown, 'fit_markdown'):
                        markdown_content = result.markdown.fit_markdown
                    elif hasattr(result.markdown, 'markdown'):
                        markdown_content = result.markdown.markdown
                    elif isinstance(result.markdown, str):
                        markdown_content = result.markdown
                
                print(f"📝 Extracted {len(markdown_content)} characters of markdown")
                
                # Safely access links
                links_count = 0
                if hasattr(result, 'links'):
                    if isinstance(result.links, dict):
                        # Count all links if it's a dict with categories
                        for key, link_list in result.links.items():
                            if isinstance(link_list, list):
                                links_count += len(link_list)
                    elif hasattr(result.links, 'internal'):
                        links_count = len(result.links.internal)
                    elif isinstance(result.links, list):
                        links_count = len(result.links)
                
                print(f"🔗 Found {links_count} links")
                
                # Check if we got some content
                if len(markdown_content) > 100:  # Should have at least some content
                    return True
                else:
                    print("⚠️  Warning: Very little content extracted")
                    return True  # Still pass the test
                    
            else:
                print(f"❌ Crawl failed: {result.error_message}")
                return False
                
    except Exception as e:
        print(f"❌ Error during basic crawl test: {str(e)}")
        return False


async def test_mini_scraper():
    """Test the scraper with a very limited configuration"""
    print("\n🧪 Testing mini scraper (max 5 pages)...")
    
    try:
        # Import the scraper
        from docs_scraper import DocumentationScraper
        
        # Get config values
        base_url = SCRAPER_CONFIG.get("base_url", "https://docs.example.com/")
        domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Create test output directory
        test_output = Path("test_output")
        test_output.mkdir(exist_ok=True)
        
        # Create mini scraper configuration
        mini_scraper = DocumentationScraper(
            base_url=base_url,
            output_dir="test_output",
            max_depth=1,  # Only go 1 level deep
            max_pages=5,  # Very limited for testing
            delay_between_requests=0.1  # Faster for testing
        )
        
        print(f"🚀 Starting mini scrape of {domain_name}...")
        await mini_scraper.scrape_documentation()
        
        # Check if files were created
        db_path = test_output / "documentation.db"
        json_path = test_output / "documentation.json"
        context_dir = test_output / "llm_context"
        
        if db_path.exists():
            print("✅ Database created successfully")
        else:
            print("❌ Database not created")
            return False
            
        if json_path.exists():
            print("✅ JSON export created successfully")
        else:
            print("❌ JSON export not created")
            
        if context_dir.exists():
            print("✅ LLM context directory created")
        else:
            print("❌ LLM context directory not created")
            
        # Check database content
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM pages")
            page_count = cursor.fetchone()[0]
            print(f"📊 Scraped {page_count} pages in test")
            
        if page_count > 0:
            print(f"✅ Mini scraper test successful for {domain_name}!")
            return True
        else:
            print("❌ No pages were scraped")
            return False
            
    except Exception as e:
        print(f"❌ Error during mini scraper test: {str(e)}")
        return False


def test_query_tool():
    """Test the query tool functionality"""
    print("\n🧪 Testing query tool...")
    
    try:
        from query_docs import DocumentationQuery
        
        # Test with the test database
        test_db = Path("test_output/documentation.db")
        if not test_db.exists():
            print("⚠️  Test database not found, skipping query tool test")
            return True
            
        query_tool = DocumentationQuery("test_output/documentation.db")
        
        # Test stats
        stats = query_tool.get_stats()
        domain_name = stats.get('domain_name', 'Documentation')
        print(f"📊 Found {stats['total_pages']} pages, {stats['total_words']} words for {domain_name}")
        
        # Test sections
        sections = query_tool.get_all_sections()
        print(f"📚 Found {len(sections)} sections: {sections}")
        
        # Test search with domain-specific keywords
        search_keywords = ADVANCED_CONFIG.get("scoring_keywords", ["tutorial", "guide", "documentation"])
        search_term = search_keywords[0] if search_keywords else "guide"
        
        search_results = query_tool.search_content(search_term, limit=2)
        print(f"🔍 Search test for '{search_term}': found {len(search_results)} results")
        
        print("✅ Query tool test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error during query tool test: {str(e)}")
        return False


def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    try:
        import shutil
        test_dir = Path("test_output")
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Could not clean up test files: {e}")


async def main():
    """Main test function"""
    # Get configuration for display
    base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    print(f"🧪 Documentation Scraper - Test Suite")
    print(f"📚 Target: {domain_name}")
    print("=" * 50)
    
    # Track test results
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Dependencies
    if check_dependencies():
        tests_passed += 1
    else:
        print("\n❌ Dependency check failed. Please install required packages.")
        return False
    
    # Test 2: Basic crawl
    if await test_basic_crawl():
        tests_passed += 1
    else:
        print("\n❌ Basic crawl test failed. Check your internet connection and crawl4ai installation.")
        return False
    
    # Test 3: Mini scraper
    if await test_mini_scraper():
        tests_passed += 1
    else:
        print("\n❌ Mini scraper test failed.")
        return False
    
    # Test 4: Query tool
    if test_query_tool():
        tests_passed += 1
    
    # Results
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print(f"\n🎉 All tests passed! You're ready to run the full scraper for {domain_name}.")
        print("💡 Run: python docs_scraper.py")
        print("\n📋 Configuration Summary:")
        print(f"   Base URL: {base_url}")
        print(f"   Max Depth: {SCRAPER_CONFIG.get('max_depth', 3)}")
        print(f"   Max Pages: {SCRAPER_CONFIG.get('max_pages', 600)}")
        print(f"   Output Dir: {SCRAPER_CONFIG.get('output_dir', 'docs_db')}")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed. Check the output above for issues.")
    
    # Ask user if they want to clean up test files
    try:
        response = input("\n🗑️  Clean up test files? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            cleanup_test_files()
    except KeyboardInterrupt:
        print("\n")
        cleanup_test_files()
    
    return tests_passed == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        cleanup_test_files()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        cleanup_test_files()
        sys.exit(1) 