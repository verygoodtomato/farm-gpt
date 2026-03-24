import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FarmGPT - 농업 컨설팅 AI",
  description: "AI 기반 스마트 농업 컨설팅 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
