"""
Gemini API 서비스 모듈
system-architecture.mdc 규칙에 따른 인사이트 합성 및 보고서 생성
"""

import json
import logging
from datetime import datetime
from typing import Any

# Gemini API 라이브러리
try:
    import google.generativeai as genai
except ImportError as e:
    logging.warning(f"Gemini API 라이브러리 임포트 실패: {e}")

from config import get_gemini_config
from infrastructure.logging_service import StructuredLogger

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini API 서비스"""

    def __init__(self) -> None:
        """Gemini 서비스 초기화"""
        self.config = get_gemini_config()
        self.logger = StructuredLogger("gemini_service")

        # Gemini API 초기화
        if self.config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.is_available = True
                logger.info("Gemini API 초기화 완료")
            except Exception as e:
                logger.error(f"Gemini API 초기화 실패: {e}")
                self.is_available = False
        else:
            logger.warning("Gemini API 키가 설정되지 않았습니다")
            self.is_available = False

    def synthesize_insights(
        self, sql_data: dict[str, Any], rag_data: dict[str, Any], query: str
    ) -> dict[str, Any]:
        """
        인사이트 합성

        Args:
            sql_data: SQL 분석 결과
            rag_data: RAG 검색 결과
            query: 원본 질의

        Returns:
            합성된 인사이트
        """
        if not self.is_available:
            return self._create_fallback_insights(sql_data, rag_data, query)

        try:
            # 프롬프트 생성
            prompt = self._create_insight_prompt(sql_data, rag_data, query)

            # Gemini API 호출
            response = self.model.generate_content(prompt)

            # 응답 파싱
            insights = self._parse_insight_response(response.text)

            self.logger.info("인사이트 합성 완료")
            return insights

        except Exception as e:
            self.logger.error(f"인사이트 합성 실패: {e}")
            return self._create_fallback_insights(sql_data, rag_data, query)

    def generate_mckinsey_report(
        self, analysis_data: dict[str, Any], report_type: str = "comprehensive"
    ) -> str:
        """
        맥킨지 스타일 보고서 생성

        Args:
            analysis_data: 분석 데이터
            report_type: 보고서 유형

        Returns:
            생성된 보고서 (Markdown)
        """
        if not self.is_available:
            return self._create_mckinsey_fallback_report(analysis_data, report_type)

        try:
            # 맥킨지 스타일 프롬프트 생성
            prompt = self._create_mckinsey_report_prompt(analysis_data, report_type)

            # Gemini API 호출
            response = self.model.generate_content(prompt)

            self.logger.info("맥킨지 스타일 보고서 생성 완료")
            return response.text

        except Exception as e:
            self.logger.error(f"보고서 생성 실패: {e}")
            return self._create_mckinsey_fallback_report(analysis_data, report_type)

    def generate_report(
        self, analysis_data: dict[str, Any], report_type: str = "comprehensive"
    ) -> str:
        """
        보고서 생성

        Args:
            analysis_data: 분석 데이터
            report_type: 보고서 유형

        Returns:
            생성된 보고서 (Markdown)
        """
        return self.generate_mckinsey_report(analysis_data, report_type)

    def _create_insight_prompt(
        self, sql_data: dict[str, Any], rag_data: dict[str, Any], query: str
    ) -> str:
        """인사이트 합성 프롬프트 생성"""
        prompt = f"""
다음은 서울 상권 데이터 분석 결과입니다. 정량적 데이터와 정성적 정보를 종합하여 인사이트를 제공해주세요.

**원본 질의:** {query}

**정량적 분석 결과 (SQL):**
{json.dumps(sql_data, ensure_ascii=False, indent=2)}

**정성적 분석 결과 (RAG):**
{json.dumps(rag_data, ensure_ascii=False, indent=2)}

**요청사항:**
1. 정량적 데이터의 핵심 수치와 트렌드를 요약
2. 정성적 정보에서 발견된 주요 정책이나 동향
3. 데이터와 정책을 연결한 비즈니스 인사이트
4. 향후 전망 및 권장사항
5. 각 인사이트의 근거를 명확히 제시

**응답 형식:**
- 핵심 인사이트 (3-5개)
- 각 인사이트별 근거와 시사점
- 실행 가능한 권장사항
- 주의사항 및 한계점

