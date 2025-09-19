"""
보고서 컴포저
다양한 데이터 소스를 결합하여 보고서 생성
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)

class ReportComposer:
    """보고서 컴포저 클래스"""

    def __init__(self, config: Dict[str, Any] = None):
        """보고서 컴포저 초기화"""
        self.config = config or {}
        # Initialize Gemini service
        try:
            from llm.gemini_service import get_gemini_service
            self.gemini_service = get_gemini_service()
            self.is_available = self.gemini_service.is_available
        except ImportError:
            logger.warning("Gemini service not available")
            self.gemini_service = None
            self.is_available = False

    def _generate_charts_from_data(self, df: pd.DataFrame) -> List[Any]:
        """
        DataFrame에서 데이터 시각화 차트를 생성합니다.
        """
        charts = []
        if df is None or df.empty:
            return charts

        # Identify potential columns for charting
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Chart 1: Bar chart for a key metric against a category
        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
            try:
                # Try to find a meaningful category and metric
                # Heuristic: find a categorical column with a reasonable number of unique values
                cat_col = None
                for col in categorical_cols:
                    if 1 < df[col].nunique() < 20:
                        cat_col = col
                        break
                
                if cat_col:
                    # Heuristic: find a metric that looks like a value/amount
                    num_col = numeric_cols[0]
                    for col in numeric_cols:
                        if any(kw in col.lower() for kw in ['금액', '매출', 'amount', 'sales', 'value']):
                            num_col = col
                            break
                    
                    # Aggregate data for clarity
                    agg_df = df.groupby(cat_col)[num_col].sum().reset_index().sort_values(by=num_col, ascending=False).head(15)

                    fig = px.bar(
                        agg_df,
                        x=cat_col,
                        y=num_col,
                        title=f"{cat_col} 별 상위 {num_col} 분석",
                        template="plotly_white",
                        labels={num_col: f"{num_col} (합계)", cat_col: cat_col}
                    )
                    fig.update_layout(title_x=0.5, font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
                    charts.append(fig)
            except Exception as e:
                logger.warning(f"Bar chart generation failed: {e}")

        return charts

    def compose_report(self, sql_df: pd.DataFrame = None, rag_documents: List[Dict] = None,
                      web_results: List[Dict] = None, kpis: Dict[str, Any] = None, 
                      target_area: str = None, target_industry: str = None, 
                      style: str = "executive") -> Dict[str, Any]:
        """
        LLM을 사용하여 맥킨지 스타일 보고서 생성
        """
        try:
            # 1. Generate visualizations from data
            charts = self._generate_charts_from_data(sql_df)

            # 2. Prepare context for the LLM
            full_context = self._prepare_llm_context(sql_df, web_results, kpis, target_area, target_industry)

            # 3. Define the McKinsey-style prompt
            prompt_template = """
            당신은 맥킨지와 같은 최상위 경영 컨설팅 회사의 유능한 컨설턴트입니다.
            당신의 임무는 주어진 데이터를 바탕으로 전문적이고, 데이터 기반의, 실행 가능한 비즈니스 분석 보고서를 작성하는 것입니다.

            **보고서 작성 지침:**
            1.  **구조:** 다음 Markdown 구조를 엄격히 준수하여 보고서를 작성하십시오.
                -   `# 제목`: 분석 대상과 목적이 명확히 드러나는 제목
                -   `## 1. Executive Summary (경영진 요약)`: 보고서의 핵심 결론과 권장 사항을 2~3 문장으로 요약합니다. 가장 중요한 내용이므로 처음에 제시해야 합니다.
                -   `## 2. Key Findings (주요 분석 결과)`: 데이터를 분석하여 발견한 가장 중요한 인사이트를 3~5개의 불릿 포인트로 제시합니다. 각 항목은 구체적인 데이터로 뒷받침되어야 합니다.
                -   `## 3. Detailed Analysis (상세 분석)`: 주요 분석 결과를 뒷받침하는 상세한 설명과 데이터 해석을 제공합니다. 제공된 SQL 데이터와 웹 검색 결과를 논리적으로 연결하여 설명합니다.
                -   `## 4. Strategic Recommendations (전략적 제언)`: 분석 결과를 바탕으로 고객이 실행할 수 있는 구체적이고 현실적인 전략을 2~3가지 제안합니다.
            2.  **어조와 스타일:** 명확하고, 간결하며, 전문적인 비즈니스 용어를 사용하십시오. 감정적인 표현은 배제하고, 객관적인 사실과 데이터에 기반하여 논리를 전개하십시오.
            3.  **데이터 활용:** 주어진 컨텍스트의 모든 데이터를 최대한 활용하여 주장을 뒷받침하십시오. 데이터를 언급할 때는 구체적인 수치를 인용하십시오.

            **[분석 컨텍스트]**
            {context}
            """
            
            # 4. Generate report using Gemini
            if self.is_available and self.gemini_service:
                # Use Gemini service for report generation
                analysis_data = {
                    "sql_data": sql_df.to_dict('records') if sql_df is not None and not sql_df.empty else [],
                    "web_results": web_results or [],
                    "kpis": kpis or {},
                    "target_area": target_area,
                    "target_industry": target_industry,
                    "context": full_context
                }
                report_content = self.gemini_service.generate_report(analysis_data, style)
            else:
                # Fallback to simple report generation
                report_content = self._generate_fallback_report(sql_df, web_results, kpis, target_area, target_industry)

            # 5. Assemble the final report object
            metadata = {
                'generated_at': datetime.now().isoformat(),
                'target_area': target_area,
                'target_industry': target_industry,
                'style': style,
                'data_sources': {
                    'sql_records': len(sql_df) if sql_df is not None else 0,
                    'web_results_count': len(web_results) if web_results else 0
                }
            }

            return {
                'status': 'success',
                'content': report_content,
                'charts': charts,  # Include generated charts
                'metadata': metadata,
                'kpis': kpis
            }

        except Exception as e:
            logger.error(f"보고서 생성 중 오류: {e}")
            return {
                'status': 'error',
                'message': f'보고서 생성 중 오류가 발생했습니다: {str(e)}',
                'content': '',
                'charts': [],
                'metadata': {}
            }

    def _prepare_llm_context(self, sql_df, web_results, kpis, target_area, target_industry):
        """Prepare a string context for the LLM from various data sources."""
        context_parts = []
        context_parts.append(f"**분석 대상:** 지역: {target_area or '전체'}, 업종: {target_industry or '전체'}")

        if kpis:
            context_parts.append("\n**주요 성과 지표 (KPIs):**")
            context_parts.append(str(kpis))

        if sql_df is not None and not sql_df.empty:
            context_parts.append("\n**SQL 데이터 분석 결과 (상위 5개 행):**")
            context_parts.append(sql_df.head().to_markdown(index=False))

        if web_results:
            context_parts.append("\n**관련 웹 검색 결과:**")
            for i, res in enumerate(web_results[:3], 1): # Top 3 results
                context_parts.append(f"- **결과 {i}: {res.get('title', '')}**\n  - 요약: {res.get('snippet', '')}")

        return "\n".join(context_parts)

    def _generate_fallback_report(self, sql_df, web_results, kpis, target_area, target_industry):
        """Generate a fallback report when Gemini is not available."""
        try:
            report_lines = []
            
            # Title
            report_lines.append(f"# 서울 상권 분석 보고서")
            report_lines.append(f"**분석 대상:** 지역: {target_area or '전체'}, 업종: {target_industry or '전체'}")
            report_lines.append("")
            
            # Executive Summary
            report_lines.append("## 1. Executive Summary (경영진 요약)")
            report_lines.append("본 보고서는 제공된 데이터를 기반으로 한 상권 분석 결과입니다.")
            if sql_df is not None and not sql_df.empty:
                report_lines.append(f"- 총 {len(sql_df)}개의 데이터 포인트를 분석했습니다.")
            if web_results:
                report_lines.append(f"- {len(web_results)}개의 웹 검색 결과를 참조했습니다.")
            report_lines.append("")
            
            # Key Findings
            report_lines.append("## 2. Key Findings (주요 분석 결과)")
            if kpis:
                for key, value in kpis.items():
                    report_lines.append(f"- **{key}**: {value}")
            else:
                report_lines.append("- 데이터 분석이 완료되었습니다.")
                if sql_df is not None and not sql_df.empty:
                    report_lines.append(f"- 총 {len(sql_df)}개의 레코드를 분석했습니다.")
            report_lines.append("")
            
            # Detailed Analysis
            report_lines.append("## 3. Detailed Analysis (상세 분석)")
            if sql_df is not None and not sql_df.empty:
                report_lines.append("### 데이터 요약")
                report_lines.append(f"- **데이터 행 수**: {len(sql_df)}")
                report_lines.append(f"- **데이터 열 수**: {len(sql_df.columns)}")
                report_lines.append("- **컬럼 목록**:")
                for col in sql_df.columns:
                    report_lines.append(f"  - {col}")
                report_lines.append("")
                
                # Show sample data
                report_lines.append("### 샘플 데이터 (상위 5개 행)")
                report_lines.append("```")
                report_lines.append(sql_df.head().to_string())
                report_lines.append("```")
                report_lines.append("")
            
            # Strategic Recommendations
            report_lines.append("## 4. Strategic Recommendations (전략적 제언)")
            report_lines.append("1. **데이터 기반 의사결정**: 분석된 데이터를 바탕으로 한 전략적 의사결정을 권장합니다.")
            report_lines.append("2. **지속적 모니터링**: 정기적인 데이터 업데이트와 분석을 통해 동향을 파악하세요.")
            report_lines.append("3. **추가 분석**: 더 구체적인 인사이트가 필요한 경우 특정 질의를 통해 추가 분석을 요청하세요.")
            report_lines.append("")
            
            # Conclusion
            report_lines.append("## 5. 결론")
            report_lines.append("본 보고서는 제공된 데이터를 기반으로 작성되었습니다.")
            report_lines.append("더 정교한 분석을 위해서는 Gemini API 설정이 필요합니다.")
            report_lines.append("")
            
            # Footer
            report_lines.append("---")
            report_lines.append(f"*보고서 생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}*")
            report_lines.append("*생성 도구: 서울 상권 분석 LLM (폴백 모드)*")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"폴백 보고서 생성 실패: {e}")
            return f"# 보고서 생성 오류\n\n보고서 생성 중 오류가 발생했습니다: {str(e)}"

def get_report_composer(config: Dict[str, Any] = None) -> ReportComposer:
    """보고서 컴포저 인스턴스 반환"""
    return ReportComposer(config)
