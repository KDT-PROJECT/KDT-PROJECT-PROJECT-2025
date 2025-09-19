"""
UI Components for Seoul Commercial Analysis System
TASK-004: Streamlit 프런트엔드(UI/UX) 구현 - 공통 컴포넌트
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from infrastructure.logging_service import StructuredLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UIComponents:
    """Common UI components for the Streamlit application."""

    def __init__(self):
        """Initialize UI components."""
        self.logger = StructuredLogger("ui_components")

    def apply_custom_css(self):
        """Apply custom CSS styling to the application."""
        try:
            custom_css = """
            <style>
            /* Main theme colors */
            :root {
                --primary-color: #1f77b4;
                --secondary-color: #ff7f0e;
                --success-color: #2ca02c;
                --warning-color: #d62728;
                --info-color: #17a2b8;
                --light-color: #f8f9fa;
                --dark-color: #343a40;
            }

            /* Header styling */
            .main-header {
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .main-header h1 {
                margin: 0;
                font-size: 2.5rem;
                font-weight: bold;
            }

            .main-header p {
                margin: 0.5rem 0 0 0;
                font-size: 1.1rem;
                opacity: 0.9;
            }

            /* Status indicators */
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }

            .status-connected {
                background-color: var(--success-color);
                animation: pulse 2s infinite;
            }

            .status-disconnected {
                background-color: var(--warning-color);
            }

            .status-error {
                background-color: var(--warning-color);
            }

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            /* Card styling */
            .metric-card {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                border-left: 4px solid var(--primary-color);
                margin-bottom: 1rem;
            }

            .metric-card h3 {
                margin: 0 0 0.5rem 0;
                color: var(--primary-color);
                font-size: 1.1rem;
            }

            .metric-card .value {
                font-size: 2rem;
                font-weight: bold;
                color: var(--dark-color);
            }

            .metric-card .label {
                color: #666;
                font-size: 0.9rem;
            }

            /* Progress bar styling */
            .progress-container {
                background: #f0f0f0;
                border-radius: 10px;
                padding: 3px;
                margin: 1rem 0;
            }

            .progress-bar {
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                height: 20px;
                border-radius: 8px;
                transition: width 0.3s ease;
            }

            /* Button styling */
            .stButton > button {
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: bold;
                transition: all 0.3s ease;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }

            /* Tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }

            .stTabs [data-baseweb="tab"] {
                background: #f8f9fa;
                border-radius: 8px 8px 0 0;
                padding: 0.5rem 1rem;
                font-weight: bold;
            }

            .stTabs [aria-selected="true"] {
                background: var(--primary-color);
                color: white;
            }

            /* Alert styling */
            .alert {
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border-left: 4px solid;
            }

            .alert-success {
                background-color: #d4edda;
                border-color: var(--success-color);
                color: #155724;
            }

            .alert-warning {
                background-color: #fff3cd;
                border-color: var(--warning-color);
                color: #856404;
            }

            .alert-error {
                background-color: #f8d7da;
                border-color: var(--warning-color);
                color: #721c24;
            }

            .alert-info {
                background-color: #d1ecf1;
                border-color: var(--info-color);
                color: #0c5460;
            }

            /* Footer styling */
            .footer {
                background: var(--dark-color);
                color: white;
                padding: 1rem;
                text-align: center;
                margin-top: 3rem;
                border-radius: 8px;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .main-header h1 {
                    font-size: 2rem;
                }
                
                .metric-card {
                    margin-bottom: 0.5rem;
                }
            }

            /* Loading animation */
            .loading-spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Data table styling */
            .dataframe {
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }

            /* Chart container */
            .chart-container {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin: 1rem 0;
            }
            </style>
            """
            st.markdown(custom_css, unsafe_allow_html=True)
            self.logger.info("Custom CSS applied successfully")

        except Exception as e:
            self.logger.error(f"Error applying custom CSS: {e}")

    def render_header(self, title: str = "서울 상권분석 LLM", subtitle: str = "AI 기반 상권 분석 시스템"):
        """Render the main application header."""
        try:
            header_html = f"""
            <div class="main-header">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            """
            st.markdown(header_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error rendering header: {e}")

    def render_health_status(self, status: str = "connected", kpis: Dict[str, Any] = None):
        """Render health status indicator with KPIs."""
        try:
            col1, col2, col3 = st.columns([1, 2, 3])
            
            with col1:
                if status == "connected":
                    st.markdown(
                        '<span class="status-indicator status-connected"></span>**Connected**',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<span class="status-indicator status-disconnected"></span>**Disconnected**',
                        unsafe_allow_html=True
                    )
            
            with col2:
                if kpis:
                    p95_time = kpis.get("p95_response_time", 0)
                    sql_acc = kpis.get("text_to_sql_accuracy", 0)
                    st.markdown(f"**KPI:** P95 {p95_time:.1f}s | SQL Acc {sql_acc:.1%}")
            
            with col3:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(f"**Last Updated:** {current_time}")

        except Exception as e:
            self.logger.error(f"Error rendering health status: {e}")

    def render_metric_card(self, title: str, value: str, label: str = "", color: str = "primary"):
        """Render a metric card."""
        try:
            color_class = f"border-left: 4px solid var(--{color}-color);"
            
            card_html = f"""
            <div class="metric-card" style="{color_class}">
                <h3>{title}</h3>
                <div class="value">{value}</div>
                <div class="label">{label}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error rendering metric card: {e}")

    def show_alert(self, message: str, alert_type: str = "info", icon: str = None):
        """Show styled alert message."""
        try:
            icons = {
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "info": "ℹ️"
            }
            
            icon_str = icons.get(alert_type, icons["info"])
            if icon:
                icon_str = icon
            
            alert_html = f"""
            <div class="alert alert-{alert_type}">
                {icon_str} {message}
            </div>
            """
            st.markdown(alert_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error showing alert: {e}")

    def show_progress(self, current: int, total: int, message: str = "Processing..."):
        """Show progress bar with message."""
        try:
            progress = current / total if total > 0 else 0
            
            st.markdown(f"**{message}**")
            progress_html = f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress * 100}%"></div>
            </div>
            <div style="text-align: center; margin-top: 0.5rem;">
                {current}/{total} ({progress:.1%})
            </div>
            """
            st.markdown(progress_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error showing progress: {e}")

    def render_loading_spinner(self, message: str = "Loading..."):
        """Render loading spinner with message."""
        try:
            spinner_html = f"""
            <div style="text-align: center; padding: 2rem;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 1rem;">{message}</p>
            </div>
            """
            st.markdown(spinner_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error rendering loading spinner: {e}")

    def render_footer(self, version: str = "1.0.0"):
        """Render application footer."""
        try:
            footer_html = f"""
            <div class="footer">
                <p><strong>서울 상권분석 LLM</strong> | Powered by AI | Version {version}</p>
                <p>© 2024 Seoul Commercial Analysis System. All rights reserved.</p>
            </div>
            """
            st.markdown(footer_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error rendering footer: {e}")

    def render_data_table(self, data, title: str = "", max_rows: int = 20):
        """Render styled data table."""
        try:
            if title:
                st.subheader(title)
            
            if data is not None and not data.empty:
                # Show data info
                st.info(f"총 {len(data)}개 행, {len(data.columns)}개 컬럼")
                
                # Display table
                st.dataframe(data.head(max_rows), use_container_width=True)
                
                if len(data) > max_rows:
                    st.caption(f"상위 {max_rows}개 행만 표시 (전체: {len(data)}개)")
            else:
                st.warning("표시할 데이터가 없습니다.")

        except Exception as e:
            self.logger.error(f"Error rendering data table: {e}")

    def render_chart_container(self, chart, title: str = ""):
        """Render chart in styled container."""
        try:
            if title:
                st.subheader(title)
            
            chart_html = f"""
            <div class="chart-container">
                {chart}
            </div>
            """
            st.markdown(chart_html, unsafe_allow_html=True)

        except Exception as e:
            self.logger.error(f"Error rendering chart container: {e}")

    def render_download_buttons(self, data, filename_prefix: str = "data"):
        """Render download buttons for data."""
        try:
            if data is not None and not data.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # CSV download
                    csv = data.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Excel download
                    excel_buffer = data.to_excel(index=False)
                    st.download_button(
                        label="📊 Excel 다운로드",
                        data=excel_buffer,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col3:
                    # JSON download
                    json_data = data.to_json(orient='records', force_ascii=False, indent=2)
                    st.download_button(
                        label="📄 JSON 다운로드",
                        data=json_data,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

        except Exception as e:
            self.logger.error(f"Error rendering download buttons: {e}")

    def render_error_guide(self, error_type: str, suggestions: List[str] = None):
        """Render error guide with suggestions."""
        try:
            if suggestions is None:
                suggestions = []
            
            st.error("❌ 오류가 발생했습니다.")
            
            if suggestions:
                st.markdown("**💡 다음을 시도해보세요:**")
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"{i}. {suggestion}")
            
            # Add retry button
            if st.button("🔄 다시 시도", type="secondary"):
                st.rerun()

        except Exception as e:
            self.logger.error(f"Error rendering error guide: {e}")

    def render_empty_state(self, title: str, description: str, action_button: str = None):
        """Render empty state with call to action."""
        try:
            st.markdown(f"### {title}")
            st.info(description)
            
            if action_button:
                if st.button(action_button, type="primary"):
                    st.rerun()

        except Exception as e:
            self.logger.error(f"Error rendering empty state: {e}")


def create_ui_components() -> UIComponents:
    """
    Factory function to create UI components instance.

    Returns:
        UIComponents instance
    """
    return UIComponents()


# Global UI components instance
_ui_components = None

def get_ui_components() -> UIComponents:
    """Get global UI components instance."""
    global _ui_components
    if _ui_components is None:
        _ui_components = UIComponents()
    return _ui_components


if __name__ == "__main__":
    # Test the UI components
    components = UIComponents()
    components.apply_custom_css()
    components.render_header()
    components.show_alert("Test message", "success")
    components.render_footer()
