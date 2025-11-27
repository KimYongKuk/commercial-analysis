"""
MCP Tool Router 테스트 스크립트

mcp_client_new.py의 기능을 검증합니다.
"""

import asyncio
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 모듈 import
from rag.mcp_client_new import (
    UniversalMCPClient,
    MCPToolRouter,
    ToolSchemaConverter
)


async def test_basic_setup():
    """기본 설정 테스트 (JSON 설정 파일 사용)"""
    print("\n" + "="*70)
    print("테스트 1: 기본 설정 및 초기화 (JSON)")
    print("="*70)

    # API 키 확인
    openai_key = os.getenv("OPENAI_API_KEY")

    print(f"[OK] OPENAI_API_KEY: {'설정됨' if openai_key else '[X] 없음'}")

    if not openai_key:
        print("\n[X] OPENAI_API_KEY를 .env 파일에 설정해주세요.")
        return None, None

    # ✨ 1. JSON 설정 파일로 UniversalMCPClient 초기화 (간소화!)
    print("\n[1] JSON 설정 파일로 MCP 서버 로드...")
    try:
        universal_client = UniversalMCPClient.from_config("mcp_config.json")
    except Exception as e:
        print(f"[ERROR] 설정 파일 로드 실패: {e}")
        return None, None

    # 2. 도구 발견
    print("[2] MCP 도구 목록 발견...")
    try:
        tools = await universal_client.discover_all_tools()
        print(f"[OK] 발견된 도구: {len(tools)}개")
        for tool in tools:
            print(f"   - {tool.get('name')}: {tool.get('description', 'N/A')[:50]}...")
    except Exception as e:
        print(f"[ERROR] 도구 발견 실패: {e}")
        print("   수동 스키마를 사용합니다.")

    # 3. MCPToolRouter 초기화
    print("\n[3] MCPToolRouter 초기화...")
    router = MCPToolRouter(
        openai_api_key=openai_key,
        universal_client=universal_client,
        model_name="gpt-4o-mini",
        temperature=0.3
    )

    print("\n[OK] 모든 컴포넌트 초기화 완료!")
    return universal_client, router


async def test_simple_queries(router):
    """간단한 질문 테스트 (도구 불필요)"""
    print("\n" + "="*70)
    print("테스트 2: 간단한 질문 (도구 불필요)")
    print("="*70)

    test_cases = [
        ("안녕하세요", "인사말"),
        ("고맙습니다", "감사 인사"),
        ("안녕히 가세요", "작별 인사")
    ]

    for query, description in test_cases:
        print(f"\n질문: '{query}' ({description})")
        print("-" * 50)

        result = await router.select_and_execute_mcp_tools(
            query=query,
            local_docs=[]
        )

        print(f"결과:")
        print(f"  - MCP 사용: {result['mcp_used']}")
        print(f"  - 도구 목록: {result['tools_used']}")
        print(f"  - 직접 답변: {result.get('direct_answer', 'N/A')[:100] if result.get('direct_answer') else 'None'}...")

        assert result['mcp_used'] == False, "간단한 질문은 MCP를 사용하지 않아야 합니다"
        print("[OK] 통과")


async def test_local_sufficient(router):
    """로컬 문서로 충분한 질문 테스트"""
    print("\n" + "="*70)
    print("테스트 3: 로컬 문서로 충분한 질문")
    print("="*70)

    # 가상의 로컬 문서 (RAG 검색 결과)
    local_docs = [
        {
            "content": "카페 창업 시 고려해야 할 사항: 입지, 초기 비용, 메뉴 구성, 인테리어, 마케팅 전략 등...",
            "score": 0.92,
            "metadata": {"source": "cafe_startup_guide.pdf"}
        },
        {
            "content": "카페 초기 투자 비용은 일반적으로 5천만원~1억원 정도입니다...",
            "score": 0.88,
            "metadata": {"source": "startup_cost_analysis.pdf"}
        }
    ]

    query = "카페 창업 시 고려사항은 무엇인가요?"

    print(f"\n질문: '{query}'")
    print(f"로컬 문서: {len(local_docs)}개 (평균 유사도: {sum(d['score'] for d in local_docs)/len(local_docs):.2f})")
    print("-" * 50)

    result = await router.select_and_execute_mcp_tools(
        query=query,
        local_docs=local_docs
    )

    print(f"\n결과:")
    print(f"  - MCP 사용: {result['mcp_used']}")
    print(f"  - 도구 목록: {result['tools_used']}")

    # LLM이 로컬 문서로 충분하다고 판단하면 도구를 사용하지 않아야 함
    if not result['mcp_used']:
        print("[OK] LLM 판단: 로컬 문서로 충분 (웹 검색 불필요)")
    else:
        print("⚠️  LLM이 추가 도구를 선택했습니다 (예상과 다름)")
        print(f"   사용된 도구: {result['tools_used']}")


