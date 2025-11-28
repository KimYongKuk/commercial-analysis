# MCP 아키텍처 완전 가이드

> **AI 기반 상권 분석 챗봇 프로젝트의 MCP 통합 전략**
>
> 작성일: 2025년
> 대상: 백엔드/AI 개발자, MCP 학습자

---

## 📚 목차

1. [MCP 개요 및 개념](#1-mcp-개요-및-개념)
2. [핵심 아키텍처 분석](#2-핵심-아키텍처-분석)
   - 2.1 UniversalMCPClient
   - **2.2 도구 자동 발견 (Auto-Discovery)** ⭐ NEW!
   - 2.3 MCPToolRouter
   - 2.4 RAGChain
3. [코드 흐름 상세 분석](#3-코드-흐름-상세-분석)
4. [실전 예제 & 베스트 프랙티스](#4-실전-예제--베스트-프랙티스)

---

## 1. MCP 개요 및 개념

### 1.1 MCP(Model Context Protocol)란?

**MCP**는 LLM(대형 언어 모델)이 외부 도구 및 데이터 소스에 접근할 수 있도록 하는 **표준화된 프로토콜**입니다.

#### 핵심 개념
- **클라이언트-서버 아키텍처**: LLM 애플리케이션(클라이언트)이 다양한 MCP 서버와 통신
- **도구 추상화**: 웹 검색, 데이터베이스 조회, API 호출 등을 "도구"로 추상화
- **표준 인터페이스**: 모든 MCP 서버는 동일한 프로토콜로 통신 (JSON-RPC 2.0 기반)

---

### 1.2 왜 MCP를 사용하는가?

#### 기존 방식의 문제점

**문제 1: 정적인 지식 베이스**
```python
# ❌ 기존 RAG 방식
# - 로컬 문서만 검색 가능
# - 최신 정보 반영 불가능
# - 2025년 최신 트렌드? → 답변 불가

retriever.search("2025년 강남 상권 트렌드")
# → 2023년 문서만 반환... 😢
```

**문제 2: 외부 API 하드코딩**
```python
# ❌ 기존 방식
import requests

def search_web(query):
    # Tavily API 직접 호출
    response = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query}
    )
    return response.json()

# 문제점:
# 1. API 변경 시 코드 수정 필요
# 2. 새 검색 엔진 추가 시 코드 중복
# 3. 도구 선택 로직이 복잡해짐
```

#### MCP 방식의 장점

**✅ 해결책: MCP 프로토콜**
```python
# ✅ MCP 방식
# 1. 설정 파일로 서버 등록
# mcp_config.json
{
  "mcpServers": {
    "tavily": {"url": "https://mcp.tavily.com/..."},
    "brave": {"command": "npx", "args": ["@smithery/cli", "run", "brave"]}
  }
}

# 2. LLM이 자동으로 필요한 도구 선택
router = MCPToolRouter(openai_api_key, universal_client)
result = await router.select_and_execute_mcp_tools(
    query="2025년 강남 상권 트렌드",
    local_docs=[...]
)

# LLM이 판단: "tavily_search 도구가 필요하구나!"
# → 자동으로 Tavily MCP 서버 호출
# → 최신 웹 검색 결과 반환
```

**장점 요약**
1. **유연성**: 새 도구 추가 = 설정 파일만 수정
2. **자동화**: LLM이 필요한 도구를 자동 선택
3. **확장성**: 100개의 도구도 동일한 인터페이스로 관리
4. **최신성**: 웹 검색으로 실시간 정보 접근

---

### 1.3 프로젝트에서의 MCP 역할

우리 프로젝트는 **RAG + MCP 하이브리드 아키텍처**를 사용합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                     사용자 질문                              │
│              "2025년 강남 카페 창업 전망은?"                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │         RAG 파이프라인 시작            │
        └───────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌───────────────┐       ┌──────────────┐
        │  로컬 문서 검색 │       │ MCP Tool     │
        │   (벡터 DB)    │       │ Router 실행  │
        │               │       │              │
        │ • 카페 창업    │       │ LLM이 판단:  │
        │   가이드.pdf   │       │ "최신 정보   │
        │ • 상권 분석    │       │  필요!"      │
        │   기초.pdf     │       │              │
        └───────────────┘       └──────────────┘
                │                       │
                │                       ▼
                │               ┌──────────────┐
                │               │ Tavily MCP   │
                │               │ 서버 호출    │
                │               │              │
                │               │ • 웹 검색    │
                │               │ • 최신 뉴스  │
                │               └──────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                ┌───────────────────────┐
                │  LLM 답변 생성        │
                │  (로컬 + 웹 결합)     │
                └───────────────────────┘
                            │
                            ▼
                    "카페 창업은..."
```

**핵심 전략**
- **로컬 문서**: 기본 지식, 가이드 (항상 검색)
- **MCP 도구**: 최신 정보, 실시간 데이터 (필요 시 LLM이 자동 선택)
- **하이브리드**: 두 결과를 결합하여 최적의 답변 생성

---

## 2. 핵심 아키텍처 분석

프로젝트의 MCP 구현은 **3개의 핵심 클래스**로 구성됩니다.

```
┌──────────────────────────────────────────────────────────┐
│                  MCP 아키텍처 구조                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  UniversalMCPClient                            │     │
│  │  • 여러 MCP 서버 통합 관리                      │     │
│  │  • 도구 발견 (discover_all_tools)              │     │
│  │  • 도구 실행 디스패치 (call_tool)              │     │
│  └────────────────────────────────────────────────┘     │
│                        ▲                                │
│                        │                                │
│  ┌────────────────────────────────────────────────┐     │
│  │  MCPToolRouter                                 │     │
│  │  • LLM 기반 도구 선택                           │     │
│  │  • 간단한 질문 필터링                           │     │
│  │  • Tool Calling 실행                           │     │
│  └────────────────────────────────────────────────┘     │
│                        ▲                                │
│                        │                                │
│  ┌────────────────────────────────────────────────┐     │
│  │  RAGChain                                      │     │
│  │  • RAG + MCP 통합 파이프라인                    │     │
│  │  • 3가지 생성 전략 (로컬/MCP/하이브리드)        │     │
│  │  • 스트리밍 지원                                │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

### 2.1 UniversalMCPClient: 범용 MCP 클라이언트

**역할**: 여러 MCP 서버를 통합 관리하는 허브

#### 핵심 기능

**1) JSON 설정 파일로 초기화**

```python
# rag/mcp_client_new.py (38~116줄)

class UniversalMCPClient:
    """
    여러 MCP 서버를 통합 관리하는 범용 클라이언트

    - 여러 MCP 서버 등록 (Tavily, Brave, 커스텀 서버 등)
    - 도구 이름으로 자동 디스패치
    - 모든 MCP 서버의 도구 목록 통합 관리
    """

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
                        },
                        "brave": {
                            "command": "npx",
                            "args": ["@smithery/cli", "run", "brave"]
                        }
                    }
                }

        Returns:
            초기화된 UniversalMCPClient 인스턴스
        """
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
        for server_name, server_config in config["mcpServers"].items():
            # 환경변수 치환
            if "url" in server_config:
                server_config["url"] = replace_env_vars(server_config["url"])

            # FastMCP Client 생성
            fastmcp_client = Client({"mcpServers": {server_name: server_config}})

            instance.mcp_servers[server_name] = {
                "client": fastmcp_client,
                "tools": [],
                "config": server_config
            }

        return instance
```

**실제 사용 예시**
```python
# mcp_config.json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
    }
  }
}

# 초기화
client = UniversalMCPClient.from_config("mcp_config.json")
# → 환경변수 TAVILY_API_KEY를 자동으로 URL에 삽입
# → FastMCP 클라이언트 생성
```

---

**2) 모든 MCP 서버의 도구 발견**

```python
# rag/mcp_client_new.py (139~191줄)

async def discover_all_tools(self) -> List[Dict[str, Any]]:
    """
    모든 등록된 MCP 서버의 도구 목록 수집

    Returns:
        통합 도구 목록
        [
            {
                "server": "tavily",
                "name": "tavily_search",
                "description": "실시간 웹 검색",
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
            async with client:
                tools = await client.list_tools()

            # 도구에 서버 정보 추가
            for tool in tools:
                tool_dict = {
                    "name": getattr(tool, 'name', 'unknown'),
                    "description": getattr(tool, 'description', ''),
                    "inputSchema": getattr(tool, 'inputSchema', {}),
                    "server": server_name  # 어느 서버에 속하는지 표시
                }
                all_tools.append(tool_dict)

            # 서버에 도구 목록 캐싱
            server_info["tools"] = all_tools

            print(f"[UniversalMCPClient] {server_name}: {len(tools)}개 도구 발견")

        except Exception as e:
            print(f"[ERROR] {server_name} 도구 목록 조회 실패: {e}")

    return all_tools
```

**실제 동작 예시**
```python
# main.py (55~61줄)
if rag_chain.enable_mcp and rag_chain.universal_client:
    print("[RAG] MCP 도구 목록 발견 중...")
    tools = await rag_chain.universal_client.discover_all_tools()
    print(f"[OK] {len(tools)}개 MCP 도구 발견 완료")

# 출력:
# [UniversalMCPClient] tavily: 2개 도구 발견
# [OK] 2개 MCP 도구 발견 완료
#   - tavily_search
#   - tavily_extract
```

---

**3) 동적 도구 디스패치**

```python
# rag/mcp_client_new.py (193~242줄)

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

    # 1. 도구가 어느 서버에 속하는지 찾기
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

    # 2. 해당 서버의 클라이언트로 도구 호출
    client = self.mcp_servers[target_server]["client"]

    try:
        async with client:
            result = await client.call_tool(tool_name, tool_args)
            # FastMCP는 ToolResult 객체 반환, .data 속성에 실제 데이터
            result_data = result.data if hasattr(result, 'data') else result

        print(f"[OK] 도구 실행 완료: {tool_name}")
        return result_data

    except Exception as e:
        print(f"[ERROR] 도구 실행 실패: {e}")
        raise
```

**동작 흐름**
```python
# 예시: tavily_search 호출
await client.call_tool(
    "tavily_search",
    {"query": "강남 카페 트렌드", "max_results": 5}
)

# 내부 동작:
# 1. "tavily_search"가 어느 서버에 속하는지 검색
#    → "tavily" 서버에 속함
# 2. tavily 서버의 FastMCP 클라이언트 가져오기
# 3. client.call_tool("tavily_search", {...}) 실행
# 4. 결과 반환
```

---

### 2.2 도구 자동 발견 (Auto-Discovery)

**역할**: MCP 서버의 모든 도구를 자동으로 발견하고 OpenAI Function 스키마로 변환

#### 왜 자동 발견이 필요한가?

**기존 방식 (수동 정의)의 문제점:**
```python
# ❌ 수동으로 Tavily 도구만 정의
available_tools = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web...",
            "parameters": {...}
        }
    }
]

# 문제점:
# 1. Brave 도구는 사용 불가능 (정의 안 됨)
# 2. 새 서버 추가 시마다 수동으로 도구 정의 필요
# 3. 도구 스키마가 변경되면 코드 수정 필요
# 4. 확장성 없음
```

**자동 발견 방식의 장점:**
```python
# ✅ 모든 MCP 서버의 도구를 자동 발견
await router.initialize()

# 내부 동작:
# 1. mcp_config.json에서 등록된 모든 서버 탐색
# 2. 각 서버의 list_tools() 호출
# 3. MCP 스키마 → OpenAI Function 스키마 변환
# 4. Description 자동 보강 (선택 사항)
# 5. self.discovered_tools에 캐싱

# 결과: Tavily 4개 + Brave 6개 = 총 10개 도구 자동 발견!
# → LLM이 10개 중에서 자동 선택
```

**장점 요약:**
- ✅ **유연성**: 설정 파일만 수정하면 새 도구 자동 추가
- ✅ **확장성**: 100개 도구도 동일한 로직으로 처리
- ✅ **자동화**: 스키마 변환 자동화
- ✅ **유지보수**: 도구 스펙 변경 시 코드 수정 불필요

---

#### 자동 발견 구현 (3단계)

**1단계: MCP 스키마 → OpenAI Function 스키마 변환**

```python
# rag/mcp_client_new.py (252~288줄)

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
```

**핵심 변환 로직:**
- `mcp_tool["inputSchema"]` → `openai_tool["function"]["parameters"]`
- `mcp_tool["name"]` → `openai_tool["function"]["name"]`
- `mcp_tool["description"]` → `openai_tool["function"]["description"]`

---

**2단계: Description 자동 보강 (선택 사항)**

```python
# rag/mcp_client_new.py (290~326줄)

@staticmethod
def enhance_tool_description(openai_tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenAI Function 스키마의 description을 보강

    특정 도구에 대해 LLM이 더 잘 이해할 수 있도록 상세한 가이드 추가
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
```

**왜 Description 보강이 중요한가?**

LLM은 도구 설명만 보고 선택 판단을 합니다. 상세한 가이드를 추가하면:
- ✅ 불필요한 웹 검색 방지 (비용 절감)
- ✅ 더 정확한 도구 선택
- ✅ 로컬 문서 우선 활용

---

**3단계: MCPToolRouter.initialize() - 도구 자동 발견 및 캐싱**

```python
# rag/mcp_client_new.py (410~464줄)

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
```

**핵심 특징:**
1. **Lazy Loading**: 첫 요청 시에만 실행 (서버 시작 속도 향상)
2. **캐싱**: `self.discovered_tools`에 저장 → 두 번째 요청부터는 재사용
3. **Fallback**: 자동 발견 실패 시 수동 정의로 대체
4. **멱등성**: `is_initialized` 플래그로 중복 실행 방지

---

**동작 흐름**

```python
# 서버 시작 시
rag_chain = RAGChain(...)
# → MCPToolRouter 생성, 하지만 도구 발견 안 함 (빠른 시작)

# 첫 사용자 요청
result = await rag_chain.run("2025년 강남 트렌드")

# rag_chain.py (272~277줄)
if not self.mcp_initialized:
    print("[RAG] 첫 요청 감지, MCP 도구 자동 발견 시작...")
    tool_count = await self.mcp_tool_router.initialize()  # ⭐ 여기서 발견!
    self.mcp_initialized = True
    print(f"[OK] MCP 도구 발견 완료: {tool_count}개")

# 출력:
# [MCPToolRouter] MCP 도구 자동 발견 시작...
# [UniversalMCPClient] tavily: 4개 도구 발견
# [UniversalMCPClient] brave: 6개 도구 발견
# [OK] MCPToolRouter 초기화 완료: 10개 도구 준비
#    - tavily_search
#    - tavily_extract
#    - brave_web_search
#    - brave_local_search
#    ...

# 두 번째 요청
result = await rag_chain.run("카페 창업 가이드")
# → 이미 초기화됨, 캐시된 도구 사용 (재발견 안 함!)
```

---

**자동 발견 vs 수동 정의 비교**

| 항목 | 수동 정의 | 자동 발견 |
|------|----------|-----------|
| 도구 추가 | 코드 수정 필요 | 설정 파일만 수정 |
| Brave 지원 | ❌ 불가능 | ✅ 자동 지원 |
| 확장성 | 낮음 (하드코딩) | 높음 (동적) |
| 유지보수 | 도구 변경 시 코드 수정 | 자동 반영 |
| 초기화 속도 | 즉시 | 첫 요청 시 (Lazy) |
| Fallback | - | 실패 시 수동 정의 사용 |

---

### 2.3 MCPToolRouter: LLM 기반 도구 자동 선택

**역할**: LLM이 사용자 질문을 분석하여 필요한 MCP 도구를 자동으로 선택하고 실행

#### 핵심 개념: "언제 웹 검색이 필요한가?"

**문제**: 모든 질문에 웹 검색을 하면?
- ❌ 비용 증가 (Tavily API 호출 = 돈)
- ❌ 속도 느림 (웹 검색 = 2~5초)
- ❌ 불필요한 데이터 (로컬 문서로 충분한 질문도 많음)

**해결책**: LLM이 판단하게 하자!

```python
# rag/mcp_client_new.py (431~507줄)

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
    # 1단계: 간단한 질문 필터링 (Tool Calling 건너뛰기)
    if self._is_simple_query(query):
        print("[MCPToolRouter] 간단한 질문 감지 → Tool Calling 건너뛰기")
        return {
            "mcp_used": False,
            "tools_used": [],
            "results": {},
            "direct_answer": None
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

        try:
            result = await self.universal_client.call_tool(tool_name, tool_args)
            results[tool_name] = result
            tools_used.append(tool_name)
        except Exception as e:
            results[tool_name] = {"error": str(e)}

    return {
        "mcp_used": True,
        "tools_used": tools_used,
        "results": results,
        "direct_answer": None
    }
```

---

#### 2단계 필터링 전략

**필터 1: 규칙 기반 (간단한 질문)**

```python
# rag/mcp_client_new.py (403~429줄)

def _is_simple_query(self, query: str) -> bool:
    """
    간단한 질문인지 판단 (규칙 기반 필터링)

    간단한 질문은 Tool Calling을 건너뛰고 바로 답변
    → LLM 호출 1회만 (비용 절약)
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
```

**예시**
```python
# ✅ 필터링됨 (Tool Calling 건너뛰기)
_is_simple_query("안녕하세요")      # True → 바로 답변
_is_simple_query("감사합니다")      # True → 바로 답변

# ❌ 필터링 안 됨 (LLM 판단 필요)
_is_simple_query("강남 카페 창업") # False → 2단계로
```

---

**필터 2: LLM 기반 (OpenAI Function Calling)**

```python
# rag/mcp_client_new.py (509~567줄)

async def _ask_llm_for_tools(
    self,
    query: str,
    local_docs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    LLM에게 필요한 MCP 도구 선택 요청
    """
    # 시스템 프롬프트 생성
    system_prompt = self._build_tool_selection_prompt(local_docs)

    # 메시지 구성
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history[-4:])  # 최근 4개만

    messages.append({"role": "user", "content": query})

    # ✅ 자동 발견된 도구 목록 사용 (Tavily + Brave + ...)
    available_tools = self.discovered_tools

    # Fallback: 자동 발견 실패 시 수동 정의 사용
    if not available_tools or len(available_tools) == 0:
        print("[WARN] 자동 발견된 도구 없음, Fallback으로 수동 정의 사용")
        available_tools = ToolSchemaConverter.get_tavily_tools_manual()

    # OpenAI Function Calling 실행
    response = self.client.chat.completions.create(
        model=self.model_name,
        messages=messages,
        tools=available_tools,  # ✅ 자동 발견된 모든 도구 (Tavily + Brave + ...)
        tool_choice="auto",     # LLM이 자동 선택
        temperature=0.3         # 낮은 temperature = 일관된 선택
    )

    message = response.choices[0].message

    return {
        "tool_calls": message.tool_calls or [],
        "direct_answer": message.content if not message.tool_calls else None
    }
```

**시스템 프롬프트 (핵심 로직)**

```python
# rag/mcp_client_new.py (569~625줄)

def _build_tool_selection_prompt(
    self,
    local_docs: List[Dict[str, Any]]
) -> str:
    """도구 선택을 위한 시스템 프롬프트 생성"""

    # 로컬 문서 요약
    if local_docs and len(local_docs) > 0:
        docs_summary = f"로컬 문서 {len(local_docs)}개 검색 완료"
    else:
        docs_summary = "로컬 문서 검색 결과 없음"

    prompt = f"""당신은 상권 분석 챗봇의 도구 선택 에이전트입니다.

**현재 상황:**
{docs_summary}

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
```

---

**실제 동작 예시**

```python
# 테스트 케이스 1: 인사말
query = "안녕하세요"
local_docs = []

result = await router.select_and_execute_mcp_tools(query, local_docs)
# → 1단계 필터: True (간단한 질문)
# → Tool Calling 건너뛰기
# → mcp_used = False

# 테스트 케이스 2: 기본 지식 질문
query = "카페 창업 시 고려사항은?"
local_docs = [
    {"content": "카페 창업 가이드...", "score": 0.85}
]

result = await router.select_and_execute_mcp_tools(query, local_docs)
# → 1단계 필터: False (복잡한 질문)
# → 2단계: LLM 판단
# → 시스템 프롬프트: "로컬 문서 1개 검색 완료 (유사도 0.85)"
# → LLM: "로컬 문서로 충분하네. 도구 호출 불필요!"
# → mcp_used = False

# 테스트 케이스 3: 최신 정보 필요
query = "2025년 강남 상권 트렌드는?"
local_docs = [
    {"content": "상권 분석 기초...", "score": 0.65}
]

result = await router.select_and_execute_mcp_tools(query, local_docs)
# → 1단계 필터: False
# → 2단계: LLM 판단
# → 시스템 프롬프트: "로컬 문서 1개 (유사도 0.65, 낮음)"
# → LLM: "2025년이라는 키워드! tavily_search 필요!"
# → tool_calls = [{"function": {"name": "tavily_search", ...}}]
# → 3단계: tavily_search 실행
# → mcp_used = True, tools_used = ["tavily_search"]
```

---

### 2.3 RAGChain: RAG + MCP 통합 파이프라인

**역할**: 로컬 RAG와 MCP 도구를 결합하여 최적의 답변 생성

#### 3가지 생성 전략

```python
# rag/rag_chain.py (595~678줄)

async def run(
    self,
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """RAG 파이프라인 실행 (MCP Tool Router 통합)"""

    # 1. 로컬 문서 검색 (항상 실행)
    print(f"[DOCS] 1단계: 로컬 문서 검색 (Top-{top_k})...")
    local_docs = self.retriever.search(query, top_k=top_k)

    # 2. MCP Tool Router 실행 (LLM이 판단)
    print(f"[MCP] 2단계: LLM 기반 도구 선택 및 실행...")
    mcp_result = await self._execute_mcp_tools(query, local_docs)

    # 3. 전략 선택 및 실행
    if mcp_result['mcp_used'] and mcp_result['results']:
        # Case A: MCP 도구 사용됨
        if local_docs:
            # 전략 1: 하이브리드 (로컬 + MCP)
            return self._generate_hybrid(
                local_docs,
                mcp_result['results'],
                query,
                conversation_history
            )
        else:
            # 전략 2: MCP만
            return self._generate_from_mcp(
                mcp_result['results'],
                query,
                conversation_history
            )

    elif local_docs:
        # 전략 3: 로컬 문서만
        return self._generate_from_docs(local_docs, query, conversation_history)

    else:
        # 전략 4: 정보 없음 → LLM 일반 지식
        return self._generate_general_response(query, conversation_history)
```

---

**전략 1: 로컬 문서만 사용 (기존 RAG)**

```python
# rag/rag_chain.py (286~338줄)

def _generate_from_docs(
    self,
    local_docs: List[Dict[str, Any]],
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    로컬 문서만 사용하여 답변 생성 (기존 RAG 로직)
    """
    print("[GENERATE] 전략: 로컬 문서만 사용 (RAG)")

    # 프롬프트 생성
    messages = self.create_prompt(query, local_docs, conversation_history)

    # LLM 호출
    response = self.client.chat.completions.create(
        model=self.model_name,
        messages=messages,
        temperature=self.temperature,
        max_tokens=self.max_tokens
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": local_docs,
        "web_search_used": False,
        "query": query,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
    }
```

**프롬프트 구조**
```python
# rag/rag_chain.py (148~191줄)

def create_prompt(
    self,
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """RAG 프롬프트 생성 (로컬 문서 전용)"""

    # 시스템 프롬프트
    system_prompt = """당신은 상권 분석 및 창업 컨설팅 전문가입니다.

답변 전략:
1. **부동산/상권 관련 질문**: 제공된 참고 문서를 기반으로 전문적이고 구체적인 답변을 제공하세요.
   - 참고 문서의 내용을 자연스럽게 설명하고, 필요시 출처를 언급하세요.

2. **일상적인 대화/인사**: 참고 자료와 무관하게 자연스럽고 친근하게 응답하세요.
"""

    # 검색된 문서 포맷팅
    context = self.retriever.format_documents_for_prompt(retrieved_docs)

    # 사용자 프롬프트
    user_prompt = f"""[참고 문서]
{context}

[사용자 질문]
{query}

위 참고 문서를 바탕으로 사용자의 질문에 답변해주세요.
"""

    # 메시지 구성
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_prompt})

    return messages
```

---

**전략 2: MCP 도구 결과만 사용**

```python
# rag/rag_chain.py (377~452줄)

def _generate_from_mcp(
    self,
    mcp_results: Dict[str, Any],
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """MCP 도구 결과만 사용하여 답변 생성"""

    print("[GENERATE] 전략: MCP 도구 결과만 사용")

    # MCP 결과를 컨텍스트로 변환
    mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=3)

    # 시스템 프롬프트
    system_prompt = """당신은 상권 분석 전문가입니다.
웹 검색 결과를 기반으로 최신 정보를 반영한 전문적인 답변을 제공하세요.
"""

    # 사용자 프롬프트
    user_prompt = f"""[MCP 도구 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위 검색 결과를 바탕으로 사용자의 질문에 답변해주세요.
"""

    # 메시지 구성 및 LLM 호출
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_prompt})

    response = self.client.chat.completions.create(
        model=self.model_name,
        messages=messages,
        temperature=self.temperature,
        max_tokens=self.max_tokens
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [],
        "mcp_results": mcp_results,
        "web_search_used": True,
        "query": query
    }
```

**MCP 결과 포맷팅**
```python
# rag/rag_chain.py (340~375줄)

def _format_mcp_results_for_prompt(
    self,
    mcp_results: Dict[str, Any],
    max_results_per_tool: int = 3
) -> str:
    """MCP 도구 실행 결과를 프롬프트용 텍스트로 포맷팅"""

    formatted_parts = []

    for tool_name, tool_result in mcp_results.items():
        formatted_parts.append(f"[{tool_name} 결과]")

        # Tavily/Brave 검색 결과 형식 처리
        if isinstance(tool_result, dict) and 'results' in tool_result:
            results = tool_result.get('results', [])[:max_results_per_tool]
            for i, item in enumerate(results, 1):
                text = f"\n{i}. 제목: {item.get('title', 'N/A')}\n"
                text += f"   URL: {item.get('url', 'N/A')}\n"
                text += f"   내용: {item.get('content', 'N/A')}"
                formatted_parts.append(text)
        else:
            # 기타 결과 형식
            formatted_parts.append(str(tool_result)[:500])

    return "\n\n---\n\n".join(formatted_parts)
```

---

**전략 3: 하이브리드 (로컬 + MCP)**

```python
# rag/rag_chain.py (454~537줄)

def _generate_hybrid(
    self,
    local_docs: List[Dict[str, Any]],
    mcp_results: Dict[str, Any],
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """로컬 문서 + MCP 도구 결과 결합하여 답변 생성"""

    print("[GENERATE] 전략: 하이브리드 (로컬 + MCP)")

    # 로컬 문서 컨텍스트
    local_context = self.retriever.format_documents_for_prompt(local_docs)

    # MCP 결과 컨텍스트
    mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=2)

    # 시스템 프롬프트
    system_prompt = """당신은 상권 분석 전문가입니다.
로컬 지식 데이터베이스와 최신 웹 검색 결과를 모두 활용하여 전문적인 답변을 제공하세요.
"""

    # 사용자 프롬프트
    user_prompt = f"""[내부 참고 문서]
{local_context}

[최신 MCP 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위의 내부 참고 문서와 최신 검색 결과를 종합하여 사용자의 질문에 답변해주세요.
"""

    # LLM 호출
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_prompt})

    response = self.client.chat.completions.create(
        model=self.model_name,
        messages=messages,
        temperature=self.temperature,
        max_tokens=self.max_tokens
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": local_docs,
        "mcp_results": mcp_results,
        "web_search_used": True,
        "query": query
    }
```

**하이브리드 전략의 장점**
- ✅ **기본 지식 + 최신 정보** 결합
- ✅ **출처 다양화** (로컬 문서 + 웹 검색)
- ✅ **신뢰성 향상** (여러 소스 크로스 체크)

---

## 3. 코드 흐름 상세 분석

### 3.1 전체 요청 흐름 (End-to-End)

```
사용자 → 프론트엔드 → FastAPI → RAGChain → LLM → 사용자

1. 사용자가 질문 입력
   "2025년 강남 카페 창업 전망은?"

2. 프론트엔드 (React)
   POST /api/rag-chat-stream
   {
     "message": "2025년 강남 카페 창업 전망은?",
     "conversation_history": [...]
   }

3. FastAPI 엔드포인트 (main.py:398~429)
   @app.post("/api/rag-chat-stream")
   async def rag_chat_stream(request: ChatRequest):
       return StreamingResponse(
           stream_rag_response(...),
           media_type="text/event-stream"
       )

4. RAG 체인 가져오기 (main.py:42~64)
   rag = await get_rag_chain()
   # → Lazy Loading으로 첫 요청 시 초기화
   # → MCP Tool Router도 함께 초기화

5. RAG 파이프라인 실행 (rag_chain.py:595~678)
   async for chunk in rag.stream_run(
       query=query,
       conversation_history=conversation_history,
       top_k=3
   ):
       yield chunk

6. 단계별 실행:

   [1단계] 로컬 문서 검색
   local_docs = self.retriever.search(query, top_k=3)
   # → 벡터 DB (Chroma)에서 유사도 검색
   # → 상위 3개 문서 반환

   [2단계] MCP Tool Router 실행
   mcp_result = await self._execute_mcp_tools(query, local_docs)

   내부 동작:
   2-1. 간단한 질문 필터링
        if _is_simple_query(query):  # "안녕" 같은 인사?
            return {"mcp_used": False}

   2-2. LLM 기반 도구 선택
        tools_result = await _ask_llm_for_tools(query, local_docs)

        # OpenAI Function Calling
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "도구 선택 프롬프트"},
                {"role": "user", "content": query}
            ],
            tools=[tavily_search, tavily_extract],  # 사용 가능한 도구
            tool_choice="auto"  # LLM이 자동 선택
        )

        # LLM 응답:
        # tool_calls = [
        #     {
        #         "function": {
        #             "name": "tavily_search",
        #             "arguments": '{"query": "2025년 강남 카페", "max_results": 5}'
        #         }
        #     }
        # ]

   2-3. 선택된 도구 실행
        for tool_call in tool_calls:
            tool_name = "tavily_search"
            tool_args = {"query": "2025년 강남 카페", "max_results": 5}

            result = await universal_client.call_tool(tool_name, tool_args)
            # → Tavily MCP 서버 호출
            # → 웹 검색 결과 반환

   [3단계] 전략 선택 및 답변 생성

   조건 분기:
   if mcp_result['mcp_used'] and local_docs:
       # 하이브리드 전략
       yield {"type": "sources", "content": local_docs}
       yield {"type": "mcp_results", "content": mcp_results}

       async for chunk in _stream_hybrid(...):
           yield {"type": "answer", "content": chunk}

   elif mcp_result['mcp_used']:
       # MCP만
       async for chunk in _stream_from_mcp(...):
           yield chunk

   elif local_docs:
       # 로컬만
       async for chunk in _stream_from_docs(...):
           yield chunk

   else:
       # 일반 대화
       async for chunk in _stream_general_response(...):
           yield chunk

7. 스트리밍 응답 (SSE)

   # 프론트엔드로 실시간 전송
   data: {"event": "sources", "sources": [...]}
   data: {"event": "mcp_results", "mcp_results": {...}}
   data: {"event": "answer", "content": "2025년"}
   data: {"event": "answer", "content": " 강남"}
   data: {"event": "answer", "content": " 카페"}
   ...
   data: {"event": "done"}

8. 프론트엔드 렌더링
   - sources 수신 → 참고 문서 표시
   - mcp_results 수신 → 웹 검색 결과 표시
   - answer 청크 수신 → 타이핑 효과로 표시
```

---

### 3.2 MCP 도구 선택 로직 상세

**시나리오 1: 인사말 ("안녕하세요")**

```python
# 입력
query = "안녕하세요"
local_docs = []

# 1단계: 규칙 기반 필터
_is_simple_query("안녕하세요")
# → len("안녕하세요") = 5 (10자 이하)
# → "안녕" in query → True
# → return True

# 결과
{
    "mcp_used": False,
    "tools_used": [],
    "results": {},
    "direct_answer": None
}

# LLM 호출 횟수: 0회 (비용 절약!)
```

---

**시나리오 2: 기본 지식 질문 ("카페 창업 가이드")**

```python
# 입력
query = "카페 창업 시 고려사항은?"
local_docs = [
    {
        "content": "카페 창업 시에는 입지, 메뉴, 인테리어...",
        "score": 0.85,
        "metadata": {"source": "startup_guide.pdf"}
    }
]

# ========================================
# [1단계] 로컬 문서 검색 (이미 완료)
# ========================================
# retriever.search(query, top_k=3)
# → 유사도 0.85로 관련 문서 발견

# ========================================
# [2단계] MCPToolRouter - 도구 선택
# ========================================

# 2-1. 규칙 기반 필터
_is_simple_query("카페 창업 시 고려사항은?")
# → 복잡한 질문 → False (통과)

# 2-2. LLM 기반 도구 선택 ⭐ (LLM 호출 1회)
_ask_llm_for_tools(query, local_docs)

# 시스템 프롬프트:
"""
당신은 도구 선택 에이전트입니다.

현재 상황:
로컬 문서 1개 검색 완료 (유사도 평균: 0.85)
  - startup_guide.pdf (유사도: 0.85)

판단 기준:
1. 도구 불필요: 로컬 문서로 충분히 답변 가능한 경우
2. tavily_search 필요: 최신 정보 필요, "2025년" 키워드 등
"""

# 사용자 메시지:
"카페 창업 시 고려사항은?"

# LLM 판단:
# → "로컬 문서 유사도가 0.85로 높고, 기본 지식 질문이네."
# → "웹 검색 불필요!"
# → tool_calls = None

# 2-3. MCPToolRouter 결과
{
    "mcp_used": False,
    "tools_used": [],
    "results": {},
    "direct_answer": None
}

# ========================================
# [3단계] RAGChain - 답변 생성 (로컬 문서만 사용)
# ========================================

# mcp_used = False이므로 _generate_from_docs() 호출
# ⭐ LLM 호출 2회

# 프롬프트 구성:
messages = [
    {
        "role": "system",
        "content": "당신은 상권 분석 전문가입니다..."
    },
    {
        "role": "user",
        "content": """
[참고 문서]
startup_guide.pdf: 카페 창업 시에는 입지, 메뉴, 인테리어...

[사용자 질문]
카페 창업 시 고려사항은?
"""
    }
]

# LLM 호출 (gpt-4o-mini, temperature=0.7)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)

# 답변:
"카페 창업 시에는 다음과 같은 사항을 고려해야 합니다:
1. 입지: 유동인구가 많은 곳...
2. 메뉴 구성: 차별화된 메뉴...
3. 인테리어: 컨셉에 맞는..."

# ========================================
# 최종 결과
# ========================================
{
    "answer": "카페 창업 시에는...",
    "sources": [{"content": "...", "score": 0.85}],
    "web_search_used": False,
    "tools_used": [],
    "usage": {
        "total_tokens": 1200
    }
}

# ========================================
# 총 비용 분석
# ========================================
# LLM 호출: 2회
#   1. 도구 선택 (gpt-4o-mini, ~500 토큰) = $0.0001
#   2. 답변 생성 (gpt-4o-mini, ~1200 토큰) = $0.0002
# MCP 서버 호출: 0회
# 총 비용: ~$0.0003
```

---

**시나리오 3: 최신 정보 필요 ("2025년 강남 트렌드")**

```python
# 입력
query = "2025년 강남 카페 창업 전망은?"
local_docs = [
    {
        "content": "상권 분석의 기초는...",
        "score": 0.65,  # 유사도 낮음
        "metadata": {"source": "basic_guide.pdf"}
    }
]

# ========================================
# [1단계] 로컬 문서 검색 (이미 완료)
# ========================================
# retriever.search(query, top_k=3)
# → 유사도 0.65로 약간 관련 있는 문서 발견 (충분하지 않음)

# ========================================
# [2단계] MCPToolRouter - 도구 선택
# ========================================

# 2-1. 규칙 기반 필터
_is_simple_query("2025년 강남 카페 창업 전망은?")
# → False (통과)

# 2-2. LLM 기반 도구 선택 ⭐ (LLM 호출 1회)
_ask_llm_for_tools(query, local_docs)

# ✅ 자동 발견된 도구 목록 전달
# available_tools = self.discovered_tools
# → Tavily 4개 + Brave 6개 = 총 10개 도구
#    - tavily_search, tavily_extract, ...
#    - brave_web_search, brave_local_search, ...

# 시스템 프롬프트:
"""
현재 상황:
로컬 문서 1개 검색 완료 (유사도 평균: 0.65)  ← 낮은 유사도!
  - basic_guide.pdf (유사도: 0.65)

판단 기준:
2. tavily_search 필요:
   - "2025년", "최근", "현재" 등 시간 키워드  ← "2025년" 감지!
   - 로컬 문서에 없는 최신 정보
3. brave_web_search 필요:
   - Brave 검색 엔진 사용이 유리한 경우
   - 특정 지역 정보 검색 시
"""

# 사용자 메시지:
"2025년 강남 카페 창업 전망은?"

# LLM 판단:
# → "2025년이라는 키워드가 있네!"
# → "로컬 문서 유사도도 0.65로 낮고..."
# → "최신 정보 필요!"
# → "10개 도구 중에서... tavily_search가 적합해!"
# ⭐ LLM이 자동으로 Tavily와 Brave 중 선택!

# LLM 응답:
{
    "tool_calls": [
        {
            "function": {
                "name": "tavily_search",  # ← LLM이 10개 중 tavily_search 선택
                "arguments": '{"query": "2025년 강남 카페 창업 트렌드", "max_results": 5, "search_depth": "advanced"}'
            }
        }
    ]
}

# 2-3. 도구 실행 (MCP 서버 호출, LLM 아님!)
universal_client.call_tool(
    "tavily_search",
    {
        "query": "2025년 강남 카페 창업 트렌드",
        "max_results": 5,
        "search_depth": "advanced"
    }
)

# → Tavily MCP 서버 호출 (웹 검색 API)
# → 실시간 웹 검색 실행
# → 검색 결과 반환:
{
    "results": [
        {
            "title": "2025년 강남 카페 시장 전망",
            "url": "https://...",
            "content": "2025년 강남 지역의 카페 시장은...",
            "score": 0.95
        },
        {
            "title": "최신 카페 창업 트렌드",
            "url": "https://...",
            "content": "요즘 인기 있는 카페 컨셉은...",
            "score": 0.92
        },
        ...
    ]
}

# 2-4. MCPToolRouter 결과
{
    "mcp_used": True,
    "tools_used": ["tavily_search"],
    "results": {
        "tavily_search": {...}
    },
    "direct_answer": None
}

# ========================================
# [3단계] RAGChain - 답변 생성 (하이브리드)
# ========================================

# mcp_used = True이고 local_docs도 있으므로 _generate_hybrid() 호출
# ⭐ LLM 호출 2회

# 프롬프트 구성:
messages = [
    {
        "role": "system",
        "content": "당신은 상권 분석 전문가입니다. 로컬 문서와 최신 웹 검색 결과를 모두 활용하세요..."
    },
    {
        "role": "user",
        "content": """
[내부 참고 문서]
basic_guide.pdf: 상권 분석의 기초는...

[최신 MCP 검색 결과]
[tavily_search 결과]
1. 제목: 2025년 강남 카페 시장 전망
   URL: https://...
   내용: 2025년 강남 지역의 카페 시장은...

2. 제목: 최신 카페 창업 트렌드
   URL: https://...
   내용: 요즘 인기 있는 카페 컨셉은...

[사용자 질문]
2025년 강남 카페 창업 전망은?
"""
    }
]

# LLM 호출 (gpt-4o-mini, temperature=0.7)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)

# 답변:
"2025년 강남 카페 창업 전망에 대해 말씀드리겠습니다.

최신 시장 조사에 따르면, 2025년 강남 지역의 카페 시장은...
(웹 검색 결과 활용)

기본적인 상권 분석 관점에서는...
(로컬 문서 활용)

종합적으로 보면..."

# ========================================
# 최종 결과
# ========================================
{
    "answer": "2025년 강남 카페 창업 전망에 대해...",
    "sources": [{"content": "...", "score": 0.65}],  # 로컬 문서
    "mcp_results": {"tavily_search": {...}},  # 웹 검색 결과
    "web_search_used": True,
    "tools_used": ["tavily_search"],
    "usage": {
        "total_tokens": 2500
    }
}

# ========================================
# 총 비용 분석
# ========================================
# LLM 호출: 2회
#   1. 도구 선택 (gpt-4o-mini, ~500 토큰) = $0.0001
#   2. 답변 생성 (gpt-4o-mini, ~2500 토큰, 컨텍스트 2배) = $0.0004
# MCP 서버 호출: 1회
#   - Tavily Search API = $0.01 ⭐⭐⭐ (진짜 비용!)
# 총 비용: ~$0.0105 (시나리오 2 대비 약 35배)
```

---

### 3.3 Tool Schema 변환 과정

**MCP 도구 정의 → OpenAI Function 스키마 변환**

```python
# rag/mcp_client_new.py (282~364줄)

class ToolSchemaConverter:
    """MCP Tool Schema ↔ OpenAI Function Schema 변환"""

    @staticmethod
    def get_tavily_tools_manual() -> List[Dict[str, Any]]:
        """Tavily MCP 도구를 수동으로 정의"""
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

**예시:**
✅ "2025년 강남 상권 트렌드" → 사용
✅ "최근 부동산 시장 동향" → 사용
❌ "카페 창업 기본 가이드" → 사용 안 함 (로컬 문서로 충분)
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
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
```

**왜 수동 정의를 사용하는가?**

1. **Description 커스터마이징**: LLM에게 명확한 사용 시점 가이드
2. **안정성**: MCP 서버 변경과 무관하게 일관된 스키마
3. **최적화**: 불필요한 파라미터 제거 (예: `topic`, `days` 제외)

---

### 3.4 스트리밍 응답 처리

**SSE (Server-Sent Events) 프로토콜 사용**

```python
# main.py (347~396줄)

async def stream_rag_response(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 3
):
    """RAG 응답을 SSE 스트리밍으로 전송"""

    try:
        # RAG 체인 가져오기
        rag = await get_rag_chain()

        # 스트리밍 실행 (async for 사용)
        async for chunk in rag.stream_run(
            query=query,
            conversation_history=conversation_history,
            top_k=top_k
        ):
            # SSE 형식으로 데이터 전송
            chunk_type = chunk.get("type")
            content = chunk.get("content")

            if chunk_type == "sources":
                # 참고 문서 정보 전송
                yield f"data: {json.dumps({'event': 'sources', 'sources': content})}\n\n"

            elif chunk_type == "mcp_results":
                # MCP 검색 결과 전송
                yield f"data: {json.dumps({'event': 'mcp_results', 'mcp_results': content})}\n\n"

            elif chunk_type == "answer":
                # 답변 청크 전송 (실시간 타이핑 효과)
                data = f"data: {json.dumps({'event': 'answer', 'content': content})}\n\n"
                yield data
                await asyncio.sleep(0)  # 즉시 플러시

            elif chunk_type == "error":
                # 에러 전송
                yield f"data: {json.dumps({'event': 'error', 'message': content})}\n\n"

        # 스트리밍 완료
        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    except Exception as e:
        error_msg = json.dumps({
            "event": "error",
            "message": f"RAG 스트리밍 오류: {str(e)}"
        })
        yield f"data: {error_msg}\n\n"
```

**프론트엔드 수신 예시**
```javascript
// React EventSource
const eventSource = new EventSource('/api/rag-chat-stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.event === 'sources') {
    // 참고 문서 표시
    setSources(data.sources);
  }
  else if (data.event === 'mcp_results') {
    // 웹 검색 결과 표시
    setWebResults(data.mcp_results);
  }
  else if (data.event === 'answer') {
    // 답변 실시간 표시 (타이핑 효과)
    setAnswer(prev => prev + data.content);
  }
  else if (data.event === 'done') {
    // 완료
    eventSource.close();
  }
};
```

---

## 4. 실전 예제 & 베스트 프랙티스

### 4.1 MCP 설정 파일 작성법

**기본 구조 (mcp_config.json)**

```json
{
  "mcpServers": {
    "서버_이름": {
      "url": "원격_MCP_서버_URL",
      "또는": "로컬_명령어"
    }
  }
}
```

**예시 1: 원격 MCP 서버 (Tavily)**

```json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
    }
  }
}
```

- `${TAVILY_API_KEY}`: 환경변수 자동 치환
- `.env` 파일: `TAVILY_API_KEY=tvly-abc123...`

---

**예시 2: 로컬 MCP 서버 (Brave)**

```json
{
  "mcpServers": {
    "brave": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@smithery/cli@latest",
        "run",
        "brave",
        "--key",
        "bb935426-668e-4721-8468-737bb538b799",
        "--profile",
        "molecular-anteater-cPxy9A"
      ]
    }
  }
}
```

- `command`: 실행할 명령어 (Windows: `cmd`, Mac/Linux: `sh`)
- `args`: 명령어 인자 배열

---

**예시 3: 여러 MCP 서버 등록**

```json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
    },
    "brave": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "brave", "--key", "${BRAVE_API_KEY}"]
    },
    "custom_db": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

---

### 4.2 새로운 MCP 서버 추가하는 방법

**시나리오**: Google Search MCP 서버 추가

**1단계: MCP 서버 찾기**

- [MCP 서버 디렉토리](https://github.com/modelcontextprotocol/servers) 검색
- 또는 직접 구현 (FastMCP 사용)

**2단계: 설정 파일 수정**

```json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
    },
    "google": {
      "url": "https://mcp.google.com/search?apiKey=${GOOGLE_API_KEY}"
    }
  }
}
```

**3단계: 환경변수 설정**

```bash
# .env 파일
GOOGLE_API_KEY=AIzaSyAbc123...
```

**4단계: Description 보강 (선택 사항)**

자동 발견 시스템이 도구를 자동으로 찾아주지만, LLM이 더 잘 선택할 수 있도록 Description을 보강할 수 있습니다.

```python
# rag/mcp_client_new.py

