"""
Web Search RAG for Seoul Commercial Analysis System
웹 검색을 통한 RAG (Retrieval Augmented Generation) 시스템
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
import logging

# .env 파일 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)


class WebSearchRAG:
    """웹 검색을 활용한 RAG 시스템"""
    
    def __init__(self):
        """웹 검색 RAG 시스템 초기화"""
        # API 키 로드
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # 설정값 로드
        self.max_results = int(os.getenv('MAX_SEARCH_RESULTS', 10))
        self.user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        
        # API 키 검증 (선택적)
        self._validate_api_keys()
    
    def _validate_api_keys(self):
        """필요한 API 키들이 설정되었는지 확인"""
        required_keys = {
            'SERPER_API_KEY': self.serper_api_key,
            'TAVILY_API_KEY': self.tavily_api_key,
            'OPENAI_API_KEY': self.openai_api_key
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        
        if missing_keys:
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
            logger.info("웹 검색 기능이 제한될 수 있습니다.")
        else:
            logger.info("✓ 모든 API 키가 정상적으로 로드되었습니다.")
    
    def search_with_serper(self, query: str, num_results: int = None) -> List[Dict]:
        """Google Serper API를 사용한 웹 검색"""
        if not self.serper_api_key:
            logger.warning("Serper API 키가 설정되지 않았습니다.")
            return []
            
        if not num_results:
            num_results = self.max_results
            
        url = "https://google.serper.dev/search"
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": "kr",  # 한국 결과
            "hl": "ko"   # 한국어
        }
        
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # 검색 결과 파싱
            if 'organic' in data:
                for item in data['organic']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'serper',
                        'score': 0.8  # 기본 점수
                    })
            
            logger.info(f"✓ Serper API: {len(results)}개 결과 검색 완료")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Serper API 오류: {e}")
            return []
    
    def search_with_tavily(self, query: str, num_results: int = None) -> List[Dict]:
        """Tavily API를 사용한 AI 기반 웹 검색"""
        if not self.tavily_api_key:
            logger.warning("Tavily API 키가 설정되지 않았습니다.")
            return []
            
        if not num_results:
            num_results = self.max_results
            
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": True,
            "max_results": num_results,
            "include_domains": [],
            "exclude_domains": []
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Tavily 결과 파싱
            if 'results' in data:
                for item in data['results']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('url', ''),
                        'snippet': item.get('content', ''),
                        'raw_content': item.get('raw_content', ''),
                        'score': item.get('score', 0.9),  # Tavily 점수 사용
                        'source': 'tavily'
                    })
            
            logger.info(f"✓ Tavily API: {len(results)}개 결과 검색 완료")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Tavily API 오류: {e}")
            return []
    
    def combined_search(self, query: str, use_both: bool = True) -> List[Dict]:
        """Serper와 Tavily를 함께 사용한 통합 검색"""
        all_results = []
        
        if use_both and self.serper_api_key and self.tavily_api_key:
            # 두 API 모두 사용
            serper_results = self.search_with_serper(query, 5)
            tavily_results = self.search_with_tavily(query, 5)
            
            all_results.extend(serper_results)
            all_results.extend(tavily_results)
        elif self.tavily_api_key:
            # Tavily 우선
            tavily_results = self.search_with_tavily(query)
            if tavily_results:
                all_results = tavily_results
            elif self.serper_api_key:
                logger.info("Tavily 실패, Serper로 대체 검색...")
                all_results = self.search_with_serper(query)
        elif self.serper_api_key:
            # Serper만 사용
            all_results = self.search_with_serper(query)
        else:
            logger.warning("사용 가능한 검색 API가 없습니다.")
            return []
        
        # 중복 URL 제거
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result.get('link', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        logger.info(f"✓ 총 {len(unique_results)}개 고유 검색 결과")
        return unique_results
    
    def search_commercial_data(self, query: str, area: str = None, industry: str = None) -> List[Dict]:
        """상권 분석에 특화된 웹 검색"""
        # 상권 분석 관련 키워드 추가
        enhanced_query = query
        
        if area:
            enhanced_query = f"{area} {enhanced_query}"
        
        if industry:
            enhanced_query = f"{industry} {enhanced_query}"
        
        # 상권 분석 관련 키워드 추가
        commercial_keywords = [
            "상권분석", "매출데이터", "업종별매출", "지역별상권",
            "서울상권", "강남상권", "서초상권", "상권동향",
            "창업지원", "스타트업", "상권정보"
        ]
        
        # 쿼리에 상권 관련 키워드가 없으면 추가
        if not any(keyword in enhanced_query for keyword in commercial_keywords):
            enhanced_query = f"{enhanced_query} 상권분석"
        
        return self.combined_search(enhanced_query)
    
    def scrape_content(self, url: str) -> str:
        """웹 페이지 내용 스크래핑"""
        try:
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            # 간단한 HTML 파싱 (실제로는 BeautifulSoup 사용 권장)
            content = response.text
            
            # 내용 길이 제한
            max_length = int(os.getenv('MAX_CONTENT_LENGTH', 10000))
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"✗ 스크래핑 오류 ({url}): {e}")
            return ""
    
    def get_search_summary(self, results: List[Dict]) -> Dict:
        """검색 결과 요약 정보 생성"""
        if not results:
            return {
                'total_results': 0,
                'sources': [],
                'summary': '검색 결과가 없습니다.'
            }
        
        sources = list(set([result.get('source', 'unknown') for result in results]))
        
        # 간단한 요약 생성
        titles = [result.get('title', '') for result in results if result.get('title')]
        summary = f"총 {len(results)}개의 검색 결과를 찾았습니다. "
        summary += f"주요 소스: {', '.join(sources)}"
        
        return {
            'total_results': len(results),
            'sources': sources,
            'summary': summary,
            'top_titles': titles[:3]  # 상위 3개 제목
        }


def create_web_search_rag() -> WebSearchRAG:
    """웹 검색 RAG 인스턴스 생성"""
    return WebSearchRAG()


# 전역 인스턴스
_web_search_rag = None

def get_web_search_rag() -> WebSearchRAG:
    """전역 웹 검색 RAG 인스턴스 반환"""
    global _web_search_rag
    if _web_search_rag is None:
        _web_search_rag = WebSearchRAG()
    return _web_search_rag


if __name__ == "__main__":
    # 환경변수 확인
    print("=== 환경변수 확인 ===")
    required_vars = [
        'SERPER_API_KEY', 'TAVILY_API_KEY', 'OPENAI_API_KEY',
        'MAX_SEARCH_RESULTS', 'USER_AGENT', 'REQUEST_TIMEOUT'
    ]
    
    for var in required_vars:
        value = os.getenv(var, 'Not set')
        if 'API_KEY' in var:
            # API 키는 앞 4자리만 표시
            display_value = value[:4] + "..." if len(value) > 4 else "Not set"
        else:
            display_value = value
        print(f"{var}: {display_value}")
    
    print("\n=== 웹 검색 RAG 테스트 ===")
    
    try:
        # RAG 시스템 초기화
        rag = WebSearchRAG()
        
        # 검색 쿼리
        query = "서울 강남구 상권분석 2024"
        
        # 통합 검색 실행
        results = rag.search_commercial_data(query, area="강남구")
        
        # 결과 출력
        print(f"\n검색 결과 ({len(results)}개):")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['link']}")
            print(f"   요약: {result['snippet'][:100]}...")
            print(f"   출처: {result['source']}")
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        print("\n.env 파일에 필요한 API 키들이 모두 설정되어 있는지 확인하세요!")
