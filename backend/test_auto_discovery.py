"""
MCP 자동 발견 기능 테스트

자동 발견 방식으로 변경 후:
1. Tavily와 Brave 도구 모두 발견되는지 확인
2. LLM이 두 도구 중 선택할 수 있는지 확인
3. Description 보강이 제대로 동작하는지 확인
"""

import asyncio
import os
from dotenv import load_dotenv
from rag.mcp_client_new import UniversalMCPClient, MCPToolRouter

load_dotenv()


async def test_auto_discovery():
    """MCP 자동 발견 테스트"""

    print("\n" + "="*60)
    print("MCP 자동 발견 기능 테스트")
    print("="*60)

    # 1. UniversalMCPClient 초기화
    print("\n[1단계] UniversalMCPClient 초기화")
    universal_client = UniversalMCPClient.from_config("mcp_config.json")

    # 2. 도구 발견
    print("\n[2단계] MCP 도구 자동 발견")
    tools = await universal_client.discover_all_tools()

    print(f"\n발견된 도구: {len(tools)}개")
    for i, tool in enumerate(tools, 1):
        server = tool.get('server', 'unknown')
        name = tool.get('name', 'unknown')
        desc = tool.get('description', '')[:50]
        print(f"  {i}. [{server}] {name}")
        print(f"     설명: {desc}...")

    # 3. MCPToolRouter 초기화
    print("\n[3단계] MCPToolRouter 초기화")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY 환경변수가 필요합니다.")
        return

    router = MCPToolRouter(
        openai_api_key=openai_api_key,
        universal_client=universal_client,
        enable_description_enhancement=True
    )

    # 4. 도구 초기화 (자동 발견 + 스키마 변환)
    print("\n[4단계] 도구 초기화 (스키마 변환)")
    tool_count = await router.initialize()

    print(f"\n변환된 OpenAI Function 스키마: {tool_count}개")
    for i, tool in enumerate(router.discovered_tools, 1):
        func = tool['function']
        name = func['name']
        desc = func['description'][:80]
        params = func.get('parameters', {})
        required = params.get('required', [])

        print(f"\n  {i}. {name}")
        print(f"     설명: {desc}...")
        print(f"     필수 파라미터: {required}")

    # 5. 테스트 시나리오
    print("\n" + "="*60)
    print("테스트 시나리오")
    print("="*60)

    test_queries = [
        {
            "query": "2025년 강남 카페 트렌드",
            "local_docs": [{"content": "상권 분석 기초", "score": 0.65}],
            "expected": "tavily_search 또는 brave_web_search 선택"
        },
        {
            "query": "카페 창업 기본 가이드",
            "local_docs": [{"content": "카페 창업 가이드", "score": 0.85}],
            "expected": "도구 불필요"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}] {test['query']}")
        print(f"예상: {test['expected']}")

        try:
            result = await router.select_and_execute_mcp_tools(
                query=test['query'],
                local_docs=test['local_docs']
            )

            print(f"결과:")
            print(f"  - MCP 사용: {result['mcp_used']}")
            print(f"  - 사용된 도구: {result['tools_used']}")

            if result['mcp_used']:
                print(f"  ✅ LLM이 외부 도구가 필요하다고 판단")
            else:
                print(f"  ✅ LLM이 로컬 문서로 충분하다고 판단")

        except Exception as e:
            print(f"  ❌ 오류: {e}")

    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_auto_discovery())
