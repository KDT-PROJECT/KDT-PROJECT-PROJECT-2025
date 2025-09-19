"""Apple-style KPI Dashboard for Seoul Commercial Analysis App"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

class AppleKPIDashboard:
    """Apple-style KPI Dashboard with responsive design"""

    def __init__(self):
        self.apple_colors = {
            'primary': '#007AFF',
            'secondary': '#5AC8FA',
            'success': '#30D158',
            'warning': '#FF9500',
            'danger': '#FF3B30',
            'purple': '#AF52DE',
            'pink': '#FF2D92',
            'yellow': '#FFCC00',
            'gray': '#8E8E93'
        }

    def render_dashboard(self, kpi_data: Optional[Dict] = None):
        """Render complete KPI dashboard"""
        # Load CSS for dashboard-specific styles
        self._load_dashboard_css()

        # Generate mock data if none provided
        if not kpi_data:
            kpi_data = self._generate_mock_data()

        # Dashboard header
        self._render_dashboard_header()

        # Main KPI cards
        self._render_main_kpis(kpi_data)

        # Performance metrics grid
        self._render_performance_grid(kpi_data)

        # Charts section
        self._render_charts_section(kpi_data)

    def _load_dashboard_css(self):
        """Load dashboard-specific CSS"""
        dashboard_css = """
        <style>
        /* KPI Dashboard Styles */
        .kpi-dashboard {
            padding: 0;
            margin: 0;
        }

        .kpi-main-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .kpi-performance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }

        .kpi-chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }

        .kpi-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            position: relative;
            overflow: hidden;
        }

        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #007AFF 0%, #5AC8FA 100%);
            border-radius: 20px 20px 0 0;
        }

        .kpi-main-value {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            line-height: 1;
        }

        .kpi-label {
            color: #6B7280;
            font-size: 1rem;
            font-weight: 500;
            margin: 0.5rem 0;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .kpi-change {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1rem;
            font-weight: 600;
        }

        .kpi-change-positive {
            color: #30D158;
        }

        .kpi-change-negative {
            color: #FF3B30;
        }

        .kpi-icon {
            width: 60px;
            height: 60px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%);
            color: white;
        }

        .performance-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            text-align: center;
        }

        .performance-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
        }

        .performance-value {
            font-size: 2rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }

        .performance-label {
            color: #6B7280;
            font-size: 0.9rem;
            font-weight: 500;
            margin: 0;
        }

        .chart-container {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            min-height: 400px;
        }

        .section-header {
            text-align: center;
            margin: 3rem 0 2rem 0;
        }

        .section-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #1F2937 0%, #4B5563 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }

        .section-subtitle {
            color: #6B7280;
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
        }

        .realtime-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(48, 209, 88, 0.1);
            color: #30D158;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.9rem;
            font-weight: 600;
            border: 1px solid rgba(48, 209, 88, 0.2);
        }

        .realtime-dot {
            width: 8px;
            height: 8px;
            background: #30D158;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .kpi-chart-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .kpi-main-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }

            .kpi-performance-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .kpi-card {
                padding: 1.5rem;
            }

            .kpi-main-value {
                font-size: 2.5rem;
            }

            .section-title {
                font-size: 2rem;
            }
        }

        @media (max-width: 480px) {
            .kpi-performance-grid {
                grid-template-columns: 1fr;
            }

            .kpi-main-value {
                font-size: 2rem;
            }

            .kpi-card {
                padding: 1rem;
            }
        }
        </style>
        """
        st.markdown(dashboard_css, unsafe_allow_html=True)

    def _render_dashboard_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div class="section-header">
            <div class="realtime-indicator">
                <div class="realtime-dot"></div>
                실시간 업데이트
            </div>
            <h1 class="section-title">📊 KPI 대시보드</h1>
            <p class="section-subtitle">서울 상권 분석 핵심 성과 지표</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_main_kpis(self, kpi_data: Dict):
        """Render main KPI cards"""
        st.markdown('<div class="kpi-main-grid">', unsafe_allow_html=True)

        # Create columns for responsive layout
        col1, col2, col3, col4 = st.columns(4)

        main_kpis = [
            {
                'title': '총 매출액',
                'value': kpi_data['total_revenue'],
                'change': kpi_data['revenue_change'],
                'icon': '💰',
                'color': 'primary'
            },
            {
                'title': '활성 상권',
                'value': kpi_data['active_districts'],
                'change': kpi_data['districts_change'],
                'icon': '🏢',
                'color': 'success'
            },
            {
                'title': '거래 건수',
                'value': kpi_data['total_transactions'],
                'change': kpi_data['transactions_change'],
                'icon': '📈',
                'color': 'purple'
            },
            {
                'title': '성장률',
                'value': kpi_data['growth_rate'],
                'change': kpi_data['growth_change'],
                'icon': '🚀',
                'color': 'warning'
            }
        ]

        columns = [col1, col2, col3, col4]

        for i, kpi in enumerate(main_kpis):
            with columns[i]:
                self._render_main_kpi_card(kpi)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_main_kpi_card(self, kpi: Dict):
        """Render individual main KPI card"""
        change_class = "kpi-change-positive" if kpi['change'] >= 0 else "kpi-change-negative"
        change_icon = "↗" if kpi['change'] >= 0 else "↘"

        st.markdown(f"""
        <div class="kpi-card apple-animate-scale-in">
            <div class="kpi-icon">{kpi['icon']}</div>
            <div class="kpi-main-value">{kpi['value']}</div>
            <div class="kpi-label">{kpi['title']}</div>
            <div class="kpi-change {change_class}">
                <span>{change_icon}</span>
                <span>{abs(kpi['change']):.1f}%</span>
                <span style="color: #9CA3AF; font-weight: 400;">vs 지난 주</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_performance_grid(self, kpi_data: Dict):
        """Render performance metrics grid"""
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">⚡ 성능 지표</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="kpi-performance-grid">', unsafe_allow_html=True)

        performance_metrics = [
            {'label': '응답 시간', 'value': f"{kpi_data['response_time']:.2f}초", 'color': '#007AFF'},
            {'label': '처리 성공률', 'value': f"{kpi_data['success_rate']:.1f}%", 'color': '#30D158'},
            {'label': '사용자 만족도', 'value': f"{kpi_data['user_satisfaction']:.1f}/5.0", 'color': '#FF9500'},
            {'label': '시스템 가동률', 'value': f"{kpi_data['uptime']:.2f}%", 'color': '#AF52DE'},
            {'label': 'CPU 사용률', 'value': f"{kpi_data['cpu_usage']:.1f}%", 'color': '#FF3B30'},
            {'label': '메모리 사용률', 'value': f"{kpi_data['memory_usage']:.1f}%", 'color': '#5AC8FA'},
            {'label': '데이터 처리량', 'value': f"{kpi_data['data_throughput']:.1f}MB/s", 'color': '#FF2D92'},
            {'label': '활성 세션', 'value': f"{kpi_data['active_sessions']}", 'color': '#FFCC00'}
        ]

        # Create responsive columns
        cols = st.columns(4)

        for i, metric in enumerate(performance_metrics):
            with cols[i % 4]:
                st.markdown(f"""
                <div class="performance-card apple-animate-fade-in">
                    <div class="performance-value" style="color: {metric['color']}">
                        {metric['value']}
                    </div>
                    <div class="performance-label">{metric['label']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_charts_section(self, kpi_data: Dict):
        """Render charts section"""
        st.markdown("""
        <div class="section-header">
            <h2 class="section-title">📈 분석 차트</h2>
        </div>
        """, unsafe_allow_html=True)

        # Create responsive chart layout
        col1, col2 = st.columns(2)

        with col1:
            self._render_revenue_trend_chart(kpi_data)

        with col2:
            self._render_district_performance_chart(kpi_data)

    def _render_revenue_trend_chart(self, kpi_data: Dict):
        """Render revenue trend chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        # Generate trend data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
        values = kpi_data['revenue_trend']

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='매출 추이',
            line=dict(color='#007AFF', width=3),
            marker=dict(color='#007AFF', size=8),
            fill='tonexty',
            fillcolor='rgba(0, 122, 255, 0.1)'
        ))

        fig.update_layout(
            title=dict(
                text='📈 주간 매출 추이',
                x=0.5,
                font=dict(size=18, color='#1F2937', family='system-ui')
            ),
            xaxis_title='날짜',
            yaxis_title='매출 (억원)',
            font_family="system-ui",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(t=60, l=40, r=40, b=40),
            height=350
        )

        fig.update_xaxes(showgrid=True, gridcolor='rgba(209, 213, 219, 0.3)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(209, 213, 219, 0.3)')

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_district_performance_chart(self, kpi_data: Dict):
        """Render district performance chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        districts = ['강남구', '서초구', '송파구', '중구', '마포구']
        values = kpi_data['district_performance']

        fig = go.Figure(data=[
            go.Bar(
                x=districts,
                y=values,
                marker_color=['#007AFF', '#30D158', '#FF9500', '#AF52DE', '#FF3B30'],
                text=values,
                textposition='auto',
            )
        ])

        fig.update_layout(
            title=dict(
                text='🏙️ 구별 성과',
                x=0.5,
                font=dict(size=18, color='#1F2937', family='system-ui')
            ),
            xaxis_title='구',
            yaxis_title='성과 점수',
            font_family="system-ui",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(t=60, l=40, r=40, b=40),
            height=350
        )

        fig.update_xaxes(showgrid=True, gridcolor='rgba(209, 213, 219, 0.3)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(209, 213, 219, 0.3)')

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def _generate_mock_data(self) -> Dict:
        """Generate mock KPI data"""
        np.random.seed(42)  # For consistent results

        return {
            # Main KPIs
            'total_revenue': '2,847억원',
            'revenue_change': 12.3,
            'active_districts': '25개',
            'districts_change': 4.2,
            'total_transactions': '1.2M',
            'transactions_change': 8.7,
            'growth_rate': '15.4%',
            'growth_change': 2.1,

            # Performance metrics
            'response_time': 1.23,
            'success_rate': 98.7,
            'user_satisfaction': 4.6,
            'uptime': 99.95,
            'cpu_usage': 67.3,
            'memory_usage': 72.1,
            'data_throughput': 234.7,
            'active_sessions': 1847,

            # Chart data
            'revenue_trend': np.random.normal(100, 15, 52).cumsum() + 500,
            'district_performance': [95, 87, 82, 78, 73],
        }

def render_kpi_dashboard():
    """Main function to render KPI dashboard"""
    dashboard = AppleKPIDashboard()
    dashboard.render_dashboard()

# For testing
if __name__ == "__main__":
    render_kpi_dashboard()
