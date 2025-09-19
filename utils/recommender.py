from typing import Tuple, Optional
import pandas as pd
from sqlalchemy import create_engine, text

from utils.config import GEMINI_API_KEY, MYSQL_URI, GEMINI_LLM_MODEL, GEMINI_EMB_MODEL
from llama_index.core import Settings, SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

def _init_llm():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY가 config.py에 설정되어야 합니다.")
    Settings.llm = Gemini(api_key=GEMINI_API_KEY, model=GEMINI_LLM_MODEL)
    Settings.embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY, model_name=GEMINI_EMB_MODEL)

def _get_sqldb() -> SQLDatabase:
    if not MYSQL_URI:
        raise RuntimeError("MYSQL_URI가 config.py에 설정되어야 합니다.")
    engine = create_engine(MYSQL_URI, pool_pre_ping=True)
    return SQLDatabase(engine)

def run_text_sql(user_query_ko: str, table_whitelist: Optional[list] = None) -> Tuple[str, Optional[pd.DataFrame], Optional[str]]:
    """
    한국어 질의 -> (LLM) SQL 생성/실행 -> 한국어 요약
    Returns: (final_text, df(optional), generated_sql(optional))
    """
    _init_llm()
    sql_db = _get_sqldb()

    # ✅ 0.10.x 방식: NLSQLTableQueryEngine 사용
    qengine = NLSQLTableQueryEngine(
        sql_database=sql_db,
        tables=table_whitelist,     # 안전하게 허용 테이블만 지정 권장
        synthesize_response=True,   # 결과를 LLM이 자연어로 요약
        verbose=False
    )

    sys_prompt = (
        "당신은 한국어 Text-to-SQL 전문가입니다. "
        "사용자 질문을 SQL(SELECT만)로 변환하여 MySQL에서 실행하고, "
        "결과를 간결한 한국어로 요약하세요. "
        "DELETE/UPDATE/DDL은 절대 금지합니다. "
        "가능하면 표로 핵심 수치를 보여주세요."
    )
    prompt = f"{sys_prompt}\n\n질문: {user_query_ko}"
    response = qengine.query(prompt)

    # 1) 자연어 요약
    final_text = str(response)

    # 2) 생성된 SQL 추출 (버전에 따라 key가 다를 수 있어 방어적으로)
    generated_sql = None
    try:
        # 최신 버전에서 흔히 들어오는 위치
        generated_sql = response.metadata.get("sql_query")
        if not generated_sql and hasattr(response, "extra_info"):
            generated_sql = response.extra_info.get("sql_query")
    except Exception:
        pass

    # 3) DataFrame으로 결과 재조회 (가능한 경우)
    df = None
    try:
        if generated_sql:
            engine = _get_sqldb().engine
            with engine.connect() as conn:
                res = conn.execute(text(generated_sql))
                df = pd.DataFrame(res.fetchall(), columns=res.keys())
    except Exception:
        df = None

    return final_text, df, generated_sql