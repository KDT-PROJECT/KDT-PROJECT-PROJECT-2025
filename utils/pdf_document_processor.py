"""PDF Document Processing and Indexing System"""

import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pickle
import json

import PyPDF2
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import faiss

class PDFDocumentProcessor:
    """Process and index PDF documents for semantic search"""

    def __init__(self, pdf_folder: str = "data/pdf",
                 index_path: str = "models/artifacts/pdf_index",
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize PDF processor

        Args:
            pdf_folder: Path to folder containing PDF files
            index_path: Path to save/load index files
            model_name: Name of sentence transformer model for embeddings
        """
        self.pdf_folder = Path(pdf_folder)
        self.index_path = Path(index_path)
        self.model_name = model_name

        # Create index directory if it doesn't exist
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Initialize sentence transformer model
        self.embedding_model = SentenceTransformer(model_name)

        # Storage for document chunks and metadata
        self.document_chunks = []
        self.document_metadata = []
        self.embeddings = None
        self.faiss_index = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Load existing index if available
        self._load_index()

    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF file using PyMuPDF for better Korean support

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # Use PyMuPDF (fitz) for better text extraction
            doc = fitz.open(str(pdf_path))
            text = ""
            metadata = {
                "filename": pdf_path.name,
                "filepath": str(pdf_path),
                "page_count": len(doc),
                "file_size": pdf_path.stat().st_size,
                "last_modified": pdf_path.stat().st_mtime
            }

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text.strip():
                    text += f"\n--- 페이지 {page_num + 1} ---\n{page_text}\n"

            doc.close()

            # Clean and normalize text
            text = self._clean_text(text)

            return text, metadata

        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            # Fallback to PyPDF2
            return self._extract_with_pypdf2(pdf_path)

    def _extract_with_pypdf2(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction method using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- 페이지 {page_num + 1} ---\n{page_text}\n"

                metadata = {
                    "filename": pdf_path.name,
                    "filepath": str(pdf_path),
                    "page_count": len(reader.pages),
                    "file_size": pdf_path.stat().st_size,
                    "last_modified": pdf_path.stat().st_mtime
                }

                text = self._clean_text(text)
                return text, metadata

        except Exception as e:
            self.logger.error(f"Error with PyPDF2 extraction from {pdf_path}: {e}")
            return "", {"filename": pdf_path.name, "error": str(e)}

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Remove special characters that might interfere with processing
        import re
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)

        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = 500,
                   overlap: int = 50) -> List[str]:
        """
        Split text into chunks for better search granularity

        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk (in characters)
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Find the last sentence end within the chunk
                for i in range(end - 1, start + chunk_size // 2, -1):
                    if text[i] in '.!?。！？':
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start >= len(text):
                break

        return chunks

    def process_all_pdfs(self, force_reindex: bool = False) -> None:
        """
        Process all PDF files in the configured folder

        Args:
            force_reindex: If True, reprocess all files even if already indexed
        """
        if not self.pdf_folder.exists():
            self.logger.error(f"PDF folder {self.pdf_folder} does not exist")
            return

        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")

        # Clear existing data if force reindexing
        if force_reindex:
            self.document_chunks = []
            self.document_metadata = []
            self.embeddings = None
            self.faiss_index = None

        # Get existing file hashes to avoid reprocessing
        existing_hashes = self._get_existing_file_hashes()

        processed_count = 0
        for pdf_file in pdf_files:
            try:
                # Check if file needs processing
                file_hash = self._get_file_hash(pdf_file)
                if not force_reindex and file_hash in existing_hashes:
                    continue

                self.logger.info(f"Processing {pdf_file.name}...")

                # Extract text
                text, metadata = self.extract_text_from_pdf(pdf_file)

                if not text.strip():
                    self.logger.warning(f"No text extracted from {pdf_file.name}")
                    continue

                # Chunk text
                chunks = self.chunk_text(text)
                self.logger.info(f"Created {len(chunks)} chunks from {pdf_file.name}")

                # Add chunks to collection
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_id": i,
                        "chunk_text": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                        "file_hash": file_hash
                    })

                    self.document_chunks.append(chunk)
                    self.document_metadata.append(chunk_metadata)

                processed_count += 1

            except Exception as e:
                self.logger.error(f"Error processing {pdf_file}: {e}")

        self.logger.info(f"Processed {processed_count} new PDF files")

        # Generate embeddings and build index
        if self.document_chunks:
            self._build_embeddings_and_index()
            self._save_index()

    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file for change detection"""
        stat = file_path.stat()
        content = f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_existing_file_hashes(self) -> set:
        """Get hashes of already processed files"""
        hashes = set()
        for metadata in self.document_metadata:
            if "file_hash" in metadata:
                hashes.add(metadata["file_hash"])
        return hashes

    def _build_embeddings_and_index(self) -> None:
        """Generate embeddings and build FAISS index"""
        if not self.document_chunks:
            return

        self.logger.info("Generating embeddings for document chunks...")

        # Generate embeddings in batches for memory efficiency
        batch_size = 32
        all_embeddings = []

        for i in range(0, len(self.document_chunks), batch_size):
            batch = self.document_chunks[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch,
                convert_to_numpy=True,
                show_progress_bar=True if i == 0 else False
            )
            all_embeddings.extend(batch_embeddings)

        self.embeddings = np.array(all_embeddings).astype('float32')

        # Build FAISS index
        self.logger.info("Building FAISS index...")
        dimension = self.embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.faiss_index.add(self.embeddings)

        self.logger.info(f"Index built with {self.faiss_index.ntotal} vectors")

    def search(self, query: str, top_k: int = 10,
               min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks

        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of search results with metadata
        """
        if not self.faiss_index or not self.document_chunks:
            self.logger.warning("No index available. Please process PDFs first.")
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self.faiss_index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= min_score:
                result = {
                    "content": self.document_chunks[idx],
                    "score": float(score),
                    "metadata": self.document_metadata[idx]
                }
                results.append(result)

        return results

    def _save_index(self) -> None:
        """Save index and metadata to disk"""
        try:
            # Save FAISS index
            if self.faiss_index:
                faiss_path = self.index_path / "pdf_index.faiss"
                faiss.write_index(self.faiss_index, str(faiss_path))

            # Save document chunks and metadata
            data_path = self.index_path / "pdf_data.pkl"
            with open(data_path, 'wb') as f:
                pickle.dump({
                    "document_chunks": self.document_chunks,
                    "document_metadata": self.document_metadata,
                    "embeddings": self.embeddings
                }, f)

            # Save configuration
            config_path = self.index_path / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "model_name": self.model_name,
                    "pdf_folder": str(self.pdf_folder),
                    "total_chunks": len(self.document_chunks)
                }, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Index saved to {self.index_path}")

        except Exception as e:
            self.logger.error(f"Error saving index: {e}")

    def _load_index(self) -> None:
        """Load existing index from disk"""
        try:
            faiss_path = self.index_path / "pdf_index.faiss"
            data_path = self.index_path / "pdf_data.pkl"
            config_path = self.index_path / "config.json"

            if not all(p.exists() for p in [faiss_path, data_path, config_path]):
                self.logger.info("No existing index found. Will create new index.")
                return

            # Load FAISS index
            self.faiss_index = faiss.read_index(str(faiss_path))

            # Load document data
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.document_chunks = data["document_chunks"]
                self.document_metadata = data["document_metadata"]
                self.embeddings = data["embeddings"]

            # Load config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.logger.info(f"Loaded existing index with {len(self.document_chunks)} chunks")

        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            # Reset to empty state
            self.document_chunks = []
            self.document_metadata = []
            self.embeddings = None
            self.faiss_index = None

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        stats = {
            "total_chunks": len(self.document_chunks),
            "total_files": len(set(m.get("filename", "") for m in self.document_metadata)),
            "index_exists": self.faiss_index is not None,
            "model_name": self.model_name
        }

        if self.document_metadata:
            file_sizes = [m.get("file_size", 0) for m in self.document_metadata]
            stats["total_size_mb"] = sum(file_sizes) / (1024 * 1024)

        return stats

def get_pdf_processor() -> PDFDocumentProcessor:
    """Get configured PDF processor instance"""
    return PDFDocumentProcessor()

# For testing
if __name__ == "__main__":
    processor = PDFDocumentProcessor()
    processor.process_all_pdfs()

    # Test search
    results = processor.search("창업 지원 프로그램", top_k=5)
    print(f"Found {len(results)} results")
    for result in results:
        print(f"Score: {result['score']:.3f}")
        print(f"File: {result['metadata']['filename']}")
        print(f"Content: {result['content'][:200]}...")
        print("-" * 50)