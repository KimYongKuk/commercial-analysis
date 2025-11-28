# FastAPI 서버 메인 파일
# OpenAI API와 연결된 실제 챗봇 서버!

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import os
import httpx
import json

# RAG 모듈 import
from rag.rag_chain import RAGChain

# ============================================
# 환경 변수 로드
# ============================================
# .env 파일에서 API 키 읽어오기
load_dotenv()

# OpenAI 클라이언트 생성
# os.getenv("OPENAI_API_KEY") = .env 파일의 OPENAI_API_KEY 값을 읽음
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# ============================================
# RAG 시스템 초기화 (Lazy Loading)
# ============================================
# 첫 요청 시에만 초기화되어 시작 속도 개선
import asyncio

# ============================================
# RAG 시스템 초기화 (Lazy Loading)
# ============================================
# 첫 요청 시에만 초기화되어 시작 속도 개선
rag_chain = None

async def get_rag_chain():
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

        # MCP 도구는 첫 요청 시 자동 발견됩니다 (Lazy Loading in RAGChain)
        print("[OK] RAG system ready! (MCP 도구는 첫 요청 시 발견됩니다)")
    return rag_chain

# ============================================
# FastAPI 앱 생성
# ============================================
app = FastAPI(
    title="JobFlex Chatbot API",
    description="상권 분석 챗봇 백엔드 (OpenAI 연결)",
    version="2.0.0"  # OpenAI 연결 완료!
)

# ============================================
# CORS 설정
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React 개발 서버
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic 모델 (데이터 검증)
# ============================================
class ChatRequest(BaseModel):
    """
    클라이언트에서 보내는 요청 형식
    """
    message: str  # 사용자 메시지
    analysis_results: Optional[List[Dict[str, Any]]] = None  # 분석 결과 (선택적)
    conversation_history: Optional[List[Dict[str, str]]] = None  # 대화 히스토리 (선택적)

class ChatResponse(BaseModel):
    """
    서버에서 반환하는 응답 형식
    """
    reply: str    # AI 챗봇의 답변
    message: str  # 원본 메시지 (디버깅용)

class RAGChatResponse(BaseModel):
    """
    RAG 챗봇 응답 형식 (참고 문서 포함)
    """
    reply: str                           # AI 챗봇의 답변
    message: str                         # 원본 메시지
    sources: Optional[List[Dict[str, Any]]] = []  # 참고 문서들
    usage: Optional[Dict[str, int]] = None        # 토큰 사용량

