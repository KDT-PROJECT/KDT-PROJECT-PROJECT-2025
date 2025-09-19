"""
통합 검색 서비스
지능형 검색, 이미지 검색, 비디오 검색 기능을 제공합니다.
"""

import logging
import os
import requests
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from infrastructure.logging_service import StructuredLogger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IntegratedSearchService:
    """통합 검색 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.logger = StructuredLogger("integrated_search_service")
        
        # API 키 설정
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # 데이터베이스 설정
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "seoul_commercial"),
            "port": int(os.getenv("DB_PORT", "3306"))
        }
        
        self.logger.info("통합 검색 서비스가 초기화되었습니다.")
    
    def intelligent_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        지능형 검색: MySQL과 웹에서 최적의 데이터를 찾아 분석하고 시각화
        
        Args:
            query: 검색 질의
            max_results: 최대 결과 수
            
        Returns:
            검색 결과와 분석 데이터
        """
        try:
            self.logger.info(f"지능형 검색 시작: {query}")
            
            # 1. MySQL 데이터베이스에서 관련 데이터 검색
            db_results = self._search_database(query)
            
            # 2. 웹에서 관련 정보 검색
            web_results = self._search_web(query, max_results)
            
            # 3. LLM을 사용하여 데이터 분석 및 통합
            analysis = self._analyze_with_llm(query, db_results, web_results)
            
            # 4. 시각화 데이터 생성
            visualizations = self._create_visualizations(db_results, web_results)
            
            return {
                "status": "success",
                "query": query,
                "database_results": db_results,
                "web_results": web_results,
                "analysis": analysis,
                "visualizations": visualizations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"지능형 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
    
    def image_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        이미지 검색: 질의와 관련된 이미지를 찾아줍니다.
        
        Args:
            query: 검색 질의
            max_results: 최대 결과 수
            
        Returns:
            이미지 검색 결과
        """
        try:
            self.logger.info(f"이미지 검색 시작: {query}")
            
            # Serper API를 사용한 이미지 검색
            if not self.serper_api_key:
                return {
                    "status": "error",
                    "message": "Serper API 키가 설정되지 않았습니다."
                }
            
            # 이미지 검색을 위한 쿼리 최적화
            image_query = f"{query} 이미지 사진"
            
            # Serper API 호출
            url = "https://google.serper.dev/images"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": image_query,
                "num": max_results
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 결과 처리
            images = []
            if "images" in data:
                for img in data["images"]:
                    images.append({
                        "title": img.get("title", ""),
                        "url": img.get("imageUrl", ""),
                        "source": img.get("source", ""),
                        "width": img.get("width", 0),
                        "height": img.get("height", 0)
                    })
            
            return {
                "status": "success",
                "query": query,
                "images": images,
                "total_count": len(images),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"이미지 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
    
    def video_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        비디오 검색: 질의와 관련된 유튜브나 네이버 영상을 검색합니다.
        
        Args:
            query: 검색 질의
            max_results: 최대 결과 수
            
        Returns:
            비디오 검색 결과
        """
        try:
            self.logger.info(f"비디오 검색 시작: {query}")
            
            # 1. YouTube 검색
            youtube_results = self._search_youtube(query, max_results // 2)
            
            # 2. 네이버 비디오 검색 (웹 검색을 통해)
            naver_results = self._search_naver_video(query, max_results // 2)
            
            # 3. 결과 통합
            all_videos = youtube_results + naver_results
            
            return {
                "status": "success",
                "query": query,
                "videos": all_videos,
                "youtube_count": len(youtube_results),
                "naver_count": len(naver_results),
                "total_count": len(all_videos),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"비디오 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
    
    def _search_database(self, query: str) -> Dict[str, Any]:
        """데이터베이스에서 관련 데이터 검색"""
        try:
            # 간단한 키워드 기반 검색
            # 실제로는 더 정교한 검색 로직이 필요합니다.
            
            # 예시: 상권 데이터 검색
            search_terms = query.lower().split()
            
            # 데이터베이스 연결 및 검색
            from utils.dao import run_sql
            
            # 기본 검색 쿼리
            sql_query = """
            SELECT * FROM seoul_commercial_data 
            WHERE 상권명 LIKE '%{}%' 
            OR 업종명 LIKE '%{}%'
            LIMIT 50
            """.format(search_terms[0] if search_terms else "", 
                      search_terms[1] if len(search_terms) > 1 else "")
            
            result = run_sql(sql_query, self.db_config)
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "data": result["results"],
                    "count": len(result["results"])
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "데이터베이스 검색 실패")
                }
                
        except Exception as e:
            self.logger.error(f"데이터베이스 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _search_web(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """웹에서 관련 정보 검색"""
        try:
            if not self.serper_api_key:
                return []
            
            # Serper API를 사용한 웹 검색
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": max_results
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 결과 처리
            results = []
            if "organic" in data:
                for item in data["organic"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "web"
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"웹 검색 오류: {e}")
            return []
    
    def _analyze_with_llm(self, query: str, db_results: Dict[str, Any], web_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """LLM을 사용하여 데이터 분석 및 통합"""
        try:
            # 간단한 분석 로직 (실제로는 LLM API 호출)
            analysis = {
                "summary": f"'{query}'에 대한 검색 결과를 분석했습니다.",
                "key_insights": [],
                "recommendations": []
            }
            
            # 데이터베이스 결과 분석
            if db_results.get("status") == "success" and db_results.get("count", 0) > 0:
                analysis["key_insights"].append(f"데이터베이스에서 {db_results['count']}개의 관련 데이터를 찾았습니다.")
            
            # 웹 결과 분석
            if web_results:
                analysis["key_insights"].append(f"웹에서 {len(web_results)}개의 관련 정보를 찾았습니다.")
            
            # 추천사항 생성
            if db_results.get("count", 0) > 0 and web_results:
                analysis["recommendations"].append("데이터베이스와 웹 정보를 종합하여 더 정확한 분석을 수행할 수 있습니다.")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM 분석 오류: {e}")
            return {
                "summary": "분석 중 오류가 발생했습니다.",
                "key_insights": [],
                "recommendations": []
            }
    
    def _create_visualizations(self, db_results: Dict[str, Any], web_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시각화 데이터 생성"""
        try:
            visualizations = {}
            
            # 데이터베이스 결과 시각화
            if db_results.get("status") == "success" and db_results.get("data"):
                df = pd.DataFrame(db_results["data"])
                
                # 숫자 컬럼이 있는 경우 차트 생성
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    # 막대 차트
                    fig_bar = px.bar(df.head(10), x=df.columns[0], y=numeric_cols[0], 
                                   title="데이터베이스 검색 결과")
                    visualizations["database_chart"] = fig_bar.to_json()
            
            # 웹 결과 시각화
            if web_results:
                # 소스별 분포 차트
                sources = [result.get("source", "unknown") for result in web_results]
                source_counts = pd.Series(sources).value_counts()
                
                fig_pie = px.pie(values=source_counts.values, names=source_counts.index,
                               title="웹 검색 결과 소스별 분포")
                visualizations["web_chart"] = fig_pie.to_json()
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"시각화 생성 오류: {e}")
            return {}
    
    def _search_youtube(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """YouTube 검색"""
        try:
            if not self.serper_api_key:
                return []
            
            # YouTube 검색을 위한 쿼리
            youtube_query = f"{query} site:youtube.com"
            
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": youtube_query,
                "num": max_results
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 결과 처리
            videos = []
            if "organic" in data:
                for item in data["organic"]:
                    if "youtube.com" in item.get("link", ""):
                        videos.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "description": item.get("snippet", ""),
                            "source": "YouTube"
                        })
            
            return videos
            
        except Exception as e:
            self.logger.error(f"YouTube 검색 오류: {e}")
            return []
    
    def _search_naver_video(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """네이버 비디오 검색"""
        try:
            if not self.serper_api_key:
                return []
            
            # 네이버 비디오 검색을 위한 쿼리
            naver_query = f"{query} site:tv.naver.com"
            
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": naver_query,
                "num": max_results
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 결과 처리
            videos = []
            if "organic" in data:
                for item in data["organic"]:
                    if "tv.naver.com" in item.get("link", ""):
                        videos.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "description": item.get("snippet", ""),
                            "source": "Naver TV"
                        })
            
            return videos
            
        except Exception as e:
            self.logger.error(f"네이버 비디오 검색 오류: {e}")
            return []


# 전역 인스턴스
_integrated_search_service = None

def get_integrated_search_service() -> IntegratedSearchService:
    """통합 검색 서비스 인스턴스 반환"""
    global _integrated_search_service
    if _integrated_search_service is None:
        _integrated_search_service = IntegratedSearchService()
    return _integrated_search_service
