# Documentation Scraper & MCP Server

A comprehensive, domain-agnostic documentation scraping and AI integration toolkit. Scrape any documentation website, create structured databases, and integrate with Claude Desktop via MCP (Model Context Protocol) for seamless AI-powered documentation assistance.

## 🚀 Features

### Core Functionality
- **🌐 Universal Documentation Scraper**: Works with any documentation website
- **📊 Structured Database**: SQLite database with full-text search capabilities  
- **🤖 MCP Server Integration**: Native Claude Desktop integration via Model Context Protocol
- **📝 LLM-Optimized Output**: Ready-to-use context files for AI applications
- **⚙️ Configuration-Driven**: Single config file controls all settings

### Advanced Tools
- **🔍 Query Interface**: Command-line tool for searching and analyzing scraped content
- **🛠️ Debug Suite**: Comprehensive debugging tools for testing and validation
- **📋 Auto-Configuration**: Automatic MCP setup file generation
- **📈 Progress Tracking**: Detailed logging and error handling
- **💾 Resumable Crawls**: Smart caching for interrupted crawls

## 📋 Prerequisites

- Python 3.8 or higher
- Internet connection
- ~500MB free disk space per documentation site

## 🛠️ Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd documentation-scraper

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Target

Edit `config.py` to set your documentation site:

```python
SCRAPER_CONFIG = {
    "base_url": "https://docs.example.com/",  # Your documentation site
    "output_dir": "docs_db",
    "max_pages": 200,
    # ... other settings
}
```

### 3. Run the Scraper

```bash
python docs_scraper.py
```

### 4. Query Your Documentation

```bash
# Search for content
python query_docs.py --search "tutorial"

# Browse by section
python query_docs.py --section "getting-started"

# Get statistics
python query_docs.py --stats
```

### 5. Set Up Claude Integration

```bash
# Generate MCP configuration files
python utils/gen_mcp.py

# Follow the instructions to add to Claude Desktop
```

## 🏗️ Project Structure

```
📁 documentation-scraper/
├── 📄 config.py                    # Central configuration file
├── 🕷️ docs_scraper.py              # Main scraper script
├── 🔍 query_docs.py                # Query and analysis tool
├── 🤖 mcp_docs_server.py           # MCP server for Claude integration
├── 📋 requirements.txt             # Python dependencies
├── 📁 utils/                       # Debug and utility tools
│   ├── 🛠️ gen_mcp.py               # Generate MCP config files
│   ├── 🧪 debug_scraper.py         # Test scraper functionality
│   ├── 🔧 debug_mcp_server.py      # Debug MCP server
│   ├── 🎯 debug_mcp_client.py      # Test MCP tools directly
│   ├── 📡 debug_mcp_server_protocol.py # Test MCP via JSON-RPC
│   └── 🌐 debug_site_content.py    # Debug content extraction
├── 📁 docs_db/                     # Generated documentation database
│   ├── 📊 documentation.db         # SQLite database
│   ├── 📄 documentation.json       # JSON export
│   ├── 📋 scrape_summary.json      # Statistics
│   └── 📁 llm_context/             # LLM-ready context files
└── 📁 mcp/                         # Generated MCP configuration
    ├── 🔧 run_mcp_server.bat       # Windows launcher script
    └── ⚙️ claude_mcp_config.json   # Claude Desktop config
```

## ⚙️ Configuration

### Main Configuration (`config.py`)

The entire system is controlled by a single configuration file:

```python
# Basic scraping settings
SCRAPER_CONFIG = {
    "base_url": "https://docs.example.com/",
    "output_dir": "docs_db",
    "max_depth": 3,
    "max_pages": 200,
    "delay_between_requests": 0.5,
}

# URL filtering rules
URL_FILTER_CONFIG = {
    "skip_patterns": [r'/api/', r'\.pdf$'],
    "allowed_domains": ["docs.example.com"],
}

# MCP server settings
MCP_CONFIG = {
    "server_name": "docs-server",
    "default_search_limit": 10,
    "max_search_limit": 50,
}
```

### Environment Overrides

