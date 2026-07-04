import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { Header } from "@/components/layout/Header";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trợ lý pháp luật Việt Nam",
  description:
    "Tra cứu pháp luật Việt Nam bằng ngôn ngữ tự nhiên, lọc theo lĩnh vực. Công cụ tham khảo, không thay thế tư vấn pháp lý chuyên nghiệp.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={`${geistSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-[family-name:var(--font-geist-sans)]">
        <Header />
        {children}
      </body>
    </html>
  );
}
