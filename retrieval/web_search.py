"""
Web search module using Serper API for real-time information gathering.
PRD TASK3: Utilize web search tools for real-time information collection.
"""

import logging
import requests
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class SerperWebSearchTool:
    """Web search tool class using Serper API"""

    def __init__(self):
        """Initialize the web search tool."""
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY is not set in the environment variables.")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        })

    def _search_request(self, endpoint: str, query: str, max_results: int) -> Optional[Dict[str, Any]]:
        """Helper function to make a request to the Serper API."""
        url = f"https://google.serper.dev/{endpoint}"
        payload = {
            "q": query,
            "num": max_results
        }
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed for endpoint '{endpoint}': {e}")
            return None

    def search_web(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a web search using the Serper API.
        
        Args:
            query: The search query.
            max_results: The maximum number of results to return.
            
        Returns:
            A list of search results.
        """
        data = self._search_request("search", query, max_results)
        if not data or "organic" not in data:
            return []
        
        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Serper Web Search"
            }
            for item in data["organic"]
        ]
        logger.info(f"Serper web search for '{query}' returned {len(results)} results.")
        return results

    def search_images(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Perform an image search using the Serper API.
        
        Args:
            query: The search query.
            max_results: The maximum number of results to return.
            
        Returns:
            A list of image results.
        """
        data = self._search_request("images", query, max_results)
        if not data or "images" not in data:
            return []
            
        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "imageUrl": item.get("imageUrl", ""),
                "source": "Serper Image Search"
            }
            for item in data["images"]
        ]
        logger.info(f"Serper image search for '{query}' returned {len(results)} results.")
        return results

    def search_videos(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a video search using the Serper API.
        
        Args:
            query: The search query.
            max_results: The maximum number of results to return.
            
        Returns:
            A list of video results.
        """
        data = self._search_request("videos", query, max_results)
        if not data or "videos" not in data:
            return []

        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "thumbnailUrl": item.get("thumbnail", ""),
                "source": item.get("source", "Serper Video Search"),
                "duration": item.get("duration", "")
            }
            for item in data["videos"]
        ]
        logger.info(f"Serper video search for '{query}' returned {len(results)} results.")
        return results

# Global instance for easy access
search_tool = SerperWebSearchTool()

def search_web(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    return search_tool.search_web(query, max_results)

def search_images(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    return search_tool.search_images(query, max_results)

def search_videos(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    return search_tool.search_videos(query, max_results)