const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// Chat
export async function sendChatMessage(
  messages: ChatMessage[],
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  onSources?: (sources: string[]) => void,
  useRag: boolean = true
) {
  try {
    const response = await fetch(`${API_URL}/api/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, stream: true, use_rag: useRag }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const reader = response.body?.getReader();
    if (!reader) throw new Error("No reader");
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") { onDone(); return; }
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) { onError(parsed.error); return; }
          if (parsed.sources && onSources) onSources(parsed.sources);
          if (parsed.content) onChunk(parsed.content);
        } catch {}
      }
    }
    onDone();
  } catch (error) {
    onError(error instanceof Error ? error.message : "알 수 없는 오류");
  }
}

// Smart Farm
export async function analyzeSmartFarm(data: Record<string, number>) {
  const res = await fetch(`${API_URL}/api/smartfarm/analyze`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  return res.json();
}

export async function runSimulation(crop: string, hours: number = 24, month: number = 1) {
  const params = new URLSearchParams({ crop, hours: String(hours), month: String(month) });
  const res = await fetch(`${API_URL}/api/smartfarm/simulate?${params}`, { method: "POST" });
  return res.json();
}

export async function compareStrategies(crop: string, month: number = 1) {
  const params = new URLSearchParams({ crop, month: String(month) });
  const res = await fetch(`${API_URL}/api/smartfarm/compare?${params}`, { method: "POST" });
  return res.json();
}

// Diagnosis
export async function diagnoseFromText(cropType: string, symptoms: string) {
  const formData = new FormData();
  formData.append("crop_type", cropType);
  formData.append("symptoms", symptoms);
  const res = await fetch(`${API_URL}/api/diagnosis/text`, { method: "POST", body: formData });
  return res.json();
}

export async function diagnoseFromImage(file: File, cropType?: string, additionalInfo?: string) {
  const formData = new FormData();
  formData.append("file", file);
  if (cropType) formData.append("crop_type", cropType);
  if (additionalInfo) formData.append("additional_info", additionalInfo);
  const res = await fetch(`${API_URL}/api/diagnosis/image`, { method: "POST", body: formData });
  return res.json();
}

// Analytics
export async function getMarketInfo(cropType: string) {
  const res = await fetch(`${API_URL}/api/analytics/market-info/${encodeURIComponent(cropType)}`);
  return res.json();
}

export async function predictPrice(cropType: string, monthsAhead: number = 3) {
  const params = new URLSearchParams({ crop_type: cropType, months_ahead: String(monthsAhead) });
  const res = await fetch(`${API_URL}/api/analytics/predict-price?${params}`, { method: "POST" });
  return res.json();
}

export async function predictYield(params: {
  crop_type: string; area_m2?: number; avg_temp_day?: number; avg_temp_night?: number; co2_level?: number;
}) {
  const sp = new URLSearchParams();
  sp.set("crop_type", params.crop_type);
  if (params.area_m2) sp.set("area_m2", String(params.area_m2));
  if (params.avg_temp_day) sp.set("avg_temp_day", String(params.avg_temp_day));
  if (params.avg_temp_night) sp.set("avg_temp_night", String(params.avg_temp_night));
  if (params.co2_level) sp.set("co2_level", String(params.co2_level));
  const res = await fetch(`${API_URL}/api/analytics/predict-yield?${sp}`, { method: "POST" });
  return res.json();
}

export async function getPriceHistory(cropType: string) {
  const res = await fetch(`${API_URL}/api/analytics/price-history/${encodeURIComponent(cropType)}`);
  return res.json();
}

// Knowledge
export async function indexKnowledgeBase() {
  const res = await fetch(`${API_URL}/api/knowledge/index`, { method: "POST" });
  return res.json();
}

export async function searchKnowledge(query: string, nResults: number = 5) {
  const params = new URLSearchParams({ query, n_results: String(nResults) });
  const res = await fetch(`${API_URL}/api/knowledge/search?${params}`);
  return res.json();
}

export async function getKnowledgeStats() {
  const res = await fetch(`${API_URL}/api/knowledge/stats`);
  return res.json();
}

export async function getKnowledgeFiles() {
  const res = await fetch(`${API_URL}/api/knowledge/files`);
  return res.json();
}
