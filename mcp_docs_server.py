#!/usr/bin/env python3
"""
MCP Documentation Server

A Model Context Protocol server that provides AI agents with searchable access
to documentation databases. Works with any documentation database following
the standard schema (pages, sections, full-text search).

Configuration:
    Primary: Uses config.py for default settings
    Override: Environment variables can override config values
    
Environment Variables (optional overrides):
    DOCS_DB_PATH: Path to the documentation database
    DOCS_DB_NAME: Name/description of the documentation
    DOCS_BASE_URL: Base URL for the documentation site
    MCP_SERVER_NAME: Name of the MCP server

Usage:
    python mcp_docs_server.py

"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import configuration
try:
    from config import MCP_CONFIG, get_mcp_server_config
except ImportError as e:
    print("❌ Configuration file 'config.py' is required but not found.")
    print("Please ensure config.py exists and contains the required configuration variables.")
    sys.exit(1)

# FastMCP for easy MCP server creation
try:
    from fastmcp import FastMCP
except ImportError:
    print("❌ FastMCP not found. Install with: pip install fastmcp")
    sys.exit(1)


class DocumentationMCP:
    """MCP server for documentation database access"""
    
    def __init__(
        self,
        db_path: str,
        docs_name: str = "Documentation",
        base_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.db_path = Path(db_path)
        self.docs_name = docs_name
        self.base_url = base_url
        self.config = config or {}  # Store config for later use
        
        # Get configuration settings (use provided config or defaults from MCP_CONFIG)
        if config:
            self.search_limit = config.get("search_limit", 10)
            self.max_search_limit = config.get("max_search_limit", 50)
            self.section_limit = config.get("section_limit", 20)
            self.max_section_limit = config.get("max_section_limit", 100)
            self.snippet_length = config.get("snippet_length", 32)
            self.enable_fts_fallback = config.get("enable_fts_fallback", True)
        else:
            # Fallback to MCP_CONFIG for backward compatibility
            self.search_limit = MCP_CONFIG.get("default_search_limit", 10)
            self.max_search_limit = MCP_CONFIG.get("max_search_limit", 50)
            self.section_limit = MCP_CONFIG.get("default_section_limit", 20)
            self.max_section_limit = MCP_CONFIG.get("max_section_limit", 100)
            self.snippet_length = MCP_CONFIG.get("snippet_length", 32)
            self.enable_fts_fallback = MCP_CONFIG.get("enable_fts_fallback", True)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Verify database schema
        self._verify_schema()
    
    def _verify_schema(self):
        """Verify the database has the expected schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('pages', 'pages_fts')
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'pages' not in tables:
                    raise ValueError("Database missing 'pages' table")
                    
                # Check if FTS is available (optional but recommended)
                self.has_fts = 'pages_fts' in tables
                
        except Exception as e:
            raise ValueError(f"Invalid database schema: {e}")
    
    def search_content(
        self, 
        query: str, 
        limit: int = None,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search documentation content"""
        # Apply limits from config
        if limit is None:
            limit = self.search_limit
        limit = min(limit, self.max_search_limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if self.has_fts:
                # Use full-text search if available
                sql = """
                    SELECT p.url, p.title, p.section, p.subsection, p.word_count,
                           snippet(pages_fts, 1, '<mark>', '</mark>', '...', ?) as snippet
                    FROM pages_fts 
                    JOIN pages p ON pages_fts.rowid = p.id
                    WHERE pages_fts MATCH ?
                """
                params = [self.snippet_length, query]
                
                if section:
                    sql += " AND p.section = ?"
                    params.append(section)
                    
                sql += " ORDER BY rank LIMIT ?"
                params.append(limit)
                
            elif self.enable_fts_fallback:
                # Fallback to LIKE search
                sql = """
                    SELECT url, title, section, subsection, word_count,
                           substr(markdown, 1, 200) as snippet
                    FROM pages 
                    WHERE (title LIKE ? OR markdown LIKE ?)
                """
                like_query = f"%{query}%"
                params = [like_query, like_query]
                
                if section:
                    sql += " AND section = ?"
                    params.append(section)
                    
                sql += " ORDER BY word_count DESC LIMIT ?"
                params.append(limit)
            else:
                # No search available
                return [{"error": "Full-text search not available and fallback disabled"}]
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """Get all documentation sections with stats"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    section,
                    COUNT(*) as page_count,
                    SUM(word_count) as total_words,
                    AVG(word_count) as avg_words
                FROM pages 
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section 
                ORDER BY page_count DESC
            """)
            
            return [{
                "section": row[0],
                "page_count": row[1],
                "total_words": row[2] or 0,
                "avg_words": round(row[3] or 0, 1)
            } for row in cursor.fetchall()]
    
    def get_page_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get specific page by URL"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT url, title, section, subsection, word_count, 
                       markdown, scraped_at
                FROM pages 
                WHERE url = ?
            """, (url,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_section_pages(self, section: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get all pages from a specific section"""
        # Apply limits from config
        if limit is None:
            limit = self.section_limit
        limit = min(limit, self.max_section_limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT url, title, section, subsection, word_count
                FROM pages 
                WHERE section = ?
                ORDER BY word_count DESC
                LIMIT ?
            """, (section, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Basic stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_pages,
                    SUM(word_count) as total_words,
                    AVG(word_count) as avg_words_per_page,
                    COUNT(DISTINCT section) as section_count
                FROM pages
            """)
            stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
            
            # Top sections
            cursor = conn.execute("""
                SELECT section, COUNT(*) as pages
                FROM pages 
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section 
                ORDER BY pages DESC 
                LIMIT 5
            """)
            stats['top_sections'] = [
                {"section": row[0], "pages": row[1]} 
                for row in cursor.fetchall()
            ]
            
            return stats


def get_configuration() -> Dict[str, Any]:
    """Get MCP server configuration from config and environment variables"""
    
    # Use the helper function from config.py
    config = get_mcp_server_config()
    
    # Allow environment variable overrides
    final_config = {
        "db_path": os.getenv("DOCS_DB_PATH", config["db_path"]),
        "docs_name": os.getenv("DOCS_DB_NAME", config["docs_name"]),
        "base_url": os.getenv("DOCS_BASE_URL", config["base_url"]),
        "server_name": os.getenv("MCP_SERVER_NAME", config["server_name"]),
        # Include additional config values
        "server_description": config["server_description"],
        "search_limit": config["search_limit"],
        "max_search_limit": config["max_search_limit"],
        "section_limit": config["section_limit"],
        "max_section_limit": config["max_section_limit"],
        "snippet_length": config["snippet_length"],
        "enable_fts_fallback": config["enable_fts_fallback"],
        "include_full_urls": config["include_full_urls"],
    }
    
    return final_config


# Initialize MCP server
def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server"""
    
    # Get configuration
    config = get_configuration()
    
    # Initialize documentation handler
    try:
        docs = DocumentationMCP(
            config["db_path"], 
            config["docs_name"], 
            config["base_url"] if config["base_url"] else None,
            config  # Pass the full config
        )
    except Exception as e:
        print(f"❌ Failed to initialize documentation database: {e}")
        print(f"💡 Check database path: {config['db_path']}")
        print(f"💡 Run the scraper first: python docs_scraper.py")
        sys.exit(1)
    
    # Create MCP server
    server_description = config["server_description"]
    mcp = FastMCP(config["server_name"])
    
    @mcp.tool()
    def search_documentation(
        query: str, 
        limit: int = None, 
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search through documentation content.
        
        Args:
            query: Search query text
            limit: Maximum number of results (default from config)
            section: Optional section to search within
        
        Returns:
            List of matching pages with snippets and metadata
        """
        try:
            results = docs.search_content(query, limit, section)
            
            # Add base URL to results if configured
            if docs.base_url and docs.config.get("include_full_urls", True):
                for result in results:
                    if not result.get('url', '').startswith(('http://', 'https://')):
                        result['full_url'] = docs.base_url.rstrip('/') + '/' + result.get('url', '').lstrip('/')
                    else:
                        result['full_url'] = result.get('url', '')
            
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    @mcp.tool()
    def get_documentation_sections() -> List[Dict[str, Any]]:
        """
        Get all available documentation sections with statistics.
        
        Returns:
            List of sections with page counts and word counts
        """
        try:
            return docs.get_sections()
        except Exception as e:
            return [{"error": f"Failed to get sections: {str(e)}"}]
    
    @mcp.tool()
    def get_page_content(url: str) -> Optional[Dict[str, Any]]:
        """
        Get the full content of a specific documentation page.
        
        Args:
            url: URL of the page to retrieve
            
        Returns:
            Page content including title, section, and full markdown
        """
        try:
            return docs.get_page_by_url(url)
        except Exception as e:
            return {"error": f"Failed to get page: {str(e)}"}
    
    @mcp.tool()
    def browse_section(section: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Browse all pages in a specific documentation section.
        
        Args:
            section: Name of the section to browse
            limit: Maximum number of pages to return (default from config)
            
        Returns:
            List of pages in the section, ordered by word count
        """
        try:
            return docs.get_section_pages(section, limit)
        except Exception as e:
            return [{"error": f"Failed to browse section: {str(e)}"}]
    
    @mcp.tool()
    def get_documentation_stats() -> Dict[str, Any]:
        """
        Get overall statistics about the documentation database.
        
        Returns:
            Statistics including total pages, words, sections, and top sections
        """
        try:
            stats = docs.get_stats()
            stats['database_name'] = docs.docs_name
            if docs.base_url:
                stats['base_url'] = docs.base_url
            stats['server_config'] = {
                'has_fts': docs.has_fts,
                'search_limit': docs.search_limit,
                'max_search_limit': docs.max_search_limit,
                'section_limit': docs.section_limit
            }
            return stats
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}
    
    @mcp.resource("documentation://info")
    def documentation_info() -> str:
        """General information about this documentation database"""
        stats = docs.get_stats()
        return f"""
# {docs.docs_name}

This documentation database contains {stats.get('total_pages', 0)} pages 
with {stats.get('total_words', 0)} total words across {stats.get('section_count', 0)} sections.

Search capabilities: {'Full-text search' if docs.has_fts else 'Basic text search'}
Base URL: {docs.base_url or 'Not configured'}

Available tools:
- search_documentation: Search for content (limit: {docs.max_search_limit})
- get_documentation_sections: List all sections  
- get_page_content: Get full page content
- browse_section: Browse pages in a section (limit: {docs.max_section_limit})
- get_documentation_stats: Get database statistics

Use these tools to find relevant information from the documentation.
        """.strip()
    
    return mcp


if __name__ == "__main__":
    # Ensure FastMCP is available
    try:
        import fastmcp
    except ImportError:
        print("❌ FastMCP not found. Install with:")
        print("pip install fastmcp")
        sys.exit(1)
    
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        if Path(".env").exists():
            load_dotenv()
            print("✅ Loaded environment overrides from .env file")
    except ImportError:
        # python-dotenv not installed, skip
        pass
    
    # Get configuration for display
    config = get_configuration()
    
    print(f"🚀 Starting MCP Documentation Server")
    print(f"📊 Database: {config['db_path']}")
    print(f"📚 Documentation: {config['docs_name']}")
    print(f"🌐 Base URL: {config['base_url'] or 'Not configured'}")
    print(f"🔧 Server Name: {config['server_name']}")
    print(f"⚙️  Config Source: config.py + environment overrides")
    print(f"🔗 Server ready for MCP connections...")
    
    # Create and run the MCP server
    mcp = create_mcp_server()
    mcp.run() 