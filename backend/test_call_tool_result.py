"""
FastMCP call_tool 결과 타입 확인
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os
from dotenv import load_dotenv
from fastmcp import Client

load_dotenv()

async def test():
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    server_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"

    client = Client(server_url)

    async with client:
        result = await client.call_tool(
            "tavily_search",
            {
                "query": "test query",
                "max_results": 1
            }
        )

        print(f"결과 타입: {type(result)}")
        print(f"결과 속성: {dir(result)}")
        print(f"\n결과 내용:")
        print(result)

        # content 속성 확인
        if hasattr(result, 'content'):
            print(f"\ncontent 타입: {type(result.content)}")
            print(f"content 내용: {result.content}")

asyncio.run(test())
