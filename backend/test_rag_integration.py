"""
RAG Chain + MCP Tool Router 통합 테스트

기존 RAG 기능이 정상 작동하는지 확인합니다.
"""

import asyncio
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# RAG Chain import
from rag.rag_chain import RAGChain


async def test_rag_initialization():
    """RAG Chain 초기화 테스트"""
    print("\n" + "="*70)
    print("테스트 1: RAG Chain 초기화")
    print("="*70)

    try:
        rag_chain = RAGChain(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-4o-mini",
            temperature=0.7,
            mcp_config_path="mcp_config.json",
            enable_mcp=True
        )

        print("[OK] RAG Chain 초기화 성공")
        print(f"   - 모델: {rag_chain.model_name}")
        print(f"   - MCP 활성화: {rag_chain.enable_mcp}")

        return rag_chain

    except Exception as e:
        print(f"[ERROR] RAG Chain 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_simple_query(rag_chain):
    """간단한 질문 테스트 (로컬 문서만)"""
    print("\n" + "="*70)
    print("테스트 2: 간단한 질문 (로컬 문서)")
    print("="*70)

    query = "카페 창업 시 고려사항은?"

    print(f"\n질문: '{query}'")
    print("-" * 50)

    result = await rag_chain.run(query, top_k=3)

    print(f"\n결과:")
    print(f"  - 답변: {result['answer'][:100]}...")
    print(f"  - 로컬 문서: {len(result.get('sources', []))}개")
    print(f"  - MCP 사용: {result.get('web_search_used', False)}")
    print(f"  - 도구 목록: {result.get('tools_used', [])}")

    assert 'answer' in result, "답변이 없습니다"
    print("[OK] 테스트 통과")


async def test_realtime_query(rag_chain):
    """최신 정보 필요 질문 테스트 (MCP 도구 사용)"""
    print("\n" + "="*70)
    print("테스트 3: 최신 정보 필요 질문")
    print("="*70)

    query = "2025년 강남역 상권 트렌드는?"

    print(f"\n질문: '{query}'")
    print("-" * 50)

    result = await rag_chain.run(query, top_k=3)

    print(f"\n결과:")
    print(f"  - 답변: {result['answer'][:150]}...")
    print(f"  - 로컬 문서: {len(result.get('sources', []))}개")
    print(f"  - MCP 사용: {result.get('web_search_used', False)}")
    print(f"  - 도구 목록: {result.get('tools_used', [])}")

    if result.get('tools_used'):
        print(f"\n사용된 도구:")
        for tool in result['tools_used']:
            print(f"  - {tool}")

    if result.get('mcp_results'):
        print(f"\nMCP 결과 키: {list(result['mcp_results'].keys())}")

    assert 'answer' in result, "답변이 없습니다"
    print("[OK] 테스트 통과")


async def test_conversation_history(rag_chain):
    """대화 히스토리 테스트"""
    print("\n" + "="*70)
    print("테스트 4: 대화 히스토리")
    print("="*70)

    # 첫 번째 질문
    query1 = "강남역 근처에서 카페를 창업하려고 합니다"
    print(f"\n질문 1: '{query1}'")

    result1 = await rag_chain.run(query1, top_k=3)
    print(f"답변 1: {result1['answer'][:80]}...")

    # 두 번째 질문 (이전 대화 참조)
    query2 = "초기 투자 비용은 어느 정도인가요?"
    print(f"\n질문 2: '{query2}' (이전 대화 참조)")

    conversation_history = [
        {"role": "user", "content": query1},
        {"role": "assistant", "content": result1['answer']}
    ]

    result2 = await rag_chain.run(
        query2,
        conversation_history=conversation_history,
        top_k=3
    )

    print(f"답변 2: {result2['answer'][:80]}...")
    print(f"  - 로컬 문서: {len(result2.get('sources', []))}개")
    print(f"  - 도구 목록: {result2.get('tools_used', [])}")

    assert 'answer' in result2, "답변이 없습니다"
    print("[OK] 테스트 통과")


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*70)
    print("RAG Chain + MCP Tool Router 통합 테스트")
    print("="*70)

    try:
        # 1. 초기화
        rag_chain = await test_rag_initialization()

        if not rag_chain:
            print("\n[X] 초기화 실패. 테스트 중단.")
            return

        # MCP 도구 목록 발견 (한 번만)
        if rag_chain.mcp_tool_router:
            print("\n[MCP] 도구 목록 발견 중...")
            tools = await rag_chain.mcp_tool_router.universal_client.discover_all_tools()
            print(f"[OK] {len(tools)}개 도구 발견")
            for tool in tools:
                print(f"   - {tool.get('name')}")

        # 2. 간단한 질문 (로컬만)
        await test_simple_query(rag_chain)

        # 3. 최신 정보 필요 (MCP 사용)
        await test_realtime_query(rag_chain)

        # 4. 대화 히스토리
        await test_conversation_history(rag_chain)

        print("\n" + "="*70)
        print("[OK] 모든 테스트 완료!")
        print("="*70)

    except Exception as e:
        print(f"\n[X] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
