"""
Tab Components for Seoul Commercial Analysis System
TASK-004: Streamlit 프런트엔드(UI/UX) 구현 - 탭 컴포넌트
"""

import logging
import os
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from infrastructure.logging_service import StructuredLogger
from utils.ui_components import get_ui_components

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TabComponents:
    """Tab components for the Streamlit application."""

    def __init__(self):
        """Initialize tab components."""
        self.logger = StructuredLogger("tab_components")
        self.ui_components = get_ui_components()

    def render_sql_tab(self, app):
        """Render enhanced SQL analysis tab with CSV analysis."""
        try:
            st.subheader("📊 스마트 데이터 분석")
            st.write("자연어 질의를 입력하면 로컬 CSV 파일과 웹 데이터를 자동으로 검색하여 종합 분석합니다.")

            # Main query section
            with st.container():
                st.markdown("### 🧠 지능형 데이터 분석")
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    user_query = st.text_input(
                        "분석하고 싶은 내용을 자연어로 입력하세요:",
                        placeholder="예: 강남구 소매업 2024년 매출 분석, 서울 상권 트렌드 비교",
                        key="smart_analysis_input",
                        help="질의를 입력하면 자동으로 관련 CSV 파일과 웹 데이터를 찾아 분석합니다."
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    analyze_button = st.button("🔍 스마트 분석", type="primary", use_container_width=True)
            
            # Analysis options
            with st.expander("분석 옵션"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    include_visualization = st.checkbox("시각화 포함", value=True, key="smart_analysis_viz")
                
                with col2:
                    include_web_search = st.checkbox("웹 데이터 검색", value=True, key="smart_analysis_web")
                
                with col3:
                    max_sources = st.slider("최대 데이터 소스 수", 3, 10, 5, key="smart_analysis_sources")
            
            # Execute analysis
            if analyze_button and user_query:
                self._execute_smart_analysis(app, user_query, include_visualization, include_web_search, max_sources)
            
            # Show recent results
            self._show_recent_analysis_results()

        except Exception as e:
            self.logger.error(f"Error rendering SQL tab: {e}")
            st.error("SQL 탭 렌더링 중 오류가 발생했습니다.")

    def _render_web_csv_importer(self, app):
        """Renders the UI for importing CSV from the web."""
        try:
            search_query = st.text_input(
                "찾고 싶은 데이터에 대한 키워드를 입력하세요 (예: 서울시 인구 통계)",
                key="csv_search_query"
            )

            if st.button("🔍 CSV 파일 검색", key="search_csv_button"):
                if search_query:
                    with st.spinner("웹에서 CSV 파일을 검색 중입니다..."):
                        from utils.web_search_client import WebSearchClient
                        client = WebSearchClient()
                        results = client.search_for_csv_files(search_query)
                        st.session_state['csv_search_results'] = results
                        if not results:
                            st.warning("관련 CSV 파일을 찾지 못했습니다. 다른 키워드로 시도해보세요.")
                else:
                    st.warning("검색어를 입력해주세요.")

            if 'csv_search_results' in st.session_state and st.session_state['csv_search_results']:
                results = st.session_state['csv_search_results']
                
                options = {f"{res['title']} ({res['url']})": res['url'] for res in results}
                selected_option = st.selectbox(
                    "데이터베이스에 추가할 CSV 파일을 선택하세요.",
                    options.keys()
                )
                selected_url = options[selected_option]

                table_name = st.text_input(
                    "데이터베이스에 저장할 테이블 이름을 입력하세요.",
                    key="db_table_name",
                    help="영문, 숫자, 밑줄(_)만 사용 가능합니다."
                ).lower().replace(" ", "_")

                if st.button("📥 데이터베이스로 가져오기", key="import_csv_button"):
                    if not selected_url or not table_name:
                        st.warning("URL과 테이블 이름을 모두 입력해주세요.")
                        return

                    with st.spinner(f"'{table_name}' 테이블로 데이터를 가져오는 중..."):
                        try:
                            data_service = app.data_integration_service
                            if data_service is None:
                                st.error("데이터 통합 서비스를 초기화할 수 없습니다.")
                                return

                            result = data_service.load_csv_from_web_to_db(selected_url, table_name)
                            
                            if result.get('success'):
                                st.success(result.get('message', '성공적으로 가져왔습니다.'))
                                st.info(f"가져온 행 수: {result.get('rows_imported', 0)}")
                                with st.expander("컬럼 이름 변경 내역 보기"):
                                    st.json(result.get('renamed_columns', {}))
                                if 'csv_search_results' in st.session_state:
                                    del st.session_state['csv_search_results']
                                st.rerun() # Refresh the UI to show new state
                            else:
                                st.error(result.get('message', '알 수 없는 오류가 발생했습니다.'))

                        except Exception as e:
                            self.logger.error(f"데이터 가져오기 실패: {e}", exc_info=True)
                            st.error(f"데이터를 가져오는 중 심각한 오류가 발생했습니다: {e}")

        except Exception as e:
            self.logger.error(f"웹 CSV 가져오기 UI 렌더링 오류: {e}", exc_info=True)
            st.error("웹 CSV 가져오기 UI를 렌더링하는 중 오류가 발생했습니다.")

    def _show_available_data_sources(self):
        """Show available data sources for natural language querying."""
        try:
            # Check for imported data
            if 'last_imported_table' in st.session_state:
                table_info = st.session_state['last_imported_table']
                st.info(f"📊 사용 가능한 데이터: {table_info['table_name']} 테이블 ({table_info['file_type'].upper()}, {table_info['rows']}행, {table_info['columns']}열)")
            
            # Check for SQL analysis results
            if hasattr(st.session_state, 'last_sql_df') and st.session_state.last_sql_df is not None:
                df = st.session_state.last_sql_df
                st.info(f"📈 SQL 분석 결과: {len(df)}행 {len(df.columns)}열 데이터")
                
            # Show available tables in database
            try:
                from utils.data_integration import get_data_integration_service
                data_service = get_data_integration_service()
                db_stats = data_service.get_database_stats()
                
                if not db_stats.get('error') and db_stats.get('tables'):
                    with st.expander("🗄️ 데이터베이스 테이블 목록"):
                        for table_name, table_info in db_stats['tables'].items():
                            st.write(f"**{table_name}**: {table_info.get('rows', 0)}행, {table_info.get('columns', 0)}열")
            except Exception as e:
                # Database connection might not be available
                pass
                
        except Exception as e:
            self.logger.error(f"Error showing available data sources: {e}")

    def _enhance_query_with_context(self, user_query: str) -> str:
        """Enhance user query with context about available data sources."""
        try:
            context_parts = []
            
            # Add information about imported data
            if 'last_imported_table' in st.session_state:
                table_info = st.session_state['last_imported_table']
                context_parts.append(f"사용 가능한 데이터: {table_info['table_name']} 테이블 ({table_info['rows']}행, {table_info['columns']}열)")
            
            # Add information about existing SQL results
            if hasattr(st.session_state, 'last_sql_df') and st.session_state.last_sql_df is not None:
                df = st.session_state.last_sql_df
                context_parts.append(f"기존 분석 결과: {len(df)}행 {len(df.columns)}열 데이터")
            
            # Add database table information
            try:
                from utils.data_integration import get_data_integration_service
                data_service = get_data_integration_service()
                db_stats = data_service.get_database_stats()
                
                if not db_stats.get('error') and db_stats.get('tables'):
                    table_list = []
                    for table_name, table_info in db_stats['tables'].items():
                        table_list.append(f"{table_name}({table_info.get('rows', 0)}행)")
                    if table_list:
                        context_parts.append(f"데이터베이스 테이블: {', '.join(table_list)}")
            except Exception:
                pass
            
            # Combine context with user query
            if context_parts:
                context = " | ".join(context_parts)
                enhanced_query = f"컨텍스트: {context} | 사용자 질의: {user_query}"
                return enhanced_query
            else:
                return user_query
                
        except Exception as e:
            self.logger.error(f"Error enhancing query with context: {e}")
            return user_query

    def _execute_sql_query(self, app, user_query: str, max_rows: int, timeout: int, show_sql: bool):
        """Execute SQL query with progress tracking."""
        try:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Query validation
            status_text.text("질의 검증 중...")
            progress_bar.progress(10)
            
            # Check for PII and prompt injection
            if not app.pii_guard.is_safe(user_query):
                st.error("개인정보가 포함된 질의는 처리할 수 없습니다.")
                return
            
            if not app.prompt_guard.is_safe(user_query):
                st.error("잘못된 질의 형식입니다.")
                return
            
            # Step 2: Text-to-SQL conversion
            status_text.text("자연어를 SQL로 변환 중...")
            progress_bar.progress(30)
            
            # Enhance query with context about available data
            enhanced_query = self._enhance_query_with_context(user_query)
            
            # Use text-to-SQL service
            sql_result = app.text_to_sql_service.convert_to_sql(enhanced_query)
            
            if not sql_result["success"]:
                st.error(f"SQL 변환 실패: {sql_result.get('error', 'Unknown error')}")
                return
            
            generated_sql = sql_result["sql"]
            
            # Step 3: SQL execution
            status_text.text("SQL 실행 중...")
            progress_bar.progress(60)
            
            # Database configuration from environment variables
            db_config = {
                "host": os.getenv("DB_HOST", "localhost"),
                "user": os.getenv("DB_USER", "seoul_ro"),
                "password": os.getenv("DB_PASSWORD", "seoul_ro_password_2024"),
                "database": os.getenv("DB_NAME", "seoul_commercial"),
                "port": int(os.getenv("DB_PORT", "3306"))
            }
            
            # Execute SQL
            from utils.dao import run_sql
            sql_execution_result = run_sql(generated_sql, db_config)
            
            if sql_execution_result["status"] != "success":
                error_message = sql_execution_result.get('message', 'Unknown error')
                
                # MySQL 연결 오류에 대한 특별한 처리
                if "Access denied" in error_message:
                    st.error("🔐 MySQL 데이터베이스 연결 오류")
                    st.warning("""
                    **MySQL 연결이 거부되었습니다.**
                    
                    다음 중 하나를 확인해주세요:
                    1. MySQL 서비스가 실행 중인지 확인
                    2. MySQL root 사용자의 비밀번호 설정
                    3. `.env` 파일에 올바른 데이터베이스 설정이 있는지 확인
                    
                    **해결 방법:**
                    - MySQL Workbench나 명령줄에서 MySQL에 연결하여 비밀번호를 확인하세요
                    - `.env` 파일에 `DB_PASSWORD=your_mysql_password`를 추가하세요
                    """)
                else:
                    st.error(f"SQL 실행 실패: {error_message}")
                return
            
            # Step 4: Result processing
            status_text.text("결과 처리 중...")
            progress_bar.progress(80)
            
            # Convert to DataFrame
            df = pd.DataFrame(sql_execution_result["results"])
            
            # Step 5: Display results
            status_text.text("완료!")
            progress_bar.progress(100)
            
            # Show success message
            st.success(f"✅ 쿼리가 성공적으로 실행되었습니다. ({len(df)}개 행)")
            
            # Store in session state
            st.session_state.last_sql_df = df
            st.session_state.last_sql_query = generated_sql
            
            # Display results
            self._display_sql_results(df, generated_sql, show_sql, max_rows)
            
            # Clear progress indicators
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            self.logger.error(f"Error executing SQL query: {e}")
            st.error(f"SQL 쿼리 실행 중 오류가 발생했습니다: {str(e)}")

    def _display_sql_results(self, df: pd.DataFrame, sql_query: str, show_sql: bool, max_rows: int):
        """Display SQL query results."""
        try:
            # Show SQL query if requested
            if show_sql:
                with st.expander("실행된 SQL 쿼리", expanded=False):
                    st.code(sql_query, language="sql")
            
            # Display data table
            self.ui_components.render_data_table(df, "분석 결과", max_rows)
            
            # Create charts if data is suitable
            if not df.empty and len(df) > 1:
                self._create_sql_charts(df)
            
            # Download buttons
            self.ui_components.render_download_buttons(df, "sql_analysis")
            
        except Exception as e:
            self.logger.error(f"Error displaying SQL results: {e}")

    def _create_sql_charts(self, df: pd.DataFrame):
        """Create charts from SQL data."""
        try:
            st.subheader("📊 데이터 시각화")
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) == 0:
                st.info("차트를 생성할 수 있는 숫자 데이터가 없습니다.")
                return
            
            # Create tabs for different chart types
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["막대 차트", "선 차트", "파이 차트"])
            
            with chart_tab1:
                if len(numeric_cols) >= 1:
                    # Bar chart
                    x_col = df.columns[0] if df.columns[0] not in numeric_cols else df.columns[1] if len(df.columns) > 1 else None
                    y_col = numeric_cols[0]
                    
                    if x_col:
                        fig = px.bar(df.head(20), x=x_col, y=y_col, title=f"{x_col}별 {y_col}")
                        st.plotly_chart(fig, use_container_width=True)
            
            with chart_tab2:
                if len(numeric_cols) >= 1:
                    # Line chart
                    x_col = df.columns[0] if df.columns[0] not in numeric_cols else df.columns[1] if len(df.columns) > 1 else None
                    y_col = numeric_cols[0]
                    
                    if x_col:
                        fig = px.line(df.head(20), x=x_col, y=y_col, title=f"{x_col}별 {y_col} 트렌드")
                        st.plotly_chart(fig, use_container_width=True)
            
            with chart_tab3:
                if len(numeric_cols) >= 1:
                    # Pie chart
                    x_col = df.columns[0] if df.columns[0] not in numeric_cols else df.columns[1] if len(df.columns) > 1 else None
                    y_col = numeric_cols[0]
                    
                    if x_col:
                        fig = px.pie(df.head(10), names=x_col, values=y_col, title=f"{x_col}별 {y_col} 비율")
                        st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.logger.error(f"Error creating SQL charts: {e}")

    def _show_recent_sql_results(self):
        """Show recent SQL results from session state."""
        try:
            if st.session_state.get("last_sql_df") is not None:
                st.subheader("📊 최근 SQL 결과")
                
                with st.expander("최근 실행된 SQL 결과 보기", expanded=False):
                    df = st.session_state.last_sql_df
                    self.ui_components.render_data_table(df, "", 20)
                    
                    if st.session_state.get("last_sql_query"):
                        st.code(st.session_state.last_sql_query, language="sql")
        
        except Exception as e:
            self.logger.error(f"Error showing recent SQL results: {e}")
    
    def _execute_smart_analysis(self, app, query: str, include_visualization: bool, include_web_search: bool, max_sources: int):
        """Execute smart analysis using CSV analysis service."""
        try:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Query validation
            status_text.text("🔍 질의 분석 중...")
            progress_bar.progress(10)
            
            # Check for PII and prompt injection
            if not app.pii_guard.is_safe(query):
                st.error("개인정보가 포함된 질의는 처리할 수 없습니다.")
                return
            
            if not app.prompt_guard.is_safe(query):
                st.error("잘못된 질의 형식입니다.")
                return
            
            # Step 2: CSV analysis
            status_text.text("📁 로컬 CSV 파일 검색 중...")
            progress_bar.progress(30)
            
            # Get CSV analysis service
            from utils.csv_analysis_service import get_csv_analysis_service
            csv_service = get_csv_analysis_service()
            
            # Execute analysis
            analysis_result = csv_service.analyze_query(query)
            
            if analysis_result["status"] != "success":
                st.error(f"분석 실패: {analysis_result.get('message', 'Unknown error')}")
                return
            
            # Step 3: Display results
            status_text.text("📊 결과 생성 중...")
            progress_bar.progress(80)
            
            # Store in session state
            st.session_state.last_smart_analysis = analysis_result
            
            # Display results
            self._display_smart_analysis_results(analysis_result, include_visualization)
            
            # Step 4: Complete
            status_text.text("✅ 완료!")
            progress_bar.progress(100)
            
            # Clear progress indicators
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            self.logger.error(f"Error executing smart analysis: {e}")
            st.error(f"스마트 분석 중 오류가 발생했습니다: {str(e)}")
    
    def _display_smart_analysis_results(self, analysis_result: Dict[str, Any], include_visualization: bool):
        """Display smart analysis results with dashboard visualization."""
        try:
            st.subheader("🎯 분석 결과")
            
            # Analysis summary
            if analysis_result.get("analysis"):
                analysis = analysis_result["analysis"]
                
                st.markdown("### 📋 분석 요약")
                st.info(analysis.get("summary", ""))
                
                # Key insights
                if analysis.get("insights"):
                    st.markdown("#### 🔍 주요 인사이트")
                    for insight in analysis["insights"]:
                        st.write(f"• {insight}")
                
                # Recommendations
                if analysis.get("recommendations"):
                    st.markdown("#### 💡 추천사항")
                    for rec in analysis["recommendations"]:
                        st.write(f"• {rec}")
            
            # Data sources with metadata
            self._display_data_sources_with_metadata(analysis_result)
            
            # Dashboard visualization
            if include_visualization and analysis_result.get("dashboard"):
                self._display_dashboard_visualization(analysis_result["dashboard"])
            
            # Metadata
            self._display_analysis_metadata(analysis_result.get("metadata", {}))
            
        except Exception as e:
            self.logger.error(f"Error displaying smart analysis results: {e}")
    
    def _display_data_sources_with_metadata(self, analysis_result: Dict[str, Any]):
        """Display data sources with metadata."""
        try:
            st.markdown("### 📊 데이터 소스")
            
            # Local CSV results
            local_results = analysis_result.get("local_csv_results", {})
            if local_results.get("status") == "success" and local_results.get("files"):
                st.markdown("#### 📁 로컬 CSV 파일")
                
                for i, file_info in enumerate(local_results["files"], 1):
                    with st.expander(f"파일 {i}: {file_info['file_name']} (관련도: {file_info['relevance_score']:.2f})"):
                        st.markdown(f"**파일명**: {file_info['file_name']}")
                        st.markdown(f"**경로**: {file_info['file_path']}")
                        st.markdown(f"**관련도 점수**: {file_info['relevance_score']:.2f}")
                        st.markdown(f"**출처**: 로컬 CSV 파일")
                        
                        # File analysis
                        analysis = file_info.get("analysis", {})
                        if analysis.get("columns"):
                            st.markdown(f"**컬럼 수**: {len(analysis['columns'])}")
                            st.markdown(f"**데이터 행 수**: {analysis.get('row_count', 0)}")
                            
                            if analysis.get("relevant_columns"):
                                st.markdown("**관련 컬럼**: " + ", ".join(analysis["relevant_columns"]))
                        
                        # Data preview
                        if analysis.get("data_preview"):
                            st.markdown("**데이터 미리보기**:")
                            preview_df = pd.DataFrame(analysis["data_preview"])
                            st.dataframe(preview_df, use_container_width=True)
            
            # Web CSV results
            web_results = analysis_result.get("web_csv_results", {})
            if web_results.get("status") == "success" and web_results.get("files"):
                st.markdown("#### 🌐 웹 CSV/Excel 파일")
                
                for i, file_info in enumerate(web_results["files"], 1):
                    with st.expander(f"웹 파일 {i}: {file_info['title'][:50]}..."):
                        st.markdown(f"**제목**: {file_info['title']}")
                        st.markdown(f"**URL**: [{file_info['url']}]({file_info['url']})")
                        st.markdown(f"**파일 타입**: {file_info['file_type']}")
                        st.markdown(f"**출처**: 웹 검색")
                        
                        if file_info.get("snippet"):
                            st.markdown("**설명**: " + file_info["snippet"])
            
        except Exception as e:
            self.logger.error(f"Error displaying data sources: {e}")
    
    def _display_dashboard_visualization(self, dashboard_data: Dict[str, Any]):
        """Display dashboard visualization."""
        try:
            st.markdown("### 📈 대시보드")
            
            # Metrics
            if dashboard_data.get("metrics"):
                st.markdown("#### 📊 주요 지표")
                metrics = dashboard_data["metrics"]
                
                # Create columns for metrics
                cols = st.columns(min(len(metrics), 4))
                for i, metric in enumerate(metrics):
                    with cols[i % 4]:
                        st.metric(
                            label=metric["title"],
                            value=metric["value"],
                            help=f"출처: {metric['source']}"
                        )
            
            # Charts
            if dashboard_data.get("charts"):
                st.markdown("#### 📊 데이터 시각화")
                charts = dashboard_data["charts"]
                
                for chart in charts:
                    if chart["type"] == "bar":
                        # Create bar chart
                        df = pd.DataFrame(chart["data"])
                        
                        fig = px.bar(
                            df, 
                            x=chart["x_column"], 
                            y=chart["y_column"],
                            title=chart["title"],
                            color=chart["y_column"],
                            color_continuous_scale="viridis"
                        )
                        
                        fig.update_layout(
                            xaxis_title=chart["x_column"],
                            yaxis_title=chart["y_column"],
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.logger.error(f"Error displaying dashboard visualization: {e}")
    
    def _display_analysis_metadata(self, metadata: Dict[str, Any]):
        """Display analysis metadata."""
        try:
            if metadata:
                with st.expander("📋 분석 메타데이터"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("로컬 파일 수", metadata.get("local_files_count", 0))
                        st.metric("웹 파일 수", metadata.get("web_files_count", 0))
                    
                    with col2:
                        st.metric("분석 시간", metadata.get("analysis_timestamp", "Unknown"))
                        
                        # Download button for analysis report
                        if st.button("📥 분석 보고서 다운로드"):
                            self._download_analysis_report(metadata)
            
        except Exception as e:
            self.logger.error(f"Error displaying analysis metadata: {e}")
    
    def _download_analysis_report(self, metadata: Dict[str, Any]):
        """Download analysis report."""
        try:
            # Create a simple report
            report_content = f"""
# 데이터 분석 보고서

## 분석 정보
- 분석 시간: {metadata.get('analysis_timestamp', 'Unknown')}
- 로컬 파일 수: {metadata.get('local_files_count', 0)}
- 웹 파일 수: {metadata.get('web_files_count', 0)}

## 상세 내용
이 보고서는 스마트 데이터 분석 시스템에 의해 생성되었습니다.
            """
            
            # Download button
            st.download_button(
                label="📄 보고서 다운로드 (.md)",
                data=report_content,
                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error downloading analysis report: {e}")
    
    def _show_recent_analysis_results(self):
        """Show recent analysis results from session state."""
        try:
            if st.session_state.get("last_smart_analysis"):
                st.subheader("📊 최근 분석 결과")
                
                with st.expander("최근 분석 결과 보기", expanded=False):
                    analysis = st.session_state.last_smart_analysis
                    query = analysis.get("query", "Unknown query")
                    
                    st.write(f"**분석 질의**: {query}")
                    
                    # Summary
                    if analysis.get("analysis", {}).get("summary"):
                        st.write(f"**분석 요약**: {analysis['analysis']['summary']}")
                    
                    # Data sources count
                    local_count = analysis.get("metadata", {}).get("local_files_count", 0)
                    web_count = analysis.get("metadata", {}).get("web_files_count", 0)
                    
                    st.write(f"**데이터 소스**: 로컬 {local_count}개, 웹 {web_count}개")
                    
                    # Key insights preview
                    if analysis.get("analysis", {}).get("insights"):
                        st.write("**주요 인사이트**:")
                        for insight in analysis["analysis"]["insights"][:2]:  # Show first 2
                            st.write(f"• {insight}")
        
        except Exception as e:
            self.logger.error(f"Error showing recent analysis results: {e}")

    def render_rag_tab(self, app):
        """Render integrated search tab with 3 functionalities."""
        try:
            st.subheader("🔍 통합 검색")
            st.write("지능형 검색, 이미지 검색, 비디오 검색을 통해 종합적인 정보를 찾습니다.")
            
            # Create sub-tabs for different search types
            search_tab1, search_tab2, search_tab3 = st.tabs([
                "🧠 지능형 검색", 
                "🖼️ 이미지 검색", 
                "🎥 비디오 검색"
            ])
            
            # Tab 1: Intelligent Search
            with search_tab1:
                self._render_intelligent_search(app)
            
            # Tab 2: Image Search
            with search_tab2:
                self._render_image_search(app)
            
            # Tab 3: Video Search
            with search_tab3:
                self._render_video_search(app)
            
            # Show recent results
            self._show_recent_integrated_results()

        except Exception as e:
            self.logger.error(f"Error rendering integrated search tab: {e}")
            st.error("통합 검색 탭 렌더링 중 오류가 발생했습니다.")

    def _execute_web_search(self, app, search_query: str, area: str, industry: str, max_results: int):
        """Execute web search using WebSearchRAG."""
        try:
            with st.spinner("웹 검색 중..."):
                # Get web search RAG service
                from utils.web_search_rag import get_web_search_rag
                web_search_rag = get_web_search_rag()
                
                # Prepare search parameters
                area_param = None if area == "전체" else area
                industry_param = None if industry == "전체" else industry
                
                # Execute search
                results = web_search_rag.search_commercial_data(
                    search_query, 
                    area=area_param, 
                    industry=industry_param
                )
                
                if results:
                    st.success(f"✅ {len(results)}개의 관련 정보를 찾았습니다.")
                    
                    # Store in session state
                    st.session_state.last_web_results = results
                    st.session_state.last_web_query = search_query
                    
                    # Display results
                    self._display_web_results(results)
                    
                    # Show search summary
                    summary = web_search_rag.get_search_summary(results)
                    if summary:
                        with st.expander("검색 요약", expanded=False):
                            st.write(f"**총 결과 수**: {summary['total_results']}개")
                            st.write(f"**검색 소스**: {', '.join(summary['sources'])}")
                            st.write(f"**요약**: {summary['summary']}")
                    
                else:
                    st.warning("관련 정보를 찾을 수 없습니다. 다른 검색어를 시도해보세요.")
                
        except Exception as e:
            self.logger.error(f"Error executing web search: {e}")
            st.error(f"웹 검색 중 오류가 발생했습니다: {str(e)}")

    def _display_web_results(self, results: List[Dict[str, Any]]):
        """Display web search results."""
        try:
            st.subheader("📄 검색 결과")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"결과 {i} - {result.get('title', 'No Title')[:50]}..."):
                    # Title and link
                    st.markdown(f"**제목**: {result.get('title', 'No Title')}")
                    st.markdown(f"**링크**: [{result.get('link', 'No Link')}]({result.get('link', '#')})")
                    
                    # Content snippet
                    st.markdown("**내용 요약:**")
                    snippet = result.get('snippet', 'No content available')
                    st.write(snippet)
                    
                    # Source and score
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("검색 소스", result.get('source', 'Unknown'))
                    
                    with col2:
                        score = result.get('score', 0)
                        st.metric("관련도 점수", f"{score:.3f}")
                    
                    # Raw content if available
                    if result.get('raw_content'):
                        with st.expander("상세 내용", expanded=False):
                            raw_content = result.get('raw_content', '')
                            # Limit content length for display
                            if len(raw_content) > 2000:
                                raw_content = raw_content[:2000] + "..."
                            st.write(raw_content)
                    
                    st.markdown("---")
            
        except Exception as e:
            self.logger.error(f"Error displaying web results: {e}")

    def _render_intelligent_search(self, app):
        """Render intelligent search interface."""
        try:
            st.markdown("### 🧠 지능형 검색")
            st.write("MySQL 데이터베이스와 웹에서 최적의 데이터를 찾아 분석하고 시각화합니다.")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                search_query = st.text_input(
                    "검색할 내용을 입력하세요:",
                    placeholder="예: 강남구 소매업 매출 분석, 서울 상권 트렌드",
                    key="intelligent_search_input",
                    help="MySQL과 웹에서 종합적으로 검색할 키워드를 입력하세요."
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                search_button = st.button("🧠 지능형 검색", type="primary", use_container_width=True)
            
            # Search options
            with st.expander("검색 옵션"):
                col1, col2 = st.columns(2)
                
                with col1:
                    max_results = st.slider("최대 결과 수", 5, 20, 10, key="intelligent_search_results")
                
                with col2:
                    include_visualization = st.checkbox("시각화 포함", value=True, key="intelligent_search_viz")
            
            # Execute intelligent search
            if search_button and search_query:
                self._execute_intelligent_search(app, search_query, max_results, include_visualization)
                
        except Exception as e:
            self.logger.error(f"Error rendering intelligent search: {e}")
            st.error("지능형 검색 렌더링 중 오류가 발생했습니다.")
    
    def _render_image_search(self, app):
        """Render image search interface."""
        try:
            st.markdown("### 🖼️ 이미지 검색")
            st.write("질의와 관련된 이미지를 찾아줍니다.")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                search_query = st.text_input(
                    "이미지를 검색할 내용을 입력하세요:",
                    placeholder="예: 강남구 상권, 서울 스카이라인, 상가 건물",
                    key="image_search_input",
                    help="찾고 싶은 이미지와 관련된 키워드를 입력하세요."
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                search_button = st.button("🖼️ 이미지 검색", type="primary", use_container_width=True)
            
            # Search options
            with st.expander("이미지 검색 옵션"):
                col1, col2 = st.columns(2)
                
                with col1:
                    max_images = st.slider("최대 이미지 수", 5, 20, 10, key="image_search_count")
                
                with col2:
                    image_size = st.selectbox("이미지 크기", ["전체", "큰 이미지", "중간 이미지", "작은 이미지"], key="image_search_size")
            
            # Execute image search
            if search_button and search_query:
                self._execute_image_search(app, search_query, max_images)
                
        except Exception as e:
            self.logger.error(f"Error rendering image search: {e}")
            st.error("이미지 검색 렌더링 중 오류가 발생했습니다.")
    
    def _render_video_search(self, app):
        """Render video search interface."""
        try:
            st.markdown("### 🎥 비디오 검색")
            st.write("질의와 관련된 유튜브나 네이버 영상을 검색합니다.")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                search_query = st.text_input(
                    "비디오를 검색할 내용을 입력하세요:",
                    placeholder="예: 강남구 상권 분석, 서울 창업 가이드, 상가 투자",
                    key="video_search_input",
                    help="찾고 싶은 비디오와 관련된 키워드를 입력하세요."
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                search_button = st.button("🎥 비디오 검색", type="primary", use_container_width=True)
            
            # Search options
            with st.expander("비디오 검색 옵션"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    max_videos = st.slider("최대 비디오 수", 5, 20, 10, key="video_search_count")
                
                with col2:
                    include_youtube = st.checkbox("YouTube 포함", value=True, key="video_search_youtube")
                
                with col3:
                    include_naver = st.checkbox("네이버 TV 포함", value=True, key="video_search_naver")
            
            # Execute video search
            if search_button and search_query:
                self._execute_video_search(app, search_query, max_videos, include_youtube, include_naver)
                
        except Exception as e:
            self.logger.error(f"Error rendering video search: {e}")
            st.error("비디오 검색 렌더링 중 오류가 발생했습니다.")
    
    def _show_recent_integrated_results(self):
        """Show recent integrated search results from session state."""
        try:
            # Intelligent search results
            if st.session_state.get("last_intelligent_search"):
                st.subheader("🧠 최근 지능형 검색 결과")
                
                with st.expander("최근 지능형 검색 결과 보기", expanded=False):
                    results = st.session_state.last_intelligent_search
                    query = results.get("query", "Unknown query")
                    
                    st.write(f"**검색어**: {query}")
                    
                    if results.get("database_results", {}).get("count", 0) > 0:
                        st.write(f"**데이터베이스 결과**: {results['database_results']['count']}개")
                    
                    if results.get("web_results"):
                        st.write(f"**웹 결과**: {len(results['web_results'])}개")
                    
                    if results.get("analysis", {}).get("summary"):
                        st.write(f"**분석 요약**: {results['analysis']['summary']}")
            
            # Image search results
            if st.session_state.get("last_image_search"):
                st.subheader("🖼️ 최근 이미지 검색 결과")
                
                with st.expander("최근 이미지 검색 결과 보기", expanded=False):
                    results = st.session_state.last_image_search
                    query = results.get("query", "Unknown query")
                    
                    st.write(f"**검색어**: {query}")
                    st.write(f"**이미지 수**: {results.get('total_count', 0)}개")
                    
                    # Show first few images
                    images = results.get("images", [])
                    for i, img in enumerate(images[:3], 1):
                        st.markdown(f"**{i}. {img.get('title', 'No Title')[:30]}...**")
                        st.caption(f"출처: {img.get('source', 'Unknown')}")
            
            # Video search results
            if st.session_state.get("last_video_search"):
                st.subheader("🎥 최근 비디오 검색 결과")
                
                with st.expander("최근 비디오 검색 결과 보기", expanded=False):
                    results = st.session_state.last_video_search
                    query = results.get("query", "Unknown query")
                    
                    st.write(f"**검색어**: {query}")
                    st.write(f"**비디오 수**: {results.get('total_count', 0)}개")
                    st.write(f"YouTube: {results.get('youtube_count', 0)}개, 네이버 TV: {results.get('naver_count', 0)}개")
                    
                    # Show first few videos
                    videos = results.get("videos", [])
                    for i, video in enumerate(videos[:3], 1):
                        st.markdown(f"**{i}. {video.get('title', 'No Title')[:30]}...**")
                        st.caption(f"출처: {video.get('source', 'Unknown')}")
        
        except Exception as e:
            self.logger.error(f"Error showing recent integrated results: {e}")
    
    def _execute_intelligent_search(self, app, query: str, max_results: int, include_visualization: bool):
        """Execute intelligent search."""
        try:
            with st.spinner("지능형 검색 중..."):
                # Get integrated search service
                from utils.integrated_search_service import get_integrated_search_service
                search_service = get_integrated_search_service()
                
                # Execute intelligent search
                results = search_service.intelligent_search(query, max_results)
                
                if results["status"] == "success":
                    st.success(f"✅ 지능형 검색이 완료되었습니다.")
                    
                    # Store in session state
                    st.session_state.last_intelligent_search = results
                    
                    # Display results
                    self._display_intelligent_search_results(results, include_visualization)
                    
                else:
                    st.error(f"지능형 검색 실패: {results.get('message', 'Unknown error')}")
                    
        except Exception as e:
            self.logger.error(f"Error executing intelligent search: {e}")
            st.error(f"지능형 검색 중 오류가 발생했습니다: {str(e)}")
    
    def _execute_image_search(self, app, query: str, max_images: int):
        """Execute image search."""
        try:
            with st.spinner("이미지 검색 중..."):
                # Get integrated search service
                from utils.integrated_search_service import get_integrated_search_service
                search_service = get_integrated_search_service()
                
                # Execute image search
                results = search_service.image_search(query, max_images)
                
                if results["status"] == "success":
                    st.success(f"✅ {results['total_count']}개의 이미지를 찾았습니다.")
                    
                    # Store in session state
                    st.session_state.last_image_search = results
                    
                    # Display results
                    self._display_image_search_results(results)
                    
                else:
                    st.error(f"이미지 검색 실패: {results.get('message', 'Unknown error')}")
                    
        except Exception as e:
            self.logger.error(f"Error executing image search: {e}")
            st.error(f"이미지 검색 중 오류가 발생했습니다: {str(e)}")
    
    def _execute_video_search(self, app, query: str, max_videos: int, include_youtube: bool, include_naver: bool):
        """Execute video search."""
        try:
            with st.spinner("비디오 검색 중..."):
                # Get integrated search service
                from utils.integrated_search_service import get_integrated_search_service
                search_service = get_integrated_search_service()
                
                # Execute video search
                results = search_service.video_search(query, max_videos)
                
                if results["status"] == "success":
                    st.success(f"✅ {results['total_count']}개의 비디오를 찾았습니다.")
                    
                    # Store in session state
                    st.session_state.last_video_search = results
                    
                    # Display results
                    self._display_video_search_results(results)
                    
                else:
                    st.error(f"비디오 검색 실패: {results.get('message', 'Unknown error')}")
                    
        except Exception as e:
            self.logger.error(f"Error executing video search: {e}")
            st.error(f"비디오 검색 중 오류가 발생했습니다: {str(e)}")
    
    def _display_intelligent_search_results(self, results: Dict[str, Any], include_visualization: bool):
        """Display intelligent search results."""
        try:
            st.subheader("🧠 지능형 검색 결과")
            
            # Analysis section
            if results.get("analysis"):
                analysis = results["analysis"]
                
                st.markdown("### 📊 분석 결과")
                st.write(analysis.get("summary", ""))
                
                if analysis.get("key_insights"):
                    st.markdown("#### 🔍 주요 인사이트")
                    for insight in analysis["key_insights"]:
                        st.write(f"• {insight}")
                
                if analysis.get("recommendations"):
                    st.markdown("#### 💡 추천사항")
                    for rec in analysis["recommendations"]:
                        st.write(f"• {rec}")
            
            # Database results
            if results.get("database_results") and results["database_results"].get("status") == "success":
                st.markdown("### 🗄️ 데이터베이스 검색 결과")
                db_data = results["database_results"]["data"]
                if db_data:
                    df = pd.DataFrame(db_data)
                    st.dataframe(df.head(10))
                    st.info(f"총 {len(db_data)}개의 데이터베이스 결과를 찾았습니다.")
            
            # Web results
            if results.get("web_results"):
                st.markdown("### 🌐 웹 검색 결과")
                web_results = results["web_results"]
                
                for i, result in enumerate(web_results[:5], 1):
                    with st.expander(f"웹 결과 {i} - {result.get('title', 'No Title')[:50]}..."):
                        st.markdown(f"**제목**: {result.get('title', 'No Title')}")
                        st.markdown(f"**링크**: [{result.get('link', 'No Link')}]({result.get('link', '#')})")
                        st.write(f"**내용**: {result.get('snippet', 'No content available')}")
            
            # Visualizations
            if include_visualization and results.get("visualizations"):
                st.markdown("### 📈 시각화")
                visualizations = results["visualizations"]
                
                if "database_chart" in visualizations:
                    import plotly.graph_objects as go
                    import json
                    fig_data = json.loads(visualizations["database_chart"])
                    fig = go.Figure(fig_data)
                    st.plotly_chart(fig, use_container_width=True)
                
                if "web_chart" in visualizations:
                    import plotly.graph_objects as go
                    import json
                    fig_data = json.loads(visualizations["web_chart"])
                    fig = go.Figure(fig_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
        except Exception as e:
            self.logger.error(f"Error displaying intelligent search results: {e}")
    
    def _display_image_search_results(self, results: Dict[str, Any]):
        """Display image search results."""
        try:
            st.subheader("🖼️ 이미지 검색 결과")
            
            images = results.get("images", [])
            
            if images:
                # Display images in a grid
                cols = st.columns(3)
                
                for i, img in enumerate(images):
                    col_idx = i % 3
                    
                    with cols[col_idx]:
                        st.markdown(f"**{img.get('title', 'No Title')[:30]}...**")
                        
                        # Display image
                        try:
                            st.image(img.get('url', ''), use_container_width=True)
                        except:
                            st.write("이미지를 불러올 수 없습니다.")
                        
                        # Image info
                        st.caption(f"출처: {img.get('source', 'Unknown')}")
                        st.caption(f"크기: {img.get('width', 0)}x{img.get('height', 0)}")
                        
                        # Link to original
                        if img.get('url'):
                            st.markdown(f"[원본 보기]({img['url']})")
                        
                        st.markdown("---")
            else:
                st.info("검색된 이미지가 없습니다.")
                
        except Exception as e:
            self.logger.error(f"Error displaying image search results: {e}")
    
    def _display_video_search_results(self, results: Dict[str, Any]):
        """Display video search results."""
        try:
            st.subheader("🎥 비디오 검색 결과")
            
            videos = results.get("videos", [])
            
            if videos:
                # Summary
                st.info(f"YouTube: {results.get('youtube_count', 0)}개, 네이버 TV: {results.get('naver_count', 0)}개")
                
                # Display videos
                for i, video in enumerate(videos, 1):
                    with st.expander(f"비디오 {i} - {video.get('title', 'No Title')[:50]}..."):
                        st.markdown(f"**제목**: {video.get('title', 'No Title')}")
                        st.markdown(f"**출처**: {video.get('source', 'Unknown')}")
                        st.write(f"**설명**: {video.get('description', 'No description available')}")
                        
                        # Video link
                        if video.get('url'):
                            st.markdown(f"[비디오 보기]({video['url']})")
                        
                        st.markdown("---")
            else:
                st.info("검색된 비디오가 없습니다.")
                
        except Exception as e:
            self.logger.error(f"Error displaying video search results: {e}")

    def render_report_tab(self, app):
        """Render report generation tab."""
        try:
            st.subheader("📋 보고서 생성")
            st.write("SQL 데이터와 문헌 검색 결과를 결합하여 종합 보고서를 생성합니다.")
            
            # Report configuration
            with st.container():
                st.markdown("### ⚙️ 보고서 설정")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    target_area = st.selectbox(
                        "분석 지역",
                        ["전체", "강남구", "서초구", "송파구", "마포구", "용산구"],
                        help="분석할 지역을 선택합니다."
                    )
                
                with col2:
                    target_industry = st.selectbox(
                        "분석 업종",
                        ["전체", "IT", "금융", "의료", "교육", "소매업", "서비스업"],
                        help="분석할 업종을 선택합니다."
                    )
                
                with col3:
                    report_style = st.selectbox(
                        "보고서 스타일",
                        ["executive", "detailed", "summary"],
                        help="보고서의 상세 정도를 선택합니다."
                    )
            
            # Data sources
            with st.container():
                st.markdown("### 📊 데이터 소스")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    use_sql_data = st.checkbox("SQL 데이터 사용", value=True)
                    if use_sql_data and st.session_state.get("last_sql_df") is not None:
                        df = st.session_state.last_sql_df
                        st.success(f"✅ SQL 데이터: {len(df)}개 행")
                    else:
                        st.info("ℹ️ SQL 데이터 없음")
                
                with col2:
                    use_web_data = st.checkbox("웹 검색 데이터 사용", value=True)
                    if use_web_data and st.session_state.get("last_web_results"):
                        results = getattr(st.session_state, 'last_web_results', [])
                        st.success(f"✅ 웹 검색 결과: {len(results)}개")
                    else:
                        st.info("ℹ️ 웹 검색 결과 없음")
            
            # Report options
            with st.expander("고급 옵션"):
                col1, col2 = st.columns(2)
                
                with col1:
                    include_charts = st.checkbox("차트 포함", value=True, key="report_charts")
                
                with col2:
                    include_metadata = st.checkbox("메타데이터 포함", value=True, key="report_metadata")
            
            # Generate report
            col1, col2 = st.columns([1, 1])
            
            with col1:
                generate_button = st.button("📋 보고서 생성", type="primary", use_container_width=True)
            
            with col2:
                if st.button("🔄 새로고침", type="secondary", use_container_width=True):
                    st.rerun()
            
            if generate_button:
                self._generate_report(
                    app, target_area, target_industry, report_style,
                    use_sql_data, use_web_data, include_charts, 
                    include_metadata
                )
            
            # Show recent report
            self._show_recent_report()

        except Exception as e:
            self.logger.error(f"Error rendering report tab: {e}")
            st.error("보고서 생성 탭 렌더링 중 오류가 발생했습니다.")

    def _generate_report(self, app, target_area: str, target_industry: str, 
                        report_style: str, use_sql_data: bool, use_web_data: bool,
                        include_charts: bool, include_metadata: bool):
        """Generate comprehensive report."""
        try:
            with st.spinner("보고서 생성 중..."):
                # Prepare data sources
                sql_df = getattr(st.session_state, 'last_sql_df', None) if use_sql_data else None
                if sql_df is None:
                    sql_df = pd.DataFrame()
                web_results = getattr(st.session_state, 'last_web_results', []) if use_web_data else []
                
                # Generate KPIs
                kpis = {
                    "total_sales": sql_df.get('당월_매출_금액', pd.Series([0])).sum() if '당월_매출_금액' in sql_df.columns else 0,
                    "avg_growth_rate": 0.15,  # Placeholder
                    "avg_transaction": sql_df.get('당월_매출_건수', pd.Series([0])).mean() if '당월_매출_건수' in sql_df.columns else 0,
                    "web_search_count": len(web_results)
                }
                
                # Generate McKinsey-style report using Gemini service
                from llm.gemini_service import get_gemini_service

                gemini_service = get_gemini_service()

                # Prepare analysis data for report generation
                analysis_data = {
                    "query_info": {
                        "target_area": target_area,
                        "target_industry": target_industry,
                        "analysis_timestamp": datetime.now().isoformat()
                    },
                    "quantitative_data": {
                        "sql_results": sql_df.to_dict('records') if not sql_df.empty else [],
                        "kpis": kpis,
                        "data_summary": {
                            "total_records": len(sql_df) if not sql_df.empty else 0,
                            "columns": list(sql_df.columns) if not sql_df.empty else []
                        }
                    },
                    "qualitative_data": {
                        "web_search_results": web_results,
                        "external_sources_count": len(web_results)
                    },
                    "metadata": {
                        "report_style": report_style,
                        "include_charts": include_charts,
                        "include_metadata": include_metadata,
                        "data_sources_used": {
                            "sql_data": use_sql_data and not sql_df.empty,
                            "web_data": use_web_data and len(web_results) > 0
                        }
                    }
                }

                # Generate McKinsey-style report
                report_content = gemini_service.generate_mckinsey_report(
                    analysis_data,
                    report_type="comprehensive"
                )

                # Create report result structure
                report = {
                    "status": "success",
                    "content": report_content,
                    "metadata": analysis_data["metadata"],
                    "data_sources": {
                        "sql_data_used": use_sql_data and not sql_df.empty,
                        "web_data_used": use_web_data and len(web_results) > 0,
                        "total_sql_records": len(sql_df) if not sql_df.empty else 0,
                        "total_web_results": len(web_results)
                    },
                    "kpis": kpis,
                    "generated_at": datetime.now().isoformat()
                }
                
                if report["status"] == "success":
                    st.success("✅ 보고서가 성공적으로 생성되었습니다.")
                    
                    # Store in session state
                    st.session_state.last_report = report
                    
                    # Display report
                    self._display_report(report, include_metadata)
                                        
                else:
                    st.error(f"보고서 생성 오류: {report.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            st.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")

    def _display_report(self, report: Dict[str, Any], include_metadata: bool):
        """Display generated report."""
        try:
            st.subheader("📋 생성된 보고서")
            
            # Display report content
            st.markdown(report["content"])
            
            # Add download buttons
            self._render_report_download_buttons(report["content"])
            
            # Show metadata if requested
            if include_metadata and report.get("metadata"):
                with st.expander("보고서 메타데이터"):
                    st.json(report["metadata"])
            
            # Show data sources
            if report.get("data_sources"):
                with st.expander("데이터 출처"):
                    st.json(report["data_sources"])
            
            # Show KPIs
            if report.get("kpis"):
                with st.expander("주요 성과 지표"):
                    st.json(report["kpis"])
            
        except Exception as e:
            self.logger.error(f"Error displaying report: {e}")
    
    def _render_report_download_buttons(self, report_content: str):
        """Render download buttons for the report."""
        try:
            st.markdown("---")
            st.markdown("### 📥 보고서 다운로드")
            st.info("💡 **맥킨지 컨설팅 스타일** 보고서를 PDF 또는 Word 형식으로 다운로드하세요.")

            # Import the new report export utility
            from utils.report_export import get_report_exporter

            exporter = get_report_exporter()

            # Create download buttons with professional formatting
            exporter.create_download_buttons(
                markdown_content=report_content,
                title="서울_상권_분석_보고서_McKinsey_Style"
            )

            # Installation guide if needed
            if not (exporter.pdf_available and exporter.word_available):
                with st.expander("📋 설치 가이드"):
                    st.code(exporter.get_installation_guide())

        except ImportError as e:
            # Fallback to basic download functionality
            st.markdown("---")
            st.markdown("### 📥 보고서 다운로드")
            st.error(f"다운로드 기능을 로드할 수 없습니다: {str(e)}")

            # Provide basic markdown download
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            st.download_button(
                label="📄 Markdown 다운로드",
                data=report_content,
                file_name=f"서울_상권_분석_보고서_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True
            )
        except Exception as e:
            self.logger.error(f"Error rendering download buttons: {e}")
            st.error(f"다운로드 버튼 생성 중 오류가 발생했습니다: {str(e)}")
            
            # Basic download options
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"seoul_analysis_report_{timestamp}"
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Text download
                st.download_button(
                    label="📄 텍스트 (.txt)",
                    data=report_content,
                    file_name=f"{base_filename}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="텍스트 형식으로 보고서를 다운로드합니다."
                )
            
            with col2:
                # Markdown download
                st.download_button(
                    label="📄 마크다운 (.md)",
                    data=report_content,
                    file_name=f"{base_filename}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="마크다운 형식으로 보고서를 다운로드합니다."
                )
        except Exception as e:
            self.logger.error(f"Error rendering download buttons: {e}")
            st.error(f"다운로드 버튼 생성 중 오류가 발생했습니다: {e}")

    

    def _show_recent_report(self):
        """Show recent report from session state."""
        try:
            if st.session_state.get("last_report"):
                st.subheader("📋 최근 보고서")
                
                with st.expander("최근 생성된 보고서 보기", expanded=False):
                    report = st.session_state.last_report
                    content = report.get("content", "No content available")
                    st.markdown(content[:500] + "..." if len(content) > 500 else content)
                    
                    if st.button("전체 보고서 보기"):
                        st.markdown(content)
        
        except Exception as e:
            self.logger.error(f"Error showing recent report: {e}")



def create_tab_components() -> TabComponents:
    """
    Factory function to create tab components instance.

    Returns:
        TabComponents instance
    """
    return TabComponents()


# Global tab components instance
_tab_components = None

def get_tab_components() -> TabComponents:
    """Get global tab components instance."""
    global _tab_components
    if _tab_components is None:
        _tab_components = TabComponents()
    return _tab_components


if __name__ == "__main__":
    # Test the tab components
    components = TabComponents()
    print("Tab components initialized successfully")
