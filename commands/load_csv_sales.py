import argparse
import pandas as pd
from sqlalchemy import create_engine, text, Table, Column, BigInteger, String, Date, Numeric, MetaData
from sqlalchemy.dialects.mysql import insert
from utils.config import MYSQL_URI

def upsert_csv(csv_path: str, schema: str = "mydb", batch: int = 1000, encoding: str | None = None):
    if not MYSQL_URI:
        raise RuntimeError("MYSQL_URI가 utils/config.py에 설정되어야 합니다.")

    # 1) CSV 로드
    df = pd.read_csv(csv_path, encoding=encoding) if encoding else pd.read_csv(csv_path)
    required = {"region_id", "industry_id", "date", "sales_amt"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"CSV에 필수 컬럼이 없습니다: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["sales_amt"] = pd.to_numeric(df["sales_amt"], errors="coerce")
    df = df.dropna(subset=["date", "sales_amt"])

    # 2) 테이블 메타
    engine = create_engine(MYSQL_URI, pool_pre_ping=True)
    meta = MetaData(schema=schema)
    sales_daily = Table(
        "sales_daily", meta,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("region_id", String(64), nullable=False),
        Column("industry_id", String(64), nullable=False),
        Column("sales_date", Date, nullable=False),
        Column("sales_amt", Numeric(18, 2), nullable=False),
        extend_existing=True,
    )

    # 3) 업서트
    rows = [
        {
            "region_id":   str(r["region_id"]),
            "industry_id": str(r["industry_id"]),
            "sales_date":  r["date"],
            "sales_amt":   float(r["sales_amt"]),
        }
        for _, r in df.iterrows()
    ]

    with engine.begin() as conn:
        conn.execute(text(f"USE {schema}"))
        for i in range(0, len(rows), batch):
            chunk = rows[i:i+batch]
            stmt = insert(sales_daily).values(chunk)
            upsert = stmt.on_duplicate_key_update(
                sales_amt=stmt.inserted.sales_amt
                # 누적합 필요 시:
                # sales_amt=sales_daily.c.sales_amt + stmt.inserted.sales_amt
            )
            conn.execute(upsert)

    print(f"✅ 업서트 완료: {len(rows)} rows")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load CSV into MySQL (upsert into sales_daily).")
    ap.add_argument("--csv", default="data/sales.csv", help="CSV 경로")
    ap.add_argument("--schema", default="mydb", help="스키마명(데이터베이스명)")
    ap.add_argument("--batch", type=int, default=1000, help="배치 크기")
    ap.add_argument("--encoding", default=None, help="CSV 인코딩 (예: cp949)")
    args = ap.parse_args()
    upsert_csv(args.csv, args.schema, args.batch, args.encoding)