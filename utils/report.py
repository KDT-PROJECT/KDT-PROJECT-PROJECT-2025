"""
Report Synthesis Engine for Seoul Commercial Analysis System
This module generates comprehensive reports by combining SQL results and retrieved documents.
"""

import json
import logging
from datetime import datetime
from typing import Any

# Gemini imports
import google.generativeai as genai

# Text processing imports
import nltk

# LLM imports
from llama_index.llms.huggingface import HuggingFaceLLM
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportSynthesizer:
    """Synthesizes comprehensive reports from SQL results and retrieved documents."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the report synthesizer.

        Args:
            config: Configuration dictionary containing:
                - hf_llm_config: HuggingFace LLM configuration
                - gemini_config: Gemini API configuration
                - report_config: Report generation configuration
        """
        self.config = config
        self.hf_llm_config = config.get("hf_llm_config", {})
        self.gemini_config = config.get("gemini_config", {})
        self.report_config = config.get("report_config", {})

        self.hf_llm = None
        self.gemini_model = None

        self._initialize_models()
        self._initialize_nltk()

    def _initialize_models(self):
        """Initialize LLM models."""
        try:
            # Initialize HuggingFace LLM
            self.hf_llm = HuggingFaceLLM(
                model_name=self.hf_llm_config.get(
                    "model_name", "microsoft/DialoGPT-medium"
                ),
                tokenizer_name=self.hf_llm_config.get(
                    "tokenizer_name", "microsoft/DialoGPT-medium"
                ),
                context_window=self.hf_llm_config.get("context_window", 2048),
                max_new_tokens=self.hf_llm_config.get("max_new_tokens", 512),
                temperature=self.hf_llm_config.get("temperature", 0.7),
                device_map=self.hf_llm_config.get("device_map", "auto"),
                trust_remote_code=True,
            )

            # Initialize Gemini
            api_key = self.gemini_config.get("api_key")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name=self.gemini_config.get("model_name", "gemini-pro")
                )

            logger.info("LLM models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

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

    def _extract_key_insights(
        self, sql_results: list[dict[str, Any]], retrieved_docs: list[dict[str, Any]]
    ) -> list[str]:
        """
        Extract key insights from SQL results and retrieved documents.

        Args:
            sql_results: SQL query results
            retrieved_docs: Retrieved documents

        Returns:
            List of key insights
        """
        try:
            insights = []

            # Analyze SQL results
            if sql_results:
                # Extract numerical insights
                numerical_insights = self._extract_numerical_insights(sql_results)
                insights.extend(numerical_insights)

                # Extract trend insights
                trend_insights = self._extract_trend_insights(sql_results)
                insights.extend(trend_insights)

            # Analyze retrieved documents
            if retrieved_docs:
                # Extract document insights
                doc_insights = self._extract_document_insights(retrieved_docs)
                insights.extend(doc_insights)

            return insights

        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return []

    def _extract_numerical_insights(
        self, sql_results: list[dict[str, Any]]
    ) -> list[str]:
        """Extract numerical insights from SQL results."""
        try:
            insights = []

            if not sql_results:
                return insights

            # Find numerical columns
            numerical_columns = []
            for key in sql_results[0].keys():
                if any(
                    key.lower().contains(word)
                    for word in ["amount", "count", "total", "sum", "avg", "sales"]
                ):
                    numerical_columns.append(key)

            # Extract insights for each numerical column
            for column in numerical_columns:
                values = [row[column] for row in sql_results if row[column] is not None]
                if values:
                    max_val = max(values)
                    min_val = min(values)
                    avg_val = sum(values) / len(values)

                    insights.append(
                        f"{column} ranges from {min_val:,.2f} to {max_val:,.2f} with an average of {avg_val:,.2f}"
                    )

            return insights

        except Exception as e:
            logger.error(f"Error extracting numerical insights: {e}")
            return []

    def _extract_trend_insights(self, sql_results: list[dict[str, Any]]) -> list[str]:
        """Extract trend insights from SQL results."""
        try:
            insights = []

            if not sql_results:
                return insights

            # Look for time-based columns
            time_columns = []
            for key in sql_results[0].keys():
                if any(
                    word in key.lower() for word in ["year", "month", "date", "time"]
                ):
                    time_columns.append(key)

            # Analyze trends
            for column in time_columns:
                # Group by time and calculate totals
                time_groups = {}
                for row in sql_results:
                    time_val = row[column]
                    if time_val not in time_groups:
                        time_groups[time_val] = []
                    time_groups[time_val].append(row)

                # Calculate trend
                if len(time_groups) > 1:
                    sorted_times = sorted(time_groups.keys())
                    first_time = sorted_times[0]
                    last_time = sorted_times[-1]

                    first_count = len(time_groups[first_time])
                    last_count = len(time_groups[last_time])

                    if first_count > 0:
                        trend = (last_count - first_count) / first_count * 100
                        if trend > 0:
                            insights.append(
                                f"Data shows an increasing trend from {first_time} to {last_time} with {trend:.1f}% growth"
                            )
                        elif trend < 0:
                            insights.append(
                                f"Data shows a decreasing trend from {first_time} to {last_time} with {abs(trend):.1f}% decline"
                            )

            return insights

        except Exception as e:
            logger.error(f"Error extracting trend insights: {e}")
            return []

    def _extract_document_insights(
        self, retrieved_docs: list[dict[str, Any]]
    ) -> list[str]:
        """Extract insights from retrieved documents."""
        try:
            insights = []

            if not retrieved_docs:
                return insights

            # Extract key phrases and concepts
            all_text = " ".join([doc.get("text", "") for doc in retrieved_docs])

            # Tokenize and find important terms
            tokens = word_tokenize(all_text.lower())
            filtered_tokens = [
                token
                for token in tokens
                if token not in self.stop_words and len(token) > 3
            ]

            # Count term frequencies
            term_counts = {}
            for token in filtered_tokens:
                term_counts[token] = term_counts.get(token, 0) + 1

            # Get top terms
            top_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            # Create insights from top terms
            for term, count in top_terms:
                insights.append(
                    f"'{term}' appears {count} times in the retrieved documents, indicating its importance"
                )

            return insights

        except Exception as e:
            logger.error(f"Error extracting document insights: {e}")
            return []

    def _generate_hf_draft(
        self,
        sql_results: list[dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
        query: str,
    ) -> str:
        """
        Generate initial report draft using HuggingFace LLM.

        Args:
            sql_results: SQL query results
            retrieved_docs: Retrieved documents
            query: Original query

        Returns:
            Generated report draft
        """
        try:
            # Prepare context
            context = self._prepare_context(sql_results, retrieved_docs, query)

            # Create prompt
            prompt = f"""
            You are a business analyst specializing in Seoul commercial analysis. 
            Generate a comprehensive report based on the following data and context.
            
            Query: {query}
            
            Context:
            {context}
            
            Please generate a report that includes:
            1. Executive Summary
            2. Key Findings
            3. Data Analysis
            4. Insights and Recommendations
            5. Conclusion
            
            Make the report professional, data-driven, and actionable.
            """

            # Generate response
            response = self.hf_llm.complete(prompt)

            return response.text

        except Exception as e:
            logger.error(f"Error generating HF draft: {e}")
            return "Error generating report draft"

    def _prepare_context(
        self,
        sql_results: list[dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
        query: str,
    ) -> str:
        """Prepare context for report generation."""
        try:
            context_parts = []

            # Add query context
            context_parts.append(f"Original Query: {query}")

            # Add SQL results context
            if sql_results:
                context_parts.append(f"SQL Results ({len(sql_results)} rows):")
                for i, row in enumerate(sql_results[:5]):  # Limit to first 5 rows
                    context_parts.append(
                        f"Row {i+1}: {json.dumps(row, ensure_ascii=False)}"
                    )

            # Add retrieved documents context
            if retrieved_docs:
                context_parts.append(
                    f"Retrieved Documents ({len(retrieved_docs)} documents):"
                )
                for i, doc in enumerate(
                    retrieved_docs[:3]
                ):  # Limit to first 3 documents
                    text = doc.get("text", "")[:500]  # Limit text length
                    context_parts.append(f"Document {i+1}: {text}...")

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error preparing context: {e}")
            return "Error preparing context"

    def _enhance_with_gemini(self, draft: str, insights: list[str]) -> str:
        """
        Enhance report with Gemini for better insights and analysis.

        Args:
            draft: Initial report draft
            insights: Extracted insights

        Returns:
            Enhanced report
        """
        try:
            if not self.gemini_model:
                logger.warning("Gemini model not available, returning original draft")
                return draft

            # Prepare enhancement prompt
            prompt = f"""
            You are an expert business analyst. Please enhance the following report draft 
            with deeper insights, better analysis, and more actionable recommendations.
            
            Original Draft:
            {draft}
            
            Key Insights to Incorporate:
            {chr(10).join(insights)}
            
            Please provide an enhanced version that:
            1. Improves the analysis depth
            2. Adds more strategic insights
            3. Provides clearer recommendations
            4. Maintains professional tone
            5. Ensures data accuracy
            
            Return only the enhanced report without any additional commentary.
            """

            # Generate enhanced response
            response = self.gemini_model.generate_content(prompt)

            return response.text

        except Exception as e:
            logger.error(f"Error enhancing with Gemini: {e}")
            return draft

    def _format_report(
        self,
        report: str,
        sql_results: list[dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Format the final report with metadata and citations.

        Args:
            report: Generated report
            sql_results: SQL query results
            retrieved_docs: Retrieved documents

        Returns:
            Formatted report dictionary
        """
        try:
            # Generate report ID
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(report) % 10000:04d}"

            # Create citations
            citations = []
            for i, doc in enumerate(retrieved_docs):
                citation = {
                    "id": f"doc_{i+1}",
                    "source": doc.get("metadata", {}).get("file_name", "Unknown"),
                    "relevance_score": doc.get("hybrid_score", 0),
                    "text_snippet": doc.get("text", "")[:200] + "...",
                }
                citations.append(citation)

            # Format report
            formatted_report = {
                "id": report_id,
                "title": f"Seoul Commercial Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": report,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "sql_results_count": len(sql_results),
                    "retrieved_docs_count": len(retrieved_docs),
                    "citations_count": len(citations),
                    "word_count": len(report.split()),
                    "character_count": len(report),
                },
                "citations": citations,
                "data_summary": {
                    "sql_results": (
                        sql_results[:5] if sql_results else []
                    ),  # First 5 rows
                    "retrieved_docs": [
                        {
                            "id": doc.get("id", ""),
                            "text_snippet": doc.get("text", "")[:300] + "...",
                            "metadata": doc.get("metadata", {}),
                        }
                        for doc in retrieved_docs[:3]  # First 3 documents
                    ],
                },
            }

            return formatted_report

        except Exception as e:
            logger.error(f"Error formatting report: {e}")
            return {
                "id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Seoul Commercial Analysis Report",
                "content": report,
                "metadata": {"error": str(e)},
                "citations": [],
                "data_summary": {},
            }

    def synthesize_report(
        self,
        sql_results: list[dict[str, Any]],
        retrieved_docs: list[dict[str, Any]],
        query: str,
    ) -> dict[str, Any]:
        """
        Synthesize a comprehensive report from SQL results and retrieved documents.

        Args:
            sql_results: SQL query results
            retrieved_docs: Retrieved documents
            query: Original query

        Returns:
            Comprehensive report dictionary
        """
        try:
            # Extract key insights
            insights = self._extract_key_insights(sql_results, retrieved_docs)

            # Generate initial draft with HuggingFace LLM
            draft = self._generate_hf_draft(sql_results, retrieved_docs, query)

            # Enhance with Gemini if available
            enhanced_report = self._enhance_with_gemini(draft, insights)

            # Format final report
            formatted_report = self._format_report(
                enhanced_report, sql_results, retrieved_docs
            )

            return formatted_report

        except Exception as e:
            logger.error(f"Error synthesizing report: {e}")
            return {
                "id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Seoul Commercial Analysis Report",
                "content": f"Error generating report: {str(e)}",
                "metadata": {"error": str(e)},
                "citations": [],
                "data_summary": {},
            }


def compose_report(
    sql_results: list[dict[str, Any]],
    retrieved_docs: list[dict[str, Any]],
    query: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Compose a comprehensive report from SQL results and retrieved documents.

    Args:
        sql_results: SQL query results
        retrieved_docs: Retrieved documents
        query: Original query
        config: Configuration dictionary

    Returns:
        Comprehensive report dictionary
    """
    try:
        synthesizer = ReportSynthesizer(config)
        return synthesizer.synthesize_report(sql_results, retrieved_docs, query)
    except Exception as e:
        logger.error(f"Error in compose_report: {e}")
        return {
            "id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Seoul Commercial Analysis Report",
            "content": f"Error generating report: {str(e)}",
            "metadata": {"error": str(e)},
            "citations": [],
            "data_summary": {},
        }


def main():
    """Main function for testing the report synthesizer."""
    # Example configuration
    config = {
        "hf_llm_config": {
            "model_name": "microsoft/DialoGPT-medium",
            "context_window": 2048,
            "max_new_tokens": 512,
            "temperature": 0.7,
        },
        "gemini_config": {"api_key": "your_gemini_api_key", "model_name": "gemini-pro"},
        "report_config": {"max_citations": 10, "max_sql_rows": 100},
    }

    # Example data
    sql_results = [
        {"region_name": "강남구", "total_sales": 15000000, "transaction_count": 150},
        {"region_name": "서초구", "total_sales": 12000000, "transaction_count": 120},
    ]

    retrieved_docs = [
        {
            "id": "doc_1",
            "text": "강남구는 서울의 주요 상권 지역으로 높은 매출을 기록하고 있습니다.",
            "metadata": {"file_name": "seoul_analysis.pdf"},
            "hybrid_score": 0.95,
        }
    ]

    query = "서울 상권 매출 분석"

    # Generate report
    report = compose_report(sql_results, retrieved_docs, query, config)

    print("Generated Report:")
    print(f"ID: {report['id']}")
    print(f"Title: {report['title']}")
    print(f"Content: {report['content'][:500]}...")
    print(f"Citations: {len(report['citations'])}")


if __name__ == "__main__":
    main()
