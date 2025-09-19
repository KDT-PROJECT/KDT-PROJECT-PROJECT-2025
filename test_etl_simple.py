from utils.csv_etl import get_csv_etl_service
import pandas as pd

print("=== ETL 테스트 시작 ===")

# ETL 서비스 초기화
etl_service = get_csv_etl_service()

# 데이터베이스 연결 확인
if etl_service.engine:
    print("OK 데이터베이스 연결 성공")
else:
    print("FAIL 데이터베이스 연결 실패")
    exit()

# 테이블 생성 테스트
print("\n=== 테이블 생성 테스트 ===")
table_created = etl_service.create_commercial_table()
if table_created:
    print("OK 테이블 생성 성공")
else:
    print("FAIL 테이블 생성 실패")

# 단일 파일 처리 테스트 (샘플 데이터만)
print("\n=== 샘플 데이터 처리 테스트 ===")
sample_file = "data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv"

# 샘플 데이터 읽기 (첫 100행만)
df_sample = pd.read_csv(sample_file, encoding='cp949', nrows=100)
print(f"샘플 데이터 크기: {df_sample.shape}")

# 컬럼명 정리 테스트
df_cleaned = etl_service.clean_column_names(df_sample)
print(f"정리된 데이터 크기: {df_cleaned.shape}")
print(f"정리된 컬럼명: {list(df_cleaned.columns)[:5]}...")

# 결측값 및 데이터 타입 처리
df_cleaned = df_cleaned.fillna(0)
numeric_columns = [col for col in df_cleaned.columns if '매출' in col or '건수' in col]
for col in numeric_columns:
    df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce').fillna(0)

print(f"데이터 타입 처리 완료")

# 샘플 데이터 DB 삽입
try:
    df_cleaned.to_sql(
        'commercial_analysis',
        con=etl_service.engine,
        if_exists='append',
        index=False,
        chunksize=50
    )
    print(f"OK 샘플 데이터 {len(df_cleaned)}건 삽입 성공")
except Exception as e:
    print(f"FAIL 데이터 삽입 실패: {str(e)}")

# 테이블 정보 확인
print("\n=== 테이블 정보 확인 ===")
table_info = etl_service.get_table_info()
print(f"테이블 상태: {table_info.get('status')}")
if table_info.get('status') == 'success':
    print(f"총 행 수: {table_info.get('row_count')}")
    print(f"컬럼 수: {len(table_info.get('columns', []))}")

print("\n=== ETL 테스트 완료 ===")