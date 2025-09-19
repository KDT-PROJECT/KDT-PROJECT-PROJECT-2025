"""Web Search Client for Hybrid Search"""

import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from duckduckgo_search import DDGS

class WebSearchClient:
    """Client for web search integration"""

    def __init__(self):
        """Initialize web search client"""
        self.logger = logging.getLogger(__name__)

    def search_for_data_files(self, query: str, max_results: int = 10, file_types: List[str] = None) -> List[Dict[str, str]]:
        """
        Searches the web for data files (CSV, Excel, etc.) related to the query.

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.
            file_types (List[str]): List of file types to search for. Default: ['csv', 'xlsx', 'xls']

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing the 'title', 'url', and 'file_type'.
        """
        if file_types is None:
            file_types = ['csv', 'xlsx', 'xls']
        
        results = []
        
        for file_type in file_types:
            try:
                search_query = f"{query} filetype:{file_type}"
                with DDGS() as ddgs:
                    search_results = ddgs.text(search_query, max_results=max_results//len(file_types) + 1)
                    if search_results:
                        for r in search_results:
                            url = r.get('href', '')
                            # Check if the URL likely points to the correct file type
                            if (url.endswith(f'.{file_type}') or 
                                f'.{file_type}' in url.lower()):
                                results.append({
                                    "title": r.get('title', 'No Title'),
                                    "url": url,
                                    "file_type": file_type,
                                    "source": r.get('href', ''),
                                    "description": r.get('body', '')[:200] + '...' if r.get('body') else ''
                                })
            except Exception as e:
                self.logger.error(f"An error occurred during web search for {file_type} files: {e}")
                continue
        
        # Remove duplicates and limit results
        unique_results = []
        seen_urls = set()
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    break
        
        return unique_results

    def search_for_csv_files(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Searches the web for CSV files related to the query.
        (Legacy method for backward compatibility)

        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing the 'title' and 'url' of a CSV file.
        """
        results = self.search_for_data_files(query, max_results, ['csv'])
        # Convert to old format for backward compatibility
        return [{"title": r["title"], "url": r["url"]} for r in results]

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        try:
            # For now, return mock results with Korean startup/business content
            # In production, this would integrate with actual search APIs
            mock_results = self._get_mock_web_results(query, max_results)
            return mock_results

        except Exception as e:
            self.logger.error(f"Error in web search: {e}")
            return []

    def _get_mock_web_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate mock web search results for demonstration"""

        # Mock web results related to startup and business support in Seoul
        mock_data = [
            {
                "title": "서울시 창업지원 정책 현황 및 발전방안",
                "content": "서울시는 다양한 창업지원 정책을 통해 청년 창업가들을 지원하고 있습니다. 주요 프로그램으로는 서울창업허브, 청년창업센터, 창업지원금 등이 있으며, 매년 수천 개의 스타트업이 이러한 프로그램의 혜택을 받고 있습니다. 특히 IT, 바이오, 핀테크 분야에서 높은 성과를 보이고 있습니다.",
                "url": "https://startup.seoul.go.kr/policy/current",
                "relevance_score": 0.95,
                "date_published": "2024-12-01"
            },
            {
                "title": "2025년 창업지원사업 통합공고 - 중소벤처기업부",
                "content": "중소벤처기업부에서 2025년도 창업지원사업 통합공고를 발표했습니다. 총 예산 3조 2,940억원 규모로 예비창업자부터 성장기업까지 단계별 맞춤형 지원을 제공합니다. 주요 사업으로는 창업도약패키지, 청년창업사관학교, K-스타트업센터 등이 있습니다.",
                "url": "https://www.mss.go.kr/site/smba/ex/announce/2025startup",
                "relevance_score": 0.92,
                "date_published": "2024-12-15"
            },
            {
                "title": "서울 상권분석 리포트 2024 - 서울시 빅데이터담당관",
                "content": "서울시 25개 구별 상권현황을 분석한 2024년 리포트입니다. 강남구, 서초구, 송파구가 매출액 상위 3개 구로 나타났으며, 온라인 매출 비중이 전년 대비 15% 증가했습니다. 특히 배달음식, 생활용품 온라인 쇼핑 분야에서 큰 성장을 보였습니다.",
                "url": "https://data.seoul.go.kr/dataList/commercialArea/2024",
                "relevance_score": 0.89,
                "date_published": "2024-11-20"
            },
            {
                "title": "창업기업 자금조달 가이드 - 한국창업진흥원",
                "content": "창업기업이 알아야 할 자금조달 방법과 절차를 상세히 안내합니다. 정부지원자금, 엔젤투자, VC투자, 크라우드펀딩 등 다양한 자금조달 옵션을 소개하고, 단계별 준비사항과 주의점을 설명합니다. 특히 초기 창업기업을 위한 실무 팁을 제공합니다.",
                "url": "https://www.kised.or.kr/funding/guide/startup",
                "relevance_score": 0.86,
                "date_published": "2024-10-10"
            },
            {
                "title": "소상공인 디지털 전환 지원사업 - 소상공인시장진흥공단",
                "content": "소상공인의 디지털 전환을 위한 다양한 지원사업을 소개합니다. 온라인 쇼핑몰 구축, 배달앱 연동, 디지털 마케팅 교육 등을 통해 소상공인들의 디지털 역량 강화를 돕고 있습니다. 최대 200만원까지 지원 가능하며, 온라인 신청을 통해 접수할 수 있습니다.",
                "url": "https://www.semas.or.kr/web/contents/digital_transformation",
                "relevance_score": 0.83,
                "date_published": "2024-09-25"
            }
        ]

        # Filter results based on query relevance
        filtered_results = []
        query_lower = query.lower()

        for result in mock_data:
            # Simple relevance scoring based on keyword matching
            title_content = (result["title"] + " " + result["content"]).lower()

            # Check for Korean keywords
            keywords = ["창업", "지원", "상권", "분석", "사업", "소상공인", "스타트업"]
            query_keywords = [word for word in keywords if word in query_lower]

            if query_keywords:
                # Boost score if query keywords match
                keyword_matches = sum(1 for kw in query_keywords if kw in title_content)
                if keyword_matches > 0:
                    result["relevance_score"] *= (1 + keyword_matches * 0.1)
                    filtered_results.append(result)

        # If no specific matches, return top results
        if not filtered_results:
            filtered_results = mock_data

        # Sort by relevance score and return top results
        filtered_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return filtered_results[:max_results]

    def search_real_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform real web search using external API
        This is a placeholder for actual web search implementation
        """
        # TODO: Implement real web search using APIs like:
        # - Google Custom Search API
        # - Bing Search API
        # - DuckDuckGo API
        # - SerpAPI

        # For now, return mock results
        return self._get_mock_web_results(query, max_results)

# For testing
if __name__ == "__main__":
    client = WebSearchClient()
    
    # Test CSV search
    csv_results = client.search_for_csv_files("seoul population data", max_results=5)
    print("--- CSV Search Results ---")
    for result in csv_results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print("-" * 20)

    # Test existing search
    results = client.search("서울 창업 지원 프로그램", max_results=3)
    print("\n--- Mock Web Search Results ---")
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Score: {result['relevance_score']}")
        print(f"Content: {result['content'][:100]}...")
        print("-" * 50)
