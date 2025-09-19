import pandas as pd
import glob
import os

csv_files = glob.glob("data/csv/*.csv")
encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']

for file in csv_files:
    print(f"File: {os.path.basename(file)}")

    for encoding in encodings:
        try:
            df = pd.read_csv(file, encoding=encoding, nrows=3)
            print(f"OK Encoding: {encoding}")
            print(f"Columns: {list(df.columns)[:5]}")  # First 5 columns
            print(f"Shape: {df.shape}")
            break
        except Exception as e:
            print(f"FAIL Encoding {encoding} failed: {str(e)[:50]}")
    print("---")