async def test_realtime_needed(router):
    """최신 정보 필요 질문 테스트 (MCP 도구 사용)"""
    print("\n" + "="*70)
    print("테스트 4: 최신 정보 필요 (MCP 도구 사용)")
    print("="*70)

    # 로컬 문서는 일반 가이드만 있음
    local_docs = [
        {
            "content": "상권 분석의 기본 원칙: 유동인구, 경쟁 업체, 임대료 등을 고려해야 합니다...",
            "score": 0.70,
            "metadata": {"source": "basic_guide.pdf"}
        }
    ]

    query = "2025년 강남역 상권 트렌드는 어떤가요?"

    print(f"\n질문: '{query}'")
    print(f"로컬 문서: {len(local_docs)}개 (유사도: {local_docs[0]['score']:.2f})")
    print(f"키워드 분석: '2025년' (최신), '트렌드' (실시간 정보)")
    print("-" * 50)

    result = await router.select_and_execute_mcp_tools(
        query=query,
        local_docs=local_docs
    )

    print(f"\n결과:")
    print(f"  - MCP 사용: {result['mcp_used']}")
    print(f"  - 도구 목록: {result['tools_used']}")

    if result['mcp_used']:
        print("[OK] LLM 판단: 최신 정보 필요 (웹 검색 실행)")

        # 도구 실행 결과 확인
        if "tavily_search" in result['results']:
            tavily_result = result['results']['tavily_search']
            if isinstance(tavily_result, dict) and 'results' in tavily_result:
                print(f"\n웹 검색 결과: {len(tavily_result.get('results', []))}개")
                for i, item in enumerate(tavily_result.get('results', [])[:2], 1):
                    print(f"  [{i}] {item.get('title', 'N/A')}")
                    print(f"      {item.get('url', 'N/A')}")
            else:
                print(f"  결과: {str(tavily_result)[:100]}...")
    else:
        print("⚠️  LLM이 도구를 선택하지 않았습니다 (예상과 다름)")


async def test_tool_schema_converter():
    """Tool Schema 변환기 테스트"""
    print("\n" + "="*70)
    print("테스트 5: Tool Schema 변환")
    print("="*70)

    # 수동 정의된 도구 가져오기
    tools = ToolSchemaConverter.get_tavily_tools_manual()

    print(f"\n정의된 도구: {len(tools)}개")
    for tool in tools:
        func = tool['function']
        print(f"\n  이름: {func['name']}")
        print(f"  설명: {func['description'][:100]}...")
        print(f"  필수 파라미터: {func['parameters'].get('required', [])}")

    assert len(tools) == 2, "Tavily 도구는 2개여야 합니다"
    assert tools[0]['function']['name'] == "tavily_search", "첫 번째 도구는 tavily_search"
    assert tools[1]['function']['name'] == "tavily_extract", "두 번째 도구는 tavily_extract"

    print("\n[OK] 모든 스키마 검증 통과")


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*70)
    print("MCP Tool Router 통합 테스트")
    print("="*70)

    try:
        # 1. 기본 설정
        universal_client, router = await test_basic_setup()

        if not router:
            print("\n[X] 설정 실패. 테스트 중단.")
            return

        # 2. 간단한 질문 테스트
        await test_simple_queries(router)

        # 3. 로컬 문서로 충분한 질문
        await test_local_sufficient(router)

        # 4. 최신 정보 필요 질문 (실제 웹 검색)
        await test_realtime_needed(router)

        # 5. Tool Schema 변환기
        await test_tool_schema_converter()

        print("\n" + "="*70)
        print("[OK] 모든 테스트 완료!")
        print("="*70)

    except Exception as e:
        print(f"\n[X] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
