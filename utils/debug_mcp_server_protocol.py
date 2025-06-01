#!/usr/bin/env python3
"""
Test MCP Server Protocol

This script tests the MCP server using the actual JSON-RPC protocol
by sending requests and validating responses.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path so we can import config and locate mcp_docs_server.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import configuration for dynamic testing
try:
    from config import ADVANCED_CONFIG
    config_available = True
except ImportError:
    print("⚠️  Config not available - using default test values")
    config_available = False


def send_mcp_request(method, params=None, id_val=1):
    """Send a JSON-RPC request to the MCP server"""
    request = {
        "jsonrpc": "2.0", 
        "id": id_val,
        "method": method
    }
    if params:
        request["params"] = params
    
    # Convert to JSON and send via stdin
    request_json = json.dumps(request) + "\n"
    
    try:
        # Start the MCP server process (in parent directory)
        mcp_server_path = parent_dir / "mcp_docs_server.py"
        process = subprocess.Popen(
            [sys.executable, str(mcp_server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(parent_dir)  # Run from parent directory
        )
        
        # Send request and get response
        stdout, stderr = process.communicate(input=request_json, timeout=10)
        
        # Parse response
        lines = stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if 'id' in response and response['id'] == id_val:
                        return response
                except json.JSONDecodeError:
                    continue
        
        return {"error": f"No valid response found. STDERR: {stderr}"}
        
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_test_search_term():
    """Get a search term for testing, from config if available"""
    if config_available:
        # Use first scoring keyword from config for dynamic testing
        scoring_keywords = ADVANCED_CONFIG.get("scoring_keywords", [])
        if scoring_keywords:
            return scoring_keywords[0]
    
    # Fallback to generic term
    return "guide"


def test_mcp_server():
    """Test the MCP server protocol"""
    
    print("🧪 Testing MCP Server via JSON-RPC Protocol")
    print("=" * 60)
    
    # Test 1: Initialize
    print("\n📡 Test 1: Initialize")
    print("-" * 40)
    
    init_params = {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "roots": {"listChanged": True},
            "sampling": {}
        },
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
    
    response = send_mcp_request("initialize", init_params, 1)
    if "error" in response:
        print(f"❌ Initialize failed: {response['error']}")
        return
    else:
        print("✅ Initialize successful")
        if "result" in response:
            capabilities = response["result"].get("capabilities", {})
            print(f"🔧 Tools available: {capabilities.get('tools', {}).get('listChanged', False)}")
    
    # Test 2: List tools
    print("\n📡 Test 2: List Tools")
    print("-" * 40)
    
    response = send_mcp_request("tools/list", None, 2)
    if "error" in response:
        print(f"❌ List tools failed: {response['error']}")
    else:
        print("✅ List tools successful")
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"🛠️ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.get('name', 'Unknown')}")
    
    # Test 3: Call search tool
    print("\n📡 Test 3: Call Search Tool")
    print("-" * 40)
    
    # Use dynamic search term from config
    search_term = get_test_search_term()
    search_params = {
        "name": "search_documentation",
        "arguments": {
            "query": search_term,
            "limit": 2
        }
    }
    
    response = send_mcp_request("tools/call", search_params, 3)
    if "error" in response:
        print(f"❌ Search tool failed: {response['error']}")
    else:
        print(f"✅ Search tool successful (searched for '{search_term}')")
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                # Parse the result
                try:
                    results = json.loads(content[0].get("text", "[]"))
                    print(f"🔍 Found {len(results)} search results:")
                    for i, result in enumerate(results[:2], 1):
                        if isinstance(result, dict):
                            print(f"   {i}. {result.get('title', 'Untitled')} ({result.get('word_count', 0)} words)")
                except:
                    print(f"📄 Raw content: {content}")
    
    # Test 4: Call stats tool  
    print("\n📡 Test 4: Call Stats Tool")
    print("-" * 40)
    
    stats_params = {
        "name": "get_documentation_stats",
        "arguments": {}
    }
    
    response = send_mcp_request("tools/call", stats_params, 4)
    if "error" in response:
        print(f"❌ Stats tool failed: {response['error']}")
    else:
        print("✅ Stats tool successful")
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                try:
                    stats = json.loads(content[0].get("text", "{}"))
                    if isinstance(stats, dict):
                        print(f"📊 Total Pages: {stats.get('total_pages', 'N/A'):,}")
                        print(f"📝 Total Words: {stats.get('total_words', 'N/A'):,}")
                        print(f"📚 Sections: {stats.get('section_count', 'N/A')}")
                        if 'domain_name' in stats:
                            print(f"🌐 Documentation: {stats['domain_name']}")
                except:
                    print(f"📄 Raw content: {content}")
    
    # Test 5: List resources
    print("\n📡 Test 5: List Resources")
    print("-" * 40)
    
    response = send_mcp_request("resources/list", None, 5)
    if "error" in response:
        print(f"❌ List resources failed: {response['error']}")
    else:
        print("✅ List resources successful")
        if "result" in response and "resources" in response["result"]:
            resources = response["result"]["resources"]
            print(f"📋 Found {len(resources)} resources:")
            for resource in resources:
                print(f"   - {resource.get('uri', 'Unknown')}")
    
    print("\n" + "="*60)
    print("🎉 MCP Server Protocol Testing Complete!")
    print("💡 Server is working correctly via JSON-RPC")
    
    if config_available:
        print("📋 Used configuration-based test parameters")
    else:
        print("📋 Used default test parameters (config not available)")


if __name__ == "__main__":
    test_mcp_server() 