# ============================================
# 엔드포인트: 서버 상태 체크
# ============================================
@app.get("/")
async def root():
    return {
        "message": "JobFlex Chatbot API (OpenAI 연결 완료!)",
        "status": "healthy",
        "version": "2.0.0",
        "ai_model": "gpt-3.5-turbo"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ============================================
# 메인 챗봇 엔드포인트 (OpenAI 연결!)
# ============================================
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    실제 OpenAI API를 사용한 챗봇 엔드포인트

    작동 방식:
    1. 사용자 메시지 받기
    2. OpenAI API로 메시지 보내기
    3. AI 응답 받아서 클라이언트에게 전달
    """
    try:
        user_message = request.message
        analysis_results = request.analysis_results
        conversation_history = request.conversation_history

        # Logging
        print("\n" + "="*50)
        print("[Backend] Received user message:", user_message)
        print("[Backend] History count:", len(conversation_history) if conversation_history else 0)
        if conversation_history:
            print("[Backend] History:")
            for i, msg in enumerate(conversation_history, 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:50]
                print(f"  {i}. [{role}] {content}...")
        print("="*50 + "\n")

        # ============================================
        # System Prompt 생성 (분석 결과 포함)
        # ============================================
        base_prompt = """당신은 JobFlex의 상권 분석 전문 AI 어시스턴트입니다.

역할:
- 창업을 고려하는 사용자에게 상권 분석 도움
- 업종, 위치, 예산 등에 대한 조언 제공
- 친절하고 전문적인 톤으로 대화
- 한국어로 응답

답변 전략:
1. **부동산/상권 관련 질문**: 전문적이고 구체적인 조언을 제공하세요.
   - 분석 결과가 있으면 활용
   - 실용적이고 구체적인 답변 제공

2. **일상적인 대화/인사/잡담**: 자연스럽고 친근하게 응답하세요.
   - "안녕하세요", "고맙습니다", "오늘 날씨 어때?" 등의 질문에는 일반적인 대화로 응답
   - 상권 분석과 무관한 대화는 억지로 연결하지 마세요
   - 친근하고 따뜻한 톤 유지

응답 스타일:
- 간결하고 명확하게 (2-3문장)
- 실용적인 조언 중심
- 이모지 적절히 사용 (😊, 📊, 💡 등)"""

        # 분석 결과가 있으면 System Prompt에 추가
        if analysis_results and len(analysis_results) > 0:
            analysis_context = "\n\n=== 현재 분석된 입지 정보 ===\n"

            for i, location in enumerate(analysis_results, 1):
                analysis_context += f"\n[{i}순위] {location.get('name', '알 수 없음')}\n"
                analysis_context += f"- 종합 점수: {location.get('score', 0)}점\n"

                metrics = location.get('metrics', {})
                analysis_context += f"- 입지 점수: {metrics.get('location', 0)}점\n"
                analysis_context += f"- 유동인구 점수: {metrics.get('footTraffic', 0)}점\n"
                analysis_context += f"- 임대료 점수: {metrics.get('rent', 0)}점\n"
                analysis_context += f"- 경쟁업체 점수: {metrics.get('competition', 0)}점\n"

                descriptions = location.get('descriptions', {})
                if descriptions:
                    analysis_context += f"\n상세 분석:\n"
                    analysis_context += f"  • 입지: {descriptions.get('location', '')}\n"
                    analysis_context += f"  • 유동인구: {descriptions.get('footTraffic', '')}\n"
                    analysis_context += f"  • 임대료: {descriptions.get('rent', '')}\n"
                    analysis_context += f"  • 경쟁업체: {descriptions.get('competition', '')}\n"

            analysis_context += "\n위 분석 결과를 바탕으로 사용자의 질문에 구체적으로 답변해주세요."
            system_prompt = base_prompt + analysis_context
        else:
            system_prompt = base_prompt

        # ============================================
        # 메시지 리스트 생성 (대화 히스토리 포함)
        # ============================================
        messages_list = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # 대화 히스토리가 있으면 추가 (최근 10개만)
        if conversation_history and len(conversation_history) > 0:
            messages_list.extend(conversation_history)

        # 현재 사용자 메시지 추가
        messages_list.append({
            "role": "user",
            "content": user_message
        })

        # Logging: Messages to OpenAI
        print("[Backend] Sending to OpenAI, message count:", len(messages_list))
        print("[Backend] Message structure:")
        for i, msg in enumerate(messages_list, 1):
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:50]
            print(f"  {i}. [{role}] {content_preview}...")

        # ============================================
        # OpenAI API 호출
        # ============================================
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 사용할 AI 모델
            messages=messages_list,  # 전체 대화 히스토리 포함
            max_completion_tokens=500,  # 최대 응답 길이
            temperature=0.7,        # 창의성 (0~1, 높을수록 창의적)
        )

        # AI 응답 추출
        ai_reply = response.choices[0].message.content

        # Logging: OpenAI response
        print("[OK] [Backend] OpenAI response:", ai_reply[:100] if ai_reply else "None")
        print("="*50 + "\n")

        # 응답 반환
        return ChatResponse(
            reply=ai_reply,
            message=user_message
        )

    except Exception as e:
        # 에러 발생 시 처리
        # 예: API 키 문제, 네트워크 오류 등
        print(f"Error: {str(e)}")  # 서버 로그에 출력

        raise HTTPException(
            status_code=500,
            detail=f"챗봇 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# RAG 챗봇 엔드포인트 (지식 기반 답변)
# ============================================
@app.post("/api/rag-chat", response_model=RAGChatResponse)
async def rag_chat(request: ChatRequest):
    """
    RAG (Retrieval-Augmented Generation) 기반 챗봇

    작동 방식:
    1. 사용자 질문 받기
    2. 벡터 DB에서 관련 문서 검색 (BGE-M3-KO 임베딩)
    3. 검색된 문서를 컨텍스트로 OpenAI API 호출
    4. 지식 기반 답변 + 참고 문서 반환

    장점:
    - 업로드된 지식 문서 기반 정확한 답변
    - 출처 제공 (신뢰성)

    단점:
    - 일반 챗봇보다 느림 (2~5초)
    - 토큰 사용량 많음 (비용 약 10배)
    """
    try:
        user_message = request.message
        conversation_history = request.conversation_history

        # Logging
        print("\n" + "="*50)
        print("[RAG Backend] Received user message:", user_message)
        print("[RAG Backend] History count:", len(conversation_history) if conversation_history else 0)
        print("="*50 + "\n")

        # RAG 체인 가져오기 (Lazy Loading)
        rag = await get_rag_chain()

        # RAG 파이프라인 실행
        result = await rag.run(
            query=user_message,
            conversation_history=conversation_history,
            top_k=3  # 상위 3개 문서 검색
        )

        # Logging
        print("[OK] [RAG Backend] RAG answer generated")
        print(f"   - Sources: {len(result.get('sources', []))}")
        print(f"   - Tokens: {result.get('usage', {}).get('total_tokens', 'N/A')}")
        print("="*50 + "\n")

        # 응답 반환
        return RAGChatResponse(
            reply=result["answer"],
            message=user_message,
            sources=result.get("sources", []),
            usage=result.get("usage")
        )

    except Exception as e:
        print(f"[ERROR] [RAG Backend] Error: {str(e)}")
        print("="*50 + "\n")

        raise HTTPException(
            status_code=500,
            detail=f"RAG 챗봇 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# RAG 챗봇 스트리밍 엔드포인트
# ============================================

async def stream_rag_response(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 3
):
    """
    RAG 응답을 SSE 스트리밍으로 전송
    """
    import asyncio

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
            elif chunk_type == "web_results":
                # 웹 검색 결과 전송
                yield f"data: {json.dumps({'event': 'web_results', 'web_results': content})}\n\n"
            elif chunk_type == "answer":
                # 답변 청크 전송 (ASCII 이스케이프로 안전하게 전송)
                data = f"data: {json.dumps({'event': 'answer', 'content': content})}\n\n"
                yield data
                # 즉시 플러시를 위해 아주 짧은 대기
                await asyncio.sleep(0)
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


@app.post("/api/rag-chat-stream")
async def rag_chat_stream(request: ChatRequest):
    """
    RAG 챗봇 스트리밍 엔드포인트 (SSE)

    작동 방식:
    1. 사용자 질문 받기
    2. 벡터 DB에서 관련 문서 검색
    3. 검색된 문서를 컨텍스트로 OpenAI API 스트리밍 호출
    4. 실시간 답변 + 참고 문서 반환
    """
    print("\n" + "="*50)
    print("[RAG Stream] Received request:")
    print(f"  - query: {request.message[:50]}...")
    print(f"  - history: {len(request.conversation_history) if request.conversation_history else 0} items")
    print("="*50 + "\n")

    return StreamingResponse(
        stream_rag_response(
            query=request.message,
            conversation_history=request.conversation_history,
            top_k=3
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "none",
            "Transfer-Encoding": "chunked"
        }
    )


# ============================================
# MISO API 프록시 엔드포인트 (Streaming)
# ============================================

class MisoChatRequest(BaseModel):
    """
    MISO 챗봇 요청 형식
    """
    query: str  # 사용자 질문
    conversation_id: Optional[str] = ""  # 대화 ID (연속 대화용)
    user: Optional[str] = "user-001"  # 사용자 식별자
    inputs: Optional[Dict[str, Any]] = {}  # 추가 입력 변수

# MISO API 에러 메시지 매핑
MISO_ERROR_MESSAGES = {
    "Conversation does not exists": "요청한 대화를 찾을 수 없습니다. 새 대화를 시작해주세요.",
    "invalid_param": "잘못된 파라미터가 입력되었습니다.",
    "app_unavailable": "앱 설정을 사용할 수 없습니다. 관리자에게 문의하세요.",
    "provider_not_initialize": "모델 인증 정보가 설정되어 있지 않습니다.",
    "provider_quota_exceeded": "API 호출 한도를 초과했습니다.",
    "model_currently_not_support": "현재 모델을 사용할 수 없습니다.",
    "completion_request_error": "텍스트 생성 요청에 실패하였습니다.",
    "internal_server_error": "서버 내부 오류가 발생했습니다.",
}

async def stream_miso_response(query: str, conversation_id: str, user: str, inputs: dict):
    """
    MISO API SSE 스트리밍 응답을 프록시
    """
    miso_api_key = "app-yZ7SPwZItUQCpmOu3wyxPc0h"

    if not miso_api_key:
        error_msg = json.dumps({
            "event": "error",
            "message": "MISO_API_KEY 환경변수가 설정되지 않았습니다."
        }, ensure_ascii=False)
        yield f"data: {error_msg}\n\n"
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream(
                "POST",
                "https://api.miso.gs/ext/v1/chat",
                headers={
                    "Authorization": f"Bearer {miso_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": inputs,
                    "query": query,
                    "mode": "streaming",
                    "conversation_id": conversation_id,
                    "user": user
                }
            ) as response:
                # 에러 응답 처리
                if response.status_code != 200:
                    error_body = await response.aread()
                    try:
                        error_data = json.loads(error_body)
                        error_code = error_data.get("code", "unknown")
                        error_detail = MISO_ERROR_MESSAGES.get(
                            error_code,
                            error_data.get("message", "알 수 없는 오류가 발생했습니다.")
                        )
                    except:
                        error_detail = f"HTTP {response.status_code} 오류가 발생했습니다."

                    error_msg = json.dumps({
                        "event": "error",
                        "message": error_detail
                    }, ensure_ascii=False)
                    yield f"data: {error_msg}\n\n"
                    return

                # SSE 스트리밍 응답 전달
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"
                    else:
                        yield "\n"

        except httpx.TimeoutException:
            error_msg = json.dumps({
                "event": "error",
                "message": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            }, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
        except httpx.RequestError as e:
            error_msg = json.dumps({
                "event": "error",
                "message": f"네트워크 오류가 발생했습니다: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"

@app.post("/api/miso-chat")
async def miso_chat(request: MisoChatRequest):
    """
    MISO API 프록시 엔드포인트 (SSE Streaming)

    - 클라이언트에서 이 엔드포인트를 호출하면
    - MISO API로 요청을 전달하고
    - SSE 스트리밍 응답을 그대로 전달
    """
    print("\n" + "="*50)
    print("[MISO Proxy] Received request:")
    print(f"  - query: {request.query[:50]}...")
    print(f"  - conversation_id: {request.conversation_id}")
    print(f"  - user: {request.user}")
    print("="*50 + "\n")

    return StreamingResponse(
        stream_miso_response(
            query=request.query,
            conversation_id=request.conversation_id or "",
            user=request.user or "user-001",
            inputs=request.inputs or {}
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================
# 서버 실행 방법
# ============================================
# cd backend
# uvicorn main:app --reload --port 8000
#
# 또는 백그라운드 실행:
# nohup uvicorn main:app --port 8000 &

# ============================================
# 코드 설명 요약
# ============================================
# 1. load_dotenv() - .env 파일에서 API 키 로드
# 2. OpenAI(api_key=...) - OpenAI 클라이언트 생성
# 3. client.chat.completions.create() - AI에게 메시지 보내기
#    - model: 사용할 AI 모델 (gpt-3.5-turbo, gpt-4 등)
#    - messages: 대화 내용
#      - system: AI의 역할/성격 정의
#      - user: 사용자 메시지
#    - max_tokens: 최대 응답 길이
#    - temperature: 창의성 (0=보수적, 1=창의적)
# 4. response.choices[0].message.content - AI 응답 추출
