from duckduckgo_search import DDGS
import re
from typing import List, Dict, Optional


class WebSearchService:
    """Search the web for Arch Linux information"""
    
    @staticmethod
    async def search_arch_info(query: str, max_results: int = 3) -> str:
        """Search for Arch Linux related information"""
        try:
            # Enhance query with Arch Linux context
            enhanced_query = f"{query} arch linux"
            
            # Search using DuckDuckGo
            with DDGS() as ddgs:
                results = list(ddgs.text(enhanced_query, max_results=max_results))
            
            if not results:
                return ""
            
            # Format results for LLM context
            context = "\n\n**WEB SEARCH RESULTS (use this information):**\n"
            context += f"Query: '{query}'\n\n"
            
            for idx, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('body', 'No description')
                url = result.get('href', '')
                
                context += f"{idx}. **{title}**\n"
                context += f"   {snippet}\n"
                if url:
                    context += f"   Source: {url}\n"
                context += "\n"
            
            return context
            
        except Exception as e:
            # If rate limited or error, fail silently - LLM can still respond
            print(f"Search error: {e}")
            # Return a note that search failed but don't break the response
            return "\n\n**Note:** Web search temporarily unavailable. Using existing knowledge.\n"
    
    @staticmethod
    async def search_arch_wiki(topic: str) -> str:
        """Search Arch Wiki specifically"""
        try:
            wiki_query = f"site:wiki.archlinux.org {topic}"
            
            with DDGS() as ddgs:
                results = list(ddgs.text(wiki_query, max_results=2))
            
            if not results:
                return ""
            
            context = "\n\n**ARCH WIKI RESULTS:**\n"
            for result in results:
                title = result.get('title', '')
                snippet = result.get('body', '')
                url = result.get('href', '')
                
                context += f"• **{title}**\n"
                context += f"  {snippet}\n"
                if url:
                    context += f"  {url}\n"
                context += "\n"
            
            return context
            
        except Exception as e:
            print(f"Wiki search error: {e}")
            return ""
    
    @staticmethod
    def should_search(user_message: str) -> Optional[str]:
        """Determine if we should search and extract query"""
        user_message_lower = user_message.lower()
        
        # Patterns that indicate need for search
        search_patterns = [
            r"what is ([a-zA-Z0-9\-_]+)",
            r"tell me about ([a-zA-Z0-9\-_]+)",
            r"(?:do you know|heard of|familiar with) ([a-zA-Z0-9\-_]+)",
            r"explain ([a-zA-Z0-9\-_]+)",
            r"(?:how does|what does) ([a-zA-Z0-9\-_]+) (?:do|work)",
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, user_message_lower)
            if match:
                potential_query = match.group(1)
                # Exclude common words
                if len(potential_query) > 2 and potential_query not in ['the', 'is', 'it', 'that', 'this']:
                    return potential_query
        
        return None
