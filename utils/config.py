# utils/config.py
# ⚠️ 퍼블릭 저장소에 올리지 마세요. (키 노출 위험)

# 🔑 Google Gemini API Key (예: "AIza...") - 반드시 실제 값으로 교체
GEMINI_API_KEY = "여기에_GEMINI_API_KEY"

# 🗄️ MySQL 연결 URI (예: "mysql+pymysql://user:pass@host:3306/dbname")
MYSQL_URI = "mysql+pymysql://user:pass@host:3306/dbname"

# 📚 문서 위치(RAG용)
RAG_DOCS_DIR = "data/docs"

# 🔧 모델명(필요 시 조정)
GEMINI_LLM_MODEL = "models/gemini-1.5-flash"
GEMINI_EMB_MODEL = "text-embedding-004"

# 💾 인덱스 보관 디렉터리
RAG_INDEX_DIR = "models/artifacts/rag_index"