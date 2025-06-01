#!/usr/bin/env python3
"""
Debug version of MCP Documentation Server with enhanced logging
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Add debug logging
def debug_log(message):
    print(f"[DEBUG] {message}", file=sys.stderr, flush=True)

debug_log("=== MCP Documentation Server Debug Start ===")
debug_log(f"Python executable: {sys.executable}")
debug_log(f"Python version: {sys.version}")
debug_log(f"Current working directory: {os.getcwd()}")
debug_log(f"Script location: {__file__}")
debug_log(f"Parent directory: {parent_dir}")

# Import and get configuration
try:
    from config import SCRAPER_CONFIG, MCP_CONFIG, get_mcp_server_config
    debug_log("✅ Configuration loaded successfully")
    
    # Get configuration values
    base_url = SCRAPER_CONFIG.get("base_url", "")
    output_dir = SCRAPER_CONFIG.get("output_dir", "docs_db")
    
    # Get complete MCP configuration
    config = get_mcp_server_config()
    
    # Derive domain name for display
    domain_name = config["docs_name"]
    
    debug_log(f"Target documentation: {domain_name}")
    debug_log(f"Base URL: {base_url}")
    debug_log(f"Output directory: {output_dir}")
    
except ImportError as e:
    debug_log(f"❌ Configuration import failed: {e}")
    debug_log("Please ensure config.py exists in the parent directory")
    sys.exit(1)

# Get derived configuration values
db_path = config["db_path"]
docs_name = config["docs_name"]
server_name = config["server_name"]

debug_log(f"Database path: {db_path}")
debug_log(f"Documentation name: {docs_name}")
debug_log(f"Server name: {server_name}")

# Check environment variables (show both config and env values)
debug_log("Environment variables:")
env_vars = {
    "DOCS_DB_PATH": db_path,
    "DOCS_DB_NAME": docs_name,
    "DOCS_BASE_URL": base_url,
    "MCP_SERVER_NAME": server_name
}

for key, config_value in env_vars.items():
    env_value = os.getenv(key, "NOT_SET")
    debug_log(f"  {key}: {env_value} (config: {config_value})")

# Check database file
debug_log(f"Database path (resolved): {os.path.abspath(db_path)}")
debug_log(f"Database exists: {Path(db_path).exists()}")

if not Path(db_path).exists():
    debug_log("⚠️  Database not found! Run the scraper first:")
    debug_log("   python docs_scraper.py")

# Try to import dependencies
try:
    import fastmcp
    debug_log(f"✅ FastMCP version: {fastmcp.__version__ if hasattr(fastmcp, '__version__') else 'Unknown'}")
except ImportError as e:
    debug_log(f"❌ FastMCP import failed: {e}")
    debug_log("Install with: pip install fastmcp")
    sys.exit(1)

try:
    import sqlite3
    debug_log("✅ SQLite3 available")
    
    # Test database connection if it exists
    if Path(db_path).exists():
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM pages")
                page_count = cursor.fetchone()[0]
                debug_log(f"✅ Database connection successful: {page_count} pages found")
        except Exception as e:
            debug_log(f"❌ Database connection failed: {e}")
    
except ImportError as e:
    debug_log(f"❌ SQLite3 import failed: {e}")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    debug_log("✅ python-dotenv available")
    if Path(".env").exists():
        load_dotenv()
        debug_log("✅ Loaded .env file")
except ImportError:
    debug_log("⚠️  python-dotenv not available (optional)")

# Show MCP configuration
debug_log("MCP Configuration:")
debug_log(f"  Server description: {MCP_CONFIG.get('server_description', 'Documentation Server')}")
debug_log(f"  Default search limit: {MCP_CONFIG.get('default_search_limit', 10)}")
debug_log(f"  Max search limit: {MCP_CONFIG.get('max_search_limit', 50)}")
debug_log(f"  Enable FTS fallback: {MCP_CONFIG.get('enable_fts_fallback', True)}")

debug_log("=== Starting MCP Documentation Server ===")

# Import and run the actual server
try:
    from mcp_docs_server import create_mcp_server
    debug_log("✅ Successfully imported MCP server")
    
    mcp = create_mcp_server()
    debug_log("✅ MCP server created successfully")
    debug_log(f"🚀 Starting MCP server for {domain_name}...")
    
    mcp.run()
    
except Exception as e:
    debug_log(f"❌ ERROR: {e}")
    import traceback
    debug_log(f"Traceback: {traceback.format_exc()}")
    sys.exit(1) 