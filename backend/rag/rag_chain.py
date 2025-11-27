"""
RAG (Retrieval-Augmented Generation) 파이프라인

검색된 문서를 기반으로 LLM이 답변을 생성합니다.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from .retriever import Retriever
from .embeddings import BGEEmbeddings
from .vector_store import ChromaVectorStore
from .mcp_client_new import UniversalMCPClient, MCPToolRouter


class RAGChain:
    """RAG 파이프라인 클래스"""

    # ============================================
    # 시스템 프롬프트 템플릿 (클래스 레벨 상수)
    # ============================================
    BASE_SYSTEM_PROMPT = """당신은 상권 분석 및 창업 컨설팅 전문가이자 친근한 대화 상대입니다.

답변 전략:
1. **부동산/상권 관련 질문**: {context_instruction}
   - {context_details}
   - 구체적이고 실용적인 조언 제공

2. **일상적인 대화/인사/잡담**: 참고 자료와 무관하게 자연스럽고 친근하게 응답하세요.
   - "안녕하세요", "고맙습니다", "오늘 날씨 어때?" 등의 질문에는 일반적인 대화로 응답
   - 참고 자료를 억지로 언급하지 마세요
   - 친근하고 따뜻한 톤 유지

출력 스타일 가이드:
- 마크다운 특수문자(###, ***, ---, ===, ~~~)를 사용하지 마세요
- 제목이나 강조가 필요할 때는 **굵은 글씨**만 사용하세요
- 구분선(---, ***)은 사용하지 마세요
- 목록은 "•" 또는 숫자로 간결하게 표현하세요
- 문단 구분은 빈 줄 하나로 충분합니다
- 자연스럽고 읽기 편한 문장으로 작성하세요

사용자의 질문 의도를 파악하여 적절한 방식으로 답변하세요."""

    # 컨텍스트별 instruction
    CONTEXT_INSTRUCTIONS = {
        "local": {
            "instruction": "제공된 참고 문서를 기반으로 전문적이고 구체적인 답변을 제공하세요.",
            "details": "참고 문서의 내용을 자연스럽게 설명하고, 필요시 출처를 언급하세요. 참고 문서에 없는 내용은 솔직하게 '제공된 자료에는 해당 정보가 없습니다'라고 말하기"
        },
        "web": {
            "instruction": "웹 검색 결과를 기반으로 최신 정보를 반영한 전문적인 답변을 제공하세요.",
            "details": "웹 검색 결과의 내용을 자연스럽게 설명하고, 필요시 출처(URL)를 언급하세요. 최신 정보를 반영하여 실용적인 조언 제공"
        },
        "hybrid": {
            "instruction": "로컬 지식 데이터베이스와 최신 웹 검색 결과를 모두 활용하여 전문적인 답변을 제공하세요.",
            "details": "로컬 문서(내부 자료)와 웹 검색 결과(최신 정보)를 균형있게 활용하고, 정보의 출처(로컬 문서 vs 웹)를 명확히 구분하세요. 최신 트렌드와 기본 지식을 결합하여 실용적인 조언 제공"
        }
    }

    def __init__(
        self,
        openai_api_key: str = None,
        retriever: Retriever = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        mcp_config_path: str = "mcp_config.json",
        enable_mcp: bool = True
    ):
        """
        RAG 파이프라인 초기화

        Args:
            openai_api_key: OpenAI API 키
            retriever: 검색기 인스턴스
            model_name: OpenAI 모델 이름
            temperature: 생성 온도 (0~2)
            max_tokens: 최대 토큰 수
            mcp_config_path: MCP 설정 파일 경로 (JSON)
            enable_mcp: MCP 도구 활성화 여부
        """
        # OpenAI API 키 설정
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        self.client = OpenAI(api_key=openai_api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 검색기 초기화
        if retriever is None:
            print("[RAG] 기본 Retriever 초기화 중...")
            self.retriever = Retriever()
        else:
            self.retriever = retriever

        # MCP Tool Router 초기화
        self.mcp_tool_router = None
        self.enable_mcp = enable_mcp

        if enable_mcp:
            try:
                print(f"[RAG] MCP Tool Router 초기화 중... (설정: {mcp_config_path})")

                # UniversalMCPClient 초기화 (JSON 설정)
                self.universal_client = UniversalMCPClient.from_config(mcp_config_path)

                # MCPToolRouter 초기화
                self.mcp_tool_router = MCPToolRouter(
                    openai_api_key=openai_api_key,
                    universal_client=self.universal_client,
                    model_name="gpt-4o-mini",  # Tool selection용 경량 모델
                    temperature=0.3  # 도구 선택은 낮은 temperature
                )

                print("[OK] MCP Tool Router 활성화 완료")
            except Exception as e:
                print(f"[ERROR] MCP Tool Router 초기화 실패: {e}")
                print("   -> MCP 기능 비활성화")
                self.enable_mcp = False
                self.mcp_tool_router = None
                self.universal_client = None

        print(f"[OK] RAG 파이프라인 준비 완료 (모델: {model_name})")

    def _get_system_prompt(self, mode: str) -> str:
        """
        컨텍스트 모드에 맞는 시스템 프롬프트 생성

        Args:
            mode: "local", "web", "hybrid"

        Returns:
            완성된 시스템 프롬프트
        """
        if mode not in self.CONTEXT_INSTRUCTIONS:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {list(self.CONTEXT_INSTRUCTIONS.keys())}")

        context_info = self.CONTEXT_INSTRUCTIONS[mode]
        return self.BASE_SYSTEM_PROMPT.format(
            context_instruction=context_info["instruction"],
            context_details=context_info["details"]
        )

    def create_prompt(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        RAG 프롬프트 생성 (로컬 문서 전용)

        Args:
            query: 사용자 질문
            retrieved_docs: 검색된 문서들
            conversation_history: 대화 기록

        Returns:
            OpenAI 메시지 형식의 프롬프트
        """
        # 시스템 프롬프트 (템플릿 사용)
        system_prompt = self._get_system_prompt("local")

        # 검색된 문서 포맷팅
        context = self.retriever.format_documents_for_prompt(retrieved_docs)

        # 사용자 프롬프트 구성
        user_prompt = f"""[참고 문서]
{context}

[사용자 질문]
{query}

위 참고 문서를 바탕으로 사용자의 질문에 답변해주세요.
"""

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        # 대화 기록 추가 (있으면)
        if conversation_history:
            messages.extend(conversation_history)

        # 현재 질문 추가
        messages.append({"role": "user", "content": user_prompt})

        return messages

    def _build_search_query_with_history(
        self,
        current_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_history: int = 5
    ) -> str:
        """
        이전 사용자 질문들을 현재 질문에 연결하여 검색 쿼리 생성
        
        Args:
            current_query: 현재 질문
            conversation_history: 대화 기록 (user + assistant)
            max_history: 포함할 최대 이전 질문 개수 (기본 2개)
        
        Returns:
            확장된 검색 쿼리 (이전 user 질문들 + 현재 질문)
        
        Example:
            conversation_history = [
                {"role": "user", "content": "강남역 맛집"},
                {"role": "assistant", "content": "..."},
                {"role": "user", "content": "그 근처 아파트"}
            ]
            current_query = "가격대는?"
            
            → 결과: "강남역 맛집 그 근처 아파트 가격대는?"
        """
        if not conversation_history:
            return current_query
        
        # 사용자 질문만 추출 (role="user")
        # assistant 답변은 제외 (검색 효율성 및 임베딩 품질 향상)
        user_queries = [
            msg["content"] 
            for msg in conversation_history 
            if msg.get("role") == "user"
        ][-max_history:]  # 최근 N개만 선택
        
        if not user_queries:
            return current_query
        
        # 이전 질문들 + 현재 질문 연결
        combined_query = " ".join(user_queries + [current_query])
        
        print(f"[SEARCH QUERY] 원본: {current_query}")
        print(f"[SEARCH QUERY] 확장: {combined_query}")
        
        return combined_query

    async def _execute_mcp_tools(
        self,
        query: str,
        local_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        MCP Tool Router를 사용하여 필요한 도구 실행

        Args:
            query: 사용자 질문
            local_docs: 로컬 검색 결과

        Returns:
            MCP 실행 결과
            {
                'mcp_used': bool,
                'tools_used': List[str],
                'results': Dict[str, Any],
                'direct_answer': Optional[str]
            }
        """
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
            return {
                'mcp_used': False,
                'tools_used': [],
                'results': {},
                'direct_answer': None
            }

    def _generate_from_docs(
        self,
        local_docs: List[Dict[str, Any]],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        로컬 문서만 사용하여 답변 생성 (기존 RAG 로직)

        Args:
            local_docs: 검색된 로컬 문서
            query: 사용자 질문
            conversation_history: 대화 기록

        Returns:
            답변 결과
        """
        print("[GENERATE] 전략: 로컬 문서만 사용 (RAG)")

        # 프롬프트 생성
        messages = self.create_prompt(query, local_docs, conversation_history)

        # LLM 호출
        try:
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

        except Exception as e:
            print(f"[ERROR] LLM 호출 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": local_docs,
                "web_search_used": False,
                "query": query
            }

    def _format_mcp_results_for_prompt(
        self,
        mcp_results: Dict[str, Any],
        max_results_per_tool: int = 3
    ) -> str:
        """
        MCP 도구 실행 결과를 프롬프트용 텍스트로 포맷팅

        Args:
            mcp_results: MCP 도구 실행 결과 딕셔너리
            max_results_per_tool: 각 도구당 최대 결과 개수

        Returns:
            포맷팅된 텍스트
        """
        if not mcp_results:
            return "MCP 검색 결과를 찾을 수 없습니다."

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

    def _generate_from_mcp(
        self,
        mcp_results: Dict[str, Any],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        MCP 도구 결과만 사용하여 답변 생성

        Args:
            mcp_results: MCP 도구 실행 결과
            query: 사용자 질문
            conversation_history: 대화 기록

        Returns:
            답변 결과
        """
        print("[GENERATE] 전략: MCP 도구 결과만 사용")

        # MCP 결과를 컨텍스트로 변환
        mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=3)

        # 시스템 프롬프트 (템플릿 사용)
        system_prompt = self._get_system_prompt("web")

        # 사용자 프롬프트
        user_prompt = f"""[MCP 도구 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위 검색 결과를 바탕으로 사용자의 질문에 답변해주세요.
"""

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        # LLM 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "sources": [],
                "mcp_results": mcp_results,
                "web_search_used": True,  # 호환성 유지
                "query": query,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            print(f"[ERROR] LLM 호출 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "mcp_results": mcp_results,
                "web_search_used": True,
                "query": query
            }

    def _generate_hybrid(
        self,
        local_docs: List[Dict[str, Any]],
        mcp_results: Dict[str, Any],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        로컬 문서 + MCP 도구 결과 결합하여 답변 생성

        Args:
            local_docs: 로컬 검색 결과
            mcp_results: MCP 도구 실행 결과
            query: 사용자 질문
            conversation_history: 대화 기록

        Returns:
            답변 결과
        """
        print("[GENERATE] 전략: 하이브리드 (로컬 + MCP)")

        # 로컬 문서 컨텍스트
        local_context = self.retriever.format_documents_for_prompt(local_docs)

        # MCP 결과 컨텍스트
        mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=2)

        # 시스템 프롬프트 (템플릿 사용)
        system_prompt = self._get_system_prompt("hybrid")

        # 사용자 프롬프트
        user_prompt = f"""[내부 참고 문서]
{local_context}

[최신 MCP 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위의 내부 참고 문서와 최신 검색 결과를 종합하여 사용자의 질문에 답변해주세요.
"""

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        # LLM 호출
        try:
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
                "mcp_results": mcp_results,
                "web_search_used": True,  # 호환성 유지
                "query": query,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            print(f"[ERROR] LLM 호출 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": local_docs,
                "mcp_results": mcp_results,
                "web_search_used": True,
                "query": query
            }

    def _generate_general_response(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        참고 자료 없이 LLM의 일반 지식으로 답변 생성
        """
        print("[GENERATE] 전략: 일반 대화 (No Context)")

        # 시스템 프롬프트 (일반 대화용)
        system_prompt = """당신은 친절하고 전문적인 AI 어시스턴트입니다.
사용자의 질문에 대해 당신이 가진 일반적인 지식을 바탕으로 답변해주세요.
상권 분석이나 창업과 관련된 질문이라면 일반적인 조언을 제공하고,
그 외의 질문(인사, 일반 상식 등)에는 자연스럽게 대화하세요."""

        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
            
        messages.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "sources": [],
                "mcp_results": {},
                "web_search_used": False,
                "query": query,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            print(f"[ERROR] LLM 호출 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "mcp_results": {},
                "web_search_used": False,
                "query": query
            }

    async def run(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        RAG 파이프라인 실행 (MCP Tool Router 통합)

        Args:
            query: 사용자 질문
            conversation_history: 대화 기록
            top_k: 검색할 문서 개수

        Returns:
            {
                "answer": "LLM 답변",
                "sources": [{...}, {...}],     # 참고 문서
                "mcp_results": {...},          # MCP 도구 결과 (있으면)
                "tools_used": [...],           # 사용된 도구 목록
                "web_search_used": bool,       # 호환성 유지
                "query": "원본 질문"
            }
        """
        print(f"\n[SEARCH] RAG 파이프라인 시작: {query}")

        # 0. 검색용 쿼리 생성 (이전 질문 포함)
        search_query = self._build_search_query_with_history(
            query,
            conversation_history,
            max_history=2  # 최근 2개 질문만 포함
        )

        # 1. 로컬 문서 검색 (항상 실행)
        print(f"[DOCS] 1단계: 로컬 문서 검색 (Top-{top_k})...")
        local_docs = self.retriever.search(search_query, top_k=top_k)
        print(f"   [OK] {len(local_docs)}개 문서 검색 완료")

        # 2. MCP Tool Router 실행 (LLM이 판단)
        print(f"[MCP] 2단계: LLM 기반 도구 선택 및 실행...")
        mcp_result = await self._execute_mcp_tools(query, local_docs)

        if mcp_result['mcp_used']:
            print(f"   [OK] LLM 판단: MCP 도구 사용")
            print(f"   [OK] 사용된 도구: {mcp_result['tools_used']}")
        else:
            print(f"   [OK] LLM 판단: 로컬 문서로 충분")

        # 3. 전략 선택 및 실행
        if mcp_result['mcp_used'] and mcp_result['results']:
            # Case A: MCP 도구 사용됨
            if local_docs:
                # 로컬 + MCP 하이브리드
                print(f"[STRATEGY] 하이브리드 (로컬 + MCP)")
                result = self._generate_hybrid(
                    local_docs,
                    mcp_result['results'],
                    query,
                    conversation_history
                )
            else:
                # MCP만
                print(f"[STRATEGY] MCP 도구 결과만 사용")
                result = self._generate_from_mcp(
                    mcp_result['results'],
                    query,
                    conversation_history
                )

            # 도구 목록 추가
            result['tools_used'] = mcp_result['tools_used']
            return result

        elif local_docs:
            # Case B: 로컬 문서만 사용
            print(f"[STRATEGY] 로컬 문서만 사용")
            result = self._generate_from_docs(local_docs, query, conversation_history)
            result['tools_used'] = []
            return result

        else:
            # Case C: 정보 없음 -> LLM 일반 지식으로 답변
            print(f"[STRATEGY] 정보 없음 -> 일반 대화 모드")
            return self._generate_general_response(query, conversation_history)

    async def stream_run(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 3
    ):
        """
        RAG 파이프라인 스트리밍 실행 (MCP Tool Router 통합)

        Args:
            query: 사용자 질문
            conversation_history: 대화 기록
            top_k: 검색할 문서 개수

        Yields:
            답변 청크 또는 메타데이터
        """
        print(f"\n[SEARCH] RAG 파이프라인 시작 (스트리밍): {query}")

        # 0. 검색용 쿼리 생성 (이전 질문 포함)
        search_query = self._build_search_query_with_history(
            query,
            conversation_history,
            max_history=2  # 최근 2개 질문만 포함
        )

        # 1. 로컬 문서 검색 (항상 실행)
        print(f"[DOCS] 1단계: 로컬 문서 검색 (Top-{top_k})...")
        local_docs = self.retriever.search(search_query, top_k=top_k)
        print(f"   [OK] {len(local_docs)}개 문서 검색 완료")

        # 2. MCP Tool Router 실행 (LLM이 판단)
        print(f"[MCP] 2단계: LLM 기반 도구 선택 및 실행...")
        mcp_result = await self._execute_mcp_tools(query, local_docs)

        if mcp_result['mcp_used']:
            print(f"   [OK] LLM 판단: MCP 도구 사용")
            print(f"   [OK] 사용된 도구: {mcp_result['tools_used']}")
        else:
            print(f"   [OK] LLM 판단: 로컬 문서로 충분")

        # 3. 전략 선택 및 실행
        if mcp_result['mcp_used'] and mcp_result['results']:
            # Case A: MCP 도구 사용됨
            if local_docs:
                # 하이브리드
                print(f"[STREAM] 하이브리드 스트리밍 시작")
                yield {"type": "sources", "content": local_docs}
                yield {"type": "mcp_results", "content": mcp_result['results']}
                yield {"type": "tools_used", "content": mcp_result['tools_used']}
                async for chunk in self._stream_hybrid(local_docs, mcp_result['results'], query, conversation_history):
                    yield chunk
            else:
                # MCP만
                print(f"[STREAM] MCP 결과 스트리밍 시작")
                yield {"type": "mcp_results", "content": mcp_result['results']}
                yield {"type": "tools_used", "content": mcp_result['tools_used']}
                async for chunk in self._stream_from_mcp(mcp_result['results'], query, conversation_history):
                    yield chunk

        elif local_docs:
            # Case B: 로컬 문서만 사용
            print(f"[STREAM] 로컬 문서만 사용 (스트리밍)")
            yield {"type": "sources", "content": local_docs}
            yield {"type": "tools_used", "content": []}
            async for chunk in self._stream_from_docs(local_docs, query, conversation_history):
                yield chunk

        else:
            # Case C: 정보 없음 -> LLM 일반 지식으로 답변
            print(f"[STREAM] 정보 없음 -> 일반 대화 모드 (스트리밍)")
            yield {
                "type": "answer",
                "content": ""
            }
            async for chunk in self._stream_general_response(query, conversation_history):
                yield chunk

    async def _stream_from_docs(
        self,
        local_docs: List[Dict[str, Any]],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        로컬 문서만 사용하여 스트리밍 답변 생성

        Args:
            local_docs: 검색된 로컬 문서
            query: 사용자 질문
            conversation_history: 대화 기록

        Yields:
            답변 청크
        """
        print("[STREAM] 로컬 문서 기반 스트리밍")

        # 프롬프트 생성
        messages = self.create_prompt(query, local_docs, conversation_history)

        # LLM 스트리밍 호출 (비동기)
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            # 동기 스트림을 순회하면서 바로바로 yield
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:  # 빈 문자열 제외
                        yield {
                            "type": "answer",
                            "content": content
                        }

        except Exception as e:
            print(f"[ERROR] LLM 스트리밍 실패: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }

    async def _stream_from_mcp(
        self,
        mcp_results: Dict[str, Any],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        MCP 도구 결과만 사용하여 스트리밍 답변 생성

        Args:
            mcp_results: MCP 도구 실행 결과
            query: 사용자 질문
            conversation_history: 대화 기록

        Yields:
            답변 청크
        """
        print("[STREAM] MCP 결과 기반 스트리밍")

        # MCP 결과를 컨텍스트로 변환
        mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=3)

        # 시스템 프롬프트 (템플릿 사용)
        system_prompt = self._get_system_prompt("web")

        # 사용자 프롬프트
        user_prompt = f"""[MCP 도구 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위 검색 결과를 바탕으로 사용자의 질문에 답변해주세요.
"""

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        # LLM 스트리밍 호출
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield {
                            "type": "answer",
                            "content": content
                        }

        except Exception as e:
            print(f"[ERROR] LLM 스트리밍 실패: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }

    async def _stream_general_response(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        참고 자료 없이 LLM의 일반 지식으로 스트리밍 답변 생성
        """
        print("[STREAM] 일반 대화 기반 스트리밍")

        # 시스템 프롬프트 (일반 대화용)
        system_prompt = """당신은 친절하고 전문적인 AI 어시스턴트입니다.
사용자의 질문에 대해 당신이 가진 일반적인 지식을 바탕으로 답변해주세요.
상권 분석이나 창업과 관련된 질문이라면 일반적인 조언을 제공하고,
그 외의 질문(인사, 일반 상식 등)에는 자연스럽게 대화하세요."""

        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
            
        messages.append({"role": "user", "content": query})

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield {
                            "type": "answer",
                            "content": content
                        }

        except Exception as e:
            print(f"[ERROR] LLM 스트리밍 실패: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield {
                            "type": "answer",
                            "content": content
                        }

        except Exception as e:
            print(f"[ERROR] LLM 스트리밍 실패: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }

    async def _stream_hybrid(
        self,
        local_docs: List[Dict[str, Any]],
        mcp_results: Dict[str, Any],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        로컬 문서 + MCP 도구 결과 결합하여 스트리밍 답변 생성

        Args:
            local_docs: 로컬 검색 결과
            mcp_results: MCP 도구 실행 결과
            query: 사용자 질문
            conversation_history: 대화 기록

        Yields:
            답변 청크
        """
        print("[STREAM] 하이브리드 (로컬 + MCP) 스트리밍")

        # 로컬 문서 컨텍스트
        local_context = self.retriever.format_documents_for_prompt(local_docs)

        # MCP 결과 컨텍스트
        mcp_context = self._format_mcp_results_for_prompt(mcp_results, max_results_per_tool=2)

        # 시스템 프롬프트 (템플릿 사용)
        system_prompt = self._get_system_prompt("hybrid")

        # 사용자 프롬프트
        user_prompt = f"""[내부 참고 문서]
{local_context}

[최신 MCP 검색 결과]
{mcp_context}

[사용자 질문]
{query}

위의 내부 참고 문서와 최신 검색 결과를 종합하여 사용자의 질문에 답변해주세요.
"""

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        # LLM 스트리밍 호출
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield {
                            "type": "answer",
                            "content": content
                        }

        except Exception as e:
            print(f"[ERROR] LLM 스트리밍 실패: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }


# 사용 예시
if __name__ == "__main__":
    # RAG 체인 초기화
    rag_chain = RAGChain()

    # 질문
    query = "강남에서 카페를 창업하려고 하는데 어떤 점을 고려해야 하나요?"

    # 실행
    result = rag_chain.run(query, top_k=3)

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"질문: {result['query']}")
    print(f"\n답변:\n{result['answer']}")
    print(f"\n참고 문서 ({len(result['sources'])}개):")
    for i, source in enumerate(result['sources']):
        print(f"  [{i+1}] {source['metadata'].get('source', 'unknown')} (유사도: {source['score']:.3f})")
