import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "TaxEase | AI-powered ITR Guidance System",
  description: "AI-driven tax insights in a sleek workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex h-screen overflow-hidden bg-background font-sans text-foreground">
        <Sidebar className="w-64 flex-shrink-0" />
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-auto p-6 bg-background">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
