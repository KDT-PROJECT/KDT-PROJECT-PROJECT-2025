
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class IntelligentSearchService:
    def __init__(self):
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def web_search(self, query: str):
        try:
            response = self.tavily_client.search(query=query, search_depth="advanced")
            return response['results']
        except Exception as e:
            return f"Error performing web search: {e}"

    def image_search(self, query: str):
        try:
            response = self.tavily_client.search(query=query, search_depth="advanced", topic="images")
            return response['results']
        except Exception as e:
            return f"Error performing image search: {e}"

    def video_search(self, query: str):
        try:
            response = self.tavily_client.search(query=query, search_depth="advanced", topic="videos")
            return response['results']
        except Exception as e:
            return f"Error performing video search: {e}"

def get_intelligent_search_service():
    return IntelligentSearchService()
