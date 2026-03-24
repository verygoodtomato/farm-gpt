"use client";

import { useState } from "react";
import { getMarketInfo, predictPrice, predictYield, getPriceHistory } from "@/lib/api";
import ReactMarkdown from "react-markdown";

const POPULAR_CROPS = [
  { name: "딸기", emoji: "🍓" },
  { name: "토마토", emoji: "🍅" },
  { name: "파프리카", emoji: "🫑" },
  { name: "사과", emoji: "🍎" },
  { name: "배추", emoji: "🥬" },
  { name: "고추", emoji: "🌶️" },
  { name: "감자", emoji: "🥔" },
  { name: "쌀", emoji: "🌾" },
];

type TabType = "market" | "price" | "yield";

interface PricePoint {
  month: string;
  price: number;
}

interface PricePrediction {
  month: string;
  predicted_price: number;
  price_range?: { low: number; high: number };
  confidence?: number;
  note?: string;
}

export default function AnalyticsView() {
  const [selectedCrop, setSelectedCrop] = useState("");
  const [activeTab, setActiveTab] = useState<TabType>("market");
  const [isLoading, setIsLoading] = useState(false);

  // Market analysis
  const [marketResult, setMarketResult] = useState<string | null>(null);

  // Price prediction
  const [pricePredictions, setPricePredictions] = useState<PricePrediction[]>([]);
  const [priceAnalysis, setPriceAnalysis] = useState<string | null>(null);
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);

  // Yield prediction
  const [yieldForm, setYieldForm] = useState({
    area: "1000",
    tempDay: "",
    tempNight: "",
    co2: "",
  });
  const [yieldResult, setYieldResult] = useState<any>(null);

  const handleCropSelect = async (cropName: string) => {
    setSelectedCrop(cropName);
    if (activeTab === "market") {
      await loadMarketInfo(cropName);
    } else if (activeTab === "price") {
      await loadPricePrediction(cropName);
    }
  };

  const loadMarketInfo = async (crop: string) => {
    setIsLoading(true);
    setMarketResult(null);
    try {
      const response = await getMarketInfo(crop);
      setMarketResult(response.analysis);
    } catch {
      setMarketResult("분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadPricePrediction = async (crop: string) => {
    setIsLoading(true);
    setPricePredictions([]);
    setPriceAnalysis(null);
    try {
      const [predRes, histRes] = await Promise.all([
        predictPrice(crop, 6),
        getPriceHistory(crop),
      ]);
      setPricePredictions(predRes.predictions || []);
      setPriceAnalysis(predRes.ai_analysis || null);
      setPriceHistory(histRes.monthly_prices || []);
    } catch {
      setPriceAnalysis("가격 예측 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleYieldPredict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCrop) return;

    setIsLoading(true);
    setYieldResult(null);
    try {
      const result = await predictYield({
        crop_type: selectedCrop,
        area_m2: parseFloat(yieldForm.area) || 1000,
        avg_temp_day: yieldForm.tempDay ? parseFloat(yieldForm.tempDay) : undefined,
        avg_temp_night: yieldForm.tempNight ? parseFloat(yieldForm.tempNight) : undefined,
        co2_level: yieldForm.co2 ? parseFloat(yieldForm.co2) : undefined,
      });
      setYieldResult(result);
    } catch {
      setYieldResult({ status: "error", message: "예측 실패" });
    } finally {
      setIsLoading(false);
    }
  };

  const maxPrice = Math.max(...priceHistory.map((p) => p.price).filter(Boolean), 1);

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: "market", label: "시장 분석", icon: "📈" },
    { id: "price", label: "가격 예측", icon: "💰" },
    { id: "yield", label: "수확량 예측", icon: "🌾" },
  ];

  return (
    <div className="flex flex-col h-full">
      <header className="bg-white border-b px-6 py-4">
        <h2 className="text-xl font-bold text-gray-800">📊 데이터 분석</h2>
        <p className="text-sm text-gray-500">
          농산물 시장 동향, 가격 예측, 수확량 예측
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Tabs */}
          <div className="flex gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  if (selectedCrop && tab.id === "market") loadMarketInfo(selectedCrop);
                  if (selectedCrop && tab.id === "price") loadPricePrediction(selectedCrop);
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-farm-600 text-white"
                    : "bg-white border text-gray-600 hover:bg-gray-50"
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          {/* Crop Selection */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold text-sm text-gray-500 mb-3">작물 선택</h3>
            <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
              {POPULAR_CROPS.map((crop) => (
                <button
                  key={crop.name}
                  onClick={() => handleCropSelect(crop.name)}
                  disabled={isLoading}
                  className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all ${
                    selectedCrop === crop.name
                      ? "border-farm-500 bg-farm-50"
                      : "border-gray-100 hover:border-farm-300"
                  } disabled:opacity-50`}
                >
                  <span className="text-2xl">{crop.emoji}</span>
                  <span className="text-xs font-medium text-gray-700 mt-1">
                    {crop.name}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Market Analysis */}
          {activeTab === "market" && (
            <div className="bg-white rounded-xl border p-6">
              <h3 className="font-bold text-lg mb-4">
                {selectedCrop ? `${selectedCrop} 시장 분석` : "시장 분석"}
              </h3>
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin text-3xl mb-2">⏳</div>
                  <p className="text-gray-500 text-sm">AI 분석 중...</p>
                </div>
              ) : marketResult ? (
                <div className="message-content prose prose-sm max-w-none">
                  <ReactMarkdown>{marketResult}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">작물을 선택하세요</p>
              )}
            </div>
          )}

          {/* Price Prediction */}
          {activeTab === "price" && (
            <div className="space-y-6">
              {/* Price Chart */}
              {priceHistory.length > 0 && (
                <div className="bg-white rounded-xl border p-6">
                  <h3 className="font-bold text-lg mb-4">월별 평균 가격</h3>
                  <div className="flex items-end gap-1 h-40">
                    {priceHistory.map((point, i) => {
                      const height = point.price > 0 ? (point.price / maxPrice) * 100 : 0;
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <span className="text-[10px] text-gray-500 mb-1">
                            {point.price > 0 ? `${(point.price / 1000).toFixed(0)}k` : "-"}
                          </span>
                          <div
                            className={`w-full rounded-t transition-all ${
                              point.price > 0 ? "bg-farm-400" : "bg-gray-100"
                            }`}
                            style={{ height: `${Math.max(height, 2)}%` }}
                          />
                          <span className="text-[10px] text-gray-400 mt-1">
                            {point.month.replace("월", "")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Predictions */}
              {pricePredictions.length > 0 && (
                <div className="bg-white rounded-xl border p-6">
                  <h3 className="font-bold text-lg mb-4">가격 예측 (향후 6개월)</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {pricePredictions.map((pred, i) => (
                      <div key={i} className="p-3 rounded-lg bg-gray-50 border">
                        <p className="text-sm font-medium text-gray-700">{pred.month}</p>
                        {pred.note ? (
                          <p className="text-sm text-gray-400">{pred.note}</p>
                        ) : (
                          <>
                            <p className="text-lg font-bold text-farm-700">
                              {pred.predicted_price?.toLocaleString()}원
                            </p>
                            {pred.price_range && (
                              <p className="text-xs text-gray-400">
                                {pred.price_range.low.toLocaleString()} ~{" "}
                                {pred.price_range.high.toLocaleString()}
                              </p>
                            )}
                            {pred.confidence && (
                              <p className="text-xs text-farm-600">
                                신뢰도: {(pred.confidence * 100).toFixed(0)}%
                              </p>
                            )}
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Analysis */}
              {priceAnalysis && (
                <div className="bg-white rounded-xl border p-6">
                  <h3 className="font-bold text-lg mb-4">AI 시장 전망</h3>
                  <div className="message-content prose prose-sm max-w-none">
                    <ReactMarkdown>{priceAnalysis}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Yield Prediction */}
          {activeTab === "yield" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">환경 조건 입력</h3>
                {!selectedCrop ? (
                  <p className="text-center text-gray-400 py-8">
                    먼저 작물을 선택하세요
                  </p>
                ) : (
                  <form onSubmit={handleYieldPredict} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        재배 면적 (m²)
                      </label>
                      <input
                        type="number"
                        value={yieldForm.area}
                        onChange={(e) =>
                          setYieldForm((f) => ({ ...f, area: e.target.value }))
                        }
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          주간 평균온도 (°C)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={yieldForm.tempDay}
                          onChange={(e) =>
                            setYieldForm((f) => ({ ...f, tempDay: e.target.value }))
                          }
                          placeholder="예: 23"
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          야간 평균온도 (°C)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={yieldForm.tempNight}
                          onChange={(e) =>
                            setYieldForm((f) => ({ ...f, tempNight: e.target.value }))
                          }
                          placeholder="예: 8"
                          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        CO2 농도 (ppm)
                      </label>
                      <input
                        type="number"
                        value={yieldForm.co2}
                        onChange={(e) =>
                          setYieldForm((f) => ({ ...f, co2: e.target.value }))
                        }
                        placeholder="예: 800"
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-farm-500 focus:outline-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full py-3 bg-farm-600 text-white rounded-lg hover:bg-farm-700 disabled:bg-gray-300 transition-colors font-medium"
                    >
                      {isLoading ? "예측 중..." : "수확량 예측"}
                    </button>
                  </form>
                )}
              </div>

              <div className="bg-white rounded-xl border p-6">
                <h3 className="font-bold text-lg mb-4">예측 결과</h3>
                {yieldResult && yieldResult.status !== "error" ? (
                  <div className="space-y-4">
                    <div className="text-center p-4 bg-farm-50 rounded-xl">
                      <p className="text-sm text-gray-500">예상 수확량</p>
                      <p className="text-3xl font-bold text-farm-700">
                        {yieldResult.total_predicted_yield_kg?.toLocaleString()} kg
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {yieldResult.area_m2}m² 기준 | 재배기간{" "}
                        {yieldResult.growth_days}일
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm font-medium text-gray-700">
                        단위 수확량: {yieldResult.adjusted_yield_per_m2} kg/m²
                        <span className="text-xs text-gray-400 ml-1">
                          (기준: {yieldResult.base_yield_per_m2} kg/m²)
                        </span>
                      </p>
                      <p className="text-sm font-medium text-gray-700">
                        환경 보정계수: {yieldResult.adjustment_factor}
                      </p>
                    </div>

                    {yieldResult.environmental_factors?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">
                          환경 요인 분석
                        </p>
                        <div className="space-y-2">
                          {yieldResult.environmental_factors.map(
                            (f: any, i: number) => (
                              <div
                                key={i}
                                className="flex items-center justify-between p-2 rounded bg-gray-50 text-sm"
                              >
                                <span className="text-gray-600">{f.factor}</span>
                                <span className="text-gray-500">
                                  {f.actual} (최적: {f.optimal})
                                </span>
                                <span
                                  className={`font-medium ${
                                    f.impact.startsWith("+")
                                      ? "text-green-600"
                                      : f.impact.startsWith("-")
                                      ? "text-red-600"
                                      : "text-gray-600"
                                  }`}
                                >
                                  {f.impact}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : yieldResult?.status === "error" ? (
                  <p className="text-center text-red-500 py-8">
                    {yieldResult.message}
                  </p>
                ) : (
                  <p className="text-center text-gray-400 py-8">
                    환경 조건을 입력하고 예측을 실행하세요
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