You can override any setting with environment variables:

```bash
export DOCS_DB_PATH="/custom/path/documentation.db"
export DOCS_BASE_URL="https://different-docs.com/"
python mcp_docs_server.py
```

## 🤖 Claude Desktop Integration

### Automatic Setup

1. **Generate configuration files**:
   ```bash
   python utils/gen_mcp.py
   ```

2. **Copy the generated config** to Claude Desktop:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. **Restart Claude Desktop**

### Manual Setup

If you prefer manual setup, add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": ["path/to/mcp_docs_server.py"],
      "cwd": "path/to/project",
      "env": {
        "DOCS_DB_PATH": "path/to/docs_db/documentation.db"
      }
    }
  }
}
```

### Available MCP Tools

Once connected, Claude can use these tools:

- **🔍 search_documentation**: Search for content across all documentation
- **📚 get_documentation_sections**: List all available sections  
- **📄 get_page_content**: Get full content of specific pages
- **🗂️ browse_section**: Browse pages within a section
- **📊 get_documentation_stats**: Get database statistics

## 🔧 Command Line Tools

### Documentation Scraper

```bash
# Basic scraping
python docs_scraper.py

# Override config settings
python docs_scraper.py  # Settings from config.py
```

### Query Tool

```bash
# Search for content
python query_docs.py --search "authentication guide"

# Browse specific sections  
python query_docs.py --section "api-reference"

# Get database statistics
python query_docs.py --stats

# List all sections
python query_docs.py --list-sections

# Export section to file
python query_docs.py --export-section "tutorials" --format markdown > tutorials.md

# Use custom database
python query_docs.py --db "custom/path/docs.db" --search "example"
```

### Debug Tools

```bash
# Test scraper functionality
python utils/debug_scraper.py

# Test MCP server
python utils/debug_mcp_server.py

# Test MCP tools directly
python utils/debug_mcp_client.py

# Test MCP protocol
python utils/debug_mcp_server_protocol.py

# Debug content extraction
python utils/debug_site_content.py

# Generate MCP config files
python utils/gen_mcp.py
```

## 📊 Database Schema

### Pages Table
```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    markdown TEXT,
    word_count INTEGER,
    section TEXT,
    subsection TEXT,
    scraped_at TIMESTAMP,
    metadata TEXT
);
```

### Full-Text Search
```sql
-- Search using FTS5
SELECT * FROM pages_fts WHERE pages_fts MATCH 'your search term';

-- Or use the query tool
python query_docs.py --search "your search term"
```

## 🎯 Example Use Cases

### 1. Documentation Analysis
```bash
# Get overview of documentation
python query_docs.py --stats

# Find all tutorial content
python query_docs.py --search "tutorial guide example"

# Export specific sections
python query_docs.py --export-section "getting-started" > onboarding.md
```

### 2. AI Integration with Claude
```python
# Once MCP is set up, ask Claude:
# "Search the documentation for authentication examples"
# "What sections are available in the documentation?"
# "Show me the content for the API reference page"
```

### 3. Custom Applications
```python
import sqlite3

# Connect to your scraped documentation
conn = sqlite3.connect('docs_db/documentation.db')

# Query for specific content
results = conn.execute("""
    SELECT title, url, markdown 
    FROM pages 
    WHERE section = 'tutorials' 
    AND word_count > 500
    ORDER BY word_count DESC
""").fetchall()

# Build your own tools on top of the structured data
```

## 🔍 Debugging and Testing

### Test Scraper Before Full Run
```bash
python utils/debug_scraper.py
```

### Validate Content Extraction  
```bash
python utils/debug_site_content.py
```

### Test MCP Integration
```bash
# Test server functionality
python utils/debug_mcp_server.py

# Test tools directly
python utils/debug_mcp_client.py

