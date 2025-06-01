# MCP Documentation Server

A **Model Context Protocol (MCP) server** that provides AI agents with real-time, searchable access to any documentation database. This server is **completely domain-agnostic** and automatically integrates with Claude Desktop through our configuration-driven setup.

## 🚀 Features

- **🌐 Universal Documentation Access**: Works with any scraped documentation site
- **🔍 Full-text Search**: Fast FTS5 search with highlighting and snippets
- **📚 Section Browsing**: Organized access to documentation sections
- **📄 Complete Page Retrieval**: Full content access with metadata
- **⚙️ Configuration-Driven**: Single config file controls everything
- **🔧 Auto-Setup**: Automatic Claude Desktop configuration generation
- **⚡ High Performance**: Optimized SQLite database with indexing
- **🛠️ Debug Suite**: Comprehensive testing and validation tools

## 🛠️ Quick Setup

### 1. Configure Your Documentation

Edit `config.py` to set your target documentation:

```python
SCRAPER_CONFIG = {
    "base_url": "https://docs.example.com/",
    "output_dir": "docs_db",
    "max_pages": 200,
}

MCP_CONFIG = {
    "server_name": "docs-server",
    "server_description": "Documentation Search Server",
    "default_search_limit": 10,
    "max_search_limit": 50,
}
```

### 2. Scrape Your Documentation

```bash
# Scrape the documentation site
python docs_scraper.py

# Verify the database was created
python query_docs.py --stats
```

### 3. Generate MCP Configuration

```bash
# Auto-generate Claude Desktop config files
python utils/gen_mcp.py
```

### 4. Test the MCP Server

```bash
# Test server functionality
python utils/debug_mcp_server.py

# Test MCP tools directly  
python utils/debug_mcp_client.py

# Test MCP protocol
python utils/debug_mcp_server_protocol.py
```

### 5. Connect to Claude Desktop

1. **Copy the generated configuration** from `mcp/claude_mcp_config.json`
2. **Add it to Claude Desktop config**:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. **Restart Claude Desktop**

## 🔌 Claude Desktop Integration

### Automatic Configuration

Our `gen_mcp.py` tool creates everything you need:

```bash
python utils/gen_mcp.py
```

**Generated files:**
- `mcp/run_mcp_server.bat` - Windows launcher script
- `mcp/claude_mcp_config.json` - Claude Desktop configuration

**Example generated config:**
```json
{
  "mcpServers": {
    "docs_example_com": {
      "command": "C:\\path\\to\\mcp\\run_mcp_server.bat",
      "args": [],
      "cwd": "C:\\path\\to\\project",
      "env": {
        "DOCS_DB_PATH": "C:\\path\\to\\docs_db\\documentation.db",
        "DOCS_DB_NAME": "docs.example.com",
        "DOCS_BASE_URL": "https://docs.example.com/",
        "MCP_SERVER_NAME": "docs-server"
      }
    }
  }
}
```

### Manual Configuration

If you prefer manual setup:

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": ["mcp_docs_server.py"],
      "cwd": "/path/to/project",
      "env": {
        "DOCS_DB_PATH": "/path/to/docs_db/documentation.db",
        "DOCS_DB_NAME": "Your Documentation",
        "DOCS_BASE_URL": "https://docs.yoursite.com/"
      }
    }
  }
}
```

## 🧰 Available MCP Tools

Once connected, Claude can use these tools:

### 🔍 `search_documentation`
Search through documentation content with full-text search.

```javascript
// Search with basic query
search_documentation({
    query: "authentication guide",
    limit: 10
})

