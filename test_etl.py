import pandas as pd
from utils.csv_etl import get_csv_etl_service

# CSV 파일의 실제 컬럼명 확인
df = pd.read_csv("data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv", encoding='cp949', nrows=1)
print("실제 컬럼명:")
for i, col in enumerate(df.columns):
    print(f"{i+1:2d}. {col}")

print(f"\n총 컬럼 수: {len(df.columns)}")

# ETL 서비스 테스트
etl_service = get_csv_etl_service()

# 테이블 정보 확인
print("\n=== 테이블 정보 ===")
table_info = etl_service.get_table_info()
print(table_info)

# CSV 로드 실행
print("\n=== CSV 로드 실행 ===")
result = etl_service.load_all_csv_files()
print(result)