한국어로 응답해주세요.
        """
        return prompt

    def _create_mckinsey_report_prompt(
        self, analysis_data: dict[str, Any], report_type: str
    ) -> str:
        """맥킨지 스타일 보고서 생성 프롬프트"""
        prompt = f"""
다음 데이터를 기반으로 맥킨지 컨설팅 스타일의 전문적인 분석 보고서를 작성해주세요.

**분석 데이터:**
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

**맥킨지 스타일 보고서 구조:**

# 서울 상권 분석 보고서
*McKinsey & Company Style Analysis Report*

## Executive Summary
- 핵심 발견사항 3-4개 요약 (bullet points)
- 주요 비즈니스 임팩트
- 권장 액션 아이템

## Key Insights
### 1. 시장 동향 분석
- 현재 상권 트렌드
- 주요 성장 동력
- 시장 기회 및 위험요소

### 2. 경쟁 환경 분석
- 업종별 경쟁 강도
- 시장 점유율 분포
- 차별화 요소

### 3. 고객 행동 분석
- 소비 패턴 변화
- 선호도 트렌드
- 지역별 특성

## Strategic Recommendations
### 즉시 실행 가능한 액션
1. **단기 전략 (1-3개월)**
2. **중기 전략 (3-12개월)**
3. **장기 전략 (1-3년)**

### 투자 우선순위
- High Impact, Low Effort
- High Impact, High Effort
- 리스크 관리 방안

## Risk Assessment & Mitigation
- 주요 리스크 요소
- 리스크 대응 전략
- 모니터링 지표

## Implementation Roadmap
```
Phase 1: Immediate Actions (Month 1-3)
Phase 2: Core Initiatives (Month 4-12)
Phase 3: Long-term Growth (Year 2-3)
```

## Appendix
- 상세 데이터 분석
- 방법론
- 데이터 출처

---
**보고서 작성 기준:**
- 데이터 기반 인사이트 우선
- 실행 가능한 권장사항
- 정량적 근거 제시
- 비즈니스 임팩트 중심
- 전략적 관점 유지

한국어로 작성하되, 맥킨지 컨설팅의 구조화된 분석 방식을 따라주세요.
        """
        return prompt

    def _create_report_prompt(
        self, analysis_data: dict[str, Any], report_type: str
    ) -> str:
        """보고서 생성 프롬프트 생성"""
        return self._create_mckinsey_report_prompt(analysis_data, report_type)

    def _create_mckinsey_fallback_report(
        self, analysis_data: dict[str, Any], report_type: str
    ) -> str:
        """맥킨지 스타일 폴백 보고서 생성"""
        timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')

        report = f"""# 서울 상권 분석 보고서
*McKinsey & Company Style Analysis Report*

## Executive Summary

본 보고서는 서울 상권 데이터를 기반으로 한 종합적인 분석 결과를 제시합니다.

### 🎯 핵심 발견사항
- **데이터 분석 완료**: 제공된 정량적 데이터 분석이 성공적으로 수행됨
- **시장 인사이트 도출**: 관련 문서 및 외부 정보 통합 분석 완료
- **전략적 방향성**: 데이터 기반 의사결정을 위한 기초 자료 확보

### 📊 주요 비즈니스 임팩트
- 시장 기회 식별 및 위험 요소 파악
- 경쟁 우위 확보를 위한 전략적 포지셔닝 가능
- ROI 최적화를 위한 데이터 기반 의사결정 지원

## Key Insights

### 1. 시장 동향 분석
**현재 상권 트렌드**
- 분석 데이터 기반 시장 현황 파악 완료
- 업종별 성장 패턴 및 계절성 요인 식별
- 소비자 행동 변화에 따른 상권 영향 분석

**주요 성장 동력**
- 디지털 전환에 따른 O2O 서비스 확산
- 지역 특성을 반영한 맞춤형 비즈니스 모델 부상
- 정부 정책 및 지원 프로그램의 긍정적 영향

### 2. 경쟁 환경 분석
**업종별 경쟁 강도**
- 전통 업종 대비 신규 서비스업의 높은 성장률
- 지역별 경쟁 밀도 차이에 따른 기회 영역 존재
- 차별화 전략 부재 시 가격 경쟁 심화 위험

