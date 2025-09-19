"""Simplified Enhanced Report UI Component"""

import streamlit as st
from typing import Dict, Any

class EnhancedReportUI:
    """Simplified Enhanced Report UI Component"""
    
    @staticmethod
    def render_report_hero():
        """Render report generation hero section"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h2>📋 보고서 생성</h2>
            <p>SQL 분석 결과와 문서 검색 결과를 종합하여 보고서를 생성합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_data_status():
        """Render data availability status"""
        return {
            "sql_available": True,
            "rag_available": True,
            "hybrid_available": True
        }
    
    @staticmethod
    def render_report_config():
        """Render report configuration options"""
        st.subheader("📊 보고서 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_sql_data = st.checkbox("SQL 데이터 사용", value=True)
            use_web_data = st.checkbox("웹 검색 데이터 사용", value=False)
        
        with col2:
            report_style = st.selectbox("보고서 스타일", ["executive", "detailed", "summary"])
            include_charts = st.checkbox("차트 포함", value=True)
        
        return {
            "use_sql_data": use_sql_data,
            "use_web_data": use_web_data,
            "report_style": report_style,
            "include_charts": include_charts
        }
