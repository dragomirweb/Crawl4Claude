#!/usr/bin/env python3
"""
Documentation Query Tool

Utility script to query and analyze scraped documentation databases.
Provides various ways to search and extract information from the documentation.

Usage examples:
    python query_docs.py --search "tutorial"
    python query_docs.py --section "getting-started" 
    python query_docs.py --stats
    python query_docs.py --export-section "api" --format markdown
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Import configuration
try:
    from config import SCRAPER_CONFIG, get_database_path, get_docs_display_name
except ImportError as e:
    print("❌ Configuration file 'config.py' is required but not found.")
    print("Please ensure config.py exists and contains the required configuration variables.")
    sys.exit(1)


class DocumentationQuery:
    """Query interface for scraped documentation databases"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use config helper to get database path
            db_path = get_database_path()
        
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Get base URL for display purposes
        self.base_url = SCRAPER_CONFIG.get("base_url", "")
        self.domain_name = get_docs_display_name()
            
    def _extract_domain_name(self) -> str:
        """Extract domain name from base URL for display (deprecated - use get_docs_display_name())"""
        return get_docs_display_name()
    
    def search_content(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for content containing the query string"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Try FTS search first
            try:
                cursor = conn.execute("""
                    SELECT p.url, p.title, p.section, p.subsection, p.word_count,
                           snippet(pages_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
                    FROM pages_fts 
                    JOIN pages p ON pages_fts.rowid = p.id
                    WHERE pages_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                
                results = [dict(row) for row in cursor.fetchall()]
                if results:
                    return results
            except sqlite3.OperationalError:
                # FTS not available, fall back to LIKE search
                pass
            
            # Fallback LIKE search
            cursor = conn.execute("""
                SELECT url, title, section, subsection, word_count,
                       substr(markdown, 1, 200) as snippet
                FROM pages 
                WHERE title LIKE ? OR markdown LIKE ?
                ORDER BY word_count DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_section(self, section: str) -> List[Dict]:
        """Get all pages from a specific section"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT url, title, section, subsection, word_count, markdown
                FROM pages 
                WHERE section = ?
                ORDER BY title
            """, (section,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get summary statistics about the documentation"""
        with sqlite3.connect(self.db_path) as conn:
            # Total pages and words
            cursor = conn.execute("SELECT COUNT(*), SUM(word_count) FROM pages")
            total_pages, total_words = cursor.fetchone()
            
            # Pages by section
            cursor = conn.execute("""
                SELECT section, COUNT(*) as page_count, SUM(word_count) as word_count
                FROM pages 
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section 
                ORDER BY page_count DESC
            """)
            sections = [{"section": row[0], "pages": row[1], "words": row[2]} 
                       for row in cursor.fetchall()]
            
            # Top pages by word count
            cursor = conn.execute("""
                SELECT title, url, word_count 
                FROM pages 
                ORDER BY word_count DESC 
                LIMIT 10
            """)
            top_pages = [{"title": row[0], "url": row[1], "words": row[2]} 
                        for row in cursor.fetchall()]
            
            return {
                "total_pages": total_pages,
                "total_words": total_words,
                "sections": sections,
                "top_pages": top_pages,
                "domain_name": self.domain_name,
                "base_url": self.base_url
            }
    
    def get_all_sections(self) -> List[str]:
        """Get list of all documentation sections"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT section 
                FROM pages 
                WHERE section IS NOT NULL AND section != ''
                ORDER BY section
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def export_section(self, section: str, format: str = "markdown") -> str:
        """Export a section in the specified format"""
        pages = self.get_by_section(section)
        
        if format.lower() == "json":
            return json.dumps(pages, indent=2, ensure_ascii=False)
        
        elif format.lower() == "markdown":
            output = [f"# {self.domain_name} Documentation: {section.title()}\n"]
            output.append(f"Total pages: {len(pages)}\n")
            if self.base_url:
                output.append(f"Source: {self.base_url}\n")
            output.append("---\n")
            
            for page in pages:
                output.append(f"## {page['title']}\n")
                output.append(f"**URL:** {page['url']}\n")
                if page['subsection']:
                    output.append(f"**Subsection:** {page['subsection']}\n")
                output.append(f"**Word Count:** {page['word_count']}\n\n")
                output.append(page['markdown'] + "\n\n")
                output.append("---\n\n")
            
            return "\n".join(output)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_page_by_url(self, url: str) -> Optional[Dict]:
        """Get a specific page by URL"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM pages WHERE url = ?
            """, (url,))
            
            row = cursor.fetchone()
            return dict(row) if row else None


def get_default_db_path() -> str:
    """Get the default database path from config"""
    return get_database_path()


def main():
    # Get domain info for help text
    domain_name = get_docs_display_name()
    base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
    
    parser = argparse.ArgumentParser(
        description=f"Query and analyze scraped documentation database for {domain_name}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python query_docs.py --search "tutorial guide"
    python query_docs.py --section "getting-started" 
    python query_docs.py --stats
    python query_docs.py --export-section "api" --format markdown > api.md
    python query_docs.py --list-sections
        """
    )
    
    default_db = get_default_db_path()
    parser.add_argument("--db", default=default_db,
                       help=f"Path to the documentation database (default: {default_db})")
    
    # Search operations
    parser.add_argument("--search", metavar="QUERY",
                       help="Search for content containing the query")
    parser.add_argument("--section", metavar="SECTION",
                       help="Get all pages from a specific section")
    parser.add_argument("--url", metavar="URL",
                       help="Get a specific page by URL")
    
    # Export operations
    parser.add_argument("--export-section", metavar="SECTION",
                       help="Export a section to stdout")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                       help="Export format (default: markdown)")
    
    # Information operations
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics")
    parser.add_argument("--list-sections", action="store_true",
                       help="List all available sections")
    
    # Options
    parser.add_argument("--limit", type=int, default=10,
                       help="Limit number of search results (default: 10)")
    
    args = parser.parse_args()
    
    try:
        query_tool = DocumentationQuery(args.db)
        
        if args.search:
            print(f"🔍 Searching for: '{args.search}'\n")
            results = query_tool.search_content(args.search, args.limit)
            
            if not results:
                print("No results found.")
                return
                
            for i, result in enumerate(results, 1):
                print(f"{i}. **{result['title']}**")
                print(f"   Section: {result['section']}")
                print(f"   URL: {result['url']}")
                print(f"   Words: {result['word_count']}")
                if result.get('snippet'):
                    print(f"   Preview: {result['snippet']}")
                print()
        
        elif args.section:
            print(f"📚 Pages in section: '{args.section}'\n")
            pages = query_tool.get_by_section(args.section)
            
            if not pages:
                print("No pages found in this section.")
                return
                
            for page in pages:
                print(f"• {page['title']}")
                print(f"  URL: {page['url']}")
                print(f"  Words: {page['word_count']}")
                if page['subsection']:
                    print(f"  Subsection: {page['subsection']}")
                print()
        
        elif args.url:
            print(f"📄 Page details for: {args.url}\n")
            page = query_tool.get_page_by_url(args.url)
            
            if not page:
                print("Page not found.")
                return
                
            print(f"**Title:** {page['title']}")
            print(f"**Section:** {page['section']}")
            if page['subsection']:
                print(f"**Subsection:** {page['subsection']}")
            print(f"**Word Count:** {page['word_count']}")
            print(f"**Scraped:** {page['scraped_at']}")
            print("\n**Content:**")
            print(page['markdown'][:500] + "..." if len(page['markdown']) > 500 else page['markdown'])
        
        elif args.export_section:
            content = query_tool.export_section(args.export_section, args.format)
            print(content)
        
        elif args.stats:
            print(f"📊 {query_tool.domain_name} Documentation Statistics\n")
            stats = query_tool.get_stats()
            
            print(f"**Source:** {stats['base_url'] or 'Local database'}")
            print(f"**Database:** {query_tool.db_path}")
            print(f"**Total Pages:** {stats['total_pages']:,}")
            print(f"**Total Words:** {stats['total_words']:,}")
            print()
            
            if stats['sections']:
                print("**Pages by Section:**")
                for section in stats['sections']:
                    section_name = section['section'] or 'General'
                    print(f"  {section_name}: {section['pages']} pages ({section['words']:,} words)")
                print()
            
            if stats['top_pages']:
                print("**Largest Pages:**")
                for page in stats['top_pages']:
                    print(f"  {page['title']}: {page['words']:,} words")
                    print(f"    {page['url']}")
                    print()
        
        elif args.list_sections:
            print(f"📋 Available Sections in {query_tool.domain_name}\n")
            sections = query_tool.get_all_sections()
            
            if sections:
                for section in sections:
                    print(f"• {section}")
            else:
                print("No sections found in the database.")
        
        else:
            parser.print_help()
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure you've run the scraper first: python docs_scraper.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 