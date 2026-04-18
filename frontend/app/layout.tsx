import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";

export const metadata: Metadata = {
  title: "Robo-Advisor | BMD5302",
  description: "Portfolio optimisation and risk assessment dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className="flex h-screen overflow-hidden bg-base">
        <Script id="theme-init" strategy="beforeInteractive">
          {`
            (function () {
              try {
                var savedLang = localStorage.getItem("lang");
                var lang = savedLang === "zh" || savedLang === "en" ? savedLang : "en";
                document.documentElement.dataset.theme = "dark";
                document.documentElement.lang = lang;
              } catch (e) {
                document.documentElement.dataset.theme = "dark";
                document.documentElement.lang = "en";
              }
            })();
          `}
        </Script>
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-base bg-dot-grid bg-[size:32px_32px]">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <TopBar />
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
