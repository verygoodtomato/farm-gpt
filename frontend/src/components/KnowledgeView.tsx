"use client";

import { useState, useEffect } from "react";
import {
  indexKnowledgeBase,
  searchKnowledge,
  getKnowledgeStats,
  getKnowledgeFiles,
} from "@/lib/api";

interface KnowledgeFile {
  name: string;
  size_kb: number;
  stem: string;
}

interface SearchResult {
  content: string;
  source: string;
  relevance: number;
}

export default function KnowledgeView() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [stats, setStats] = useState<{ total_documents: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [indexResult, setIndexResult] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [filesRes, statsRes] = await Promise.all([
        getKnowledgeFiles(),
        getKnowledgeStats(),
      ]);
      setFiles(filesRes.files || []);
      setStats(statsRes);
    } catch {
      // API not available yet
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleIndex = async () => {
    setIsIndexing(true);
    setIndexResult(null);
    try {
      const result = await indexKnowledgeBase();
      setIndexResult(
        `인덱싱 완료: ${result.total_files}개 파일, ${result.total_chunks}개 청크`
      );
      loadData();
    } catch (e) {
      setIndexResult("인덱싱 실패. ChromaDB 연결을 확인하세요.");
    } finally {
      setIsIndexing(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const result = await searchKnowledge(searchQuery);
      setSearchResults(result.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const SOURCE_LABELS: Record<string, string> = {
    strawberry: "딸기 재배",
    tomato: "토마토 재배",
    paprika: "파프리카 재배",
    smartfarm_basics: "스마트팜 기초",
    pest_management: "병해충 관리",
    climate_farming: "기후변화 농업",
  };

  return (
    <div className="flex flex-col h-full">
      <header className="bg-white border-b px-6 py-4">
        <h2 className="text-xl font-bold text-gray-800">📚 지식베이스 관리</h2>
        <p className="text-sm text-gray-500">
          RAG에 사용되는 농업 지식 문서를 관리하고 검색합니다
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Stats & Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl border p-5">
              <p className="text-sm text-gray-500">등록된 문서</p>
              <p className="text-3xl font-bold text-farm-700">{files.length}</p>
            </div>
            <div className="bg-white rounded-xl border p-5">
              <p className="text-sm text-gray-500">벡터 청크 수</p>
              <p className="text-3xl font-bold text-farm-700">
                {stats?.total_documents ?? "-"}
              </p>
            </div>
            <div className="bg-white rounded-xl border p-5 flex flex-col justify-between">
              <p className="text-sm text-gray-500 mb-2">인덱싱</p>
              <button
                onClick={handleIndex}
                disabled={isIndexing}
                className="w-full py-2 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 transition-colors text-sm font-medium"
              >
                {isIndexing ? "인덱싱 중..." : "전체 인덱싱 실행"}
              </button>
              {indexResult && (
                <p className="text-xs text-gray-500 mt-1">{indexResult}</p>
              )}
            </div>
          </div>

          {/* File List */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold text-lg mb-4">지식 문서 목록</h3>
            {files.length === 0 ? (
              <p className="text-gray-400 text-center py-4">
                등록된 문서가 없습니다
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {files.map((file) => (
                  <div
                    key={file.name}
                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:border-farm-300 transition-colors"
                  >
                    <span className="text-2xl">📄</span>
                    <div className="flex-1">
                      <p className="font-medium text-gray-700">
                        {SOURCE_LABELS[file.stem] || file.stem}
                      </p>
                      <p className="text-xs text-gray-400">
                        {file.name} ({file.size_kb} KB)
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Search */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold text-lg mb-4">지식베이스 검색</h3>
            <form onSubmit={handleSearch} className="flex gap-3 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색어를 입력하세요 (예: 딸기 온도 관리)"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-farm-500"
              />
              <button
                type="submit"
                disabled={isSearching || !searchQuery.trim()}
                className="px-5 py-2 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 transition-colors text-sm font-medium"
              >
                {isSearching ? "검색 중..." : "검색"}
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className="space-y-3">
                {searchResults.map((result, i) => (
                  <div key={i} className="p-4 rounded-lg bg-gray-50 border">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs bg-farm-100 text-farm-700 px-2 py-0.5 rounded-full">
                        {SOURCE_LABELS[result.source] || result.source}
                      </span>
                      <span className="text-xs text-gray-400">
                        관련도: {(result.relevance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-4">
                      {result.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
