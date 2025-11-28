"""
MCP Tool Calling 시스템

LLM이 필요한 MCP 도구를 자동으로 선택하고 실행하는 시스템입니다.
RAG 레이어(로컬 검색)는 별도로 동작하며, MCP는 추가 외부 도구만 관리합니다.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from fastmcp import Client
import json
import asyncio
import os


# ============================================
# 1. UniversalMCPClient (범용 MCP 클라이언트)
# ============================================

class UniversalMCPClient:
    """
    여러 MCP 서버를 통합 관리하는 범용 클라이언트

    - 여러 MCP 서버 등록 (Tavily, 커스텀 서버 등)
    - 도구 이름으로 자동 디스패치
    - 모든 MCP 서버의 도구 목록 통합 관리
    """

    def __init__(self):
        """MCP 클라이언트 초기화"""
        self.mcp_servers = {}  # {server_name: {"client": client, "tools": [...]}}
        print("[UniversalMCPClient] 초기화 완료")

    @classmethod
    def from_config(cls, config_path: str):
        """
        JSON 설정 파일로 UniversalMCPClient 초기화

        Args:
            config_path: MCP 설정 파일 경로 (예: "mcp_config.json")
                형식:
                {
                    "mcpServers": {
                        "tavily": {
                            "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
                        }
                    }
                }

        Returns:
            초기화된 UniversalMCPClient 인스턴스
        """
        import json
        import os
        import re
        from fastmcp import Client

        print(f"\n[UniversalMCPClient] JSON 설정 파일 로드: {config_path}")

        # JSON 파일 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 환경변수 치환 함수
        def replace_env_vars(text: str) -> str:
            """${VAR_NAME} 형식의 환경변수를 실제 값으로 치환"""
            def replacer(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))

            return re.sub(r'\$\{([^}]+)\}', replacer, text)

        # UniversalMCPClient 인스턴스 생성
        instance = cls()

        # mcpServers 설정 처리
        if "mcpServers" not in config:
            raise ValueError("JSON 설정에 'mcpServers' 키가 없습니다.")

        for server_name, server_config in config["mcpServers"].items():
            print(f"[UniversalMCPClient] 서버 등록 중: {server_name}")

            # 환경변수 치환
            if "url" in server_config:
                server_config["url"] = replace_env_vars(server_config["url"])

            if "command" in server_config:
                server_config["command"] = replace_env_vars(server_config["command"])

            if "args" in server_config and isinstance(server_config["args"], list):
                server_config["args"] = [
                    replace_env_vars(arg) if isinstance(arg, str) else arg
                    for arg in server_config["args"]
                ]

            # FastMCP Client 생성 (단일 서버 config)
            single_server_config = {"mcpServers": {server_name: server_config}}

            try:
                # FastMCP Client가 mcpServers 형식을 직접 처리
                fastmcp_client = Client(single_server_config)

                instance.mcp_servers[server_name] = {
                    "client": fastmcp_client,
                    "tools": [],
                    "config": server_config
                }

                print(f"   [OK] {server_name} 등록 완료")

            except Exception as e:
                print(f"   [ERROR] {server_name} 등록 실패: {e}")

        print(f"[OK] 총 {len(instance.mcp_servers)}개 MCP 서버 로드 완료\n")

        return instance

    def register_server(
        self,
        server_name: str,
        client: Any,
        description: str = ""
    ):
        """
        MCP 서버 등록

        Args:
            server_name: 서버 식별자 (예: "tavily", "custom")
            client: MCP 클라이언트 인스턴스 (TavilyMCPClient 등)
            description: 서버 설명
        """
        self.mcp_servers[server_name] = {
            "client": client,
            "tools": [],  # 나중에 list_tools()로 채움
            "description": description
        }
        print(f"[UniversalMCPClient] MCP 서버 등록: {server_name} - {description}")

    async def discover_all_tools(self) -> List[Dict[str, Any]]:
        """
        모든 등록된 MCP 서버의 도구 목록 수집

        Returns:
            통합 도구 목록
            [
                {
                    "server": "tavily",
                    "name": "tavily_search",
                    "description": "...",
                    "inputSchema": {...}
                },
                ...
            ]
        """
        all_tools = []

        for server_name, server_info in self.mcp_servers.items():
            client = server_info["client"]

            # FastMCP Client는 list_tools() 메서드 사용
            try:
                # FastMCP Client context 사용
                async with client:
                    tools = await client.list_tools()

                # 도구에 서버 정보 추가
                for tool in tools:
                    # Tool 객체를 딕셔너리로 변환
                    if hasattr(tool, '__dict__'):
                        tool_dict = {
                            "name": getattr(tool, 'name', 'unknown'),
                            "description": getattr(tool, 'description', ''),
                            "inputSchema": getattr(tool, 'inputSchema', {}),
                            "server": server_name
                        }
                    elif isinstance(tool, dict):
                        tool_dict = {**tool, "server": server_name}
                    else:
                        continue

                    all_tools.append(tool_dict)

                # 서버에 도구 목록 캐싱 (딕셔너리 형식으로)
                server_info["tools"] = all_tools

                print(f"[UniversalMCPClient] {server_name}: {len(tools)}개 도구 발견")

            except Exception as e:
                print(f"[ERROR] {server_name} 도구 목록 조회 실패: {e}")

        return all_tools

    async def call_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        도구 이름으로 적절한 MCP 서버에 동적 디스패치

        Args:
            tool_name: 도구 이름 (예: "tavily_search")
            tool_args: 도구 파라미터

        Returns:
            도구 실행 결과
        """
        print(f"\n[UniversalMCPClient] 도구 호출: {tool_name}")
        print(f"   파라미터: {json.dumps(tool_args, ensure_ascii=False)[:100]}...")

        # 도구가 어느 서버에 속하는지 찾기
        target_server = None
        for server_name, server_info in self.mcp_servers.items():
            for tool in server_info["tools"]:
                if tool.get("name") == tool_name:
                    target_server = server_name
                    break
            if target_server:
                break

        if not target_server:
            raise ValueError(f"도구 '{tool_name}'을 찾을 수 없습니다.")

        # 해당 서버의 클라이언트로 도구 호출
        client = self.mcp_servers[target_server]["client"]

        # FastMCP Client는 call_tool() 메서드 사용
        try:
            async with client:
                result = await client.call_tool(tool_name, tool_args)
                # FastMCP는 ToolResult 객체 반환, .data 속성에 실제 데이터
                if hasattr(result, 'data'):
                    result_data = result.data
                else:
                    result_data = result

            print(f"[OK] 도구 실행 완료: {tool_name}")
            return result_data

        except Exception as e:
            print(f"[ERROR] 도구 실행 실패: {e}")
            raise


