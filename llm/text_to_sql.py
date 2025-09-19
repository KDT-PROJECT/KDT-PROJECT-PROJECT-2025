"""
Text-to-SQL service module
LlamaIndex NL->SQL conversion implementation according to tech-stack.mdc rules
"""

import logging
from typing import Any

from llama_index.core import SQLDatabase
from llama_index.core.indices.struct_store.sql_query import NLSQLTableQueryEngine
from llama_index.core.objects import SQLTableSchema
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

from config import get_db_config, get_llm_config, get_rag_config
from utils.guards import get_sql_guard

logger = logging.getLogger(__name__)


class TextToSQLService:
    """
    Service for converting natural language to SQL queries
    Implemented using LlamaIndex and HuggingFace LLM
    """

    def __init__(self):
        """Initialize Text-to-SQL service"""
        try:
            # Load configurations
            self.llm_config = get_llm_config()
            self.rag_config = get_rag_config()
            self.db_config = get_db_config()

            # Initialize SQL guard
            self.sql_guard = get_sql_guard()

            # Initialize LLM
            self.llm = self._initialize_llm()

            # Initialize embedding model
            self.embedding_model = self._initialize_embedding()

            # Initialize SQL database
            self.sql_database = self._initialize_sql_database()

            # Initialize query engine
            self.query_engine = self._initialize_query_engine()

            logger.info("Text-to-SQL service initialization completed")

        except Exception as e:
            logger.error(f"Text-to-SQL service initialization failed: {e}")
            raise

    def _initialize_llm(self) -> HuggingFaceLLM:
        """Initialize HuggingFace LLM"""
        try:
            llm = HuggingFaceLLM(
                model_name=self.llm_config.LLM_MODEL,
                tokenizer_name=self.llm_config.LLM_MODEL,
                context_window=2048,
                max_new_tokens=512,
                temperature=self.llm_config.LLM_TEMPERATURE,
                device_map="auto",
            )
            logger.info(f"HuggingFace LLM initialized: {self.llm_config.LLM_MODEL}")
            return llm
        except Exception as e:
            logger.error(f"HuggingFace LLM initialization failed: {e}")
            raise

    def _initialize_embedding(self) -> HuggingFaceEmbedding:
        """Initialize HuggingFace embedding model"""
        try:
            embedding = HuggingFaceEmbedding(
                model_name=self.rag_config.EMBEDDING_MODEL, device="cpu"
            )
            logger.info(
                f"HuggingFace embedding model initialized: {self.rag_config.EMBEDDING_MODEL}"
            )
            return embedding
        except Exception as e:
            logger.error(f"HuggingFace embedding model initialization failed: {e}")
            raise

    def _initialize_sql_database(self) -> SQLDatabase:
        """Initialize SQL database"""
        try:
            connection_string = self.db_config.get_connection_string()
            sql_database = SQLDatabase.from_uri(connection_string)
            logger.info("SQL database initialized")
            return sql_database
        except Exception as e:
            logger.error(f"SQL database initialization failed: {e}")
            raise

    def _initialize_query_engine(self) -> NLSQLTableQueryEngine:
        """Initialize query engine"""
        try:
            # Create SQL table objects
            sql_tables = [
                SQLTableSchema(
                    table_name="regions",
                    context_str="Region information table with region_id, region_name, region_code, district columns",
                ),
                SQLTableSchema(
                    table_name="industries",
                    context_str="Industry information table with industry_id, industry_name, industry_code, category columns",
                ),
                SQLTableSchema(
                    table_name="sales_2024",
                    context_str="2024 sales data table with region_id, industry_id, date, sales_amount, transaction_count, avg_transaction_amount columns",
                ),
            ]

            # Create query engine with HuggingFace embedding model
            query_engine = NLSQLTableQueryEngine(
                sql_database=self.sql_database,
                tables=sql_tables,
                llm=self.llm,
                embed_model=self.embedding_model,
                verbose=True,
            )

            logger.info("Query engine initialized")
            return query_engine

        except Exception as e:
            logger.error(f"Query engine initialization failed: {e}")
            raise

    def generate_sql_query(
        self,
        natural_language: str,
        context: dict[str, Any] | None = None,
        examples: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int = 3,
    ) -> str | None:
        """
        Convert natural language to SQL query

        Args:
            natural_language: Natural language query
            context: Additional context information
            examples: List of example queries
            temperature: LLM temperature setting
            max_tokens: Maximum token count
            timeout: Timeout setting
            max_retries: Maximum retry count

        Returns:
            str: Generated SQL query or None (on failure)
        """
        try:
            logger.info(f"SQL query generation started: {natural_language[:100]}...")

            # Input validation
            if not natural_language or not natural_language.strip():
                logger.warning("Empty natural language query")
                return None

            # Add context to natural language if provided
            if context:
                context_str = " ".join([f"{k}: {v}" for k, v in context.items()])
                natural_language = f"{natural_language} (context: {context_str})"

            # Add examples to natural language if provided
            if examples:
                examples_str = " ".join(examples)
                natural_language = f"{natural_language} (examples: {examples_str})"

            # Update LLM settings
            if temperature is not None:
                self.llm.temperature = temperature
            if max_tokens is not None:
                self.llm.max_new_tokens = max_tokens

            # Retry logic
            for attempt in range(max_retries + 1):
                try:
                    # Generate SQL query
                    response = self.query_engine.query(natural_language)

                    if response and hasattr(response, "response"):
                        sql_query = response.response

                        # Validate SQL query
                        if self.validate_sql_query(sql_query):
                            # Sanitize SQL query
                            sanitized_query = self.sanitize_sql_query(sql_query)
                            logger.info(
                                f"SQL query generation successful: {sanitized_query[:100]}..."
                            )
                            return sanitized_query
                        else:
                            logger.warning(
                                f"Generated SQL query failed security validation: {sql_query}"
                            )
                            if attempt < max_retries:
                                continue
                            else:
                                return None
                    else:
                        logger.warning("LLM response is empty")
                        if attempt < max_retries:
                            continue
                        else:
                            return None

                except Exception as e:
                    logger.error(
                        f"SQL query generation attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < max_retries:
                        continue
                    else:
                        return None

            return None

        except Exception as e:
            logger.error(f"Unexpected error during SQL query generation: {e}")
            return None

    def validate_sql_query(self, sql_query: str) -> bool:
        """
        Validate SQL query security

        Args:
            sql_query: SQL query to validate

        Returns:
            bool: Validation result
        """
        try:
            return self.sql_guard.validate_query(sql_query)
        except Exception as e:
            logger.error(f"Error during SQL query validation: {e}")
            return False

    def sanitize_sql_query(self, sql_query: str) -> str:
        """
        Sanitize and secure SQL query

        Args:
            sql_query: SQL query to sanitize

        Returns:
            str: Sanitized SQL query
        """
        try:
            return self.sql_guard.sanitize_query(sql_query)
        except Exception as e:
            logger.error(f"Error during SQL query sanitization: {e}")
            return sql_query

    def get_schema_info(self) -> dict[str, Any]:
        """
        Get database schema information

        Returns:
            Dict[str, Any]: Schema information
        """
        try:
            schema_info = {"tables": [], "columns": {}, "relationships": []}

            # Get table list
            tables = self.sql_database.get_usable_table_names()
            schema_info["tables"] = tables

            # Get column information for each table
            for table in tables:
                try:
                    columns = self.sql_database.get_single_table_info(table)
                    schema_info["columns"][table] = columns
                except Exception as e:
                    logger.warning(
                        f"Failed to get column information for table {table}: {e}"
                    )
                    schema_info["columns"][table] = []

            logger.info(f"Schema information retrieved: {len(tables)} tables")
            return schema_info

        except Exception as e:
            logger.error(f"Error during schema information retrieval: {e}")
            return {"tables": [], "columns": {}, "relationships": []}

    def get_table_info(self, table_name: str) -> str | None:
        """
        Get detailed information for specific table

        Args:
            table_name: Table name

        Returns:
            str: Table information or None
        """
        try:
            table_info = self.sql_database.get_single_table_info(table_name)
            logger.info(f"Table {table_name} information retrieved")
            return table_info
        except Exception as e:
            logger.error(f"Failed to get table {table_name} information: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            bool: Connection success
        """
        try:
            # Test connection with simple query
            result = self.sql_database.run_sql("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_available_tables(self) -> list[str]:
        """
        Get list of available tables

        Returns:
            List[str]: Table list
        """
        try:
            tables = self.sql_database.get_usable_table_names()
            logger.info(f"Available tables retrieved: {len(tables)} tables")
            return tables
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []

    def get_query_metadata(self, sql_query: str) -> dict[str, Any]:
        """
        Get SQL query metadata

        Args:
            sql_query: SQL query

        Returns:
            Dict[str, Any]: Query metadata
        """
        try:
            return self.sql_guard.get_query_metadata(sql_query)
        except Exception as e:
            logger.error(f"Error during query metadata retrieval: {e}")
            return {}


# Global Text-to-SQL service instance
text_to_sql_service = None


def get_text_to_sql_service() -> TextToSQLService:
    """Get Text-to-SQL service instance"""
    global text_to_sql_service
    if text_to_sql_service is None:
        text_to_sql_service = TextToSQLService()
    return text_to_sql_service