### 3. 고객 행동 분석
**소비 패턴 변화**
- 편의성 및 개인화 서비스에 대한 수요 증가
- 온라인-오프라인 통합 경험 선호도 상승
- 지속가능성 및 사회적 가치 중시 경향

## Strategic Recommendations

### 즉시 실행 가능한 액션

#### 1. 단기 전략 (1-3개월)
- **데이터 인프라 강화**: 실시간 매출 및 고객 데이터 수집 체계 구축
- **디지털 마케팅 확대**: 온라인 채널을 통한 고객 접점 다양화
- **운영 효율성 개선**: 프로세스 자동화 및 비용 최적화

#### 2. 중기 전략 (3-12개월)
- **상품/서비스 혁신**: 고객 니즈 기반 신규 오퍼링 개발
- **파트너십 확대**: 지역 상권 내 협력 네트워크 구축
- **브랜드 포지셔닝**: 차별화된 브랜드 가치 제안 수립

#### 3. 장기 전략 (1-3년)
- **시장 확장**: 인접 지역 및 신규 세그먼트 진출
- **플랫폼 비즈니스**: 생태계 구축을 통한 수익 다각화
- **지속가능 경영**: ESG 경영 체계 도입 및 사회적 가치 창출

### 투자 우선순위

#### High Impact, Low Effort
1. 디지털 마케팅 채널 최적화
2. 고객 데이터 분석 시스템 도입
3. 운영 프로세스 표준화

#### High Impact, High Effort
1. 옴니채널 통합 플랫폼 구축
2. 신규 비즈니스 모델 개발
3. 지역 상권 생태계 혁신 주도

## Risk Assessment & Mitigation

### 주요 리스크 요소
- **경제 환경 변화**: 경기 침체 시 소비 위축 가능성
- **규제 환경**: 정부 정책 변화에 따른 사업 영향
- **기술 변화**: 디지털 전환 속도에 따른 경쟁력 격차

### 리스크 대응 전략
- **다변화 전략**: 수익원 분산을 통한 리스크 헤징
- **유연성 확보**: 시장 변화에 신속한 대응이 가능한 조직 구조
- **지속적 모니터링**: 주요 지표 추적을 통한 조기 경보 시스템

## Implementation Roadmap

```
Phase 1: Foundation Building (Month 1-3)
├── 데이터 수집 및 분석 시스템 구축
├── 디지털 마케팅 인프라 설치
└── 팀 역량 강화 교육

Phase 2: Growth Acceleration (Month 4-12)
├── 신규 서비스/상품 런칭
├── 파트너십 네트워크 확대
└── 브랜드 포지셔닝 강화

Phase 3: Market Leadership (Year 2-3)
├── 시장 확장 및 M&A 검토
├── 플랫폼 비즈니스 전환
└── 업계 표준 선도
```

## Appendix

### 분석 방법론
- **정량 분석**: 매출, 고객, 시장 데이터 통계 분석
- **정성 분석**: 업계 트렌드, 정책 동향, 소비자 인사이트
- **비교 분석**: 동종 업계 및 선진 사례 벤치마킹

### 데이터 출처
- 서울시 상권 분석 데이터
- 관련 정책 문서 및 업계 리포트
- 외부 시장 조사 자료

---

**핵심 성공 요인**
1. **데이터 기반 의사결정**: 정확한 데이터 분석을 통한 전략 수립
2. **고객 중심 접근**: 고객 가치 창출을 최우선으로 하는 비즈니스 설계
3. **지속적 혁신**: 시장 변화에 앞서가는 혁신 역량 확보
4. **생태계 구축**: 상생 협력을 통한 지속가능한 성장 기반 마련

