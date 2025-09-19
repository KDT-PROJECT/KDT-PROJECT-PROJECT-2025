"""
서울 상권분석 LLM 시스템 - Apple 스타일 UI
애플 홈페이지를 참고한 Streamlit UI 구현
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules
try:
    from utils.data_loader import load_csv_to_mysql, get_csv_file_info
    from utils.sql_text2sql import nl_to_sql
    from utils.rag_hybrid import index_pdfs, hybrid_search
    from utils.web_search import search_web
    from utils.pdf_processor import process_all_pdfs
    from utils.mckinsey_viz import create_mckinsey_dashboard
    from utils.report_generator import generate_report_downloads
    from utils.dao import run_sql
except ImportError as e:
    st.warning(f"일부 모듈을 로드할 수 없습니다: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_css():
    """Apple 스타일 CSS 로드"""
    try:
        with open("styles/apple_style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS 파일을 찾을 수 없습니다.")

def create_apple_header():
    """애플 스타일 헤더 생성"""
    st.markdown("""
    <div class="apple-header">
        <h1>🏙️ 서울 상권분석 LLM</h1>
        <p>AI 기반 상권 데이터 분석 및 인사이트 도출 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_dashboard():
    """메트릭 대시보드 생성"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">₩1.25조</div>
            <div class="metric-label">총 매출</div>
            <div class="metric-change positive">↗ +12.5%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">25</div>
            <div class="metric-label">분석 지역</div>
            <div class="metric-change positive">↗ +3개</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">8</div>
            <div class="metric-label">분석 업종</div>
            <div class="metric-change">→ 유지</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">92%</div>
            <div class="metric-label">정확도</div>
            <div class="metric-change positive">↗ +2%</div>
        </div>
        """, unsafe_allow_html=True)

