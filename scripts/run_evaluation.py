#!/usr/bin/env python3
"""
평가 스위트 실행 스크립트
TASK-016: 평가 스위트 - 정확도/각주율/지연 벤치
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.eval_suite import EvaluationSuite
from utils.sql_text2sql import TextToSQL
from utils.database import DatabaseManager
from utils.hybrid_retrieval import HybridRetrieval
from utils.report import ReportGenerator
from infrastructure.logging_service import LoggingService


def setup_components(config: dict) -> tuple:
    """평가에 필요한 컴포넌트들을 설정합니다."""
    logger = LoggingService().get_system_logger()
    
    try:
        # Database manager 설정
        db_manager = DatabaseManager(config.get("database", {}))
        
        # Text-to-SQL 엔진 설정
        sql_engine = TextToSQL(
            db_manager=db_manager,
            model_name=config.get("llm", {}).get("model_name", "microsoft/DialoGPT-medium"),
            device=config.get("llm", {}).get("device", "cpu")
        )
        
        # RAG 엔진 설정 (실제 구현에 따라 조정 필요)
        rag_engine = None
        if config.get("enable_rag_evaluation", True):
            try:
                rag_engine = HybridRetrieval(
                    vector_store_path=config.get("vector_store", {}).get("path", "data/vector_store"),
                    bm25_path=config.get("bm25", {}).get("path", "data/bm25_index")
                )
            except Exception as e:
                logger.warning(f"RAG 엔진 설정 실패: {e}")
                rag_engine = None
        
        # 보고서 생성기 설정
        report_generator = None
        if config.get("enable_report_evaluation", True):
            try:
                report_generator = ReportGenerator(
                    sql_engine=sql_engine,
                    rag_engine=rag_engine,
                    config=config.get("report", {})
                )
            except Exception as e:
                logger.warning(f"보고서 생성기 설정 실패: {e}")
                report_generator = None
        
        return sql_engine, rag_engine, report_generator
        
    except Exception as e:
        logger.error(f"컴포넌트 설정 실패: {e}")
        raise


def load_config(config_path: str) -> dict:
    """설정 파일을 로드합니다."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"설정 파일 JSON 파싱 오류: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """기본 설정을 반환합니다."""
    return {
        "database": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "seoul_commercial"
        },
        "llm": {
            "model_name": "microsoft/DialoGPT-medium",
            "device": "cpu"
        },
        "vector_store": {
            "path": "data/vector_store"
        },
        "bm25": {
            "path": "data/bm25_index"
        },
        "report": {
            "template_path": "prompts/report_templates"
        },
        "evaluation": {
            "results_path": "models/artifacts/evaluation"
        },
        "enable_rag_evaluation": True,
        "enable_report_evaluation": True
    }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="서울 상권 분석 LLM 시스템 평가 스위트 실행")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/evaluation_config.json",
        help="평가 설정 파일 경로"
    )
    parser.add_argument(
        "--components",
        nargs="+",
        choices=["sql", "rag", "report", "all"],
        default=["all"],
        help="평가할 컴포넌트 선택"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_report.md",
        help="평가 보고서 출력 파일 경로"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 설정 로드
    config = load_config(args.config)
    
    # 로깅 설정
    logger = LoggingService().get_system_logger()
    if args.verbose:
        logger.setLevel("DEBUG")
    
    try:
        print("🚀 서울 상권 분석 LLM 시스템 평가 시작")
        print(f"📋 평가 컴포넌트: {', '.join(args.components)}")
        print(f"📁 설정 파일: {args.config}")
        print(f"📄 출력 파일: {args.output}")
        print("-" * 50)
        
        # 평가 스위트 초기화
        eval_config = config.get("evaluation", {})
        eval_suite = EvaluationSuite(eval_config)
        
        # 컴포넌트 설정
        sql_engine = None
        rag_engine = None
        report_generator = None
        
        if "all" in args.components or "sql" in args.components:
            print("🔧 Text-to-SQL 엔진 설정 중...")
            sql_engine, _, _ = setup_components(config)
            print("✅ Text-to-SQL 엔진 설정 완료")
        
        if "all" in args.components or "rag" in args.components:
            print("🔧 RAG 엔진 설정 중...")
            _, rag_engine, _ = setup_components(config)
            if rag_engine:
                print("✅ RAG 엔진 설정 완료")
            else:
                print("⚠️  RAG 엔진 설정 건너뜀")
        
        if "all" in args.components or "report" in args.components:
            print("🔧 보고서 생성기 설정 중...")
            _, _, report_generator = setup_components(config)
            if report_generator:
                print("✅ 보고서 생성기 설정 완료")
            else:
                print("⚠️  보고서 생성기 설정 건너뜀")
        
        # 평가 실행
        print("\n📊 평가 실행 중...")
        results = eval_suite.run_comprehensive_evaluation(
            sql_engine=sql_engine,
            rag_engine=rag_engine,
            report_generator=report_generator
        )
        
        # 결과 출력
        print("\n📈 평가 결과:")
        print(f"⏱️  총 평가 시간: {results.get('total_evaluation_time', 0):.2f}초")
        
        # KPI 성과 출력
        kpi_perf = results.get("overall_metrics", {}).get("kpi_performance", {})
        if kpi_perf:
            print("\n🎯 KPI 성과:")
            print(f"  • Text-to-SQL 정확도: {kpi_perf.get('sql_accuracy_achieved', 0):.1%} "
                  f"({kpi_perf.get('sql_accuracy_status', 'N/A')})")
            print(f"  • 응답 시간 (P95): {kpi_perf.get('response_time_achieved', 0):.2f}초 "
                  f"({kpi_perf.get('response_time_status', 'N/A')})")
            print(f"  • 근거 각주 포함률: {kpi_perf.get('evidence_citation_achieved', 0):.1%} "
                  f"({kpi_perf.get('evidence_citation_status', 'N/A')})")
        
        # 상세 결과 출력
        components = results.get("components", {})
        if "text_to_sql" in components:
            sql_data = components["text_to_sql"]
            print(f"\n🔍 Text-to-SQL 상세:")
            print(f"  • 정확도: {sql_data.get('accuracy', 0):.1%}")
            print(f"  • 성공한 쿼리: {sql_data.get('successful_queries', 0)}/{sql_data.get('total_queries', 0)}")
            print(f"  • 평균 응답 시간: {sql_data.get('avg_response_time', 0):.2f}초")
        
        if "rag" in components:
            rag_data = components["rag"]
            print(f"\n🔍 RAG 상세:")
            print(f"  • 평균 관련성 점수: {rag_data.get('avg_relevance_score', 0):.3f}")
            print(f"  • 평균 응답 시간: {rag_data.get('avg_response_time', 0):.2f}초")
        
        if "report_generation" in components:
            report_data = components["report_generation"]
            print(f"\n🔍 보고서 생성 상세:")
            print(f"  • 성공률: {report_data.get('success_rate', 0):.1%}")
            print(f"  • 평균 품질 점수: {report_data.get('avg_quality_score', 0):.3f}")
            print(f"  • 평균 생성 시간: {report_data.get('avg_generation_time', 0):.2f}초")
        
        # 보고서 생성
        print(f"\n📝 평가 보고서 생성 중: {args.output}")
        report_content = eval_suite.generate_evaluation_report(results)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("✅ 평가 완료!")
        print(f"📄 상세 보고서: {args.output}")
        
        # JSON 결과도 저장
        json_output = args.output.replace('.md', '.json')
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📊 JSON 결과: {json_output}")
        
    except Exception as e:
        logger.error(f"평가 실행 실패: {e}")
        print(f"❌ 평가 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