// Search within specific section
search_documentation({
    query: "API endpoints", 
    limit: 5,
    section: "api-reference"
})
```

**Returns:** Array of pages with title, URL, section, word count, and highlighted snippets.

### 📚 `get_documentation_sections`
Get all available sections with statistics.

```javascript
get_documentation_sections()
```

**Returns:** `[{"section": "tutorials", "page_count": 45, "total_words": 18500}, ...]`

### 📄 `get_page_content`
Retrieve the full content of a specific page.

```javascript
get_page_content({
    url: "https://docs.example.com/tutorials/getting-started"
})
```

**Returns:** Complete page with title, markdown content, section, word count, and metadata.

### 🗂️ `browse_section`
Browse all pages in a specific section.

```javascript
browse_section({
    section: "tutorials",
    limit: 20
})
```

**Returns:** Array of pages in the section, ordered by relevance.

### 📊 `get_documentation_stats`
Get overall database statistics and server info.

```javascript
get_documentation_stats()
```

**Returns:** Total pages, words, sections, top sections, and server configuration.

## 🌐 Multi-Site Examples

### Python Documentation
```python
# config.py
SCRAPER_CONFIG = {
    "base_url": "https://docs.python.org/3/",
    "output_dir": "python_docs",
    "max_pages": 1000,
}

MCP_CONFIG = {
    "server_name": "python-docs-server",
    "docs_display_name": "Python 3 Documentation",
}
```

### React Documentation  
```python
# config.py
SCRAPER_CONFIG = {
    "base_url": "https://react.dev/",
    "output_dir": "react_docs", 
    "max_pages": 300,
}

MCP_CONFIG = {
    "server_name": "react-docs-server",
    "docs_display_name": "React Documentation",
}
```

### Corporate Documentation
```python
# config.py
SCRAPER_CONFIG = {
    "base_url": "https://internal-docs.company.com/",
    "output_dir": "company_docs",
    "max_pages": 500,
}

MCP_CONFIG = {
    "server_name": "company-docs-server", 
    "docs_display_name": "Company Internal Docs",
}
```

## 🔧 Command Line Interface

### Run MCP Server Directly
```bash
# Start the MCP server
python mcp_docs_server.py

# With debug output
python utils/debug_mcp_docs_server.py
```

### Query Documentation Locally
```bash
# Search documentation
python query_docs.py --search "tutorial example"

# Browse sections
python query_docs.py --section "getting-started"

# Get statistics  
python query_docs.py --stats

# Export sections
python query_docs.py --export-section "api" --format markdown > api_docs.md
```

## 🧪 Testing & Debugging

### Comprehensive Test Suite

```bash
# Test scraper functionality (5-page test)
python utils/debug_scraper.py

# Test MCP server locally
python utils/debug_mcp_server.py

# Test all MCP tools directly
python utils/debug_mcp_client.py

# Test MCP JSON-RPC protocol
python utils/debug_mcp_server_protocol.py

# Test content extraction 
python utils/debug_site_content.py

# Generate/regenerate MCP configs
python utils/gen_mcp.py
```

### Debugging Checklist

**✅ Scraper Issues:**
- Database exists: `ls docs_db/documentation.db`
- Database has content: `python query_docs.py --stats`
- Test scraping: `python utils/debug_scraper.py`

**✅ MCP Server Issues:**
- Configuration valid: `python utils/debug_mcp_server.py`  
- Tools working: `python utils/debug_mcp_client.py`
- Protocol working: `python utils/debug_mcp_server_protocol.py`

**✅ Claude Connection Issues:**
- Config file syntax valid
- Paths are absolute and correct
- Server starts without errors
- Environment variables set correctly

## 🔍 Example Claude Interactions

Once connected, you can ask Claude:

### Documentation Search
> **User:** "Search for authentication examples in the documentation"
> 
> **Claude:** *Uses `search_documentation` to find auth-related content*

### Section Exploration  
> **User:** "What sections are available in this documentation?"
>
> **Claude:** *Uses `get_documentation_sections` to list all sections*

### Deep Content Access
> **User:** "Show me the full content of the getting started guide"
>
> **Claude:** *Uses `search_documentation` to find the guide, then `get_page_content` to get full text*

### Section Analysis
> **User:** "How many tutorial pages are there and what do they cover?"
>
> **Claude:** *Uses `browse_section` to analyze the tutorials section*

### Documentation Overview
> **User:** "Give me an overview of this documentation database"
>
> **Claude:** *Uses `get_documentation_stats` to provide comprehensive statistics*

## 📊 Database Schema

The MCP server works with any documentation database following this schema:

```sql
-- Main content table
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,        -- Raw HTML content
    markdown TEXT,       -- Clean markdown content  
    word_count INTEGER,
    section TEXT,        -- Main section (e.g., "tutorials")
    subsection TEXT,     -- Subsection (e.g., "advanced")
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT        -- JSON metadata
);

