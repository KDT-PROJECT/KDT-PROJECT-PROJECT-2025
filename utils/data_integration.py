"""
데이터 통합 유틸리티
Streamlit 앱에서 데이터 파이프라인을 활용할 수 있도록 하는 통합 서비스
"""

import logging
from typing import Dict, Any
import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import re

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrationService:
    """데이터 통합 서비스 클래스"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        데이터 통합 서비스 초기화
        
        Args:
            db_config: MySQL 데이터베이스 연결 설정
        """
        self.db_config = db_config
        self._rag_service = None
    
    @property
    def rag_service(self):
        """RAGIntegrationService를 동적으로 로드합니다."""
        if self._rag_service is None:
            from data.rag_integration_service import RAGIntegrationService
            try:
                self._rag_service = RAGIntegrationService(self.db_config)
                logger.info("RAGIntegrationService 초기화 완료")
            except Exception as e:
                logger.error(f"RAGIntegrationService 초기화 실패: {e}")
                self._rag_service = None
        return self._rag_service

    def load_data_from_web_to_db(self, url: str, table_name: str, file_type: str = None) -> Dict[str, Any]:
        """
        웹에서 데이터 파일(CSV, Excel)을 로드하여 데이터베이스에 저장합니다.

        Args:
            url (str): 데이터 파일의 URL.
            table_name (str): 데이터베이스에 저장될 테이블의 이름.
            file_type (str): 파일 형식 ('csv', 'xlsx', 'xls'). None이면 URL에서 자동 감지.

        Returns:
            Dict[str, Any]: 작업 결과 (성공 여부, 메시지 등).
        """
        if not self.rag_service or not self.rag_service.engine:
            self.rag_service.connect_database() # Ensure connection
            if not self.rag_service.engine:
                 return {'success': False, 'message': '데이터베이스 엔진이 초기화되지 않았습니다.'}

        # Sanitize table name to prevent SQL injection
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            return {'success': False, 'message': '테이블 이름은 영문, 숫자, 밑줄(_)만 포함할 수 있습니다.'}

        # Auto-detect file type if not provided
        if file_type is None:
            if url.lower().endswith('.csv'):
                file_type = 'csv'
            elif url.lower().endswith('.xlsx'):
                file_type = 'xlsx'
            elif url.lower().endswith('.xls'):
                file_type = 'xls'
            else:
                return {'success': False, 'message': '지원되지 않는 파일 형식입니다. (CSV, XLSX, XLS만 지원)'}

        try:
            # Load data based on file type
            df = self._load_dataframe_from_url(url, file_type)
            
            if df is None:
                return {'success': False, 'message': f'{file_type.upper()} 파일을 로드할 수 없습니다.'}

            # Clean column names to be database-friendly
            original_columns = df.columns
            df.columns = [re.sub(r'[^a-zA-Z0-9_]', '', col).lower() for col in df.columns]
            renamed_columns = dict(zip(original_columns, df.columns))

            # Save DataFrame to SQL database
            df.to_sql(table_name, self.rag_service.engine, if_exists='replace', index=False)
            
            return {
                'success': True,
                'message': f"'{url}'의 데이터가 '{table_name}' 테이블에 성공적으로 저장되었습니다.",
                'rows_imported': len(df),
                'columns_count': len(df.columns),
                'file_type': file_type,
                'renamed_columns': renamed_columns
            }

        except Exception as e:
            logger.error(f"웹 데이터 로딩 실패: {e}")
            return {'success': False, 'message': f'데이터 파일을 처리하는 중 오류가 발생했습니다: {str(e)}'}
        finally:
            if self.rag_service:
                self.rag_service.disconnect_database()

    def _load_dataframe_from_url(self, url: str, file_type: str) -> pd.DataFrame:
        """
        URL에서 데이터 파일을 로드하여 DataFrame으로 변환합니다.
        
        Args:
            url (str): 파일 URL
            file_type (str): 파일 형식
            
        Returns:
            pd.DataFrame: 로드된 데이터
        """
        try:
            if file_type == 'csv':
                # Try different encodings for CSV
                encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(url, encoding=encoding)
                        logger.info(f"CSV 파일 로드 성공 (인코딩: {encoding})")
                        return df
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.warning(f"CSV 로드 실패 (인코딩: {encoding}): {e}")
                        continue
                        
            elif file_type in ['xlsx', 'xls']:
                # Load Excel file
                df = pd.read_excel(url, engine='openpyxl' if file_type == 'xlsx' else 'xlrd')
                logger.info(f"Excel 파일 로드 성공")
                return df
                
            else:
                logger.error(f"지원되지 않는 파일 형식: {file_type}")
                return None
                
        except Exception as e:
            logger.error(f"데이터 파일 로드 실패: {e}")
            return None

    def load_csv_from_web_to_db(self, url: str, table_name: str) -> Dict[str, Any]:
        """
        웹에서 CSV 파일을 로드하여 데이터베이스에 저장합니다.
        (Legacy method for backward compatibility)

        Args:
            url (str): CSV 파일의 URL.
            table_name (str): 데이터베이스에 저장될 테이블의 이름.

        Returns:
            Dict[str, Any]: 작업 결과 (성공 여부, 메시지 등).
        """
        return self.load_data_from_web_to_db(url, table_name, 'csv')

    @st.cache_data(ttl=300)
    def search_data(_self, query: str, search_type: str = "hybrid", limit: int = 10) -> Dict[str, Any]:
        """
        데이터 검색 (Streamlit 캐시 적용)
        """
        if not _self.rag_service:
            return {'error': 'RAG 서비스가 초기화되지 않았습니다.'}
        
        try:
            if not _self.rag_service.connect_database():
                return {'error': '데이터베이스 연결에 실패했습니다.'}
            
            _self.rag_service.load_embedding_model()
            
            if search_type == "sql":
                sql_results = _self.rag_service.search_sql_data(query, limit)
                result = {'query': query, 'sql_results': sql_results, 'pdf_results': [], 'total_sql_results': len(sql_results), 'total_pdf_results': 0}
            elif search_type == "pdf":
                pdf_results = _self.rag_service.search_pdf_documents(query, limit)
                result = {'query': query, 'sql_results': [], 'pdf_results': pdf_results, 'total_sql_results': 0, 'total_pdf_results': len(pdf_results)}
            else:
                result = _self.rag_service.hybrid_search(query, sql_limit=limit//2, pdf_limit=limit//2)
            
            insights = _self.rag_service.generate_insights(result.get('sql_results', []), result.get('pdf_results', []))
            result['insights'] = insights
            return result
            
        except Exception as e:
            logger.error(f"데이터 검색 실패: {e}")
            return {'error': f'데이터 검색 중 오류가 발생했습니다: {str(e)}'}
        finally:
            if _self.rag_service:
                _self.rag_service.disconnect_database()
    
    @st.cache_data(ttl=600)
    def get_database_stats(_self) -> Dict[str, Any]:
        """데이터베이스 통계 조회 (Streamlit 캐시 적용)"""
        if not _self.rag_service:
            return {'error': 'RAG 서비스가 초기화되지 않았습니다.'}
        
        try:
            if not _self.rag_service.connect_database():
                return {'error': '데이터베이스 연결에 실패했습니다.'}
            
            stats = _self.rag_service.get_database_stats()
            return stats
            
        except Exception as e:
            logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {'error': f'통계 조회 중 오류가 발생했습니다: {str(e)}'}
        finally:
            if _self.rag_service:
                _self.rag_service.disconnect_database()

def get_data_integration_service() -> "DataIntegrationService":
    """데이터 통합 서비스 인스턴스 반환"""
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'seoul_commercial',
        'port': 3306,
        'charset': 'utf8mb4'
    }
    return DataIntegrationService(db_config)