@staticmethod
def enhance_tool_description(openai_tool: Dict[str, Any]) -> Dict[str, Any]:
    """OpenAI Function 스키마의 description을 보강"""
    tool_name = openai_tool["function"]["name"]

    # Google Search에 대한 상세 가이드 추가
    if tool_name == "google_search":
        openai_tool["function"]["description"] += """

**사용 시점:**
- 일반적인 웹 검색이 필요한 경우
- Tavily보다 광범위한 결과가 필요할 때

**사용 안 함:**
- 뉴스/트렌드 검색 (Tavily가 더 적합)
- 로컬 문서로 충분한 경우
"""

    return openai_tool
```

**5단계: 재시작 및 자동 확인**

✅ **자동 발견 시스템 덕분에 코드 수정 불필요!**

```bash
# 서버 재시작만 하면 됨
uvicorn main:app --reload

# 출력:
# [UniversalMCPClient] JSON 설정 파일 로드: mcp_config.json
# [UniversalMCPClient] 서버 등록 중: tavily
# [OK] tavily 등록 완료
# [UniversalMCPClient] 서버 등록 중: google  ← 새 서버 자동 등록!
# [OK] google 등록 완료
# [OK] 총 3개 MCP 서버 로드 완료

# 첫 요청 시:
# [MCPToolRouter] MCP 도구 자동 발견 시작...
# [UniversalMCPClient] tavily: 4개 도구 발견
# [UniversalMCPClient] google: 2개 도구 발견  ← 자동 발견!
# [OK] MCPToolRouter 초기화 완료: 6개 도구 준비
#    - tavily_search
#    - tavily_extract
#    - google_search  ← 자동 추가!
#    - google_image_search
```

**기존 방식 vs 자동 발견 방식 비교**

| 단계 | 기존 (수동 정의) | 자동 발견 |
|------|-----------------|----------|
| 1. 설정 파일 수정 | ✅ mcp_config.json | ✅ mcp_config.json |
| 2. 환경변수 설정 | ✅ .env | ✅ .env |
| 3. 도구 스키마 정의 | ❌ 코드 수정 필요! | ✅ 자동! |
| 4. Description 보강 | ❌ 코드 수정 필요! | ⭐ 선택 사항 |
| 5. 재시작 | ✅ | ✅ |

**결과**: 설정 파일만 수정하면 끝! 🎉

```bash
# 서버 재시작
uvicorn main:app --reload

