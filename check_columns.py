import pandas as pd

# CSV 파일의 실제 컬럼명 확인
df = pd.read_csv("data/csv/서울시 상권분석서비스(추정매출-상권)_2024년.csv", encoding='cp949', nrows=1)
print("실제 컬럼명:")
for i, col in enumerate(df.columns):
    print(f"{i+1:2d}. {col}")

print(f"\n총 컬럼 수: {len(df.columns)}")
print(f"데이터 형태: {df.shape}")

# 첫 번째 행 데이터 샘플
print("\n첫 번째 행 샘플:")
first_row = df.iloc[0]
for col in df.columns[:10]:  # 처음 10개 컬럼만
    print(f"{col}: {first_row[col]}")