# ============================================
# 2. ToolSchemaConverter (스키마 변환)
# ============================================

class ToolSchemaConverter:
    """MCP Tool Schema ↔ OpenAI Function Schema 변환"""

    @staticmethod
    def mcp_to_openai(mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 도구 정의를 OpenAI Function 포맷으로 변환

        Args:
            mcp_tool: MCP 도구 스키마
            {
                "server": "tavily",
                "name": "tavily_search",
                "description": "Search the web using Tavily API",
                "inputSchema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }

        Returns:
            OpenAI Function 스키마
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "Search the web using Tavily API",
                    "parameters": {...}
                }
            }
        """
        return {
            "type": "function",
            "function": {
                "name": mcp_tool.get("name"),
                "description": mcp_tool.get("description", ""),
                "parameters": mcp_tool.get("inputSchema", {})
            }
        }

    @staticmethod
    def enhance_tool_description(openai_tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        OpenAI Function 스키마의 description을 보강 (선택 사항)

        특정 도구에 대해 LLM이 더 잘 이해할 수 있도록 상세한 가이드 추가

        Args:
            openai_tool: OpenAI Function 스키마

        Returns:
            Description이 보강된 OpenAI Function 스키마
        """
        tool_name = openai_tool["function"]["name"]

        # Tavily Search에 대한 상세 가이드
        if tool_name == "tavily_search":
            openai_tool["function"]["description"] += """

**사용 시점:**
- 최신 뉴스, 트렌드, 실시간 데이터가 필요한 경우
- "2025년", "최근", "현재", "요즘" 등의 키워드가 있는 경우
- 로컬 문서에 없는 최신 정보가 필요한 경우

**사용 안 함:**
- 로컬 문서로 충분히 답변 가능한 경우
- 일반적인 가이드, 기본 지식 질문
- 시간과 무관한 기본 개념 설명

**예시:**
✅ "2025년 강남 상권 트렌드" → 사용
✅ "최근 부동산 시장 동향" → 사용
❌ "카페 창업 기본 가이드" → 사용 안 함 (로컬 문서로 충분)
❌ "메뉴 가격 책정 방법" → 사용 안 함 (기본 지식)
"""

        return openai_tool

    @staticmethod
    def get_tavily_tools_manual() -> List[Dict[str, Any]]:
        """
        Tavily MCP 도구를 수동으로 정의 (자동 발견 실패 시 폴백)

        Returns:
            OpenAI Function 스키마 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": """실시간 웹 검색 도구. 최신 정보, 뉴스, 트렌드가 필요할 때 사용.