# 테스트
curl -X POST http://localhost:8000/api/rag-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "2025년 AI 트렌드",
    "conversation_history": []
  }'

# 로그 확인
# [UniversalMCPClient] tavily: 2개 도구 발견
# [UniversalMCPClient] google: 1개 도구 발견
# [OK] 3개 MCP 도구 발견 완료
```

---

### 4.3 커스텀 MCP 도구 만들기

**시나리오**: 내부 데이터베이스 조회 MCP 서버 구축

**FastMCP로 구현**

```python
# custom_mcp_server.py

from fastmcp import FastMCP
import sqlite3

mcp = FastMCP("Internal Database MCP")

@mcp.tool()
def query_sales_data(region: str, year: int) -> dict:
    """
    내부 매출 데이터 조회

    Args:
        region: 지역 (예: "강남", "홍대")
        year: 연도 (예: 2024)

    Returns:
        매출 데이터
    """
    # 데이터베이스 조회
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM sales WHERE region = ? AND year = ?",
        (region, year)
    )

    results = cursor.fetchall()
    conn.close()

    return {
        "region": region,
        "year": year,
        "total_sales": sum(row[2] for row in results),
        "count": len(results)
    }

# MCP 서버 실행
if __name__ == "__main__":
    mcp.run()
```

**mcp_config.json에 등록**

```json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
    },
    "internal_db": {
      "command": "python",
      "args": ["custom_mcp_server.py"]
    }
  }
}
```

**사용 예시**

```python
# LLM이 자동으로 선택
query = "강남 지역 2024년 매출 데이터 알려줘"

