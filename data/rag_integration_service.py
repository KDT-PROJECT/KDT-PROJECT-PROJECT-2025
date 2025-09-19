"""
RAG 시스템 통합 서비스
MySQL 데이터와 PDF 문서를 활용한 통합 검색 및 분석 서비스
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import numpy as np
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from sentence_transformers import SentenceTransformer
import pandas as pd

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGIntegrationService:
    """RAG 시스템 통합 서비스 클래스"""
    
    def __init__(self, db_config: Dict[str, Any], embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        RAG 통합 서비스 초기화
        
        Args:
            db_config: MySQL 데이터베이스 연결 설정
            embedding_model: 임베딩 모델명
        """
        self.db_config = db_config
        self.embedding_model = embedding_model
        self.connection = None
        self.cursor = None
        self.embedder = None
        
    def connect_database(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("데이터베이스 연결 성공")
            return True
        except Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect_database(self):
        """데이터베이스 연결 해제"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("데이터베이스 연결 해제")
    
    def load_embedding_model(self):
        """임베딩 모델 로드"""
        try:
            self.embedder = SentenceTransformer(self.embedding_model)
            logger.info(f"임베딩 모델 로드 완료: {self.embedding_model}")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            raise
    
    def search_sql_data(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """SQL 데이터 검색"""
        try:
            # 기본 매출 데이터 검색 쿼리
            sql_query = """
            SELECT 
                상권_구분_코드_명,
                상권_코드_명,
                서비스_업종_코드_명,
                기준_년분기_코드,
                당월_매출_금액,
                당월_매출_건수,
                주중_매출_금액,
                주말_매출_금액,
                남성_매출_금액,
                여성_매출_금액
            FROM sales_data_csv
            WHERE 
                상권_구분_코드_명 LIKE %s OR
                상권_코드_명 LIKE %s OR
                서비스_업종_코드_명 LIKE %s
            ORDER BY 당월_매출_금액 DESC
            LIMIT %s
            """
            
            search_term = f"%{query}%"
            self.cursor.execute(sql_query, (search_term, search_term, search_term, limit))
            results = self.cursor.fetchall()
            
            logger.info(f"SQL 데이터 검색 완료: {len(results)}건")
            return results
            
        except Error as e:
            logger.error(f"SQL 데이터 검색 실패: {e}")
            return []
    
    def search_pdf_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """PDF 문서 검색 (벡터 검색) - 질의 유사도 기반 정렬"""
        try:
            # 쿼리 전처리 및 키워드 추출
            processed_query = self._preprocess_query(query)
            query_keywords = self._extract_keywords(processed_query)
            
            # 쿼리 임베딩 생성
            query_embedding = self.embedder.encode(query)
            query_embedding_json = json.dumps(query_embedding.tolist())
            
            # 벡터 유사도 검색 (간단한 구현)
            # 실제로는 벡터 데이터베이스나 전문 검색 엔진 사용 권장
            sql_query = """
            SELECT 
                dc.chunk_id,
                dc.doc_id,
                dc.content,
                dc.metadata,
                pd.file_name,
                pd.title,
                pd.content_type
            FROM document_chunks dc
            JOIN pdf_documents pd ON dc.doc_id = pd.doc_id
            WHERE dc.content LIKE %s
            ORDER BY LENGTH(dc.content) DESC
            LIMIT %s
            """
            
            search_term = f"%{query}%"
            self.cursor.execute(sql_query, (search_term, limit * 2))  # 더 많은 결과를 가져와서 필터링
            results = self.cursor.fetchall()
            
            # 질의 유사도 기반 점수 계산 및 정렬
            scored_results = []
            for result in results:
                content = result.get('content', '')
                title = result.get('title', '')
                
                # 기본 벡터 유사도 점수
                vector_score = 0.8  # 실제로는 코사인 유사도 계산
                
                # 질의 유사도 점수 계산
                query_similarity = self._calculate_query_similarity(query, content)
                title_similarity = self._calculate_query_similarity(query, title)
                
                # 키워드 매칭 점수
                keyword_score = self._calculate_keyword_score(query_keywords, content)
                
                # 종합 점수 계산
                final_score = (
                    vector_score * 0.4 +           # 벡터 유사도
                    query_similarity * 0.3 +       # 내용 유사도
                    title_similarity * 0.2 +       # 제목 유사도
                    keyword_score * 0.1            # 키워드 매칭
                )
                
                result['similarity_score'] = final_score
                result['query_similarity'] = query_similarity
                result['title_similarity'] = title_similarity
                result['keyword_score'] = keyword_score
                
                scored_results.append(result)
            
            # 질의 유사도 순으로 정렬
            scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # 상위 결과만 반환
            top_results = scored_results[:limit]
            
            logger.info(f"PDF 문서 검색 완료: {len(top_results)}건 (질의 유사도 기반 정렬)")
            return top_results
            
        except Error as e:
            logger.error(f"PDF 문서 검색 실패: {e}")
            return []
    
    def hybrid_search(self, query: str, sql_limit: int = 5, pdf_limit: int = 5) -> Dict[str, Any]:
        """하이브리드 검색 (SQL + PDF)"""
        try:
            # SQL 데이터 검색
            sql_results = self.search_sql_data(query, sql_limit)
            
            # PDF 문서 검색
            pdf_results = self.search_pdf_documents(query, pdf_limit)
            
            # 통합 결과 생성
            hybrid_result = {
                'query': query,
                'sql_results': sql_results,
                'pdf_results': pdf_results,
                'total_sql_results': len(sql_results),
                'total_pdf_results': len(pdf_results),
                'search_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"하이브리드 검색 완료: SQL {len(sql_results)}건, PDF {len(pdf_results)}건")
            return hybrid_result
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return {
                'query': query,
                'sql_results': [],
                'pdf_results': [],
                'total_sql_results': 0,
                'total_pdf_results': 0,
                'error': str(e),
                'search_timestamp': datetime.now().isoformat()
            }
    
    def generate_insights(self, sql_data: List[Dict], pdf_data: List[Dict]) -> Dict[str, Any]:
        """데이터 기반 인사이트 생성"""
        try:
            insights = {
                'summary': '',
                'key_findings': [],
                'recommendations': [],
                'data_quality': {}
            }
            
            # SQL 데이터 분석
            if sql_data:
                df = pd.DataFrame(sql_data)
                
                # 매출 분석
                total_sales = df['당월_매출_금액'].sum() if '당월_매출_금액' in df.columns else 0
                avg_sales = df['당월_매출_금액'].mean() if '당월_매출_금액' in df.columns else 0
                max_sales = df['당월_매출_금액'].max() if '당월_매출_금액' in df.columns else 0
                
                insights['data_quality']['sql_records'] = len(sql_data)
                insights['data_quality']['total_sales'] = total_sales
                insights['data_quality']['avg_sales'] = avg_sales
                insights['data_quality']['max_sales'] = max_sales
                
                # 주요 발견사항
                if '상권_구분_코드_명' in df.columns:
                    top_districts = df.groupby('상권_구분_코드_명')['당월_매출_금액'].sum().nlargest(3)
                    insights['key_findings'].append(f"상위 매출 상권구분: {', '.join(top_districts.index.tolist())}")
                
                if '서비스_업종_코드_명' in df.columns:
                    top_industries = df.groupby('서비스_업종_코드_명')['당월_매출_금액'].sum().nlargest(3)
                    insights['key_findings'].append(f"상위 매출 업종: {', '.join(top_industries.index.tolist())}")
            
            # PDF 데이터 분석
            if pdf_data:
                insights['data_quality']['pdf_documents'] = len(pdf_data)
                
                # 문서 유형별 분석
                content_types = [doc.get('content_type', 'unknown') for doc in pdf_data]
                type_counts = {}
                for content_type in content_types:
                    type_counts[content_type] = type_counts.get(content_type, 0) + 1
                
                insights['key_findings'].append(f"관련 문서 유형: {dict(type_counts)}")
                
                # 주요 키워드 추출 (간단한 구현)
                all_content = ' '.join([doc.get('content', '') for doc in pdf_data])
                keywords = self.extract_keywords(all_content)
                if keywords:
                    insights['key_findings'].append(f"주요 키워드: {', '.join(keywords[:5])}")
            
            # 요약 생성
            insights['summary'] = self.generate_summary(insights)
            
            # 추천사항 생성
            insights['recommendations'] = self.generate_recommendations(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"인사이트 생성 실패: {e}")
            return {
                'summary': '인사이트 생성 중 오류가 발생했습니다.',
                'key_findings': [],
                'recommendations': [],
                'error': str(e)
            }
    
    def _preprocess_query(self, query: str) -> str:
        """질의 전처리"""
        try:
            import re
            # 불필요한 문자 제거 및 정규화
            processed = re.sub(r'[^\w\s가-힣]', ' ', query)
            processed = ' '.join(processed.split())
            return processed.lower()
        except Exception as e:
            logger.error(f"질의 전처리 중 오류: {e}")
            return query.lower()
    
    def _extract_keywords(self, query: str) -> List[str]:
        """질의에서 키워드 추출"""
        try:
            # 불용어 제거
            stop_words = {'은', '는', '이', '가', '을', '를', '에', '의', '로', '으로', '와', '과', '도', '만', '부터', '까지', '에서', '에게', '한테', '에게서', '한테서', '의', '것', '수', '등', '및', '또는', '그리고', '하지만', '그러나'}
            words = query.split()
            keywords = [word for word in words if word not in stop_words and len(word) > 1]
            return keywords
        except Exception as e:
            logger.error(f"키워드 추출 중 오류: {e}")
            return query.split()
    
    def _calculate_query_similarity(self, query: str, content: str) -> float:
        """질의와 콘텐츠 간의 유사도 계산"""
        try:
            query_lower = query.lower()
            content_lower = content.lower()
            
            # Jaccard 유사도
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            if not query_words or not content_words:
                return 0.0
            
            intersection = query_words.intersection(content_words)
            union = query_words.union(content_words)
            jaccard_sim = len(intersection) / len(union) if union else 0.0
            
            # 부분 문자열 매칭 점수
            partial_match_score = 0.0
            for query_word in query_words:
                if any(query_word in content_word for content_word in content_words):
                    partial_match_score += 0.5
            partial_match_score = min(partial_match_score / len(query_words), 1.0)
            
            # 최종 유사도
            final_similarity = (jaccard_sim * 0.7 + partial_match_score * 0.3)
            return min(final_similarity, 1.0)

        except Exception as e:
            logger.error(f"질의 유사도 계산 중 오류: {e}")
            return 0.0
    
    def _calculate_keyword_score(self, keywords: List[str], content: str) -> float:
        """키워드 매칭 점수 계산"""
        try:
            if not keywords:
                return 0.0
            
            content_lower = content.lower()
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            return matches / len(keywords)

        except Exception as e:
            logger.error(f"키워드 점수 계산 중 오류: {e}")
            return 0.0

    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """텍스트에서 키워드 추출 (간단한 구현)"""
        try:
            # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용)
            words = text.split()
            word_counts = {}
            
            for word in words:
                if len(word) > 2:  # 2글자 이상만
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # 빈도순으로 정렬
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            return [word for word, count in sorted_words[:top_k]]
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return []
    
    def generate_summary(self, insights: Dict[str, Any]) -> str:
        """인사이트 요약 생성"""
        try:
            summary_parts = []
            
            # 데이터 품질 정보
            data_quality = insights.get('data_quality', {})
            if data_quality:
                if 'sql_records' in data_quality:
                    summary_parts.append(f"총 {data_quality['sql_records']}건의 매출 데이터를 분석했습니다.")
                
                if 'pdf_documents' in data_quality:
                    summary_parts.append(f"총 {data_quality['pdf_documents']}개의 관련 문서를 검토했습니다.")
            
            # 주요 발견사항
            key_findings = insights.get('key_findings', [])
            if key_findings:
                summary_parts.append("주요 발견사항:")
                for finding in key_findings[:3]:  # 상위 3개만
                    summary_parts.append(f"- {finding}")
            
            return " ".join(summary_parts) if summary_parts else "분석 결과가 없습니다."
            
        except Exception as e:
            logger.error(f"요약 생성 실패: {e}")
            return "요약 생성 중 오류가 발생했습니다."
    
    def generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """추천사항 생성"""
        try:
            recommendations = []
            
            data_quality = insights.get('data_quality', {})
            
            # 매출 데이터 기반 추천
            if 'total_sales' in data_quality and data_quality['total_sales'] > 0:
                recommendations.append("매출 데이터를 활용한 상세 분석을 권장합니다.")
            
            # PDF 문서 기반 추천
            if 'pdf_documents' in data_quality and data_quality['pdf_documents'] > 0:
                recommendations.append("관련 정책 문서를 참고하여 전략을 수립하세요.")
            
            # 일반적인 추천
            recommendations.extend([
                "정기적인 데이터 업데이트를 통해 최신 정보를 유지하세요.",
                "다양한 관점에서 데이터를 분석해보세요.",
                "전문가와의 상담을 통해 인사이트를 검증하세요."
            ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"추천사항 생성 실패: {e}")
            return ["추천사항 생성 중 오류가 발생했습니다."]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 정보 조회"""
        try:
            stats = {}
            
            # 테이블별 레코드 수 조회
            tables = ['commercial_districts', 'commercial_areas', 'service_industries', 
                     'sales_data', 'pdf_documents', 'document_chunks']
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = self.cursor.fetchone()
                stats[table] = result['count'] if result else 0
            
            # 매출 데이터 통계
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(sales_amount) as total_sales,
                    AVG(sales_amount) as avg_sales,
                    MAX(sales_amount) as max_sales,
                    MIN(sales_amount) as min_sales
                FROM sales_data
            """)
            sales_stats = self.cursor.fetchone()
            stats['sales_statistics'] = sales_stats
            
            # PDF 문서 통계
            self.cursor.execute("""
                SELECT 
                    content_type,
                    COUNT(*) as count
                FROM pdf_documents
                GROUP BY content_type
            """)
            pdf_stats = self.cursor.fetchall()
            stats['pdf_statistics'] = pdf_stats
            
            return stats
            
        except Error as e:
            logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {}
    
    def run_integration_test(self) -> bool:
        """통합 서비스 테스트"""
        try:
            logger.info("RAG 통합 서비스 테스트 시작")
            
            # 1. 데이터베이스 연결
            if not self.connect_database():
                return False
            
            # 2. 임베딩 모델 로드
            self.load_embedding_model()
            
            # 3. 데이터베이스 통계 조회
            stats = self.get_database_stats()
            logger.info(f"데이터베이스 통계: {stats}")
            
            # 4. 테스트 검색
            test_query = "강남구 매출"
            hybrid_result = self.hybrid_search(test_query, sql_limit=3, pdf_limit=3)
            logger.info(f"테스트 검색 결과: {hybrid_result}")
            
            # 5. 인사이트 생성
            insights = self.generate_insights(
                hybrid_result['sql_results'],
                hybrid_result['pdf_results']
            )
            logger.info(f"생성된 인사이트: {insights}")
            
            logger.info("RAG 통합 서비스 테스트 완료")
            return True
            
        except Exception as e:
            logger.error(f"RAG 통합 서비스 테스트 실패: {e}")
            return False
        finally:
            self.disconnect_database()


def main():
    """메인 실행 함수"""
    # 데이터베이스 설정
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'seoul_commercial',
        'port': 3306,
        'charset': 'utf8mb4'
    }
    
    # RAG 통합 서비스 실행
    rag_service = RAGIntegrationService(db_config)
    success = rag_service.run_integration_test()
    
    if success:
        print("✅ RAG 통합 서비스 테스트 완료!")
    else:
        print("❌ RAG 통합 서비스 테스트 실패!")


if __name__ == "__main__":
    main()
