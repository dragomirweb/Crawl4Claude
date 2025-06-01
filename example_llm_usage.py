#!/usr/bin/env python3
"""
Example: Using Documentation for LLM Context

This script demonstrates various ways to use scraped documentation
as context for Large Language Models (LLMs). It shows how to:

1. Load and prepare documentation content
2. Search for relevant sections
3. Create context for specific questions
4. Format content for different LLM providers

Usage:
    python example_llm_usage.py
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

# Import configuration
try:
    from config import SCRAPER_CONFIG, ADVANCED_CONFIG
except ImportError as e:
    raise ImportError(
        "Configuration file 'config.py' is required but not found. "
        "Please ensure config.py exists and contains the required configuration variables."
    ) from e


class DocumentationLLMContext:
    """Helper class for using documentation as LLM context"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use config to determine default database path
            output_dir = SCRAPER_CONFIG.get("output_dir", "docs_db")
            db_path = f"{output_dir}/documentation.db"
        
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Get domain-specific keywords from config
        self.domain_keywords = ADVANCED_CONFIG.get("scoring_keywords", [
            "tutorial", "guide", "documentation", "reference"
        ])
    
    def search_relevant_content(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for content relevant to a query"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Try FTS search first
            try:
                cursor = conn.execute("""
                    SELECT url, title, section, markdown, word_count,
                           snippet(pages_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
                    FROM pages_fts 
                    WHERE pages_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, max_results))
                results = [dict(row) for row in cursor.fetchall()]
                
                if results:
                    return results
            except:
                # Fallback to simple LIKE search if FTS fails
                pass
            
            # Fallback search
            cursor = conn.execute("""
                SELECT url, title, section, markdown, word_count
                FROM pages 
                WHERE markdown LIKE ? OR title LIKE ?
                ORDER BY word_count DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", max_results))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_section_content(self, section: str) -> List[Dict]:
        """Get all content from a specific section"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT url, title, markdown, word_count
                FROM pages 
                WHERE section = ?
                ORDER BY title
            """, (section,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create_context_for_question(self, question: str, max_words: int = 4000) -> str:
        """Create optimized context for a specific question"""
        
        # Extract key terms from the question
        key_terms = self._extract_key_terms(question)
        
        # Search for relevant content
        relevant_docs = []
        for term in key_terms:
            docs = self.search_relevant_content(term, max_results=3)
            relevant_docs.extend(docs)
        
        # Remove duplicates and sort by relevance
        seen_urls = set()
        unique_docs = []
        for doc in relevant_docs:
            if doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                unique_docs.append(doc)
        
        # Build context within word limit
        context_parts = []
        current_words = 0
        
        for doc in unique_docs:
            doc_words = doc.get('word_count', 0)
            if current_words + doc_words > max_words:
                # Truncate if necessary
                remaining_words = max_words - current_words
                if remaining_words > 100:  # Only include if substantial content remains
                    content = self._truncate_content(doc['markdown'], remaining_words)
                    context_parts.append(f"## {doc['title']}\n\n{content}")
                break
            else:
                context_parts.append(f"## {doc['title']}\n\n{doc['markdown']}")
                current_words += doc_words
        
        return "\n\n---\n\n".join(context_parts)
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key terms from a question"""
        # Simple keyword extraction (could be enhanced with NLP)
        import re
        
        # Use domain-specific terms from config
        domain_terms = self.domain_keywords
        
        # Extract words from question
        words = re.findall(r'\b\w+\b', question.lower())
        
        # Filter out stop words
        stop_words = {
            'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'cannot',
            'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between',
            'how', 'what', 'when', 'where', 'why', 'which', 'who'
        }
        
        # Prioritize domain terms and longer words
        key_terms = []
        for word in words:
            if word in domain_terms:
                key_terms.insert(0, word)  # Prioritize domain-specific terms
            elif word not in stop_words and len(word) > 3:
                key_terms.append(word)
        
        return key_terms[:5]  # Limit to top 5 terms
    
    def _truncate_content(self, content: str, max_words: int) -> str:
        """Truncate content to approximately max_words"""
        words = content.split()
        if len(words) <= max_words:
            return content
        
        truncated = ' '.join(words[:max_words])
        return truncated + "..."
    
    def format_for_openai(self, context: str, question: str, domain_name: str = "documentation") -> List[Dict]:
        """Format context and question for OpenAI API"""
        return [
            {
                "role": "system",
                "content": (
                    f"You are an expert consultant with deep knowledge of the provided {domain_name}. "
                    f"Use the following documentation to provide accurate, detailed answers. "
                    f"Base your responses strictly on the provided documentation content.\n\n"
                    f"DOCUMENTATION:\n{context}"
                )
            },
            {
                "role": "user", 
                "content": question
            }
        ]
    
    def format_for_anthropic(self, context: str, question: str, domain_name: str = "documentation") -> str:
        """Format context and question for Anthropic Claude"""
        return f"""You are an expert consultant with deep knowledge of the provided {domain_name}. Use the following documentation to provide accurate, detailed answers.

<documentation>
{context}
</documentation>

Question: {question}"""


def example_search_and_context():
    """Example: Search for content and create context"""
    print("🔍 Example: Searching for relevant content")
    
    try:
        llm_context = DocumentationLLMContext()
        
        # Get first domain keyword from config for search example
        search_term = ADVANCED_CONFIG.get("scoring_keywords", ["tutorial"])[0]
        
        # Search for content
        results = llm_context.search_relevant_content(f"{search_term} guide", max_results=3)
        
        print(f"Found {len(results)} relevant documents for '{search_term}':")
        for i, doc in enumerate(results, 1):
            print(f"{i}. {doc['title']} (Section: {doc['section']})")
            print(f"   URL: {doc['url']}")
            print(f"   Words: {doc['word_count']}")
            if doc.get('snippet'):
                print(f"   Preview: {doc['snippet']}")
            print()
            
    except FileNotFoundError:
        print("❌ Database not found. Run the scraper first: python docs_scraper.py")


def example_question_context():
    """Example: Create context for a specific question"""
    print("❓ Example: Creating context for a user question")
    
    # Use a generic example question based on domain keywords
    domain_keywords = ADVANCED_CONFIG.get("scoring_keywords", ["documentation"])
    primary_keyword = domain_keywords[0] if domain_keywords else "feature"
    
    question = f"How do I get started with {primary_keyword}? What are the basic concepts I need to understand?"
    
    try:
        llm_context = DocumentationLLMContext()
        
        # Create context for the question
        context = llm_context.create_context_for_question(question, max_words=2000)
        
        print(f"Question: {question}")
        print(f"Context length: {len(context.split())} words")
        print("\nGenerated context preview:")
        print("=" * 50)
        print(context[:500] + "..." if len(context) > 500 else context)
        print("=" * 50)
        
        # Show formatted for different LLM providers
        print("\n🤖 OpenAI Format:")
        openai_messages = llm_context.format_for_openai(context, question, "knowledge base")
        print(json.dumps(openai_messages, indent=2)[:300] + "...")
        
        print("\n🤖 Anthropic Format:")
        anthropic_prompt = llm_context.format_for_anthropic(context, question, "knowledge base")
        print(anthropic_prompt[:300] + "...")
        
    except FileNotFoundError:
        print("❌ Database not found. Run the scraper first: python docs_scraper.py")


def example_section_content():
    """Example: Get all content from a specific section"""
    
    try:
        llm_context = DocumentationLLMContext()
        
        # Get available sections from database
        with sqlite3.connect(llm_context.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT section FROM pages WHERE section != '' ORDER BY section")
            sections = [row[0] for row in cursor.fetchall()]
        
        if not sections:
            print("📚 No sections found in the documentation database.")
            return
            
        # Use the first available section as example
        example_section = sections[0]
        print(f"📚 Example: Getting content from '{example_section}' section")
        
        # Get section content
        section_docs = llm_context.get_section_content(example_section)
        
        print(f"Found {len(section_docs)} documents in '{example_section}' section:")
        total_words = sum(doc['word_count'] for doc in section_docs)
        
        for doc in section_docs[:5]:  # Show first 5
            print(f"• {doc['title']} ({doc['word_count']} words)")
        
        if len(section_docs) > 5:
            print(f"... and {len(section_docs) - 5} more documents")
            
        print(f"\nTotal words in {example_section} section: {total_words:,}")
        
        if len(sections) > 1:
            print(f"\nOther available sections: {', '.join(sections[1:])}")
        
    except FileNotFoundError:
        print("❌ Database not found. Run the scraper first: python docs_scraper.py")


def example_mcp_server_setup():
    """Example: Setting up the documentation as an MCP server"""
    print("🖥️  Example: Setting up Documentation as MCP Server")
    
    try:
        llm_context = DocumentationLLMContext()
        
        # Check if MCP server file exists
        mcp_server_path = Path("mcp_docs_server.py")
        if not mcp_server_path.exists():
            print("❌ MCP server file not found. This example requires mcp_docs_server.py")
            return
        
        base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
        domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
        output_dir = SCRAPER_CONFIG.get("output_dir", "docs_db")
        
        print(f"📚 Documentation source: {domain_name}")
        print(f"🗂️  Database path: {output_dir}/documentation.db")
        print("\n🔧 MCP Server Setup Steps:")
        print("1. Start the MCP server:")
        print(f"   python mcp_docs_server.py")
        print("\n2. Configure your MCP client (e.g., Claude Desktop):")
        print("   Add to your claude_mcp_config.json:")
        
        # Generate example MCP config
        mcp_config = {
            "mcpServers": {
                f"{domain_name.replace('.', '_')}_docs": {
                    "command": "python",
                    "args": [str(Path("mcp_docs_server.py").resolve())],
                    "env": {
                        "DB_PATH": str(Path(output_dir) / "documentation.db")
                    }
                }
            }
        }
        
        print(json.dumps(mcp_config, indent=2))
        
        print("\n3. Available MCP tools once connected:")
        print("   • search_docs - Search through documentation")
        print("   • get_section - Get all content from a section")
        print("   • get_stats - Get documentation statistics")
        print("   • create_context - Create LLM-optimized context")
        
        print("\n💡 Benefits of using MCP:")
        print("   • Real-time access to documentation from Claude")
        print("   • No need to copy/paste context manually")
        print("   • Automatic context optimization")
        print("   • Searchable knowledge base integration")
        
    except FileNotFoundError:
        print("❌ Database not found. Run the scraper first: python docs_scraper.py")


def example_mcp_usage_scenarios():
    """Example: Common MCP usage scenarios with the documentation"""
    print("🎯 Example: MCP Usage Scenarios")
    
    try:
        llm_context = DocumentationLLMContext()
        
        base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
        domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
        domain_keywords = ADVANCED_CONFIG.get("scoring_keywords", ["documentation"])
        
        print(f"📖 Documentation: {domain_name}")
        print("\n🔍 Common MCP Usage Scenarios:")
        
        # Scenario 1: Quick search
        print("\n1️⃣  **Quick Search Scenario**")
        print("   User in Claude: 'Search the docs for getting started guides'")
        print("   MCP Response: Uses search_docs tool to find relevant content")
        example_search = domain_keywords[0] if domain_keywords else "guide"
        search_results = llm_context.search_relevant_content(example_search, max_results=2)
        if search_results:
            print(f"   Found {len(search_results)} results for '{example_search}':")
            for result in search_results[:2]:
                print(f"   • {result['title']} ({result['word_count']} words)")
        
        # Scenario 2: Section exploration
        print("\n2️⃣  **Section Exploration Scenario**")
        print("   User in Claude: 'Show me all content from the tutorials section'")
        print("   MCP Response: Uses get_section tool to retrieve organized content")
        
        # Get available sections for example
        with sqlite3.connect(llm_context.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT section FROM pages WHERE section != '' LIMIT 3")
            sections = [row[0] for row in cursor.fetchall()]
        
        if sections:
            example_section = sections[0]
            section_docs = llm_context.get_section_content(example_section)
            print(f"   Example: '{example_section}' section has {len(section_docs)} documents")
            if section_docs:
                total_words = sum(doc['word_count'] for doc in section_docs)
                print(f"   Total content: {total_words:,} words")
        
        # Scenario 3: Context creation
        print("\n3️⃣  **Intelligent Context Creation Scenario**")
        print("   User in Claude: 'Help me understand how to implement feature X'")
        print("   MCP Response: Uses create_context tool to build optimized context")
        
        example_question = f"How do I get started with {domain_keywords[0] if domain_keywords else 'this system'}?"
        context = llm_context.create_context_for_question(example_question, max_words=1000)
        context_word_count = len(context.split())
        print(f"   Generated context: {context_word_count} words of relevant documentation")
        
        print("\n🚀 Advanced MCP Integration Tips:")
        print("   • Use specific search terms for better results")
        print("   • Combine multiple tools in a conversation")
        print("   • Ask for section overviews before diving deep")
        print("   • Request context creation for complex topics")
        
        print(f"\n📋 Sample MCP Commands to try:")
        print(f"   'Search the {domain_name} docs for authentication'")
        print(f"   'Get all content from the API reference section'")
        print(f"   'Create context for integrating with external services'")
        print(f"   'Show me statistics about the documentation'")
        
    except FileNotFoundError:
        print("❌ Database not found. Run the scraper first: python docs_scraper.py")


def main():
    """Run example demonstrations"""
    base_url = SCRAPER_CONFIG.get("base_url", "documentation site")
    domain_name = base_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    print(f"🤖 Documentation LLM Context Examples")
    print(f"📚 Source: {domain_name}")
    print("=" * 50)
    
    example_search_and_context()
    print("\n" + "-" * 50 + "\n")
    
    example_question_context()
    print("\n" + "-" * 50 + "\n")
    
    example_section_content()
    print("\n" + "-" * 50 + "\n")
    
    example_mcp_server_setup()
    print("\n" + "-" * 50 + "\n")
    
    example_mcp_usage_scenarios()
    
    print("\n💡 Tips for using with LLMs:")
    print("• Limit context to 4000-8000 words for most models")
    print("• Use specific sections for focused questions")
    print("• Search for relevant content before creating context")
    print("• Adjust max_words based on your LLM's context limit")
    print("• Customize domain keywords in config.py for better search results")
    print("• Use MCP integration for seamless Claude Desktop experience")


if __name__ == "__main__":
    main() 