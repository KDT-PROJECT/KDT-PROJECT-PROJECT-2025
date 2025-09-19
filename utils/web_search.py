"""
웹 검색 모듈 - Tavily 및 Serper API 활용
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.serper_api_key = os.getenv('SERPER_API_KEY')

    def search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Tavily API를 사용한 웹 검색"""
        if not self.tavily_api_key:
            logger.warning("Tavily API key not found")
            return []

        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "include_images": False,
                "include_raw_content": False,
                "max_results": max_results,
                "include_domains": [],
                "exclude_domains": []
            }

            # Add proper headers and connection settings
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Seoul-Startup-Analysis/1.0"
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
                stream=False  # Disable streaming to prevent chunk errors
            )
            response.raise_for_status()

            data = response.json()
            results = []

            # Safely process results with error handling
            for result in data.get('results', []):
                try:
                    results.append({
                        'title': str(result.get('title', '')),
                        'content': str(result.get('content', '')),
                        'url': str(result.get('url', '')),
                        'score': float(result.get('score', 0)),
                        'source': 'tavily'
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping malformed Tavily result: {e}")
                    continue

            logger.info(f"Tavily 검색 완료: {len(results)}개 결과")
            return results

        except requests.exceptions.Timeout:
            logger.error("Tavily API timeout")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily API request error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Tavily 검색 실패: {str(e)}")
            return []

    def search_serper(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Serper API를 사용한 웹 검색"""
        if not self.serper_api_key:
            logger.warning("Serper API key not found")
            return []

        try:
            url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": max_results,
                "hl": "ko",
                "gl": "kr"
            }

            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json",
                "User-Agent": "Seoul-Startup-Analysis/1.0"
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
                stream=False  # Disable streaming to prevent chunk errors
            )
            response.raise_for_status()

            data = response.json()
            results = []

            # Safely process results with error handling
            for result in data.get('organic', []):
                try:
                    results.append({
                        'title': str(result.get('title', '')),
                        'content': str(result.get('snippet', '')),
                        'url': str(result.get('link', '')),
                        'score': 1.0,  # Serper doesn't provide scores
                        'source': 'serper'
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping malformed Serper result: {e}")
                    continue

            logger.info(f"Serper 검색 완료: {len(results)}개 결과")
            return results

        except requests.exceptions.Timeout:
            logger.error("Serper API timeout")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Serper 검색 실패: {str(e)}")
            return []

    def hybrid_web_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Tavily와 Serper를 결합한 하이브리드 웹 검색"""
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to hybrid search")
                return []

            # Tavily와 Serper 각각 절반씩 검색 (안전한 분할)
            half_results = max(1, max_results // 2)

            # 안전하게 각 API 호출
            tavily_results = []
            serper_results = []

            try:
                tavily_results = self.search_tavily(query, half_results)
            except Exception as e:
                logger.warning(f"Tavily search failed in hybrid: {str(e)}")

            try:
                serper_results = self.search_serper(query, half_results)
            except Exception as e:
                logger.warning(f"Serper search failed in hybrid: {str(e)}")

            # 결과 합치기
            all_results = tavily_results + serper_results

            if not all_results:
                logger.warning("No results from both search APIs")
                return []

            # 중복 URL 제거 (안전한 처리)
            seen_urls = set()
            unique_results = []

            for result in all_results:
                try:
                    url = str(result.get('url', ''))
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        # 결과 데이터 검증
                        validated_result = {
                            'title': str(result.get('title', '')),
                            'content': str(result.get('content', '')),
                            'url': url,
                            'score': float(result.get('score', 0)),
                            'source': str(result.get('source', ''))
                        }
                        unique_results.append(validated_result)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping malformed result in hybrid search: {e}")
                    continue

            # 점수 순으로 정렬 (안전한 정렬)
            try:
                unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            except Exception as e:
                logger.warning(f"Failed to sort results: {str(e)}")

            final_results = unique_results[:max_results]
            logger.info(f"하이브리드 검색 완료: {len(final_results)}개 결과")
            return final_results

        except Exception as e:
            logger.error(f"하이브리드 웹 검색 실패: {str(e)}")
            return []

def get_web_search_service() -> WebSearchService:
    """웹 검색 서비스 인스턴스 반환"""
    return WebSearchService()