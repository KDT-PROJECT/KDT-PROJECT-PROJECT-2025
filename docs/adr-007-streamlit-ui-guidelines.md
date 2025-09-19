# ADR-007: Streamlit UI Guidelines and Best Practices

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates specific guidelines for the Streamlit UI implementation in the Seoul Commercial Analysis LLM System. The current system needs to follow these UI rules:

1. **UI Rules**: Follow specific Streamlit UI guidelines
2. **User Experience**: Provide intuitive and responsive interface
3. **Performance**: Optimize UI performance and responsiveness
4. **Accessibility**: Ensure accessibility and usability

## Decision
We will implement comprehensive Streamlit UI guidelines following the development policy requirements:

### Streamlit UI Architecture

#### 1. UI Structure
- **Tab-based Navigation**: Organize functionality into logical tabs
- **Sidebar Navigation**: Use sidebar for main navigation and system status
- **Responsive Layout**: Ensure UI works on different screen sizes
- **Consistent Styling**: Maintain consistent visual design

#### 2. User Experience
- **Intuitive Interface**: Clear and easy-to-use interface
- **Real-time Feedback**: Provide immediate feedback for user actions
- **Error Handling**: Clear error messages and recovery guidance
- **Loading States**: Show loading indicators for long operations

#### 3. Performance Optimization
- **Caching**: Use Streamlit caching for expensive operations
- **Lazy Loading**: Load content only when needed
- **State Management**: Efficient state management with session state
- **Resource Optimization**: Minimize resource usage

#### 4. Accessibility & Usability
- **Keyboard Navigation**: Support keyboard navigation
- **Screen Reader Support**: Ensure screen reader compatibility
- **Color Contrast**: Maintain proper color contrast
- **Text Readability**: Ensure text is readable and well-formatted

## Implementation Details

### UI Structure Implementation

