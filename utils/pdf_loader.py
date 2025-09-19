"""
PDF 로더 및 청킹 시스템
system-architecture.mdc 규칙에 따른 서울 창업정보 문서 처리
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# PDF 처리 라이브러리
try:
    import fitz  # PyMuPDF
    import PyPDF2
except ImportError as e:
    logging.warning(f"PDF 라이브러리 임포트 실패: {e}")

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """문서 청크 데이터 클래스"""

    text: str
    chunk_id: str
    page_number: int
    source_file: str
    metadata: dict[str, Any]
    start_char: int
    end_char: int


class PDFLoader:
    """PDF 문서 로더"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        PDF 로더 초기화

        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 겹침 크기 (문자 수)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_extensions = [".pdf"]

        logger.info(
            f"PDF 로더 초기화: chunk_size={chunk_size}, overlap={chunk_overlap}"
        )

    def load_documents(self, directory_path: str) -> list[DocumentChunk]:
        """
        디렉토리에서 PDF 문서들을 로드하고 청킹

        Args:
            directory_path: PDF 파일들이 있는 디렉토리 경로

        Returns:
            청크 리스트
        """
        chunks = []
        directory = Path(directory_path)

        if not directory.exists():
            logger.error(f"디렉토리가 존재하지 않습니다: {directory_path}")
            return chunks

        # PDF 파일 찾기
        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"발견된 PDF 파일: {len(pdf_files)}개")

        for pdf_file in pdf_files:
            try:
                file_chunks = self._load_pdf_file(pdf_file)
                chunks.extend(file_chunks)
                logger.info(
                    f"PDF 파일 처리 완료: {pdf_file.name} ({len(file_chunks)}개 청크)"
                )
            except Exception as e:
                logger.error(f"PDF 파일 처리 실패: {pdf_file.name} - {e}")

        logger.info(f"전체 문서 처리 완료: {len(chunks)}개 청크")
        return chunks

    def _load_pdf_file(self, pdf_path: Path) -> list[DocumentChunk]:
        """개별 PDF 파일 로드 및 청킹"""
        chunks = []

        try:
            # PyMuPDF로 PDF 열기
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()

                if text.strip():
                    # 페이지 텍스트 청킹
                    page_chunks = self._chunk_text(
                        text=text, source_file=pdf_path.name, page_number=page_num + 1
                    )
                    chunks.extend(page_chunks)

            doc.close()

        except Exception as e:
            logger.error(f"PDF 파일 로드 실패: {pdf_path} - {e}")
            # 폴백으로 PyPDF2 사용
            try:
                chunks = self._load_with_pypdf2(pdf_path)
            except Exception as e2:
                logger.error(f"PyPDF2로도 로드 실패: {pdf_path} - {e2}")

        return chunks

    def _load_with_pypdf2(self, pdf_path: Path) -> list[DocumentChunk]:
        """PyPDF2를 사용한 폴백 로드"""
        chunks = []

        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()

                if text.strip():
                    page_chunks = self._chunk_text(
                        text=text, source_file=pdf_path.name, page_number=page_num + 1
                    )
                    chunks.extend(page_chunks)

        return chunks

    def _chunk_text(
        self, text: str, source_file: str, page_number: int
    ) -> list[DocumentChunk]:
        """텍스트 청킹"""
        chunks = []

        # 텍스트 전처리
        cleaned_text = self._clean_text(text)

        if len(cleaned_text) <= self.chunk_size:
            # 청크 크기보다 작으면 전체를 하나의 청크로
            chunk = DocumentChunk(
                text=cleaned_text,
                chunk_id=f"{source_file}_p{page_number}_c0",
                page_number=page_number,
                source_file=source_file,
                metadata={"chunk_size": len(cleaned_text), "is_complete_page": True},
                start_char=0,
                end_char=len(cleaned_text),
            )
            chunks.append(chunk)
        else:
            # 청킹 수행
            start = 0
            chunk_index = 0

            while start < len(cleaned_text):
                end = min(start + self.chunk_size, len(cleaned_text))

                # 문장 경계에서 자르기 시도
                if end < len(cleaned_text):
                    # 마지막 문장 끝 찾기
                    last_sentence_end = cleaned_text.rfind(".", start, end)
                    if last_sentence_end > start + self.chunk_size // 2:
                        end = last_sentence_end + 1

                chunk_text = cleaned_text[start:end].strip()

                if chunk_text:
                    chunk = DocumentChunk(
                        text=chunk_text,
                        chunk_id=f"{source_file}_p{page_number}_c{chunk_index}",
                        page_number=page_number,
                        source_file=source_file,
                        metadata={
                            "chunk_size": len(chunk_text),
                            "chunk_index": chunk_index,
                            "is_complete_page": False,
                        },
                        start_char=start,
                        end_char=end,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                # 다음 청크 시작 위치 (겹침 고려)
                start = end - self.chunk_overlap
                if start >= len(cleaned_text):
                    break

        return chunks

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 불필요한 공백 제거
        text = re.sub(r"\s+", " ", text)

        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣.,!?;:()\[\]{}"\'-]', "", text)

        # 연속된 구두점 정리
        text = re.sub(r"[.]{2,}", "...", text)
        text = re.sub(r"[!]{2,}", "!!", text)
        text = re.sub(r"[?]{2,}", "??", text)

        return text.strip()

    def extract_metadata(self, pdf_path: Path) -> dict[str, Any]:
        """PDF 메타데이터 추출"""
        metadata = {
            "file_name": pdf_path.name,
            "file_size": pdf_path.stat().st_size,
            "file_path": str(pdf_path),
        }

        try:
            doc = fitz.open(pdf_path)
            pdf_metadata = doc.metadata

            metadata.update(
                {
                    "title": pdf_metadata.get("title", ""),
                    "author": pdf_metadata.get("author", ""),
                    "subject": pdf_metadata.get("subject", ""),
                    "creator": pdf_metadata.get("creator", ""),
                    "producer": pdf_metadata.get("producer", ""),
                    "creation_date": pdf_metadata.get("creationDate", ""),
                    "modification_date": pdf_metadata.get("modDate", ""),
                    "page_count": len(doc),
                }
            )

            doc.close()

        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {pdf_path} - {e}")

        return metadata


class DocumentProcessor:
    """문서 처리기"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """문서 처리기 초기화"""
        self.pdf_loader = PDFLoader(chunk_size, chunk_overlap)
        self.processed_documents = []

        logger.info("문서 처리기 초기화 완료")

    def process_directory(self, directory_path: str) -> list[dict[str, Any]]:
        """
        디렉토리 처리

        Args:
            directory_path: 처리할 디렉토리 경로

        Returns:
            처리된 문서 리스트
        """
        chunks = self.pdf_loader.load_documents(directory_path)

        # 청크를 문서 형태로 변환
        documents = []
        for chunk in chunks:
            document = {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": {
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_id,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    **chunk.metadata,
                },
            }
            documents.append(document)

        self.processed_documents.extend(documents)
        logger.info(f"문서 처리 완료: {len(documents)}개 문서")

        return documents

    def get_document_stats(self) -> dict[str, Any]:
        """문서 통계 반환"""
        if not self.processed_documents:
            return {"total_documents": 0}

        total_chars = sum(len(doc["text"]) for doc in self.processed_documents)
        avg_chunk_size = total_chars / len(self.processed_documents)

        # 파일별 통계
        file_stats = {}
        for doc in self.processed_documents:
            source_file = doc["metadata"]["source_file"]
            if source_file not in file_stats:
                file_stats[source_file] = 0
            file_stats[source_file] += 1

        return {
            "total_documents": len(self.processed_documents),
            "total_characters": total_chars,
            "average_chunk_size": avg_chunk_size,
            "files_processed": len(file_stats),
            "chunks_per_file": file_stats,
        }


# 전역 문서 처리기 인스턴스
_document_processor = None


def get_document_processor(
    chunk_size: int = 1000, chunk_overlap: int = 200
) -> DocumentProcessor:
    """문서 처리기 인스턴스 반환"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor(chunk_size, chunk_overlap)
    return _document_processor
