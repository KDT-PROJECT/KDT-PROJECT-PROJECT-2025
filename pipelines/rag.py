"""
Hybrid RAG 파이프라인 - BM25 + Vector 검색을 통한 문서 검색
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
import pandas as pd
from chromadb.config import Settings
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from utils.database import DatabaseManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridRAGPipeline:
    """Hybrid RAG 파이프라인 클래스"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        vector_store_path: str = "models/artifacts/chroma_db",
        bm25_corpus_path: str = "models/artifacts/bm25_corpus.json",
    ):
        """
        Hybrid RAG 파이프라인 초기화

        Args:
            db_manager: 데이터베이스 매니저 인스턴스
            vector_store_path: 벡터 스토어 경로
            bm25_corpus_path: BM25 코퍼스 경로
        """
        self.db_manager = db_manager
        self.vector_store_path = vector_store_path
        self.bm25_corpus_path = bm25_corpus_path

        # 모델 초기화
        self.embed_model = None
        self.sentence_transformer = None
        self.chroma_client = None
        self.vector_store = None
        self.vector_index = None
        self.bm25 = None
        self.bm25_corpus = []
        self.bm25_documents = []

        # 초기화
        self._initialize_models()
        self._initialize_vector_store()
        self._load_bm25_corpus()

    def _initialize_models(self):
        """모델 초기화"""
        try:
            # 임베딩 모델 초기화
            self.embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )

            # Sentence Transformer 초기화 (BM25와 함께 사용)
            self.sentence_transformer = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )

            logger.info("임베딩 모델이 초기화되었습니다.")

        except Exception as e:
            logger.error(f"모델 초기화 중 오류 발생: {e}")

    def _initialize_vector_store(self):
        """벡터 스토어 초기화"""
        try:
            # ChromaDB 클라이언트 초기화
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_store_path,
                settings=Settings(anonymized_telemetry=False),
            )

            # 컬렉션 생성 또는 가져오기
            try:
                collection = self.chroma_client.get_collection("seoul_documents")
            except:
                collection = self.chroma_client.create_collection("seoul_documents")

            # 벡터 스토어 생성
            self.vector_store = ChromaVectorStore(chroma_collection=collection)

            # 스토리지 컨텍스트 생성
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            # 벡터 인덱스 생성
            self.vector_index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context,
                embed_model=self.embed_model,
            )

            logger.info("벡터 스토어가 초기화되었습니다.")

        except Exception as e:
            logger.error(f"벡터 스토어 초기화 중 오류 발생: {e}")

    def _load_bm25_corpus(self):
        """BM25 코퍼스 로드"""
        try:
            corpus_path = Path(self.bm25_corpus_path)
            if corpus_path.exists():
                with open(corpus_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.bm25_corpus = data.get("corpus", [])
                    self.bm25_documents = data.get("documents", [])

                # BM25 인덱스 생성
                if self.bm25_corpus:
                    self.bm25 = BM25Okapi(self.bm25_corpus)
                    logger.info(
                        f"BM25 코퍼스가 로드되었습니다: {len(self.bm25_corpus)} 문서"
                    )
                else:
                    logger.info("BM25 코퍼스가 비어있습니다.")
            else:
                logger.info("BM25 코퍼스 파일이 없습니다.")

        except Exception as e:
            logger.error(f"BM25 코퍼스 로드 중 오류 발생: {e}")

    def _save_bm25_corpus(self):
        """BM25 코퍼스 저장"""
        try:
            corpus_path = Path(self.bm25_corpus_path)
            corpus_path.parent.mkdir(parents=True, exist_ok=True)

            data = {"corpus": self.bm25_corpus, "documents": self.bm25_documents}

            with open(corpus_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"BM25 코퍼스가 저장되었습니다: {corpus_path}")

        except Exception as e:
            logger.error(f"BM25 코퍼스 저장 중 오류 발생: {e}")

    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", text)

        # 특수 문자 정리
        text = re.sub(r"[^\w\s가-힣]", " ", text)

        # 연속된 공백 제거
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _tokenize_korean(self, text: str) -> list[str]:
        """한국어 토큰화 (간단한 형태소 분석)"""
        # 공백으로 분리
        tokens = text.split()

        # 2글자 이상인 토큰만 유지
        tokens = [token for token in tokens if len(token) >= 2]

        return tokens

    def add_documents_from_database(self) -> bool:
        """데이터베이스에서 문서 추가"""
        try:
            # docs 테이블에서 문서 조회
            query = "SELECT * FROM docs WHERE content_text IS NOT NULL"
            result = self.db_manager.execute_query(query)

            if result is None or result.empty:
                logger.warning("데이터베이스에 문서가 없습니다.")
                return False

            documents = []
            corpus_tokens = []

            for _, row in result.iterrows():
                # 문서 객체 생성
                doc_text = self._preprocess_text(str(row["content_text"]))
                if len(doc_text) < 50:  # 너무 짧은 문서 제외
                    continue

                doc = Document(
                    text=doc_text,
                    metadata={
                        "doc_id": row["doc_id"],
                        "title": row["title"],
                        "source": row["source"],
                        "url": row["url"],
                        "published_date": (
                            str(row["published_date"])
                            if pd.notna(row["published_date"])
                            else None
                        ),
                    },
                )
                documents.append(doc)

                # BM25용 토큰화
                tokens = self._tokenize_korean(doc_text)
                corpus_tokens.append(tokens)

            if not documents:
                logger.warning("처리할 문서가 없습니다.")
                return False

            # 벡터 인덱스에 문서 추가
            self.vector_index.insert(documents)

            # BM25 코퍼스 업데이트
            self.bm25_corpus.extend(corpus_tokens)
            self.bm25_documents.extend([doc.text for doc in documents])

            # BM25 인덱스 재생성
            if self.bm25_corpus:
                self.bm25 = BM25Okapi(self.bm25_corpus)

            # BM25 코퍼스 저장
            self._save_bm25_corpus()

            logger.info(f"{len(documents)}개 문서가 추가되었습니다.")
            return True

        except Exception as e:
            logger.error(f"데이터베이스 문서 추가 중 오류 발생: {e}")
            return False

    def add_documents_from_pdf(self, pdf_path: str) -> bool:
        """PDF 파일에서 문서 추가"""
        try:
            # PDF 파싱 (간단한 구현)
            # 실제로는 PyPDF2, pdfplumber 등을 사용해야 함
            logger.info(f"PDF 문서 추가 기능은 향후 구현 예정: {pdf_path}")
            return False

        except Exception as e:
            logger.error(f"PDF 문서 추가 중 오류 발생: {e}")
            return False

    def vector_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """벡터 검색"""
        try:
            if not self.vector_index:
                logger.error("벡터 인덱스가 초기화되지 않았습니다.")
                return []

            # 쿼리 엔진 생성
            query_engine = self.vector_index.as_query_engine(
                similarity_top_k=top_k, response_mode="no_text"
            )

            # 검색 실행
            response = query_engine.query(query)

            # 결과 파싱
            results = []
            for node in response.source_nodes:
                results.append(
                    {
                        "text": node.text,
                        "metadata": node.metadata,
                        "score": node.score,
                        "search_type": "vector",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"벡터 검색 중 오류 발생: {e}")
            return []

    def bm25_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """BM25 검색"""
        try:
            if not self.bm25:
                logger.error("BM25 인덱스가 초기화되지 않았습니다.")
                return []

            # 쿼리 토큰화
            query_tokens = self._tokenize_korean(query)
            if not query_tokens:
                return []

            # BM25 점수 계산
            scores = self.bm25.get_scores(query_tokens)

            # 상위 k개 결과 선택
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # 점수가 0보다 큰 경우만
                    results.append(
                        {
                            "text": self.bm25_documents[idx],
                            "score": float(scores[idx]),
                            "search_type": "bm25",
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"BM25 검색 중 오류 발생: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """하이브리드 검색 (벡터 + BM25)"""
        try:
            # 벡터 검색
            vector_results = self.vector_search(query, top_k * 2)

            # BM25 검색
            bm25_results = self.bm25_search(query, top_k * 2)

            # 결과 통합
            combined_results = {}

            # 벡터 검색 결과 추가
            for result in vector_results:
                text_hash = hash(result["text"])
                if text_hash not in combined_results:
                    combined_results[text_hash] = {
                        "text": result["text"],
                        "metadata": result.get("metadata", {}),
                        "vector_score": result["score"],
                        "bm25_score": 0.0,
                        "combined_score": 0.0,
                    }
                else:
                    combined_results[text_hash]["vector_score"] = result["score"]

            # BM25 검색 결과 추가
            for result in bm25_results:
                text_hash = hash(result["text"])
                if text_hash not in combined_results:
                    combined_results[text_hash] = {
                        "text": result["text"],
                        "metadata": {},
                        "vector_score": 0.0,
                        "bm25_score": result["score"],
                        "combined_score": 0.0,
                    }
                else:
                    combined_results[text_hash]["bm25_score"] = result["score"]

            # 점수 정규화 및 결합
            vector_scores = [
                r["vector_score"]
                for r in combined_results.values()
                if r["vector_score"] > 0
            ]
            bm25_scores = [
                r["bm25_score"]
                for r in combined_results.values()
                if r["bm25_score"] > 0
            ]

            max_vector_score = max(vector_scores) if vector_scores else 1.0
            max_bm25_score = max(bm25_scores) if bm25_scores else 1.0

            for result in combined_results.values():
                # 점수 정규화
                norm_vector_score = (
                    result["vector_score"] / max_vector_score
                    if max_vector_score > 0
                    else 0
                )
                norm_bm25_score = (
                    result["bm25_score"] / max_bm25_score if max_bm25_score > 0 else 0
                )

                # 결합 점수 계산
                result["combined_score"] = (
                    vector_weight * norm_vector_score + bm25_weight * norm_bm25_score
                )

            # 결합 점수로 정렬
            sorted_results = sorted(
                combined_results.values(),
                key=lambda x: x["combined_score"],
                reverse=True,
            )

            # 상위 k개 반환
            final_results = []
            for result in sorted_results[:top_k]:
                final_results.append(
                    {
                        "text": result["text"],
                        "metadata": result["metadata"],
                        "vector_score": result["vector_score"],
                        "bm25_score": result["bm25_score"],
                        "combined_score": result["combined_score"],
                        "search_type": "hybrid",
                    }
                )

            return final_results

        except Exception as e:
            logger.error(f"하이브리드 검색 중 오류 발생: {e}")
            return []

    def search(
        self, query: str, search_type: str = "hybrid", top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        문서 검색

        Args:
            query: 검색 쿼리
            search_type: 검색 유형 ("vector", "bm25", "hybrid")
            top_k: 반환할 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            if search_type == "vector":
                return self.vector_search(query, top_k)
            elif search_type == "bm25":
                return self.bm25_search(query, top_k)
            elif search_type == "hybrid":
                return self.hybrid_search(query, top_k)
            else:
                logger.error(f"지원하지 않는 검색 유형: {search_type}")
                return []

        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return []

    def get_document_stats(self) -> dict[str, Any]:
        """문서 통계 정보 조회"""
        try:
            stats = {
                "total_documents": len(self.bm25_documents),
                "vector_store_initialized": self.vector_index is not None,
                "bm25_initialized": self.bm25 is not None,
                "corpus_size": len(self.bm25_corpus),
            }

            # 데이터베이스 문서 수
            query = "SELECT COUNT(*) as count FROM docs WHERE content_text IS NOT NULL"
            result = self.db_manager.execute_query(query)
            if result is not None and not result.empty:
                stats["database_documents"] = result.iloc[0]["count"]

            return stats

        except Exception as e:
            logger.error(f"문서 통계 조회 중 오류 발생: {e}")
            return {}

    def clear_indexes(self) -> bool:
        """인덱스 초기화"""
        try:
            # 벡터 스토어 초기화
            if self.chroma_client:
                try:
                    self.chroma_client.delete_collection("seoul_documents")
                except:
                    pass
                self._initialize_vector_store()

            # BM25 초기화
            self.bm25_corpus = []
            self.bm25_documents = []
            self.bm25 = None
            self._save_bm25_corpus()

            logger.info("모든 인덱스가 초기화되었습니다.")
            return True

        except Exception as e:
            logger.error(f"인덱스 초기화 중 오류 발생: {e}")
            return False
