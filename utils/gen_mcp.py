#!/usr/bin/env python3
"""
MCP Configuration Generator

This script generates the necessary files for setting up the MCP server with Claude Desktop:
1. run_mcp_server.bat - Windows batch file to launch the MCP server
2. claude_mcp_config.json - Claude Desktop configuration file

Usage:
    python utils/gen_mcp.py
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import configuration
try:
    from config import get_mcp_server_config
    config = get_mcp_server_config()
    print(f"✅ Configuration loaded for {config['docs_name']}")
except ImportError as e:
    print(f"❌ Configuration import failed: {e}")
    print("Please ensure config.py exists in the parent directory")
    sys.exit(1)


def get_absolute_paths():
    """Get absolute paths for the current project"""
    # Get the absolute path of the project root (parent of utils/)
    project_root = parent_dir.resolve()
    
    # Generate paths
    paths = {
        "project_root": str(project_root),
        "database_path": str(project_root / config["db_path"]),
        "mcp_server_script": str(project_root / "mcp_docs_server.py"),
        "debug_server_script": str(project_root / "utils" / "debug_mcp_docs_server.py"),
        "mcp_dir": str(project_root / "mcp"),
        "batch_file": str(project_root / "mcp" / "run_mcp_server.bat"),
        "config_file": str(project_root / "mcp" / "claude_mcp_config.json"),
    }
    
    return paths


def generate_batch_file(paths):
    """Generate the Windows batch file for running the MCP server"""
    
    # Create mcp directory if it doesn't exist
    mcp_dir = Path(paths["mcp_dir"])
    mcp_dir.mkdir(exist_ok=True)
    
    # Determine which server script to use
    server_script = "mcp_docs_server.py"
    if not Path(paths["mcp_server_script"]).exists():
        print("⚠️  Main MCP server not found, using debug version")
        server_script = "utils\\debug_mcp_docs_server.py"
    
    batch_content = f'''@echo off

REM MCP Documentation Server Launcher
REM Generated automatically from config.py

cd /d "{paths['project_root']}"

REM Set environment variables from config
set DOCS_DB_PATH={paths['database_path']}
set DOCS_DB_NAME={config['docs_name']}
set DOCS_BASE_URL={config['base_url']}
set MCP_SERVER_NAME={config['server_name']}

echo [DEBUG] Working directory: %CD% 1>&2
echo [DEBUG] Target documentation: {config['docs_name']} 1>&2
echo [DEBUG] Database path: %DOCS_DB_PATH% 1>&2
echo [DEBUG] Base URL: %DOCS_BASE_URL% 1>&2

REM Check if database exists
if not exist "%DOCS_DB_PATH%" (
    echo [ERROR] Database not found at: %DOCS_DB_PATH% 1>&2
    echo [ERROR] Please run the scraper first: python docs_scraper.py 1>&2
    exit /b 1
)

REM Auto-detect Python
set "PYTHON_EXE=python"
if exist "%USERPROFILE%\\miniconda3\\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\\miniconda3\\python.exe"
    echo [DEBUG] Using conda Python: %PYTHON_EXE% 1>&2
) else if exist "%USERPROFILE%\\anaconda3\\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\\anaconda3\\python.exe"
    echo [DEBUG] Using conda Python: %PYTHON_EXE% 1>&2
) else (
    echo [DEBUG] Using system Python 1>&2
)

REM Check Python availability
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python. 1>&2
    exit /b 1
)

REM Install dependencies if needed
echo [DEBUG] Checking dependencies... 1>&2
"%PYTHON_EXE%" -c "import fastmcp" 2>nul || (
    echo [INFO] Installing FastMCP... 1>&2
    "%PYTHON_EXE%" -m pip install fastmcp
)

"%PYTHON_EXE%" -c "import sqlite3" 2>nul || (
    echo [ERROR] SQLite3 not available 1>&2
    exit /b 1
)

REM Run the MCP server
echo [DEBUG] Starting MCP Documentation Server for {config['docs_name']}... 1>&2
"%PYTHON_EXE%" {server_script}
'''
    
    batch_file_path = Path(paths["batch_file"])
    with open(batch_file_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Generated batch file: {batch_file_path}")
    return batch_file_path


def generate_claude_config(paths):
    """Generate the Claude Desktop MCP configuration file"""
    
    # No need to manually escape - json.dump() handles backslash escaping automatically
    batch_path = paths["batch_file"]
    project_root = paths["project_root"]
    database_path = paths["database_path"]
    
    # Create server name from domain (replace dots with underscores for valid JSON key)
    server_key = config['docs_name'].lower().replace(" ", "_").replace(".", "_").replace("-", "_")
    
    claude_config = {
        "mcpServers": {
            server_key: {
                "command": batch_path,
                "args": [],
                "cwd": project_root,
                "env": {
                    "DOCS_DB_PATH": database_path,
                    "DOCS_DB_NAME": config["docs_name"],
                    "DOCS_BASE_URL": config["base_url"],
                    "MCP_SERVER_NAME": config["server_name"]
                }
            }
        }
    }
    
    config_file_path = Path(paths["config_file"])
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(claude_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated Claude config: {config_file_path}")
    return config_file_path


def display_setup_instructions(paths):
    """Display setup instructions for the user"""
    print("\n" + "="*60)
    print("🎉 MCP Configuration Files Generated Successfully!")
    print("="*60)
    
    print(f"\n📁 Files created:")
    print(f"   • {paths['batch_file']}")
    print(f"   • {paths['config_file']}")
    
    print(f"\n🚀 Setup Instructions:")
    print(f"   1. Copy the contents of {paths['config_file']}")
    print(f"   2. Add it to your Claude Desktop configuration:")
    print(f"      - Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print(f"      - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print(f"   3. Restart Claude Desktop")
    
    print(f"\n📋 Configuration Summary:")
    print(f"   • Documentation: {config['docs_name']}")
    print(f"   • Database: {paths['database_path']}")
    print(f"   • Base URL: {config['base_url']}")
    print(f"   • Server Name: {config['server_name']}")
    
    print(f"\n💡 Troubleshooting:")
    print(f"   • Test batch file: {paths['batch_file']}")
    print(f"   • Check database exists: {paths['database_path']}")
    print(f"   • Run scraper if needed: python docs_scraper.py")
    
    print(f"\n🔗 Claude Desktop Configuration Preview:")
    with open(paths['config_file'], 'r', encoding='utf-8') as f:
        config_content = f.read()
    print(config_content)


def main():
    """Main function to generate MCP configuration files"""
    
    print(f"🔧 MCP Configuration Generator")
    print(f"📚 Target: {config['docs_name']}")
    print(f"🌐 Base URL: {config['base_url']}")
    print("="*50)
    
    # Get absolute paths
    paths = get_absolute_paths()
    
    # Check if database exists
    db_path = Path(paths["database_path"])
    if not db_path.exists():
        print(f"⚠️  Database not found: {db_path}")
        print(f"💡 Run the scraper first: python docs_scraper.py")
        print(f"💡 Continuing with config generation...")
    else:
        print(f"✅ Database found: {db_path}")
    
    # Generate files
    try:
        batch_file = generate_batch_file(paths)
        config_file = generate_claude_config(paths)
        
        # Display instructions
        display_setup_instructions(paths)
        
    except Exception as e:
        print(f"❌ Error generating files: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
