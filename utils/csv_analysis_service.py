"""
CSV 분석 서비스
사용자 질의에 대해 CSV 파일을 검색하고 분석하는 서비스
"""

import logging
import os
import pandas as pd
import glob
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import re

from infrastructure.logging_service import StructuredLogger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CSVAnalysisService:
    """CSV 분석 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.logger = StructuredLogger("csv_analysis_service")
        
        # CSV 파일 경로 설정
        self.csv_folder = "data/csv"
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = os.path.join(self.project_root, self.csv_folder)
        
        # API 키 설정
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        self.logger.info("CSV 분석 서비스가 초기화되었습니다.")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        사용자 질의를 분석하여 CSV 데이터와 웹 데이터를 종합 분석
        
        Args:
            query: 사용자 질의
            
        Returns:
            분석 결과와 시각화 데이터
        """
        try:
            self.logger.info(f"질의 분석 시작: {query}")
            
            # 1. 로컬 CSV 파일 검색
            local_csv_results = self._search_local_csv_files(query)
            
            # 2. 웹에서 CSV/Excel 파일 검색
            web_csv_results = self._search_web_csv_files(query)
            
            # 3. LLM을 사용하여 데이터 선별 및 분석
            analysis_result = self._analyze_with_llm(query, local_csv_results, web_csv_results)
            
            # 4. 대시보드 시각화 데이터 생성
            dashboard_data = self._create_dashboard_visualization(analysis_result)
            
            return {
                "status": "success",
                "query": query,
                "local_csv_results": local_csv_results,
                "web_csv_results": web_csv_results,
                "analysis": analysis_result,
                "dashboard": dashboard_data,
                "metadata": {
                    "local_files_count": len(local_csv_results.get("files", [])),
                    "web_files_count": len(web_csv_results.get("files", [])),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"질의 분석 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
    
    def _search_local_csv_files(self, query: str) -> Dict[str, Any]:
        """로컬 CSV 파일에서 관련 데이터 검색"""
        try:
            self.logger.info("로컬 CSV 파일 검색 시작")
            
            # CSV 파일 목록 가져오기
            csv_files = self._get_csv_file_list()
            
            relevant_files = []
            search_terms = self._extract_search_terms(query)
            
            for file_info in csv_files:
                # 파일명과 내용에서 관련성 검사
                relevance_score = self._calculate_relevance_score(file_info, search_terms, query)
                
                if relevance_score > 0.3:  # 임계값 설정
                    # CSV 파일 내용 분석
                    file_analysis = self._analyze_csv_file(file_info["path"], query)
                    
                    if file_analysis["has_relevant_data"]:
                        relevant_files.append({
                            "file_name": file_info["name"],
                            "file_path": file_info["path"],
                            "relevance_score": relevance_score,
                            "analysis": file_analysis,
                            "source": "local_csv"
                        })
            
            # 관련성 점수로 정렬
            relevant_files.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "status": "success",
                "files": relevant_files[:5],  # 상위 5개 파일만 반환
                "total_files_scanned": len(csv_files)
            }
            
        except Exception as e:
            self.logger.error(f"로컬 CSV 파일 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    def _search_web_csv_files(self, query: str) -> Dict[str, Any]:
        """웹에서 CSV/Excel 파일 검색"""
        try:
            self.logger.info("웹 CSV/Excel 파일 검색 시작")
            
            if not self.serper_api_key:
                return {
                    "status": "error",
                    "message": "Serper API 키가 설정되지 않았습니다.",
                    "files": []
                }
            
            # 웹 검색 쿼리 최적화
            web_query = f"{query} filetype:csv OR filetype:xlsx OR filetype:xls"
            
            # Serper API 호출
            import requests
            
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": web_query,
                "num": 10
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 결과 처리
            web_files = []
            if "organic" in data:
                for item in data["organic"]:
                    url = item.get("link", "")
                    if any(ext in url.lower() for ext in ['.csv', '.xlsx', '.xls']):
                        web_files.append({
                            "title": item.get("title", ""),
                            "url": url,
                            "snippet": item.get("snippet", ""),
                            "source": "web",
                            "file_type": self._get_file_type_from_url(url)
                        })
            
            return {
                "status": "success",
                "files": web_files,
                "total_results": len(web_files)
            }
            
        except Exception as e:
            self.logger.error(f"웹 CSV 파일 검색 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    def _analyze_with_llm(self, query: str, local_results: Dict[str, Any], web_results: Dict[str, Any]) -> Dict[str, Any]:
        """LLM을 사용하여 데이터 선별 및 분석"""
        try:
            self.logger.info("LLM 분석 시작")
            
            # 데이터 수집
            all_data_sources = []
            
            # 로컬 CSV 데이터
            if local_results.get("status") == "success":
                for file_info in local_results.get("files", []):
                    all_data_sources.append({
                        "type": "local_csv",
                        "name": file_info["file_name"],
                        "path": file_info["file_path"],
                        "relevance_score": file_info["relevance_score"],
                        "analysis": file_info["analysis"],
                        "data_preview": file_info["analysis"].get("data_preview", [])
                    })
            
            # 웹 CSV 데이터
            if web_results.get("status") == "success":
                for file_info in web_results.get("files", []):
                    all_data_sources.append({
                        "type": "web_csv",
                        "name": file_info["title"],
                        "url": file_info["url"],
                        "snippet": file_info["snippet"],
                        "file_type": file_info["file_type"]
                    })
            
            # LLM 분석 (간단한 로직으로 구현, 실제로는 LLM API 호출)
            analysis = self._perform_llm_analysis(query, all_data_sources)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM 분석 오류: {e}")
            return {
                "summary": "분석 중 오류가 발생했습니다.",
                "selected_sources": [],
                "insights": [],
                "recommendations": []
            }
    
    def _create_dashboard_visualization(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """대시보드 시각화 데이터 생성"""
        try:
            dashboard_data = {
                "charts": [],
                "metrics": [],
                "tables": []
            }
            
            # 선택된 데이터 소스에서 시각화 생성
            selected_sources = analysis_result.get("selected_sources", [])
            
            for source in selected_sources:
                if source["type"] == "local_csv" and source.get("data_preview"):
                    # 데이터 시각화 생성
                    chart_data = self._create_chart_from_data(source["data_preview"], source["name"])
                    if chart_data:
                        dashboard_data["charts"].append(chart_data)
                    
                    # 메트릭 생성
                    metrics = self._create_metrics_from_data(source["data_preview"], source["name"])
                    dashboard_data["metrics"].extend(metrics)
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"대시보드 시각화 생성 오류: {e}")
            return {"charts": [], "metrics": [], "tables": []}
    
    def _get_csv_file_list(self) -> List[Dict[str, str]]:
        """CSV 파일 목록 가져오기"""
        try:
            csv_files = []
            
            if os.path.exists(self.csv_path):
                for file_path in glob.glob(os.path.join(self.csv_path, "*.csv")):
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    csv_files.append({
                        "name": file_name,
                        "path": file_path,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            
            return csv_files
            
        except Exception as e:
            self.logger.error(f"CSV 파일 목록 가져오기 오류: {e}")
            return []
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """질의에서 검색 키워드 추출"""
        # 간단한 키워드 추출 로직
        # 실제로는 더 정교한 NLP 처리가 필요
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query.lower())
        
        # 불용어 제거
        stop_words = ['의', '을', '를', '이', '가', '에', '에서', '로', '으로', '와', '과', '는', '은', '도', '만', '까지', '부터']
        keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
        
        return keywords
    
    def _calculate_relevance_score(self, file_info: Dict[str, str], search_terms: List[str], query: str) -> float:
        """파일 관련성 점수 계산"""
        try:
            score = 0.0
            file_name = file_info["name"].lower()
            
            # 파일명에서 키워드 매칭
            for term in search_terms:
                if term in file_name:
                    score += 0.3
            
            # 특정 키워드 가중치
            if any(keyword in file_name for keyword in ['상권', '매출', '분석', '데이터']):
                score += 0.2
            
            if any(keyword in query.lower() for keyword in ['강남', '서초', '송파', '마포']):
                if any(keyword in file_name for keyword in ['강남', '서초', '송파', '마포']):
                    score += 0.3
            
            return min(score, 1.0)  # 최대 1.0으로 제한
            
        except Exception as e:
            self.logger.error(f"관련성 점수 계산 오류: {e}")
            return 0.0
    
    def _analyze_csv_file(self, file_path: str, query: str) -> Dict[str, Any]:
        """CSV 파일 내용 분석"""
        try:
            # CSV 파일 읽기 (처음 몇 행만) - 인코딩 자동 감지
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, nrows=100, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return {
                    "has_relevant_data": False,
                    "error": "파일 인코딩을 읽을 수 없습니다."
                }
            
            # 기본 정보
            analysis = {
                "has_relevant_data": False,
                "columns": list(df.columns),
                "row_count": len(df),
                "data_preview": df.head(5).to_dict('records'),
                "data_types": df.dtypes.to_dict()
            }
            
            # 질의와 관련된 컬럼 찾기
            search_terms = self._extract_search_terms(query)
            relevant_columns = []
            
            for col in df.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in search_terms):
                    relevant_columns.append(col)
            
            if relevant_columns:
                analysis["has_relevant_data"] = True
                analysis["relevant_columns"] = relevant_columns
            
            # 숫자 컬럼이 있는지 확인
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_columns:
                analysis["has_numeric_data"] = True
                analysis["numeric_columns"] = numeric_columns
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"CSV 파일 분석 오류: {e}")
            return {
                "has_relevant_data": False,
                "error": str(e)
            }
    
    def _get_file_type_from_url(self, url: str) -> str:
        """URL에서 파일 타입 추출"""
        if '.csv' in url.lower():
            return 'csv'
        elif '.xlsx' in url.lower():
            return 'xlsx'
        elif '.xls' in url.lower():
            return 'xls'
        else:
            return 'unknown'
    
    def _perform_llm_analysis(self, query: str, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """LLM을 사용한 데이터 분석 (간단한 로직으로 구현)"""
        try:
            # 실제로는 OpenAI나 Anthropic API를 호출해야 함
            # 여기서는 간단한 로직으로 구현
            
            selected_sources = []
            insights = []
            recommendations = []
            
            # 관련성 점수가 높은 소스 선택
            for source in data_sources:
                if source.get("relevance_score", 0) > 0.5:
                    selected_sources.append(source)
            
            # 인사이트 생성
            if selected_sources:
                insights.append(f"총 {len(selected_sources)}개의 관련 데이터 소스를 찾았습니다.")
                
                local_sources = [s for s in selected_sources if s["type"] == "local_csv"]
                web_sources = [s for s in selected_sources if s["type"] == "web_csv"]
                
                if local_sources:
                    insights.append(f"로컬 CSV 파일에서 {len(local_sources)}개의 관련 데이터를 발견했습니다.")
                
                if web_sources:
                    insights.append(f"웹에서 {len(web_sources)}개의 추가 데이터 소스를 찾았습니다.")
            
            # 추천사항 생성
            if selected_sources:
                recommendations.append("선택된 데이터 소스들을 종합하여 분석을 진행합니다.")
                recommendations.append("대시보드에서 시각화된 결과를 확인하세요.")
            
            return {
                "summary": f"'{query}'에 대한 분석이 완료되었습니다.",
                "selected_sources": selected_sources,
                "insights": insights,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"LLM 분석 수행 오류: {e}")
            return {
                "summary": "분석 중 오류가 발생했습니다.",
                "selected_sources": [],
                "insights": [],
                "recommendations": []
            }
    
    def _create_chart_from_data(self, data: List[Dict[str, Any]], source_name: str) -> Optional[Dict[str, Any]]:
        """데이터에서 차트 생성"""
        try:
            if not data:
                return None
            
            df = pd.DataFrame(data)
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_columns) == 0:
                return None
            
            # 첫 번째 숫자 컬럼으로 막대 차트 생성
            y_column = numeric_columns[0]
            x_column = df.columns[0] if df.columns[0] not in numeric_columns else df.columns[1] if len(df.columns) > 1 else None
            
            if x_column:
                return {
                    "type": "bar",
                    "title": f"{source_name} - {x_column}별 {y_column}",
                    "x_column": x_column,
                    "y_column": y_column,
                    "data": data[:10]  # 상위 10개만
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"차트 생성 오류: {e}")
            return None
    
    def _create_metrics_from_data(self, data: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
        """데이터에서 메트릭 생성"""
        try:
            metrics = []
            
            if not data:
                return metrics
            
            df = pd.DataFrame(data)
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            for col in numeric_columns:
                if col in df.columns:
                    value = df[col].sum() if df[col].dtype in ['int64', 'float64'] else len(df)
                    metrics.append({
                        "title": f"{source_name} - {col} 총합",
                        "value": value,
                        "source": source_name
                    })
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"메트릭 생성 오류: {e}")
            return []


# 전역 인스턴스
_csv_analysis_service = None

def get_csv_analysis_service() -> CSVAnalysisService:
    """CSV 분석 서비스 인스턴스 반환"""
    global _csv_analysis_service
    if _csv_analysis_service is None:
        _csv_analysis_service = CSVAnalysisService()
    return _csv_analysis_service
