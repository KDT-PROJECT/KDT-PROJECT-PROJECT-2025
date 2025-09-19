"""Seoul Commercial Analysis LLM Application"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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
# from utils.performance_dashboard import PerformanceDashboard  # Not implemented
from intelligent_search_service import get_intelligent_search_service
from components.seoul_map_visualization import SeoulMapVisualization

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
        # self._performance_dashboard = None  # Not implemented
        self._intelligent_search_service = None
        self._map_visualization = None

        self.logger.info("SeoulCommercialApp initialized")

    @property
    def intelligent_search_service(self):
        """Lazy load intelligent search service"""
        if self._intelligent_search_service is None:
            self._intelligent_search_service = get_intelligent_search_service()
        return self._intelligent_search_service

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

    # @property
    # def performance_dashboard(self):
    #     """Lazy load performance dashboard - Not implemented"""
    #     return None

    @property
    def map_visualization(self):
        """Lazy load map visualization"""
        if self._map_visualization is None:
            self._map_visualization = SeoulMapVisualization()
        return self._map_visualization

    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        if "session_id" not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        
        # Cache-related session state
        if "last_sql_df" not in st.session_state:
            st.session_state.last_sql_df = None
        if "last_rag_hits" not in st.session_state:
            st.session_state.last_rag_hits = []
        if "last_report" not in st.session_state:
            st.session_state.last_report = None
        if "cache_stats" not in st.session_state:
            st.session_state.cache_stats = {
                "hits": 0,
                "misses": 0,
                "total_queries": 0
            }

    def render_header(self):
        """Render application header"""
        st.title("?�� ?�울 ?�권 분석 LLM")
        st.markdown("### AI 기반 상권 데이터 분석 및 리포트 생성")
        st.markdown("---")

    def render_sidebar(self):
        """Render sidebar with options"""
        with st.sidebar:
            st.header("?�️ ?�정")

            # Analysis mode selection
            analysis_mode = st.selectbox(
                "분석 모드",
                ["자동", "SQL 분석", "문서 검색", "종합 분석"],
                help="자동: AI가 적절한 분석 방법을 선택합니다.",
            )

            # Chart type selection
            chart_type = st.selectbox(
                "차트 ?�형",
                ["막대 차트", "선 차트", "파이 차트", "히트맵"],
                help="데이터 유형에 따라 적절한 차트 유형을 선택합니다.",
            )

            # Advanced options
            with st.expander("고급 옵션"):
                max_results = st.slider("최대 결과 수", 10, 1000, 100)
                enable_caching = st.checkbox("캐싱 활성화", value=True)
                debug_mode = st.checkbox("디버그 모드", value=False)
            
            # Cache management
            with st.expander("캐시 관리"):
                cache_stats = self.cache_service.get_stats()
                st.metric("캐시 사용량", f"{cache_stats['cache_size']}/{cache_stats['max_size']}")
                st.metric("히트율", f"{cache_stats['hit_rate']:.1%}")
                st.metric("총 요청", cache_stats['hit_count'] + cache_stats['miss_count'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("캐시 정리"):
                        self.cache_service.clear()
                        st.session_state.cache_stats = {"hits": 0, "misses": 0, "total_queries": 0}
                        st.success("캐시가 정리되었습니다.")

                with col2:
                    if st.button("캐시 통계 새로고침"):
                        st.rerun()

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
                "message": "질의 처리 �??�류가 발생?�습?�다.",
            }

    def _format_orchestrator_result(
        self, result: dict[str, Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        """Format orchestrator result for display"""
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "message": "분석???�료히트맵?�습?�다.",
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
                "message": "히트맵?�는 분석 모드?�니??",
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
                "message": "SQL 분석???�료히트맵?�습?�다.",
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
            "message": "SQL 분석???�료?�었?�니??",
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
                "message": "문서 검?�을 ?�료히트맵?�습?�다.",
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
            "message": "문서 검?�이 ?�료?�었?�니??",
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
            "message": "?�합 분석???�료?�었?�니??",
        }

    def route_intent(self, query: str) -> str:
        """Simple keyword-based intent routing"""
        query_lower = query.lower()

        sql_keywords = [
            "매출",
            "거래",
            "데이터",
            "통계",
            "위치",
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
    app = SeoulCommercialApp()
    app.initialize_session_state()

    # Render UI
    app.render_header()
    options = app.render_sidebar()

    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "상권 질의 분석", 
        "상권 SQL 분석", 
        "상권 문서 검색", 
        "상권 보고서 생성", 
        "상권 지원 정보",
        "시스템 모니터링",
        "통합 검색",
        "상권 지도 분석"
    ])

    with tab7:
        st.title("통합 검색")
        st.info("웹, 이미지, 비디오 등 다양한 소스에서 정보를 검색합니다.")
        
        search_tab1, search_tab2, search_tab3 = st.tabs(["통합 검색", "이미지 검색", "유튜브 비디오"])

        with search_tab1:
            st.subheader("웹 검색 결과")
            web_query = st.text_input("검색어를 입력하세요", key="web_query")
            if st.button("검색", key="web_search"):
                if web_query:
                    with st.spinner("웹에서 검색 중..."):
                        results = app.intelligent_search_service.web_search(web_query)
                        if isinstance(results, list):
                            for result in results:
                                st.markdown(f"### [{result['title']}]({result['url']})")
                                st.write(result['content'])
                        else:
                            st.info("검색 결과가 없습니다.")

        with search_tab2:
            st.subheader("이미지 검색 결과")
            image_query = st.text_input("검색어를 입력하세요", key="image_query")
            if st.button("검색", key="image_search"):
                if image_query:
                    with st.spinner("이미지 검색 중..."):
                        results = app.intelligent_search_service.image_search(image_query)
                        if isinstance(results, list):
                            for result in results:
                                st.image(result['thumbnail_url'], caption=result['title'], use_column_width=True)
                                st.markdown(f"[{result['title']}]({result['url']})")
                        else:
                            st.info("검색 결과가 없습니다.")
        
        with search_tab3:
            st.subheader("유튜브 비디오 검색 결과")
            video_query = st.text_input("검색어를 입력하세요", key="video_query")
            if st.button("검색", key="video_search"):
                if video_query:
                    with st.spinner("유튜브 비디오 검색 중..."):
                        results = app.intelligent_search_service.video_search(video_query)
                        if isinstance(results, list):
                            for result in results:
                                st.image(result['thumbnail_url'], caption=result['title'], use_column_width=True)
                                st.markdown(f"### [{result['title']}]({result['url']})")
                                st.write(result['content'])
                        else:
                            st.info("검색 결과가 없습니다.")

    with tab1:
        # Main chat interface
        st.subheader("?�� 질의 ?�력")

        # Query input
        user_query = st.text_input(
            "분석?�고 ?��? ?�용???�력?�세??",
            placeholder="예: 강남구 매출 추이를 분석해주세요",
            key="user_query",
        )

        if st.button("분석 ?�행", type="primary"):
            if user_query:
                # Add to query history
                st.session_state.query_history.append(user_query)
                
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Query validation
                    status_text.text("질의 검�?�?..")
                    progress_bar.progress(10)
                    
                    # Check for PII and prompt injection
                    if not app.pii_guard.is_safe(user_query):
                        st.error("개인정보가 포함된 질의는 처리할 수 없습니다.")
                        return
                    
                    if not app.prompt_guard.is_safe(user_query):
                        st.error("잘못된 질의 형식입니다.")
                        return
                    
                    # Step 2: Query processing
                    status_text.text("질의 처리 �?..")
                    progress_bar.progress(30)
                    
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
                    status_text.text("결과 검�?�?..")
                    progress_bar.progress(70)
                    
                    if result["success"]:
                        status_text.text("분석 ?�료!")
                        progress_bar.progress(100)
                        st.success(result["message"])

                        # Display results based on mode
                        if result["mode"] == "sql" and result.get("data"):
                            st.header("📊 분석")
                            df = pd.DataFrame(result["data"])
                            st.dataframe(df)

                            # Show SQL query if available
                            if result.get("sql_query"):
                                with st.expander("?�행??SQL 쿼리"):
                                    st.code(result["sql_query"], language="sql")

                            # Store in session state
                            st.session_state.last_sql_df = df
                            st.session_state.last_sql_query = result.get("sql_query")

                        elif result["mode"] == "rag" and result.get("documents"):
                            st.subheader("관련 문서")
                            for i, doc in enumerate(result["documents"][:5]):  # Show top 5
                                with st.expander(f"문서 {i+1}"):
                                    st.write(doc.get("content", "No content available"))

                            # Store in session state
                            st.session_state.last_rag_hits = result["documents"]

                        elif result["mode"] == "mixed":
                            st.header("📊 분석")

                            # SQL data
                            if result.get("sql_data"):
                                st.write("**?�량 분석:**")
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
                                st.write("**AI ?�사?�트:**")
                                st.write(
                                    result["insights"].get(
                                        "summary", "No insights available"
                                    )
                                )

                    else:
                        status_text.text("분석 ?�패")
                        progress_bar.progress(100)
                        st.error(f"?�류: {result.get('error', 'Unknown error')}")
                        
                        # Show error details if available
                        if result.get("error_details"):
                            with st.expander("?�류 ?�세 ?�보"):
                                st.json(result["error_details"])
                
                except Exception as e:
                    status_text.text("분석 �??�류 발생")
                    progress_bar.progress(100)
                    st.error(f"분석 �??�류가 발생?�습?�다: {str(e)}")
                    
                    # Log error
                    app.logger.error(f"Query processing error: {e}", exc_info=True)
                
                finally:
                    # Clear progress indicators
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    
            else:
                st.warning("질의�??�력?�주?�요.")

        # Recent results from session state
        if st.session_state.last_sql_df is not None or st.session_state.last_rag_hits or st.session_state.last_report:
            st.subheader("?�� 최근 결과")
            
            # SQL results
            if st.session_state.last_sql_df is not None:
                with st.expander("최근 SQL 분석 결과"):
                    st.dataframe(st.session_state.last_sql_df)
            
            # RAG results
            if st.session_state.last_rag_hits:
                with st.expander("최근 문서 검색 결과"):
                    for i, doc in enumerate(st.session_state.last_rag_hits[:3]):
                        st.write(f"**문서 {i+1}:**")
                        st.write(doc.get("content", "No content available")[:200] + "...")
            
            # Report results
            if st.session_state.last_report:
                with st.expander("최근 보고서"):
                    st.write(st.session_state.last_report.get("summary", "No summary available"))

        # Query history
        if st.session_state.query_history:
            st.subheader("?�� 최근 질의")
            for i, query in enumerate(st.session_state.query_history[-5:]):
                st.write(f"{i+1}. {query}")

    with tab2:
        st.header("📊 분석")
        st.write("SQL 분석 기능을 사용하여 데이터를 분석합니다.")
        
        # SQL query input
        sql_query = st.text_area(
            "SQL 쿼리�??�력?�세??",
            placeholder="SELECT * FROM regions WHERE name = '강남�?",
            height=100
        )
        
        # Query options
        col1, col2 = st.columns(2)
        with col1:
            max_rows = st.slider("최대 표시 행 수", 10, 1000, 100)
        with col2:
            show_sql = st.checkbox("SQL 쿼리 표시", value=True)
        
        if st.button("SQL 실행", type="primary"):
            if sql_query:
                with st.spinner("SQL 실행 중..."):
                    try:
                        # Database configuration
                        db_config = {
                            "host": "localhost",
                            "user": "root",
                            "password": "password",
                            "database": "seoul_commercial",
                            "port": 3306
                        }
                        
                        # Execute SQL query
                        result = run_sql(sql_query, db_config)
                        
                        if result["success"]:
                            st.success("SQL 쿼리가 성공적으로 실행되었습니다")
                            
                            # Display results
                            if result["results"]:
                                df = pd.DataFrame(result["results"])
                                st.dataframe(df.head(max_rows))
                                
                                # Show query info
                                st.info(f"{result['row_count']}개의 행이 반환되었습니다")
                                
                                # Show SQL query if requested
                                if show_sql:
                                    with st.expander("실행된 SQL 쿼리"):
                                        st.code(sql_query, language="sql")
                                
                                # Store in session state
                                st.session_state.last_sql_df = df
                                st.session_state.last_sql_query = sql_query
                                
                            else:
                                st.warning("쿼리 결과가 없습니다.")
                        else:
                            st.error(f"SQL 실행 오류: {result.get('message', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"SQL 실행 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("SQL 쿼리를 입력해주세요.")
        
        # Show recent SQL results
        if st.session_state.last_sql_df is not None:
            st.subheader("최근 SQL 결과")
            with st.expander("최근 실행된 SQL 결과 보기"):
                st.dataframe(st.session_state.last_sql_df)
                if st.session_state.last_sql_query:
                    st.code(st.session_state.last_sql_query, language="sql")

    with tab3:
        st.subheader("문서 검색")
        st.write("문서 검색 기능을 사용하여 관련 문서를 찾습니다.")
        
        # Search query input
        search_query = st.text_input(
            "검색할 내용을 입력하세요",
            placeholder="예: 강남구 정책"
        )
        
        # Search options
        col1, col2, col3 = st.columns(3)
        with col1:
            top_k = st.slider("검색 결과 수", 5, 20, 10)
        with col2:
            alpha = st.slider("하이브리드 가중치", 0.0, 1.0, 0.5, 0.1)
        with col3:
            show_scores = st.checkbox("관련도 점수 표시", value=True)
        
        if st.button("문서 검색", type="primary"):
            if search_query:
                with st.spinner("문서 검색 중..."):
                    try:
                        # Perform hybrid search
                        results = app.hybrid_retrieval.hybrid_search(
                            search_query, 
                            top_k=top_k, 
                            alpha=alpha
                        )
                        
                        if results and not any("error" in result for result in results):
                            st.success(f"{len(results)}개의 관련 문서를 찾았습니다.")
                            
                            # Display results
                            for i, doc in enumerate(results, 1):
                                with st.expander(f"문서 {i} - 관련도: {doc.get('combined_score', 0):.3f}"):
                                    st.write("**내용:**")
                                    st.write(doc.get("content", "No content available"))
                                    
                                    if show_scores:
                                        st.write("**점수:**")
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("종합 점수", f"{doc.get('combined_score', 0):.3f}")
                                        with col2:
                                            st.metric("벡터 점수", f"{doc.get('vector_score', 0):.3f}")
                                        with col3:
                                            st.metric("BM25 점수", f"{doc.get('bm25_score', 0):.3f}")
                                    
                                    st.write("**메타데이터**")
                                    metadata = doc.get("metadata", {})
                                    for key, value in metadata.items():
                                        st.write(f"- **{key}**: {value}")
                            
                            # Store in session state
                            st.session_state.last_rag_hits = results
                            
                        else:
                            st.warning("관련 문서를 찾을 수 없습니다.")
                            if results and any("error" in result for result in results):
                                st.error(f"검색 오류: {results[0].get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"문서 검색 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("검색할 내용을 입력해주세요.")
        
        # Show recent search results
        if st.session_state.last_rag_hits:
            st.subheader("최근 검색 결과")
            with st.expander("최근 검색 결과 보기"):
                for i, doc in enumerate(st.session_state.last_rag_hits[:5], 1):
                    st.write(f"**문서 {i}:**")
                    st.write(doc.get("content", "No content available")[:200] + "...")
                    st.write("---")

    with tab4:
        st.subheader("보고서 생성")
        st.write("AI 기반 보고서 생성 기능을 사용합니다")
        
        # Report configuration
        col1, col2, col3 = st.columns(3)
        with col1:
            target_area = st.selectbox("분석 지역", ["강남구", "서초구", "송파구", "전체"]) 
        with col2:
            target_industry = st.selectbox("분석 업종", ["IT", "금융", "의료", "교육", "전체"])
        with col3:
            report_style = st.selectbox("보고서 스타일", ["executive", "detailed", "summary"])
        
        # Data sources
        st.subheader("데이터 소스")
        use_sql_data = st.checkbox("SQL 데이터 사용", value=True)
        use_rag_data = st.checkbox("문서 검색 데이터 사용", value=True)
        
        # Report options
        with st.expander("고급 옵션"):
            include_charts = st.checkbox("차트 포함", value=True)
            include_metadata = st.checkbox("메타데이터 포함", value=True)
            save_to_file = st.checkbox("파일 저장", value=False)
        
        if st.button("보고서 생성", type="primary"):
            with st.spinner("보고서 생성 중..."):
                try:
                    # Prepare data sources
                    sql_df = st.session_state.last_sql_df if use_sql_data and st.session_state.last_sql_df is not None else pd.DataFrame()
                    rag_documents = st.session_state.last_rag_hits if use_rag_data and st.session_state.last_rag_hits else []
                    
                    # Generate KPIs
                    kpis = {
                        "total_sales": sql_df.get('sales_amount', pd.Series([0])).sum() if 'sales_amount' in sql_df.columns else 0,
                        "avg_growth_rate": 0.15,  # Placeholder
                        "avg_transaction": sql_df.get('transaction_count', pd.Series([0])).mean() if 'transaction_count' in sql_df.columns else 0,
                        "document_count": len(rag_documents)
                    }
                    
                    # Generate report using composer
                    report = app.report_composer.compose_report(
                        sql_df=sql_df,
                        rag_documents=rag_documents,
                        kpis=kpis,
                        target_area=target_area,
                        target_industry=target_industry,
                        style=report_style
                    )
                    
                    if report["status"] == "success":
                        st.success("보고서가 성공적으로 생성되었습니다")
                        
                        # Display report
                        st.subheader("생성된 보고서")
                        st.markdown(report["content"])
                        
                        # Show metadata
                        if include_metadata and report.get("metadata"):
                            with st.expander("보고서 메타데이터"):
                                metadata = report["metadata"]
                                st.json(metadata)
                        
                        # Show data sources
                        if report.get("data_sources"):
                            with st.expander("데이터 출처"):
                                st.json(report["data_sources"])
                        
                        # Show KPIs
                        if report.get("kpis"):
                            with st.expander("주요 성과 지표"):
                                st.json(report["kpis"])
                        
                        # Save to file if requested
                        if save_to_file:
                            try:
                                # Generate markdown
                                markdown_content = app.markdown_output.generate_markdown(
                                    report["content"],
                                    report.get("metadata", {}),
                                    report.get("data_sources", {}),
                                    report.get("kpis", {}),
                                    report.get("chart_specs", [])
                                )
                                
                                # Save markdown file
                                filename = f"seoul_analysis_{target_area}_{target_industry}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                                file_path = app.markdown_output.save_markdown(markdown_content, filename)
                                
                                st.success(f"보고서가 저장되었습니다: {file_path}")
                                
                                # Provide download link
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    st.download_button(
                                        label="생성된 보고서 다운로드",
                                        data=f.read(),
                                        file_name=filename,
                                        mime="text/markdown"
                                    )
                                
                            except Exception as e:
                                st.error(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
                        
                        # Store in session state
                        st.session_state.last_report = report
                        
                    else:
                        st.error(f"보고서 생성 오류: {report.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"보고???�성 �??�류가 발생?�습?�다: {str(e)}")
        
        # Show recent report
        if st.session_state.last_report:
            st.subheader("최근 보고서")
            with st.expander("최근 생성된 보고서 보기"):
                report = st.session_state.last_report
                st.markdown(report.get("content", "No content available")[:500] + "...")
                
                if st.button("전체 보고서 보기"):
                    st.markdown(report.get("content", "No content available"))

    with tab5:
        st.subheader("모델 성능 대시보드")
        st.write("테스트 성능 및 KPI 지표 결과를 확인합니다")
        
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
            st.subheader("평가 실행")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("평가 실행", type="primary"):
                    with st.spinner("평가 실행 중..."):
                        st.info("평가 실행 기능은 구현 중입니다.")
            
            with col2:
                if st.button("결과 새로고침"):
                    st.rerun()
                    
        except ImportError as e:
            st.error(f"대시보드 로드에 실패했습니다: {e}")
        except Exception as e:
            st.error(f"대시보드 오류: {e}")

    with tab6:
        st.subheader("???�능 모니?�링")
        st.write("?�스???�능 �?KPI 모니?�링")
        
        # Performance monitoring dashboard
        try:
            app.performance_dashboard.render_performance_dashboard()
        except Exception as e:
            st.error(f"?�능 모니?�링 ?�?�보???�류: {e}")

    # Footer
    st.markdown("---")
    st.markdown("**?�울 ?�권 분석 LLM** | Powered by AI")


if __name__ == "__main__":
    main()