#### Main Application Layout
```python
import streamlit as st
import time
from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class StreamlitUI:
    """Main Streamlit UI class"""
    
    def __init__(self):
        self.setup_page_config()
        self.setup_custom_css()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Setup page configuration"""
        st.set_page_config(
            page_title="서울 상권분석 LLM 시스템",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo/help',
                'Report a bug': 'https://github.com/your-repo/issues',
                'About': "서울 상권분석 LLM 시스템 v1.0.0"
            }
        )
    
    def setup_custom_css(self):
        """Setup custom CSS styling"""
        custom_css = """
        <style>
        /* Main container styling */
        .main-container {
            padding: 1rem;
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #e9ecef;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-left: 20px;
            padding-right: 20px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #007bff;
            color: white;
        }
        
        /* Metric styling */
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        
        /* Error message styling */
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
        }
        
        /* Success message styling */
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #c3e6cb;
        }
        
        /* Loading spinner styling */
        .loading-spinner {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-container {
                padding: 0.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 40px;
                font-size: 0.9rem;
            }
        }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'system_initialized' not in st.session_state:
            st.session_state.system_initialized = False
        
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "📈 SQL 분석"
        
        if 'user_queries' not in st.session_state:
            st.session_state.user_queries = []
        
        if 'system_health' not in st.session_state:
            st.session_state.system_health = {}
        
        if 'kpi_metrics' not in st.session_state:
            st.session_state.kpi_metrics = {}
    
    def render_main_layout(self):
        """Render main application layout"""
        # Header
        self.render_header()
        
        # Sidebar
        with st.sidebar:
            self.render_sidebar()
        
        # Main content area
        self.render_main_content()
    
    def render_header(self):
        """Render application header"""
        st.title("🏢 서울 상권분석 LLM 시스템")
        st.markdown("---")
        
        # System status indicator
        if st.session_state.system_initialized:
            st.success("✅ 시스템이 정상적으로 작동 중입니다")
        else:
            st.warning("⚠️ 시스템 초기화 중...")
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        st.header("📊 시스템 메뉴")
        
        # Tab selection
        tab = st.radio(
            "분석 모드 선택",
            ["📈 SQL 분석", "📚 문헌 검색", "📋 보고서 생성", "📊 KPI 대시보드", "🔍 시스템 상태", "⚙️ 시스템 설정"],
            index=0
        )
        
        st.session_state.current_tab = tab
        
        st.markdown("---")
        st.markdown("### 💡 사용 가이드")
        st.markdown("""
        1. **SQL 분석**: 자연어로 데이터베이스 질의
        2. **문헌 검색**: PDF 문서에서 관련 정보 검색
        3. **보고서 생성**: 종합 분석 보고서 자동 생성
        4. **KPI 대시보드**: 성능 지표 및 사용 통계
        5. **시스템 상태**: 시스템 건강 상태 및 컴포넌트 상태
        6. **시스템 설정**: 데이터베이스 및 모델 설정
        """)
        
        # System status
        st.markdown("---")
        st.markdown("### 🔧 시스템 상태")
        self.render_system_status()
    
    def render_main_content(self):
        """Render main content area based on selected tab"""
        tab = st.session_state.current_tab
        
        if tab == "📈 SQL 분석":
            self.render_sql_analysis()
        elif tab == "📚 문헌 검색":
            self.render_document_search()
        elif tab == "📋 보고서 생성":
            self.render_report_generation()
        elif tab == "📊 KPI 대시보드":
            self.render_kpi_dashboard()
        elif tab == "🔍 시스템 상태":
            self.render_health_check()
        elif tab == "⚙️ 시스템 설정":
            self.render_system_settings()
    
    def render_system_status(self):
        """Render system status in sidebar"""
        health = st.session_state.system_health
        
        if health:
            # Database status
            db_status = health.get('database', {})
            if db_status.get('status') == 'healthy':
                st.success("🗄️ 데이터베이스: 정상")
            else:
                st.error("🗄️ 데이터베이스: 오류")
            
            # LLM status
            llm_status = health.get('llm', {})
            if llm_status.get('status') == 'healthy':
                st.success("🤖 LLM: 정상")
            else:
                st.error("🤖 LLM: 오류")
            
            # RAG status
            rag_status = health.get('rag', {})
            if rag_status.get('status') == 'healthy':
                st.success("🔍 RAG: 정상")
            else:
                st.error("🔍 RAG: 오류")
        else:
            st.info("시스템 상태 확인 중...")
```

### Tab Implementation

