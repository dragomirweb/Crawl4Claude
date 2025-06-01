#!/usr/bin/env python3
"""
Test script for the MCP Documentation Server

This script tests the MCP server functionality without requiring
a full MCP client connection. Useful for debugging and validation.

Usage:
    python utils/debug_mcp_server.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import configuration
try:
    from config import SCRAPER_CONFIG, MCP_CONFIG, ADVANCED_CONFIG
except ImportError as e:
    print("❌ Configuration file 'config.py' is required but not found.")
    print("Please ensure config.py exists in the root directory and contains the required configuration variables.")
    sys.exit(1)

try:
    from mcp_docs_server import DocumentationMCP, get_configuration
except ImportError as e:
    print(f"❌ Failed to import MCP server: {e}")
    print("Make sure mcp_docs_server.py is in the root directory")
    sys.exit(1)


def setup_test_environment():
    """Setup test environment using config values"""
    
    # Get configuration
    config = get_configuration()
    
    # Set environment variables for testing (override any existing ones)
    os.environ["DOCS_DB_PATH"] = config["db_path"]
    os.environ["DOCS_DB_NAME"] = config["docs_name"]
    os.environ["DOCS_BASE_URL"] = config["base_url"] or ""
    os.environ["MCP_SERVER_NAME"] = config["server_name"]
    
    return config


def test_documentation_mcp():
    """Test the DocumentationMCP class functionality"""
    
    # Setup test environment
    config = setup_test_environment()
    db_path = config["db_path"]
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Please run the scraper first: python docs_scraper.py")
        return False
    
    base_url = config["base_url"]
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0] if base_url else "Documentation"
    
    print(f"🧪 Testing MCP Documentation Server for {domain_name}")
    print("=" * 50)
    
    try:
        # Initialize the documentation handler
        docs = DocumentationMCP(
            db_path=db_path,
            docs_name=config["docs_name"],
            base_url=base_url if base_url else None
        )
        
        print("✅ DocumentationMCP initialized successfully")
        print(f"📊 Database: {db_path}")
        print(f"📚 Documentation: {config['docs_name']}")
        print(f"🌐 Base URL: {base_url or 'Not configured'}")
        print(f"🔍 FTS Available: {docs.has_fts}")
        
        # Test 1: Get stats
        print("\n🧪 Test 1: Get Statistics")
        stats = docs.get_stats()
        print(f"   📄 Total pages: {stats.get('total_pages', 0)}")
        print(f"   📝 Total words: {stats.get('total_words', 0):,}")
        print(f"   📚 Sections: {stats.get('section_count', 0)}")
        
        # Test 2: Get sections
        print("\n🧪 Test 2: Get Sections")
        sections = docs.get_sections()
        print(f"   Found {len(sections)} sections:")
        for section in sections[:5]:  # Show first 5
            print(f"   - {section['section']}: {section['page_count']} pages")
        
        # Test 3: Search content
        print("\n🧪 Test 3: Search Content")
        # Use domain-specific search terms from config
        search_keywords = ADVANCED_CONFIG.get("scoring_keywords", ["tutorial", "guide", "documentation"])
        search_term = search_keywords[0] if search_keywords else "guide"
        
        results = docs.search_content(search_term, limit=3)
        print(f"   Found {len(results)} results for '{search_term}':")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.get('title', 'Untitled')}")
            print(f"      Section: {result.get('section', 'N/A')}")
            print(f"      Words: {result.get('word_count', 0)}")
        
        # Test 4: Get page by URL
        print("\n🧪 Test 4: Get Page by URL")
        if results:
            url = results[0]['url']
            page = docs.get_page_by_url(url)
            if page:
                print(f"   ✅ Retrieved page: {page.get('title', 'Untitled')}")
                print(f"   📝 Content length: {len(page.get('markdown', ''))}")
            else:
                print(f"   ❌ Failed to retrieve page: {url}")
        
        # Test 5: Browse section
        print("\n🧪 Test 5: Browse Section")
        if sections:
            section_name = sections[0]['section']
            section_pages = docs.get_section_pages(section_name, limit=3)
            print(f"   📚 Pages in '{section_name}' section:")
            for page in section_pages:
                print(f"   - {page.get('title', 'Untitled')} ({page.get('word_count', 0)} words)")
        
        # Test 6: Configuration limits
        print("\n🧪 Test 6: Configuration Limits")
        print(f"   Search limit: {docs.search_limit} (max: {docs.max_search_limit})")
        print(f"   Section limit: {docs.section_limit} (max: {docs.max_section_limit})")
        print(f"   Snippet length: {docs.snippet_length} words")
        print(f"   FTS fallback: {docs.enable_fts_fallback}")
        
        print("\n✅ All tests passed! MCP server is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_tools():
    """Test the MCP tools interface"""
    
    print("\n🧪 Testing MCP Tools Interface")
    print("=" * 50)
    
    try:
        from mcp_docs_server import create_mcp_server
        
        print("✅ MCP server creation function available")
        
        # Test configuration loading
        config = get_configuration()
        print(f"✅ Configuration loaded successfully")
        print(f"   Server name: {config['server_name']}")
        print(f"   Database: {config['db_path']}")
        
        # Test MCP config values
        server_description = MCP_CONFIG.get("server_description", "Documentation Server")
        default_search_limit = MCP_CONFIG.get("default_search_limit", 10)
        print(f"   Description: {server_description}")
        print(f"   Default search limit: {default_search_limit}")
        
        print("💡 To fully test MCP tools, run the server and connect with an MCP client")
        print(f"💡 Start server with: python mcp_docs_server.py")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_mcp_config_example():
    """Show example MCP configuration for Claude Desktop"""
    
    config = get_configuration()
    base_url = config["base_url"]
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0] if base_url else "docs"
    
    print("\n📋 MCP Configuration Example for Claude Desktop:")
    print("=" * 50)
    
    mcp_config = {
        "mcpServers": {
            f"{domain_name.replace('.', '_')}_docs": {
                "command": "python",
                "args": [str(Path("mcp_docs_server.py").resolve())],
                "env": {
                    "DOCS_DB_PATH": config["db_path"],
                    "DOCS_DB_NAME": config["docs_name"],
                    "DOCS_BASE_URL": config["base_url"] or "",
                    "MCP_SERVER_NAME": config["server_name"]
                }
            }
        }
    }
    
    import json
    print(json.dumps(mcp_config, indent=2))


if __name__ == "__main__":
    # Get configuration for display
    try:
        config = get_configuration()
        base_url = config["base_url"]
        domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0] if base_url else "Documentation"
    except:
        domain_name = "Documentation"
    
    print(f"🚀 MCP Documentation Server Test Suite")
    print(f"📚 Target: {domain_name}")
    print("This will test the MCP server functionality locally")
    print()
    
    # Test the core functionality
    core_test = test_documentation_mcp()
    
    # Test the MCP interface
    mcp_test = test_mcp_tools()
    
    # Show configuration example
    if core_test and mcp_test:
        show_mcp_config_example()
    
    print("\n" + "=" * 50)
    if core_test and mcp_test:
        print("🎉 All tests passed! Your MCP server is ready to use.")
        print("\n📋 Next steps:")
        print("1. Ensure FastMCP is installed: pip install fastmcp")
        print("2. Run the server: python mcp_docs_server.py")
        print("3. Add the configuration above to your Claude Desktop config")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1) 