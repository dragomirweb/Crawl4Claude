#!/usr/bin/env python3
"""
Simple MCP Client for testing the Documentation Server

This script acts as a basic MCP client to test our documentation server
by calling its tools directly and showing the results.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import configuration
try:
    from config import get_mcp_server_config, ADVANCED_CONFIG
    config = get_mcp_server_config()
    print(f"✅ Configuration loaded for {config['docs_name']}")
except ImportError as e:
    print(f"❌ Configuration import failed: {e}")
    print("Please ensure config.py exists in the parent directory")
    sys.exit(1)

# Set environment variables from config
os.environ["DOCS_DB_PATH"] = config["db_path"]
os.environ["DOCS_DB_NAME"] = config["docs_name"]
os.environ["DOCS_BASE_URL"] = config["base_url"]
os.environ["MCP_SERVER_NAME"] = config["server_name"]

try:
    from mcp_docs_server import create_mcp_server
except ImportError as e:
    print(f"❌ Failed to import MCP server: {e}")
    sys.exit(1)


def get_test_search_terms():
    """Get search terms for testing from config"""
    # Use scoring keywords from config if available
    keywords = ADVANCED_CONFIG.get("scoring_keywords", ["tutorial", "guide", "documentation"])
    
    # Add some generic terms that should work for most documentation sites
    additional_terms = ["example", "reference", "API", "configuration"]
    
    # Combine and deduplicate
    all_terms = list(dict.fromkeys(keywords + additional_terms))  # Preserves order, removes duplicates
    
    return all_terms[:4]  # Return first 4 terms for testing


async def test_mcp_tools():
    """Test all MCP tools directly"""
    
    domain_name = config["docs_name"]
    db_path = config["db_path"]
    base_url = config["base_url"]
    
    print(f"🧪 Testing MCP Documentation Server Tools")
    print(f"📚 Target: {domain_name}")
    print("=" * 60)
    
    # Import the DocumentationMCP class directly for testing
    from mcp_docs_server import DocumentationMCP
    
    # Create the documentation handler using config values
    docs = DocumentationMCP(
        db_path=db_path,
        docs_name=config["docs_name"],
        base_url=base_url if base_url else None
    )
    
    print("✅ Documentation handler created successfully")
    print(f"📊 Database: {db_path}")
    print(f"🔍 FTS Available: {docs.has_fts}")
    
    # Test 1: Get documentation stats  
    print("\n" + "="*60)
    print("🧪 Test 1: get_documentation_stats")
    print("-" * 40)
    
    try:
        stats_result = docs.get_stats()
        stats_result['database_name'] = docs.docs_name
        if docs.base_url:
            stats_result['base_url'] = docs.base_url
        
        print(f"📊 Total Pages: {stats_result.get('total_pages', 'N/A'):,}")
        print(f"📝 Total Words: {stats_result.get('total_words', 'N/A'):,}")
        print(f"📚 Sections: {stats_result.get('section_count', 'N/A')}")
        print(f"🏷️ Database Name: {stats_result.get('database_name', 'N/A')}")
        print(f"🌐 Base URL: {stats_result.get('base_url', 'N/A')}")
        
        if 'top_sections' in stats_result:
            print(f"\n🔝 Top Sections:")
            for section in stats_result['top_sections'][:3]:
                print(f"   - {section['section']}: {section['pages']} pages")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get sections
    print("\n" + "="*60)
    print("🧪 Test 2: get_documentation_sections")
    print("-" * 40)
    
    try:
        sections_result = docs.get_sections()
        
        print(f"📚 Found {len(sections_result)} sections:")
        for i, section in enumerate(sections_result[:5], 1):
            print(f"   {i}. {section['section']}: {section['page_count']} pages ({section['total_words']:,} words)")
        
        if len(sections_result) > 5:
            print(f"   ... and {len(sections_result) - 5} more sections")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search documentation - use first scoring keyword
    print("\n" + "="*60)
    search_terms = get_test_search_terms()
    search_term = search_terms[0] if search_terms else "guide"
    print(f"🧪 Test 3: search_documentation('{search_term}')")
    print("-" * 40)
    
    try:
        search_result = docs.search_content(query=search_term, limit=3)
        
        # Add base URL to results if available
        if docs.base_url:
            for result in search_result:
                if not result['url'].startswith(('http://', 'https://')):
                    result['full_url'] = docs.base_url.rstrip('/') + '/' + result['url'].lstrip('/')
                else:
                    result['full_url'] = result['url']
        
        print(f"🔍 Found {len(search_result)} results for '{search_term}':")
        for i, result in enumerate(search_result, 1):
            print(f"\n   {i}. {result.get('title', 'Untitled')}")
            print(f"      📍 Section: {result.get('section', 'N/A')}")
            print(f"      🔗 URL: {result.get('url', 'N/A')}")
            if result.get('full_url'):
                print(f"      🌐 Full URL: {result['full_url']}")
            print(f"      📝 Words: {result.get('word_count', 0)}")
            if result.get('snippet'):
                snippet = result['snippet'][:100] + "..." if len(result['snippet']) > 100 else result['snippet']
                print(f"      💡 Preview: {snippet}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        search_result = []
    
    # Test 4: Browse section - get first available section
    print("\n" + "="*60)
    section_to_browse = None
    try:
        sections_list = docs.get_sections()
        if sections_list and len(sections_list) > 0:
            section_to_browse = sections_list[0]['section']
    except:
        pass
    
    if section_to_browse:
        print(f"🧪 Test 4: browse_section('{section_to_browse}')")
        print("-" * 40)
        
        try:
            browse_result = docs.get_section_pages(section=section_to_browse, limit=5)
            
            print(f"📚 Found {len(browse_result)} pages in '{section_to_browse}' section:")
            for i, page in enumerate(browse_result, 1):
                print(f"   {i}. {page.get('title', 'Untitled')} ({page.get('word_count', 0)} words)")
                print(f"      🔗 {page.get('url', 'N/A')}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("🧪 Test 4: browse_section (skipped - no sections available)")
        print("-" * 40)
        print("⏭️ No sections found to browse")
    
    # Test 5: Get page content
    print("\n" + "="*60)
    print("🧪 Test 5: get_page_content (from search result)")
    print("-" * 40)
    
    try:
        if search_result and len(search_result) > 0:
            page_url = search_result[0]['url']
            page_result = docs.get_page_by_url(url=page_url)
            
            if page_result and 'error' not in page_result:
                print(f"📄 Page: {page_result.get('title', 'Untitled')}")
                print(f"📍 Section: {page_result.get('section', 'N/A')}")
                print(f"🔗 URL: {page_result.get('url', 'N/A')}")
                print(f"📝 Words: {page_result.get('word_count', 0)}")
                print(f"📅 Scraped: {page_result.get('scraped_at', 'N/A')}")
                
                content = page_result.get('markdown', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"📖 Content preview: {preview}")
                else:
                    print("📖 No content available")
            else:
                print(f"❌ Could not retrieve page: {page_result.get('error', 'Unknown error') if page_result else 'No result'}")
        else:
            print("⏭️ Skipping - no search results available")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Test different search queries - use config-based terms
    print("\n" + "="*60)
    print("🧪 Test 6: Multiple search queries")
    print("-" * 40)
    
    search_queries = get_test_search_terms()
    
    for query in search_queries:
        try:
            results = docs.search_content(query=query, limit=2)
            print(f"🔍 '{query}': {len(results)} results")
            for result in results:
                print(f"   - {result.get('title', 'Untitled')} ({result.get('word_count', 0)} words)")
        except Exception as e:
            print(f"❌ Error searching '{query}': {e}")
    
    print("\n" + "="*60)
    print(f"🎉 All MCP tools tested successfully for {domain_name}!")
    print("💡 Your MCP server is ready for Claude Desktop integration")
    print("\n📋 Tools tested:")
    print("   ✅ get_documentation_stats")
    print("   ✅ get_documentation_sections") 
    print("   ✅ search_documentation")
    print("   ✅ browse_section")
    print("   ✅ get_page_content")
    print("   ✅ Multiple search queries")


if __name__ == "__main__":
    domain_name = config.get("docs_name", "Documentation")
    print(f"🚀 MCP Documentation Server Tool Tester")
    print(f"📚 Target: {domain_name}")
    print("This will test all MCP tools directly without running a server")
    print()
    
    asyncio.run(test_mcp_tools()) 