#### SQL Analysis Tab
```python
    def render_sql_analysis(self):
        """Render SQL analysis tab"""
        st.header("📈 SQL 분석")
        st.markdown("자연어로 데이터베이스에 질의하고 결과를 분석합니다.")
        
        # Query input section
        with st.container():
            st.subheader("🔍 질의 입력")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                query = st.text_area(
                    "자연어 질의를 입력하세요:",
                    placeholder="예: 강남구에서 매출이 가장 높은 업종은 무엇인가요?",
                    height=100,
                    key="sql_query_input"
                )
            
            with col2:
                st.markdown("### 옵션")
                max_results = st.number_input("최대 결과 수", min_value=10, max_value=1000, value=100)
                include_charts = st.checkbox("차트 포함", value=True)
                st.markdown("---")
                
                if st.button("🔍 분석 실행", type="primary", use_container_width=True):
                    if query:
                        self.execute_sql_analysis(query, max_results, include_charts)
                    else:
                        st.error("질의를 입력해주세요.")
        
        # Results section
        if 'sql_results' in st.session_state:
            self.render_sql_results()
    
    def execute_sql_analysis(self, query: str, max_results: int, include_charts: bool):
        """Execute SQL analysis"""
        with st.spinner("분석 중..."):
            try:
                # Execute SQL analysis
                results = self.system.sql_service.analyze_query(query, max_results)
                
                # Store results in session state
                st.session_state.sql_results = {
                    'query': query,
                    'results': results,
                    'include_charts': include_charts,
                    'timestamp': time.time()
                }
                
                st.success("분석이 완료되었습니다!")
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
    
    def render_sql_results(self):
        """Render SQL analysis results"""
        results = st.session_state.sql_results
        
        st.subheader("📊 분석 결과")
        
        # Query display
        st.markdown(f"**질의**: {results['query']}")
        st.markdown(f"**실행 시간**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")
        
        # Results display
        if results['results']:
            df = results['results']
            
            # Data table
            st.subheader("📋 데이터 테이블")
            st.dataframe(df, use_container_width=True)
            
            # Charts
            if results['include_charts'] and len(df) > 0:
                st.subheader("📈 시각화")
                
                # Auto-generate charts based on data
                self.render_auto_charts(df)
        else:
            st.info("결과가 없습니다.")
    
    def render_auto_charts(self, df: pd.DataFrame):
        """Render auto-generated charts"""
        if len(df) == 0:
            return
        
        # Determine chart types based on data
        numeric_columns = df.select_dtypes(include=['number']).columns
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_columns) > 0 and len(categorical_columns) > 0:
            # Bar chart for categorical vs numeric
            x_col = categorical_columns[0]
            y_col = numeric_columns[0]
            
            fig = px.bar(df, x=x_col, y=y_col, title=f"{x_col}별 {y_col}")
            st.plotly_chart(fig, use_container_width=True)
        
        elif len(numeric_columns) > 1:
            # Scatter plot for numeric vs numeric
            x_col = numeric_columns[0]
            y_col = numeric_columns[1]
            
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
            st.plotly_chart(fig, use_container_width=True)
        
        elif len(numeric_columns) == 1:
            # Histogram for single numeric column
            col = numeric_columns[0]
            
            fig = px.histogram(df, x=col, title=f"{col} 분포")
            st.plotly_chart(fig, use_container_width=True)
```

#### Document Search Tab
```python
    def render_document_search(self):
        """Render document search tab"""
        st.header("📚 문헌 검색")
        st.markdown("PDF 문서에서 관련 정보를 검색합니다.")
        
        # Search input section
        with st.container():
            st.subheader("🔍 검색 입력")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_query = st.text_area(
                    "검색할 내용을 입력하세요:",
                    placeholder="예: 스타트업 지원 정책",
                    height=100,
                    key="search_query_input"
                )
            
            with col2:
                st.markdown("### 옵션")
                top_k = st.number_input("결과 수", min_value=1, max_value=20, value=5)
                search_type = st.selectbox("검색 유형", ["하이브리드", "벡터", "BM25"])
                st.markdown("---")
                
                if st.button("🔍 검색 실행", type="primary", use_container_width=True):
                    if search_query:
                        self.execute_document_search(search_query, top_k, search_type)
                    else:
                        st.error("검색어를 입력해주세요.")
        
        # Results section
        if 'search_results' in st.session_state:
            self.render_search_results()
    
    def execute_document_search(self, query: str, top_k: int, search_type: str):
        """Execute document search"""
        with st.spinner("검색 중..."):
            try:
                # Execute document search
                results = self.system.rag_service.search_documents(query, top_k, search_type)
                
                # Store results in session state
                st.session_state.search_results = {
                    'query': query,
                    'results': results,
                    'search_type': search_type,
                    'timestamp': time.time()
                }
                
                st.success(f"{len(results)}개의 결과를 찾았습니다!")
                
            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
    
    def render_search_results(self):
        """Render document search results"""
        results = st.session_state.search_results
        
        st.subheader("📋 검색 결과")
        
        # Query display
        st.markdown(f"**검색어**: {results['query']}")
        st.markdown(f"**검색 유형**: {results['search_type']}")
        st.markdown(f"**검색 시간**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")
        
        # Results display
        if results['results']:
            for i, result in enumerate(results['results'], 1):
                with st.expander(f"결과 {i} (점수: {result.get('score', 0):.3f})"):
                    st.markdown(f"**출처**: {result.get('source', 'Unknown')}")
                    st.markdown(f"**페이지**: {result.get('page', 'N/A')}")
                    
                    if result.get('text'):
                        st.markdown("**내용**:")
                        st.markdown(result['text'])
                    
                    if result.get('url'):
                        st.markdown(f"**URL**: {result['url']}")
        else:
            st.info("검색 결과가 없습니다.")
```

