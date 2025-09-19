# 서울 상권분석 LLM 시스템

## 📋 프로젝트 개요

서울 상권분석 LLM 시스템은 자연어 질의를 통한 상권 데이터 분석과 AI 기반 보고서 자동 생성을 제공하는 통합 플랫폼입니다.

### 🎯 주요 기능

- **📈 자연어 SQL 분석**: LlamaIndex Text-to-SQL을 통한 자연어 질의 처리
- **📚 하이브리드 문서 검색**: BM25 + Vector 검색을 통한 정확한 문서 검색
- **📋 AI 보고서 생성**: 정량/정성 데이터를 종합한 자동 보고서 생성
- **🗺️ 지도 시각화**: Google Maps API 기반 상권 데이터 지도 시각화
- **⚙️ 통합 관리**: Streamlit 기반의 사용자 친화적 인터페이스

### 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Text-to-SQL   │    │   MySQL DB      │
│                 │◄──►│   (LlamaIndex)  │◄──►│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │  Hybrid RAG     │              │
         └──────────────►│  (BM25+Vector)  │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │  LLM Report     │
                        │  Generator      │
                        └─────────────────┘
```

## 🚀 설치 및 실행

### 1. 환경 요구사항

- Python 3.8+
- MySQL 8.0+
- 8GB+ RAM (LLM 모델 실행용)

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

1. MySQL 서버 실행
2. `config.py`에서 데이터베이스 연결 정보 수정:

```python
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'
DB_NAME = 'seoul_commercial'
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

## 📁 프로젝트 구조

```
KDT_project/
├── app.py                           # Streamlit 메인 애플리케이션
├── config.py                        # 설정 관리
├── requirements.txt                 # Python 의존성
├── utils/                           # 유틸리티 모듈
│   ├── database.py                 # 데이터베이스 관리
│   ├── data_loader.py              # CSV → MySQL ETL 로더
│   ├── sql_text2sql.py             # LlamaIndex Text-to-SQL 모듈
│   ├── rag_hybrid.py               # Hybrid Retrieval (BM25 + Vector)
│   └── viz.py                      # Plotly 기반 시각화 함수
├── pipelines/                       # 데이터 파이프라인
│   ├── etl.py                      # ETL 파이프라인 (기본)
│   ├── etl_csv_to_mysql.py         # CSV → MySQL 적재 파이프라인
│   ├── text_to_sql.py              # Text-to-SQL 파이프라인
│   ├── rag.py                      # RAG 파이프라인 (기본)
│   ├── index_pdfs.py               # PDF/웹 문서 인덱싱
│   ├── eval_suite.py               # 평가 스크립트 (정확도, 속도)
│   └── report_generator.py         # 보고서 생성 파이프라인
├── prompts/                         # 프롬프트 엔지니어링
│   ├── text_to_sql_prompt.md       # Text-to-SQL 스키마/예시 프롬프트
│   └── report_generation_prompt.md # 보고서 생성용 시스템 프롬프트
├── tests/                           # 테스트 코드
│   ├── __init__.py
│   ├── test_sql_queries.py         # Text-to-SQL 정확도 테스트
│   ├── test_rag_pipeline.py        # RAG 품질/속도 테스트
│   └── test_report_generation.py   # 보고서 생성 기능 테스트
├── models/                          # 모델 및 인덱스
│   ├── artifacts/                  # 학습된 가중치/벡터 인덱스
│   └── cache/                      # 캐시 (SQL 결과/검색 결과)
├── reports/                         # 생성된 보고서
├── logs/                            # 로그 파일
├── data/                            # 데이터 저장소
│   └── sales.csv                   # 서울시 상권/매출 CSV
└── docs/                            # 프로젝트 문서
    ├── prd.mdc                     # PRD (제품 요구사항 문서)
    ├── Project-Goal-Scope.mdc      # 프로젝트 목표/범위 문서
    ├── project-structure.mdc       # 프로젝트 구조 문서
    ├── system-architecture.mdc     # 아키텍처 문서
    └── user-scenarios.mdc          # 사용자 시나리오 문서
```

## 🚀 실행 방법

1. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 설정**:
   - `config.py`에서 데이터베이스 연결 정보 설정
   - 필요한 API 키 설정 (Gemini, HuggingFace 등)

3. **데이터 준비**:
   - `data/` 폴더에 서울시 상권 데이터 CSV 파일 배치
   - PDF 문서들을 `data/` 폴더에 배치

4. **애플리케이션 실행**:
   ```bash
   streamlit run app.py
   ```

5. **브라우저에서 접속**:
   - 기본 URL: `http://localhost:8501`

## 🧪 테스트 및 개발

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_utils_signatures.py -v

# 커버리지 포함 테스트
pytest --cov=utils --cov=pipelines --cov=app.py
```

### 코드 품질 검사

```bash
# 린팅 (ruff)
python -m ruff check . --fix

# 포맷팅 (black)
python -m black .

