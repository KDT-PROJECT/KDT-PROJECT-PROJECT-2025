"""
지능형 상권 분석 앱
MySQL 우선 검색 → 웹 검색 백업 → LLM 분석
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 경로 설정
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 지능형 검색 서비스 import
from intelligent_search_service_complete import get_intelligent_search_service_complete

# 페이지 설정
st.set_page_config(
    page_title="지능형 상권 분석 LLM",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }

    .search-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 5px solid #667eea;
    }

    .result-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }

    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }

    .mysql-badge {
        background-color: #28a745;
        color: white;
    }

    .web-badge {
        background-color: #007bff;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """헤더 렌더링"""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 지능형 상권 분석 LLM</h1>
        <p>MySQL 데이터 우선 검색 + 웹 검색 백업 + AI 분석</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("⚙️ 검색 설정")

        search_mode = st.selectbox(
            "검색 모드",
            ["지능형 검색 (MySQL → 웹)", "MySQL만", "웹 검색만"],
            help="지능형 검색은 MySQL을 먼저 검색하고, 데이터가 없으면 웹에서 검색합니다."
        )

        st.markdown("---")

        st.header("📊 데이터 소스")
        mysql_status = st.empty()
        web_status = st.empty()

        # 상태 표시
        mysql_status.success("✅ MySQL 연결 준비됨")
        web_status.info("🌐 웹 검색 API 준비됨")

        st.markdown("---")

        st.header("🔍 검색 예시")
        st.markdown("""
        **MySQL 우선 검색 예시:**
        - 강남구 카페 매출 분석
        - 2024년 IT업종 트렌드
        - 서초구 음식점 거래건수

        **웹 검색 백업 예시:**
        - 최신 창업 지원 정책
        - 상권 분석 보고서
        - 창업 트렌드 분석
        """)

        return {
            "search_mode": search_mode
        }


def render_search_interface():
    """검색 인터페이스 렌더링"""
    st.markdown("""
    <div class="search-container">
        <h3>🔍 지능형 검색</h3>
        <p>궁금한 내용을 자연어로 입력하세요. AI가 MySQL과 웹에서 최적의 데이터를 찾아 분석해드립니다.</p>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: 강남구 카페 창업 현황을 분석해주세요",
        key="search_query"
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        search_button = st.button("🔍 검색 시작", type="primary", use_container_width=True)

    with col2:
        if st.button("💡 검색어 제안", use_container_width=True):
            suggestions = [
                "서울시 강남구 커피숍 매출 트렌드",
                "2024년 IT 스타트업 창업 현황",
                "서초구 음식점 업종별 거래건수",
                "상권 분석 최신 동향"
            ]
            st.write("**추천 검색어:**")
            for suggestion in suggestions:
                if st.button(f"• {suggestion}", key=f"suggestion_{suggestion}"):
                    st.session_state.search_query = suggestion
                    st.rerun()

    return query, search_button


def render_search_results(result):
    """검색 결과 렌더링"""
    if not result['success']:
        st.error("검색 결과를 찾을 수 없습니다.")
        return

    # 데이터 소스 표시
    source = result['primary_source']
    if source == 'mysql':
        st.markdown('<div class="source-badge mysql-badge">📊 MySQL 데이터베이스</div>', unsafe_allow_html=True)
    elif source == 'web':
        st.markdown('<div class="source-badge web-badge">🌐 웹 검색 결과</div>', unsafe_allow_html=True)

    # AI 분석 결과
    st.markdown("""
    <div class="result-container">
        <h3>🤖 AI 분석 결과</h3>
    </div>
    """, unsafe_allow_html=True)

    if 'analysis' in result:
        st.markdown(result['analysis'])

    # MySQL 데이터가 있는 경우 시각화
    if source == 'mysql' and 'mysql_data' in result:
        mysql_data = result['mysql_data']
        if mysql_data['success'] and mysql_data['data'] is not None:
            render_mysql_visualization(mysql_data['data'])

    # 웹 검색 결과가 있는 경우 링크 표시
    if source == 'web' and 'web_data' in result:
        web_data = result['web_data']
        if web_data['success'] and web_data['data']:
            render_web_results(web_data['data'])


