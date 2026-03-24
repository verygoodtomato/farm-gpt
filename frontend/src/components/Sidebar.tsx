"use client";

import { ViewType } from "@/app/page";

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
}

const menuItems: { id: ViewType; label: string; icon: string; desc: string }[] = [
  { id: "chat", label: "AI 컨설팅", icon: "💬", desc: "농업 전문 상담" },
  { id: "diagnosis", label: "작물 진단", icon: "🔍", desc: "병해충 진단" },
  { id: "smartfarm", label: "스마트팜", icon: "🌡️", desc: "환경 제어 최적화" },
  { id: "analytics", label: "데이터 분석", icon: "📊", desc: "수확량/가격 예측" },
  { id: "knowledge", label: "지식베이스", icon: "📚", desc: "RAG 문서 관리" },
];

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  return (
    <aside className="w-64 bg-farm-800 text-white flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-farm-700">
        <h1 className="text-2xl font-bold">🌾 FarmGPT</h1>
        <p className="text-farm-300 text-sm mt-1">농업 컨설팅 AI</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
              activeView === item.id
                ? "bg-farm-600 text-white"
                : "text-farm-200 hover:bg-farm-700 hover:text-white"
            }`}
          >
            <span className="text-lg mr-3">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
            <p className="text-xs text-farm-300 ml-8 mt-0.5">{item.desc}</p>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-farm-700">
        <p className="text-xs text-farm-400 text-center">
          스마트농업 AI 경진대회
        </p>
      </div>
    </aside>
  );
}
