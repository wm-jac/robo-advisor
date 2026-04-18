"use client";

import { useEffect, useRef } from "react";
import { Languages, MoonStar, SunMedium } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { t } from "@/lib/i18n";

export default function TopBar() {
  const { lang, theme, setLang, setTheme } = useAppStore();
  const hydrated = useRef(false);

  useEffect(() => {
    const savedLang = window.localStorage.getItem("lang");
    setTheme("dark");
    if (savedLang === "en" || savedLang === "zh") {
      setLang(savedLang);
    }
    hydrated.current = true;
  }, [setLang, setTheme]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.lang = lang;
    if (!hydrated.current) return;
    window.localStorage.setItem("lang", lang);
  }, [lang, theme]);

  return (
    <div className="sticky top-0 z-30 flex justify-end mb-6">
      <div className="control-shell">
        <span className="hidden sm:inline text-[11px] text-muted px-1">
          {t(lang, "top_right_note")}
        </span>

        <div className="flex items-center gap-1 rounded-xl bg-base/50 px-1 py-1">
          <button
            type="button"
            className={`control-button ${theme === "dark" ? "active" : ""}`}
            onClick={() => setTheme("dark")}
          >
            <MoonStar size={14} />
            {t(lang, "top_theme_dark")}
          </button>
          <button
            type="button"
            className={`control-button ${theme === "light" ? "active" : ""}`}
            onClick={() => setTheme("light")}
          >
            <SunMedium size={14} />
            {t(lang, "top_theme_light")}
          </button>
        </div>

        <div className="flex items-center gap-1 rounded-xl bg-base/50 px-1 py-1">
          <span className="px-2 text-muted">
            <Languages size={14} />
          </span>
          <button
            type="button"
            className={`control-button ${lang === "en" ? "active" : ""}`}
            onClick={() => setLang("en")}
          >
            {t(lang, "top_lang_en")}
          </button>
          <button
            type="button"
            className={`control-button ${lang === "zh" ? "active" : ""}`}
            onClick={() => setLang("zh")}
          >
            {t(lang, "top_lang_zh")}
          </button>
        </div>
      </div>
    </div>
  );
}
