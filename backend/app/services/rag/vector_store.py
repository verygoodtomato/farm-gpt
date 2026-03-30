import os
import hashlib
from pathlib import Path
from typing import Optional

import chromadb

from app.core.config import get_settings

settings = get_settings()

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"


class VectorStore:
    """ChromaDB 기반 벡터 저장소 (로컬 영속 모드)"""

    def __init__(self):
        persist_dir = settings.chroma_persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = "farm_knowledge"
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        """텍스트를 청크로 분할 (섹션 기반 + 크기 기반 혼합)"""
        sections = []
        current_section = ""
        current_heading = ""

        for line in text.split("\n"):
            if line.startswith("## "):
                if current_section.strip():
                    sections.append((current_heading, current_section.strip()))
                current_heading = line.strip("# ").strip()
                current_section = line + "\n"
            elif line.startswith("### "):
                if current_section.strip():
                    sections.append((current_heading, current_section.strip()))
                current_heading = line.strip("# ").strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"

        if current_section.strip():
            sections.append((current_heading, current_section.strip()))

        chunks = []
        for heading, section in sections:
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                words = section.split()
                current_chunk = []
                current_len = 0

                for word in words:
                    current_chunk.append(word)
                    current_len += len(word) + 1

                    if current_len >= chunk_size:
                        chunks.append(" ".join(current_chunk))
                        overlap_words = []
                        overlap_len = 0
                        for w in reversed(current_chunk):
                            overlap_len += len(w) + 1
                            overlap_words.insert(0, w)
                            if overlap_len >= overlap:
                                break
                        current_chunk = overlap_words
                        current_len = overlap_len

                if current_chunk:
                    chunks.append(" ".join(current_chunk))

        return chunks

    def _file_hash(self, filepath: Path) -> str:
        """파일 내용의 해시값 생성"""
        return hashlib.md5(filepath.read_text(encoding="utf-8").encode()).hexdigest()

    def index_knowledge_base(self, directory: Optional[Path] = None) -> dict:
        """지식베이스 디렉토리의 모든 마크다운 파일을 인덱싱"""
        kb_dir = directory or KNOWLEDGE_BASE_DIR
        if not kb_dir.exists():
            return {"status": "error", "message": f"Directory not found: {kb_dir}"}

        md_files = list(kb_dir.glob("*.md"))
        if not md_files:
            return {"status": "error", "message": "No markdown files found"}

        total_chunks = 0
        indexed_files = []

        for filepath in md_files:
            content = filepath.read_text(encoding="utf-8")
            file_hash = self._file_hash(filepath)
            source = filepath.stem

            existing = self.collection.get(
                where={"source": source},
                limit=1,
            )
            if existing["ids"] and existing["metadatas"]:
                existing_hash = existing["metadatas"][0].get("file_hash", "")
                if existing_hash == file_hash:
                    indexed_files.append({"file": filepath.name, "status": "skipped", "reason": "unchanged"})
                    continue
                old_ids = self.collection.get(where={"source": source})["ids"]
                if old_ids:
                    self.collection.delete(ids=old_ids)

            chunks = self._chunk_text(content)
            ids = [f"{source}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": source,
                    "file_hash": file_hash,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]

            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )

            total_chunks += len(chunks)
            indexed_files.append({"file": filepath.name, "status": "indexed", "chunks": len(chunks)})

        return {
            "status": "success",
            "total_files": len(md_files),
            "total_chunks": total_chunks,
            "files": indexed_files,
        }

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """쿼리와 관련된 문서 검색"""
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                search_results.append({
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "relevance": round(1 - dist, 4),
                })

        return search_results

    def get_stats(self) -> dict:
        """벡터 저장소 통계"""
        count = self.collection.count()
        return {
            "collection": self.collection_name,
            "total_documents": count,
        }


vector_store = VectorStore()