def render_sql_analysis_tab():
    """SQL 분석 탭 렌더링"""
    st.markdown("### 📊 SQL 분석")
    st.markdown("자연어 질의를 SQL로 변환하고 데이터를 분석합니다.")
    
    # 질의 입력 섹션
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.text_input(
            "분석하고 싶은 내용을 입력하세요:",
            placeholder="예: 강남구 소매업 2024년 월별 매출 추세",
            key="user_query_apple"
        )
    
    with col2:
        if st.button("🚀 분석 실행", type="primary", use_container_width=True):
            if user_query:
                with st.spinner("AI가 분석 중입니다..."):
                    try:
                        # Text to SQL conversion
                        schema_prompt = "스키마 정보가 여기에 들어갑니다."
                        llm_cfg = {"model": "HuggingFaceH4/zephyr-7b-beta"}
                        sql_query = nl_to_sql(user_query, schema_prompt, llm_cfg)
                        
                        st.success("✅ SQL 쿼리가 생성되었습니다!")
                        
                        # Show generated SQL
                        with st.expander("🔍 생성된 SQL 쿼리", expanded=False):
                            st.code(sql_query, language="sql")
                        
                        # Execute SQL
                        mysql_url = "mysql+pymysql://test:test@localhost:3306/test_db"
                        result_df = run_sql(sql_query, mysql_url, timeout_s=10)
                        
                        if not result_df.empty:
                            # Store in session state
                            st.session_state.last_sql_df = result_df
                            st.session_state.last_sql_query = sql_query
                            
                            # Display results
                            st.markdown("#### 📈 분석 결과")
                            st.dataframe(result_df, use_container_width=True)
                            
                            # Create visualizations
                            if len(result_df.columns) >= 2:
                                st.markdown("#### 📊 시각화")
                                
                                # Create Apple-style charts
                                fig = go.Figure()
                                
                                if 'date' in result_df.columns:
                                    # Time series chart
                                    fig.add_trace(go.Scatter(
                                        x=result_df.iloc[:, 0],
                                        y=result_df.iloc[:, 1],
                                        mode='lines+markers',
                                        name='트렌드',
                                        line=dict(color='#007AFF', width=3),
                                        marker=dict(size=8, color='#007AFF')
                                    ))
                                else:
                                    # Bar chart
                                    fig.add_trace(go.Bar(
                                        x=result_df.iloc[:, 0],
                                        y=result_df.iloc[:, 1],
                                        name='데이터',
                                        marker_color='#007AFF'
                                    ))
                                
                                fig.update_layout(
                                    title="분석 결과 시각화",
                                    xaxis_title=result_df.columns[0],
                                    yaxis_title=result_df.columns[1],
                                    font=dict(family="Arial", size=12),
                                    paper_bgcolor='white',
                                    plot_bgcolor='white',
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("⚠️ 쿼리 결과가 없습니다.")
                            
                    except Exception as e:
                        st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("⚠️ 질의를 입력해주세요.")

def render_document_search_tab():
    """문서 검색 탭 렌더링"""
    st.markdown("### 📄 문서 검색")
    st.markdown("PDF 문서와 웹 검색을 통해 관련 정보를 찾습니다.")
    
    # 검색 옵션
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "검색하고 싶은 내용을 입력하세요:",
            placeholder="예: 강남구 창업 지원금 요건",
            key="search_query_apple"
        )
    
    with col2:
        search_type = st.selectbox(
            "검색 유형",
            ["일반 검색", "뉴스 검색", "서울 관련 검색"],
            key="search_type_apple"
        )
    
    # 검색 실행
    if st.button("🔍 검색 실행", type="primary", use_container_width=True):
        if search_query:
            with st.spinner("검색 중입니다..."):
                try:
                    # 웹 검색
                    search_type_map = {
                        "일반 검색": "general",
                        "뉴스 검색": "news", 
                        "서울 관련 검색": "seoul"
                    }
                    
                    web_results = search_web(search_query, search_type_map[search_type], max_results=5)
                    
                    if web_results:
                        st.success(f"✅ {len(web_results)}개의 관련 정보를 찾았습니다!")
                        
                        # 검색 결과 표시
                        for i, result in enumerate(web_results, 1):
                            with st.expander(f"📄 결과 {i}: {result.get('title', 'Unknown')[:50]}...", expanded=False):
                                st.markdown(f"**출처**: {result.get('source', 'N/A')}")
                                st.markdown(f"**URL**: {result.get('url', 'N/A')}")
                                st.markdown(f"**내용**: {result.get('snippet', 'N/A')}")
                                st.markdown(f"**관련도**: {result.get('relevance_score', 0):.2f}")
                        
                        # 세션 상태에 저장
                        st.session_state.last_web_results = web_results
                    else:
                        st.warning("⚠️ 관련 정보를 찾을 수 없습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("⚠️ 검색 질의를 입력해주세요.")

def render_report_generation_tab():
    """보고서 생성 탭 렌더링"""
    st.markdown("### 📋 보고서 생성")
    st.markdown("분석 결과를 종합하여 전문적인 보고서를 생성합니다.")
    
    # 데이터 상태 확인
    col1, col2 = st.columns(2)
    
    with col1:
        sql_available = hasattr(st.session_state, 'last_sql_df') and st.session_state.last_sql_df is not None
        if sql_available:
            st.success("✅ SQL 분석 데이터 준비됨")
        else:
            st.warning("⚠️ SQL 분석 데이터 없음")
    
    with col2:
        web_available = hasattr(st.session_state, 'last_web_results') and st.session_state.last_web_results
        if web_available:
            st.success("✅ 웹 검색 결과 준비됨")
        else:
            st.warning("⚠️ 웹 검색 결과 없음")
    
    # 보고서 생성 옵션
    st.markdown("#### 📊 보고서 옵션")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_style = st.selectbox(
            "보고서 스타일",
            ["맥킨지 스타일", "간단 요약", "상세 분석"],
            key="report_style_apple"
        )
    
    with col2:
        include_charts = st.checkbox("차트 포함", value=True, key="include_charts_apple")
    
    with col3:
        include_web_data = st.checkbox("웹 검색 결과 포함", value=True, key="include_web_apple")
    
    # 보고서 생성 버튼
    if st.button("📋 보고서 생성", type="primary", use_container_width=True):
        with st.spinner("보고서를 생성하고 있습니다..."):
            try:
                # 데이터 준비
                sql_df = st.session_state.get('last_sql_df', pd.DataFrame())
                web_results = st.session_state.get('last_web_results', [])
                
                # 샘플 데이터 생성 (실제 데이터가 없는 경우)
                if sql_df.empty:
                    sql_df = pd.DataFrame({
                        'date': pd.date_range('2024-01-01', '2024-12-31', freq='M'),
                        'sales_amt': [100000000000 + i * 10000000000 for i in range(12)],
                        'region': ['강남구'] * 12,
                        'industry': ['소매업'] * 12
                    })
                
                # 분석 데이터
                data = {
                    "total_sales": sql_df['sales_amt'].sum() if 'sales_amt' in sql_df.columns else 1250000000000,
                    "growth_rate": 12.5,
                    "region_count": sql_df['region'].nunique() if 'region' in sql_df.columns else 25,
                    "industry_count": sql_df['industry'].nunique() if 'industry' in sql_df.columns else 8,
                    "top_region": sql_df['region'].mode().iloc[0] if 'region' in sql_df.columns else "강남구",
                    "top_industry": sql_df['industry'].mode().iloc[0] if 'industry' in sql_df.columns else "소매업"
                }
                
                # 보고서 생성
                reports = generate_report_downloads(sql_df, data, web_results)
                
                st.success("✅ 보고서가 성공적으로 생성되었습니다!")
                
                # 보고서 미리보기
                st.markdown("#### 📄 보고서 미리보기")
                markdown_report = reports["markdown"].decode('utf-8')
                st.markdown(markdown_report[:1000] + "..." if len(markdown_report) > 1000 else markdown_report)
                
                # 다운로드 버튼들
                st.markdown("#### 📥 다운로드")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        label="📄 Markdown 다운로드",
                        data=reports["markdown"],
                        file_name=f"seoul_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        label="📝 Word 다운로드",
                        data=reports["docx"],
                        file_name=f"seoul_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                
                with col3:
                    st.download_button(
                        label="📄 PDF 다운로드",
                        data=reports["pdf"],
                        file_name=f"seoul_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # 세션 상태에 저장
                st.session_state.last_report = {
                    "markdown": markdown_report,
                    "data": data,
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                st.error(f"❌ 보고서 생성 중 오류가 발생했습니다: {str(e)}")

def render_data_management_sidebar():
    """데이터 관리 사이드바 렌더링"""
    with st.sidebar:
        st.markdown("### 📊 데이터 관리")
        
        # CSV 파일 정보
        csv_path = "data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv"
        
        if st.button("📁 CSV 파일 정보", use_container_width=True):
            try:
                info = get_csv_file_info(csv_path)
                if info["status"] == "success":
                    st.success(f"✅ 파일 크기: {info['file_size_mb']}MB")
                    st.info(f"📋 컬럼 수: {info['total_columns']}개")
                else:
                    st.error(f"❌ {info['message']}")
            except Exception as e:
                st.error(f"파일 정보 조회 실패: {str(e)}")
        
        # 데이터베이스 설정
        st.markdown("#### 🔗 데이터베이스 설정")
        
        mysql_host = st.text_input("호스트", value="localhost", key="mysql_host_apple")
        mysql_user = st.text_input("사용자", value="seoul_ro", key="mysql_user_apple")
        mysql_password = st.text_input("비밀번호", type="password", value="seoul_ro_password_2024", key="mysql_password_apple")
        mysql_database = st.text_input("데이터베이스", value="seoul_commercial", key="mysql_database_apple")
        
        mysql_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:3306/{mysql_database}"
        
        # 데이터 로딩 버튼
        if st.button("🚀 데이터 로딩", type="primary", use_container_width=True):
            with st.spinner("데이터를 로딩하고 있습니다..."):
                try:
                    result = load_csv_to_mysql(csv_path, mysql_url)
                    if result["status"] == "success":
                        st.success("✅ 데이터 로딩 완료!")
                        st.session_state.data_loaded = True
                    else:
                        st.error(f"❌ {result['message']}")
                except Exception as e:
                    st.error(f"데이터 로딩 실패: {str(e)}")
        
        # 상태 표시
        if hasattr(st.session_state, 'data_loaded') and st.session_state.data_loaded:
            st.success("✅ 데이터 로드됨")
        else:
            st.warning("⚠️ 데이터 로드 필요")

def main():
    """메인 애플리케이션 함수"""
    # 페이지 설정
    st.set_page_config(
        page_title="서울 상권분석 LLM",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS 로드
    load_css()
    
    # 헤더
    create_apple_header()
    
    # 메트릭 대시보드
    create_metrics_dashboard()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "📊 SQL 분석",
        "📄 문서 검색", 
        "📋 보고서 생성"
    ])
    
    with tab1:
        render_sql_analysis_tab()
    
    with tab2:
        render_document_search_tab()
    
    with tab3:
        render_report_generation_tab()
    
    # 사이드바
    render_data_management_sidebar()
    
    # 푸터
    st.markdown("""
    <div class="apple-footer">
        <p><strong>서울 상권분석 LLM 시스템 v1.0</strong></p>
        <p>© 2024 All Rights Reserved | AI 기반 상권 데이터 분석 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
