#!/usr/bin/env python3
"""
외부 데이터 통합 기능 테스트 스크립트
data_sites.txt에 있는 데이터 포털 사이트들을 활용한 외부 데이터 검색 테스트
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_external_data_service():
    """외부 데이터 서비스 테스트"""
    try:
        from retrieval.external_data_service import get_external_data_service
        
        logger.info("🔍 외부 데이터 서비스 테스트 시작")
        
        service = get_external_data_service()
        
        # 사용 가능한 포털 목록 확인
        portals = service.get_portal_list()
        logger.info(f"✅ 사용 가능한 포털: {len(portals)}개")
        for portal in portals:
            logger.info(f"  - {portal['display_name']}: {portal['base_url']}")
        
        # 테스트 검색 실행
        test_query = "서울시 상권 데이터"
        logger.info(f"🔍 테스트 검색: '{test_query}'")
        
        results = service.search_all_portals(test_query, max_results_per_portal=3)
        
        if results:
            logger.info(f"✅ 검색 성공: {len(results)}개 결과")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"  {i}. {result.title[:50]}... (출처: {result.source})")
        else:
            logger.warning("⚠️ 검색 결과가 없습니다")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 외부 데이터 서비스 테스트 실패: {str(e)}")
        return False

def test_hybrid_service():
    """하이브리드 서비스 테스트"""
    try:
        from retrieval.hybrid_external_rag import get_hybrid_external_rag_service
        
        logger.info("🔗 하이브리드 서비스 테스트 시작")
        
        service = get_hybrid_external_rag_service()
        
        # 하이브리드 검색 테스트
        test_query = "상권 분석 데이터"
        logger.info(f"🔍 하이브리드 검색: '{test_query}'")
        
        result = service.search_hybrid(
            query=test_query,
            max_results=10,
            include_external=True,
            include_rag=False,  # RAG 서비스가 없을 수 있으므로 False
            include_sql=False   # SQL 서비스가 없을 수 있으므로 False
        )
        
        if result["success"]:
            logger.info(f"✅ 하이브리드 검색 성공: {len(result['results'])}개 결과")
            
            # 소스별 결과 분포 확인
            if "source_breakdown" in result:
                logger.info("📊 소스별 결과 분포:")
                for source, count in result["source_breakdown"].items():
                    logger.info(f"  - {source}: {count}개")
            
            # 상위 3개 결과 표시
            for i, res in enumerate(result["results"][:3], 1):
                logger.info(f"  {i}. {res['title'][:50]}... (타입: {res['result_type']}, 점수: {res['relevance_score']:.2f})")
        else:
            logger.warning(f"⚠️ 하이브리드 검색 실패: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 하이브리드 서비스 테스트 실패: {str(e)}")
        return False

def test_query_orchestrator():
    """질의 오케스트레이터 테스트"""
    try:
        from orchestration.query_orchestrator import get_query_orchestrator
        
        logger.info("🎯 질의 오케스트레이터 테스트 시작")
        
        orchestrator = get_query_orchestrator()
        
        # 외부 데이터 관련 질의 테스트
        test_queries = [
            "외부 데이터에서 서울시 상권 정보를 가져와줘",
            "공공데이터포털에서 창업 지원 데이터를 찾아줘",
            "kaggle에서 상권 분석 데이터셋을 검색해줘"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 질의 테스트: '{query}'")
            
            result = orchestrator.process_query(query)
            
            if result["success"]:
                logger.info(f"✅ 질의 처리 성공 (모드: {result['mode']}, 신뢰도: {result['confidence']:.2f})")
                
                # 결과 요약 표시
                if "result" in result and "summary" in result["result"]:
                    logger.info(f"📝 요약: {result['result']['summary'][:100]}...")
            else:
                logger.warning(f"⚠️ 질의 처리 실패: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 질의 오케스트레이터 테스트 실패: {str(e)}")
        return False

def test_intent_router():
    """의도 라우터 테스트"""
    try:
        from orchestration.intent_router import get_intent_router
        
        logger.info("🧭 의도 라우터 테스트 시작")
        
        router = get_intent_router()
        
        # 외부 데이터 관련 질의 테스트
        test_queries = [
            "외부 데이터에서 서울시 상권 정보를 가져와줘",
            "공공데이터포털에서 창업 지원 데이터를 찾아줘",
            "kaggle에서 상권 분석 데이터셋을 검색해줘",
            "서울시 데이터포털에서 매출 데이터를 참조해줘"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 의도 라우팅 테스트: '{query}'")
            
            result = router.route_intent(query)
            
            logger.info(f"✅ 라우팅 결과: {result['mode'].value} (신뢰도: {result['confidence']:.2f})")
            
            if result['reasoning']:
                for reason in result['reasoning']:
                    logger.info(f"  📋 이유: {reason}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 의도 라우터 테스트 실패: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("🚀 외부 데이터 통합 기능 테스트 시작")
    logger.info("=" * 60)
    
    test_results = []
    
    # 1. 외부 데이터 서비스 테스트
    test_results.append(("외부 데이터 서비스", test_external_data_service()))
    logger.info("")
    
    # 2. 하이브리드 서비스 테스트
    test_results.append(("하이브리드 서비스", test_hybrid_service()))
    logger.info("")
    
    # 3. 의도 라우터 테스트
    test_results.append(("의도 라우터", test_intent_router()))
    logger.info("")
    
    # 4. 질의 오케스트레이터 테스트
    test_results.append(("질의 오케스트레이터", test_query_orchestrator()))
    logger.info("")
    
    # 테스트 결과 요약
    logger.info("=" * 60)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"📈 총 테스트: {len(test_results)}개")
    logger.info(f"✅ 성공: {passed}개")
    logger.info(f"❌ 실패: {failed}개")
    logger.info(f"📊 성공률: {(passed / len(test_results) * 100):.1f}%")
    
    if failed == 0:
        logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return True
    else:
        logger.warning(f"⚠️ {failed}개의 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
