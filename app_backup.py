"""Seoul Commercial Analysis LLM Application"""

import logging
import sys
import time
from pathlib import Path
from typing import Any
from datetime import datetime

import pandas as pd
import streamlit as st

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Apple UI components
from components.apple_components import AppleUI, AppleLayoutManager
from components.enhanced_search_ui import EnhancedSearchUI
from components.enhanced_report_ui import EnhancedReportUI

# Import hybrid search system
from utils.hybrid_search_engine import get_hybrid_search_engine

# Import configuration and services
from infrastructure.cache_service import get_cache_service
from infrastructure.logging_service import StructuredLogger
from llm.gemini_service import get_gemini_service
from llm.text_to_sql import get_text_to_sql_service
from orchestration.query_orchestrator import get_query_orchestrator
from utils.guards import get_pii_guard, get_prompt_guard, get_sql_guard
from pipelines.report_generator import ReportGenerator
from utils.report_composer import ReportComposer
from utils.rag_hybrid import HybridRetrieval
from utils.markdown_output import MarkdownOutput
from utils.dao import run_sql
from utils.evaluation_hooks import get_evaluation_hooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeoulCommercialApp:
    """Seoul Commercial Analysis Streamlit Application"""

    def __init__(self):
        """Initialize the application"""
        self.logger = StructuredLogger("seoul_commercial_app")
        self.cache_service = get_cache_service()
        self.sql_guard = get_sql_guard()
        self.prompt_guard = get_prompt_guard()
        self.pii_guard = get_pii_guard()

        # Lazy loading for expensive services
        self._text_to_sql_service = None
        self._gemini_service = None
        self._query_orchestrator = None
        self._report_generator = None
        self._report_composer = None
        self._hybrid_retrieval = None
        self._markdown_output = None
        self._evaluation_hooks = None
        self._kpi_dashboard = None
        self._hybrid_search_engine = None

        self.logger.info("SeoulCommercialApp initialized")

    @property
    def text_to_sql_service(self):
        """Lazy load text-to-SQL service"""
        if self._text_to_sql_service is None:
            self._text_to_sql_service = get_text_to_sql_service()
        return self._text_to_sql_service

    @property
    def gemini_service(self):
        """Lazy load Gemini service"""
        if self._gemini_service is None:
            self._gemini_service = get_gemini_service()
        return self._gemini_service

    @property
    def query_orchestrator(self):
        """Lazy load query orchestrator"""
        if self._query_orchestrator is None:
            self._query_orchestrator = get_query_orchestrator()
        return self._query_orchestrator

    @property
    def report_generator(self):
        """Lazy load report generator"""
        if self._report_generator is None:
            config = {
                "hf_llm_config": {
                    "model_name": "microsoft/DialoGPT-medium",
                    "context_window": 2048,
                    "max_new_tokens": 1024,
                    "temperature": 0.7,
                },
                "gemini_config": {},
                "report_config": {
                    "template_path": "prompts/report_system_prompt.md"
                }
            }
            self._report_generator = ReportGenerator(config)
        return self._report_generator

    @property
    def report_composer(self):
        """Lazy load report composer"""
        if self._report_composer is None:
            config = {
                "template_config": {
                    "template_path": "prompts/report_templates.md"
                },
                "output_config": {},
                "quality_config": {}
            }
            self._report_composer = ReportComposer(config)
        return self._report_composer

    @property
    def hybrid_retrieval(self):
        """Lazy load hybrid retrieval"""
        if self._hybrid_retrieval is None:
            config = {
                "vector_store_config": {
                    "collection_name": "seoul_documents"
                },
                "embedding_config": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2"
                },
                "chunking_config": {
                    "chunk_size": 512,
                    "chunk_overlap": 50
                },
                "index_path": "models/artifacts/vector_index"
            }
            self._hybrid_retrieval = HybridRetrieval(config)
        return self._hybrid_retrieval

    @property
    def markdown_output(self):
        """Lazy load markdown output"""
        if self._markdown_output is None:
            config = {
                "output_config": {},
                "file_config": {"output_dir": "reports"},
                "format_config": {
                    "include_charts": True,
                    "include_toc": True,
                    "include_metadata": True
                }
            }
            self._markdown_output = MarkdownOutput(config)
        return self._markdown_output

    @property
    def evaluation_hooks(self):
        """Lazy load evaluation hooks"""
        if self._evaluation_hooks is None:
            self._evaluation_hooks = get_evaluation_hooks()
        return self._evaluation_hooks


    @property
    def hybrid_search_engine(self):
        """Lazy load hybrid search engine"""
        if self._hybrid_search_engine is None:
            self._hybrid_search_engine = get_hybrid_search_engine()
        return self._hybrid_search_engine

    def initialize_session_state(self):
        """Initialize Streamlit session state with all required variables"""
        # Basic session state
        session_defaults = {
            "messages": [],
            "query_history": [],
            "session_id": f"session_{int(time.time())}",

            # Data-related session state
            "last_sql_df": None,
            "last_sql_query": "",
            "last_rag_hits": [],
            "last_report": None,
            "last_hybrid_search": None,

            # UI state
            "search_query_input": "",
            "quick_search_triggered": False,

            # Cache and statistics
            "cache_stats": {
                "hits": 0,
                "misses": 0,
                "total_queries": 0
            }
        }

        # Initialize all session state variables safely
        for key, default_value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

        self.logger.info("Session state initialized successfully")

    def render_header(self):
        """Render Apple-style application header"""
        AppleUI.render_hero_header()

    def render_sidebar(self):
        """Render Apple-style sidebar with options"""
        with st.sidebar:
            # Apple-style header
            st.markdown("""
            <div class="apple-card">
                <div class="apple-card-header">
                    <div class="apple-card-icon">⚙️</div>
                    <h3 class="apple-card-title">설정</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Analysis mode selection
            analysis_mode = st.selectbox(
                "🤖 분석 모드",
                ["자동", "SQL 분석", "문서 검색", "혼합 분석"],
                help="자동: AI가 적절한 분석 방법을 선택합니다",
            )

            # Chart type selection
            chart_type = st.selectbox(
                "📊 차트 유형",
                ["막대 차트", "선 차트", "파이 차트", "히트맵"],
                help="데이터 시각화에 사용할 차트 유형을 선택합니다",
            )

            # Advanced options
            with st.expander("🔧 고급 옵션"):
                max_results = st.slider("최대 결과 수", 10, 1000, 100)
                enable_caching = st.checkbox("캐싱 활성화", value=True)
                debug_mode = st.checkbox("디버그 모드", value=False)

            # Cache management with Apple-style metrics
            with st.expander("💾 캐시 관리"):
                cache_stats = self.cache_service.get_stats()

                # Use Apple-style metrics
                AppleUI.render_metric_card(
                    label="캐시 크기",
                    value=f"{cache_stats['cache_size']}/{cache_stats['max_size']}",
                    icon="💾"
                )

                AppleUI.render_metric_card(
                    label="히트율",
                    value=f"{cache_stats['hit_rate']:.1%}",
                    icon="🎯"
                )

                AppleUI.render_metric_card(
                    label="총 요청",
                    value=str(cache_stats['hit_count'] + cache_stats['miss_count']),
                    icon="📊"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if AppleUI.render_button("클리어", "secondary", "🗑️", "cache_clear"):
                        self.cache_service.clear()
                        st.session_state.cache_stats = {"hits": 0, "misses": 0, "total_queries": 0}
                        AppleUI.render_alert("캐시가 클리어되었습니다.", "success")

                with col2:
                    if AppleUI.render_button("새로고침", "secondary", "🔄", "cache_refresh"):
                        st.rerun()

            # Display sidebar stats
            AppleUI.render_sidebar_stats()

            return {
                "analysis_mode": analysis_mode,
                "chart_type": chart_type,
                "max_results": max_results,
                "enable_caching": enable_caching,
                "debug_mode": debug_mode,
            }

    def process_query(self, user_query: str, options: dict[str, Any]) -> dict[str, Any]:
        """Process user query using the orchestrator with caching"""
        try:
            # Check cache first if enabled
            if options.get("enable_caching", True):
                cache_key = f"{user_query}_{options.get('analysis_mode', 'auto')}"
                cached_result = self.cache_service.get(
                    cache_key, 
                    mode="query",
                    analysis_mode=options.get("analysis_mode", "auto")
                )
                
                if cached_result:
                    self.logger.info(f"Cache hit for query: {user_query}")
                    st.session_state.cache_stats["hits"] += 1
                    return cached_result

            # Use the query orchestrator to process the query
            result = self.query_orchestrator.process_query(
                user_query, session_id=st.session_state.session_id
            )

            formatted_result = self._format_orchestrator_result(result, options)
            
            # Cache the result if enabled
            if options.get("enable_caching", True) and formatted_result.get("success"):
                self.cache_service.set(
                    cache_key,
                    mode="query",
                    data=formatted_result,
                    analysis_mode=options.get("analysis_mode", "auto")
                )
                self.logger.info(f"Cached result for query: {user_query}")
            
            # Update cache miss stats
            st.session_state.cache_stats["misses"] += 1

            return formatted_result

        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "질의 처리 중 오류가 발생했습니다.",
            }

    def _format_orchestrator_result(
        self, result: dict[str, Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Format orchestrator result for display"""
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "message": "분석을 완료할 수 없습니다.",
            }

        mode = result["mode"]
        if mode == "sql":
            return self._format_sql_result(result, options)
        elif mode == "rag":
            return self._format_rag_result(result, options)
        elif mode == "mixed":
            return self._format_mixed_result(result, options)
        else:
            return {
                "success": False,
                "error": f"Unknown mode: {mode}",
                "message": "알 수 없는 분석 모드입니다.",
            }

    def _format_sql_result(
        self, result: dict[str, Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Format SQL analysis result"""
        sql_data = result["result"]
        if not sql_data["success"]:
            return {
                "success": False,
                "error": sql_data.get("error", "SQL execution failed"),
                "message": "SQL 분석을 완료할 수 없습니다.",
            }

        # Update session state with SQL results
        if sql_data.get("data"):
            st.session_state.last_sql_df = pd.DataFrame(sql_data["data"])
        
        # Update cache stats
        st.session_state.cache_stats["total_queries"] += 1

        return {
            "success": True,
            "mode": "sql",
            "data": sql_data["data"],
            "sql_query": sql_data.get("sql_query"),
            "message": "SQL 분석이 완료되었습니다.",
        }

    def _format_rag_result(
        self, result: dict[str, Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Format RAG analysis result"""
        rag_data = result["result"]
        if not rag_data["success"]:
            return {
                "success": False,
                "error": rag_data.get("error", "RAG search failed"),
                "message": "문서 검색을 완료할 수 없습니다.",
            }

        # Update session state with RAG results
        if rag_data.get("results"):
            st.session_state.last_rag_hits = rag_data["results"]
        
        # Update cache stats
        st.session_state.cache_stats["total_queries"] += 1

        return {
            "success": True,
            "mode": "rag",
            "documents": rag_data["results"],
            "message": "문서 검색이 완료되었습니다.",
        }

    def _format_mixed_result(
        self, result: dict[str, Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Format mixed analysis result"""
        mixed_data = result["result"]

        # Update session state with mixed results
        if mixed_data.get("sql_result", {}).get("data"):
            st.session_state.last_sql_df = pd.DataFrame(mixed_data["sql_result"]["data"])
        if mixed_data.get("rag_result", {}).get("results"):
            st.session_state.last_rag_hits = mixed_data["rag_result"]["results"]
        if mixed_data.get("gemini_insight"):
            st.session_state.last_report = mixed_data["gemini_insight"]
        
        # Update cache stats
        st.session_state.cache_stats["total_queries"] += 1

        return {
            "success": True,
            "mode": "mixed",
            "sql_data": mixed_data.get("sql_result", {}).get("data"),
            "rag_documents": mixed_data.get("rag_result", {}).get("results"),
            "insights": mixed_data.get("gemini_insight", {}),
            "message": "혼합 분석이 완료되었습니다.",
        }

    def route_intent(self, query: str) -> str:
        """Simple keyword-based intent routing"""
        query_lower = query.lower()

        sql_keywords = [
            "매출",
            "거래",
            "데이터",
            "통계",
            "수치",
            "비교",
            "추이",
            "분석",
        ]
        rag_keywords = [
            "정책",
            "지원",
            "사업",
            "전략",
            "방안",
            "인사이트",
            "보고서",
            "문서",
        ]

        has_sql = any(keyword in query_lower for keyword in sql_keywords)
        has_rag = any(keyword in query_lower for keyword in rag_keywords)

        if has_sql and not has_rag:
            return "sql"
        elif has_rag and not has_sql:
            return "rag"
        else:
            return "mixed"


def main():
    """Main application entry point"""
    # Setup Apple design
    AppleLayoutManager.setup_page_config()

    app = SeoulCommercialApp()
    app.initialize_session_state()

    # Load Apple CSS
    AppleUI.load_css()

    # Handle quick queries
    quick_query = AppleLayoutManager.handle_quick_query()
    if quick_query:
        st.session_state['user_query'] = quick_query

    # Render UI
    app.render_header()
    options = app.render_sidebar()

    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 SQL 분석",
        "📄 문서 검색",
        "📋 보고서 생성",
        "📈 KPI 대시보드"
    ])

    with tab1:
        # SQL Analysis Tab
        st.subheader("📊 SQL 분석")
        st.write("자연어 질의를 SQL로 변환하고 데이터를 분석합니다.")

        # Query input
        user_query = st.text_input(
            "분석하고 싶은 내용을 입력하세요:",
            placeholder="예: 강남구 스타벅스 매출 분석",
            key="user_query",
            value=st.session_state.get('user_query', '')
        )

        if st.button("SQL 분석 실행", type="primary"):
            if user_query:
                # Add to query history (safe access)
                if not hasattr(st.session_state, 'query_history'):
                    st.session_state.query_history = []
                st.session_state.query_history.append(user_query)

                # Apple-style progress indicators
                AppleUI.render_progress_bar(0.1, "질의 검증 중...")

                try:
                    # Step 1: Query validation
                    # Check for PII and prompt injection
                    if not app.pii_guard.is_safe(user_query):
                        AppleUI.render_alert("개인정보가 포함된 질의는 처리할 수 없습니다.", "error")
                        return

                    if not app.prompt_guard.is_safe(user_query):
                        AppleUI.render_alert("잘못된 질의 형식입니다.", "error")
                        return

                    AppleUI.render_progress_bar(0.3, "질의 처리 중...")

                    # Step 2: Query processing
                    
                    # Log query start
                    query_id = f"query_{int(time.time() * 1000)}"
                    app.evaluation_hooks.log_text_to_sql_query(
                        user_query=user_query,
                        generated_sql="",  # Will be filled by orchestrator
                        executed_sql="",   # Will be filled by orchestrator
                        execution_time=0,  # Will be calculated
                        success=False      # Will be updated
                    )
                    
                    result = app.process_query(user_query, options)

                    # Step 3: Result validation
                    AppleUI.render_progress_bar(0.7, "결과 검증 중...")

                    if result["success"]:
                        AppleUI.render_progress_bar(1.0, "분석 완료!")
                        AppleUI.render_alert(result["message"], "success")

                        # Display results based on mode with Apple styling
                        if result["mode"] == "sql" and result.get("data"):
                            AppleUI.render_card(
                                title="분석 결과",
                                content="SQL 분석이 완료되었습니다.",
                                icon="📊"
                            )

                            df = pd.DataFrame(result["data"])
                            st.dataframe(df, use_container_width=True)

                            # Create chart based on selected type
                            chart_type_map = {
                                "막대 차트": "bar",
                                "선 차트": "line",
                                "파이 차트": "pie",
                                "히트맵": "bar"  # Fallback to bar for now
                            }
                            AppleUI.render_apple_chart(
                                df,
                                chart_type_map.get(options["chart_type"], "bar"),
                                "데이터 분석 결과"
                            )

                            # Show SQL query if available
                            if result.get("sql_query"):
                                with st.expander("🔍 실행된 SQL 쿼리"):
                                    st.code(result["sql_query"], language="sql")

                            # Store in session state
                            st.session_state.last_sql_df = df
                            st.session_state.last_sql_query = result.get("sql_query")

                        elif result["mode"] == "rag" and result.get("documents"):
                            AppleUI.render_card(
                                title="관련 문서",
                                content="문서 검색이 완료되었습니다.",
                                icon="📄"
                            )

                            for i, doc in enumerate(result["documents"][:5]):  # Show top 5
                                with st.expander(f"📄 문서 {i+1}"):
                                    st.write(doc.get("content", "No content available"))

                            # Store in session state
                            st.session_state.last_rag_hits = result["documents"]

                        elif result["mode"] == "mixed":
                            st.subheader("🔍 통합 분석 결과")

                            # SQL data
                            if result.get("sql_data"):
                                st.write("**정량 분석:**")
                                df = pd.DataFrame(result["sql_data"])
                                st.dataframe(df)
                                st.session_state.last_sql_df = df

                            # RAG documents
                            if result.get("rag_documents"):
                                st.write("**관련 문서:**")
                                for i, doc in enumerate(result["rag_documents"][:3]):
                                    with st.expander(f"문서 {i+1}"):
                                        st.write(doc.get("content", "No content available"))
                                st.session_state.last_rag_hits = result["rag_documents"]

                            # Insights
                            if result.get("insights"):
                                st.write("**AI 인사이트:**")
                                st.write(
                                    result["insights"].get(
                                        "summary", "No insights available"
                                    )
                                )

                    else:
                        status_text.text("분석 실패")
                        progress_bar.progress(100)
                        st.error(f"오류: {result.get('error', 'Unknown error')}")
                        
                        # Show error details if available
                        if result.get("error_details"):
                            with st.expander("오류 상세 정보"):
                                st.json(result["error_details"])
                
                except Exception as e:
                    status_text.text("분석 중 오류 발생")
                    progress_bar.progress(100)
                    st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                    
                    # Log error
                    app.logger.error(f"Query processing error: {e}", exc_info=True)
                
                finally:
                    # Clear progress indicators
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    
            else:
                st.warning("질의를 입력해주세요.")

        # Recent results from session state (safe access)
        last_sql_df = getattr(st.session_state, 'last_sql_df', None)
        last_rag_hits = getattr(st.session_state, 'last_rag_hits', [])
        last_report = getattr(st.session_state, 'last_report', None)

        if last_sql_df is not None or last_rag_hits or last_report:
            st.subheader("📊 최근 결과")

            # SQL results
            if last_sql_df is not None:
                with st.expander("최근 SQL 분석 결과"):
                    st.dataframe(last_sql_df)

            # RAG results
            if last_rag_hits:
                with st.expander("최근 문서 검색 결과"):
                    for i, doc in enumerate(last_rag_hits[:3]):
                        st.write(f"**문서 {i+1}:**")
                        st.write(doc.get("content", "No content available")[:200] + "...")
            
            # Report results
            if last_report:
                with st.expander("최근 보고서"):
                    st.write(last_report.get("summary", "No summary available"))

        # Query history (safe access)
        query_history = getattr(st.session_state, 'query_history', [])
        if query_history:
            st.subheader("📝 최근 질의")
            for i, query in enumerate(query_history[-5:]):
                st.write(f"{i+1}. {query}")

    with tab2:
        # Document Search Tab
        st.subheader("📄 문서 검색")
        st.write("PDF 문서에서 관련 정보를 검색합니다.")
        
        # Enhanced document search interface
        EnhancedSearchUI.render_search_hero()

    with tab3:
        # Report Generation Tab
        st.subheader("📋 보고서 생성")
        st.write("SQL 분석 결과와 문서 검색 결과를 종합하여 보고서를 생성합니다.")
        
        # Enhanced report generation interface
        EnhancedReportUI.render_report_hero()
            progress_container = st.container()

            try:
                # Search progress tracking
                with progress_container:
                    # Step 1: Initialize
                    EnhancedSearchUI.render_search_progress("starting", 0.1)
                    time.sleep(0.5)

                    # Step 2: PDF Search
                    EnhancedSearchUI.render_search_progress("pdf_search", 0.3)

                    # Step 3: Web Search
                    EnhancedSearchUI.render_search_progress("web_search", 0.6)

                    # Step 4: AI Processing
                    EnhancedSearchUI.render_search_progress("ai_processing", 0.9)

                    # Perform the actual search
                    if search_options["search_mode"] == "pdf_only":
                        pdf_results = search_options["pdf_results"]
                        web_results = 0
                    elif search_options["search_mode"] == "web_only":
                        pdf_results = 0
                        web_results = search_options["web_results"]
                    else:  # hybrid
                        pdf_results = search_options["pdf_results"]
                        web_results = search_options["web_results"]

                    response = app.hybrid_search_engine.search_and_answer(
                        search_query,
                        pdf_results=pdf_results,
                        web_results=web_results
                    )

                    # Step 5: Complete
                    EnhancedSearchUI.render_search_progress("completed", 1.0)
                    time.sleep(0.5)

                # Clear progress and show results
                progress_container.empty()

                # Render source styles
                EnhancedSearchUI.render_source_styles()

                # Display results
                EnhancedSearchUI.render_search_results(response, search_options)

                # Store in session state
                st.session_state.last_hybrid_search = response

            except Exception as e:
                progress_container.empty()
                st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
                app.logger.error(f"Enhanced search error: {e}")

        elif search_button_clicked and not search_query.strip():
            st.warning("검색할 내용을 입력해주세요.")

        # Recent search results
        if st.session_state.get('last_hybrid_search'):
            st.markdown("---")
            st.markdown("### 📋 최근 검색 기록")

            with st.expander("최근 검색 및 답변 보기", expanded=False):
                recent = st.session_state.last_hybrid_search

                st.markdown(f"**🔍 질문:** {recent.get('query', 'Unknown')}")
                st.markdown(f"**🤖 답변:** {recent.get('answer', 'No answer available')[:200]}...")

                if recent.get("sources"):
                    st.markdown("**📚 주요 출처:**")
                    for i, source in enumerate(recent["sources"][:3], 1):
                        source_type = "📄 PDF" if source["type"] == "pdf" else "🌐 웹"
                        st.write(f"{i}. {source_type} {source['title']} (관련도: {source['score']:.2f})")

        # System status section
        st.markdown("---")
        with st.expander("📊 시스템 상태 및 통계", expanded=False):
            try:
                status = app.hybrid_search_engine.get_system_status()

                # Status indicators
                col1, col2, col3 = st.columns(3)

                with col1:
                    pdf_status = status.get("pdf_processor", {})
                    pdf_ready = pdf_status.get("status") == "ready"
                    status_color = "🟢" if pdf_ready else "🔴"

                    st.markdown(f"""
                    **📚 PDF 시스템**
                    {status_color} 상태: {'정상' if pdf_ready else '오류'}
                    - 문서 수: {pdf_status.get("total_files", 0)}개
                    - 검색 청크: {pdf_status.get("total_chunks", 0)}개
                    """)

                with col2:
                    ai_status = status.get("gemini_service", {})
                    ai_ready = ai_status.get("status") == "ready"
                    ai_status_color = "🟢" if ai_ready else "🔴"

                    st.markdown(f"""
                    **🤖 AI 시스템**
                    {ai_status_color} 상태: {'정상' if ai_ready else '오류'}
                    - 답변 생성: {'가능' if ai_ready else '불가능'}
                    """)

                with col3:
                    overall_ready = status.get("overall_status") == "ready"
                    overall_color = "🟢" if overall_ready else "🔴"

                    st.markdown(f"""
                    **⚡ 전체 시스템**
                    {overall_color} 상태: {'정상' if overall_ready else '점검 필요'}
                    - 검색 기능: {'활성화' if overall_ready else '비활성화'}
                    """)

                # PDF files info
                if pdf_status.get("total_files", 0) > 0:
                    st.markdown("**📁 PDF 문서 현황:**")
                    st.info(f"data/pdf 폴더에서 {pdf_status['total_files']}개 문서가 인덱싱되어 검색 가능합니다.")
                else:
                    st.warning("PDF 문서가 인덱싱되지 않았습니다. data/pdf 폴더에 문서를 추가하고 시스템을 다시 시작해주세요.")

            except Exception as e:
                st.error(f"시스템 상태 확인 중 오류: {str(e)}")

    with tab4:
        # Enhanced report generation interface
        EnhancedReportUI.render_report_hero()

        # Data availability status
        data_status = EnhancedReportUI.render_data_status()

        # Report configuration
        report_config = EnhancedReportUI.render_report_config()

        # Data source configuration
        data_source_config = EnhancedReportUI.render_data_source_config(data_status)

        # Advanced options
        report_options = EnhancedReportUI.render_report_options()

        # Generate report button
        if st.button("🚀 보고서 생성", type="primary", use_container_width=True):
            # Check if any data source is selected or mock data generation is enabled
            has_data_source = (
                data_source_config["use_sql_data"] or
                data_source_config["use_rag_data"] or
                data_source_config["use_hybrid_data"] or
                data_source_config["generate_mock_data"]
            )

            if not has_data_source:
                st.warning("최소 하나의 데이터 소스를 선택하거나 샘플 데이터 생성을 활성화해주세요.")
                return

            progress_container = st.container()

            try:
                # Report generation progress
                with progress_container:
                    # Step 1: Data preparation
                    EnhancedReportUI.render_report_progress("preparing", 0.2)
                    time.sleep(0.5)

                    # Prepare data sources with safe access
                    if data_source_config["generate_mock_data"]:
                        # Use mock data
                        mock_data = EnhancedReportUI.generate_mock_data(report_config)
                        sql_df = mock_data["sql_df"]
                        rag_documents = mock_data["rag_documents"]
                        hybrid_data = mock_data["hybrid_search"]
                    else:
                        # Use real data with safe access
                        sql_df = pd.DataFrame()
                        if data_source_config["use_sql_data"]:
                            sql_df = getattr(st.session_state, 'last_sql_df', None)
                            if sql_df is None:
                                sql_df = pd.DataFrame()

                        rag_documents = []
                        if data_source_config["use_rag_data"]:
                            rag_documents = getattr(st.session_state, 'last_rag_hits', [])
                            if rag_documents is None:
                                rag_documents = []

                        hybrid_data = None
                        if data_source_config["use_hybrid_data"]:
                            hybrid_data = getattr(st.session_state, 'last_hybrid_search', None)

                    # Step 2: Data analysis
                    EnhancedReportUI.render_report_progress("analyzing", 0.4)
                    time.sleep(0.5)

                    # Generate KPIs safely
                    kpis = {
                        "total_sales": 0,
                        "avg_growth_rate": 0.15,
                        "avg_transaction": 0,
                        "document_count": len(rag_documents)
                    }

                    if not sql_df.empty:
                        if '당월_매출_금액' in sql_df.columns:
                            kpis["total_sales"] = sql_df['당월_매출_금액'].sum()
                        if '당월_매출_건수' in sql_df.columns:
                            kpis["avg_transaction"] = sql_df['당월_매출_건수'].mean()
                        if 'growth_rate' in sql_df.columns:
                            kpis["avg_growth_rate"] = sql_df['growth_rate'].mean() / 100

                    # Step 3: Report generation
                    EnhancedReportUI.render_report_progress("generating", 0.6)
                    time.sleep(0.5)

                    # Generate report content
                    report_content = f"""
# 서울 상권 분석 보고서

## 📊 개요
- **분석 지역**: {report_config['target_area']}
- **분석 업종**: {report_config['target_industry']}
- **보고서 유형**: {report_config['report_style']}
- **생성 일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}

## 📈 주요 지표
- **총 매출액**: {kpis['total_sales']:,.0f}원
- **평균 거래건수**: {kpis['avg_transaction']:,.0f}건
- **평균 성장률**: {kpis['avg_growth_rate']:.1%}
- **분석된 문서 수**: {kpis['document_count']}개

## 🔍 데이터 분석 결과

### SQL 분석 데이터
{'데이터가 포함되어 있습니다.' if not sql_df.empty else '데이터가 없습니다.'}

### 문서 검색 결과
{f'{len(rag_documents)}개의 관련 문서가 분석되었습니다.' if rag_documents else '검색된 문서가 없습니다.'}

### 하이브리드 검색 인사이트
{hybrid_data['answer'][:200] + '...' if hybrid_data and hybrid_data.get('answer') else 'AI 인사이트가 없습니다.'}

## 💡 주요 인사이트
1. {report_config['target_area']} 지역의 {report_config['target_industry']} 업종 분석
2. 데이터 기반 상권 현황 파악
3. 성장 가능성 및 기회 요인 분석

## 📋 결론 및 제언
- 지속적인 모니터링을 통한 트렌드 파악 필요
- 데이터 기반 의사결정 체계 구축 권장
- 정기적인 보고서 업데이트를 통한 변화 추적

---
*본 보고서는 AI 기반 분석 시스템으로 생성되었습니다.*
                    """

                    # Step 4: Formatting
                    EnhancedReportUI.render_report_progress("formatting", 0.8)
                    time.sleep(0.5)

                    # Step 5: Finalizing
                    EnhancedReportUI.render_report_progress("finalizing", 0.9)
                    time.sleep(0.5)

                    # Prepare report data
                    report_data = {
                        "status": "success",
                        "content": report_content,
                        "metadata": {
                            "generated_at": datetime.now().isoformat(),
                            "config": report_config,
                            "data_sources": data_source_config,
                            "options": report_options
                        },
                        "data_sources": {
                            "sql_rows": len(sql_df) if not sql_df.empty else 0,
                            "rag_documents": len(rag_documents),
                            "hybrid_confidence": hybrid_data.get('confidence', 0) if hybrid_data else 0
                        },
                        "kpis": kpis
                    }

                    # Step 6: Complete
                    EnhancedReportUI.render_report_progress("completed", 1.0)
                    time.sleep(0.5)

                # Clear progress and show results
                progress_container.empty()

                # Display generated report
                EnhancedReportUI.render_generated_report(report_data, report_options)

                # Store in session state
                st.session_state.last_report = report_data

            except Exception as e:
                progress_container.empty()
                st.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")
                app.logger.error(f"Report generation error: {e}")

        # Recent report section
        if hasattr(st.session_state, 'last_report') and st.session_state.last_report:
            st.markdown("---")
            st.markdown("### 📋 최근 생성된 보고서")

            with st.expander("최근 보고서 미리보기", expanded=False):
                recent = st.session_state.last_report
                if isinstance(recent, dict) and recent.get("content"):
                    st.markdown(f"**생성 일시**: {recent.get('metadata', {}).get('generated_at', 'Unknown')}")
                    st.markdown(f"**보고서 내용** (미리보기):")
                    content_preview = recent["content"][:500] + "..." if len(recent["content"]) > 500 else recent["content"]
                    st.markdown(content_preview)

                    if st.button("전체 보고서 다시 보기"):
                        EnhancedReportUI.render_generated_report(recent, recent.get('metadata', {}).get('options', {}))
                else:
                    st.info("이전에 생성된 보고서가 없습니다.")

    with tab5:
        # Apple-style KPI Dashboard
        app.kpi_dashboard.render_dashboard()

    with tab6:
        st.subheader("📈 평가 대시보드")
        st.write("시스템 성능 및 KPI 평가 결과를 확인합니다.")
        
        # Import evaluation dashboard
        try:
            from utils.evaluation_dashboard import EvaluationDashboard
            
            # Initialize evaluation dashboard
            eval_config = {
                "evaluation": {
                    "results_path": "models/artifacts/evaluation"
                }
            }
            eval_dashboard = EvaluationDashboard(eval_config)
            
            # Load and display evaluation results
            eval_dashboard.render_evaluation_dashboard()
            
            # Add evaluation controls
            st.subheader("🔧 평가 실행")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("평가 실행", type="primary"):
                    with st.spinner("평가 실행 중..."):
                        # Here you would run the actual evaluation
                        st.info("평가 실행 기능은 구현 중입니다.")
            
            with col2:
                if st.button("결과 새로고침"):
                    st.rerun()
                    
        except ImportError as e:
            st.error(f"평가 대시보드를 로드할 수 없습니다: {e}")
        except Exception as e:
            st.error(f"평가 대시보드 오류: {e}")


    # Apple-style Footer
    AppleUI.render_footer()


if __name__ == "__main__":
    main()
