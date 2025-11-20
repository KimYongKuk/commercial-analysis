"""
BGE-M3-KO 임베딩 모델을 사용한 텍스트 벡터화 모듈

BGE-M3-KO는 한국어에 최적화된 임베딩 모델입니다.
HuggingFace: dragonkue/BGE-m3-ko
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import torch


class BGEEmbeddings:
    """BGE-M3-KO 임베딩 모델 래퍼 클래스"""

    def __init__(
        self,
        model_name: str = "dragonkue/BGE-m3-ko",
        device: str = None
    ):
        """
        BGE-M3-KO 임베딩 모델 초기화

        Args:
            model_name: HuggingFace 모델 이름 (기본값: dragonkue/BGE-m3-ko)
            device: 실행 디바이스 ('cuda', 'cpu', None=자동감지)
        """
        # GPU 사용 가능 여부 자동 감지
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"🚀 BGE-M3-KO 임베딩 모델 로딩 중... (device: {self.device})")

        try:
            # SentenceTransformer 모델 로드
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"✅ 모델 로드 완료: {model_name}")
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        단일 쿼리 텍스트를 임베딩 벡터로 변환

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (list of floats)
        """
        if not text or not text.strip():
            raise ValueError("텍스트가 비어있습니다.")

        # 임베딩 생성
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # 코사인 유사도 계산을 위한 정규화
        )

        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        여러 문서를 배치로 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []

        # 빈 텍스트 필터링
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("유효한 텍스트가 없습니다.")

        # 배치 임베딩 생성
        embeddings = self.model.encode(
            valid_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(valid_texts) > 10,  # 10개 이상일 때만 진행바 표시
            batch_size=32  # 배치 크기
        )

        return embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        """임베딩 벡터의 차원 수 반환"""
        return self.model.get_sentence_embedding_dimension()


# LangChain 호환 임베딩 클래스
class LangChainBGEEmbeddings:
    """
    LangChain과 호환되는 BGE-M3-KO 임베딩 클래스

    LangChain의 Embeddings 인터페이스를 구현하여
    LangChain의 다른 컴포넌트와 함께 사용 가능
    """

    def __init__(
        self,
        model_name: str = "dragonkue/BGE-m3-ko",
        device: str = None
    ):
        """
        Args:
            model_name: HuggingFace 모델 이름
            device: 실행 디바이스
        """
        self.embeddings = BGEEmbeddings(model_name=model_name, device=device)

    def embed_query(self, text: str) -> List[float]:
        """LangChain 호환 쿼리 임베딩"""
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain 호환 문서 임베딩"""
        return self.embeddings.embed_documents(texts)


# 사용 예시
if __name__ == "__main__":
    # 기본 사용
    embeddings = BGEEmbeddings()

    # 단일 쿼리 임베딩
    query = "서울 강남구 상권 분석"
    query_embedding = embeddings.embed_query(query)
    print(f"쿼리 임베딩 차원: {len(query_embedding)}")
    print(f"임베딩 벡터 (일부): {query_embedding[:5]}")

    # 문서 배치 임베딩
    documents = [
        "강남역 주변은 유동인구가 많습니다.",
        "임대료가 비교적 높은 편입니다.",
        "경쟁업체가 많아 시장 진입이 어렵습니다."
    ]
    doc_embeddings = embeddings.embed_documents(documents)
    print(f"\n문서 개수: {len(doc_embeddings)}")
    print(f"각 문서 임베딩 차원: {len(doc_embeddings[0])}")
