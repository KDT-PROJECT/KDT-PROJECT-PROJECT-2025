"""Enhanced Report Generation UI Components"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import io
from docx import Document
from fpdf import FPDF

class EnhancedReportUI:
    """Enhanced UI components for report generation"""

    @staticmethod
    def _create_word_report(content: str) -> io.BytesIO:
        """Create a Word document from the report content."""
        document = Document()
        document.add_paragraph(content)
        bio = io.BytesIO()
        document.save(bio)
        bio.seek(0)
        return bio

    @staticmethod
    def _create_pdf_report(content: str) -> io.BytesIO:
        """Create a PDF document from the report content."""
        pdf = FPDF()
        pdf.add_page()
        
        # Add a font that supports Korean characters
        # IMPORTANT: You must have a Korean font file (e.g., NanumGothic.ttf) in your project directory.
        try:
            pdf.add_font('NanumGothic', '', 'NanumGothic.ttf', uni=True)
            pdf.set_font('NanumGothic', '', 12)
        except RuntimeError:
            # Fallback to a standard font if the Korean font is not found
            pdf.set_font('Arial', '', 12)
            st.warning("한글 폰트(NanumGothic.ttf)를 찾을 수 없어 PDF 내보내기 시 한글이 깨질 수 있습니다.")

        # Add content to the PDF
        for line in content.split('\n'):
            pdf.multi_cell(0, 10, line)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        bio = io.BytesIO(pdf_output)
        bio.seek(0)
        return bio

    @staticmethod
    def render_report_hero():
        """Render hero section for report generation"""
        st.markdown("""
        <div class="report-hero apple-animate-fade-in">
            <div class="report-hero-content">
                <h1 class="report-hero-title">
                    📋 AI 보고서 생성
                </h1>
                <p class="report-hero-subtitle">
                    데이터 분석 결과를 전문적인 보고서로 자동 생성
                </p>
                <div class="report-hero-features">
                    <div class="report-feature">
                        <div class="report-feature-icon">📊</div>
                        <div class="report-feature-text">데이터 분석</div>
                    </div>
                    <div class="report-feature">
                        <div class="report-feature-icon">🤖</div>
                        <div class="report-feature-text">AI 인사이트</div>
                    </div>
                    <div class="report-feature">
                        <div class="report-feature-icon">📄</div>
                        <div class="report-feature-text">전문 보고서</div>
                    </div>
                </div>
            </div>
        </div>

        <style>
        .report-hero {
            background: linear-gradient(135deg, rgba(175, 82, 222, 0.1) 0%, rgba(255, 45, 146, 0.1) 100%);
            border-radius: 24px;
            padding: 3rem 2rem;
            margin: 2rem 0;
            text-align: center;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        .report-hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #AF52DE 0%, #FF2D92 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 1rem 0;
        }

        .report-hero-subtitle {
            font-size: 1.2rem;
            color: #6B7280;
            margin: 0 0 2rem 0;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .report-hero-features {
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .report-feature {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            min-width: 120px;
        }

        .report-feature-icon {
            font-size: 2rem;
            width: 60px;
            height: 60px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .report-feature-text {
            font-size: 0.9rem;
            font-weight: 500;
            color: #4B5563;
        }

        @media (max-width: 768px) {
            .report-hero {
                padding: 2rem 1rem;
            }
            .report-hero-title {
                font-size: 2rem;
            }
            .report-hero-features {
                gap: 1rem;
            }
        }
        </style>
        ", unsafe_allow_html=True)

    @staticmethod
    def render_data_status():
        """Render data availability status"""
        # Check data availability with safe access
        sql_df = getattr(st.session_state, 'last_sql_df', None)
        sql_available = sql_df is not None and not (hasattr(sql_df, 'empty') and sql_df.empty)

        rag_hits = getattr(st.session_state, 'last_rag_hits', [])
        rag_available = bool(rag_hits)

        hybrid_search = getattr(st.session_state, 'last_hybrid_search', None)
        hybrid_available = hybrid_search is not None

        st.markdown("### 📊 사용 가능한 데이터")

        col1, col2, col3 = st.columns(3)

        with col1:
            status_color = "#30D158" if sql_available else "#FF3B30"
            status_text = "사용 가능" if sql_available else "데이터 없음"
            status_icon = "✅" if sql_available else "❌"

            st.markdown(f"""
            <div class="data-status-card">
                <div class="data-status-icon" style="color: {status_color}">{status_icon}</div>
                <div class="data-status-title">SQL 분석 데이터</div>
                <div class="data-status-text" style="color: {status_color}">{status_text}</div>
                {f'<div class="data-status-detail">행 수: {len(sql_df)}개</div>' if sql_available else '<div class="data-status-detail">SQL 분석을 먼저 실행하세요</div>'}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            status_color = "#30D158" if rag_available else "#FF3B30"
            status_text = "사용 가능" if rag_available else "데이터 없음"
            status_icon = "✅" if rag_available else "❌"

            st.markdown(f"""
            <div class="data-status-card">
                <div class="data-status-icon" style="color: {status_color}">{status_icon}</div>
                <div class="data-status-title">문서 검색 데이터</div>
                <div class="data-status-text" style="color: {status_color}">{status_text}</div>
                {f'<div class="data-status-detail">문서 수: {len(rag_hits)}개</div>' if rag_available else '<div class="data-status-detail">문서 검색을 먼저 실행하세요</div>'}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            status_color = "#30D158" if hybrid_available else "#FF3B30"
            status_text = "사용 가능" if hybrid_available else "데이터 없음"
            status_icon = "✅" if hybrid_available else "❌"

            confidence = hybrid_search.get("confidence", 0) if hybrid_search else 0

            st.markdown(f"""
            <div class="data-status-card">
                <div class="data-status-icon" style="color: {status_color}">{status_icon}</div>
                <div class="data-status-title">하이브리드 검색</div>
                <div class="data-status-text" style="color: {status_color}">{status_text}</div>
                {f'<div class="data-status-detail">신뢰도: {confidence:.0%}</div>' if hybrid_available else '<div class="data-status-detail">하이브리드 검색을 먼저 실행하세요</div>'}
            </div>
            """, unsafe_allow_html=True)


        return {
            "sql_available": sql_available,
            "rag_available": rag_available,
            "hybrid_available": hybrid_available
        }

    @staticmethod
    def render_report_config():
        """Render report configuration options"""
        st.markdown("### ⚙️ 보고서 설정")

        # Report configuration in enhanced layout
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📍 분석 대상**")
            target_area = st.selectbox(
                "분석 지역",
                ["강남구", "서초구", "송파구", "중구", "마포구", "전체"],
                help="보고서에서 집중 분석할 지역을 선택하세요"
            )

            target_industry = st.selectbox(
                "분석 업종",
                ["IT/소프트웨어", "금융/핀테크", "의료/바이오", "교육/에듀테크", "유통/이커머스", "전체"],
                help="보고서에서 집중 분석할 업종을 선택하세요"
            )

        with col2:
            st.markdown("**📋 보고서 유형**")
            report_style = st.selectbox(
                "보고서 스타일",
                ["executive", "detailed", "summary"],
                format_func=lambda x: {
                    "executive": "📊 경영진용 (요약형)",
                    "detailed": "📄 상세 분석형",
                    "summary": "📝 간단 요약형"
                }[x],
                help="보고서의 상세도와 길이를 선택하세요"
            )

            report_language = st.selectbox(
                "언어",
                ["korean", "english"],
                format_func=lambda x: "🇰🇷 한국어" if x == "korean" else "🇺🇸 English",
                help="보고서 생성 언어를 선택하세요"
            )

        return {
            "target_area": target_area,
            "target_industry": target_industry,
            "report_style": report_style,
            "report_language": report_language
        }

    @staticmethod
    def render_data_source_config(data_status: Dict[str, bool]):
        """Render data source configuration"""
        st.markdown("### 📊 데이터 소스 선택")

        col1, col2 = st.columns(2)

        with col1:
            use_sql_data = st.checkbox(
                "📈 SQL 분석 데이터 사용",
                value=data_status["sql_available"],
                disabled=not data_status["sql_available"],
                help="SQL 분석 결과를 보고서에 포함합니다" if data_status["sql_available"] else "SQL 분석 데이터가 없습니다"
            )

            use_rag_data = st.checkbox(
                "📚 문서 검색 데이터 사용",
                value=data_status["rag_available"],
                disabled=not data_status["rag_available"],
                help="문서 검색 결과를 보고서에 포함합니다" if data_status["rag_available"] else "문서 검색 데이터가 없습니다"
            )

        with col2:
            use_hybrid_data = st.checkbox(
                "🔄 하이브리드 검색 데이터 사용",
                value=data_status["hybrid_available"],
                disabled=not data_status["hybrid_available"],
                help="하이브리드 검색 결과와 AI 답변을 보고서에 포함합니다" if data_status["hybrid_available"] else "하이브리드 검색 데이터가 없습니다"
            )

            generate_mock_data = st.checkbox(
                "🎲 샘플 데이터로 생성",
                value=False,
                help="실제 데이터가 없을 때 샘플 데이터로 보고서를 생성합니다"
            )

        return {
            "use_sql_data": use_sql_data,
            "use_rag_data": use_rag_data,
            "use_hybrid_data": use_hybrid_data,
            "generate_mock_data": generate_mock_data
        }

    @staticmethod
    def render_report_options():
        """Render advanced report options"""
        with st.expander("🔧 고급 옵션", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                include_charts = st.checkbox("📊 차트 및 그래프 포함", value=True)
                include_metadata = st.checkbox("📋 메타데이터 포함", value=True)
                include_recommendations = st.checkbox("💡 추천사항 포함", value=True)

            with col2:
                save_to_file = st.checkbox("💾 파일로 저장", value=False)
                auto_download = st.checkbox("📥 자동 다운로드", value=False)
                share_report = st.checkbox("🔗 공유 링크 생성", value=False)

        return {
            "include_charts": include_charts,
            "include_metadata": include_metadata,
            "include_recommendations": include_recommendations,
            "save_to_file": save_to_file,
            "auto_download": auto_download,
            "share_report": share_report
        }

    @staticmethod
    def render_report_progress(stage: str, progress: float):
        """Render report generation progress"""
        stage_info = {
            "preparing": {"text": "데이터 준비 중", "icon": "📊", "color": "#007AFF"},
            "analyzing": {"text": "데이터 분석 중", "icon": "🔍", "color": "#FF9500"},
            "generating": {"text": "보고서 생성 중", "icon": "📝", "color": "#30D158"},
            "formatting": {"text": "서식 적용 중", "icon": "🎨", "color": "#AF52DE"},
            "finalizing": {"text": "최종 검토 중", "icon": "✅", "color": "#FF2D92"},
            "completed": {"text": "생성 완료", "icon": "🎉", "color": "#30D158"}
        }

        info = stage_info.get(stage, stage_info["preparing"])

        st.markdown(f"""
        <div class="report-progress-container">
            <div class="report-progress-header">
                <div class="report-progress-icon" style="color: {info['color']}">
                    {info['icon']}
                </div>
                <div class="report-progress-text">
                    {info['text']}
                </div>
            </div>
            <div class="report-progress-bar">
                <div class="report-progress-fill" style="width: {progress * 100}%; background: {info['color']}"></div>
            </div>
            <div class="report-progress-percentage">
                {progress * 100:.0f}%
            </div>
        </div>

        <style>
        .report-progress-container {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}

        .report-progress-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .report-progress-icon {{
            font-size: 1.5rem;
            animation: pulse 2s infinite;
        }}

        .report-progress-text {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
        }}

        .report-progress-bar {{
            width: 100%;
            height: 8px;
            background: #E5E7EB;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }}

        .report-progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
            animation: shimmer 2s infinite;
        }}

        .report-progress-percentage {{
            text-align: right;
            font-size: 0.9rem;
            font-weight: 500;
            color: #6B7280;
        }}

        @keyframes pulse {{
            0%, 100% {{
                transform: scale(1);
            }}
            50% {{
                transform: scale(1.1);
            }}
        }}

        @keyframes shimmer {{
            0% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.7;
            }}
            100% {{
                opacity: 1;
            }}
        }}
        </style>
        ", unsafe_allow_html=True)

    @staticmethod
    def render_generated_report(report_data: Dict[str, Any], options: Dict[str, Any]):
        """Render the generated report with enhanced styling"""
        if not report_data.get("status") == "success":
            st.error(f"보고서 생성 실패: {report_data.get('message', '알 수 없는 오류')}")
            return

        # Report header
        st.markdown("""
        <div class="generated-report-header">
            <div class="report-success-icon">🎉</div>
            <h2 class="report-success-title">보고서 생성 완료!</h2>
            <p class="report-success-subtitle">AI가 분석한 데이터를 바탕으로 전문 보고서를 생성했습니다</p>
        </div>
        """, unsafe_allow_html=True)

        # Report content
        st.markdown("### 📄 생성된 보고서")

        report_content = report_data.get("content", "보고서 내용을 불러올 수 없습니다.")
        
        # Display report in a styled container
        st.markdown(f"""
        <div class="report-content-container">
            {report_content}
        </div>
        """, unsafe_allow_html=True)

        # Download and share options
        EnhancedReportUI._render_download_options(report_content)

        # Report metadata and additional info
        col1, col2 = st.columns(2)

        with col1:
            if options.get("include_metadata") and report_data.get("metadata"):
                with st.expander("📋 보고서 메타데이터"):
                    st.json(report_data["metadata"])

            if report_data.get("data_sources"):
                with st.expander("📊 데이터 출처"):
                    st.json(report_data["data_sources"])

        with col2:
            if report_data.get("kpis"):
                with st.expander("📈 주요 성과 지표"):
                    st.json(report_data["kpis"])

            if report_data.get("chart_specs"):
                with st.expander("📊 차트 명세"):
                    st.json(report_data["chart_specs"])

        # Add CSS styles
        st.markdown("""
        <style>
        .generated-report-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(48, 209, 88, 0.1) 0%, rgba(0, 122, 255, 0.1) 100%);
            border-radius: 20px;
            margin: 2rem 0;
            border: 1px solid rgba(48, 209, 88, 0.2);
        }

        .report-success-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .report-success-title {
            font-size: 2rem;
            font-weight: 700;
            color: #1F2937;
            margin: 0 0 0.5rem 0;
        }

        .report-success-subtitle {
            color: #6B7280;
            font-size: 1.1rem;
            margin: 0;
        }

        .report-content-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            line-height: 1.8;
        }

        .report-content-container h1, .report-content-container h2, .report-content-container h3 {
            color: #1F2937;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        .report-content-container p {
            color: #374151;
            margin-bottom: 1rem;
        }

        .report-content-container ul, .report-content-container ol {
            color: #374151;
            padding-left: 2rem;
        }
        </style>
        ", unsafe_allow_html=True)

    @staticmethod
    def _render_download_options(report_content: str):
        """Render download and sharing options"""
        st.markdown("### 📥 다운로드")

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"seoul_analysis_report_{timestamp}"

        col1, col2 = st.columns(2)

        with col1:
            # Word download
            word_bio = EnhancedReportUI._create_word_report(report_content)
            st.download_button(
                label="📄 Word로 다운로드 (.docx)",
                data=word_bio,
                file_name=f"{base_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                help="보고서를 Word 형식으로 다운로드합니다"
            )

        with col2:
            # PDF download
            pdf_bio = EnhancedReportUI._create_pdf_report(report_content)
            st.download_button(
                label="📄 PDF로 다운로드 (.pdf)",
                data=pdf_bio,
                file_name=f"{base_filename}.pdf",
                mime="application/pdf",
                help="보고서를 PDF 형식으로 다운로드합니다"
            )

    @staticmethod
    def generate_mock_data(config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock data for report when no real data is available"""
        return {
            "sql_df": pd.DataFrame({
                "region": ["강남구", "서초구", "송파구", "중구"],
                "sales_amount": [1500000000, 1200000000, 1100000000, 800000000],
                "transaction_count": [15000, 12000, 11000, 8000],
                "growth_rate": [12.5, 8.3, 9.7, 6.2]
            }),
            "rag_documents": [
                {"content": "서울시 창업 지원 정책에 대한 모의 문서입니다.", "source": "mock_policy.pdf"},
                {"content": "청년 창업 활성화 방안 모의 문서입니다.", "source": "mock_youth.pdf"}
            ],
            "hybrid_search": {
                "answer": "서울시는 다양한 창업 지원 프로그램을 운영하고 있습니다.",
                "confidence": 0.85,
                "sources": [
                    {"type": "pdf", "title": "창업지원정책.pdf", "score": 0.92},
                    {"type": "web", "title": "서울시 창업허브", "score": 0.88}
                ]
            }
        }
