# MISO API 통합 가이드

이 문서는 프로젝트에서 MISO 에이전트 API를 사용하기 위한 통합 가이드입니다.

## 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [환경 설정](#환경-설정)
4. [백엔드 구현](#백엔드-구현)
5. [프론트엔드 구현](#프론트엔드-구현)
6. [에러 처리](#에러-처리)
7. [테스트](#테스트)
8. [트러블슈팅](#트러블슈팅)

---

## 개요

### MISO API란?
사내 챗봇 플랫폼에서 외부 접근을 위해 제공하는 에이전트 API입니다.

### 주요 특징
- **SSE(Server-Sent Events) 스트리밍** 지원
- **대화 연속성** (conversation_id)
- **에이전트 추론 로그** 제공 (agent_thoughts)

### API 엔드포인트
```
POST https://api.miso.gs/ext/v1/chat
```

---

## 아키텍처

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  Frontend   │ --> │  FastAPI Proxy  │ --> │  MISO API   │
│  (React)    │     │  (Backend)      │     │             │
└─────────────┘     └─────────────────┘     └─────────────┘
     │                      │                      │
     │   /api/miso-chat     │   api.miso.gs/ext/   │
     │   (SSE Stream)       │   v1/chat            │
     └──────────────────────┴──────────────────────┘
```

### 프록시 서버를 사용하는 이유
1. **API 키 보안**: 클라이언트에 API 키 노출 방지
2. **CORS 해결**: 브라우저의 CORS 정책 우회
3. **요청/응답 가공**: 필요시 데이터 변환 가능

---

## 환경 설정

### 1. 필수 패키지 설치

**백엔드 (Python)**
```bash
cd backend
pip install httpx
```

**프론트엔드 (Node.js)**
```bash
npm install
```

### 2. 환경 변수 설정

`backend/.env` 파일에 추가:
```env
MISO_API_KEY=app-xxxxxxxxxxxxxxxxxxxxx
```

### 3. 서버 실행

**백엔드**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**프론트엔드**
```bash
npm run dev
```

---

## 백엔드 구현

### 파일 위치
`backend/main.py`

### 주요 코드

#### 1. Import 추가
```python
from fastapi.responses import StreamingResponse
import httpx
import json
```

#### 2. 요청 모델
```python
class MisoChatRequest(BaseModel):
    query: str                              # 사용자 질문
    conversation_id: Optional[str] = ""     # 대화 ID (연속 대화용)
    user: Optional[str] = "user-001"        # 사용자 식별자
    inputs: Optional[Dict[str, Any]] = {}   # 추가 입력 변수
```

#### 3. 스트리밍 함수
```python
async def stream_miso_response(query: str, conversation_id: str, user: str, inputs: dict):
    miso_api_key = os.getenv("MISO_API_KEY")

    async with httpx.AsyncClient(timeout=60.0) as client:
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
            async for line in response.aiter_lines():
                if line:
                    yield f"{line}\n"
                else:
                    yield "\n"
```

#### 4. 엔드포인트
```python
@app.post("/api/miso-chat")
async def miso_chat(request: MisoChatRequest):
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
```

---

## 프론트엔드 구현

### 파일 위치
`components/Chatbot.tsx`

### 주요 코드

#### 1. 상태 관리
```typescript
const [conversationId, setConversationId] = useState('');  // MISO 대화 ID
const [isLoading, setIsLoading] = useState(false);         // 로딩 상태
```

#### 2. API 호출
```typescript
const response = await fetch('http://localhost:8000/api/miso-chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: currentInput,
    conversation_id: conversationId,
    user: 'user-001',
    inputs: {},
  }),
});
```

#### 3. SSE 스트리밍 처리
```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let currentContent = '';

if (reader) {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data:')) {
        const jsonStr = line.slice(5).trim();
        if (!jsonStr || jsonStr === '[DONE]') continue;

        const data = JSON.parse(jsonStr);

        // conversation_id 저장 (연속 대화용)
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }

        // 이벤트 타입에 따른 처리
        if (data.event === 'agent_message' || data.event === 'message') {
          if (data.answer) {
            currentContent += data.answer;
          }
        } else if (data.event === 'message_replace') {
          currentContent = data.answer || '';
        } else if (data.event === 'error') {
          // 에러 처리
        }

        // UI 업데이트
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, text: currentContent }
              : msg
          )
        );
      }
    }
  }
}
```

---

## 에러 처리

### 에러 코드 및 한글 메시지

| 에러 코드 | 한글 메시지 | 해결 방법 |
|-----------|-------------|-----------|
| `Conversation does not exists` | 요청한 대화를 찾을 수 없습니다 | 새 대화 시작 (conversation_id 초기화) |
| `invalid_param` | 잘못된 파라미터가 입력되었습니다 | 요청 파라미터 확인 |
| `app_unavailable` | 앱 설정을 사용할 수 없습니다 | 관리자에게 문의 |
| `provider_not_initialize` | 모델 인증 정보가 설정되어 있지 않습니다 | MISO 앱 설정 확인 |
| `provider_quota_exceeded` | API 호출 한도를 초과했습니다 | 할당량 확인 |
| `model_currently_not_support` | 현재 모델을 사용할 수 없습니다 | 모델 설정 확인 |
| `completion_request_error` | 텍스트 생성 요청에 실패하였습니다 | 재시도 |
| `internal_server_error` | 서버 내부 오류가 발생했습니다 | 관리자에게 문의 |

### 백엔드 에러 처리 예시
```python
MISO_ERROR_MESSAGES = {
    "Conversation does not exists": "요청한 대화를 찾을 수 없습니다. 새 대화를 시작해주세요.",
    "invalid_param": "잘못된 파라미터가 입력되었습니다.",
    # ... 기타 에러
}
```

### 프론트엔드 에러 처리 예시
```typescript
if (data.event === 'error') {
  currentContent = data.message || '오류가 발생했습니다.';
  setMessages((prev) =>
    prev.map((msg) =>
      msg.id === aiMessageId
        ? { ...msg, text: currentContent, isStreaming: false }
        : msg
    )
  );
}
```

---

## 테스트

### 테스트 체크리스트

- [ ] 환경 변수 설정 확인 (`MISO_API_KEY`)
- [ ] 백엔드 서버 실행 확인 (port 8000)
- [ ] 프론트엔드 서버 실행 확인 (port 5173)
- [ ] 챗봇 UI 정상 표시
- [ ] 메시지 전송 및 스트리밍 응답 확인
- [ ] 연속 대화 테스트 (conversation_id 유지)
- [ ] 에러 발생 시 한글 메시지 표시 확인

### cURL 테스트
```bash
curl -X POST 'http://localhost:8000/api/miso-chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "안녕하세요",
    "conversation_id": "",
    "user": "test-user"
  }'
