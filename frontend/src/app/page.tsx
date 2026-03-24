"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import SmartFarmView from "@/components/SmartFarmView";
import DiagnosisView from "@/components/DiagnosisView";
import AnalyticsView from "@/components/AnalyticsView";
import KnowledgeView from "@/components/KnowledgeView";

export type ViewType = "chat" | "smartfarm" | "diagnosis" | "analytics" | "knowledge";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("chat");

  return (
    <div className="flex h-screen">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      <main className="flex-1 overflow-hidden">
        {activeView === "chat" && <ChatView />}
        {activeView === "smartfarm" && <SmartFarmView />}
        {activeView === "diagnosis" && <DiagnosisView />}
        {activeView === "analytics" && <AnalyticsView />}
        {activeView === "knowledge" && <KnowledgeView />}
      </main>
    </div>
  );
}