# MCPToolRouter가 판단:
# → "내부 데이터니까 query_sales_data 도구 필요!"
# → universal_client.call_tool("query_sales_data", {"region": "강남", "year": 2024})
# → 결과: {"total_sales": 1500000000, "count": 120}
```

---

## 마무리

### 핵심 요약

1. **MCP란?**: LLM이 외부 도구에 접근하는 표준 프로토콜
2. **UniversalMCPClient**: 여러 MCP 서버 통합 관리
3. **도구 자동 발견**: MCP 서버의 도구를 자동으로 발견하고 OpenAI Function 스키마로 변환
4. **MCPToolRouter**: LLM이 자동으로 필요한 도구 선택 (10개+ 도구 중에서)
5. **RAGChain**: 로컬 RAG + MCP 하이브리드 전략

### 아키텍처의 강점

✅ **유연성**: 설정 파일만으로 새 도구 추가 (코드 수정 불필요)
✅ **자동화**: LLM이 필요한 도구 자동 선택 + 자동 발견
✅ **확장성**: 100개 도구도 동일 인터페이스
✅ **비용 효율**: 2단계 필터링으로 불필요한 호출 방지
✅ **최신성**: 웹 검색으로 실시간 정보 접근
✅ **Lazy Loading**: 첫 요청 시에만 도구 발견 (서버 시작 속도 향상)
✅ **Fallback**: 자동 발견 실패 시 수동 정의로 대체

### 자동 발견 시스템의 장점

**기존 방식 (수동 정의):**
- ❌ 새 MCP 서버 추가 시 코드 수정 필요
- ❌ 도구 스키마를 수동으로 정의해야 함
- ❌ Brave 같은 추가 서버는 사용 불가능
- ❌ 확장성 낮음

**자동 발견 방식:**
- ✅ `mcp_config.json`만 수정하면 모든 도구 자동 발견
- ✅ MCP 스키마 → OpenAI Function 스키마 자동 변환
- ✅ Tavily + Brave + 커스텀 서버 모두 동일하게 처리
- ✅ LLM이 10개+ 도구 중에서 최적의 도구 선택
- ✅ Description 자동 보강으로 LLM 선택 정확도 향상


**참고 자료**
- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---