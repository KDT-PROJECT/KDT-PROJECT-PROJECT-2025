"""
서울 상권 분석 지도 시각화 앱
구글맵 기반 상권 데이터 시각화
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from components.seoul_map_visualization import SeoulMapVisualization

def main():
    """메인 앱 함수"""
    st.set_page_config(
        page_title="서울 상권 지도 분석",
        page_icon="🗺️",
        layout="wide"
    )
    
    st.title("🗺️ 서울 상권 지도 분석")
    st.markdown("### 구글맵 기반 상권 데이터 시각화 및 분석")
    st.markdown("---")
    
    # 지도 시각화 초기화
    map_viz = SeoulMapVisualization()
    
    # 사이드바 옵션
    with st.sidebar:
        st.header("🗺️ 지도 설정")
        
        # 지도 옵션
        show_markers = st.checkbox("마커 표시", value=True)
        show_heatmap = st.checkbox("히트맵 표시", value=True)
        use_sample_data = st.checkbox("샘플 데이터 사용", value=True)
        
        # 분석 옵션
        st.header("📊 분석 옵션")
        show_district_analysis = st.checkbox("구별 분석 표시", value=True)
        show_charts = st.checkbox("차트 표시", value=True)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 지도 시각화
        st.subheader("🗺️ 서울 상권 지도")
        
        # 데이터 로드
        if use_sample_data:
            commercial_data = map_viz.get_sample_data()
            st.info("샘플 데이터를 사용하고 있습니다.")
        else:
            # 실제 데이터 로드 (세션 상태에서)
            if 'last_sql_df' in st.session_state and st.session_state.last_sql_df is not None:
                commercial_data = st.session_state.last_sql_df
                st.info("최근 SQL 분석 결과를 지도에 표시합니다.")
            else:
                commercial_data = map_viz.get_sample_data()
                st.warning("분석 데이터가 없어 샘플 데이터를 사용합니다.")
        
        # 지도 생성 및 표시
        if not commercial_data.empty:
            # 지도 생성
            m = map_viz.create_commercial_analysis_map(
                commercial_data, 
                show_heatmap=show_heatmap,
                show_markers=show_markers
            )
            
            # 지도 표시
            from streamlit_folium import st_folium
            st_folium(m, width=700, height=500)
        else:
            st.warning("표시할 상권 데이터가 없습니다.")
    
    with col2:
        # 데이터 요약
        st.subheader("📊 상권 데이터 요약")
        
        if not commercial_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("총 상권 수", len(commercial_data))
                total_sales = commercial_data['sales_amount'].sum()
                st.metric("총 매출액", f"₩{total_sales:,.0f}")
            
            with col2:
                avg_sales = commercial_data['sales_amount'].mean()
                st.metric("평균 매출액", f"₩{avg_sales:,.0f}")
                total_transactions = commercial_data['transaction_count'].sum()
                st.metric("총 거래건수", f"{total_transactions:,}건")
            
            # 상위 상권
            st.subheader("🏆 상위 상권")
            top_commercial = commercial_data.nlargest(3, 'sales_amount')
            for idx, row in top_commercial.iterrows():
                st.write(f"**{row['name']}**")
                st.write(f"매출: ₩{row['sales_amount']:,.0f}")
                st.write(f"거래건수: {row['transaction_count']:,}건")
                st.write("---")
    
    # 구별 분석
    if show_district_analysis and not commercial_data.empty:
        st.subheader("📈 구별 상권 분석")
        
        district_analysis = map_viz.get_district_analysis(commercial_data)
        
        if not district_analysis.empty:
            # 구별 분석 테이블
            st.dataframe(district_analysis, use_container_width=True)
            
            if show_charts:
                # 구별 매출액 차트
                st.subheader("구별 총 매출액 비교")
                fig = px.bar(
                    district_analysis, 
                    x='district', 
                    y='총_매출액',
                    title='구별 총 매출액',
                    color='총_매출액',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    xaxis_title="구",
                    yaxis_title="총 매출액 (원)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 구별 상권 수 차트
                st.subheader("구별 상권 수 비교")
                fig2 = px.pie(
                    district_analysis, 
                    values='상권_수', 
                    names='district',
                    title='구별 상권 수 분포'
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    # 상세 데이터 테이블
    st.subheader("📋 상권 상세 정보")
    if not commercial_data.empty:
        st.dataframe(commercial_data, use_container_width=True)
    
    # 추가 기능
    st.subheader("🔧 추가 기능")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("샘플 데이터 새로고침"):
            st.rerun()
    
    with col2:
        if st.button("지도 확대"):
            st.info("지도를 확대하여 상세 정보를 확인하세요.")
    
    with col3:
        if st.button("데이터 내보내기"):
            csv = commercial_data.to_csv(index=False)
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name=f"seoul_commercial_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # 푸터
    st.markdown("---")
    st.markdown("**서울 상권 분석 LLM** | Powered by AI & Google Maps")

if __name__ == "__main__":
    main()