#### Report Generation Tab
```python
    def render_report_generation(self):
        """Render report generation tab"""
        st.header("📋 보고서 생성")
        st.markdown("SQL 분석과 문헌 검색 결과를 종합하여 보고서를 생성합니다.")
        
        # Report configuration
        with st.container():
            st.subheader("⚙️ 보고서 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                report_style = st.selectbox(
                    "보고서 스타일",
                    ["executive", "detailed", "summary"],
                    format_func=lambda x: {
                        "executive": "경영진용",
                        "detailed": "상세분석",
                        "summary": "요약본"
                    }[x]
                )
                
                include_charts = st.checkbox("차트 포함", value=True)
            
            with col2:
                include_sources = st.checkbox("출처 포함", value=True)
                include_recommendations = st.checkbox("권장사항 포함", value=True)
        
        # Data selection
        st.subheader("📊 데이터 선택")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**SQL 분석 결과**")
            if 'sql_results' in st.session_state:
                st.success("✅ SQL 분석 결과 사용 가능")
                sql_data = st.session_state.sql_results
            else:
                st.warning("⚠️ SQL 분석 결과가 없습니다")
                sql_data = None
        
        with col2:
            st.markdown("**문헌 검색 결과**")
            if 'search_results' in st.session_state:
                st.success("✅ 문헌 검색 결과 사용 가능")
                search_data = st.session_state.search_results
            else:
                st.warning("⚠️ 문헌 검색 결과가 없습니다")
                search_data = None
        
        # Generate report button
        if st.button("📋 보고서 생성", type="primary", use_container_width=True):
            if sql_data or search_data:
                self.generate_report(report_style, include_charts, include_sources, include_recommendations)
            else:
                st.error("보고서 생성을 위한 데이터가 없습니다. 먼저 SQL 분석이나 문헌 검색을 실행해주세요.")
        
        # Report display
        if 'generated_report' in st.session_state:
            self.render_generated_report()
    
    def generate_report(self, style: str, include_charts: bool, include_sources: bool, include_recommendations: bool):
        """Generate comprehensive report"""
        with st.spinner("보고서 생성 중..."):
            try:
                # Prepare data
                sql_data = st.session_state.get('sql_results')
                search_data = st.session_state.get('search_results')
                
                # Generate report
                report = self.system.report_service.generate_report(
                    sql_data=sql_data,
                    search_data=search_data,
                    style=style,
                    include_charts=include_charts,
                    include_sources=include_sources,
                    include_recommendations=include_recommendations
                )
                
                # Store report in session state
                st.session_state.generated_report = {
                    'report': report,
                    'style': style,
                    'timestamp': time.time()
                }
                
                st.success("보고서가 생성되었습니다!")
                
            except Exception as e:
                st.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")
    
    def render_generated_report(self):
        """Render generated report"""
        report_data = st.session_state.generated_report
        report = report_data['report']
        
        st.subheader("📋 생성된 보고서")
        
        # Report metadata
        st.markdown(f"**생성 시간**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report_data['timestamp']))}")
        st.markdown(f"**보고서 스타일**: {report_data['style']}")
        
        # Report content
        if report.get('markdown'):
            st.markdown(report['markdown'])
        
        # Charts
        if report.get('charts'):
            st.subheader("📈 차트")
            for chart in report['charts']:
                st.plotly_chart(chart, use_container_width=True)
        
        # Tables
        if report.get('tables'):
            st.subheader("📊 데이터 테이블")
            for table in report['tables']:
                st.dataframe(table, use_container_width=True)
        
        # Sources
        if report.get('sources'):
            st.subheader("📚 참고 문헌")
            for source in report['sources']:
                st.markdown(f"- {source}")
        
        # Download button
        if st.button("📥 보고서 다운로드"):
            self.download_report(report)
```

