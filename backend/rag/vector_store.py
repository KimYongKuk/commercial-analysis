"""
ChromaDB 벡터 스토어 관리 모듈

ChromaDB를 사용하여 임베딩 벡터를 저장하고 검색합니다.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import os
from pathlib import Path


class ChromaVectorStore:
    """ChromaDB 벡터 스토어 관리 클래스"""

    def __init__(
        self,
        collection_name: str = "commercial_analysis_docs",
        persist_directory: str = None
    ):
        """
        ChromaDB 벡터 스토어 초기화

        Args:
            collection_name: 컬렉션 이름
            persist_directory: 데이터 저장 경로 (None이면 기본 경로 사용)
        """
        # 저장 경로 설정
        if persist_directory is None:
            # 현재 파일 기준 상대 경로로 data/chroma_db 설정
            current_dir = Path(__file__).parent.parent
            persist_directory = str(current_dir / "data" / "chroma_db")

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # 디렉토리 생성
        os.makedirs(persist_directory, exist_ok=True)

        print(f"[DB]  ChromaDB 초기화 중...")
        print(f"   - 저장 경로: {persist_directory}")
        print(f"   - 컬렉션: {collection_name}")

        # ChromaDB 클라이언트 생성 (영구 저장)
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        # 컬렉션 생성 또는 가져오기
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
            )
            print(f"[OK] ChromaDB 준비 완료 (문서 수: {self.collection.count()})")
        except Exception as e:
            print(f"[ERROR] ChromaDB 초기화 실패: {e}")
            raise

    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        문서를 벡터 스토어에 추가

        Args:
            texts: 문서 텍스트 리스트
            embeddings: 임베딩 벡터 리스트
            metadatas: 메타데이터 리스트 (파일명, 날짜 등)
            ids: 문서 ID 리스트 (None이면 자동 생성)

        Returns:
            생성된 문서 ID 리스트
        """
        if not texts or not embeddings:
            raise ValueError("텍스트와 임베딩이 비어있습니다.")

        if len(texts) != len(embeddings):
            raise ValueError("텍스트와 임베딩의 개수가 일치하지 않습니다.")

        # ID 자동 생성
        if ids is None:
            current_count = self.collection.count()
            ids = [f"doc_{current_count + i}" for i in range(len(texts))]

        # 메타데이터 기본값 설정
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]

        try:
            # 문서 추가
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[OK] {len(texts)}개 문서 추가 완료")
            return ids
        except Exception as e:
            print(f"[ERROR] 문서 추가 실패: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        유사도 기반 문서 검색

        Args:
            query_embedding: 검색 쿼리 임베딩 벡터
            top_k: 반환할 문서 개수
            filter_metadata: 메타데이터 필터 (예: {"source": "guide.pdf"})

        Returns:
            검색 결과 딕셔너리
            {
                "documents": [...],
                "metadatas": [...],
                "distances": [...],
                "ids": [...]
            }
        """
        try:
            # 검색 수행
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata  # 메타데이터 필터링
            )

            # 결과 정리
            formatted_results = {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }

            return formatted_results
        except Exception as e:
            print(f"[ERROR] 검색 실패: {e}")
            raise

    def delete_documents(self, ids: List[str]) -> bool:
        """
        문서 삭제

        Args:
            ids: 삭제할 문서 ID 리스트

        Returns:
            성공 여부
        """
        try:
            self.collection.delete(ids=ids)
            print(f"[OK] {len(ids)}개 문서 삭제 완료")
            return True
        except Exception as e:
            print(f"[ERROR] 문서 삭제 실패: {e}")
            return False

    def delete_collection(self) -> bool:
        """
        컬렉션 전체 삭제

        Returns:
            성공 여부
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"[OK] 컬렉션 '{self.collection_name}' 삭제 완료")
            return True
        except Exception as e:
            print(f"[ERROR] 컬렉션 삭제 실패: {e}")
            return False

    def get_document_count(self) -> int:
        """컬렉션의 문서 개수 반환"""
        return self.collection.count()

    def list_collections(self) -> List[str]:
        """모든 컬렉션 목록 반환"""
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def get_all_documents(self, limit: int = None) -> Dict[str, Any]:
        """
        모든 문서 조회

        Args:
            limit: 최대 조회 개수 (None이면 전체)

        Returns:
            문서 딕셔너리
        """
        try:
            if limit is None:
                limit = self.collection.count()

            results = self.collection.get(
                limit=limit,
                include=["documents", "metadatas", "embeddings"]
            )
            return results
        except Exception as e:
            print(f"[ERROR] 문서 조회 실패: {e}")
            raise


# 사용 예시
if __name__ == "__main__":
    from embeddings import BGEEmbeddings

    # 임베딩 모델 초기화
    embeddings_model = BGEEmbeddings()

    # 벡터 스토어 초기화
    vector_store = ChromaVectorStore()

    # 샘플 문서
    documents = [
        "강남역은 서울에서 가장 유동인구가 많은 지역 중 하나입니다.",
        "상권 분석 시 임대료, 유동인구, 경쟁업체를 고려해야 합니다.",
        "카페 창업은 위치 선정이 가장 중요합니다."
    ]

    # 문서 임베딩
    doc_embeddings = embeddings_model.embed_documents(documents)

    # 메타데이터
    metadatas = [
        {"source": "guide.txt", "category": "location"},
        {"source": "guide.txt", "category": "analysis"},
        {"source": "guide.txt", "category": "startup"}
    ]

    # 문서 추가
    ids = vector_store.add_documents(
        texts=documents,
        embeddings=doc_embeddings,
        metadatas=metadatas
    )

    print(f"\n현재 문서 수: {vector_store.get_document_count()}")

    # 검색 테스트
    query = "강남에서 카페를 창업하려고 합니다"
    query_embedding = embeddings_model.embed_query(query)

    print(f"\n검색 쿼리: {query}")
    results = vector_store.search(query_embedding, top_k=2)

    print("\n검색 결과:")
    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"],
        results["metadatas"],
        results["distances"]
    )):
        print(f"\n[{i+1}] (유사도: {1-distance:.3f})")
        print(f"문서: {doc}")
        print(f"메타데이터: {metadata}")