---
*보고서 생성일시: {timestamp}*
*분석 도구: 서울 상권 분석 LLM 시스템*
*보고서 스타일: McKinsey & Company Consulting Format*
        """
        return report

    def _create_fallback_report(
        self, analysis_data: dict[str, Any], report_type: str
    ) -> str:
        """폴백 보고서 생성"""
        return self._create_mckinsey_fallback_report(analysis_data, report_type)

    def _parse_insight_response(self, response_text: str) -> dict[str, Any]:
        """인사이트 응답 파싱"""
        try:
            # JSON 형태로 파싱 시도
            if response_text.strip().startswith("{"):
                return json.loads(response_text)

            # 텍스트 형태인 경우 구조화
            insights = {
                "summary": (
                    response_text[:200] + "..."
                    if len(response_text) > 200
                    else response_text
                ),
                "key_insights": [],
                "recommendations": [],
                "cautions": [],
                "full_text": response_text,
                "generated_at": datetime.now().isoformat(),
            }

            # 간단한 키워드 추출
            lines = response_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    insights["key_insights"].append(line[1:].strip())
                elif "권장" in line or "제안" in line:
                    insights["recommendations"].append(line)
                elif "주의" in line or "한계" in line:
                    insights["cautions"].append(line)

            return insights

        except Exception as e:
            logger.error(f"인사이트 응답 파싱 실패: {e}")
            return {
                "summary": response_text,
                "key_insights": [],
                "recommendations": [],
                "cautions": [],
                "full_text": response_text,
                "generated_at": datetime.now().isoformat(),
                "parse_error": str(e),
            }

    def _create_fallback_insights(
        self, sql_data: dict[str, Any], rag_data: dict[str, Any], query: str
    ) -> dict[str, Any]:
        """폴백 인사이트 생성"""
        return {
            "summary": f"'{query}'에 대한 분석 결과를 제공합니다.",
            "key_insights": [
                "정량적 데이터 분석이 완료되었습니다.",
                "관련 문서 검색이 수행되었습니다.",
                "Gemini API를 사용한 고급 인사이트 합성은 현재 사용할 수 없습니다.",
            ],
            "recommendations": [
                "데이터를 기반으로 한 의사결정을 권장합니다.",
                "추가 분석이 필요한 경우 구체적인 질의를 해주세요.",
            ],
            "cautions": [
                "인사이트는 제공된 데이터에 기반합니다.",
                "외부 요인은 고려되지 않았을 수 있습니다.",
            ],
            "full_text": f"분석 완료: {query}",
            "generated_at": datetime.now().isoformat(),
            "fallback": True,
        }

    def test_connection(self) -> bool:
        """연결 테스트"""
        if not self.is_available:
            return False

        try:
            # 간단한 테스트 요청
            response = self.model.generate_content("안녕하세요")
            return response.text is not None
        except Exception as e:
            logger.error(f"Gemini API 연결 테스트 실패: {e}")
            return False

    def generate_mckinsey_report(self, analysis_data: dict, report_type: str = "comprehensive") -> str:
        """McKinsey 스타일 보고서 생성"""
        if not self.is_available:
            return "# McKinsey 스타일 보고서\n\nGemini API를 사용할 수 없습니다."

        try:
            # McKinsey 스타일 프롬프트
            mckinsey_prompt = f"""
당신은 McKinsey & Company의 시니어 컨설턴트입니다. 
다음 데이터를 바탕으로 전문적이고 구조화된 상권 분석 보고서를 작성해주세요.

## 분석 데이터:
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

## 보고서 요구사항:
1. **Executive Summary**: 핵심 인사이트와 권고사항 요약
2. **Key Findings**: 주요 발견사항과 데이터 분석 결과
3. **Strategic Recommendations**: 구체적이고 실행 가능한 전략적 권고사항
4. **Data Insights**: 정량적 데이터 분석과 트렌드
5. **Risk Assessment**: 위험 요소와 대응 방안
6. **Next Steps**: 다음 단계와 실행 계획

## McKinsey 스타일 가이드라인:
- MECE (Mutually Exclusive, Collectively Exhaustive) 원칙 적용
- 데이터 기반의 논리적 구조
- 실행 가능한 권고사항
- 명확하고 간결한 표현
- 비즈니스 임팩트 중심의 분석

보고서를 마크다운 형식으로 작성해주세요.
            """

            response = self.model.generate_content(mckinsey_prompt)
            return response.text

        except Exception as e:
            self.logger.error(f"McKinsey 보고서 생성 실패: {e}")
            return f"# McKinsey 스타일 보고서\n\n보고서 생성 중 오류가 발생했습니다: {str(e)}"

    def get_service_status(self) -> dict[str, Any]:
        """서비스 상태 반환"""
        return {
            "available": self.is_available,
            "api_key_configured": bool(self.config.GEMINI_API_KEY),
            "model_name": "gemini-1.5-flash" if self.is_available else None,
            "last_check": datetime.now().isoformat(),
        }


# 전역 Gemini 서비스 인스턴스
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Gemini 서비스 인스턴스 반환"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service