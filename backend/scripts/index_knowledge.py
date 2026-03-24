"""
지식베이스 인덱싱 스크립트
사용법: python -m scripts.index_knowledge
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag.vector_store import vector_store, KNOWLEDGE_BASE_DIR


def main():
    print(f"📚 지식베이스 디렉토리: {KNOWLEDGE_BASE_DIR}")
    print(f"📂 마크다운 파일 목록:")

    md_files = list(KNOWLEDGE_BASE_DIR.glob("*.md"))
    for f in md_files:
        print(f"   - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    print(f"\n총 {len(md_files)}개 파일 발견")
    print("인덱싱 시작...\n")

    result = vector_store.index_knowledge_base()

    if result["status"] == "success":
        print(f"✅ 인덱싱 완료!")
        print(f"   파일 수: {result['total_files']}")
        print(f"   청크 수: {result['total_chunks']}")
        print("\n파일별 상세:")
        for file_info in result["files"]:
            status = file_info["status"]
            if status == "indexed":
                print(f"   ✅ {file_info['file']} → {file_info['chunks']}개 청크")
            elif status == "skipped":
                print(f"   ⏭️  {file_info['file']} (변경 없음)")
    else:
        print(f"❌ 인덱싱 실패: {result['message']}")

    # 통계 출력
    stats = vector_store.get_stats()
    print(f"\n📊 벡터 저장소 통계:")
    print(f"   컬렉션: {stats['collection']}")
    print(f"   총 문서 수: {stats['total_documents']}")


if __name__ == "__main__":
    main()
