"""
평가 대시보드
TASK-016: 평가 스위트 - 정확도/각주율/지연 벤치
Streamlit에서 사용할 수 있는 평가 대시보드 컴포넌트
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from pipelines.eval_suite import EvaluationSuite
from infrastructure.logging_service import LoggingService


class EvaluationDashboard:
    """평가 대시보드 클래스"""

    def __init__(self, config: Dict[str, Any]):
        """
        평가 대시보드 초기화
        
        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.logger = LoggingService().get_system_logger()
        self.eval_suite = EvaluationSuite(config.get("evaluation", {}))

    def render_evaluation_overview(self, results: Dict[str, Any]) -> None:
        """평가 개요 렌더링"""
        st.subheader("📊 평가 개요")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "총 평가 시간",
                f"{results.get('total_evaluation_time', 0):.1f}초"
            )
        
        with col2:
            timestamp = results.get('evaluation_timestamp', 'N/A')
            if timestamp != 'N/A':
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.metric("평가 일시", dt.strftime("%Y-%m-%d %H:%M"))
                except:
                    st.metric("평가 일시", timestamp)
            else:
                st.metric("평가 일시", "N/A")
        
        with col3:
            components = results.get('components', {})
            total_components = len(components)
            st.metric("평가 컴포넌트", f"{total_components}개")
        
        with col4:
            overall_metrics = results.get('overall_metrics', {})
            kpi_perf = overall_metrics.get('kpi_performance', {})
            passed_kpis = sum(1 for status in kpi_perf.values() 
                            if isinstance(status, str) and status == 'PASS')
            total_kpis = sum(1 for key, value in kpi_perf.items() 
                           if key.endswith('_status'))
            success_rate = (passed_kpis / total_kpis * 100) if total_kpis > 0 else 0
            st.metric("KPI 달성률", f"{success_rate:.0f}%")

    def render_kpi_performance(self, results: Dict[str, Any]) -> None:
        """KPI 성과 렌더링"""
        st.subheader("🎯 KPI 성과")
        
        overall_metrics = results.get('overall_metrics', {})
        kpi_perf = overall_metrics.get('kpi_performance', {})
        
        if not kpi_perf:
            st.warning("KPI 성과 데이터가 없습니다.")
            return
        
        # KPI 성과 테이블
        kpi_data = []
        kpi_data.append({
            "지표": "Text-to-SQL 정확도",
            "달성률": f"{kpi_perf.get('sql_accuracy_achieved', 0):.1%}",
            "목표": f"{kpi_perf.get('sql_accuracy_target', 0):.1%}",
            "상태": kpi_perf.get('sql_accuracy_status', 'N/A')
        })
        kpi_data.append({
            "지표": "응답 시간 (P95)",
            "달성률": f"{kpi_perf.get('response_time_achieved', 0):.2f}초",
            "목표": f"≤{kpi_perf.get('response_time_target', 0)}초",
            "상태": kpi_perf.get('response_time_status', 'N/A')
        })
        kpi_data.append({
            "지표": "근거 각주 포함률",
            "달성률": f"{kpi_perf.get('evidence_citation_achieved', 0):.1%}",
            "목표": f"{kpi_perf.get('evidence_citation_target', 0):.1%}",
            "상태": kpi_perf.get('evidence_citation_status', 'N/A')
        })
        
        df_kpi = pd.DataFrame(kpi_data)
        
        # 상태별 색상 적용
        def color_status(val):
            if val == 'PASS':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'FAIL':
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return ''
        
        styled_df = df_kpi.style.applymap(color_status, subset=['상태'])
        st.dataframe(styled_df, use_container_width=True)
        
        # KPI 달성률 차트
        fig = go.Figure()
        
        metrics = ['Text-to-SQL 정확도', '근거 각주 포함률']
        achieved_values = [
            kpi_perf.get('sql_accuracy_achieved', 0),
            kpi_perf.get('evidence_citation_achieved', 0)
        ]
        target_values = [
            kpi_perf.get('sql_accuracy_target', 0),
            kpi_perf.get('evidence_citation_target', 0)
        ]
        
        fig.add_trace(go.Bar(
            name='달성률',
            x=metrics,
            y=achieved_values,
            marker_color=['#28a745' if a >= t else '#dc3545' for a, t in zip(achieved_values, target_values)]
        ))
        
        fig.add_trace(go.Bar(
            name='목표',
            x=metrics,
            y=target_values,
            marker_color='lightblue',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="KPI 달성률 비교",
            xaxis_title="지표",
            yaxis_title="비율",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_component_details(self, results: Dict[str, Any]) -> None:
        """컴포넌트별 상세 결과 렌더링"""
        st.subheader("🔍 컴포넌트별 상세 결과")
        
        components = results.get('components', {})
        
        if not components:
            st.warning("컴포넌트 평가 데이터가 없습니다.")
            return
        
        # Text-to-SQL 결과
        if 'text_to_sql' in components:
            self._render_sql_component(components['text_to_sql'])
        
        # RAG 결과
        if 'rag' in components:
            self._render_rag_component(components['rag'])
        
        # 보고서 생성 결과
        if 'report_generation' in components:
            self._render_report_component(components['report_generation'])

    def _render_sql_component(self, sql_data: Dict[str, Any]) -> None:
        """Text-to-SQL 컴포넌트 결과 렌더링"""
        st.subheader("🔍 Text-to-SQL 평가")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "정확도",
                f"{sql_data.get('accuracy', 0):.1%}"
            )
        
        with col2:
            st.metric(
                "성공한 쿼리",
                f"{sql_data.get('successful_queries', 0)}/{sql_data.get('total_queries', 0)}"
            )
        
        with col3:
            st.metric(
                "평균 응답 시간",
                f"{sql_data.get('avg_response_time', 0):.2f}초"
            )
        
        with col4:
            st.metric(
                "P95 응답 시간",
                f"{sql_data.get('p95_response_time', 0):.2f}초"
            )
        
        # 응답 시간 분포 차트
        response_times = sql_data.get('response_times', [])
        if response_times:
            fig = px.histogram(
                x=response_times,
                nbins=20,
                title="응답 시간 분포",
                labels={'x': '응답 시간 (초)', 'y': '빈도'}
            )
            st.plotly_chart(fig, use_container_width=True)

    def _render_rag_component(self, rag_data: Dict[str, Any]) -> None:
        """RAG 컴포넌트 결과 렌더링"""
        st.subheader("🔍 RAG 평가")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "평균 관련성 점수",
                f"{rag_data.get('avg_relevance_score', 0):.3f}"
            )
        
        with col2:
            st.metric(
                "평균 응답 시간",
                f"{rag_data.get('avg_response_time', 0):.2f}초"
            )
        
        with col3:
            st.metric(
                "P95 응답 시간",
                f"{rag_data.get('p95_response_time', 0):.2f}초"
            )
        
        # 관련성 점수 분포
        relevance_scores = rag_data.get('relevance_scores', [])
        if relevance_scores:
            fig = px.histogram(
                x=relevance_scores,
                nbins=20,
                title="관련성 점수 분포",
                labels={'x': '관련성 점수', 'y': '빈도'}
            )
            st.plotly_chart(fig, use_container_width=True)

    def _render_report_component(self, report_data: Dict[str, Any]) -> None:
        """보고서 생성 컴포넌트 결과 렌더링"""
        st.subheader("🔍 보고서 생성 평가")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "성공률",
                f"{report_data.get('success_rate', 0):.1%}"
            )
        
        with col2:
            st.metric(
                "평균 품질 점수",
                f"{report_data.get('avg_quality_score', 0):.3f}"
            )
        
        with col3:
            st.metric(
                "평균 생성 시간",
                f"{report_data.get('avg_generation_time', 0):.2f}초"
            )
        
        # 품질 점수 분포
        quality_scores = report_data.get('quality_scores', [])
        if quality_scores:
            fig = px.histogram(
                x=quality_scores,
                nbins=20,
                title="품질 점수 분포",
                labels={'x': '품질 점수', 'y': '빈도'}
            )
            st.plotly_chart(fig, use_container_width=True)

    def render_performance_trends(self, results: Dict[str, Any]) -> None:
        """성능 트렌드 렌더링"""
        st.subheader("📈 성능 트렌드")
        
        # 실제 구현에서는 과거 평가 결과들을 로드하여 트렌드를 보여줄 수 있습니다
        # 여기서는 현재 결과만 표시하는 예시를 제공합니다
        
        components = results.get('components', {})
        
        if 'text_to_sql' in components and 'rag' in components:
            sql_data = components['text_to_sql']
            rag_data = components['rag']
            
            # 응답 시간 비교
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Text-to-SQL',
                x=['평균', 'P95'],
                y=[sql_data.get('avg_response_time', 0), sql_data.get('p95_response_time', 0)],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='RAG',
                x=['평균', 'P95'],
                y=[rag_data.get('avg_response_time', 0), rag_data.get('p95_response_time', 0)],
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="컴포넌트별 응답 시간 비교",
                xaxis_title="지표",
                yaxis_title="응답 시간 (초)",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def load_evaluation_results(self, results_path: str) -> Dict[str, Any]:
        """평가 결과 로드"""
        try:
            results_dir = Path(results_path)
            if not results_dir.exists():
                return {}
            
            # 가장 최근 평가 결과 파일 찾기
            result_files = list(results_dir.glob("evaluation_results_*.json"))
            if not result_files:
                return {}
            
            latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"평가 결과 로드 실패: {e}")
            return {}

    def run_evaluation(self, sql_engine=None, rag_engine=None, report_generator=None) -> Dict[str, Any]:
        """평가 실행"""
        try:
            return self.eval_suite.run_comprehensive_evaluation(
                sql_engine=sql_engine,
                rag_engine=rag_engine,
                report_generator=report_generator
            )
        except Exception as e:
            self.logger.error(f"평가 실행 실패: {e}")
            st.error(f"평가 실행 실패: {e}")
            return {}

    def render_evaluation_dashboard(self, results: Dict[str, Any] = None) -> None:
        """평가 대시보드 전체 렌더링"""
        if results is None:
            results = self.load_evaluation_results(
                self.config.get("evaluation", {}).get("results_path", "models/artifacts/evaluation")
            )
        
        if not results:
            st.warning("평가 결과가 없습니다. 평가를 실행해주세요.")
            return
        
        # 평가 개요
        self.render_evaluation_overview(results)
        st.divider()
        
        # KPI 성과
        self.render_kpi_performance(results)
        st.divider()
        
        # 컴포넌트별 상세 결과
        self.render_component_details(results)
        st.divider()
        
        # 성능 트렌드
        self.render_performance_trends(results)
