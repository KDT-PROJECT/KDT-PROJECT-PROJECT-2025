from io import BytesIO
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def build_pdf_report(summary_text: str, df: pd.DataFrame | None = None) -> bytes:
    """
    요약 텍스트 + (선택) 표 일부를 PDF 바이트로 반환
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, H-50, "상권 인사이트 보고서")
    c.setFont("Helvetica", 10)
    c.drawString(40, H-65, datetime.now().strftime("%Y-%m-%d %H:%M"))

    # 본문
    text = c.beginText(40, H-100)
    text.setFont("Helvetica", 11)
    for line in summary_text.split("\n"):
        text.textLine(line[:110])
    c.drawText(text)

    # 표 (일부)
    if df is not None and not df.empty:
        y = H-260
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "표 (일부):")
        y -= 18
        c.setFont("Helvetica", 9)
        preview = df.head(20).copy()
        cols = [str(cn) for cn in preview.columns]
        c.drawString(40, y, " | ".join(cols)[:110])
        y -= 13
        for _, row in preview.iterrows():
            c.drawString(40, y, " | ".join([str(x) for x in row.values])[:110])
            y -= 12
            if y < 60:
                c.showPage(); y = H-60; c.setFont("Helvetica", 9)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()