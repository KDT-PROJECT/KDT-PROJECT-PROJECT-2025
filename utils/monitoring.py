"""
모니터링 및 성능평가 모듈
PRD: 백그라운드 모니터링 시스템 (웹 UI에 노출되지 않음)
"""

import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlite3
import threading
from collections import defaultdict, deque
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, db_path: str = "logs/performance.db"):
        """
        성능 모니터 초기화
        
        Args:
            db_path: 성능 데이터 저장 DB 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # 메모리 내 성능 데이터 (실시간)
        self.metrics = {
            'query_times': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'cpu_usage': deque(maxlen=1000),
            'error_count': 0,
            'success_count': 0,
            'total_queries': 0
        }
        
        # 성능 임계값
        self.thresholds = {
            'max_query_time': 3.0,  # 3초
            'max_memory_usage': 80.0,  # 80%
            'max_cpu_usage': 90.0,  # 90%
            'min_success_rate': 0.9  # 90%
        }
        
        # DB 초기화
        self._init_database()
        
        # 백그라운드 모니터링 시작
        self._start_background_monitoring()
    
    def _init_database(self):
        """성능 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 성능 메트릭 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    query_time REAL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    query_type TEXT,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            
            # 시스템 상태 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    memory_total REAL,
                    memory_available REAL,
                    cpu_percent REAL,
                    disk_usage REAL,
                    active_connections INTEGER
                )
            ''')
            
            # 알림 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("성능 모니터링 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {str(e)}")
    
    def _start_background_monitoring(self):
        """백그라운드 모니터링 시작"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    self._check_performance_thresholds()
                    time.sleep(30)  # 30초마다 체크
                except Exception as e:
                    logger.error(f"백그라운드 모니터링 오류: {str(e)}")
                    time.sleep(60)  # 오류 시 1분 대기
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("백그라운드 모니터링 시작")
    
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # CPU 사용률
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 활성 연결 수 (추정)
            active_connections = len(psutil.net_connections())
            
            # 메모리 내 데이터 업데이트
            self.metrics['memory_usage'].append(memory_usage)
            self.metrics['cpu_usage'].append(cpu_usage)
            
            # DB에 저장
            self._save_system_metrics(memory_usage, cpu_usage, disk_usage, active_connections)
            
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {str(e)}")
    
    def _save_system_metrics(self, memory_usage: float, cpu_usage: float, 
                           disk_usage: float, active_connections: int):
        """시스템 메트릭을 DB에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_status 
                (memory_total, memory_available, cpu_percent, disk_usage, active_connections)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                psutil.virtual_memory().total,
                psutil.virtual_memory().available,
                cpu_usage,
                disk_usage,
                active_connections
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"시스템 메트릭 저장 실패: {str(e)}")
    
    def record_query(self, query_type: str, execution_time: float, 
                    success: bool, error_message: str = None):
        """
        쿼리 실행 기록
        
        Args:
            query_type: 쿼리 타입 (sql, rag, web_search 등)
            execution_time: 실행 시간 (초)
            success: 성공 여부
            error_message: 오류 메시지 (실패 시)
        """
        try:
            # 메모리 내 데이터 업데이트
            self.metrics['query_times'].append(execution_time)
            self.metrics['total_queries'] += 1
            
            if success:
                self.metrics['success_count'] += 1
            else:
                self.metrics['error_count'] += 1
            
            # DB에 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (query_time, memory_usage, cpu_usage, query_type, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                execution_time,
                psutil.virtual_memory().percent,
                psutil.cpu_percent(),
                query_type,
                success,
                error_message
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"쿼리 기록: {query_type}, {execution_time:.2f}s, 성공: {success}")
            
        except Exception as e:
            logger.error(f"쿼리 기록 실패: {str(e)}")
    
    def _check_performance_thresholds(self):
        """성능 임계값 체크"""
        try:
            # 평균 쿼리 시간 체크
            if self.metrics['query_times']:
                avg_query_time = np.mean(list(self.metrics['query_times']))
                if avg_query_time > self.thresholds['max_query_time']:
                    self._create_alert('performance', 'warning', 
                                     f'평균 쿼리 시간이 임계값을 초과했습니다: {avg_query_time:.2f}s')
            
            # 메모리 사용률 체크
            if self.metrics['memory_usage']:
                avg_memory = np.mean(list(self.metrics['memory_usage']))
                if avg_memory > self.thresholds['max_memory_usage']:
                    self._create_alert('memory', 'critical', 
                                     f'메모리 사용률이 높습니다: {avg_memory:.1f}%')
            
            # CPU 사용률 체크
            if self.metrics['cpu_usage']:
                avg_cpu = np.mean(list(self.metrics['cpu_usage']))
                if avg_cpu > self.thresholds['max_cpu_usage']:
                    self._create_alert('cpu', 'critical', 
                                     f'CPU 사용률이 높습니다: {avg_cpu:.1f}%')
            
            # 성공률 체크
            if self.metrics['total_queries'] > 0:
                success_rate = self.metrics['success_count'] / self.metrics['total_queries']
                if success_rate < self.thresholds['min_success_rate']:
                    self._create_alert('reliability', 'warning', 
                                     f'성공률이 낮습니다: {success_rate:.1%}')
            
        except Exception as e:
            logger.error(f"성능 임계값 체크 실패: {str(e)}")
    
    def _create_alert(self, alert_type: str, severity: str, message: str):
        """알림 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (alert_type, severity, message)
                VALUES (?, ?, ?)
            ''', (alert_type, severity, message))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"알림 생성: {alert_type} - {message}")
            
        except Exception as e:
            logger.error(f"알림 생성 실패: {str(e)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보 반환"""
        try:
            summary = {
                'total_queries': self.metrics['total_queries'],
                'success_rate': self.metrics['success_count'] / max(self.metrics['total_queries'], 1),
                'avg_query_time': np.mean(list(self.metrics['query_times'])) if self.metrics['query_times'] else 0,
                'p95_query_time': np.percentile(list(self.metrics['query_times']), 95) if self.metrics['query_times'] else 0,
                'avg_memory_usage': np.mean(list(self.metrics['memory_usage'])) if self.metrics['memory_usage'] else 0,
                'avg_cpu_usage': np.mean(list(self.metrics['cpu_usage'])) if self.metrics['cpu_usage'] else 0,
                'error_count': self.metrics['error_count'],
                'active_alerts': self._get_active_alerts_count()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"성능 요약 생성 실패: {str(e)}")
            return {}
    
    def _get_active_alerts_count(self) -> int:
        """활성 알림 수 반환"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE resolved = FALSE 
                AND timestamp > datetime('now', '-1 hour')
            ''')
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"활성 알림 수 조회 실패: {str(e)}")
            return 0
    
    def get_recent_metrics(self, hours: int = 24) -> Dict[str, List]:
        """최근 메트릭 데이터 반환"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, query_time, memory_usage, cpu_usage, query_type, success
                FROM performance_metrics 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            '''.format(hours))
            
            rows = cursor.fetchall()
            conn.close()
            
            metrics = {
                'timestamps': [row[0] for row in rows],
                'query_times': [row[1] for row in rows],
                'memory_usage': [row[2] for row in rows],
                'cpu_usage': [row[3] for row in rows],
                'query_types': [row[4] for row in rows],
                'success': [row[5] for row in rows]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"최근 메트릭 조회 실패: {str(e)}")
            return {}

class QualityEvaluator:
    """품질 평가 클래스"""
    
    def __init__(self):
        """품질 평가기 초기화"""
        self.evaluation_criteria = {
            'sql_accuracy': 0.9,  # SQL 정확도 90% 목표
            'rag_relevance': 0.8,  # RAG 관련성 80% 목표
            'response_time': 3.0,  # 응답 시간 3초 목표
            'user_satisfaction': 4.0  # 사용자 만족도 4.0/5.0 목표
        }
    
    def evaluate_sql_accuracy(self, generated_sql: str, expected_sql: str) -> float:
        """SQL 정확도 평가"""
        try:
            # 간단한 정확도 평가 (실제로는 더 정교한 방법 필요)
            if not generated_sql or not expected_sql:
                return 0.0
            
            # 키워드 매칭
            generated_keywords = set(generated_sql.upper().split())
            expected_keywords = set(expected_sql.upper().split())
            
            if not expected_keywords:
                return 0.0
            
            intersection = generated_keywords.intersection(expected_keywords)
            accuracy = len(intersection) / len(expected_keywords)
            
            return min(accuracy, 1.0)
            
        except Exception as e:
            logger.error(f"SQL 정확도 평가 실패: {str(e)}")
            return 0.0
    
    def evaluate_rag_relevance(self, query: str, retrieved_docs: List[Dict]) -> float:
        """RAG 관련성 평가"""
        try:
            if not retrieved_docs:
                return 0.0
            
            # 간단한 관련성 평가
            query_words = set(query.lower().split())
            total_relevance = 0.0
            
            for doc in retrieved_docs:
                doc_text = (doc.get('title', '') + ' ' + doc.get('snippet', '')).lower()
                doc_words = set(doc_text.split())
                
                if query_words:
                    intersection = query_words.intersection(doc_words)
                    relevance = len(intersection) / len(query_words)
                    total_relevance += relevance
            
            avg_relevance = total_relevance / len(retrieved_docs)
            return min(avg_relevance, 1.0)
            
        except Exception as e:
            logger.error(f"RAG 관련성 평가 실패: {str(e)}")
            return 0.0
    
    def evaluate_response_time(self, start_time: float, end_time: float) -> float:
        """응답 시간 평가"""
        try:
            response_time = end_time - start_time
            target_time = self.evaluation_criteria['response_time']
            
            # 3초 이하면 1.0, 초과하면 감점
            if response_time <= target_time:
                return 1.0
            else:
                # 3초 초과 시 선형 감점 (6초 이상이면 0점)
                penalty = (response_time - target_time) / target_time
                return max(0.0, 1.0 - penalty)
            
        except Exception as e:
            logger.error(f"응답 시간 평가 실패: {str(e)}")
            return 0.0
    
    def get_overall_quality_score(self, sql_accuracy: float, rag_relevance: float, 
                                response_time: float, user_satisfaction: float = 4.0) -> float:
        """전체 품질 점수 계산"""
        try:
            # 가중 평균 계산
            weights = {
                'sql_accuracy': 0.3,
                'rag_relevance': 0.3,
                'response_time': 0.2,
                'user_satisfaction': 0.2
            }
            
            # 사용자 만족도를 0-1 스케일로 변환
            satisfaction_score = user_satisfaction / 5.0
            
            overall_score = (
                sql_accuracy * weights['sql_accuracy'] +
                rag_relevance * weights['rag_relevance'] +
                response_time * weights['response_time'] +
                satisfaction_score * weights['user_satisfaction']
            )
            
            return min(overall_score, 1.0)
            
        except Exception as e:
            logger.error(f"전체 품질 점수 계산 실패: {str(e)}")
            return 0.0

# 전역 모니터링 인스턴스
performance_monitor = PerformanceMonitor()
quality_evaluator = QualityEvaluator()

def get_system_health() -> Dict[str, Any]:
    """시스템 상태 반환 (웹 UI에서 사용)"""
    try:
        summary = performance_monitor.get_performance_summary()
        
        # 상태 결정
        if summary.get('active_alerts', 0) > 0:
            status = 'warning'
        elif summary.get('success_rate', 0) < 0.9:
            status = 'degraded'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {str(e)}")
        return {
            'status': 'error',
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
