"""
서울 상권 분석 지도 시각화 컴포넌트
Google Maps API를 사용한 상권 데이터 시각화
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import googlemaps
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import json

class SeoulMapVisualization:
    """서울 상권 분석 지도 시각화 클래스"""
    
    def __init__(self, google_maps_api_key: Optional[str] = None):
        """
        지도 시각화 초기화
        
        Args:
            google_maps_api_key: Google Maps API 키
        """
        self.google_maps_api_key = google_maps_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.gmaps = googlemaps.Client(key=self.google_maps_api_key) if self.google_maps_api_key else None
        
        # 서울 중심 좌표
        self.seoul_center = [37.5665, 126.9780]
        
        # 서울 구별 좌표 데이터
        self.seoul_districts = {
            "강남구": [37.5172, 127.0473],
            "강동구": [37.5301, 127.1238],
            "강북구": [37.6399, 127.0253],
            "강서구": [37.5509, 126.8495],
            "관악구": [37.4784, 126.9515],
            "광진구": [37.5385, 127.0823],
            "구로구": [37.4954, 126.8874],
            "금천구": [37.4563, 126.8953],
            "노원구": [37.6542, 127.0568],
            "도봉구": [37.6688, 127.0472],
            "동대문구": [37.5838, 127.0507],
            "동작구": [37.5124, 126.9395],
            "마포구": [37.5663, 126.9019],
            "서대문구": [37.5791, 126.9368],
            "서초구": [37.4837, 127.0324],
            "성동구": [37.5636, 127.0365],
            "성북구": [37.5894, 127.0167],
            "송파구": [37.5145, 127.1058],
            "양천구": [37.5170, 126.8666],
            "영등포구": [37.5264, 126.8962],
            "용산구": [37.5384, 126.9654],
            "은평구": [37.6028, 126.9291],
            "종로구": [37.5735, 126.9788],
            "중구": [37.5636, 126.9976],
            "중랑구": [37.6066, 127.0926]
        }
    
    def create_base_map(self, zoom_start: int = 11) -> folium.Map:
        """
        서울 중심의 기본 지도 생성
        
        Args:
            zoom_start: 초기 줌 레벨
            
        Returns:
            folium.Map: 기본 지도 객체
        """
        m = folium.Map(
            location=self.seoul_center,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Google Maps 타일 추가 (API 키가 있는 경우)
        if self.google_maps_api_key:
            folium.TileLayer(
                tiles=f'https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={self.google_maps_api_key}',
                attr='Google Maps',
                name='Google Maps',
                overlay=True,
                control=True
            ).add_to(m)
        
        return m
    
    def add_commercial_districts(self, map_obj: folium.Map, commercial_data: pd.DataFrame) -> folium.Map:
        """
        상권 데이터를 지도에 마커로 추가
        
        Args:
            map_obj: folium 지도 객체
            commercial_data: 상권 데이터 DataFrame
            
        Returns:
            folium.Map: 마커가 추가된 지도 객체
        """
        # 색상 팔레트 정의
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
                 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
                 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        
        for idx, row in commercial_data.iterrows():
            # 좌표 설정
            lat = row.get('latitude', self.seoul_center[0])
            lon = row.get('longitude', self.seoul_center[1])
            
            # 구별 좌표가 없는 경우 구별 좌표 사용
            if pd.isna(lat) or pd.isna(lon):
                district = row.get('district', '강남구')
                if district in self.seoul_districts:
                    lat, lon = self.seoul_districts[district]
                else:
                    continue
            
            # 매출액에 따른 색상 결정
            sales_amount = row.get('sales_amount', 0)
            if sales_amount > 1000000000:  # 10억 이상
                color = 'red'
                size = 15
            elif sales_amount > 500000000:  # 5억 이상
                color = 'orange'
                size = 12
            elif sales_amount > 100000000:  # 1억 이상
                color = 'yellow'
                size = 10
            else:
                color = 'green'
                size = 8
            
            # 팝업 정보 생성
            popup_text = f"""
            <div style="width: 200px;">
                <h4>{row.get('name', '상권')}</h4>
                <p><b>지역:</b> {row.get('district', 'N/A')}</p>
                <p><b>업종:</b> {row.get('industry', 'N/A')}</p>
                <p><b>매출액:</b> ₩{sales_amount:,.0f}</p>
                <p><b>거래건수:</b> {row.get('transaction_count', 0):,}건</p>
                <p><b>평균 거래액:</b> ₩{row.get('avg_transaction', 0):,.0f}</p>
            </div>
            """
            
            # 마커 추가
            folium.CircleMarker(
                location=[lat, lon],
                radius=size,
                popup=folium.Popup(popup_text, max_width=250),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{row.get('name', '상권')} - ₩{sales_amount:,.0f}"
            ).add_to(map_obj)
        
        return map_obj
    
    def add_heatmap_layer(self, map_obj: folium.Map, commercial_data: pd.DataFrame) -> folium.Map:
        """
        상권 데이터 히트맵 레이어 추가
        
        Args:
            map_obj: folium 지도 객체
            commercial_data: 상권 데이터 DataFrame
            
        Returns:
            folium.Map: 히트맵이 추가된 지도 객체
        """
        from folium.plugins import HeatMap
        
        # 히트맵 데이터 준비
        heat_data = []
        for idx, row in commercial_data.iterrows():
            lat = row.get('latitude', self.seoul_center[0])
            lon = row.get('longitude', self.seoul_center[1])
            sales_amount = row.get('sales_amount', 0)
            
            # 구별 좌표가 없는 경우 구별 좌표 사용
            if pd.isna(lat) or pd.isna(lon):
                district = row.get('district', '강남구')
                if district in self.seoul_districts:
                    lat, lon = self.seoul_districts[district]
                else:
                    continue
            
            # 매출액을 가중치로 사용
            weight = min(sales_amount / 1000000000, 10)  # 최대 10으로 제한
            heat_data.append([lat, lon, weight])
        
        # 히트맵 추가
        HeatMap(
            heat_data,
            name='상권 매출 히트맵',
            min_opacity=0.2,
            max_zoom=18,
            radius=25,
            blur=15,
            gradient={0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1.0: 'red'}
        ).add_to(map_obj)
        
        return map_obj
    
    def add_district_boundaries(self, map_obj: folium.Map) -> folium.Map:
        """
        서울 구별 경계선 추가
        
        Args:
            map_obj: folium 지도 객체
            
        Returns:
            folium.Map: 경계선이 추가된 지도 객체
        """
        # 구별 중심점에 마커 추가
        for district, coords in self.seoul_districts.items():
            folium.Marker(
                location=coords,
                popup=f"<b>{district}</b>",
                icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')
            ).add_to(map_obj)
        
        return map_obj
    
    def create_commercial_analysis_map(self, commercial_data: pd.DataFrame, 
                                     show_heatmap: bool = True,
                                     show_markers: bool = True) -> folium.Map:
        """
        상권 분석 지도 생성
        
        Args:
            commercial_data: 상권 데이터 DataFrame
            show_heatmap: 히트맵 표시 여부
            show_markers: 마커 표시 여부
            
        Returns:
            folium.Map: 완성된 지도 객체
        """
        # 기본 지도 생성
        m = self.create_base_map()
        
        # 구별 경계선 추가
        m = self.add_district_boundaries(m)
        
        # 마커 추가
        if show_markers and not commercial_data.empty:
            m = self.add_commercial_districts(m, commercial_data)
        
        # 히트맵 추가
        if show_heatmap and not commercial_data.empty:
            m = self.add_heatmap_layer(m, commercial_data)
        
        # 레이어 컨트롤 추가
        folium.LayerControl().add_to(m)
        
        return m
    
    def get_sample_data(self) -> pd.DataFrame:
        """
        샘플 상권 데이터 생성
        
        Returns:
            pd.DataFrame: 샘플 상권 데이터
        """
        sample_data = [
            {
                'name': '강남역 상권',
                'district': '강남구',
                'industry': '소매업',
                'sales_amount': 1500000000,
                'transaction_count': 5000,
                'avg_transaction': 300000,
                'latitude': 37.4979,
                'longitude': 127.0276
            },
            {
                'name': '홍대 상권',
                'district': '마포구',
                'industry': '음식점업',
                'sales_amount': 800000000,
                'transaction_count': 3000,
                'avg_transaction': 266667,
                'latitude': 37.5563,
                'longitude': 126.9226
            },
            {
                'name': '명동 상권',
                'district': '중구',
                'industry': '소매업',
                'sales_amount': 1200000000,
                'transaction_count': 4000,
                'avg_transaction': 300000,
                'latitude': 37.5636,
                'longitude': 126.9826
            },
            {
                'name': '잠실 상권',
                'district': '송파구',
                'industry': '소매업',
                'sales_amount': 900000000,
                'transaction_count': 3500,
                'avg_transaction': 257143,
                'latitude': 37.5133,
                'longitude': 127.1028
            },
            {
                'name': '건대 상권',
                'district': '광진구',
                'industry': '음식점업',
                'sales_amount': 600000000,
                'transaction_count': 2500,
                'avg_transaction': 240000,
                'latitude': 37.5403,
                'longitude': 127.0693
            }
        ]
        
        return pd.DataFrame(sample_data)
    
    def render_map_interface(self):
        """
        Streamlit에서 지도 인터페이스 렌더링
        """
        st.subheader("🗺️ 서울 상권 분석 지도")
        
        # 지도 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            show_markers = st.checkbox("마커 표시", value=True)
        with col2:
            show_heatmap = st.checkbox("히트맵 표시", value=True)
        with col3:
            use_sample_data = st.checkbox("샘플 데이터 사용", value=True)
        
        # 데이터 로드
        if use_sample_data:
            commercial_data = self.get_sample_data()
            st.info("샘플 데이터를 사용하고 있습니다.")
        else:
            # 실제 데이터 로드 (세션 상태에서)
            if 'last_sql_df' in st.session_state and st.session_state.last_sql_df is not None:
                commercial_data = st.session_state.last_sql_df
                st.info("최근 SQL 분석 결과를 지도에 표시합니다.")
            else:
                commercial_data = self.get_sample_data()
                st.warning("분석 데이터가 없어 샘플 데이터를 사용합니다.")
        
        # 지도 생성 및 표시
        if not commercial_data.empty:
            # 지도 생성
            m = self.create_commercial_analysis_map(
                commercial_data, 
                show_heatmap=show_heatmap,
                show_markers=show_markers
            )
            
            # 지도 표시
            st_folium(m, width=700, height=500)
            
            # KPI 대시보드 메트릭
            self._render_kpi_metrics(commercial_data)
            
            # 구별 분석 차트
            self._render_district_analysis_charts(commercial_data)
            
            # 상세 데이터 테이블
            st.subheader("📋 상권 상세 정보")
            st.dataframe(commercial_data, use_container_width=True)
            
        else:
            st.warning("표시할 상권 데이터가 없습니다.")

    def _render_kpi_metrics(self, commercial_data: pd.DataFrame):
        """KPI 메트릭 렌더링"""
        st.subheader("📊 상권 KPI 메트릭")
        
        # 메인 KPI 카드들
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 상권 수", len(commercial_data))
        with col2:
            total_sales = commercial_data['sales_amount'].sum()
            st.metric("총 매출액", f"₩{total_sales:,.0f}")
        with col3:
            avg_sales = commercial_data['sales_amount'].mean()
            st.metric("평균 매출액", f"₩{avg_sales:,.0f}")
        with col4:
            total_transactions = commercial_data['transaction_count'].sum()
            st.metric("총 거래건수", f"{total_transactions:,}건")
        
        # 추가 KPI 메트릭
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            max_sales = commercial_data['sales_amount'].max()
            st.metric("최대 매출액", f"₩{max_sales:,.0f}")
        with col6:
            min_sales = commercial_data['sales_amount'].min()
            st.metric("최소 매출액", f"₩{min_sales:,.0f}")
        with col7:
            avg_transaction = commercial_data['avg_transaction'].mean()
            st.metric("평균 거래액", f"₩{avg_transaction:,.0f}")
        with col8:
            unique_districts = commercial_data['district'].nunique()
            st.metric("활성 구역", f"{unique_districts}개")

    def _render_district_analysis_charts(self, commercial_data: pd.DataFrame):
        """구별 분석 차트 렌더링"""
        st.subheader("📈 구별 상권 분석")
        
        # 구별 분석 데이터 생성
        district_analysis = self.get_district_analysis(commercial_data)
        
        if not district_analysis.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # 구별 매출액 막대 차트
                import plotly.express as px
                fig1 = px.bar(
                    district_analysis, 
                    x='district', 
                    y='총_매출액',
                    title="구별 총 매출액",
                    color='총_매출액',
                    color_continuous_scale='Viridis'
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # 구별 상권 수 파이 차트
                fig2 = px.pie(
                    district_analysis, 
                    values='상권_수', 
                    names='district',
                    title="구별 상권 수 분포"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # 구별 상세 분석 테이블
            st.subheader("📋 구별 상세 분석")
            st.dataframe(district_analysis, use_container_width=True)
    
    def get_district_analysis(self, commercial_data: pd.DataFrame) -> pd.DataFrame:
        """
        구별 상권 분석 데이터 생성
        
        Args:
            commercial_data: 상권 데이터 DataFrame
            
        Returns:
            pd.DataFrame: 구별 분석 결과
        """
        if commercial_data.empty:
            return pd.DataFrame()
        
        district_analysis = commercial_data.groupby('district').agg({
            'sales_amount': ['sum', 'mean', 'count'],
            'transaction_count': 'sum',
            'avg_transaction': 'mean'
        }).round(0)
        
        # 컬럼명 정리
        district_analysis.columns = [
            '총_매출액', '평균_매출액', '상권_수',
            '총_거래건수', '평균_거래액'
        ]
        
        district_analysis = district_analysis.reset_index()
        district_analysis = district_analysis.sort_values('총_매출액', ascending=False)
        
        return district_analysis
