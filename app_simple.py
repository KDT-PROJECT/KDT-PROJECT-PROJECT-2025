"""Seoul Commercial Analysis LLM Application - Simplified Version"""

import logging
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import components
from components.apple_components import AppleUI
from components.enhanced_search_ui import EnhancedSearchUI
from components.enhanced_report_ui import EnhancedReportUI
from components.apple_kpi_dashboard import AppleKPIDashboard

# Import services
from llm.text_to_sql import get_text_to_sql_service
from utils.dao import run_sql
from utils.report_composer import ReportComposer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main application function"""
    st.set_page_config(
        page_title="서울 상권 분석 시스템",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Header
    st.title("🏙️ 서울 상권 분석 시스템")
    st.markdown("AI 기반 상권 데이터 분석 및 인사이트 도출 플랫폼")

    # Create tabs
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
            key="user_query"
        )

        if st.button("SQL 분석 실행", type="primary"):
            if user_query:
                with st.spinner("SQL 분석 중..."):
                    try:
                        # Text to SQL conversion
                        text_to_sql_service = get_text_to_sql_service()
                        sql_result = text_to_sql_service.convert_to_sql(user_query)
                        
                        if sql_result.get("success"):
                            sql_query = sql_result["sql"]
                            st.success("SQL 쿼리가 생성되었습니다.")
                            
                            # Show generated SQL
                            with st.expander("생성된 SQL 쿼리"):
                                st.code(sql_query, language="sql")
                            
                            # Execute SQL
                            db_config = {
                                "host": "localhost",
                                "user": "test", 
                                "password": "test",
                                "database": "test_db"
                            }
                            
                            result = run_sql(sql_query, db_config)
                            
                            if result.get("success"):
                                if result.get("results"):
                                    df = pd.DataFrame(result["results"])
                                    st.dataframe(df)
                                    st.session_state.last_sql_df = df
                                    st.session_state.last_sql_query = sql_query
                                else:
                                    st.warning("쿼리 결과가 없습니다.")
                            else:
                                st.error(f"SQL 실행 오류: {result.get('message', 'Unknown error')}")
                        else:
                            st.error(f"SQL 변환 오류: {sql_result.get('message', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("질의를 입력해주세요.")

        # Show recent results
        if hasattr(st.session_state, 'last_sql_df') and st.session_state.last_sql_df is not None:
            st.subheader("📊 최근 분석 결과")
            with st.expander("최근 SQL 분석 결과 보기"):
                st.dataframe(st.session_state.last_sql_df)
                if hasattr(st.session_state, 'last_sql_query'):
                    st.code(st.session_state.last_sql_query, language="sql")

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

    with tab4:
        # KPI Dashboard Tab
        st.subheader("📈 KPI 대시보드")
        st.write("주요 성과 지표를 시각화합니다.")
        
        # KPI Dashboard
        try:
            kpi_dashboard = AppleKPIDashboard()
            kpi_dashboard.render_dashboard()
        except Exception as e:
            st.error(f"KPI 대시보드 오류: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>서울 상권 분석 LLM 시스템 v1.0 | © 2024 All Rights Reserved</p>
        <p>AI 기반 상권 데이터 분석 및 인사이트 도출 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
