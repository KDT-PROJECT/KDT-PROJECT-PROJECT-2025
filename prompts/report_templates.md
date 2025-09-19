<<<<<<< HEAD
# Report Templates for Seoul Commercial Analysis System

## Executive Summary Template

```markdown
## Executive Summary

### 분석 개요
- **분석 대상**: {target_area} {target_industry} 업종
- **분석 기간**: {analysis_period}
- **데이터 출처**: 서울시 상권 데이터베이스, 정책문서

### 핵심 발견사항
1. **매출 성과**: {total_sales}원 (전년 대비 {growth_rate}%)
2. **성장 동력**: {growth_drivers}
3. **주요 리스크**: {main_risks}

### 핵심 수치
- 총 매출: {total_sales}원
- 평균 성장률: {avg_growth_rate}%
- 거래 건수: {transaction_count}건
- 평균 거래 금액: {avg_transaction_amount}원

### 주요 권고사항
1. {recommendation_1}
2. {recommendation_2}
3. {recommendation_3}
```

## Quantitative Analysis Template

```markdown
## Quantitative Analysis

### 매출 현황
{quantitative_data_table}

### 업종별 비교
{industry_comparison_table}

### 지역별 분석
{regional_analysis_table}

### 시계열 분석
{time_series_analysis}

### 성과 지표
{performance_metrics_table}
```

## Qualitative Analysis Template

```markdown
## Qualitative Analysis

### 정책 환경
{policy_environment_analysis}

### 시장 환경
{market_environment_analysis}

### 경쟁 환경
{competitive_environment_analysis}

### 기술 동향
{technology_trends_analysis}

### 소비자 동향
{consumer_trends_analysis}
```

## Insights & Recommendations Template

```markdown
## Insights & Recommendations

### 핵심 인사이트
1. **{insight_1_title}**: {insight_1_description}
2. **{insight_2_title}**: {insight_2_description}
3. **{insight_3_title}**: {insight_3_description}

### 전략적 권고사항
1. **{strategy_1_title}**
   - 목표: {strategy_1_goal}
   - 실행 방안: {strategy_1_action}
   - 예상 효과: {strategy_1_effect}

2. **{strategy_2_title}**
   - 목표: {strategy_2_goal}
   - 실행 방안: {strategy_2_action}
   - 예상 효과: {strategy_2_effect}

3. **{strategy_3_title}**
   - 목표: {strategy_3_goal}
   - 실행 방안: {strategy_3_action}
   - 예상 효과: {strategy_3_effect}

### 실행 로드맵
- **단기 (1-3개월)**: {short_term_actions}
- **중기 (3-6개월)**: {medium_term_actions}
- **장기 (6-12개월)**: {long_term_actions}
```

## Risk Assessment Template

```markdown
## Risk Assessment

### 시장 리스크
- **위험도**: {market_risk_level}
- **주요 위험 요소**: {market_risk_factors}
- **영향도**: {market_risk_impact}
- **대응 방안**: {market_risk_mitigation}

### 정책 리스크
- **위험도**: {policy_risk_level}
- **주요 위험 요소**: {policy_risk_factors}
- **영향도**: {policy_risk_impact}
- **대응 방안**: {policy_risk_mitigation}

### 경쟁 리스크
- **위험도**: {competitive_risk_level}
- **주요 위험 요소**: {competitive_risk_factors}
- **영향도**: {competitive_risk_impact}
- **대응 방안**: {competitive_risk_mitigation}

### 기술 리스크
- **위험도**: {technology_risk_level}
- **주요 위험 요소**: {technology_risk_factors}
- **영향도**: {technology_risk_impact}
- **대응 방안**: {technology_risk_mitigation}

### 종합 리스크 평가
- **전체 위험도**: {overall_risk_level}
- **핵심 리스크**: {key_risks}
- **리스크 관리 전략**: {risk_management_strategy}
```

## Appendix Template

```markdown
## Appendix

### 데이터 출처
- **정량 데이터**: 서울시 상권 데이터베이스
- **정성 데이터**: 정책문서, 시장보고서, 업계분석자료
- **수집일**: {data_collection_date}
- **업데이트 주기**: {update_frequency}

### SQL 쿼리
```sql
{sql_queries}
```

### 참고 문헌
{references}

### 데이터 메타데이터
{data_metadata}

### 보고서 생성 정보
- **생성일**: {generation_date}
- **생성 도구**: Seoul Commercial Analysis LLM System
- **AI 모델**: {ai_models}
- **데이터 처리**: {data_processing_tools}
- **시각화**: {visualization_tools}
```

## Chart Specifications Template