#### KPI Dashboard Tab
```python
    def render_kpi_dashboard(self):
        """Render KPI dashboard tab"""
        st.header("📊 KPI 대시보드")
        st.markdown("시스템 성능 지표와 사용 통계를 모니터링합니다.")
        
        # KPI metrics
        if 'kpi_metrics' in st.session_state and st.session_state.kpi_metrics:
            metrics = st.session_state.kpi_metrics
            
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Text-to-SQL 정확도",
                    f"{metrics.get('text_to_sql_accuracy', 0):.1f}%",
                    delta=f"{metrics.get('text_to_sql_accuracy_delta', 0):.1f}%"
                )
            
            with col2:
                st.metric(
                    "근거 인용률",
                    f"{metrics.get('evidence_citation_rate', 0):.1f}%",
                    delta=f"{metrics.get('evidence_citation_rate_delta', 0):.1f}%"
                )
            
            with col3:
                st.metric(
                    "응답 시간 (P95)",
                    f"{metrics.get('response_time_p95', 0):.2f}초",
                    delta=f"{metrics.get('response_time_p95_delta', 0):.2f}초"
                )
            
            with col4:
                st.metric(
                    "사용자 만족도",
                    f"{metrics.get('user_satisfaction', 0):.1f}/5.0",
                    delta=f"{metrics.get('user_satisfaction_delta', 0):.1f}"
                )
            
            # Performance trends
            st.subheader("📈 성능 트렌드")
            
            if metrics.get('performance_trends'):
                trends = metrics['performance_trends']
                
                # Create trend charts
                self.render_performance_trends(trends)
            
            # Usage statistics
            st.subheader("📊 사용 통계")
            
            if metrics.get('usage_stats'):
                usage = metrics['usage_stats']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**일일 사용량**")
                    st.metric("총 쿼리 수", usage.get('daily_queries', 0))
                    st.metric("고유 사용자", usage.get('daily_users', 0))
                
                with col2:
                    st.markdown("**주간 사용량**")
                    st.metric("총 쿼리 수", usage.get('weekly_queries', 0))
                    st.metric("고유 사용자", usage.get('weekly_users', 0))
        else:
            st.info("KPI 데이터를 로딩 중...")
            
            if st.button("🔄 데이터 새로고침"):
                self.refresh_kpi_data()
    
    def render_performance_trends(self, trends: Dict[str, Any]):
        """Render performance trend charts"""
        if not trends:
            return
        
        # Response time trend
        if trends.get('response_time'):
            fig = px.line(
                trends['response_time'], 
                x='timestamp', 
                y='value',
                title='응답 시간 트렌드'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Accuracy trend
        if trends.get('accuracy'):
            fig = px.line(
                trends['accuracy'], 
                x='timestamp', 
                y='value',
                title='정확도 트렌드'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def refresh_kpi_data(self):
        """Refresh KPI data"""
        with st.spinner("KPI 데이터를 새로고침 중..."):
            try:
                # Fetch latest KPI data
                kpi_data = self.system.kpi_service.get_latest_metrics()
                
                # Update session state
                st.session_state.kpi_metrics = kpi_data
                
                st.success("KPI 데이터가 새로고침되었습니다!")
                
            except Exception as e:
                st.error(f"KPI 데이터 새로고침 중 오류가 발생했습니다: {str(e)}")
```

### Performance Optimization

