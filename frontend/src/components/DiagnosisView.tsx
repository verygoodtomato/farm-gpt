"use client";

import { useState, useRef } from "react";
import { diagnoseFromText, diagnoseFromImage } from "@/lib/api";
import ReactMarkdown from "react-markdown";

const CROP_OPTIONS = [
  "딸기", "토마토", "파프리카", "고추", "배추", "사과",
  "오이", "감자", "상추", "포도", "벼", "기타",
];

export default function DiagnosisView() {
  const [cropType, setCropType] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<"text" | "image">("text");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cropType || !symptoms.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      const response = await diagnoseFromText(cropType, symptoms);
      setResult(response.diagnosis);
    } catch {
      setResult("진단 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsLoading(true);
    setResult(null);

    try {
      const response = await diagnoseFromImage(
        selectedFile,
        cropType || undefined,
        symptoms || undefined
      );
      setResult(response.diagnosis);
    } catch {
      setResult("이미지 진단 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="flex flex-col h-full">
      <header className="bg-white border-b px-6 py-4">
        <h2 className="text-xl font-bold text-gray-800">🔍 작물 병해충 진단</h2>
        <p className="text-sm text-gray-500">
          텍스트 또는 이미지로 병해충을 진단하고 대처법을 확인하세요
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input */}
          <div className="bg-white rounded-xl border p-6">
            {/* Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setMode("text")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  mode === "text"
                    ? "bg-farm-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                📝 텍스트 진단
              </button>
              <button
                onClick={() => setMode("image")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  mode === "image"
                    ? "bg-farm-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                📷 이미지 진단
              </button>
            </div>

            <form
              onSubmit={mode === "text" ? handleTextSubmit : handleImageSubmit}
              className="space-y-4"
            >
              {/* Crop Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  작물 선택 {mode === "image" && "(선택사항)"}
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {CROP_OPTIONS.map((crop) => (
                    <button
                      key={crop}
                      type="button"
                      onClick={() => setCropType(cropType === crop ? "" : crop)}
                      className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
                        cropType === crop
                          ? "bg-farm-600 text-white border-farm-600"
                          : "border-gray-200 text-gray-600 hover:border-farm-400"
                      }`}
                    >
                      {crop}
                    </button>
                  ))}
                </div>
              </div>

              {mode === "text" ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    증상 설명
                  </label>
                  <textarea
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    rows={5}
                    placeholder="증상을 자세히 설명해주세요. 예: 잎에 갈색 반점이 생기고, 아래쪽 잎부터 시들어가고 있습니다..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-farm-500 resize-none"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    이미지 업로드
                  </label>
                  {previewUrl ? (
                    <div className="relative">
                      <img
                        src={previewUrl}
                        alt="업로드된 이미지"
                        className="w-full h-48 object-cover rounded-lg border"
                      />
                      <button
                        type="button"
                        onClick={clearFile}
                        className="absolute top-2 right-2 bg-red-500 text-white w-7 h-7 rounded-full flex items-center justify-center text-sm hover:bg-red-600"
                      >
                        x
                      </button>
                      <p className="text-xs text-gray-500 mt-1">
                        {selectedFile?.name} (
                        {((selectedFile?.size || 0) / 1024).toFixed(0)} KB)
                      </p>
                    </div>
                  ) : (
                    <label className="block border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-farm-400 transition-colors">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <p className="text-3xl mb-2">📷</p>
                      <p className="text-sm text-gray-500">
                        클릭하여 이미지를 업로드하세요
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        JPG, PNG (최대 10MB)
                      </p>
                    </label>
                  )}

                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      추가 정보 (선택사항)
                    </label>
                    <input
                      type="text"
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      placeholder="예: 3일 전부터 증상 발견, 하우스 내부 습도 높음"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-farm-500"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={
                  isLoading ||
                  (mode === "text" && (!cropType || !symptoms.trim())) ||
                  (mode === "image" && !selectedFile)
                }
                className="w-full py-3 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 transition-colors font-medium"
              >
                {isLoading ? "AI 진단 중..." : "병해충 진단 요청"}
              </button>
            </form>
          </div>

          {/* Result */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold text-lg mb-4">진단 결과</h3>
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin text-4xl mb-3">🔬</div>
                <p className="text-gray-500">AI가 분석 중입니다...</p>
              </div>
            ) : result ? (
              <div className="message-content prose prose-sm max-w-none">
                <ReactMarkdown>{result}</ReactMarkdown>
              </div>
            ) : (
              <div className="text-center text-gray-400 py-12">
                <p className="text-4xl mb-3">🩺</p>
                <p>
                  {mode === "text"
                    ? "작물과 증상을 입력하고 진단을 요청하세요"
                    : "이미지를 업로드하고 진단을 요청하세요"}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
