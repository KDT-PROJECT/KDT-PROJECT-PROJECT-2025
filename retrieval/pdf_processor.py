"""
PDF 처리 모듈
PRD TASK3: PDF 파일 기반 RAG 시스템 구현
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF 처리 클래스"""
    
    def __init__(self, pdf_directory: str = "data/pdf"):
        """
        PDF 처리기 초기화
        
        Args:
            pdf_directory: PDF 파일 디렉토리 경로
        """
        self.pdf_directory = Path(pdf_directory)
        self.supported_formats = ['.pdf']
        
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        PyPDF2를 사용한 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            logger.info(f"PyPDF2 텍스트 추출 완료: {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"PyPDF2 텍스트 추출 실패: {str(e)}")
            return ""
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """
        PyMuPDF를 사용한 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
        """
        try:
            text = ""
            doc = fitz.open(pdf_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text() + "\n"
            doc.close()
            
            logger.info(f"PyMuPDF 텍스트 추출 완료: {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"PyMuPDF 텍스트 추출 실패: {str(e)}")
            return ""
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        pdfplumber를 사용한 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"pdfplumber 텍스트 추출 완료: {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"pdfplumber 텍스트 추출 실패: {str(e)}")
            return ""
    
    def extract_text(self, pdf_path: str) -> str:
        """
        PDF 텍스트 추출 (여러 방법 시도)
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
        """
        # 여러 방법으로 시도
        methods = [
            self.extract_text_pymupdf,
            self.extract_text_pdfplumber,
            self.extract_text_pypdf2
        ]
        
        for method in methods:
            try:
                text = method(pdf_path)
                if text and len(text.strip()) > 100:  # 최소 100자 이상
                    return text
            except Exception as e:
                logger.warning(f"텍스트 추출 방법 실패: {str(e)}")
                continue
        
        logger.error(f"모든 텍스트 추출 방법 실패: {pdf_path}")
        return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 원본 텍스트
            chunk_size: 청크 크기
            overlap: 겹치는 부분 크기
            
        Returns:
            청크 리스트
        """
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                # 문장 경계에서 자르기
                if end < len(text):
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    cut_point = max(last_period, last_newline)
                    if cut_point > start + chunk_size // 2:
                        chunk_text = text[start:start + cut_point + 1]
                        end = start + cut_point + 1
                
                chunks.append({
                    "text": chunk_text.strip(),
                    "start": start,
                    "end": end,
                    "length": len(chunk_text.strip())
                })
                
                start = end - overlap
                if start >= len(text):
                    break
            
            logger.info(f"텍스트 청킹 완료: {len(chunks)}개 청크")
            return chunks
            
        except Exception as e:
            logger.error(f"텍스트 청킹 실패: {str(e)}")
            return []
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일 처리
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            처리 결과 딕셔너리
        """
        try:
            if not os.path.exists(pdf_path):
                return {"status": "error", "message": "PDF 파일을 찾을 수 없습니다."}
            
            # 파일 정보
            file_name = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path)
            
            # 텍스트 추출
            text = self.extract_text(pdf_path)
            if not text:
                return {"status": "error", "message": "텍스트 추출에 실패했습니다."}
            
            # 청킹
            chunks = self.chunk_text(text)
            
            # 메타데이터 생성
            metadata = {
                "file_name": file_name,
                "file_path": pdf_path,
                "file_size": file_size,
                "text_length": len(text),
                "chunk_count": len(chunks),
                "processed_at": datetime.now().isoformat(),
                "content_hash": hashlib.md5(text.encode()).hexdigest()
            }
            
            result = {
                "status": "success",
                "metadata": metadata,
                "chunks": chunks,
                "full_text": text
            }
            
            logger.info(f"PDF 처리 완료: {file_name} -> {len(chunks)}개 청크")
            return result
            
        except Exception as e:
            logger.error(f"PDF 처리 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """
        디렉토리의 모든 PDF 파일 처리
        
        Returns:
            처리 결과 딕셔너리
        """
        try:
            if not self.pdf_directory.exists():
                return {"status": "error", "message": "PDF 디렉토리가 존재하지 않습니다."}
            
            pdf_files = list(self.pdf_directory.glob("*.pdf"))
            if not pdf_files:
                return {"status": "error", "message": "PDF 파일을 찾을 수 없습니다."}
            
            results = []
            total_chunks = 0
            
            for pdf_file in pdf_files:
                result = self.process_pdf(str(pdf_file))
                if result["status"] == "success":
                    results.append(result)
                    total_chunks += len(result["chunks"])
            
            return {
                "status": "success",
                "processed_files": len(results),
                "total_chunks": total_chunks,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"PDF 일괄 처리 실패: {str(e)}")
            return {"status": "error", "message": str(e)}

def process_pdf_file(pdf_path: str) -> Dict[str, Any]:
    """
    PDF 파일 처리 함수
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        처리 결과 딕셔너리
    """
    processor = PDFProcessor()
    return processor.process_pdf(pdf_path)

def process_all_pdfs(pdf_directory: str = "data/pdf") -> Dict[str, Any]:
    """
    모든 PDF 파일 처리 함수
    
    Args:
        pdf_directory: PDF 디렉토리 경로
        
    Returns:
        처리 결과 딕셔너리
    """
    processor = PDFProcessor(pdf_directory)
    return processor.process_all_pdfs()