```

---

## 트러블슈팅

### 1. MISO_API_KEY 환경변수 오류
**증상**: "MISO_API_KEY 환경변수가 설정되지 않았습니다" 메시지

**해결**:
1. `backend/.env` 파일 확인
2. `.env` 파일에 `MISO_API_KEY=app-xxx` 형식으로 추가
3. 백엔드 서버 재시작

### 2. CORS 오류
**증상**: 브라우저 콘솔에 CORS 관련 에러

**해결**:
1. FastAPI의 CORS 설정 확인
2. 프론트엔드 주소가 `allow_origins`에 포함되어 있는지 확인

### 3. 스트리밍이 작동하지 않음
**증상**: 응답이 한 번에 표시됨

**해결**:
1. 백엔드에서 `mode: "streaming"` 설정 확인
2. `StreamingResponse` 헤더 확인
3. 프론트엔드에서 `ReadableStream` 처리 로직 확인

### 4. 대화가 이어지지 않음
**증상**: 이전 대화 맥락을 기억하지 못함

**해결**:
1. `conversation_id` 상태가 올바르게 저장되는지 확인
2. 다음 요청에 `conversation_id`가 포함되는지 확인

---

## 참고 자료

### MISO API 공식 명세
- 엔드포인트: `POST https://api.miso.gs/ext/v1/chat`
- 인증: `Authorization: Bearer {API_KEY}`

### 요청 Body
```json
{
  "inputs": {},
  "query": "사용자 질문",
  "mode": "streaming",
  "conversation_id": "",
  "user": "user-id"
}
```

### 응답 형식 (Blocking)
```json
{
  "id": "message_id",
  "conversation_id": "conversation_id",
  "answer": "모델의 응답 텍스트",
  "agent_thoughts": [],
  "created_at": "2025-11-18T23:24:50.170Z"
}
```

### SSE 이벤트 타입
- `message` / `agent_message`: 메시지 내용 추가
- `message_replace`: 전체 메시지 대체
- `agent_thought`: 에이전트 추론 과정
- `error`: 에러 발생

---

## 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0.0 | 2025-11-19 | 최초 작성 - MISO API 스트리밍 통합 |
