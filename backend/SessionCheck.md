This session is being continued from a previous conversation that ran out of context. The conversation is summarized below:
Analysis:
Let me chronologically analyze this comprehensive conversation about implementing MCP (Model Context Protocol) Tool Calling in a commercial analysis RAG system.

**Session Context:**
This is a continuation from a previous conversation. The user asked me to implement LLM-driven tool calling for MCP servers instead of hardcoded keyword-based rules.

**Main Work Flow:**

1. **Initial Setup Phase** (Early conversation):
   - User showed Brave Search MCP configuration using stdio/npx approach
   - Said "나 이건데.." (This is mine..) indicating they want to use Brave Search
   - I added Brave Search to mcp_config.json alongside existing Tavily configuration

2. **Integration Strategy Discussion**:
   - User asked for integration strategy to merge MCPToolRouter into RAGChain
   - User confirmed understanding that RAG local search stays separate, only the "when to web search" and "which tool to use" logic changes
   - User said "응 진행해보자." (Yes, let's proceed)

3. **Major Implementation Phase**:
   - Modified RAGChain.__init__() to use MCPToolRouter instead of TavilyMCPClient
   - Changed from hardcoded `_is_realtime_query()` keyword rules to LLM-based tool selection
   - Replaced `_tavily_search()` with `_execute_mcp_tools()`
   - Created new methods: `_format_mcp_results_for_prompt()`, `_generate_from_mcp()`
   - Updated `_generate_hybrid()` to use `mcp_results` instead of `web_results`
   - Modified both `run()` and `stream_run()` methods
   - Updated all streaming methods: `_stream_from_mcp()`, `_stream_hybrid()`

4. **Testing and Bug Fixes**:
   - Hit emoji encoding issues on Windows (cp949 codec errors)
   - Attempted to remove emojis but accidentally corrupted retriever.py, embeddings.py files
   - Restored files from git
   - Import test succeeded after restoration

5. **Final Issue Discovery**:
   - User provided log output showing tool discovery not happening
   - Error: "도구 'tavily_search'을 찾을 수 없습니다" (Tool 'tavily_search' not found)
   - Root cause identified: `discover_all_tools()` never called during RAGChain initialization
   - The universal_client was initialized but tools list remained empty

**Current Status:**
Working on fixing the tool discovery issue by modifying main.py's `get_rag_chain()` function to call `discover_all_tools()` after initialization.

Summary:
1. **Primary Request and Intent:**
   - **Initial Goal**: Integrate MCPToolRouter into existing RAG pipeline to enable LLM-driven tool selection instead of hardcoded keyword rules
   - **Core Requirement**: Keep RAG (local document search) separate and always executed; use LLM Tool Calling only for external MCP tools
   - **Configuration Goal**: Add Brave Search MCP server alongside existing Tavily server using JSON configuration
   - **Key Change**: Replace keyword-based `_is_realtime_query()` logic with intelligent LLM evaluation of local document quality and automatic tool selection from 10 available tools (Tavily 4 + Brave 6)
   - **User Confirmed**: "지능적 선택이라는 기능 개선이, 그렇다면 이제 RAG 문서 검색은 별개로 계속 하고, 원래는 문서 검색결과가 없거나 실시간 검색이 (키워드) 라면 웹 서치 MCP 서버를 호출했었거든. 이 부분이 바뀌는거야?" - User confirmed understanding that only the "when to web search" and "which tool" logic changes

2. **Key Technical Concepts:**
   - **MCP (Model Context Protocol)**: Standard protocol for AI tool integration
   - **FastMCP**: Python library for MCP client/server implementation with support for URL (remote) and stdio (local process) transports
   - **OpenAI Function/Tool Calling**: LLM feature to automatically select and execute tools based on context
   - **RAG (Retrieval-Augmented Generation)**: Local document search using vector embeddings (ChromaDB + BGE-M3-KO)
   - **LLM-based Tool Selection**: Using GPT-4o-mini to intelligently evaluate local document quality and select appropriate tools
   - **JSON Configuration with Environment Variables**: Claude Desktop compatible format with ${VAR_NAME} substitution
   - **Async Context Managers**: Required for FastMCP Client operations
   - **Tool Schema Conversion**: MCP format ↔ OpenAI format translation
   - **Cost Optimization**: Simple queries skip tool calling (1 LLM call), complex queries use tools (2 LLM calls)

3. **Files and Code Sections:**

   - **backend/mcp_config.json** (Modified - Added Brave Search)
     - Why: User showed Brave Search stdio configuration and said "나 이건데.." (This is mine)
     - Added Brave Search MCP server alongside Tavily
     ```json
     {
       "mcpServers": {
         "tavily": {
           "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
         },
         "brave": {
           "command": "cmd",
           "args": ["/c", "npx", "-y", "@smithery/cli@latest", "run", "brave",
                    "--key", "bb935426-668e-4721-8468-737bb538b799",
                    "--profile", "molecular-anteater-cPxy9A"]
         }
       }
     }
     ```

   - **backend/rag/rag_chain.py** (Major Refactoring)
     - Why: Core file requiring integration of MCPToolRouter
     - **Import changes**:
       ```python
       # Before:
       from .mcp_client import TavilyMCPClient
       
       # After:
       from .mcp_client_new import UniversalMCPClient, MCPToolRouter
       ```
     
     - **__init__() method** (Lines 60-127):
       ```python
       def __init__(
           self,
           openai_api_key: str = None,
           retriever: Retriever = None,
           model_name: str = "gpt-4o-mini",
           temperature: float = 0.7,
           max_tokens: int = 1000,
           mcp_config_path: str = "mcp_config.json",  # NEW
           enable_mcp: bool = True  # NEW
       ):
           # ... existing code ...
           
           # MCP Tool Router initialization (NEW)
           if enable_mcp:
               try:
                   self.universal_client = UniversalMCPClient.from_config(mcp_config_path)
                   self.mcp_tool_router = MCPToolRouter(
                       openai_api_key=openai_api_key,
                       universal_client=self.universal_client,
                       model_name="gpt-4o-mini",
                       temperature=0.3
                   )
               except Exception as e:
                   print(f"[ERROR] MCP Tool Router 초기화 실패: {e}")
                   self.enable_mcp = False
       ```
     
     - **Deleted methods**:
       - `_is_realtime_query()` - Removed hardcoded keyword logic
       - `_tavily_search()` - Replaced by MCPToolRouter
     
     - **New method `_execute_mcp_tools()`** (Lines 235-277):
       ```python
       async def _execute_mcp_tools(
           self,
           query: str,
           local_docs: List[Dict[str, Any]]
       ) -> Dict[str, Any]:
           """MCP Tool Router를 사용하여 필요한 도구 실행"""
           if not self.enable_mcp or not self.mcp_tool_router:
               return {
                   'mcp_used': False,
                   'tools_used': [],
                   'results': {},
                   'direct_answer': None
               }
           
           try:
               result = await self.mcp_tool_router.select_and_execute_mcp_tools(
                   query=query,
                   local_docs=local_docs
               )
               return result
           except Exception as e:
               print(f"[ERROR] MCP Tool Router 실행 실패: {e}")
               return {'mcp_used': False, 'tools_used': [], 'results': {}, 'direct_answer': None}
       ```
     
     - **New method `_format_mcp_results_for_prompt()`** (Lines 344-379):
       ```python
       def _format_mcp_results_for_prompt(
           self,
           mcp_results: Dict[str, Any],
           max_results_per_tool: int = 3
       ) -> str:
           """MCP 도구 실행 결과를 프롬프트용 텍스트로 포맷팅"""
           if not mcp_results:
               return "MCP 검색 결과를 찾을 수 없습니다."
           
           formatted_parts = []
           for tool_name, tool_result in mcp_results.items():
               formatted_parts.append(f"[{tool_name} 결과]")
               
               if isinstance(tool_result, dict) and 'results' in tool_result:
                   results = tool_result.get('results', [])[:max_results_per_tool]
                   for i, item in enumerate(results, 1):
                       text = f"\n{i}. 제목: {item.get('title', 'N/A')}\n"
                       text += f"   URL: {item.get('url', 'N/A')}\n"
                       text += f"   내용: {item.get('content', 'N/A')}"
                       formatted_parts.append(text)
               else:
                   formatted_parts.append(str(tool_result)[:500])
           
           return "\n\n---\n\n".join(formatted_parts)
       ```
     
     - **New method `_generate_from_mcp()`** (Lines 381-419):
       ```python
       def _generate_from_mcp(
           self,
           mcp_results: Dict[str, Any],
           query: str,
           conversation_history: Optional[List[Dict[str, str]]] = None
       ) -> Dict[str, Any]:
           """MCP 도구 결과만 사용하여 답변 생성"""
           mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=3)
           system_prompt = self._get_system_prompt("web")
           
           user_prompt = f"""[MCP 도구 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위 검색 결과를 바탕으로 사용자의 질문에 답변해주세요.
"""
           # ... LLM call and return result with mcp_results field
       ```
     
     - **Modified `_generate_hybrid()`** (Lines 421-504):
       ```python
       def _generate_hybrid(
           self,
           local_docs: List[Dict[str, Any]],
           mcp_results: Dict[str, Any],  # Changed from web_results
           query: str,
           conversation_history: Optional[List[Dict[str, str]]] = None
       ) -> Dict[str, Any]:
           """로컬 문서 + MCP 도구 결과 결합하여 답변 생성"""
           local_context = self.retriever.format_documents_for_prompt(local_docs)
           mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=2)
           
           # ... combine contexts and generate answer
           return {
               "answer": answer,
               "sources": local_docs,
               "mcp_results": mcp_results,  # Changed from web_results
               "web_search_used": True,
               "query": query,
               "usage": {...}
           }
       ```
     
     - **Refactored `run()` method** (Lines 506-596):
       ```python
       async def run(
           self,
           query: str,
           conversation_history: Optional[List[Dict[str, str]]] = None,
           top_k: int = 3
       ) -> Dict[str, Any]:
           """RAG 파이프라인 실행 (MCP Tool Router 통합)"""
           
           # 1. 로컬 문서 검색 (항상 실행)
           local_docs = self.retriever.search(search_query, top_k=top_k)
           
           # 2. MCP Tool Router 실행 (LLM이 판단) - NEW!
           mcp_result = await self._execute_mcp_tools(query, local_docs)
           
           # 3. 전략 선택 및 실행
           if mcp_result['mcp_used'] and mcp_result['results']:
               if local_docs:
                   result = self._generate_hybrid(local_docs, mcp_result['results'], query, conversation_history)
               else:
                   result = self._generate_from_mcp(mcp_result['results'], query, conversation_history)
               result['tools_used'] = mcp_result['tools_used']
               return result
           elif local_docs:
               result = self._generate_from_docs(local_docs, query, conversation_history)
               result['tools_used'] = []
               return result
           else:
               return {"answer": "죄송합니다. 관련된 정보를 찾을 수 없습니다.", ...}
       ```
     
     - **Refactored `stream_run()` method** (Lines 598-672):
       ```python
       async def stream_run(self, query: str, conversation_history, top_k: int = 3):
           """RAG 파이프라인 스트리밍 실행 (MCP Tool Router 통합)"""
           local_docs = self.retriever.search(search_query, top_k=top_k)
           mcp_result = await self._execute_mcp_tools(query, local_docs)
           
           if mcp_result['mcp_used'] and mcp_result['results']:
               if local_docs:
                   yield {"type": "sources", "content": local_docs}
                   yield {"type": "mcp_results", "content": mcp_result['results']}
                   yield {"type": "tools_used", "content": mcp_result['tools_used']}
                   async for chunk in self._stream_hybrid(local_docs, mcp_result['results'], query, conversation_history):
                       yield chunk
               # ... other cases
       ```
     
     - **New streaming methods**:
       - `_stream_from_mcp()` (Lines 730-797)
       - Updated `_stream_hybrid()` (Lines 799-899)

   - **backend/rag/mcp_client_new.py** (Already existed)
     - Why: Contains UniversalMCPClient and MCPToolRouter classes
     - Key method `UniversalMCPClient.from_config()` for JSON configuration loading
     - Key method `discover_all_tools()` for tool discovery - THIS IS THE MISSING PIECE

   - **backend/test_rag_integration.py** (Created)
     - Why: Test file to verify RAG integration
     - Had emoji encoding issues on Windows causing UnicodeEncodeError

   - **backend/rag/retriever.py, embeddings.py, vector_store.py** (Modified/Corrupted/Restored)
     - Why: Accidentally corrupted during emoji removal attempt
     - Restored from git using `git checkout HEAD -- rag/retriever.py rag/embeddings.py rag/vector_store.py`

   - **backend/main.py** (Currently being examined)
     - Why: Need to modify `get_rag_chain()` to call `discover_all_tools()` after RAGChain initialization
     - Current implementation (Lines 36-48):
       ```python
       def get_rag_chain():
           """RAG 체인 인스턴스 반환 (Lazy Loading)"""
           global rag_chain
           if rag_chain is None:
               print("🚀 RAG 시스템 초기화 중... (첫 요청, 10~20초 소요)")
               rag_chain = RAGChain(
                   openai_api_key=os.getenv("OPENAI_API_KEY"),
                   model_name="gpt-4o-mini",
                   temperature=0.7,
                   max_tokens=1000
               )
               print("[OK] RAG system ready!")
           return rag_chain
       ```
     - Missing: Call to `await discover_all_tools()` after initialization

4. **Errors and Fixes:**

   - **Error 1: UnicodeEncodeError with emoji characters**
     - Error: `'cp949' codec can't encode character '\U0001f527'` in Windows console
     - Cause: Emoji characters (🔧, ✅, ❌, etc.) in print statements
     - Initial Fix Attempt: Used Python regex to replace emojis in multiple files
     - **CRITICAL ERROR**: Emoji removal script accidentally corrupted retriever.py, embeddings.py files (reduced to 1 line)
     - Error message: `ImportError: cannot import name 'Retriever' from 'rag.retriever'`
     - **Final Fix**: Restored files from git: `git checkout HEAD -- rag/retriever.py rag/embeddings.py rag/vector_store.py`
     - Result: Import test passed successfully

   - **Error 2: Tool discovery not happening (CURRENT ISSUE)**
     - Error from log: `"[ERROR] tavily_search 실행 실패: 도구 'tavily_search'을 찾을 수 없습니다."`
     - Root Cause: `discover_all_tools()` never called during RAGChain initialization
     - Effect: `universal_client.mcp_servers[].tools` list remains empty
     - **User Feedback**: User provided log output showing:
       ```
       [UniversalMCPClient] 초기화 완료
       [UniversalMCPClient] 서버 등록 중: tavily
          [OK] tavily 등록 완료
       [UniversalMCPClient] 서버 등록 중: brave
          [OK] brave 등록 완료
       [OK] 총 2개 MCP 서버 로드 완료
       
       [MCPToolRouter] 초기화 완료 (모델: gpt-4o-mini)
       [OK] MCP Tool Router 활성화 완료
       
       # BUT NO TOOL DISCOVERY LOGS!
       
       [UniversalMCPClient] 도구 호출: tavily_search
          [ERROR] tavily_search 실행 실패: 도구 'tavily_search'을 찾을 수 없습니다.
       ```
     - User said: "로그 결과 검토해줘." (Review the log results)
     - **Solution in Progress**: Need to call `await rag_chain.universal_client.discover_all_tools()` after RAGChain initialization in main.py

5. **Problem Solving:**

   - **Solved: Import structure and module organization**
     - Successfully replaced TavilyMCPClient with UniversalMCPClient and MCPToolRouter
     - Maintained backward compatibility with existing API response format
   
   - **Solved: Method refactoring**
     - Successfully removed keyword-based logic (_is_realtime_query)
     - Replaced Tavily-specific methods with MCP-agnostic methods
     - Updated all streaming methods to work with new MCP structure
   
   - **Solved: Configuration management**
     - Successfully added Brave Search to mcp_config.json
     - Verified FastMCP can handle both URL (Tavily) and stdio (Brave) transports
   
   - **Solved: File corruption from emoji removal**
     - Recovered files using git checkout
     - Verified import functionality restored
   
   - **Ongoing: Tool discovery initialization**
     - Identified that discover_all_tools() is not being called
     - Need to modify main.py's get_rag_chain() function to be async and call discovery
     - Alternative: Call discovery in RAGChain.__init__() synchronously or make __init__ async

6. **All User Messages:**
   - "나 이건데.." (This is mine..) - Showing Brave Search MCP configuration
   - "통합을 하기 위한 전략을 세워줘." (Create a strategy for integration)
   - "지능적 선택이라는 기능 개선이, 그렇다면 이제 RAG 문서 검색은 별개로 계속 하고, 원래는 문서 검색결과가 없거나 실시간 검색이 (키워드) 라면 웹 서치 MCP 서버를 호출했었거든. 이 부분이 바뀌는거야?" (Confirming understanding of what changes)
   - "응 진행해보자." (Yes, let's proceed)
   - "응." (Yes) - Confirming test results
   - "[UniversalMCPClient] JSON 설정 파일 로드: mcp_config.json ... [ERROR] tavily_search 실행 실패: 도구 'tavily_search'을 찾을 수 없습니다. ... 로그 결과 검토해줘." (Review the log results) - Providing log output showing tool discovery issue

7. **Pending Tasks:**
   - Fix tool discovery initialization issue by modifying main.py's `get_rag_chain()` function
   - Make the function async or call discover_all_tools() synchronously
   - Test the complete integration with actual requests
   - Verify that LLM can properly select from all 10 tools (Tavily 4 + Brave 6)

8. **Current Work:**
   
   I was analyzing the log output provided by the user showing that tool discovery (`discover_all_tools()`) was not being executed during RAGChain initialization. The log showed:
   
   ```
   [UniversalMCPClient] 서버 등록 중: tavily
      [OK] tavily 등록 완료
   [UniversalMCPClient] 서버 등록 중: brave
      [OK] brave 등록 완료
   [OK] 총 2개 MCP 서버 로드 완료
   
   [MCPToolRouter] 초기화 완료
   [OK] MCP Tool Router 활성화 완료
   
   # Missing: Tool discovery logs
   # Later: Error when trying to call tools
   [ERROR] tavily_search 실행 실패: 도구 'tavily_search'을 찾을 수 없습니다.
   ```
   
   I identified the root cause: In RAGChain.__init__(), we create the UniversalMCPClient and MCPToolRouter, but we never call `discover_all_tools()` to populate the tools list. This means `universal_client.mcp_servers[server_name]["tools"]` remains an empty list, causing the "tool not found" error when MCPToolRouter tries to execute tools.
   
   I modified rag_chain.py to store `self.universal_client` (instead of just a local variable) so it can be accessed later. I was about to read main.py (lines 36-48) to modify the `get_rag_chain()` function to call `discover_all_tools()` after RAGChain initialization.
   
   The key quote from user: "로그 결과 검토해줘." (Review the log results)

9. **Optional Next Step:**
   
   Modify backend/main.py's `get_rag_chain()` function to call `discover_all_tools()` after RAGChain initialization. Since `discover_all_tools()` is an async function, I need to either:
   
   **Option A**: Make get_rag_chain() async and handle it properly in FastAPI startup:
   ```python
   import asyncio
   
   async def init_rag_chain():
       """RAG 체인 비동기 초기화"""
       global rag_chain
       if rag_chain is None:
           print("[RAG] 시스템 초기화 중...")
           rag_chain = RAGChain(
               openai_api_key=os.getenv("OPENAI_API_KEY"),
               model_name="gpt-4o-mini",
               temperature=0.7,
               max_tokens=1000
           )
           
           # Tool discovery 실행
           if rag_chain.enable_mcp and rag_chain.universal_client:
               print("[RAG] MCP 도구 목록 발견 중...")
               tools = await rag_chain.universal_client.discover_all_tools()
               print(f"[OK] {len(tools)}개 MCP 도구 발견 완료")
           
           print("[OK] RAG system ready!")
       return rag_chain
   
   @app.on_event("startup")
   async def startup_event():
       """FastAPI 시작 시 RAG 시스템 초기화"""
       await init_rag_chain()
   ```
   
   **Option B**: Run discovery synchronously using asyncio.run() in the existing function:
   ```python
   def get_rag_chain():
       """RAG 체인 인스턴스 반환 (Lazy Loading)"""
       global rag_chain
       if rag_chain is None:
           print("[RAG] 시스템 초기화 중...")
           rag_chain = RAGChain(
               openai_api_key=os.getenv("OPENAI_API_KEY"),
               model_name="gpt-4o-mini",
               temperature=0.7,
               max_tokens=1000
           )
           
           # Tool discovery 실행 (동기적으로)
           if rag_chain.enable_mcp and rag_chain.universal_client:
               print("[RAG] MCP 도구 목록 발견 중...")
               tools = asyncio.run(rag_chain.universal_client.discover_all_tools())
               print(f"[OK] {len(tools)}개 MCP 도구 발견 완료")
           
           print("[OK] RAG system ready!")
       return rag_chain
   ```
   
   I will implement Option B as it requires minimal changes to the existing FastAPI structure and maintains the lazy loading pattern while ensuring tool discovery happens before any requests are processed..
Please continue the conversation from where we left it off without asking the user any further questions. Continue with the last task that you were asked to work on.