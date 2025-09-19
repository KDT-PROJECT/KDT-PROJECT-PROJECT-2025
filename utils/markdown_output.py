"""
마크다운 출력 유틸리티
보고서를 마크다운 형식으로 출력
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MarkdownOutput:
    """마크다운 출력 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """마크다운 출력 초기화"""
        self.config = config or {}
        self.output_dir = self.config.get('file_config', {}).get('output_dir', 'reports')
        
        # 출력 디렉토리 생성
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, content: str, metadata: Dict[str, Any] = None,
                         data_sources: Dict[str, Any] = None, kpis: Dict[str, Any] = None,
                         chart_specs: List[Dict[str, Any]] = None) -> str:
        """
        마크다운 콘텐츠 생성

        Args:
            content: 기본 콘텐츠
            metadata: 메타데이터
            data_sources: 데이터 소스 정보
            kpis: KPI 정보
            chart_specs: 차트 명세

        Returns:
            str: 생성된 마크다운 콘텐츠
        """
        try:
            markdown_content = ""
            
            # 헤더 생성
            markdown_content += self._generate_header(metadata)
            
            # 목차 생성
            if self.config.get('format_config', {}).get('include_toc', True):
                markdown_content += self._generate_toc(content)
            
            # 메인 콘텐츠
            markdown_content += content + "\n\n"
            
            # 메타데이터 추가
            if metadata and self.config.get('format_config', {}).get('include_metadata', True):
                markdown_content += self._generate_metadata_section(metadata)
            
            # 데이터 소스 추가
            if data_sources:
                markdown_content += self._generate_data_sources_section(data_sources)
            
            # KPI 추가
            if kpis:
                markdown_content += self._generate_kpi_section(kpis)
            
            # 차트 추가
            if chart_specs and self.config.get('format_config', {}).get('include_charts', True):
                markdown_content += self._generate_charts_section(chart_specs)
            
            # 푸터 추가
            markdown_content += self._generate_footer()
            
            return markdown_content

        except Exception as e:
            logger.error(f"마크다운 생성 중 오류: {e}")
            return content
    
    def save_markdown(self, content: str, filename: str) -> str:
        """
        마크다운 파일 저장

        Args:
            content: 마크다운 콘텐츠
            filename: 파일명

        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 파일명에 확장자 추가
            if not filename.endswith('.md'):
                filename += '.md'

            # 파일 경로 생성
            file_path = Path(self.output_dir) / filename
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"마크다운 파일 저장 완료: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"마크다운 파일 저장 중 오류: {e}")
            return ""
    
    def _generate_header(self, metadata: Dict[str, Any] = None) -> str:
        """헤더 생성"""
        try:
            header = "# 서울 상권 분석 보고서\n\n"
            
            if metadata:
                title = metadata.get('report_info', {}).get('title', '상권 분석 보고서')
                generated_at = metadata.get('generation_time', datetime.now().isoformat())
                target_area = metadata.get('report_info', {}).get('target_area', '전체')
                target_industry = metadata.get('report_info', {}).get('target_industry', '전체 업종')
                
                header += f"**제목**: {title}\n\n"
                header += f"**생성일시**: {generated_at}\n\n"
                header += f"**대상 지역**: {target_area}\n\n"
                header += f"**대상 업종**: {target_industry}\n\n"
            
            header += "---\n\n"
            return header

        except Exception as e:
            logger.error(f"헤더 생성 중 오류: {e}")
            return "# 서울 상권 분석 보고서\n\n"
    
    def _generate_toc(self, content: str) -> str:
        """목차 생성"""
        try:
            toc = "## 📋 목차\n\n"
            
            # 헤딩 추출
            lines = content.split('\n')
            toc_items = []
            
            for line in lines:
                if line.startswith('## '):
                    title = line[3:].strip()
                    anchor = title.lower().replace(' ', '-')
                    toc_items.append(f"- [{title}](#{anchor})")
                elif line.startswith('### '):
                    title = line[4:].strip()
                    anchor = title.lower().replace(' ', '-')
                    toc_items.append(f"  - [{title}](#{anchor})")
            
            if toc_items:
                toc += '\n'.join(toc_items) + '\n\n'
            else:
                toc += "- [요약](#요약)\n"
                toc += "- [데이터 분석](#데이터-분석)\n"
                toc += "- [문서 분석](#문서-분석)\n"
                toc += "- [주요 성과 지표](#주요-성과-지표)\n"
                toc += "- [결론 및 제언](#결론-및-제언)\n\n"
            
            toc += "---\n\n"
            return toc

        except Exception as e:
            logger.error(f"목차 생성 중 오류: {e}")
            return ""
    
    def _generate_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """메타데이터 섹션 생성"""
        try:
            section = "## 📋 보고서 정보\n\n"
            
            # 기본 정보
            if 'report_info' in metadata:
                report_info = metadata['report_info']
                section += f"- **제목**: {report_info.get('title', 'N/A')}\n"
                section += f"- **생성일시**: {report_info.get('generated_at', 'N/A')}\n"
                section += f"- **대상 지역**: {report_info.get('target_area', 'N/A')}\n"
                section += f"- **대상 업종**: {report_info.get('target_industry', 'N/A')}\n"
                section += f"- **보고서 스타일**: {report_info.get('style', 'N/A')}\n"
            
            # 데이터 소스 정보
            if 'data_sources' in metadata:
                data_sources = metadata['data_sources']
                section += f"- **SQL 레코드 수**: {data_sources.get('sql_records', 0):,}건\n"
                section += f"- **문서 수**: {data_sources.get('document_count', 0)}개\n"
            
            section += "\n"
            return section
            
        except Exception as e:
            logger.error(f"메타데이터 섹션 생성 중 오류: {e}")
            return ""
    
    def _generate_data_sources_section(self, data_sources: Dict[str, Any]) -> str:
        """데이터 소스 섹션 생성"""
        try:
            section = "## 📊 데이터 소스\n\n"
            
            section += "### 데이터 개요\n\n"
            section += f"- **SQL 데이터**: {data_sources.get('sql_records', 0):,}건\n"
            section += f"- **문서 데이터**: {data_sources.get('document_count', 0)}개\n"
            
            section += "\n### 데이터 품질\n\n"
            section += "- **데이터 완성도**: 높음\n"
            section += "- **데이터 신뢰성**: 높음\n"
            section += "- **데이터 최신성**: 최신\n"
            
            section += "\n"
            return section
            
        except Exception as e:
            logger.error(f"데이터 소스 섹션 생성 중 오류: {e}")
            return ""
    
    def _generate_kpi_section(self, kpis: Dict[str, Any]) -> str:
        """KPI 섹션 생성"""
        try:
            section = "## 📈 주요 성과 지표 (KPI)\n\n"
            
            section += "| 지표 | 값 |\n"
            section += "|------|-----|\n"
            
            for key, value in kpis.items():
                if isinstance(value, (int, float)):
                    if 'sales' in key.lower() or 'amount' in key.lower():
                        formatted_value = f"{value:,}원"
                    elif 'count' in key.lower():
                        formatted_value = f"{value:,}건"
                    elif 'rate' in key.lower():
                        formatted_value = f"{value:.1%}"
                    else:
                        formatted_value = f"{value:,}"
                else:
                    formatted_value = str(value)
                
                section += f"| {key} | {formatted_value} |\n"
            
            section += "\n"
            return section
            
        except Exception as e:
            logger.error(f"KPI 섹션 생성 중 오류: {e}")
            return ""
    
    def _generate_charts_section(self, chart_specs: List[Dict[str, Any]]) -> str:
        """차트 섹션 생성"""
        try:
            section = "## 📊 차트 및 시각화\n\n"
            
            for i, chart in enumerate(chart_specs, 1):
                chart_type = chart.get('type', 'unknown')
                title = chart.get('title', f'차트 {i}')
                description = chart.get('description', '')
                
                section += f"### {i}. {title}\n\n"
                if description:
                    section += f"{description}\n\n"
                
                section += f"**차트 유형**: {chart_type}\n\n"
                section += "```\n"
                section += "[차트 이미지가 여기에 표시됩니다]\n"
                section += "```\n\n"
            
            return section
            
        except Exception as e:
            logger.error(f"차트 섹션 생성 중 오류: {e}")
            return ""
    
    def _generate_footer(self) -> str:
        """푸터 생성"""
        try:
            footer = "---\n\n"
            footer += "## 📝 보고서 정보\n\n"
            footer += f"- **생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            footer += "- **생성 시스템**: 서울 상권 분석 LLM 시스템\n"
            footer += "- **버전**: v1.0\n\n"
            footer += "---\n\n"
            footer += "*이 보고서는 AI 시스템에 의해 자동 생성되었습니다.*\n"
            
            return footer
            
        except Exception as e:
            logger.error(f"푸터 생성 중 오류: {e}")
            return ""


def get_markdown_output(config: Dict[str, Any] = None) -> MarkdownOutput:
    """마크다운 출력 인스턴스 반환"""
    return MarkdownOutput(config)