```json
{
  "charts": [
    {
      "type": "bar",
      "title": "업종별 매출 비교",
      "x": "industry_name",
      "y": "sales_amount",
      "data": "industry_sales_data"
    },
    {
      "type": "line",
      "title": "월별 매출 트렌드",
      "x": "month",
      "y": "sales_amount",
      "data": "monthly_sales_data"
    },
    {
      "type": "pie",
      "title": "지역별 매출 비중",
      "labels": "region_name",
      "values": "sales_amount",
      "data": "regional_sales_data"
    },
    {
      "type": "scatter",
      "title": "거래 건수 vs 매출액",
      "x": "transaction_count",
      "y": "sales_amount",
      "data": "transaction_sales_data"
    }
  ]
}
```

## Report Style Guidelines

### Executive Style
- 간결하고 핵심적인 내용
- 수치 중심의 분석
- 3-5개의 핵심 인사이트
- 실행 가능한 권고사항

### Detailed Style
- 상세한 분석과 근거
- 다각도의 관점 제시
- 풍부한 데이터와 차트
- 심층적인 인사이트

### Summary Style
- 요약된 핵심 내용
- 시각적 요소 중심
- 빠른 이해를 위한 구조
- 액션 아이템 중심

## Citation Format

### 데이터 인용
- [데이터-1] sales_2024 테이블, 전체 지역, 2024년 1-12월
- [데이터-2] regions 테이블, 지역별 집계, 2024년
- [데이터-3] industries 테이블, 업종별 집계, 2024년

### 문서 인용
- [문서-1] "2024 디지털 뉴딜 정책", p.5-8, 과학기술정보통신부, 2024.03
- [문서-2] "2024 IT 시장 동향 보고서", p.15-20, 한국IT산업협회, 2024.09
- [문서-3] "IT 업계 경쟁 현황 분석", p.25-30, 한국경영연구원, 2024.08

## Quality Checklist

### 내용 품질
- [ ] 데이터 정확성 검증
- [ ] 논리적 일관성 확인
- [ ] 근거와 결론의 연결성
- [ ] 객관적 분석과 주관적 해석 구분

### 형식 품질
- [ ] 마크다운 문법 준수
- [ ] 표와 차트 가독성
- [ ] 인용 형식 일관성
- [ ] 오타 및 문법 오류 검토

### 완성도
- [ ] 모든 섹션 완성
- [ ] 데이터 출처 명시
- [ ] 실행 가능한 권고사항
- [ ] 리스크 평가 포함
=======
# Report Templates for Seoul Commercial Analysis System

## Executive Summary Template

```markdown
## Executive Summary

### 분석 개요
- **분석 대상**: {target_area} {target_industry} 업종
- **분석 기간**: {analysis_period}
- **데이터 출처**: 서울시 상권 데이터베이스, 정책문서

### 핵심 발견사항
1. **매출 성과**: {total_sales}원 (전년 대비 {growth_rate}%)
2. **성장 동력**: {growth_drivers}
3. **주요 리스크**: {main_risks}

### 핵심 수치
- 총 매출: {total_sales}원
- 평균 성장률: {avg_growth_rate}%
- 거래 건수: {transaction_count}건
- 평균 거래 금액: {avg_transaction_amount}원

### 주요 권고사항
1. {recommendation_1}
2. {recommendation_2}
3. {recommendation_3}
```

## Quantitative Analysis Template

```markdown
## Quantitative Analysis

### 매출 현황
{quantitative_data_table}

### 업종별 비교
{industry_comparison_table}

### 지역별 분석
{regional_analysis_table}

### 시계열 분석
{time_series_analysis}

### 성과 지표
{performance_metrics_table}
```

## Qualitative Analysis Template

```markdown
## Qualitative Analysis

### 정책 환경
{policy_environment_analysis}

### 시장 환경
{market_environment_analysis}

### 경쟁 환경
{competitive_environment_analysis}

### 기술 동향
{technology_trends_analysis}

### 소비자 동향
{consumer_trends_analysis}
```

## Insights & Recommendations Template

```markdown
## Insights & Recommendations

### 핵심 인사이트
1. **{insight_1_title}**: {insight_1_description}
2. **{insight_2_title}**: {insight_2_description}
3. **{insight_3_title}**: {insight_3_description}

### 전략적 권고사항
1. **{strategy_1_title}**
   - 목표: {strategy_1_goal}
   - 실행 방안: {strategy_1_action}
   - 예상 효과: {strategy_1_effect}

2. **{strategy_2_title}**
   - 목표: {strategy_2_goal}
   - 실행 방안: {strategy_2_action}
   - 예상 효과: {strategy_2_effect}

3. **{strategy_3_title}**
   - 목표: {strategy_3_goal}
   - 실행 방안: {strategy_3_action}
   - 예상 효과: {strategy_3_effect}

### 실행 로드맵
- **단기 (1-3개월)**: {short_term_actions}
- **중기 (3-6개월)**: {medium_term_actions}
- **장기 (6-12개월)**: {long_term_actions}
```