**사용 시점:**
- 최신 뉴스, 트렌드, 실시간 데이터가 필요한 경우
- "2025년", "최근", "현재", "요즘" 등의 키워드가 있는 경우
- 로컬 문서에 없는 최신 정보가 필요한 경우

**사용 안 함:**
- 로컬 문서로 충분히 답변 가능한 경우
- 일반적인 가이드, 기본 지식 질문
- 시간과 무관한 기본 개념 설명

**예시:**
✅ "2025년 강남 상권 트렌드" → 사용
✅ "최근 부동산 시장 동향" → 사용
❌ "카페 창업 기본 가이드" → 사용 안 함 (로컬 문서로 충분)
❌ "메뉴 가격 책정 방법" → 사용 안 함 (기본 지식)
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색 쿼리 (한국어 또는 영어)"
                            },
                            "search_depth": {
                                "type": "string",
                                "enum": ["basic", "advanced"],
                                "description": "검색 깊이. basic=빠른 검색, advanced=상세 검색 (기본값: advanced)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "최대 결과 개수 (기본값: 5)"
                            },
                            "topic": {
                                "type": "string",
                                "enum": ["general", "news"],
                                "description": "검색 주제. general=일반, news=뉴스 (기본값: general)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tavily_extract",
                    "description": """특정 URL의 웹 페이지 전체 내용을 추출하는 도구.

**사용 시점:**
- 특정 웹 페이지의 상세 내용이 필요한 경우
- tavily_search 결과에서 특정 URL을 더 자세히 분석해야 하는 경우

**예시:**
- tavily_search로 URL을 찾은 후, 해당 페이지의 전체 내용 추출
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "추출할 URL 리스트"
                            }
                        },
                        "required": ["urls"]
                    }
                }
            }
        ]


# ============================================
# 3. MCPToolRouter (핵심 로직)
# ============================================

class MCPToolRouter:
    """
    LLM 기반 MCP 도구 선택 및 실행 라우터

    - RAG 검색 결과를 고려하여 추가 MCP 도구 필요성 판단
    - LLM이 자동으로 필요한 도구 선택
    - 선택된 도구 실행 및 결과 반환
    """

    def __init__(
        self,
        openai_api_key: str,
        universal_client: UniversalMCPClient,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3,
        enable_description_enhancement: bool = True
    ):
        """
        Tool Router 초기화

        Args:
            openai_api_key: OpenAI API 키
            universal_client: UniversalMCPClient 인스턴스
            model_name: LLM 모델 (도구 선택용)
            temperature: 낮을수록 일관된 선택 (0.0~1.0)
            enable_description_enhancement: Description 자동 보강 활성화 여부
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.universal_client = universal_client
        self.model_name = model_name
        self.temperature = temperature
        self.enable_description_enhancement = enable_description_enhancement

        # 자동 발견된 도구 캐싱
        self.discovered_tools = []
        self.is_initialized = False

        print(f"[MCPToolRouter] 초기화 완료 (모델: {model_name})")

    async def initialize(self):
        """
        MCP 도구 자동 발견 및 스키마 변환

        - UniversalMCPClient에서 모든 MCP 서버의 도구 발견
        - MCP 스키마를 OpenAI Function 스키마로 변환
        - Description 보강 (선택 사항)
        - self.discovered_tools에 캐싱

        Returns:
            발견된 도구 개수
        """
        if self.is_initialized:
            print("[MCPToolRouter] 이미 초기화됨, 건너뛰기")
            return len(self.discovered_tools)

        print("[MCPToolRouter] MCP 도구 자동 발견 시작...")

        try:
            # 1. UniversalMCPClient에서 모든 도구 발견
            mcp_tools = await self.universal_client.discover_all_tools()

            if not mcp_tools or len(mcp_tools) == 0:
                print("[WARN] MCP 도구를 찾을 수 없음, Fallback으로 수동 정의 사용")
                self.discovered_tools = ToolSchemaConverter.get_tavily_tools_manual()
                self.is_initialized = True
                return len(self.discovered_tools)

            # 2. OpenAI Function 스키마로 변환
            self.discovered_tools = []
            for mcp_tool in mcp_tools:
                # 기본 변환
                openai_tool = ToolSchemaConverter.mcp_to_openai(mcp_tool)

                # Description 보강 (선택 사항)
                if self.enable_description_enhancement:
                    openai_tool = ToolSchemaConverter.enhance_tool_description(openai_tool)

                self.discovered_tools.append(openai_tool)

            self.is_initialized = True

            print(f"[OK] MCPToolRouter 초기화 완료: {len(self.discovered_tools)}개 도구 준비")
            for tool in self.discovered_tools:
                tool_name = tool["function"]["name"]
                print(f"   - {tool_name}")

            return len(self.discovered_tools)

        except Exception as e:
            print(f"[ERROR] MCP 도구 자동 발견 실패: {e}")
            print("[WARN] Fallback으로 수동 정의 사용")
            self.discovered_tools = ToolSchemaConverter.get_tavily_tools_manual()
            self.is_initialized = True
            return len(self.discovered_tools)

    def _is_simple_query(self, query: str) -> bool:
        """
        간단한 질문인지 판단 (규칙 기반 필터링)

        간단한 질문은 Tool Calling을 건너뛰고 바로 답변
        → LLM 호출 1회만 (비용 절약)

        Args:
            query: 사용자 질문

        Returns:
            간단한 질문 여부
        """
        simple_patterns = [
            "안녕", "hello", "hi", "감사", "고마워", "thank",
            "잘가", "bye", "굿바이"
        ]

        query_lower = query.lower()

        # 인사말이면서 짧은 경우 (10자 이하)
        if len(query) <= 10:
            for pattern in simple_patterns:
                if pattern in query_lower:
                    return True

        return False

    async def select_and_execute_mcp_tools(
        self,
        query: str,
        local_docs: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        LLM이 MCP 도구 필요성을 판단하고 실행

        Args:
            query: 사용자 질문
            local_docs: 이미 검색된 로컬 문서 (RAG 결과)
            conversation_history: 대화 기록

        Returns:
            {
                "mcp_used": bool,               # MCP 도구 사용 여부
                "tools_used": List[str],        # 사용된 도구 목록
                "results": Dict[str, Any],      # 도구 실행 결과
                "direct_answer": Optional[str]  # 도구 없이 바로 답변 가능한 경우
            }
        """
        print(f"\n[MCPToolRouter] 도구 선택 시작: {query[:50]}...")

        # 1단계: 간단한 질문 필터링 (Tool Calling 건너뛰기)
        if self._is_simple_query(query):
            print("[MCPToolRouter] 간단한 질문 감지 → Tool Calling 건너뛰기")
            return {
                "mcp_used": False,
                "tools_used": [],
                "results": {},
                "direct_answer": None  # 직접 답변하도록 신호
            }

        # 2단계: LLM에게 MCP 도구 필요성 판단 요청
        tools_result = await self._ask_llm_for_tools(
            query,
            local_docs,
            conversation_history
        )

        # 도구 사용 불필요한 경우
        if not tools_result["tool_calls"]:
            print("[MCPToolRouter] LLM 판단: MCP 도구 불필요")
            return {
                "mcp_used": False,
                "tools_used": [],
                "results": {},
                "direct_answer": tools_result.get("direct_answer")
            }

        # 3단계: 선택된 도구 실행
        print(f"[MCPToolRouter] LLM 판단: {len(tools_result['tool_calls'])}개 도구 필요")

        results = {}
        tools_used = []

        for tool_call in tools_result["tool_calls"]:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"   → {tool_name} 실행 중...")

            try:
                result = await self.universal_client.call_tool(tool_name, tool_args)
                results[tool_name] = result
                tools_used.append(tool_name)
            except Exception as e:
                print(f"   [ERROR] {tool_name} 실행 실패: {e}")
                results[tool_name] = {"error": str(e)}

        return {
            "mcp_used": True,
            "tools_used": tools_used,
            "results": results,
            "direct_answer": None
        }

    async def _ask_llm_for_tools(
        self,
        query: str,
        local_docs: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        LLM에게 필요한 MCP 도구 선택 요청

        Args:
            query: 사용자 질문
            local_docs: 로컬 검색 결과
            conversation_history: 대화 기록

        Returns:
            {
                "tool_calls": [...],           # OpenAI tool_calls
                "direct_answer": Optional[str]  # 도구 없이 바로 답변
            }
        """
        # 시스템 프롬프트 생성
        system_prompt = self._build_tool_selection_prompt(local_docs)

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        # 대화 기록 추가 (최근 4개만)
        if conversation_history:
            messages.extend(conversation_history[-4:])

        # 현재 질문 추가
        messages.append({"role": "user", "content": query})

        # 사용 가능한 도구 목록 (자동 발견된 도구 사용)
        available_tools = self.discovered_tools

        # Fallback: 자동 발견 실패 시 수동 정의 사용
        if not available_tools or len(available_tools) == 0:
            print("[WARN] 자동 발견된 도구 없음, Fallback으로 수동 정의 사용")
            available_tools = ToolSchemaConverter.get_tavily_tools_manual()

        # OpenAI Function Calling 실행
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=available_tools,  # ✅ 자동 발견된 모든 도구 (Tavily + Brave + ...)
                tool_choice="auto",  # LLM이 자동 선택
                temperature=self.temperature
            )

            message = response.choices[0].message

            return {
                "tool_calls": message.tool_calls or [],
                "direct_answer": message.content if not message.tool_calls else None
            }

        except Exception as e:
            print(f"[ERROR] LLM Tool Selection 실패: {e}")
            return {
                "tool_calls": [],
                "direct_answer": None
            }

    def _build_tool_selection_prompt(
        self,
        local_docs: List[Dict[str, Any]]
    ) -> str:
        """
        도구 선택을 위한 시스템 프롬프트 생성

        Args:
            local_docs: 로컬 검색 결과

        Returns:
            시스템 프롬프트
        """
        # 로컬 문서 요약
        if local_docs and len(local_docs) > 0:
            docs_summary = f"로컬 문서 {len(local_docs)}개 검색 완료 (유사도 평균: {sum(d.get('score', 0) for d in local_docs) / len(local_docs):.2f})"
            docs_preview = "\n".join([
                f"  - {doc.get('metadata', {}).get('source', 'unknown')} (유사도: {doc.get('score', 0):.2f})"
                for doc in local_docs[:3]
            ])
        else:
            docs_summary = "로컬 문서 검색 결과 없음"
            docs_preview = ""

        prompt = f"""당신은 상권 분석 챗봇의 도구 선택 에이전트입니다.

**현재 상황:**
{docs_summary}
{docs_preview}

**당신의 역할:**
사용자 질문을 분석하여 추가 MCP 도구가 필요한지 판단하세요.

**판단 기준:**

1. **도구 불필요 (도구 호출하지 말 것):**
   - 로컬 문서로 충분히 답변 가능한 경우
   - 일반적인 가이드, 기본 지식 질문
   - 일상적인 대화, 인사말, 감사 인사
   - 시간과 무관한 기본 개념 설명

2. **tavily_search 필요:**
   - 최신 뉴스, 트렌드, 실시간 데이터 필요
   - "2025년", "최근", "현재", "요즘" 등 시간 키워드
   - 로컬 문서에 없는 최신 정보

3. **tavily_extract 필요:**
   - 특정 URL의 상세 내용이 필요한 경우
   - tavily_search 후 추가 분석이 필요한 경우

**중요:**
- 로컬 문서로 충분하면 도구를 호출하지 마세요
- 불필요한 웹 검색은 비용과 시간 낭비입니다
- 확실히 필요한 경우만 도구를 선택하세요
"""

        return prompt


# ============================================
# 사용 예시 및 테스트
# ============================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    from .mcp_client import TavilyMCPClient

    load_dotenv()

    async def test_mcp_tool_router():
        """MCP Tool Router 테스트"""

        print("\n" + "="*60)
        print("MCP Tool Router 테스트 시작")
        print("="*60)

        # 1. UniversalMCPClient 초기화
        universal_client = UniversalMCPClient()

        # 2. Tavily MCP 서버 등록
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            tavily_client = TavilyMCPClient(tavily_api_key)
            universal_client.register_server(
                "tavily",
                tavily_client,
                "Tavily 웹 검색 MCP 서버"
            )

            # 도구 발견
            await universal_client.discover_all_tools()
        else:
            print("⚠️  TAVILY_API_KEY 없음")

        # 3. MCPToolRouter 초기화
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY 필요")
            return

        router = MCPToolRouter(
            openai_api_key=openai_api_key,
            universal_client=universal_client
        )

        # 4. 테스트 시나리오
        test_cases = [
            {
                "query": "안녕하세요",
                "local_docs": [],
                "expected": "도구 불필요 (인사말)"
            },
            {
                "query": "카페 창업 시 고려사항은?",
                "local_docs": [
                    {"content": "카페 창업 가이드...", "score": 0.85, "metadata": {"source": "guide.pdf"}}
                ],
                "expected": "도구 불필요 (로컬 문서 충분)"
            },
            {
                "query": "2025년 강남 상권 트렌드는?",
                "local_docs": [
                    {"content": "상권 분석 기초...", "score": 0.65, "metadata": {"source": "basic.pdf"}}
                ],
                "expected": "tavily_search 필요 (최신 정보)"
            }
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"테스트 {i}: {test['query']}")
            print(f"예상: {test['expected']}")
            print(f"{'='*60}")

            result = await router.select_and_execute_mcp_tools(
                query=test["query"],
                local_docs=test["local_docs"]
            )

            print(f"\n결과:")
            print(f"  - MCP 사용: {result['mcp_used']}")
            print(f"  - 사용된 도구: {result['tools_used']}")
            if result['direct_answer']:
                print(f"  - 직접 답변: {result['direct_answer'][:100]}...")

            if result['results']:
                for tool_name, tool_result in result['results'].items():
                    print(f"  - {tool_name} 결과: {str(tool_result)[:100]}...")

    # 테스트 실행
    asyncio.run(test_mcp_tool_router())
