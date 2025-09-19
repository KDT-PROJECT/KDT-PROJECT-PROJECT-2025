# utils/rag.py
# -------------------------------------------------------------
# Hybrid RAG (Vector + BM25) for LlamaIndex 0.10.50 generation
# - BM25: rank-bm25 (플러그인 불필요, 의존성 충돌 회피)
# - Vector: LlamaIndex VectorStoreIndex + as_retriever()
# - LLM: Gemini (Settings.llm.complete 사용)
# -------------------------------------------------------------

from __future__ import annotations
import os
from typing import List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from utils.config import (
    GEMINI_API_KEY,
    GEMINI_LLM_MODEL,
    GEMINI_EMB_MODEL,
    RAG_DOCS_DIR,
    RAG_INDEX_DIR,
)

from llama_index.core import (
    Settings,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.llms.huggingface import HuggingFaceLLM
# from llama_index.embeddings.gemini import GeminiEmbedding  # Import issue - using alternative
from llama_index.embeddings.google import GoogleGenerativeAIEmbedding


# =========================
# Internal helpers
# =========================
def _init_llm() -> None:
    """Settings 전역에 LLM/임베딩/청킹 설정."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY가 utils/config.py에 설정되어야 합니다.")

    # LLM / Embedding
    Settings.llm = HuggingFaceLLM(model_name="microsoft/DialoGPT-medium")
    Settings.embed_model = GoogleGenerativeAIEmbedding(api_key=GEMINI_API_KEY, model_name=GEMINI_EMB_MODEL)

    # 청킹(문단/문장 길이에 따라 조정 가능)
    Settings.node_parser = SentenceSplitter(
        chunk_size=900,
        chunk_overlap=120,
    )


def _ensure_docs_dir(docs_dir: str) -> None:
    if not os.path.isdir(docs_dir):
        raise RuntimeError(f"문서 폴더를 찾지 못했습니다: {docs_dir}")


def _normalize(arr: np.ndarray | List[float]) -> np.ndarray:
    x = np.asarray(arr, dtype=float)
    if x.size == 0:
        return x
    mn, mx = np.min(x), np.max(x)
    if mx - mn < 1e-12:
        return np.zeros_like(x)
    return (x - mn) / (mx - mn)


# =========================
# Index build / load
# =========================
def build_or_load_index(docs_dir: str = RAG_DOCS_DIR, persist_dir: str = RAG_INDEX_DIR) -> VectorStoreIndex:
    """
    data/docs의 PDF/TXT를 인덱싱하고 저장. 이미 있으면 로드.
    - 최초 1회: 문서 로드 → 임베딩 → VectorStoreIndex 생성 → persist
    - 이후: 저장된 인덱스 로드
    """
    _init_llm()
    os.makedirs(persist_dir, exist_ok=True)

    # 저장된 인덱스 우선 로드
    try:
        storage = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage)
    except Exception:
        pass  # 없거나 손상된 경우 신규 생성

    # 신규 인덱스 생성
    _ensure_docs_dir(docs_dir)
    reader = SimpleDirectoryReader(docs_dir, recursive=True, required_exts=[".pdf", ".txt"])
    docs = reader.load_data()
    if not docs:
        raise RuntimeError(f"{docs_dir} 에서 PDF/TXT 문서를 찾지 못했습니다.")

    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(persist_dir=persist_dir)
    return index


def rebuild_index(docs_dir: str = RAG_DOCS_DIR, persist_dir: str = RAG_INDEX_DIR) -> VectorStoreIndex:
    """
    강제 재구축: 기존 인덱스를 삭제하고 다시 구축합니다.
    """
    _init_llm()
    if os.path.isdir(persist_dir):
        # 안전 삭제
        for root, dirs, files in os.walk(persist_dir, topdown=False):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except Exception:
                    pass
        try:
            os.rmdir(persist_dir)
        except Exception:
            pass
    os.makedirs(persist_dir, exist_ok=True)
    return build_or_load_index(docs_dir, persist_dir)


# =========================
# Rank-BM25 retrieval
# =========================
def _bm25_topk_indices(query: str, corpus_texts: List[str], top_k: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    rank-bm25로 corpus에 대한 BM25 점수를 계산해 상위 인덱스를 반환
    - 간단 토크나이저: 공백 기준 (MVP)
    """
    tokenized_corpus = [t.split() for t in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)  # shape = (len(corpus),)
    scores = np.asarray(scores, dtype=float)

    order = np.argsort(scores)[::-1]
    order_topk = order[:top_k]
    return order_topk, scores[order_topk]


# =========================
# Public API
# =========================
def rag_query_hybrid(
    question_ko: str,
    docs_dir: str = RAG_DOCS_DIR,
    persist_dir: str = RAG_INDEX_DIR,
    top_k: int = 5,
    alpha: float = 0.5,
) -> str:
    """
    Hybrid RAG: Vector(임베딩) + BM25를 late-fusion(정규화 가중합)으로 결합해
    한국어 답변을 생성합니다.
      - alpha: 벡터 검색 가중치 (0.0~1.0), BM25 가중치는 (1 - alpha)
    """
    if not question_ko or not question_ko.strip():
        raise ValueError("질문이 비어 있습니다.")

    index = build_or_load_index(docs_dir=docs_dir, persist_dir=persist_dir)

    # 1) Vector 검색 (LlamaIndex as_retriever)
    vec_retriever = index.as_retriever(similarity_top_k=top_k)
    vec_nodes = vec_retriever.retrieve(question_ko)
    vec_texts = [n.node.get_content() for n in vec_nodes]
    vec_scores = np.array([getattr(n, "score", 0.0) or 0.0 for n in vec_nodes], dtype=float)

    # 2) BM25 검색 (rank-bm25; 전체 코퍼스 기준 상위 top_k)
    all_nodes = list(index.docstore.docs.values())
    all_texts = [n.get_content() for n in all_nodes]

    # 코퍼스가 적을 때(또는 비었을 때) 방어
    if not all_texts:
        raise RuntimeError("인덱스 내부의 문서가 비어 있습니다. PDF/TXT 파일을 추가해 주세요.")

    bm_idx, bm_scores_top = _bm25_topk_indices(question_ko, all_texts, top_k=max(top_k, 10))
    bm_nodes_top = [all_nodes[i] for i in bm_idx[:top_k]]
    bm_scores_top = bm_scores_top[:top_k]

    # 3) Late fusion: 정규화 후 가중합으로 상위 K 선정
    vec_norm = _normalize(vec_scores) if vec_scores.size else np.zeros(0)
    bm_norm = _normalize(bm_scores_top) if bm_scores_top.size else np.zeros(0)

    fused: List[Tuple[str, float]] = []
    # (a) 벡터 결과 먼저 넣기
    for i, vn in enumerate(vec_nodes):
        fused.append((vn.node.get_content(), float(alpha * (vec_norm[i] if i < len(vec_norm) else 0.0))))

    # (b) BM25 결과 추가 (중복 텍스트는 스킵)
    existing = {t for t, _ in fused}
    for i, bn in enumerate(bm_nodes_top):
        t = bn.get_content()
        if t in existing:
            continue
        fused.append((t, float((1.0 - alpha) * (bm_norm[i] if i < len(bm_norm) else 0.0))))

    # 점수 기준 정렬 후 상위 K
    fused_sorted = sorted(fused, key=lambda x: x[1], reverse=True)[:top_k]
    context = "\n\n".join([t[:1200] for t, _ in fused_sorted])  # 너무 길면 잘라서 사용

    # 4) LLM 호출(한국어 답변 + 간단 근거 인용)
    system_prompt = (
        "당신은 한국어 리서치 어시스턴트입니다. "
        "아래 컨텍스트를 바탕으로 질문에 간결하고 정확히 답하세요. "
        "가능하면 근거 문장을 짧게 인용하고, 출처/제목을 함께 언급하세요. "
        "추측은 피하고, 컨텍스트에 없는 내용은 모른다고 답하세요."
    )
    prompt = f"{system_prompt}\n\n[컨텍스트]\n{context}\n\n[질문]\n{question_ko}"

    answer = Settings.llm.complete(prompt).text
    return answer