## Risk Assessment Template

```markdown
## Risk Assessment

### 시장 리스크
- **위험도**: {market_risk_level}
- **주요 위험 요소**: {market_risk_factors}
- **영향도**: {market_risk_impact}
- **대응 방안**: {market_risk_mitigation}

### 정책 리스크
- **위험도**: {policy_risk_level}
- **주요 위험 요소**: {policy_risk_factors}
- **영향도**: {policy_risk_impact}
- **대응 방안**: {policy_risk_mitigation}

### 경쟁 리스크
- **위험도**: {competitive_risk_level}
- **주요 위험 요소**: {competitive_risk_factors}
- **영향도**: {competitive_risk_impact}
- **대응 방안**: {competitive_risk_mitigation}

### 기술 리스크
- **위험도**: {technology_risk_level}
- **주요 위험 요소**: {technology_risk_factors}
- **영향도**: {technology_risk_impact}
- **대응 방안**: {technology_risk_mitigation}

### 종합 리스크 평가
- **전체 위험도**: {overall_risk_level}
- **핵심 리스크**: {key_risks}
- **리스크 관리 전략**: {risk_management_strategy}
```

## Appendix Template

```markdown
## Appendix

### 데이터 출처
- **정량 데이터**: 서울시 상권 데이터베이스
- **정성 데이터**: 정책문서, 시장보고서, 업계분석자료
- **수집일**: {data_collection_date}
- **업데이트 주기**: {update_frequency}

### SQL 쿼리
```sql
{sql_queries}
```

### 참고 문헌
{references}

### 데이터 메타데이터
{data_metadata}

### 보고서 생성 정보
- **생성일**: {generation_date}
- **생성 도구**: Seoul Commercial Analysis LLM System
- **AI 모델**: {ai_models}
- **데이터 처리**: {data_processing_tools}
- **시각화**: {visualization_tools}
```

## Chart Specifications Template

```json
{
  "charts": [
    {
      "type": "bar",
      "title": "업종별 매출 비교",
      "x": "industry_name",
      "y": "sales_amount",
      "data": "industry_sales_data"
    },
    {
      "type": "line",
      "title": "월별 매출 트렌드",
      "x": "month",
      "y": "sales_amount",
      "data": "monthly_sales_data"
    },
    {
      "type": "pie",
      "title": "지역별 매출 비중",
      "labels": "region_name",
      "values": "sales_amount",
      "data": "regional_sales_data"
    },
    {
      "type": "scatter",
      "title": "거래 건수 vs 매출액",
      "x": "transaction_count",
      "y": "sales_amount",
      "data": "transaction_sales_data"
    }
  ]
}
```

## Report Style Guidelines

### Executive Style
- 간결하고 핵심적인 내용
- 수치 중심의 분석
- 3-5개의 핵심 인사이트
- 실행 가능한 권고사항

### Detailed Style
- 상세한 분석과 근거
- 다각도의 관점 제시
- 풍부한 데이터와 차트
- 심층적인 인사이트

### Summary Style
- 요약된 핵심 내용
- 시각적 요소 중심
- 빠른 이해를 위한 구조
- 액션 아이템 중심

## Citation Format

### 데이터 인용
- [데이터-1] sales_2024 테이블, 전체 지역, 2024년 1-12월
- [데이터-2] regions 테이블, 지역별 집계, 2024년
- [데이터-3] industries 테이블, 업종별 집계, 2024년

### 문서 인용
- [문서-1] "2024 디지털 뉴딜 정책", p.5-8, 과학기술정보통신부, 2024.03
- [문서-2] "2024 IT 시장 동향 보고서", p.15-20, 한국IT산업협회, 2024.09
- [문서-3] "IT 업계 경쟁 현황 분석", p.25-30, 한국경영연구원, 2024.08

## Quality Checklist

### 내용 품질
- [ ] 데이터 정확성 검증
- [ ] 논리적 일관성 확인
- [ ] 근거와 결론의 연결성
- [ ] 객관적 분석과 주관적 해석 구분

### 형식 품질
- [ ] 마크다운 문법 준수
- [ ] 표와 차트 가독성
- [ ] 인용 형식 일관성
- [ ] 오타 및 문법 오류 검토

### 완성도
- [ ] 모든 섹션 완성
- [ ] 데이터 출처 명시
- [ ] 실행 가능한 권고사항
- [ ] 리스크 평가 포함
>>>>>>> b15a617 (first commit)
