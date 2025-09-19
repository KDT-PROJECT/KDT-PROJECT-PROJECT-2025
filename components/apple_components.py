"""Apple-style UI Components for Seoul Commercial Analysis App"""

import streamlit as st
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

class AppleUI:
    """Apple-style UI component library for Streamlit"""

    @staticmethod
    def load_css():
        """Load Apple-style CSS"""
        css_path = "styles/apple_design.css"
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("Apple design CSS file not found. Using default styles.")

    @staticmethod
    def render_hero_header():
        """Render Apple-style hero header"""
        st.markdown("""
        <div class="apple-header apple-animate-fade-in">
            <h1>🏢 서울 상권 분석 AI</h1>
            <h3>Apple Intelligence 기반 상권 데이터 분석 플랫폼</h3>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_card(title: str, content: str, icon: str = "📊",
                   card_type: str = "default", animation: str = "scale-in") -> None:
        """Render Apple-style card component with enhanced animations"""
        animation_class = f"apple-animate-{animation}"
        hover_class = "apple-hover-lift"
        card_class = f"apple-card {animation_class} {hover_class}"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="apple-card-header">
                <div class="apple-card-icon apple-animate-float">{icon}</div>
                <h3 class="apple-card-title">{title}</h3>
            </div>
            <div class="apple-card-content">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_button(text: str, button_type: str = "primary",
                     icon: str = "", key: str = None) -> bool:
        """Render Apple-style button"""
        button_class = "apple-button"
        if button_type == "secondary":
            button_class += " apple-button-secondary"

        # Use Streamlit's button but with custom styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if key:
                return st.button(f"{icon} {text}".strip(), key=key,
                               help=f"Click to {text.lower()}")
            else:
                return st.button(f"{icon} {text}".strip(),
                               help=f"Click to {text.lower()}")

    @staticmethod
    def render_metric_card(label: str, value: str, delta: str = None,
                          icon: str = "📈", stagger: int = 0) -> None:
        """Render Apple-style metric card with staggered animations"""
        delta_html = ""
        if delta:
            delta_color = "var(--apple-green)" if delta.startswith("+") else "var(--apple-red)"
            delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'

        stagger_class = f"apple-stagger-{stagger}" if stagger > 0 else ""

        st.markdown(f"""
        <div class="apple-metric apple-animate-scale-in apple-hover-glow {stagger_class}">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;" class="apple-animate-bounce">{icon}</div>
            <div class="apple-metric-value">{value}</div>
            <div class="apple-metric-label">{label}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_progress_bar(progress: float, label: str = "") -> None:
        """Render Apple-style progress bar"""
        progress_percent = min(max(progress * 100, 0), 100)

        st.markdown(f"""
        <div style="margin: 1rem 0;">
            {f'<div style="margin-bottom: 0.5rem; color: var(--apple-gray-600);">{label}</div>' if label else ''}
            <div class="apple-progress">
                <div class="apple-progress-bar" style="width: {progress_percent}%"></div>
            </div>
            <div style="text-align: right; margin-top: 0.25rem; font-size: 0.9rem; color: var(--apple-gray-500);">
                {progress_percent:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_alert(message: str, alert_type: str = "info",
                    icon: str = None) -> None:
        """Render Apple-style alert"""
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        display_icon = icon or icons.get(alert_type, "ℹ️")

        st.markdown(f"""
        <div class="apple-alert apple-alert-{alert_type}">
            <div>{display_icon}</div>
            <div>{message}</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_stats_grid(stats: List[Dict[str, Any]]) -> None:
        """Render grid of statistics cards"""
        if not stats:
            return

        num_cols = min(len(stats), 4)
        cols = st.columns(num_cols)

        for i, stat in enumerate(stats):
            with cols[i % num_cols]:
                AppleUI.render_metric_card(
                    label=stat.get('label', ''),
                    value=stat.get('value', ''),
                    delta=stat.get('delta'),
                    icon=stat.get('icon', '📊')
                )

    @staticmethod
    def render_feature_grid():
        """Render main feature grid with enhanced animations"""
        st.markdown("""
        <div style="margin: 2rem 0;">
            <h2 style="text-align: center; color: var(--apple-gray-800); margin-bottom: 2rem;" class="apple-animate-fade-in">
                주요 기능
            </h2>
        </div>
        """, unsafe_allow_html=True)

        features = [
            {
                "icon": "🤖",
                "title": "AI 질의 분석",
                "description": "자연어로 질문하면 AI가 자동으로 데이터를 분석하고 인사이트를 제공합니다.",
                "animation": "slide-in-left"
            },
            {
                "icon": "📊",
                "title": "SQL 데이터 분석",
                "description": "강력한 SQL 엔진으로 상권 데이터를 실시간으로 분석하고 시각화합니다.",
                "animation": "slide-in-right"
            },
            {
                "icon": "📄",
                "title": "문서 검색",
                "description": "하이브리드 검색으로 관련 정책 문서와 보고서를 빠르게 찾아줍니다.",
                "animation": "slide-in-left"
            },
            {
                "icon": "📋",
                "title": "자동 보고서",
                "description": "분석 결과를 전문적인 보고서 형태로 자동 생성하여 제공합니다.",
                "animation": "slide-in-right"
            }
        ]

        cols = st.columns(2)
        for i, feature in enumerate(features):
            with cols[i % 2]:
                AppleUI.render_card(
                    title=feature["title"],
                    content=feature["description"],
                    icon=feature["icon"],
                    animation=feature["animation"]
                )

    @staticmethod
    def render_apple_chart(data, chart_type: str = "bar", title: str = ""):
        """Render Apple-style charts"""
        # Apple design colors
        apple_colors = [
            '#007AFF', '#FF3B30', '#30D158', '#FF9500',
            '#AF52DE', '#FF2D92', '#FFCC00', '#5AC8FA'
        ]

        fig = None

        if chart_type == "bar" and not data.empty:
            fig = px.bar(
                data,
                x=data.columns[0] if len(data.columns) > 0 else data.index,
                y=data.columns[1] if len(data.columns) > 1 else data.iloc[:, 0],
                title=title,
                color_discrete_sequence=apple_colors
            )
        elif chart_type == "line" and not data.empty:
            fig = px.line(
                data,
                x=data.columns[0] if len(data.columns) > 0 else data.index,
                y=data.columns[1] if len(data.columns) > 1 else data.iloc[:, 0],
                title=title,
                color_discrete_sequence=apple_colors
            )
        elif chart_type == "pie" and not data.empty:
            fig = px.pie(
                data,
                values=data.columns[1] if len(data.columns) > 1 else data.iloc[:, 0],
                names=data.columns[0] if len(data.columns) > 0 else data.index,
                title=title,
                color_discrete_sequence=apple_colors
            )

        if fig:
            # Apply Apple design theme
            fig.update_layout(
                font_family="system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                font_size=14,
                title_font_size=18,
                title_font_color="#1F2937",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=60, l=40, r=40, b=40),
                title=dict(
                    text=title,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=20, color="#1F2937", family="system-ui")
                )
            )

            # Update axes
            fig.update_xaxes(
                showgrid=True,
                gridcolor="rgba(209, 213, 219, 0.3)",
                showline=True,
                linecolor="rgba(209, 213, 219, 0.5)"
            )
            fig.update_yaxes(
                showgrid=True,
                gridcolor="rgba(209, 213, 219, 0.3)",
                showline=True,
                linecolor="rgba(209, 213, 219, 0.5)"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("차트를 표시할 데이터가 없습니다.")

    @staticmethod
    def render_sidebar_stats():
        """Render sidebar statistics with staggered animations"""
        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; margin: 2rem 0;">
                <h3 style="color: var(--apple-gray-700);" class="apple-animate-fade-in">📊 실시간 통계</h3>
            </div>
            """, unsafe_allow_html=True)

            # Mock statistics - replace with real data
            stats = [
                {"label": "총 쿼리 수", "value": "1,234", "icon": "🔍"},
                {"label": "활성 사용자", "value": "89", "icon": "👥"},
                {"label": "처리 속도", "value": "1.2초", "icon": "⚡"},
                {"label": "정확도", "value": "94.5%", "icon": "🎯"}
            ]

            for i, stat in enumerate(stats):
                AppleUI.render_metric_card(
                    label=stat["label"],
                    value=stat["value"],
                    icon=stat["icon"],
                    stagger=i + 1
                )

    @staticmethod
    def render_loading_animation(message: str = "처리 중..."):
        """Render Apple-style loading animation"""
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="
                width: 40px;
                height: 40px;
                border: 3px solid var(--apple-gray-300);
                border-top: 3px solid var(--apple-blue);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem auto;
            "></div>
            <div style="color: var(--apple-gray-600); font-size: 1rem;">
                {message}
            </div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_footer():
        """Render Apple-style footer"""
        st.markdown("""
        <div style="
            text-align: center;
            padding: 3rem 1rem 2rem 1rem;
            margin-top: 4rem;
            border-top: 1px solid var(--apple-gray-200);
            color: var(--apple-gray-500);
        ">
            <div style="margin-bottom: 1rem;">
                <span style="font-size: 1.5rem;">🏢</span>
            </div>
            <div style="font-size: 0.9rem;">
                <strong>서울 상권 분석 AI</strong> | Powered by Apple Intelligence Design
            </div>
            <div style="font-size: 0.8rem; margin-top: 0.5rem;">
                © 2024 Seoul Commercial Analysis Platform. All rights reserved.
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_quick_actions():
        """Render quick action buttons"""
        st.markdown("""
        <div style="margin: 2rem 0;">
            <h3 style="text-align: center; color: var(--apple-gray-800); margin-bottom: 1.5rem;">
                빠른 실행
            </h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        actions = [
            {"label": "매출 분석", "icon": "💰", "query": "강남구 매출 추이 분석"},
            {"label": "업종 비교", "icon": "📈", "query": "업종별 매출 비교 분석"},
            {"label": "지역 분석", "icon": "🗺️", "query": "지역별 상권 현황 분석"},
            {"label": "트렌드 분석", "icon": "📊", "query": "최근 상권 트렌드 분석"}
        ]

        cols = [col1, col2, col3, col4]

        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(
                    f"{action['icon']}\n{action['label']}",
                    key=f"quick_action_{i}",
                    use_container_width=True
                ):
                    st.session_state['quick_query'] = action['query']
                    st.rerun()

class AppleLayoutManager:
    """Manage Apple-style layouts"""

    @staticmethod
    def setup_page_config():
        """Setup Streamlit page configuration for Apple design"""
        st.set_page_config(
            page_title="서울 상권 분석 AI",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo',
                'Report a bug': 'https://github.com/your-repo/issues',
                'About': '# Seoul Commercial Analysis AI\n\nPowered by Apple Intelligence Design'
            }
        )

    @staticmethod
    def render_main_layout():
        """Render main page layout"""
        # Load CSS
        AppleUI.load_css()

        # Header
        AppleUI.render_hero_header()

        # Quick actions
        AppleUI.render_quick_actions()

        # Feature grid
        AppleUI.render_feature_grid()

        return True

    @staticmethod
    def render_analysis_layout():
        """Render analysis page layout"""
        AppleUI.load_css()

        # Create main content area with sidebar stats
        main_col, stats_col = st.columns([3, 1])

        with stats_col:
            AppleUI.render_sidebar_stats()

        with main_col:
            return True

    @staticmethod
    def handle_quick_query():
        """Handle quick query from session state"""
        if 'quick_query' in st.session_state:
            query = st.session_state['quick_query']
            del st.session_state['quick_query']
            return query
        return None