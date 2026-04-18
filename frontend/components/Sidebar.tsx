"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, TrendingUp, Brain, Briefcase } from "lucide-react";
import { clsx } from "clsx";
import { useAppStore } from "@/lib/store";
import { t } from "@/lib/i18n";

const NAV = [
  { href: "/funds", icon: BarChart2, labelKey: "nav_funds_label", subKey: "nav_funds_sub" },
  { href: "/frontier", icon: TrendingUp, labelKey: "nav_frontier_label", subKey: "nav_frontier_sub" },
  { href: "/profile", icon: Brain, labelKey: "nav_profile_label", subKey: "nav_profile_sub" },
  { href: "/portfolio", icon: Briefcase, labelKey: "nav_portfolio_label", subKey: "nav_portfolio_sub" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { lang } = useAppStore();

  return (
    <aside
      className="w-[240px] shrink-0 flex flex-col h-screen border-r border-border overflow-y-auto bg-sidebar"
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-5 border-b border-border">
        <div className="flex items-center gap-3 mb-0.5">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0"
            style={{
              background: "linear-gradient(135deg, #3b82f6, #06b6d4)",
              boxShadow: "0 0 20px rgba(59,130,246,0.4)",
            }}
          >
            📈
          </div>
          <div>
            <div
              className="text-primary font-bold leading-tight"
              style={{ fontFamily: 'var(--font-heading)', letterSpacing: "-0.02em" }}
            >
              {t(lang, "title")}
            </div>
            <div className="text-muted text-[10px] uppercase tracking-widest mt-0.5">
              {t(lang, "group")}
            </div>
            <div className="text-muted text-[10px] uppercase tracking-widest mt-0.5">
              {t(lang, "semester")}
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-muted text-[10px] uppercase tracking-widest px-3 mb-3">
          {t(lang, "nav_label")}
        </p>
        {NAV.map(({ href, icon: Icon, labelKey, subKey }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={clsx("nav-item group", active && "active")}
            >
              <div
                className={clsx(
                  "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all duration-200",
                  active
                    ? "bg-blue/20 text-blue"
                    : "bg-elevated text-muted group-hover:text-secondary"
                )}
              >
                <Icon size={15} />
              </div>
              <div className="min-w-0">
                <div
                  className={clsx(
                    "text-sm font-medium leading-tight",
                    active ? "text-blue" : "text-secondary group-hover:text-primary"
                  )}
                >
                  {t(lang, labelKey as never)}
                </div>
                <div className="text-muted text-[11px] mt-0.5 truncate">{t(lang, subKey as never)}</div>
              </div>
              {active && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue shrink-0" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border">
        <p className="text-muted text-[10px] leading-relaxed">
          {t(lang, "subtitle")}
        </p>
      </div>
    </aside>
  );
}
