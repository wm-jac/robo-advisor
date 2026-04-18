"use client";

import { motion } from "framer-motion";
import { clsx } from "clsx";

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: "blue" | "cyan" | "emerald" | "amber" | "red" | "purple";
  delay?: number;
  className?: string;
}

const ACCENT_STYLES: Record<string, { top: string; glow: string }> = {
  blue: {
    top: "linear-gradient(90deg, #3b82f6, #06b6d4)",
    glow: "rgba(59,130,246,0.12)",
  },
  cyan: {
    top: "linear-gradient(90deg, #06b6d4, #10b981)",
    glow: "rgba(6,182,212,0.12)",
  },
  emerald: {
    top: "linear-gradient(90deg, #10b981, #06b6d4)",
    glow: "rgba(16,185,129,0.12)",
  },
  amber: {
    top: "linear-gradient(90deg, #f59e0b, #f97316)",
    glow: "rgba(245,158,11,0.12)",
  },
  red: {
    top: "linear-gradient(90deg, #ef4444, #ec4899)",
    glow: "rgba(239,68,68,0.12)",
  },
  purple: {
    top: "linear-gradient(90deg, #8b5cf6, #3b82f6)",
    glow: "rgba(139,92,246,0.12)",
  },
};

export default function MetricCard({
  label,
  value,
  sub,
  accent = "blue",
  delay = 0,
  className,
}: MetricCardProps) {
  const style = ACCENT_STYLES[accent];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      className={clsx("metric-card", className)}
      whileHover={{ y: -2, boxShadow: `0 12px 40px ${style.glow}` }}
    >
      {/* Top gradient line */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: style.top }}
      />

      <p className="text-muted text-[10px] uppercase tracking-widest mb-2 font-medium">
        {label}
      </p>
      <p
        className="text-primary font-medium text-2xl leading-none"
        style={{ fontFamily: "IBM Plex Mono, monospace" }}
      >
        {value}
      </p>
      {sub && <p className="text-muted text-xs mt-1.5">{sub}</p>}
    </motion.div>
  );
}
