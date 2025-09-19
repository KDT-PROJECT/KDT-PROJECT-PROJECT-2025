"""
맥킨지 컨설팅 스타일 시각화 모듈
PRD TASK3: 맥킨지 스타일 보고서 및 대시보드 구현
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

# 맥킨지 컬러 팔레트
MCKINSEY_COLORS = {
    'primary': '#1f4e79',      # 진한 파란색
    'secondary': '#2e75b6',    # 중간 파란색
    'accent': '#70ad47',       # 녹색
    'warning': '#ffc000',      # 노란색
    'danger': '#c55a5a',       # 빨간색
    'light': '#d9e2f3',        # 연한 파란색
    'dark': '#2f2f2f',         # 어두운 회색
    'gray': '#7f7f7f',         # 회색
    'light_gray': '#f2f2f2'    # 연한 회색
}

class McKinseyVisualizer:
    """맥킨지 스타일 시각화 클래스"""
    
    def __init__(self):
        """시각화 클래스 초기화"""
        self.colors = MCKINSEY_COLORS
        self.font_family = "Arial, sans-serif"
        self.title_font_size = 16
        self.axis_font_size = 12
        self.legend_font_size = 11
    
    def create_executive_summary_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        경영진 요약 차트 생성
        
        Args:
            data: 요약 데이터
            
        Returns:
            Plotly Figure 객체
        """
        try:
            # KPI 카드들
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=("총 매출", "성장률", "지역 수", "업종 수", "평균 매출", "최고 성과 지역"),
                specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                       [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
            )
            
            # KPI 값들 (실제 데이터가 없으면 샘플 데이터 사용)
            kpis = {
                "총 매출": data.get("total_sales", 1250000000000),  # 1.25조원
                "성장률": data.get("growth_rate", 12.5),  # 12.5%
                "지역 수": data.get("region_count", 25),
                "업종 수": data.get("industry_count", 8),
                "평균 매출": data.get("avg_sales", 50000000000),  # 500억원
                "최고 성과 지역": data.get("top_region", "강남구")
            }
            
            # 각 KPI 카드 생성
            for i, (title, value) in enumerate(kpis.items()):
                row = (i // 3) + 1
                col = (i % 3) + 1
                
                if i == 0:  # 총 매출
                    fig.add_trace(go.Indicator(
                        mode="number+delta",
                        value=value,
                        number={'prefix': "₩", 'suffix': "조", 'valueformat': ".1f"},
                        delta={'reference': value * 0.9, 'valueformat': ".1%"},
                        title={'text': title, 'font': {'size': 14}},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ), row=row, col=col)
                elif i == 1:  # 성장률
                    fig.add_trace(go.Indicator(
                        mode="number+delta",
                        value=value,
                        number={'suffix': "%", 'valueformat': ".1f"},
                        delta={'reference': value - 2, 'valueformat': ".1%"},
                        title={'text': title, 'font': {'size': 14}},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ), row=row, col=col)
                else:
                    fig.add_trace(go.Indicator(
                        mode="number",
                        value=value,
                        title={'text': title, 'font': {'size': 14}},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ), row=row, col=col)
            
            # 레이아웃 설정
            fig.update_layout(
                height=400,
                showlegend=False,
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"경영진 요약 차트 생성 실패: {str(e)}")
            return go.Figure()
    
    def create_trend_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        트렌드 분석 차트 생성
        
        Args:
            df: 시계열 데이터프레임
            
        Returns:
            Plotly Figure 객체
        """
        try:
            if df.empty:
                return go.Figure()
            
            # 월별 매출 트렌드
            fig = go.Figure()
            
            # 실제 데이터가 있으면 사용, 없으면 샘플 데이터 생성
            if 'date' in df.columns and 'sales_amt' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                monthly_sales = df.groupby(df['date'].dt.to_period('M'))['sales_amt'].sum().reset_index()
                monthly_sales['date'] = monthly_sales['date'].dt.to_timestamp()
                
                fig.add_trace(go.Scatter(
                    x=monthly_sales['date'],
                    y=monthly_sales['sales_amt'],
                    mode='lines+markers',
                    name='월별 매출',
                    line=dict(color=self.colors['primary'], width=3),
                    marker=dict(size=8, color=self.colors['primary'])
                ))
            else:
                # 샘플 데이터 생성
                dates = pd.date_range('2024-01-01', '2024-12-31', freq='M')
                sales = np.random.normal(100000000000, 20000000000, len(dates)).cumsum()
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=sales,
                    mode='lines+markers',
                    name='월별 매출',
                    line=dict(color=self.colors['primary'], width=3),
                    marker=dict(size=8, color=self.colors['primary'])
                ))
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': '월별 매출 트렌드 분석',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': self.title_font_size, 'color': self.colors['dark']}
                },
                xaxis_title='월',
                yaxis_title='매출 (원)',
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white',
                height=400,
                showlegend=True
            )
            
            # Y축 포맷팅
            fig.update_yaxis(tickformat='.0f')
            
            return fig
            
        except Exception as e:
            logger.error(f"트렌드 분석 차트 생성 실패: {str(e)}")
            return go.Figure()
    
    def create_regional_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        지역별 분석 차트 생성
        
        Args:
            df: 지역별 데이터프레임
            
        Returns:
            Plotly Figure 객체
        """
        try:
            if df.empty:
                return go.Figure()
            
            # 지역별 매출 데이터 준비
            if 'region' in df.columns and 'sales_amt' in df.columns:
                regional_data = df.groupby('region')['sales_amt'].sum().sort_values(ascending=True)
            else:
                # 샘플 데이터 생성
                regions = ['강남구', '마포구', '서초구', '송파구', '영등포구', '강동구', '서대문구', '종로구']
                regional_data = pd.Series(
                    np.random.normal(100000000000, 20000000000, len(regions)),
                    index=regions
                ).sort_values(ascending=True)
            
            # 맥킨지 스타일 바 차트
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=regional_data.index,
                x=regional_data.values,
                orientation='h',
                marker=dict(
                    color=regional_data.values,
                    colorscale='Blues',
                    showscale=True,
                    colorbar=dict(title="매출 (원)")
                ),
                text=[f"₩{x:,.0f}" for x in regional_data.values],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>매출: ₩%{x:,.0f}<extra></extra>'
            ))
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': '지역별 매출 분석',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': self.title_font_size, 'color': self.colors['dark']}
                },
                xaxis_title='매출 (원)',
                yaxis_title='지역',
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white',
                height=500,
                showlegend=False,
                margin=dict(l=100, r=50, t=80, b=50)
            )
            
            # X축 포맷팅
            fig.update_xaxis(tickformat='.0f')
            
            return fig
            
        except Exception as e:
            logger.error(f"지역별 분석 차트 생성 실패: {str(e)}")
            return go.Figure()
    
    def create_industry_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        업종별 분석 차트 생성
        
        Args:
            df: 업종별 데이터프레임
            
        Returns:
            Plotly Figure 객체
        """
        try:
            if df.empty:
                return go.Figure()
            
            # 업종별 매출 데이터 준비
            if 'industry' in df.columns and 'sales_amt' in df.columns:
                industry_data = df.groupby('industry')['sales_amt'].sum()
            else:
                # 샘플 데이터 생성
                industries = ['소매업', '음식업', '서비스업', '제조업', '건설업', 'IT업', '금융업', '교육업']
                industry_data = pd.Series(
                    np.random.normal(150000000000, 30000000000, len(industries)),
                    index=industries
                )
            
            # 파이 차트 생성
            fig = go.Figure(data=[go.Pie(
                labels=industry_data.index,
                values=industry_data.values,
                hole=0.4,
                marker=dict(
                    colors=[self.colors['primary'], self.colors['secondary'], 
                           self.colors['accent'], self.colors['warning'],
                           self.colors['danger'], self.colors['light'],
                           self.colors['gray'], self.colors['light_gray']]
                ),
                textinfo='label+percent',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>매출: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>'
            )])
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': '업종별 매출 구성',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': self.title_font_size, 'color': self.colors['dark']}
                },
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white',
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.01
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"업종별 분석 차트 생성 실패: {str(e)}")
            return go.Figure()
    
    def create_heatmap_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        히트맵 차트 생성 (지역별 x 업종별)
        
        Args:
            df: 지역-업종별 데이터프레임
            
        Returns:
            Plotly Figure 객체
        """
        try:
            if df.empty:
                return go.Figure()
            
            # 피벗 테이블 생성
            if all(col in df.columns for col in ['region', 'industry', 'sales_amt']):
                pivot_data = df.pivot_table(
                    values='sales_amt', 
                    index='region', 
                    columns='industry', 
                    aggfunc='sum', 
                    fill_value=0
                )
            else:
                # 샘플 데이터 생성
                regions = ['강남구', '마포구', '서초구', '송파구', '영등포구']
                industries = ['소매업', '음식업', '서비스업', '제조업', 'IT업']
                pivot_data = pd.DataFrame(
                    np.random.normal(100000000000, 20000000000, (len(regions), len(industries))),
                    index=regions,
                    columns=industries
                )
            
            # 히트맵 생성
            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="매출 (원)"),
                hovertemplate='<b>%{y} - %{x}</b><br>매출: ₩%{z:,.0f}<extra></extra>'
            ))
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': '지역별 x 업종별 매출 히트맵',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': self.title_font_size, 'color': self.colors['dark']}
                },
                xaxis_title='업종',
                yaxis_title='지역',
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"히트맵 차트 생성 실패: {str(e)}")
            return go.Figure()
    
    def create_insights_dashboard(self, data: Dict[str, Any]) -> go.Figure:
        """
        인사이트 대시보드 생성
        
        Args:
            data: 분석 데이터
            
        Returns:
            Plotly Figure 객체
        """
        try:
            # 2x2 서브플롯 생성
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("주요 KPI", "트렌드 분석", "지역별 분석", "업종별 분석"),
                specs=[[{"type": "indicator"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "pie"}]]
            )
            
            # KPI 인디케이터
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=data.get("total_sales", 1250000000000),
                number={'prefix': "₩", 'suffix': "조", 'valueformat': ".1f"},
                delta={'reference': 1000000000000, 'valueformat': ".1%"},
                title={'text': "총 매출", 'font': {'size': 14}}
            ), row=1, col=1)
            
            # 트렌드 차트 (샘플)
            dates = pd.date_range('2024-01-01', '2024-12-31', freq='M')
            sales = np.random.normal(100000000000, 20000000000, len(dates)).cumsum()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=sales,
                mode='lines+markers',
                name='월별 매출',
                line=dict(color=self.colors['primary'], width=2)
            ), row=1, col=2)
            
            # 지역별 바 차트 (샘플)
            regions = ['강남구', '마포구', '서초구', '송파구', '영등포구']
            regional_sales = np.random.normal(100000000000, 20000000000, len(regions))
            
            fig.add_trace(go.Bar(
                x=regions,
                y=regional_sales,
                name='지역별 매출',
                marker_color=self.colors['secondary']
            ), row=2, col=1)
            
            # 업종별 파이 차트 (샘플)
            industries = ['소매업', '음식업', '서비스업', '제조업', 'IT업']
            industry_sales = np.random.normal(200000000000, 50000000000, len(industries))
            
            fig.add_trace(go.Pie(
                labels=industries,
                values=industry_sales,
                name='업종별 매출',
                hole=0.3
            ), row=2, col=2)
            
            # 레이아웃 설정
            fig.update_layout(
                height=800,
                showlegend=True,
                font=dict(family=self.font_family, size=self.axis_font_size),
                paper_bgcolor='white',
                plot_bgcolor='white',
                title={
                    'text': '서울 상권 분석 인사이트 대시보드',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': self.colors['dark']}
                }
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"인사이트 대시보드 생성 실패: {str(e)}")
            return go.Figure()

def create_mckinsey_dashboard(df: pd.DataFrame, data: Dict[str, Any] = None) -> Dict[str, go.Figure]:
    """
    맥킨지 스타일 대시보드 생성
    
    Args:
        df: 분석 데이터프레임
        data: 추가 데이터
        
    Returns:
        차트 딕셔너리
    """
    visualizer = McKinseyVisualizer()
    
    if data is None:
        data = {}
    
    charts = {
        "executive_summary": visualizer.create_executive_summary_chart(data),
        "trend_analysis": visualizer.create_trend_analysis_chart(df),
        "regional_analysis": visualizer.create_regional_analysis_chart(df),
        "industry_analysis": visualizer.create_industry_analysis_chart(df),
        "heatmap": visualizer.create_heatmap_chart(df),
        "insights_dashboard": visualizer.create_insights_dashboard(data)
    }
    
    return charts
