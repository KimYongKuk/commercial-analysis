"""
Tavily MCP 클라이언트 모듈

FastMCP를 사용하여 Tavily MCP 서버와 통신합니다.
"""

from fastmcp import Client
from typing import Dict, Any, List, Optional
import asyncio


class TavilyMCPClient:
    """FastMCP를 사용한 Tavily MCP 클라이언트"""

    def __init__(self, tavily_api_key: str):
        """
        Tavily MCP 클라이언트 초기화

        Args:
            tavily_api_key: Tavily API 키
        """
        if not tavily_api_key:
            raise ValueError("Tavily API 키가 필요합니다.")

        # Tavily MCP 원격 서버 URL
        self.server_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"
        self.client = Client(self.server_url)

        print(f"[MCP] Tavily MCP 클라이언트 초기화 완료")
        print(f"   - 서버: https://mcp.tavily.com/mcp/")

    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 10,
        topic: str = "general",
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tavily 웹 검색 실행

        Args:
            query: 검색 쿼리
            search_depth: 검색 깊이 ("basic" or "advanced")
            max_results: 최대 결과 개수
            topic: 검색 주제 ("general" or "news")
            days: 최근 N일 이내 결과 (None이면 전체 기간)

        Returns:
            검색 결과 딕셔너리
            {
                "results": [
                    {
                        "title": "...",
                        "url": "...",
                        "content": "...",
                        "score": 0.95,
                        "published_date": "..."
                    },
                    ...
                ],
                "query": "원본 쿼리"
            }
        """
        print(f"\n[MCP] Tavily 웹 검색 시작: {query}")
        print(f"   - 검색 깊이: {search_depth}")
        print(f"   - 최대 결과: {max_results}")
        print(f"   - 검색 주제: {topic}")
        if days:
            print(f"   - 기간: 최근 {days}일")

        try:
            async with self.client:
                # tavily-search 도구 호출
                search_params = {
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": max_results,
                    "topic": topic
                }
                
                if days:
                    search_params["days"] = days
                
                result = await self.client.call_tool(
                    "tavily_search",
                    search_params
                )

                result_data = result.data
                print(f"[OK] Tavily 검색 완료 (결과 수: {len(result_data.get('results', []))})")
                return result_data

        except Exception as e:
            print(f"[ERROR] Tavily 검색 실패: {e}")
            raise

    async def extract(self, urls: List[str]) -> Dict[str, Any]:
        """
        웹 페이지 데이터 추출

        Args:
            urls: 추출할 URL 리스트

        Returns:
            추출 결과 딕셔너리
        """
        print(f"\n[MCP] Tavily 데이터 추출 시작 ({len(urls)}개 URL)")

        try:
            async with self.client:
                result = await self.client.call_tool(
                    "tavily_extract",
                    {"urls": urls}
                )

                result_data = result.data
                print(f"[OK] Tavily 추출 완료")
                return result_data

        except Exception as e:
            print(f"[ERROR] Tavily 추출 실패: {e}")
            raise

    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 MCP 도구 목록 확인

        Returns:
            도구 목록
        """
        try:
            async with self.client:
                tools = await self.client.list_tools()
                return tools

        except Exception as e:
            print(f"[ERROR] MCP 도구 목록 조회 실패: {e}")
            raise

    def format_search_results_for_prompt(
        self,
        search_results: Dict[str, Any],
        max_results: int = 3
    ) -> str:
        """
        검색 결과를 프롬프트용 텍스트로 포맷팅

        Args:
            search_results: Tavily 검색 결과
            max_results: 포함할 최대 결과 개수

        Returns:
            포맷팅된 텍스트
        """
        if not search_results or not search_results.get("results"):
            return "웹 검색 결과를 찾을 수 없습니다."

        results = search_results.get("results", [])[:max_results]
        formatted_text = []

        for i, result in enumerate(results):
            text = f"[웹 검색 결과 {i+1}]\n"
            text += f"제목: {result.get('title', 'N/A')}\n"
            text += f"URL: {result.get('url', 'N/A')}\n"

            if result.get('score'):
                text += f"관련도: {result.get('score'):.2f}\n"

            text += f"내용: {result.get('content', 'N/A')}"
            formatted_text.append(text)

        return "\n\n---\n\n".join(formatted_text)


# 사용 예시
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    async def test_tavily_mcp():
        """Tavily MCP 클라이언트 테스트"""

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY 환경변수를 설정해주세요.")
            return

        client = TavilyMCPClient(api_key)

        # 1. 사용 가능한 도구 확인
        print("\n=== 사용 가능한 MCP 도구 ===")
        tools = await client.list_available_tools()
        for tool in tools:
            print(f"- {tool.get('name', 'unknown')}: {tool.get('description', '')}")

        # 2. 웹 검색 테스트
        print("\n=== 웹 검색 테스트 ===")
        query = "강남역 상권 분석 2025"
        result = await client.search(query, search_depth="basic", max_results=3)

        print(f"\n검색 쿼리: {result.get('query', query)}")
        print(f"검색 결과 수: {len(result.get('results', []))}")

        # 결과 출력
        for i, item in enumerate(result.get('results', []), 1):
            print(f"\n[{i}] {item.get('title', 'N/A')}")
            print(f"    URL: {item.get('url', 'N/A')}")
            print(f"    내용: {item.get('content', 'N/A')[:100]}...")

        # 3. 프롬프트 포맷팅 테스트
        print("\n=== 프롬프트 포맷팅 테스트 ===")
        formatted = client.format_search_results_for_prompt(result, max_results=2)
        print(formatted)

    # 테스트 실행
    asyncio.run(test_tavily_mcp())