# Test JSON-RPC protocol
python utils/debug_mcp_server_protocol.py
```

## 📈 Performance and Optimization

### Scraping Performance
- **Start small**: Use `max_pages=50` for testing
- **Adjust depth**: `max_depth=2` covers most content efficiently  
- **Rate limiting**: Increase `delay_between_requests` if getting blocked
- **Caching**: Enabled by default for resumable crawls

### Database Performance
- **Full-text search**: Automatic FTS5 index for fast searching
- **Indexing**: Optimized indexes on URL and section columns
- **Word counts**: Pre-calculated for quick statistics

### MCP Performance  
- **Configurable limits**: Set appropriate search and section limits
- **Snippet length**: Adjust snippet size for optimal response times
- **Connection pooling**: Efficient database connections

## 🌐 Supported Documentation Sites

This scraper works with most documentation websites including:

- **Static sites**: Hugo, Jekyll, MkDocs, Docusaurus
- **Documentation platforms**: GitBook, Notion, Confluence  
- **API docs**: Swagger/OpenAPI documentation
- **Wiki-style**: MediaWiki, TiddlyWiki
- **Custom sites**: Any site with consistent HTML structure

### Site-Specific Configuration

Customize URL filtering and content extraction for your target site:

```python
URL_FILTER_CONFIG = {
    "skip_patterns": [
        r'/api/',           # Skip API endpoint docs
        r'/edit/',          # Skip edit pages  
        r'\.pdf$',          # Skip PDF files
    ],
    "allowed_domains": ["docs.yoursite.com"],
}

CONTENT_FILTER_CONFIG = {
    "remove_patterns": [
        r'Edit this page.*?\n',      # Remove edit links
        r'Was this helpful\?.*?\n',  # Remove feedback sections
    ],
}
```

## 🤝 Contributing

We welcome contributions! Here are some areas where you can help:

- **New export formats**: PDF, EPUB, Word documents
- **Enhanced content filtering**: Better noise removal
- **Additional debug tools**: More comprehensive testing
- **Documentation**: Improve guides and examples
- **Performance optimizations**: Faster scraping and querying

## ⚠️ Responsible Usage

- **Respect robots.txt**: Check the target site's robots.txt file
- **Rate limiting**: Use appropriate delays between requests
- **Terms of service**: Respect the documentation site's terms
- **Fair use**: Use for educational, research, or personal purposes
- **Attribution**: Credit the original documentation source

## 📄 License

This project is provided as-is for educational and research purposes. Please respect the terms of service and licensing of the documentation sites you scrape.

---

## 🎉 Getting Started Examples

### Example 1: Scrape Python Documentation
```python
# config.py
SCRAPER_CONFIG = {
    "base_url": "https://docs.python.org/3/",
    "max_pages": 500,
    "max_depth": 3,
}
```

### Example 2: Scrape API Documentation
```python
# config.py  
SCRAPER_CONFIG = {
    "base_url": "https://api-docs.example.com/",
    "max_pages": 200,
}

URL_FILTER_CONFIG = {
    "skip_patterns": [r'/changelog/', r'/releases/'],
}
```

### Example 3: Corporate Documentation
```python
# config.py
SCRAPER_CONFIG = {
    "base_url": "https://internal-docs.company.com/",
    "output_dir": "company_docs",
}

MCP_CONFIG = {
    "server_name": "company-docs-server",
    "docs_display_name": "Company Internal Docs",
}
```

---

**Happy Documenting! 📚✨**

For questions, issues, or feature requests, please check the debug logs first, then create an issue with relevant details.

---

## 🙏 Attribution

This project is powered by **[Crawl4AI](https://github.com/unclecode/crawl4ai)** - an amazing open-source LLM-friendly web crawler and scraper.

<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://img.shields.io/badge/Powered%20by-Crawl4AI-blue?style=flat-square" alt="Powered by Crawl4AI"/>
</a>

Crawl4AI enables the intelligent web scraping capabilities that make this documentation toolkit possible. A huge thanks to [@unclecode](https://github.com/unclecode) and the Crawl4AI community for building such an incredible tool! 🚀

**Check out Crawl4AI:**
- **Repository**: https://github.com/unclecode/crawl4ai
- **Documentation**: https://crawl4ai.com
- **Discord Community**: https://discord.gg/jP8KfhDhyN

## 📄 License 