-- Full-text search (optional but recommended)
CREATE VIRTUAL TABLE pages_fts USING fts5(
    title, markdown, url, section,
    content='pages',
    content_rowid='id'
);

-- Indexes for performance
CREATE INDEX idx_pages_section ON pages(section);
CREATE INDEX idx_pages_url ON pages(url);
```

## 🚀 Multiple Documentation Servers

Run multiple MCP servers for different documentation sets:

```json
{
  "mcpServers": {
    "python_docs": {
      "command": "C:\\path\\to\\python_mcp\\run_mcp_server.bat",
      "cwd": "C:\\path\\to\\python_project"
    },
    "react_docs": {
      "command": "C:\\path\\to\\react_mcp\\run_mcp_server.bat", 
      "cwd": "C:\\path\\to\\react_project"
    },
    "company_docs": {
      "command": "C:\\path\\to\\company_mcp\\run_mcp_server.bat",
      "cwd": "C:\\path\\to\\company_project"
    }
  }
}
```

Each server operates independently with its own configuration and database.

## ⚙️ Configuration Reference

### Environment Variables (Optional Overrides)

```bash
# Override database path
DOCS_DB_PATH=/custom/path/documentation.db

# Override display name
DOCS_DB_NAME="Custom Documentation Name"

# Override base URL
DOCS_BASE_URL=https://different-docs.com/

# Override server name
MCP_SERVER_NAME=custom-docs-server
```

### Config.py Settings

```python
MCP_CONFIG = {
    # Server identification
    "server_name": "docs-server",
    "server_description": "Documentation Search and Retrieval Server",
    
    # Display name (None = auto-derive from base_url)
    "docs_display_name": None,
    
    # Search limits
    "default_search_limit": 10,
    "max_search_limit": 50,
    "default_section_limit": 20,
    "max_section_limit": 100,
    
    # Content settings
    "include_full_urls": True,
    "snippet_length": 32,
    "enable_fts_fallback": True,
}
```

## 🔧 Troubleshooting

### Common Issues

**❌ "Database not found"**
```bash
# Check if database exists
ls docs_db/documentation.db

# Re-run scraper if missing
python docs_scraper.py
```

**❌ "No search results"**
```bash
# Test database content
python query_docs.py --stats

# Test search functionality
python utils/debug_mcp_client.py
```

**❌ "Claude can't connect"**
```bash
# Test MCP protocol
python utils/debug_mcp_server_protocol.py

# Check config syntax
python -m json.tool mcp/claude_mcp_config.json
```

**❌ "Import errors"**
```bash
# Install dependencies
pip install -r requirements.txt

# Test imports
python -c "import fastmcp; print('FastMCP OK')"
```

### Debug Logs

Check logs for detailed error information:
```bash
# Scraper logs
tail -f docs_db/scraper.log

# MCP server logs (stderr)
python utils/debug_mcp_docs_server.py 2> mcp_debug.log
```

## 📝 Contributing

Areas for enhancement:
- **Additional export formats** (PDF, EPUB)
- **Enhanced search algorithms** (semantic search, relevance scoring)  
- **Real-time documentation updates** (webhook integration)
- **Multi-language support** (internationalized documentation)
- **Performance optimizations** (caching, connection pooling)

## 📄 License

This MCP server is designed to be universally reusable. Adapt and extend it for any documentation project while respecting the original documentation sources' licenses.

---

**🤖 Ready to enhance your AI workflows with comprehensive documentation access!**

For support, check the debug tools first, then create an issue with relevant logs and configuration details. 