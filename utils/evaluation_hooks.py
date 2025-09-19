"""
평가 훅스
시스템 성능 및 품질 평가를 위한 훅스
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class EvaluationHooks:
    """평가 훅스 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """평가 훅스 초기화"""
        self.config = config or {}
        self.evaluation_data = []
        
    def log_text_to_sql_query(self, user_query: str, generated_sql: str, 
                             executed_sql: str, execution_time: float, success: bool):
        """Text-to-SQL 쿼리 로깅"""
        try:
            evaluation_record = {
                'timestamp': datetime.now().isoformat(),
                'type': 'text_to_sql',
                'user_query': user_query,
                'generated_sql': generated_sql,
                'executed_sql': executed_sql,
                'execution_time_ms': execution_time,
                'success': success,
                'query_id': f"query_{int(time.time() * 1000)}"
            }
            
            self.evaluation_data.append(evaluation_record)
            logger.info(f"Text-to-SQL 쿼리 로깅: {evaluation_record['query_id']}")

        except Exception as e:
            logger.error(f"Text-to-SQL 쿼리 로깅 중 오류: {e}")
    
    def log_rag_query(self, user_query: str, retrieved_documents: list, 
                     response_time: float, success: bool):
        """RAG 쿼리 로깅"""
        try:
            evaluation_record = {
                'timestamp': datetime.now().isoformat(),
                'type': 'rag',
                'user_query': user_query,
                'retrieved_documents_count': len(retrieved_documents),
                'response_time_ms': response_time,
                'success': success,
                'query_id': f"rag_{int(time.time() * 1000)}"
            }
            
            self.evaluation_data.append(evaluation_record)
            logger.info(f"RAG 쿼리 로깅: {evaluation_record['query_id']}")

        except Exception as e:
            logger.error(f"RAG 쿼리 로깅 중 오류: {e}")
    
    def log_report_generation(self, report_type: str, data_sources: list, 
                            generation_time: float, success: bool):
        """보고서 생성 로깅"""
        try:
            evaluation_record = {
                'timestamp': datetime.now().isoformat(),
                'type': 'report_generation',
                'report_type': report_type,
                'data_sources_count': len(data_sources),
                'generation_time_ms': generation_time,
                'success': success,
                'query_id': f"report_{int(time.time() * 1000)}"
            }
            
            self.evaluation_data.append(evaluation_record)
            logger.info(f"보고서 생성 로깅: {evaluation_record['query_id']}")

        except Exception as e:
            logger.error(f"보고서 생성 로깅 중 오류: {e}")
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """평가 요약 조회"""
        try:
            if not self.evaluation_data:
                return {
                    'total_queries': 0,
                    'success_rate': 0.0,
                    'avg_response_time': 0.0,
                    'query_types': {}
                }
            
            total_queries = len(self.evaluation_data)
            successful_queries = sum(1 for record in self.evaluation_data if record.get('success', False))
            success_rate = successful_queries / total_queries if total_queries > 0 else 0.0
            
            # 평균 응답 시간 계산
            response_times = [record.get('execution_time_ms', 0) for record in self.evaluation_data 
                            if 'execution_time_ms' in record]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # 쿼리 유형별 통계
            query_types = {}
            for record in self.evaluation_data:
                query_type = record.get('type', 'unknown')
                if query_type not in query_types:
                    query_types[query_type] = {'count': 0, 'success': 0}
                query_types[query_type]['count'] += 1
                if record.get('success', False):
                    query_types[query_type]['success'] += 1
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'query_types': query_types,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"평가 요약 조회 중 오류: {e}")
            return {}

    def clear_evaluation_data(self):
        """평가 데이터 초기화"""
        try:
            self.evaluation_data.clear()
            logger.info("평가 데이터가 초기화되었습니다.")

        except Exception as e:
            logger.error(f"평가 데이터 초기화 중 오류: {e}")


def get_evaluation_hooks(config: Dict[str, Any] = None) -> EvaluationHooks:
    """평가 훅스 인스턴스 반환"""
    return EvaluationHooks(config)
