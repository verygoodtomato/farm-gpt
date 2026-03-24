from fastapi import APIRouter, UploadFile, File, Query
from pathlib import Path

from app.services.rag.rag_service import rag_service
from app.services.rag.vector_store import KNOWLEDGE_BASE_DIR

router = APIRouter()


@router.post("/index")
async def index_knowledge_base():
    """지식베이스 전체 인덱싱 (마크다운 파일 → 벡터 DB)"""
    result = rag_service.index_knowledge_base()
    return result


@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="검색 쿼리"),
    n_results: int = Query(5, ge=1, le=20, description="결과 수"),
):
    """지식베이스 검색"""
    results = rag_service.vector_store.search(query, n_results=n_results)
    return {"query": query, "results": results}


@router.get("/stats")
async def knowledge_stats():
    """지식베이스 통계"""
    stats = rag_service.get_stats()
    # 마크다운 파일 목록 추가
    files = []
    if KNOWLEDGE_BASE_DIR.exists():
        for f in KNOWLEDGE_BASE_DIR.glob("*.md"):
            files.append({
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
            })
    stats["knowledge_files"] = files
    return stats


@router.post("/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    """마크다운 파일 업로드 후 자동 인덱싱"""
    if not file.filename.endswith(".md"):
        return {"status": "error", "message": "마크다운(.md) 파일만 지원합니다."}

    # 파일 저장
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = KNOWLEDGE_BASE_DIR / file.filename
    content = await file.read()
    filepath.write_bytes(content)

    # 인덱싱
    result = rag_service.index_knowledge_base()
    return {
        "status": "success",
        "uploaded_file": file.filename,
        "indexing_result": result,
    }


@router.get("/files")
async def list_knowledge_files():
    """지식베이스 파일 목록"""
    files = []
    if KNOWLEDGE_BASE_DIR.exists():
        for f in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
            files.append({
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "stem": f.stem,
            })
    return {"files": files, "directory": str(KNOWLEDGE_BASE_DIR)}