def render_mysql_visualization(df):
    """MySQL 데이터 시각화"""
    st.markdown("""
    <div class="result-container">
        <h3>📊 데이터 시각화</h3>
    </div>
    """, unsafe_allow_html=True)

    # 데이터 테이블
    st.subheader("📋 데이터 테이블")
    st.dataframe(df, use_container_width=True)

    # 기본 통계
    if len(df) > 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("총 데이터 수", len(df))
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("컬럼 수", len(df.columns))
            st.markdown('</div>', unsafe_allow_html=True)

        # 숫자형 데이터가 있으면 추가 통계
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("숫자형 컬럼", len(numeric_cols))
                st.markdown('</div>', unsafe_allow_html=True)

            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                avg_val = df[numeric_cols[0]].mean() if len(numeric_cols) > 0 else 0
                st.metric(f"평균 {numeric_cols[0]}", f"{avg_val:,.0f}")
                st.markdown('</div>', unsafe_allow_html=True)

    # 차트 생성
    if len(df) > 0:
        render_charts(df)


def render_charts(df):
    """차트 렌더링"""
    st.subheader("📈 차트 분석")

    # 숫자형 컬럼 찾기
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    if len(numeric_cols) > 0:
        chart_type = st.selectbox("차트 유형 선택", ["막대 차트", "선 차트", "파이 차트", "히스토그램"])

        if chart_type == "막대 차트" and len(categorical_cols) > 0:
            x_col = st.selectbox("X축 (범주형)", categorical_cols)
            y_col = st.selectbox("Y축 (숫자형)", numeric_cols)

            if x_col and y_col:
                # 데이터 그룹화
                grouped_data = df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.bar(grouped_data, x=x_col, y=y_col,
                           title=f"{x_col}별 {y_col}")
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "선 차트":
            if len(df) > 1:
                y_col = st.selectbox("Y축 선택", numeric_cols)
                fig = px.line(df.reset_index(), x=df.index, y=y_col,
                             title=f"{y_col} 추이")
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "파이 차트" and len(categorical_cols) > 0:
            cat_col = st.selectbox("범주 컬럼", categorical_cols)

            if cat_col:
                value_counts = df[cat_col].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index,
                           title=f"{cat_col} 분포")
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "히스토그램":
            y_col = st.selectbox("컬럼 선택", numeric_cols)
            fig = px.histogram(df, x=y_col, title=f"{y_col} 분포")
            st.plotly_chart(fig, use_container_width=True)


def render_web_results(web_data):
    """웹 검색 결과 렌더링"""
    st.markdown("""
    <div class="result-container">
        <h3>🌐 관련 웹 리소스</h3>
    </div>
    """, unsafe_allow_html=True)

    for i, result in enumerate(web_data[:5], 1):
        with st.expander(f"{i}. {result['title']}"):
            st.markdown(f"**URL:** {result['url']}")
            st.markdown(f"**내용:** {result['snippet']}")
            if st.button(f"링크 열기", key=f"link_{i}"):
                st.markdown(f"[🔗 {result['title']}]({result['url']})")


