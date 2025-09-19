# 데이터 파이프라인 가이드

이 디렉토리는 서울시 상권분석서비스 데이터를 처리하고 RAG 시스템에서 활용할 수 있도록 하는 파이프라인들을 포함합니다.

## 📁 디렉토리 구조

```
data/
├── csv/                                    # CSV 데이터 파일
│   └── 서울시 상권분석서비스(추정매출-상권)_2024년.csv
├── pdf/                                    # PDF 문서 파일들
├── schema_updated.sql                      # 업데이트된 데이터베이스 스키마
├── csv_etl_pipeline.py                    # CSV ETL 파이프라인
├── pdf_indexing_pipeline.py               # PDF 인덱싱 파이프라인
├── rag_integration_service.py             # RAG 통합 서비스
├── run_data_pipeline.py                   # 통합 실행 스크립트
└── README.md                              # 이 파일
```

## 🚀 빠른 시작

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. MySQL 데이터베이스 설정

MySQL 서버가 실행 중인지 확인하고, 다음 설정으로 데이터베이스를 준비하세요:

```sql
CREATE DATABASE IF NOT EXISTS seoul_commercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 전체 파이프라인 실행

```bash
python data/run_data_pipeline.py --pipeline all
```

### 4. 개별 파이프라인 실행

#### CSV ETL만 실행
```bash
python data/run_data_pipeline.py --pipeline csv
```

#### PDF 인덱싱만 실행
```bash
python data/run_data_pipeline.py --pipeline pdf
```

#### RAG 통합 서비스만 실행
```bash
python data/run_data_pipeline.py --pipeline rag
```

## 📊 데이터 구조

### CSV 데이터 (상권분석서비스)
- **파일**: `서울시 상권분석서비스(추정매출-상권)_2024년.csv`
- **인코딩**: CP949
- **행 수**: 87,179행
- **열 수**: 55열
- **주요 컬럼**:
  - 기준_년분기_코드
  - 상권_구분_코드, 상권_구분_코드_명
  - 상권_코드, 상권_코드_명
  - 서비스_업종_코드, 서비스_업종_코드_명
  - 당월_매출_금액, 당월_매출_건수
  - 요일별, 시간대별, 성별, 연령대별 매출 데이터

### PDF 문서
- **위치**: `data/pdf/` 디렉토리
- **파일 수**: 89개 PDF 파일
- **문서 유형**:
  - 공고문 (창업지원사업, 입주기업 모집 등)
  - 정책 문서 (창업지원조례, 지원방안 등)
  - 보고서 (자료집, 성과보고서 등)
  - 가이드라인 (신청서, 양식 등)

## 🗄️ 데이터베이스 스키마

### 주요 테이블

1. **commercial_districts** - 상권 구분
2. **commercial_areas** - 상권
3. **service_industries** - 서비스 업종
4. **sales_data** - 매출 데이터 (메인 테이블)
5. **pdf_documents** - PDF 문서 메타데이터
6. **document_chunks** - PDF 문서 청크 (RAG용)

### 뷰
- **v_sales_summary** - 매출 요약 뷰

## 🔧 설정 옵션

### 데이터베이스 설정
```bash
python data/run_data_pipeline.py \
  --db-host localhost \
  --db-user root \
  --db-password your_password \
  --db-name seoul_commercial \
  --db-port 3306
```

### 파일 경로 설정
```bash
python data/run_data_pipeline.py \
  --csv-file path/to/your/csv/file.csv \
  --pdf-directory path/to/your/pdf/directory
```

## 📈 사용 예시

### 1. CSV 데이터 검색
```python
from data.rag_integration_service import RAGIntegrationService

# 서비스 초기화
rag_service = RAGIntegrationService(db_config)
rag_service.connect_database()
rag_service.load_embedding_model()

# SQL 데이터 검색
sql_results = rag_service.search_sql_data("강남구 매출", limit=10)
print(f"검색 결과: {len(sql_results)}건")
```

### 2. PDF 문서 검색
```python
# PDF 문서 검색
pdf_results = rag_service.search_pdf_documents("창업지원", limit=5)
print(f"문서 검색 결과: {len(pdf_results)}건")
```

### 3. 하이브리드 검색
```python
# 통합 검색
hybrid_result = rag_service.hybrid_search("강남구 창업지원", sql_limit=5, pdf_limit=5)
print(f"SQL 결과: {hybrid_result['total_sql_results']}건")
print(f"PDF 결과: {hybrid_result['total_pdf_results']}건")
```

### 4. 인사이트 생성
```python
# 인사이트 생성
insights = rag_service.generate_insights(
    hybrid_result['sql_results'],
    hybrid_result['pdf_results']
)
print(f"요약: {insights['summary']}")
print(f"주요 발견사항: {insights['key_findings']}")
```

## 🐛 문제 해결

### 1. 인코딩 오류
CSV 파일이 CP949 인코딩으로 되어 있어서 발생하는 문제입니다. 파이프라인에서 자동으로 처리하지만, 수동으로 확인하려면:

```python
import pandas as pd
df = pd.read_csv('data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv', encoding='cp949')
```

### 2. 데이터베이스 연결 오류
MySQL 서버가 실행 중인지, 사용자 권한이 올바른지 확인하세요:

```sql
SHOW DATABASES;
USE seoul_commercial;
SHOW TABLES;
```

### 3. PDF 처리 오류
PDF 파일이 손상되었거나 암호화된 경우 발생할 수 있습니다. 로그를 확인하여 문제가 되는 파일을 식별하세요.

### 4. 메모리 부족
대용량 데이터 처리 시 메모리 부족이 발생할 수 있습니다. 배치 크기를 조정하세요:

```python
# csv_etl_pipeline.py에서 batch_size 조정
self.insert_sales_data(sales_data, batch_size=500)  # 기본값: 1000
```

## 📝 로그

실행 로그는 `data_pipeline.log` 파일에 저장됩니다. 문제 발생 시 이 파일을 확인하세요.

## 🔄 업데이트

### 새로운 CSV 데이터 추가
1. CSV 파일을 `data/csv/` 디렉토리에 추가
2. `run_data_pipeline.py`의 `--csv-file` 옵션으로 파일 경로 지정
3. 파이프라인 재실행

### 새로운 PDF 문서 추가
1. PDF 파일을 `data/pdf/` 디렉토리에 추가
2. `run_data_pipeline.py`의 `--pipeline pdf` 옵션으로 인덱싱만 실행

## 📞 지원

문제가 발생하거나 질문이 있으시면 프로젝트 이슈를 생성하거나 개발팀에 문의하세요.
