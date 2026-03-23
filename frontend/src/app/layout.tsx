import type { Metadata } from "next";
import { Noto_Sans_SC } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { AuthGuard } from "@/components/layout/auth-guard";
import "./globals.css";

const notoSans = Noto_Sans_SC({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "齐家 · 家庭投资助手",
  description: "给三口之家用的投资记账本 + AI 分析助手",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={`${notoSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        <AuthGuard>{children}</AuthGuard>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