def render_sql_analysis_tab():
    """SQL 분석 탭"""
    st.header("📊 SQL 분석")
    st.markdown("자연어로 질문하면 MySQL 데이터베이스에서 데이터를 찾아 분석해드립니다.")

    query = st.text_input(
        "SQL 분석 질의를 입력하세요",
        placeholder="예: 강남구 카페 매출 분석해주세요",
        key="sql_query"
    )

    if st.button("🔍 SQL 분석 실행", key="sql_analysis_btn", type="primary"):
        if query:
            with st.spinner("🔍 MySQL 데이터베이스 검색 중..."):
                try:
                    search_service = get_intelligent_search_service_complete()
                    mysql_result = search_service.search_mysql_data(query)

                    if mysql_result['success'] and mysql_result['data'] is not None:
                        st.success("✅ MySQL에서 데이터를 찾았습니다!")

                        # 데이터 시각화
                        render_mysql_visualization(mysql_result['data'])

                        # LLM 분석
                        with st.spinner("🤖 AI 분석 중..."):
                            analysis = search_service.analyze_data_with_llm(mysql_result['data'], query)
                            st.markdown("### 🤖 AI 분석 결과")
                            st.markdown(analysis)
                    else:
                        st.warning("⚠️ MySQL에서 관련 데이터를 찾을 수 없습니다.")
                        if 'error' in mysql_result:
                            st.error(f"오류: {mysql_result['error']}")

                except Exception as e:
                    st.error(f"SQL 분석 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("질의를 입력해주세요.")


def render_document_search_tab():
    """문헌 검색 탭"""
    st.header("📚 문헌 검색")
    st.markdown("🤖 AI가 최적의 검색 엔진을 자동 선택하여 상권/창업 관련 최신 문헌과 보고서를 검색합니다.")

    query = st.text_input(
        "문헌 검색어를 입력하세요",
        placeholder="예: 창업 지원 정책, 상권 분석 보고서, 최신 창업 트렌드",
        key="doc_query"
    )

    # 검색 옵션을 간소화
    with st.expander("🔧 고급 설정 (선택사항)"):
        max_results = st.slider("최대 결과 수", 5, 20, 10)
        search_depth = st.selectbox("검색 깊이", ["기본", "심화"], index=0)

    if st.button("🔍 AI 문헌 검색 실행", key="doc_search_btn", type="primary"):
        if query:
            with st.spinner("🤖 AI가 최적의 검색 전략을 선택하고 문헌을 검색 중..."):
                try:
                    search_service = get_intelligent_search_service_complete()

                    # LLM이 검색어를 분석하여 최적의 검색 전략 결정
                    search_strategy = search_service.determine_search_strategy(query)

                    st.info(f"🎯 AI 선택 검색 전략: {search_strategy['strategy_name']}")

                    # AI가 선택한 전략에 따라 검색 실행
                    result = search_service.execute_smart_search(query, search_strategy, max_results)

                    if result['success'] and result['data']:
                        st.success(f"✅ {len(result['data'])}개의 관련 문헌을 찾았습니다!")

                        # 검색 소스 표시
                        sources_used = set([item.get('source', 'Unknown') for item in result['data']])
                        st.caption(f"📡 검색 소스: {', '.join(sources_used)}")

                        # 결과 표시
                        render_web_results(result['data'])

                        # LLM 종합 분석
                        with st.spinner("🧠 AI가 문헌 내용을 종합 분석 중..."):
                            analysis = search_service.analyze_web_results_with_smart_llm(
                                result['data'], query, search_strategy
                            )
                            st.markdown("### 🤖 AI 종합 분석 결과")
                            st.markdown(analysis)
                    else:
                        st.warning("⚠️ 관련 문헌을 찾을 수 없습니다.")
                        if 'error' in result:
                            st.error(f"오류: {result['error']}")

                except Exception as e:
                    st.error(f"문헌 검색 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("검색어를 입력해주세요.")


def render_report_generation_tab():
    """보고서 생성 탭"""
    st.header("📋 보고서 생성")
    st.markdown("MySQL 데이터와 웹 검색 결과를 종합하여 전문적인 보고서를 생성합니다.")

    query = st.text_input(
        "보고서 주제를 입력하세요",
        placeholder="예: 강남구 카페 시장 분석 보고서",
        key="report_query"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        report_type = st.selectbox("보고서 유형", ["종합 분석", "데이터 중심", "시장 동향"])
    with col2:
        include_charts = st.checkbox("차트 포함", value=True)

    if st.button("📋 보고서 생성", key="report_gen_btn", type="primary"):
        if query:
            with st.spinner("📋 종합 보고서 생성 중... (데이터 수집 → 분석 → 보고서 작성)"):
                try:
                    search_service = get_intelligent_search_service_complete()

                    # 1. MySQL 데이터 검색
                    mysql_result = search_service.search_mysql_data(query)

                    # 2. 웹 검색
                    web_result = search_service.search_web_data(query)

                    # 3. 종합 보고서 생성
                    report_content = generate_comprehensive_report(
                        query, mysql_result, web_result, report_type, include_charts
                    )

                    st.success("✅ 보고서가 생성되었습니다!")

                    # 보고서 표시
                    st.markdown("### 📋 생성된 보고서")
                    st.markdown(report_content)

                    # MySQL 데이터 시각화 (있는 경우)
                    if mysql_result['success'] and mysql_result['data'] is not None and include_charts:
                        st.markdown("### 📊 데이터 시각화")
                        render_mysql_visualization(mysql_result['data'])

                    # 웹 검색 결과 (있는 경우)
                    if web_result['success'] and web_result['data']:
                        st.markdown("### 🌐 참고 자료")
                        render_web_results(web_result['data'][:3])  # 상위 3개만 표시

                except Exception as e:
                    st.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("보고서 주제를 입력해주세요.")


def render_integrated_search_tab():
    """통합검색 탭"""
    st.header("🔍 통합검색")
    st.markdown("MySQL 데이터베이스와 웹 검색을 통합하여 가장 포괄적인 분석을 제공합니다.")

    # 검색 인터페이스
    query, search_button = render_search_interface()

    # 검색 실행
    if search_button and query:
        with st.spinner("🔍 통합검색 중... (MySQL → 웹 → AI 분석)"):
            try:
                # 지능형 검색 서비스 사용
                search_service = get_intelligent_search_service_complete()
                result = search_service.intelligent_search(query)

                # 결과를 세션 상태에 저장
                st.session_state.last_result = result
                st.session_state.last_query = query

            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
                return

    # 저장된 결과 표시
    if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
        st.markdown(f"**검색어:** {st.session_state.last_query}")
        render_search_results(st.session_state.last_result)


def generate_comprehensive_report(query, mysql_result, web_result, report_type, include_charts):
    """종합 보고서 생성"""
    try:
        search_service = get_intelligent_search_service_complete()

        # 데이터 요약
        mysql_summary = ""
        if mysql_result['success'] and mysql_result['data'] is not None:
            df = mysql_result['data']
            mysql_summary = f"""
            **MySQL 데이터 분석:**
            - 데이터 건수: {len(df)}건
            - 주요 컬럼: {', '.join(df.columns.tolist())}
            - 데이터 기간: {df.get('년도', pd.Series()).min() if '년도' in df.columns else 'N/A'} ~ {df.get('년도', pd.Series()).max() if '년도' in df.columns else 'N/A'}
            """

        web_summary = ""
        if web_result['success'] and web_result['data']:
            web_summary = f"""
            **웹 검색 결과:**
            - 검색된 문서: {len(web_result['data'])}개
            - 주요 출처: {', '.join(set([item.get('source', 'Unknown') for item in web_result['data'][:3]]))}
            """

        # LLM으로 종합 보고서 생성
        prompt = f"""
        다음 주제로 전문적인 분석 보고서를 작성해주세요: "{query}"

        보고서 유형: {report_type}

        수집된 데이터:
        {mysql_summary}
        {web_summary}

        다음 구조로 보고서를 작성해주세요:

        # {query} - 분석 보고서

        ## 1. 개요
        - 분석 목적 및 범위

        ## 2. 데이터 분석
        - 주요 발견사항
        - 통계적 인사이트

        ## 3. 시장 동향
        - 현재 트렌드
        - 예상 변화

        ## 4. 결론 및 제언
        - 핵심 결론
        - 실행 가능한 제언

        ## 5. 참고사항
        - 데이터 출처 및 한계

        각 섹션을 상세하고 전문적으로 작성해주세요.
        """

        response = search_service.gemini_model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"


def main():
    """메인 앱"""
    render_header()

    # 사이드바
    options = render_sidebar()

    # 4개 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 SQL 분석",
        "📚 문헌 검색",
        "📋 보고서 생성",
        "🔍 통합검색"
    ])

    with tab1:
        render_sql_analysis_tab()

    with tab2:
        render_document_search_tab()

    with tab3:
        render_report_generation_tab()

    with tab4:
        render_integrated_search_tab()

    # 하단 정보
    st.markdown("---")
    with st.expander("ℹ️ 서비스 정보"):
        st.markdown("""
        **🏢 지능형 상권 분석 LLM**

        **각 탭 기능:**
        - **📊 SQL 분석**: MySQL 데이터베이스 우선 검색 및 분석
        - **📚 문헌 검색**: 웹에서 상권/창업 관련 최신 문헌 검색
        - **📋 보고서 생성**: 데이터와 웹 정보를 종합한 전문 보고서 작성
        - **🔍 통합검색**: MySQL → 웹 → AI 분석의 완전한 통합 검색

        **기술 스택:**
        - MySQL 데이터베이스 (서울시 상권 분석 데이터)
        - Google Gemini AI (자연어 처리 및 분석)
        - Serper & Tavily API (웹 검색)
        - Streamlit & Plotly (UI 및 시각화)
        """)



if __name__ == "__main__":
    main()