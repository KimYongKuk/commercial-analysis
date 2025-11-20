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


class RAGChain:
    """RAG 파이프라인 클래스"""

    def __init__(
        self,
        openai_api_key: str = None,
        retriever: Retriever = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        RAG 파이프라인 초기화

        Args:
            openai_api_key: OpenAI API 키
            retriever: 검색기 인스턴스
            model_name: OpenAI 모델 이름
            temperature: 생성 온도 (0~2)
            max_tokens: 최대 토큰 수
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
            print("🔧 기본 Retriever 초기화 중...")
            self.retriever = Retriever()
        else:
            self.retriever = retriever

        print(f"✅ RAG 파이프라인 준비 완료 (모델: {model_name})")

    def create_prompt(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        RAG 프롬프트 생성

        Args:
            query: 사용자 질문
            retrieved_docs: 검색된 문서들
            conversation_history: 대화 기록

        Returns:
            OpenAI 메시지 형식의 프롬프트
        """
        # 시스템 프롬프트
        system_prompt = """당신은 상권 분석 및 창업 컨설팅 전문가입니다.
제공된 참고 문서를 바탕으로 정확하고 유용한 답변을 제공해주세요.

답변 시 주의사항:
1. 참고 문서의 내용을 기반으로 답변하되, 자연스럽게 설명해주세요.
2. 참고 문서에 없는 내용은 "제공된 자료에는 해당 정보가 없습니다"라고 명확히 말해주세요.
3. 가능한 한 구체적이고 실용적인 조언을 제공해주세요.
4. 필요시 출처를 언급해주세요.
"""

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

    def run(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        RAG 파이프라인 실행

        Args:
            query: 사용자 질문
            conversation_history: 대화 기록
            top_k: 검색할 문서 개수

        Returns:
            {
                "answer": "LLM 답변",
                "sources": [{...}, {...}],  # 참고 문서
                "query": "원본 질문"
            }
        """
        print(f"\n🔍 RAG 파이프라인 시작: {query}")

        # 1. 관련 문서 검색
        print(f"📚 1단계: 문서 검색 (Top-{top_k})...")
        retrieved_docs = self.retriever.search(query, top_k=top_k)

        if not retrieved_docs:
            return {
                "answer": "죄송합니다. 관련된 정보를 찾을 수 없습니다. 다른 질문을 해주시겠어요?",
                "sources": [],
                "query": query
            }

        print(f"   ✓ {len(retrieved_docs)}개 문서 검색 완료")

        # 2. 프롬프트 생성
        print(f"📝 2단계: 프롬프트 생성...")
        messages = self.create_prompt(query, retrieved_docs, conversation_history)

        # 3. LLM 호출
        print(f"🤖 3단계: LLM 답변 생성...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content
            print(f"   ✓ 답변 생성 완료 (토큰: {response.usage.total_tokens})")

            return {
                "answer": answer,
                "sources": retrieved_docs,
                "query": query,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": retrieved_docs,
                "query": query
            }

    def stream_run(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 3
    ):
        """
        RAG 파이프라인 스트리밍 실행

        Args:
            query: 사용자 질문
            conversation_history: 대화 기록
            top_k: 검색할 문서 개수

        Yields:
            답변 청크 또는 메타데이터
        """
        print(f"\n🔍 RAG 파이프라인 시작 (스트리밍): {query}")

        # 1. 관련 문서 검색
        retrieved_docs = self.retriever.search(query, top_k=top_k)

        if not retrieved_docs:
            yield {
                "type": "answer",
                "content": "죄송합니다. 관련된 정보를 찾을 수 없습니다."
            }
            return

        # 검색된 문서 정보 먼저 반환
        yield {
            "type": "sources",
            "content": retrieved_docs
        }

        # 2. 프롬프트 생성
        messages = self.create_prompt(query, retrieved_docs, conversation_history)

        # 3. LLM 스트리밍 호출
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "answer",
                        "content": chunk.choices[0].delta.content
                    }

        except Exception as e:
            print(f"❌ LLM 스트리밍 실패: {e}")
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
