"use client";

import { useState } from "react";
import { analyzeSmartFarm, runSimulation, compareStrategies } from "@/lib/api";
import ReactMarkdown from "react-markdown";

type TabType = "monitor" | "simulate" | "compare";

const CROPS = [
  { name: "딸기", emoji: "🍓" },
  { name: "토마토", emoji: "🍅" },
  { name: "파프리카", emoji: "🫑" },
];

const MONTHS = [
  "1월", "2월", "3월", "4월", "5월", "6월",
  "7월", "8월", "9월", "10월", "11월", "12월",
];

export default function SmartFarmView() {
  const [activeTab, setActiveTab] = useState<TabType>("monitor");
  const [isLoading, setIsLoading] = useState(false);

  // Monitor
  const [formData, setFormData] = useState({
    temperature: "", humidity: "", co2: "", light_intensity: "", soil_moisture: "",
  });
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);

  // Simulate
  const [simCrop, setSimCrop] = useState("딸기");
  const [simMonth, setSimMonth] = useState(1);
  const [simResult, setSimResult] = useState<any>(null);

  // Compare
  const [compareResult, setCompareResult] = useState<any>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setAnalysisResult(null);
    const data: Record<string, number> = {};
    if (formData.temperature) data.temperature = parseFloat(formData.temperature);
    if (formData.humidity) data.humidity = parseFloat(formData.humidity);
    if (formData.co2) data.co2 = parseFloat(formData.co2);
    if (formData.light_intensity) data.light_intensity = parseFloat(formData.light_intensity);
    if (formData.soil_moisture) data.soil_moisture = parseFloat(formData.soil_moisture);
    try {
      const res = await analyzeSmartFarm(data);
      setAnalysisResult(res.analysis);
    } catch { setAnalysisResult("분석 오류"); }
    finally { setIsLoading(false); }
  };

  const handleSimulate = async () => {
    setIsLoading(true);
    setSimResult(null);
    try {
      const res = await runSimulation(simCrop, 24, simMonth);
      setSimResult(res);
    } catch { setSimResult({ status: "error" }); }
    finally { setIsLoading(false); }
  };

  const handleCompare = async () => {
    setIsLoading(true);
    setCompareResult(null);
    try {
      const res = await compareStrategies(simCrop, simMonth);
      setCompareResult(res);
    } catch { setCompareResult({ status: "error" }); }
    finally { setIsLoading(false); }
  };

  const fields = [
    { key: "temperature", label: "온도 (°C)", placeholder: "22.5", icon: "🌡️" },
    { key: "humidity", label: "습도 (%)", placeholder: "65", icon: "💧" },
    { key: "co2", label: "CO2 (ppm)", placeholder: "800", icon: "🌬️" },
    { key: "light_intensity", label: "광량 (lux)", placeholder: "15000", icon: "☀️" },
    { key: "soil_moisture", label: "토양수분 (%)", placeholder: "40", icon: "🌱" },
  ];

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: "monitor", label: "환경 분석", icon: "📊" },
    { id: "simulate", label: "시뮬레이션", icon: "🔬" },
    { id: "compare", label: "전략 비교", icon: "⚡" },
  ];

  const ScoreBar = ({ label, score, color }: { label: string; score: number; color: string }) => (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-12">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-3">
        <div className={`h-3 rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-medium w-10 text-right">{score}</span>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      <header className="bg-white border-b px-6 py-4">
        <h2 className="text-xl font-bold text-gray-800">🌡️ 스마트팜 환경 관리</h2>
        <p className="text-sm text-gray-500">환경 분석, AI 시뮬레이션, 전략 비교</p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Tabs */}
          <div className="flex gap-2">
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === t.id ? "bg-farm-600 text-white" : "bg-white border text-gray-600 hover:bg-gray-50"
                }`}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {/* Monitor Tab */}
          {activeTab === "monitor" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">환경 데이터 입력</h3>
                <form onSubmit={handleAnalyze} className="space-y-3">
                  {fields.map((f) => (
                    <div key={f.key} className="flex items-center gap-2">
                      <span className="w-6">{f.icon}</span>
                      <label className="text-sm text-gray-700 w-28">{f.label}</label>
                      <input type="number" step="0.1"
                        value={formData[f.key as keyof typeof formData]}
                        onChange={(e) => setFormData((p) => ({ ...p, [f.key]: e.target.value }))}
                        placeholder={f.placeholder}
                        className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none text-sm" />
                    </div>
                  ))}
                  <button type="submit" disabled={isLoading}
                    className="w-full py-3 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 transition-colors font-medium mt-2">
                    {isLoading ? "분석 중..." : "AI 환경 분석"}
                  </button>
                </form>
              </div>
              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">분석 결과</h3>
                {analysisResult ? (
                  <div className="message-content prose prose-sm max-w-none">
                    <ReactMarkdown>{analysisResult}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-center text-gray-400 py-12">환경 데이터를 입력하세요</p>
                )}
              </div>
            </div>
          )}

          {/* Simulate Tab */}
          {activeTab === "simulate" && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">시뮬레이션 설정</h3>
                <div className="flex flex-wrap gap-4 items-end">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">작물</label>
                    <div className="flex gap-2">
                      {CROPS.map((c) => (
                        <button key={c.name} onClick={() => setSimCrop(c.name)}
                          className={`px-3 py-2 rounded-lg text-sm border ${
                            simCrop === c.name ? "bg-farm-600 text-white border-farm-600" : "border-gray-200 hover:border-farm-400"
                          }`}>
                          {c.emoji} {c.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">월</label>
                    <select value={simMonth} onChange={(e) => setSimMonth(Number(e.target.value))}
                      className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none">
                      {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                    </select>
                  </div>
                  <button onClick={handleSimulate} disabled={isLoading}
                    className="px-6 py-2 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 font-medium">
                    {isLoading ? "시뮬레이션 중..." : "24시간 시뮬레이션 실행"}
                  </button>
                </div>
              </div>

              {simResult && simResult.summary && (
                <>
                  {/* Score Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-xl border p-4 text-center">
                      <p className="text-xs text-gray-500">환경 적합도</p>
                      <p className={`text-3xl font-bold ${
                        simResult.summary.avg_score >= 70 ? "text-green-600" :
                        simResult.summary.avg_score >= 50 ? "text-yellow-600" : "text-red-600"
                      }`}>{simResult.summary.avg_score}</p>
                      <p className="text-xs text-gray-400">/ 100</p>
                    </div>
                    <div className="bg-white rounded-xl border p-4 text-center">
                      <p className="text-xs text-gray-500">에너지 소비</p>
                      <p className="text-2xl font-bold text-blue-600">{simResult.summary.total_energy_kwh}</p>
                      <p className="text-xs text-gray-400">kWh</p>
                    </div>
                    <div className="bg-white rounded-xl border p-4 text-center">
                      <p className="text-xs text-gray-500">용수 사용</p>
                      <p className="text-2xl font-bold text-cyan-600">{simResult.summary.total_water_l}</p>
                      <p className="text-xs text-gray-400">리터</p>
                    </div>
                    <div className="bg-white rounded-xl border p-4 text-center">
                      <p className="text-xs text-gray-500">DLI</p>
                      <p className="text-2xl font-bold text-orange-600">{simResult.summary.dli}</p>
                      <p className="text-xs text-gray-400">mol/m²/day</p>
                    </div>
                  </div>

                  {/* Score Breakdown */}
                  <div className="bg-white rounded-xl border p-6">
                    <h3 className="font-bold mb-3">최종 환경 점수</h3>
                    <div className="space-y-2">
                      <ScoreBar label="온도" score={simResult.summary.final_score.temperature} color="bg-red-400" />
                      <ScoreBar label="습도" score={simResult.summary.final_score.humidity} color="bg-blue-400" />
                      <ScoreBar label="CO2" score={simResult.summary.final_score.co2} color="bg-green-400" />
                      <ScoreBar label="VPD" score={simResult.summary.final_score.vpd} color="bg-purple-400" />
                    </div>
                  </div>

                  {/* Hourly Chart */}
                  {simResult.hourly_data && (
                    <div className="bg-white rounded-xl border p-6">
                      <h3 className="font-bold mb-3">시간별 환경 점수</h3>
                      <div className="flex items-end gap-1 h-32">
                        {simResult.hourly_data.map((h: any, i: number) => {
                          const height = Math.max(h.avg_score, 5);
                          const color = h.avg_score >= 70 ? "bg-green-400" :
                                       h.avg_score >= 50 ? "bg-yellow-400" : "bg-red-400";
                          return (
                            <div key={i} className="flex-1 flex flex-col items-center" title={`${h.hour}시: ${h.avg_score}점`}>
                              <span className="text-[9px] text-gray-400 mb-0.5">{h.avg_score}</span>
                              <div className={`w-full rounded-t ${color}`} style={{ height: `${height}%` }} />
                              <span className="text-[9px] text-gray-400 mt-0.5">{h.hour}</span>
                            </div>
                          );
                        })}
                      </div>
                      <p className="text-xs text-gray-400 text-center mt-1">시간 (0-23)</p>
                    </div>
                  )}

                  {/* Final State */}
                  <div className="bg-white rounded-xl border p-6">
                    <h3 className="font-bold mb-3">최종 온실 상태</h3>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                      {[
                        { label: "온도", value: `${simResult.final_state.temperature}°C`, icon: "🌡️" },
                        { label: "습도", value: `${simResult.final_state.humidity}%`, icon: "💧" },
                        { label: "CO2", value: `${simResult.final_state.co2}ppm`, icon: "🌬️" },
                        { label: "광량", value: `${simResult.final_state.light}lux`, icon: "☀️" },
                        { label: "토양수분", value: `${simResult.final_state.soil_moisture}%`, icon: "🌱" },
                        { label: "VPD", value: `${simResult.final_state.vpd}kPa`, icon: "📊" },
                      ].map((item, i) => (
                        <div key={i} className="text-center p-2 rounded-lg bg-gray-50">
                          <p className="text-lg">{item.icon}</p>
                          <p className="text-xs text-gray-500">{item.label}</p>
                          <p className="text-sm font-bold">{item.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Compare Tab */}
          {activeTab === "compare" && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">제어 전략 비교</h3>
                <div className="flex flex-wrap gap-4 items-end">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">작물</label>
                    <div className="flex gap-2">
                      {CROPS.map((c) => (
                        <button key={c.name} onClick={() => setSimCrop(c.name)}
                          className={`px-3 py-2 rounded-lg text-sm border ${
                            simCrop === c.name ? "bg-farm-600 text-white border-farm-600" : "border-gray-200"
                          }`}>
                          {c.emoji} {c.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">월</label>
                    <select value={simMonth} onChange={(e) => setSimMonth(Number(e.target.value))}
                      className="px-3 py-2 border rounded-lg">
                      {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                    </select>
                  </div>
                  <button onClick={handleCompare} disabled={isLoading}
                    className="px-6 py-2 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 font-medium">
                    {isLoading ? "비교 중..." : "전략 비교 실행"}
                  </button>
                </div>
              </div>

              {compareResult && compareResult.optimized && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Basic */}
                  <div className="bg-white rounded-xl border p-6">
                    <h4 className="font-bold text-gray-500 mb-4">📋 기본 제어</h4>
                    <div className="space-y-3">
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs text-gray-500">환경 점수</p>
                        <p className="text-3xl font-bold text-gray-600">{compareResult.basic.avg_score}</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs text-gray-500">에너지</p>
                        <p className="text-lg font-bold">{compareResult.basic.energy_kwh} kWh</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs text-gray-500">용수</p>
                        <p className="text-lg font-bold">{compareResult.basic.water_l} L</p>
                      </div>
                    </div>
                  </div>

                  {/* Optimized */}
                  <div className="bg-white rounded-xl border-2 border-farm-500 p-6">
                    <h4 className="font-bold text-farm-700 mb-4">🤖 AI 최적화</h4>
                    <div className="space-y-3">
                      <div className="text-center p-3 rounded-lg bg-farm-50">
                        <p className="text-xs text-gray-500">환경 점수</p>
                        <p className="text-3xl font-bold text-farm-700">{compareResult.optimized.avg_score}</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-farm-50">
                        <p className="text-xs text-gray-500">에너지</p>
                        <p className="text-lg font-bold">{compareResult.optimized.energy_kwh} kWh</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-farm-50">
                        <p className="text-xs text-gray-500">용수</p>
                        <p className="text-lg font-bold">{compareResult.optimized.water_l} L</p>
                      </div>
                    </div>
                  </div>

                  {/* Improvement */}
                  <div className="bg-white rounded-xl border p-6">
                    <h4 className="font-bold text-green-700 mb-4">📈 개선 효과</h4>
                    <div className="space-y-3">
                      <div className="text-center p-3 rounded-lg bg-green-50">
                        <p className="text-xs text-gray-500">점수 향상</p>
                        <p className="text-3xl font-bold text-green-600">
                          +{compareResult.improvement.score_diff}
                        </p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-green-50">
                        <p className="text-xs text-gray-500">에너지 절감</p>
                        <p className="text-lg font-bold text-green-600">
                          {compareResult.improvement.energy_saving_pct > 0 ? "-" : ""}
                          {Math.abs(compareResult.improvement.energy_saving_pct)}%
                        </p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-yellow-50">
                        <p className="text-xs text-gray-500">결론</p>
                        <p className="text-sm font-medium text-gray-700">
                          AI 최적화 제어가 환경 적합도를 높이면서도
                          에너지를 효율적으로 사용합니다.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
