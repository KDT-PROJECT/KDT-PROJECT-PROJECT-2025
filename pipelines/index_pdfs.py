"""
PDF Indexing Pipeline for Seoul Commercial Analysis System
This module handles PDF parsing, chunking, embedding, and vector index creation.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any

# Vector store imports
import chromadb
import fitz  # PyMuPDF

# Text processing imports
import nltk

# PDF processing imports
import PyPDF2
from chromadb.config import Settings

# Embedding imports
# LlamaIndex imports
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from pdfplumber import PDF

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFIndexer:
    """Handles PDF indexing for the Seoul Commercial Analysis System."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the PDF indexer.

        Args:
            config: Configuration dictionary containing:
                - vector_store_config: Vector store configuration
                - embedding_config: Embedding model configuration
                - chunking_config: Text chunking configuration
                - index_path: Path to store the index
        """
        self.config = config
        self.vector_store_config = config.get("vector_store_config", {})
        self.embedding_config = config.get("embedding_config", {})
        self.chunking_config = config.get("chunking_config", {})
        self.index_path = config.get("index_path", "./models/artifacts/vector_index")

        self.embedding_model = None
        self.vector_store = None
        self.index = None

        # Initialize NLTK
        self._initialize_nltk()

        # Initialize components
        self._initialize_embedding_model()
        self._initialize_vector_store()
        self._initialize_index()

    def _initialize_nltk(self):
        """Initialize NLTK components."""
        try:
            # Download required NLTK data
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)

            # Get stopwords
            self.stop_words = set(stopwords.words("english"))

            # Add Korean stopwords if available
            try:
                korean_stopwords = set(stopwords.words("korean"))
                self.stop_words.update(korean_stopwords)
            except:
                logger.warning("Korean stopwords not available")

            logger.info("NLTK initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing NLTK: {e}")
            raise

    def _initialize_embedding_model(self):
        """Initialize the embedding model."""
        try:
            model_name = self.embedding_config.get(
                "model_name", "sentence-transformers/all-MiniLM-L6-v2"
            )
            device = self.embedding_config.get("device", "cpu")

            self.embedding_model = HuggingFaceEmbedding(
                model_name=model_name, device=device
            )

            logger.info(f"Embedding model initialized: {model_name}")

        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            raise

    def _initialize_vector_store(self):
        """Initialize the vector store."""
        try:
            # Create index directory if it doesn't exist
            os.makedirs(self.index_path, exist_ok=True)

            # Initialize ChromaDB
            chroma_client = chromadb.PersistentClient(
                path=self.index_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # Create or get collection
            collection_name = self.vector_store_config.get(
                "collection_name", "seoul_commercial_docs"
            )
            collection = chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Seoul Commercial Analysis Documents"},
            )

            # Create ChromaVectorStore
            self.vector_store = ChromaVectorStore(chroma_collection=collection)

            logger.info(f"Vector store initialized: {collection_name}")

        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise

    def _initialize_index(self):
        """Initialize the vector index."""
        try:
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )

            # Create or load index
            if os.path.exists(os.path.join(self.index_path, "index.json")):
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store, storage_context=storage_context
                )
                logger.info("Loaded existing vector index")
            else:
                # Create new index
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store, storage_context=storage_context
                )
                logger.info("Created new vector index")

        except Exception as e:
            logger.error(f"Error initializing index: {e}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> dict[str, Any]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict containing extracted text and metadata
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # Try multiple PDF extraction methods
            text_content = ""
            metadata = {
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "file_size": os.path.getsize(pdf_path),
                "extraction_method": None,
                "page_count": 0,
                "extraction_timestamp": datetime.now().isoformat(),
            }

            # Method 1: PyMuPDF (fitz)
            try:
                doc = fitz.open(pdf_path)
                text_content = ""
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_content += page.get_text()

                metadata["extraction_method"] = "PyMuPDF"
                metadata["page_count"] = doc.page_count
                doc.close()

                if text_content.strip():
                    logger.info(
                        f"Successfully extracted text using PyMuPDF: {len(text_content)} characters"
                    )
                    return {"text": text_content, "metadata": metadata}

            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")

            # Method 2: pdfplumber
            try:
                with PDF(pdf_path) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""

                    metadata["extraction_method"] = "pdfplumber"
                    metadata["page_count"] = len(pdf.pages)

                    if text_content.strip():
                        logger.info(
                            f"Successfully extracted text using pdfplumber: {len(text_content)} characters"
                        )
                        return {"text": text_content, "metadata": metadata}

            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")

            # Method 3: PyPDF2
            try:
                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()

                    metadata["extraction_method"] = "PyPDF2"
                    metadata["page_count"] = len(pdf_reader.pages)

                    if text_content.strip():
                        logger.info(
                            f"Successfully extracted text using PyPDF2: {len(text_content)} characters"
                        )
                        return {"text": text_content, "metadata": metadata}

            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

            # If all methods fail
            raise Exception("All PDF extraction methods failed")

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess extracted text.

        Args:
            text: Raw text content

        Returns:
            Preprocessed text
        """
        try:
            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text)

            # Remove special characters but keep Korean characters
            text = re.sub(r"[^\w\s가-힣]", " ", text)

            # Remove multiple spaces
            text = re.sub(r"\s+", " ", text)

            # Strip leading/trailing whitespace
            text = text.strip()

            return text

        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text

    def chunk_text(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Chunk text into smaller pieces for indexing.

        Args:
            text: Text content to chunk
            metadata: Document metadata

        Returns:
            List of text chunks with metadata
        """
        try:
            # Get chunking parameters
            chunk_size = self.chunking_config.get("chunk_size", 1000)
            chunk_overlap = self.chunking_config.get("chunk_overlap", 200)

            # Preprocess text
            processed_text = self.preprocess_text(text)

            # Split into sentences
            sentences = sent_tokenize(processed_text)

            # Create chunks
            chunks = []
            current_chunk = ""
            current_length = 0
            chunk_id = 0

            for sentence in sentences:
                sentence_length = len(sentence)

                # If adding this sentence would exceed chunk size, save current chunk
                if current_length + sentence_length > chunk_size and current_chunk:
                    chunks.append(
                        {
                            "id": f"{metadata['file_name']}_chunk_{chunk_id}",
                            "text": current_chunk.strip(),
                            "metadata": {
                                **metadata,
                                "chunk_id": chunk_id,
                                "chunk_length": current_length,
                                "chunk_type": "text",
                            },
                        }
                    )

                    # Start new chunk with overlap
                    overlap_text = (
                        current_chunk[-chunk_overlap:]
                        if current_length > chunk_overlap
                        else current_chunk
                    )
                    current_chunk = overlap_text + " " + sentence
                    current_length = len(current_chunk)
                    chunk_id += 1
                else:
                    current_chunk += " " + sentence
                    current_length += sentence_length

            # Add the last chunk
            if current_chunk.strip():
                chunks.append(
                    {
                        "id": f"{metadata['file_name']}_chunk_{chunk_id}",
                        "text": current_chunk.strip(),
                        "metadata": {
                            **metadata,
                            "chunk_id": chunk_id,
                            "chunk_length": current_length,
                            "chunk_type": "text",
                        },
                    }
                )

            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return []

    def create_embeddings(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Create embeddings for text chunks.

        Args:
            chunks: List of text chunks

        Returns:
            List of chunks with embeddings
        """
        try:
            # Extract texts for embedding
            texts = [chunk["text"] for chunk in chunks]

            # Create embeddings
            embeddings = self.embedding_model.get_text_embedding_batch(texts)

            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i]
                chunk["metadata"]["embedding_dimension"] = len(embeddings[i])
                chunk["metadata"]["embedding_timestamp"] = datetime.now().isoformat()

            logger.info(f"Created embeddings for {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return chunks

    def index_chunks(self, chunks: list[dict[str, Any]]) -> bool:
        """
        Index text chunks in the vector store.

        Args:
            chunks: List of chunks to index

        Returns:
            bool: True if indexing successful, False otherwise
        """
        try:
            # Create LlamaIndex documents
            documents = []
            for chunk in chunks:
                doc = Document(
                    text=chunk["text"], metadata=chunk["metadata"], id_=chunk["id"]
                )
                documents.append(doc)

            # Add documents to index
            self.index.insert(documents)

            # Save index
            self.index.storage_context.persist(persist_dir=self.index_path)

            logger.info(f"Successfully indexed {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error indexing chunks: {e}")
            return False

    def index_pdf_file(self, pdf_path: str) -> dict[str, Any]:
        """
        Index a single PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict containing indexing results
        """
        try:
            # Extract text
            extraction_result = self.extract_text_from_pdf(pdf_path)
            text = extraction_result["text"]
            metadata = extraction_result["metadata"]

            if not text.strip():
                return {
                    "status": "error",
                    "message": "No text extracted from PDF",
                    "file_path": pdf_path,
                }

            # Chunk text
            chunks = self.chunk_text(text, metadata)

            if not chunks:
                return {
                    "status": "error",
                    "message": "No chunks created from text",
                    "file_path": pdf_path,
                }

            # Create embeddings
            chunks_with_embeddings = self.create_embeddings(chunks)

            # Index chunks
            indexing_success = self.index_chunks(chunks_with_embeddings)

            if indexing_success:
                return {
                    "status": "success",
                    "message": f"Successfully indexed PDF: {pdf_path}",
                    "file_path": pdf_path,
                    "chunks_created": len(chunks),
                    "metadata": metadata,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to index chunks",
                    "file_path": pdf_path,
                }

        except Exception as e:
            logger.error(f"Error indexing PDF file: {e}")
            return {"status": "error", "message": str(e), "file_path": pdf_path}

    def index_pdf_directory(self, directory_path: str) -> dict[str, Any]:
        """
        Index all PDF files in a directory.

        Args:
            directory_path: Path to the directory containing PDF files

        Returns:
            Dict containing indexing results
        """
        try:
            if not os.path.exists(directory_path):
                return {
                    "status": "error",
                    "message": f"Directory not found: {directory_path}",
                }

            # Find all PDF files
            pdf_files = []
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, file))

            if not pdf_files:
                return {"status": "error", "message": "No PDF files found in directory"}

            # Index each PDF file
            results = []
            successful_indexes = 0
            failed_indexes = 0

            for pdf_file in pdf_files:
                result = self.index_pdf_file(pdf_file)
                results.append(result)

                if result["status"] == "success":
                    successful_indexes += 1
                else:
                    failed_indexes += 1

            return {
                "status": "success" if successful_indexes > 0 else "error",
                "message": f"Indexed {successful_indexes} PDF files successfully, {failed_indexes} failed",
                "total_files": len(pdf_files),
                "successful_indexes": successful_indexes,
                "failed_indexes": failed_indexes,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error indexing PDF directory: {e}")
            return {"status": "error", "message": str(e)}

    def get_index_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector index.

        Returns:
            Dict containing index statistics
        """
        try:
            # Get collection stats
            collection = self.vector_store._collection
            count = collection.count()

            # Get metadata
            stats = {
                "total_documents": count,
                "index_path": self.index_path,
                "embedding_model": self.embedding_config.get("model_name", "unknown"),
                "chunk_size": self.chunking_config.get("chunk_size", 1000),
                "chunk_overlap": self.chunking_config.get("chunk_overlap", 200),
                "last_updated": datetime.now().isoformat(),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}


def index_pdfs(pdf_path: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Index PDF files for the Seoul Commercial Analysis System.

    Args:
        pdf_path: Path to PDF file or directory
        config: Configuration dictionary

    Returns:
        Dict containing indexing results
    """
    try:
        indexer = PDFIndexer(config)

        if os.path.isfile(pdf_path):
            return indexer.index_pdf_file(pdf_path)
        elif os.path.isdir(pdf_path):
            return indexer.index_pdf_directory(pdf_path)
        else:
            return {"status": "error", "message": f"Path not found: {pdf_path}"}

    except Exception as e:
        logger.error(f"Error in index_pdfs: {e}")
        return {"status": "error", "message": str(e)}


def main():
    """Main function for testing the PDF indexer."""
    # Example configuration
    config = {
        "vector_store_config": {"collection_name": "seoul_commercial_docs"},
        "embedding_config": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",
        },
        "chunking_config": {"chunk_size": 1000, "chunk_overlap": 200},
        "index_path": "./models/artifacts/vector_index",
    }

    # Test PDF indexing
    pdf_path = "data/pdfs"  # Directory containing PDF files

    result = index_pdfs(pdf_path, config)
    print(f"Indexing result: {result}")

    # Get index stats
    indexer = PDFIndexer(config)
    stats = indexer.get_index_stats()
    print(f"Index stats: {stats}")


if __name__ == "__main__":
    main()
