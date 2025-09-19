"""
외부 데이터 포털 연동 서비스
data_sites.txt에 있는 데이터 포털 사이트들을 활용한 외부 데이터 수집 및 통합
"""

import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class ExternalDataResult:
    """외부 데이터 결과 클래스"""
    title: str
    content: str
    source: str
    url: str
    data_type: str
    timestamp: str
    relevance_score: float
    metadata: Dict[str, Any]

class ExternalDataPortal:
    """외부 데이터 포털 클래스"""
    
    def __init__(self, name: str, base_url: str, api_endpoints: Dict[str, str] = None):
        self.name = name
        self.base_url = base_url
        self.api_endpoints = api_endpoints or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def search_data(self, query: str, max_results: int = 10) -> List[ExternalDataResult]:
        """데이터 검색"""
        raise NotImplementedError

class SeoulDataPortal(ExternalDataPortal):
    """서울시 데이터 포털"""
    
    def __init__(self):
        super().__init__(
            name="서울시 데이터 포털",
            base_url="https://data.seoul.go.kr",
            api_endpoints={
                "search": "/dataList/openApiList.do",
                "dataset": "/dataList/openApiDetail.do"
            }
        )
    
    def search_data(self, query: str, max_results: int = 10) -> List[ExternalDataResult]:
        """서울시 데이터 검색"""
        try:
            results = []
            
            # 서울시 공공데이터 검색
            search_url = f"{self.base_url}/dataList/openApiList.do"
            params = {
                "searchCondition": "all",
                "searchKeyword": query,
                "pageSize": max_results
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 데이터셋 목록 추출
                data_items = soup.find_all('div', class_='data-item') or soup.find_all('li', class_='dataset-item')
                
                for item in data_items[:max_results]:
                    title_elem = item.find('h3') or item.find('a', class_='title') or item.find('strong')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link_elem = item.find('a')
                        url = link_elem.get('href') if link_elem else ""
                        
                        # 설명 추출
                        desc_elem = item.find('p', class_='description') or item.find('div', class_='desc')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        results.append(ExternalDataResult(
                            title=title,
                            content=description,
                            source="서울시 데이터 포털",
                            url=urljoin(self.base_url, url) if url else "",
                            data_type="dataset",
                            timestamp=datetime.now().isoformat(),
                            relevance_score=0.8,
                            metadata={"portal": "seoul", "query": query}
                        ))
            
            logger.info(f"서울시 데이터 포털 검색 완료: '{query}' -> {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"서울시 데이터 포털 검색 실패: {str(e)}")
            return []

class DataGoKrPortal(ExternalDataPortal):
    """공공데이터포털"""
    
    def __init__(self):
        super().__init__(
            name="공공데이터포털",
            base_url="https://www.data.go.kr",
            api_endpoints={
                "search": "/api/action/datastore_search",
                "dataset": "/data/15001000/fileData.do"
            }
        )
    
    def search_data(self, query: str, max_results: int = 10) -> List[ExternalDataResult]:
        """공공데이터포털 검색"""
        try:
            results = []
            
            # 공공데이터포털 검색 API
            search_url = f"{self.base_url}/tcs/dss/selectDataSetList.do"
            params = {
                "searchWord": query,
                "pageSize": max_results,
                "pageIndex": 1
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 데이터셋 목록 추출
                data_items = soup.find_all('div', class_='result-item') or soup.find_all('li', class_='dataset')
                
                for item in data_items[:max_results]:
                    title_elem = item.find('h3') or item.find('a', class_='title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link_elem = item.find('a')
                        url = link_elem.get('href') if link_elem else ""
                        
                        # 설명 추출
                        desc_elem = item.find('p', class_='description') or item.find('div', class_='summary')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        results.append(ExternalDataResult(
                            title=title,
                            content=description,
                            source="공공데이터포털",
                            url=urljoin(self.base_url, url) if url else "",
                            data_type="dataset",
                            timestamp=datetime.now().isoformat(),
                            relevance_score=0.9,
                            metadata={"portal": "data_go_kr", "query": query}
                        ))
            
            logger.info(f"공공데이터포털 검색 완료: '{query}' -> {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"공공데이터포털 검색 실패: {str(e)}")
            return []

class KaggleDataPortal(ExternalDataPortal):
    """Kaggle 데이터 포털"""
    
    def __init__(self):
        super().__init__(
            name="Kaggle",
            base_url="https://www.kaggle.com",
            api_endpoints={
                "search": "/api/v1/datasets/search",
                "dataset": "/api/v1/datasets/download"
            }
        )
    
    def search_data(self, query: str, max_results: int = 10) -> List[ExternalDataResult]:
        """Kaggle 데이터 검색"""
        try:
            results = []
            
            # Kaggle API를 통한 데이터셋 검색 (API 키가 필요한 경우)
            # 여기서는 웹 스크래핑 방식으로 구현
            search_url = f"{self.base_url}/datasets/search"
            params = {
                "q": query,
                "sortBy": "relevance",
                "size": "all",
                "fileType": "csv"
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 데이터셋 목록 추출
                data_items = soup.find_all('div', class_='sc-1nqj7lj-0') or soup.find_all('div', class_='dataset-item')
                
                for item in data_items[:max_results]:
                    title_elem = item.find('h3') or item.find('a', class_='title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link_elem = item.find('a')
                        url = link_elem.get('href') if link_elem else ""
                        
                        # 설명 추출
                        desc_elem = item.find('p', class_='description') or item.find('div', class_='summary')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        results.append(ExternalDataResult(
                            title=title,
                            content=description,
                            source="Kaggle",
                            url=urljoin(self.base_url, url) if url else "",
                            data_type="dataset",
                            timestamp=datetime.now().isoformat(),
                            relevance_score=0.85,
                            metadata={"portal": "kaggle", "query": query}
                        ))
            
            logger.info(f"Kaggle 데이터 검색 완료: '{query}' -> {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"Kaggle 데이터 검색 실패: {str(e)}")
            return []

class ExternalDataService:
    """외부 데이터 통합 서비스"""
    
    def __init__(self):
        self.portals = {
            "seoul": SeoulDataPortal(),
            "data_go_kr": DataGoKrPortal(),
            "kaggle": KaggleDataPortal(),
        }
        self.cache = {}
        self.cache_ttl = 3600  # 1시간 캐시
    
    def search_all_portals(self, query: str, max_results_per_portal: int = 5) -> List[ExternalDataResult]:
        """모든 포털에서 데이터 검색"""
        try:
            all_results = []
            
            for portal_name, portal in self.portals.items():
                try:
                    # 캐시 확인
                    cache_key = f"{portal_name}_{query}_{max_results_per_portal}"
                    if cache_key in self.cache:
                        cached_data, timestamp = self.cache[cache_key]
                        if time.time() - timestamp < self.cache_ttl:
                            logger.info(f"캐시에서 결과 반환: {portal_name}")
                            all_results.extend(cached_data)
                            continue
                    
                    # 포털별 검색 실행
                    results = portal.search_data(query, max_results_per_portal)
                    all_results.extend(results)
                    
                    # 캐시 저장
                    self.cache[cache_key] = (results, time.time())
                    
                    # 요청 간격 조절
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"{portal_name} 포털 검색 실패: {str(e)}")
                    continue
            
            # 결과 정렬 및 중복 제거
            unique_results = self._deduplicate_results(all_results)
            sorted_results = self._sort_by_relevance(unique_results, query)
            
            logger.info(f"전체 외부 데이터 검색 완료: '{query}' -> {len(sorted_results)}개 결과")
            return sorted_results
            
        except Exception as e:
            logger.error(f"외부 데이터 검색 실패: {str(e)}")
            return []
    
    def search_specific_portal(self, portal_name: str, query: str, max_results: int = 10) -> List[ExternalDataResult]:
        """특정 포털에서 데이터 검색"""
        try:
            if portal_name not in self.portals:
                logger.error(f"지원하지 않는 포털: {portal_name}")
                return []
            
            portal = self.portals[portal_name]
            results = portal.search_data(query, max_results)
            
            logger.info(f"{portal_name} 포털 검색 완료: '{query}' -> {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"{portal_name} 포털 검색 실패: {str(e)}")
            return []
    
    def get_portal_list(self) -> List[Dict[str, str]]:
        """사용 가능한 포털 목록 반환"""
        return [
            {"name": name, "display_name": portal.name, "base_url": portal.base_url}
            for name, portal in self.portals.items()
        ]
    
    def _deduplicate_results(self, results: List[ExternalDataResult]) -> List[ExternalDataResult]:
        """결과 중복 제거"""
        seen_titles = set()
        unique_results = []
        
        for result in results:
            # 제목 기반 중복 제거
            title_key = result.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(result)
        
        return unique_results
    
    def _sort_by_relevance(self, results: List[ExternalDataResult], query: str) -> List[ExternalDataResult]:
        """관련성 순으로 정렬"""
        def relevance_score(result):
            score = result.relevance_score
            
            # 제목에 쿼리 키워드가 포함된 경우 점수 추가
            title_lower = result.title.lower()
            query_lower = query.lower()
            
            if query_lower in title_lower:
                score += 0.2
            
            # 내용에 쿼리 키워드가 포함된 경우 점수 추가
            content_lower = result.content.lower()
            if query_lower in content_lower:
                score += 0.1
            
            return score
        
        return sorted(results, key=relevance_score, reverse=True)
    
    def get_data_content(self, url: str) -> Optional[str]:
        """데이터 URL에서 실제 내용 추출"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # HTML 파싱하여 텍스트 추출
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # 텍스트 추출
            text = soup.get_text()
            
            # 정리
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # 최대 5000자로 제한
            
        except Exception as e:
            logger.error(f"데이터 내용 추출 실패 {url}: {str(e)}")
            return None

# 전역 서비스 인스턴스
_external_data_service = None

def get_external_data_service() -> ExternalDataService:
    """외부 데이터 서비스 인스턴스 반환"""
    global _external_data_service
    if _external_data_service is None:
        _external_data_service = ExternalDataService()
    return _external_data_service

def search_external_data(query: str, max_results: int = 15, portal: str = None) -> List[Dict[str, Any]]:
    """
    외부 데이터 검색 함수
    
    Args:
        query: 검색 질의
        max_results: 최대 결과 수
        portal: 특정 포털 검색 (선택사항)
        
    Returns:
        검색 결과 리스트
    """
    service = get_external_data_service()
    
    if portal:
        results = service.search_specific_portal(portal, query, max_results)
    else:
        results = service.search_all_portals(query, max_results // len(service.portals))
    
    # ExternalDataResult를 Dict로 변환
    return [
        {
            "title": result.title,
            "content": result.content,
            "source": result.source,
            "url": result.url,
            "data_type": result.data_type,
            "timestamp": result.timestamp,
            "relevance_score": result.relevance_score,
            "metadata": result.metadata
        }
        for result in results[:max_results]
    ]

def get_available_portals() -> List[Dict[str, str]]:
    """사용 가능한 포털 목록 반환"""
    service = get_external_data_service()
    return service.get_portal_list()
