"""
Tavily MCP 통합 테스트

RAG 시스템에 Tavily 웹 검색이 제대로 통합되었는지 테스트합니다.
"""

import sys
import io

# Windows 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os
from dotenv import load_dotenv
from rag.rag_chain import RAGChain

# 환경 변수 로드
load_dotenv()


async def test_tavily_mcp_basic():
    """기본 Tavily MCP 연결 테스트"""
    print("\n" + "="*60)
    print("TEST 1: Tavily MCP 기본 연결 테스트")
    print("="*60)

    try:
        rag = RAGChain(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            enable_web_search=True
        )

        if rag.tavily_mcp:
            print("✅ Tavily MCP 클라이언트 초기화 성공")

            # 사용 가능한 도구 확인
            print("\n[도구 목록 확인]")
            tools = await rag.tavily_mcp.list_available_tools()
            for tool in tools:
                print(f"  - {tool.get('name', 'unknown')}")

            return True
        else:
            print("❌ Tavily MCP 클라이언트 초기화 실패")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


async def test_case_c_fallback():
    """Case C: 로컬 문서 없음 → Tavily 폴백 테스트"""
    print("\n" + "="*60)
    print("TEST 2: Case C - Tavily 폴백 테스트")
    print("="*60)

    try:
        rag = RAGChain(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            enable_web_search=True
        )

        # 로컬 DB에 없을 것 같은 질문
        query = "이태원 상권 분석"
        print(f"\n질문: {query}")
        print("(로컬 DB에 없는 질문 → Tavily 폴백 예상)")

        result = await rag.run(query, top_k=3)

        print(f"\n[결과]")
        print(f"답변: {result['answer'][:200]}...")
        print(f"웹 검색 사용: {result.get('web_search_used', False)}")
        print(f"로컬 문서 수: {len(result.get('sources', []))}")

        if result.get('web_search_used'):
            print("✅ Tavily 폴백 정상 작동")
            return True
        else:
            print("⚠️  웹 검색이 사용되지 않음")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_case_d_realtime():
    """Case D: 실시간 정보 필요 → 웹 검색 테스트"""
    print("\n" + "="*60)
    print("TEST 3: Case D - 실시간 정보 웹 검색 테스트")
    print("="*60)

    try:
        rag = RAGChain(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            enable_web_search=True
        )

        # 실시간 키워드 포함 질문
        query = "2025년 최신 창업 트렌드"
        print(f"\n질문: {query}")
        print("(실시간 키워드 포함 → 웹 검색 예상)")

        result = await rag.run(query, top_k=3)

        print(f"\n[결과]")
        print(f"답변: {result['answer'][:200]}...")
        print(f"웹 검색 사용: {result.get('web_search_used', False)}")
        print(f"로컬 문서 수: {len(result.get('sources', []))}")

        if result.get('web_search_used'):
            print("✅ 실시간 정보 웹 검색 정상 작동")

            # 웹 검색 결과 확인
            if result.get('web_results'):
                web_results = result['web_results'].get('results', [])
                print(f"\n[웹 검색 결과 {len(web_results)}개]")
                for i, item in enumerate(web_results[:2], 1):
                    print(f"{i}. {item.get('title', 'N/A')}")
                    print(f"   URL: {item.get('url', 'N/A')}")

            return True
        else:
            print("⚠️  웹 검색이 사용되지 않음")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_realtime_detection():
    """실시간 쿼리 감지 로직 테스트"""
    print("\n" + "="*60)
    print("TEST 4: 실시간 쿼리 감지 로직 테스트")
    print("="*60)

    rag = RAGChain(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        enable_web_search=True
    )

    test_queries = [
        ("강남역 상권 분석", False),
        ("2025년 최신 트렌드", True),
        ("현재 유동인구 데이터", True),
        ("카페 창업 방법", False),
        ("요즘 인기있는 업종", True),
    ]

    print("\n[테스트 쿼리]")
    all_passed = True
    for query, expected in test_queries:
        result = rag._is_realtime_query(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} \"{query}\" → {result} (예상: {expected})")
        if result != expected:
            all_passed = False

    if all_passed:
        print("\n✅ 실시간 쿼리 감지 로직 정상")
    else:
        print("\n⚠️  일부 테스트 실패")

    return all_passed


async def main():
    """전체 테스트 실행"""
    print("\n[START] Tavily MCP Integration Test\n")

    results = []

    # Test 1: 기본 연결
    results.append(("Tavily MCP 연결", await test_tavily_mcp_basic()))

    # Test 2: 실시간 쿼리 감지
    results.append(("실시간 쿼리 감지", await test_realtime_detection()))

    # Test 3: Case C (Fallback)
    results.append(("Case C - Fallback", await test_case_c_fallback()))

    # Test 4: Case D (Realtime)
    results.append(("Case D - Realtime", await test_case_d_realtime()))

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n통과: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(main())
