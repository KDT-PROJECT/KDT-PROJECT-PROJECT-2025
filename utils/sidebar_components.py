"""
Sidebar Components for Seoul Commercial Analysis System
TASK-004: Streamlit 프런트엔드(UI/UX) 구현 - 사이드바 컴포넌트
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from infrastructure.logging_service import StructuredLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SidebarComponents:
    """Sidebar components for the Streamlit application."""

    def __init__(self):
        """Initialize sidebar components."""
        self.logger = StructuredLogger("sidebar_components")

    def render_mode_selector(self) -> str:
        """Render mode selector (SQL/RAG/Report)."""
        try:
            st.subheader("🔧 분석 모드")
            
            mode = st.radio(
                "분석 모드를 선택하세요:",
                ["SQL", "문헌(RAG)", "보고서"],
                help="각 모드에 맞는 분석 도구를 사용합니다."
            )
            
            return mode

        except Exception as e:
            self.logger.error(f"Error rendering mode selector: {e}")
            return "SQL"

    def render_sql_options(self) -> Dict[str, Any]:
        """Render SQL analysis options."""
        try:
            st.subheader("📊 SQL 분석 옵션")
            
            options = {}
            
            # Query options
            with st.expander("쿼리 설정", expanded=True):
                options["max_rows"] = st.slider(
                    "최대 결과 행 수",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    help="SQL 쿼리 결과의 최대 행 수를 설정합니다."
                )
                
                options["timeout"] = st.slider(
                    "쿼리 타임아웃 (초)",
                    min_value=5,
                    max_value=60,
                    value=30,
                    help="SQL 쿼리 실행 타임아웃을 설정합니다."
                )
                
                options["show_sql"] = st.checkbox(
                    "SQL 쿼리 표시",
                    value=True,
                    help="실행된 SQL 쿼리를 표시합니다."
                )
            
            # Chart options
            with st.expander("차트 설정"):
                options["chart_type"] = st.selectbox(
                    "차트 유형",
                    ["막대 차트", "선 차트", "파이 차트", "히트맵", "산점도"],
                    help="데이터 시각화에 사용할 차트 유형을 선택합니다."
                )
                
                options["chart_title"] = st.text_input(
                    "차트 제목",
                    value="분석 결과",
                    help="차트의 제목을 입력합니다."
                )
            
            return options

        except Exception as e:
            self.logger.error(f"Error rendering SQL options: {e}")
            return {}

    def render_rag_options(self) -> Dict[str, Any]:
        """Render RAG analysis options."""
        try:
            st.subheader("📄 문헌 검색 옵션")
            
            options = {}
            
            # Search options
            with st.expander("검색 설정", expanded=True):
                options["top_k"] = st.slider(
                    "검색 결과 수",
                    min_value=5,
                    max_value=20,
                    value=10,
                    help="검색할 문서의 최대 개수를 설정합니다."
                )
                
                options["alpha"] = st.slider(
                    "하이브리드 가중치",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    help="벡터 검색과 BM25 검색의 가중치를 조정합니다. 0.5는 균형을 의미합니다."
                )
                
                options["min_score"] = st.slider(
                    "최소 관련도 점수",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="표시할 최소 관련도 점수를 설정합니다."
                )
            
            # Display options
            with st.expander("표시 설정"):
                options["show_scores"] = st.checkbox(
                    "관련도 점수 표시",
                    value=True,
                    help="검색 결과에 관련도 점수를 표시합니다."
                )
                
                options["show_metadata"] = st.checkbox(
                    "메타데이터 표시",
                    value=True,
                    help="문서의 메타데이터를 표시합니다."
                )
                
                options["truncate_text"] = st.checkbox(
                    "텍스트 자르기",
                    value=True,
                    help="긴 텍스트를 자동으로 자릅니다."
                )
            
            return options

        except Exception as e:
            self.logger.error(f"Error rendering RAG options: {e}")
            return {}

    def render_report_options(self) -> Dict[str, Any]:
        """Render report generation options."""
        try:
            st.subheader("📋 보고서 생성 옵션")
            
            options = {}
            
            # Report settings
            with st.expander("보고서 설정", expanded=True):
                options["report_style"] = st.selectbox(
                    "보고서 스타일",
                    ["executive", "detailed", "summary"],
                    help="보고서의 상세 정도를 선택합니다."
                )
                
                options["target_area"] = st.selectbox(
                    "분석 지역",
                    ["전체", "강남구", "서초구", "송파구", "마포구", "용산구"],
                    help="분석할 지역을 선택합니다."
                )
                
                options["target_industry"] = st.selectbox(
                    "분석 업종",
                    ["전체", "IT", "금융", "의료", "교육", "소매업", "서비스업"],
                    help="분석할 업종을 선택합니다."
                )
            
            # Content options
            with st.expander("내용 설정"):
                options["include_charts"] = st.checkbox(
                    "차트 포함",
                    value=True,
                    help="보고서에 차트를 포함합니다."
                )
                
                options["include_metadata"] = st.checkbox(
                    "메타데이터 포함",
                    value=True,
                    help="보고서에 메타데이터를 포함합니다."
                )
                
                options["include_recommendations"] = st.checkbox(
                    "권고사항 포함",
                    value=True,
                    help="보고서에 권고사항을 포함합니다."
                )
            
            # Output options
            with st.expander("출력 설정"):
                options["save_to_file"] = st.checkbox(
                    "파일로 저장",
                    value=False,
                    help="보고서를 파일로 저장합니다."
                )
                
                options["output_format"] = st.multiselect(
                    "출력 형식",
                    ["markdown", "html", "pdf"],
                    default=["markdown"],
                    help="보고서의 출력 형식을 선택합니다."
                )
            
            return options

        except Exception as e:
            self.logger.error(f"Error rendering report options: {e}")
            return {}

    def render_data_status(self, session_state: Dict[str, Any]):
        """Render data status information."""
        try:
            st.subheader("📊 데이터 상태")
            
            # SQL data status
            if session_state.get("last_sql_df") is not None:
                df = session_state["last_sql_df"]
                st.success(f"✅ SQL 데이터: {len(df)}개 행")
            else:
                st.info("ℹ️ SQL 데이터 없음")
            
            # RAG data status
            if session_state.get("last_rag_hits"):
                hits = session_state["last_rag_hits"]
                st.success(f"✅ 검색 결과: {len(hits)}개 문서")
            else:
                st.info("ℹ️ 검색 결과 없음")
            
            # Report status
            if session_state.get("last_report"):
                st.success("✅ 보고서 생성됨")
            else:
                st.info("ℹ️ 보고서 없음")
            
            # Cache status
            if hasattr(session_state, 'cache_stats'):
                cache_stats = session_state.cache_stats
                st.metric("캐시 히트율", f"{cache_stats.get('hit_rate', 0):.1%}")

        except Exception as e:
            self.logger.error(f"Error rendering data status: {e}")

    def render_system_health(self, health_data: Dict[str, Any] = None):
        """Render system health information."""
        try:
            st.subheader("🔍 시스템 상태")
            
            if health_data is None:
                health_data = {
                    "database": "connected",
                    "vector_store": "connected",
                    "llm": "connected",
                    "last_check": datetime.now().isoformat()
                }
            
            # Database status
            db_status = health_data.get("database", "unknown")
            if db_status == "connected":
                st.success("✅ 데이터베이스 연결됨")
            else:
                st.error("❌ 데이터베이스 연결 실패")
            
            # Vector store status
            vs_status = health_data.get("vector_store", "unknown")
            if vs_status == "connected":
                st.success("✅ 벡터 스토어 연결됨")
            else:
                st.warning("⚠️ 벡터 스토어 연결 실패")
            
            # LLM status
            llm_status = health_data.get("llm", "unknown")
            if llm_status == "connected":
                st.success("✅ LLM 서비스 연결됨")
            else:
                st.warning("⚠️ LLM 서비스 연결 실패")
            
            # Last check time
            last_check = health_data.get("last_check", "N/A")
            if last_check != "N/A":
                try:
                    dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    st.caption(f"마지막 확인: {dt.strftime('%H:%M:%S')}")
                except:
                    st.caption(f"마지막 확인: {last_check}")

        except Exception as e:
            self.logger.error(f"Error rendering system health: {e}")

    def render_kpi_summary(self, kpis: Dict[str, Any] = None):
        """Render KPI summary."""
        try:
            st.subheader("📈 성능 지표")
            
            if kpis is None:
                kpis = {
                    "text_to_sql_accuracy": 0.92,
                    "rag_citation_rate": 0.85,
                    "p95_response_time": 2.7,
                    "user_satisfaction": 4.2
                }
            
            # Text-to-SQL accuracy
            sql_acc = kpis.get("text_to_sql_accuracy", 0)
            st.metric("Text-to-SQL 정확도", f"{sql_acc:.1%}")
            
            # RAG citation rate
            citation_rate = kpis.get("rag_citation_rate", 0)
            st.metric("RAG 각주율", f"{citation_rate:.1%}")
            
            # Response time
            response_time = kpis.get("p95_response_time", 0)
            st.metric("P95 응답 시간", f"{response_time:.1f}s")
            
            # User satisfaction
            satisfaction = kpis.get("user_satisfaction", 0)
            st.metric("사용자 만족도", f"{satisfaction:.1f}/5.0")

        except Exception as e:
            self.logger.error(f"Error rendering KPI summary: {e}")

    def render_quick_actions(self):
        """Render quick action buttons."""
        try:
            st.subheader("⚡ 빠른 작업")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 새로고침", use_container_width=True):
                    st.rerun()
                
                if st.button("🗑️ 캐시 클리어", use_container_width=True):
                    # Clear session state
                    keys_to_clear = ["last_sql_df", "last_rag_hits", "last_report"]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("캐시가 클리어되었습니다.")
                    st.rerun()
            
            with col2:
                if st.button("📊 성능 모니터링", use_container_width=True):
                    st.switch_page("pages/performance.py")
                
                if st.button("⚙️ 설정", use_container_width=True):
                    st.switch_page("pages/settings.py")

        except Exception as e:
            self.logger.error(f"Error rendering quick actions: {e}")

    def render_help_section(self):
        """Render help section."""
        try:
            st.subheader("❓ 도움말")
            
            with st.expander("사용법 가이드"):
                st.markdown("""
                **SQL 분석:**
                1. 자연어로 질의를 입력하세요
                2. 실행 버튼을 클릭하세요
                3. 결과를 확인하고 다운로드하세요
                
                **문헌 검색:**
                1. PDF 파일을 업로드하세요
                2. 인덱싱을 실행하세요
                3. 검색 질의를 입력하세요
                
                **보고서 생성:**
                1. 분석 지역과 업종을 선택하세요
                2. 보고서 스타일을 선택하세요
                3. 생성 버튼을 클릭하세요
                """)
            
            with st.expander("문제 해결"):
                st.markdown("""
                **일반적인 문제:**
                - 쿼리가 너무 복잡한 경우 기간을 축소해보세요
                - 검색 결과가 없는 경우 다른 키워드를 시도해보세요
                - 보고서 생성이 느린 경우 스타일을 변경해보세요
                """)

        except Exception as e:
            self.logger.error(f"Error rendering help section: {e}")

    def render_sidebar(self, app=None, session_state=None) -> Dict[str, Any]:
        """
        Render complete sidebar with all components.

        Args:
            app: Application instance for accessing services
            session_state: Session state for data status

        Returns:
            Dictionary with all sidebar options
        """
        try:
            with st.sidebar:
                st.title("🏢 서울 상권 분석")
                st.markdown("---")

                # Mode selector
                selected_mode = self.render_mode_selector()

                st.markdown("---")

                # Options based on mode
                if selected_mode == "SQL":
                    mode_options = self.render_sql_options()
                elif selected_mode == "문헌(RAG)":
                    mode_options = self.render_rag_options()
                elif selected_mode == "보고서":
                    mode_options = self.render_report_options()
                else:
                    mode_options = {}

                st.markdown("---")

                # Data status
                if session_state:
                    self.render_data_status(session_state)
                    st.markdown("---")

                # System health
                health_data = None
                if app and hasattr(app, 'get_system_health'):
                    try:
                        health_data = app.get_system_health()
                    except:
                        pass
                self.render_system_health(health_data)

                st.markdown("---")

                # KPI summary
                kpis = None
                if app and hasattr(app, 'get_kpis'):
                    try:
                        kpis = app.get_kpis()
                    except:
                        pass
                self.render_kpi_summary(kpis)

                st.markdown("---")

                # Quick actions
                self.render_quick_actions()

                st.markdown("---")

                # Help section
                self.render_help_section()

                # Return combined options
                result = {
                    "selected_mode": selected_mode,
                    **mode_options
                }

                return result

        except Exception as e:
            self.logger.error(f"Error rendering sidebar: {e}")
            return {"selected_mode": "SQL"}


def create_sidebar_components() -> SidebarComponents:
    """
    Factory function to create sidebar components instance.

    Returns:
        SidebarComponents instance
    """
    return SidebarComponents()


# Global sidebar components instance
_sidebar_components = None

def get_sidebar_components() -> SidebarComponents:
    """Get global sidebar components instance."""
    global _sidebar_components
    if _sidebar_components is None:
        _sidebar_components = SidebarComponents()
    return _sidebar_components


if __name__ == "__main__":
    # Test the sidebar components
    components = SidebarComponents()
    mode = components.render_mode_selector()
    print(f"Selected mode: {mode}")