#### Caching Implementation
```python
import functools
from typing import Any, Callable

class StreamlitCache:
    """Streamlit caching utilities"""
    
    @staticmethod
    def cache_data(ttl: int = 3600):
        """Cache data with TTL"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # Check if data is in session state
                if cache_key in st.session_state:
                    cached_data = st.session_state[cache_key]
                    if time.time() - cached_data['timestamp'] < ttl:
                        return cached_data['data']
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                st.session_state[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def clear_cache(pattern: str = None):
        """Clear cache entries"""
        if pattern:
            keys_to_remove = [key for key in st.session_state.keys() if pattern in key]
        else:
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('cache_')]
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        cache_keys = [key for key in st.session_state.keys() if key.startswith('cache_')]
        
        total_size = 0
        for key in cache_keys:
            if isinstance(st.session_state[key], dict):
                total_size += len(str(st.session_state[key]))
        
        return {
            'total_entries': len(cache_keys),
            'total_size': total_size,
            'entries': cache_keys
        }

# Usage example
@StreamlitCache.cache_data(ttl=1800)  # Cache for 30 minutes
def expensive_data_processing(query: str) -> pd.DataFrame:
    """Expensive data processing function"""
    # Simulate expensive operation
    time.sleep(2)
    return pd.DataFrame({'result': [1, 2, 3, 4, 5]})
```

#### State Management
```python
class StreamlitState:
    """Streamlit state management utilities"""
    
    @staticmethod
    def get_state(key: str, default: Any = None) -> Any:
        """Get state value"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set_state(key: str, value: Any):
        """Set state value"""
        st.session_state[key] = value
    
    @staticmethod
    def update_state(key: str, updates: Dict[str, Any]):
        """Update state dictionary"""
        if key not in st.session_state:
            st.session_state[key] = {}
        
        st.session_state[key].update(updates)
    
    @staticmethod
    def clear_state(key: str = None):
        """Clear state"""
        if key:
            if key in st.session_state:
                del st.session_state[key]
        else:
            st.session_state.clear()
    
    @staticmethod
    def get_state_info() -> Dict[str, Any]:
        """Get state information"""
        return {
            'total_keys': len(st.session_state),
            'keys': list(st.session_state.keys()),
            'memory_usage': len(str(st.session_state))
        }
```

### Error Handling in UI

#### UI Error Handling
```python
class UIErrorHandler:
    """UI-specific error handling"""
    
    @staticmethod
    def handle_error(error: Exception, context: str = "알 수 없는 오류"):
        """Handle and display errors in UI"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Display error message
        st.error(f"❌ {context}: {error_message}")
        
        # Show error details in expander
        with st.expander("🔍 오류 상세 정보"):
            st.code(f"오류 유형: {error_type}")
            st.code(f"오류 메시지: {error_message}")
            
            # Show stack trace for debugging
            import traceback
            st.code(traceback.format_exc())
        
        # Provide recovery suggestions
        st.markdown("### 💡 해결 방법")
        
        if "connection" in error_message.lower():
            st.markdown("- 네트워크 연결을 확인해주세요")
            st.markdown("- 잠시 후 다시 시도해주세요")
        elif "timeout" in error_message.lower():
            st.markdown("- 요청이 너무 복잡할 수 있습니다")
            st.markdown("- 더 간단한 질의를 시도해주세요")
        elif "validation" in error_message.lower():
            st.markdown("- 입력 형식을 확인해주세요")
            st.markdown("- 필수 필드가 모두 입력되었는지 확인해주세요")
        else:
            st.markdown("- 페이지를 새로고침해주세요")
            st.markdown("- 문제가 지속되면 관리자에게 문의해주세요")
    
    @staticmethod
    def show_loading_state(operation: str):
        """Show loading state"""
        with st.spinner(f"{operation} 중..."):
            pass
    
    @staticmethod
    def show_success_message(message: str):
        """Show success message"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_warning_message(message: str):
        """Show warning message"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info_message(message: str):
        """Show info message"""
        st.info(f"ℹ️ {message}")
```

## UI Testing