# 타입 체크 (mypy)
python -m mypy --strict . --ignore-missing-imports
```

### 개발 환경 설정

1. **개발 의존성 설치**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **환경 변수 설정**:
   ```bash
   cp .env.example .env
   # .env 파일에서 필요한 값들 설정
   ```

3. **데이터베이스 초기화**:
   ```bash
   python -c "from data.database_manager import DatabaseManager; db = DatabaseManager(); db.create_tables()"
   ```

### CI/CD 파이프라인

프로젝트는 GitHub Actions를 통해 자동화된 CI/CD를 지원합니다:

- **코드 품질**: ruff, black, mypy 검사
- **테스트**: pytest를 통한 단위/통합 테스트
- **보안**: 의존성 취약점 스캔
- **배포**: 자동화된 배포 파이프라인

### 브랜치 전략

- `main`: 프로덕션 브랜치
- `dev`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치
- `fix/*`: 버그 수정 브랜치

### 커밋 규칙

Conventional Commits 형식을 따릅니다:

```bash
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

### 풀 리퀘스트 가이드라인

1. **크기 제한**: 400줄 이하의 작은 PR
2. **리뷰어**: 최소 2명의 리뷰 필요
3. **테스트**: 모든 테스트 통과 필수
4. **문서**: README 업데이트 필요시 포함

## 📋 주요 기능

### 1. SQL 분석 (📈)
- 자연어로 데이터베이스 질의
- Text-to-SQL 변환
- 쿼리 결과 시각화

### 2. 문헌 검색 (📚)
- 하이브리드 RAG 검색 (BM25 + Vector)
- PDF 문서 인덱싱
- 관련 문서 검색

### 3. 보고서 생성 (📋)
- SQL 결과 + RAG 결과 종합
- LLM 기반 인사이트 생성
- 자동 보고서 작성

### 4. KPI 대시보드 (📊)
- 성능 지표 모니터링
- 사용 통계 추적
- 트렌드 분석

### 5. 시스템 상태 (🔍)
- 컴포넌트별 상태 확인
- 시스템 메트릭 모니터링
- 오류 로그 관리

### 6. 시스템 설정 (⚙️)
- 데이터베이스 연결 설정
- 모델 파라미터 조정
- 시스템 구성 관리

## 🔧 사용 방법

### 1. 시스템 설정

1. **시스템 설정** 탭에서 데이터베이스 연결 테스트
2. 테이블 생성 버튼으로 스키마 초기화
3. CSV 파일 업로드 후 ETL 실행

### 2. SQL 분석

1. **SQL 분석** 탭 선택
2. 자연어로 질의 입력 (예: "강남구에서 가장 매출이 높은 업종은?")
3. AI가 자동으로 SQL 변환 및 실행
4. 결과를 테이블과 차트로 확인

### 3. 문서 검색

1. **문헌 검색** 탭 선택
2. 검색 유형 선택 (하이브리드/벡터/BM25)
3. 검색어 입력 (예: "창업 지원 정책")
4. 관련 문서 및 점수 확인

### 4. 보고서 생성

1. **보고서 생성** 탭 선택
2. 분석 대상 지역/업종 설정
3. 보고서 유형 선택
4. AI가 자동으로 종합 보고서 생성
5. JSON/Markdown 형식으로 다운로드

## 📊 데이터 스키마

### MySQL 테이블 구조

```sql
-- 지역 정보
regions (region_id, name, gu, dong, lat, lon, adm_code)

-- 업종 정보  
industries (industry_id, name, nace_kor, category)

-- 2024년 매출 데이터
sales_2024 (region_id, industry_id, date, sales_amt, sales_cnt, visitors)

-- 특성 데이터
features (region_id, industry_id, feat_json)

-- 문서 정보
docs (doc_id, title, source, url, published_date, content_text)
```

## 🤖 AI 모델

### LLM 모델
- **기본**: `microsoft/DialoGPT-medium`
- **대체**: `distilgpt2`
- **용도**: Text-to-SQL, 보고서 생성

### 임베딩 모델
- **기본**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **용도**: 벡터 검색, 문서 임베딩

### 검색 시스템
- **BM25**: 키워드 기반 검색
- **Vector**: 의미 기반 검색
- **Hybrid**: 두 방식의 가중 결합

## 📈 성능 지표

- **SQL 변환 정확성**: ≥ 90%
- **응답 속도 (P95)**: ≤ 3초
- **근거 각주 포함률**: ≥ 80%
- **사용자 만족도**: ≥ 4.0/5.0

## 🔍 주요 기능 상세

### Text-to-SQL 파이프라인

```python
# 자연어 질의 예시
query = "강남구에서 가장 매출이 높은 업종은 무엇인가요?"

# 자동 생성 SQL
SELECT i.name, SUM(s.sales_amt) as total_sales
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
WHERE r.gu = '강남구'
GROUP BY i.name
ORDER BY total_sales DESC
LIMIT 1;
```

### Hybrid RAG 검색

```python
# 검색 결과 예시
{
    "text": "서울시 창업 지원 정책...",
    "vector_score": 0.85,
    "bm25_score": 0.72,
    "combined_score": 0.80,
    "metadata": {
        "title": "서울시 창업 가이드",
        "source": "서울창업정보",
        "published_date": "2024-01-15"
    }
}
```

### AI 보고서 구조

1. **경영진 요약**: 핵심 발견사항, 트렌드, 권고사항
2. **정량 분석**: 데이터 개요, 주요 지표, 통계적 인사이트
3. **정성 분석**: 관련 정책, 시장 동향, 성공 사례
4. **인사이트 및 권고사항**: 전략적 제안, 실행 계획

## 🛠️ 개발 및 확장

### 새로운 기능 추가

1. **새 파이프라인**: `pipelines/` 디렉토리에 모듈 추가
2. **새 프롬프트**: `prompts/` 디렉토리에 템플릿 추가
3. **새 UI 탭**: `app.py`에 함수 추가

### 설정 커스터마이징

- `config.py`: 시스템 설정 수정
- `prompts/`: LLM 프롬프트 조정
- `utils/database.py`: 데이터베이스 스키마 수정

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**서울 상권분석 LLM 시스템** - 데이터 기반 의사결정을 위한 AI 플랫폼
