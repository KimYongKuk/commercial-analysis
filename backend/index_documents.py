#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
문서 인덱싱 스크립트

data/documents/ 폴더의 모든 문서를 읽어서
ChromaDB 벡터 데이터베이스에 저장합니다.
"""

import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.document_loader import DirectoryLoader, TextSplitter
from rag.embeddings import BGEEmbeddings
from rag.vector_store import ChromaVectorStore


def main():
    print("=" * 70)
    print("📚 문서 인덱싱 시작")
    print("=" * 70)

    # 1. 문서 폴더 경로
    documents_path = Path(__file__).parent / "data" / "documents"
    print(f"\n📁 문서 폴더: {documents_path}")

    # 2. 문서 로드
    print("\n🔍 1단계: 문서 로딩 중...")
    loader = DirectoryLoader(
        directory_path=str(documents_path),
        supported_extensions=[".txt", ".pdf", ".docx", ".md"]
    )

    try:
        documents = loader.load()
        print(f"   ✓ {len(documents)}개 문서 로드 완료")

        if not documents:
            print("\n⚠️  문서가 없습니다. data/documents/ 폴더에 문서를 추가해주세요.")
            return

        # 문서 미리보기
        print("\n📄 로드된 문서 목록:")
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            content_preview = doc.page_content[:50].replace("\n", " ")
            print(f"   {i}. {source} - {content_preview}...")

    except Exception as e:
        print(f"\n❌ 문서 로드 실패: {e}")
        return

    # 3. 텍스트 분할
    print("\n✂️  2단계: 텍스트 분할 중...")
    splitter = TextSplitter(
        chunk_size=500,      # 500자 단위로 분할
        chunk_overlap=100,   # 100자 오버랩
        separator="\n\n"     # 문단 기준 분할
    )

    try:
        split_docs = splitter.split_documents(documents)
        print(f"   ✓ {len(split_docs)}개 청크로 분할 완료")

        # 청크 통계
        total_chars = sum(len(doc.page_content) for doc in split_docs)
        avg_chars = total_chars / len(split_docs) if split_docs else 0
        print(f"   - 총 문자 수: {total_chars:,}자")
        print(f"   - 평균 청크 크기: {avg_chars:.0f}자")

    except Exception as e:
        print(f"\n❌ 텍스트 분할 실패: {e}")
        return

    # 4. 임베딩 모델 초기화
    print("\n🤖 3단계: BGE-M3-KO 임베딩 모델 로딩 중...")
    try:
        embeddings_model = BGEEmbeddings()
        print(f"   ✓ 임베딩 차원: {embeddings_model.get_embedding_dimension()}")
    except Exception as e:
        print(f"\n❌ 임베딩 모델 로드 실패: {e}")
        return

    # 5. 문서 임베딩
    print("\n🔢 4단계: 문서 임베딩 중...")
    try:
        texts = [doc.page_content for doc in split_docs]
        metadatas = [doc.metadata for doc in split_docs]

        print(f"   - {len(texts)}개 청크 임베딩 시작...")
        print("   (시간이 걸릴 수 있습니다...)")

        doc_embeddings = embeddings_model.embed_documents(texts)
        print(f"   ✓ {len(doc_embeddings)}개 임베딩 생성 완료")

    except Exception as e:
        print(f"\n❌ 임베딩 생성 실패: {e}")
        return

    # 6. ChromaDB에 저장
    print("\n💾 5단계: ChromaDB에 저장 중...")
    try:
        # 기존 컬렉션 삭제 후 새로 생성
        vector_store = ChromaVectorStore(
            collection_name="commercial_analysis_docs"
        )

        # 기존 데이터가 있으면 삭제
        existing_count = vector_store.get_document_count()
        if existing_count > 0:
            print(f"   ⚠️  기존 데이터 {existing_count}개 발견")
            print("   - 기존 컬렉션 삭제 중...")
            vector_store.delete_collection()

            # 새 컬렉션 생성
            vector_store = ChromaVectorStore(
                collection_name="commercial_analysis_docs"
            )
            print("   ✓ 새 컬렉션 생성 완료")

        # 문서 추가
        ids = vector_store.add_documents(
            texts=texts,
            embeddings=doc_embeddings,
            metadatas=metadatas
        )

        print(f"   ✓ {len(ids)}개 문서 ChromaDB에 저장 완료")

    except Exception as e:
        print(f"\n❌ ChromaDB 저장 실패: {e}")
        return

    # 7. 검증
    print("\n✅ 6단계: 인덱싱 검증 중...")
    try:
        final_count = vector_store.get_document_count()
        print(f"   ✓ 최종 저장된 문서 수: {final_count}개")

        # 테스트 검색
        print("\n🔍 테스트 검색 수행...")
        test_query = "강남에서 카페 창업"
        test_embedding = embeddings_model.embed_query(test_query)
        results = vector_store.search(test_embedding, top_k=3)

        print(f"   - 검색 쿼리: '{test_query}'")
        print(f"   - 검색 결과: {len(results['documents'])}개")

        if results["documents"]:
            print("\n   📄 검색 결과 미리보기:")
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][:2],
                results["metadatas"][:2],
                results["distances"][:2]
            ), 1):
                similarity = 1 - (distance / 2)
                source = metadata.get("source", "unknown")
                preview = doc[:80].replace("\n", " ")
                print(f"   [{i}] {source} (유사도: {similarity:.3f})")
                print(f"       {preview}...")

    except Exception as e:
        print(f"\n⚠️  검증 중 오류: {e}")

    # 완료
    print("\n" + "=" * 70)
    print("🎉 문서 인덱싱 완료!")
    print("=" * 70)
    print(f"\n✅ 총 {len(split_docs)}개 문서 청크가 벡터 DB에 저장되었습니다.")
    print(f"✅ 이제 RAG 챗봇을 사용할 수 있습니다!")
    print(f"\n💡 서버 시작: cd backend && uvicorn main:app --reload")
    print(f"💡 테스트: POST http://localhost:8000/api/rag-chat")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