### UI Test Suite
```python
import pytest
from unittest.mock import Mock, patch
import streamlit as st

class TestStreamlitUI:
    """Test Streamlit UI functionality"""
    
    def test_page_config_setup(self):
        """Test page configuration setup"""
        ui = StreamlitUI()
        
        # Test that page config is set
        assert hasattr(ui, 'setup_page_config')
    
    def test_session_state_initialization(self):
        """Test session state initialization"""
        ui = StreamlitUI()
        
        # Test that session state is initialized
        assert 'system_initialized' in st.session_state
        assert 'current_tab' in st.session_state
        assert 'user_queries' in st.session_state
    
    def test_error_handling(self):
        """Test UI error handling"""
        error_handler = UIErrorHandler()
        
        # Test error handling
        test_error = ValueError("Test error")
        error_handler.handle_error(test_error, "테스트 오류")
        
        # Should not raise exception
        assert True
    
    def test_cache_functionality(self):
        """Test caching functionality"""
        cache = StreamlitCache()
        
        # Test cache decorator
        @cache.cache_data(ttl=60)
        def test_function(x):
            return x * 2
        
        # First call should execute function
        result1 = test_function(5)
        assert result1 == 10
        
        # Second call should use cache
        result2 = test_function(5)
        assert result2 == 10
    
    def test_state_management(self):
        """Test state management"""
        state = StreamlitState()
        
        # Test setting and getting state
        state.set_state('test_key', 'test_value')
        assert state.get_state('test_key') == 'test_value'
        
        # Test updating state
        state.update_state('test_dict', {'key1': 'value1'})
        assert state.get_state('test_dict')['key1'] == 'value1'
        
        # Test clearing state
        state.clear_state('test_key')
        assert state.get_state('test_key') is None
```

## Consequences

### Positive
- **Better User Experience**: Intuitive and responsive interface
- **Improved Performance**: Optimized UI with caching and state management
- **Enhanced Accessibility**: Better accessibility and usability
- **Consistent Design**: Consistent visual design and user experience
- **Error Resilience**: Better error handling and user guidance

### Negative
- **Complexity**: More complex UI code and state management
- **Performance Overhead**: UI optimizations may add complexity
- **Maintenance**: More UI code to maintain and test
- **Browser Compatibility**: Need to ensure cross-browser compatibility

### Risks
- **State Management Issues**: Complex state management may cause bugs
- **Performance Degradation**: UI optimizations may not work as expected
- **User Confusion**: Complex UI may confuse users
- **Accessibility Issues**: UI may not be accessible to all users

## Success Metrics

### UI Performance Metrics
- **Page Load Time**: <2s for initial page load
- **Response Time**: <1s for user interactions
- **Cache Hit Rate**: >80% for cached operations
- **State Management**: <100ms for state updates

### User Experience Metrics
- **User Satisfaction**: >4.0/5.0 rating
- **Error Rate**: <5% of user interactions result in errors
- **Accessibility Score**: >90% accessibility compliance
- **Usability Score**: >85% usability rating

## Implementation Timeline

### Phase 1: Basic UI Structure (Week 1)
- [x] Implement main application layout
- [x] Create tab-based navigation
- [x] Set up basic styling and CSS

### Phase 2: Tab Implementation (Week 2)
- [x] Implement SQL analysis tab
- [x] Implement document search tab
- [x] Implement report generation tab

### Phase 3: Performance Optimization (Week 3)
- [ ] Implement caching system
- [ ] Add state management
- [ ] Optimize UI performance

### Phase 4: Testing & Polish (Week 4)
- [ ] Implement UI testing
- [ ] Add error handling
- [ ] Polish user experience

## References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Best Practices](https://docs.streamlit.io/knowledge-base/tutorials/best-practices)
- [Streamlit Performance](https://docs.streamlit.io/knowledge-base/tutorials/performance)
- [Streamlit State Management](https://docs.streamlit.io/knowledge-base/tutorials/session-state)
- [Streamlit Caching](https://docs.streamlit.io/knowledge-base/tutorials/caching)
