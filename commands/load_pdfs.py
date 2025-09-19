import argparse, os, json, hashlib
from glob import glob
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text, Table, Column, BigInteger, String, Date, JSON, Text, MetaData
from sqlalchemy.dialects.mysql import insert
from pypdf import PdfReader

from utils.config import MYSQL_URI, RAG_DOCS_DIR

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def extract_pdf_text(path: str) -> str:
    try:
        reader = PdfReader(path)
        texts = []
        for p in reader.pages:
            t = p.extract_text() or ""
            if t:
                texts.append(t)
        return "\n\n".join(texts).strip()
    except Exception:
        return ""  # 추출 실패 시 빈 문자열

def upsert_pdfs(folder: str, schema: str = "mydb", pattern: str = "*.pdf", batch: int = 50):
    if not MYSQL_URI:
        raise RuntimeError("MYSQL_URI가 utils/config.py에 설정되어야 합니다.")

    engine = create_engine(MYSQL_URI, pool_pre_ping=True)
    meta = MetaData(schema=schema)
    docs = Table(
        "docs", meta,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("doc_hash", String(64), nullable=False),
        Column("title", String(255), nullable=False),
        Column("source", String(1024)),
        Column("published_date", Date),
        Column("content", Text),
        Column("meta_json", JSON),
        extend_existing=True,
    )

    paths = sorted(glob(os.path.join(folder, pattern)))
    if not paths:
        print(f"경로 '{folder}'에 PDF가 없습니다.")
        return

    rows = []
    for p in paths:
        try:
            with open(p, "rb") as f:
                raw = f.read()
            h = sha256_bytes(raw)
            title = os.path.splitext(os.path.basename(p))[0]
            content = extract_pdf_text(p)
            meta = {
                "size_bytes": len(raw),
                "pages": None,
                "ingested_at": datetime.utcnow().isoformat() + "Z",
            }
            # pages 수 채우기 시도
            try:
                meta["pages"] = len(PdfReader(p).pages)
            except Exception:
                pass

            rows.append({
                "doc_hash": h,
                "title": title,
                "source": os.path.abspath(p),
                "published_date": None,
                "content": content if content else None,
                "meta_json": json.dumps(meta, ensure_ascii=False),
            })
        except Exception as e:
            print(f"⚠️ PDF 처리 실패: {p} - {e}")

    with engine.begin() as conn:
        conn.execute(text(f"USE {schema}"))
        for i in range(0, len(rows), batch):
            chunk = rows[i:i+batch]
            stmt = insert(docs).values(chunk)
            upsert = stmt.on_duplicate_key_update(
                title=stmt.inserted.title,
                source=stmt.inserted.source,
                content=stmt.inserted.content,
                meta_json=stmt.inserted.meta_json,
                published_date=stmt.inserted.published_date
            )
            conn.execute(upsert)

    print(f"✅ PDF 업서트 완료: {len(rows)} files")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ingest PDFs into MySQL 'docs' table (upsert by SHA256).")
    ap.add_argument("--dir", default=RAG_DOCS_DIR, help="PDF 폴더 경로")
    ap.add_argument("--schema", default="mydb", help="스키마명(데이터베이스명)")
    ap.add_argument("--pattern", default="*.pdf", help="파일 패턴")
    ap.add_argument("--batch", type=int, default=50, help="배치 크기")
    args = ap.parse_args()
    upsert_pdfs(args.dir, args.schema, args.pattern, args.batch)