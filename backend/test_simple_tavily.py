"""
Tavily MCP 간단 테스트 - 도구 목록 확인
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

    print(f"Server URL: {server_url[:50]}...")

    client = Client(server_url)

    async with client:
        print("\n[사용 가능한 도구]")
        tools = await client.list_tools()

        for tool in tools:
            print(f"\n도구 이름: {tool.name}")
            print(f"설명: {tool.description}")
            if hasattr(tool, 'inputSchema'):
                print(f"입력 스키마: {tool.inputSchema}")

asyncio.run(test())
