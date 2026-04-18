"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { analyzeFunds, analyzeDefaults } from "@/lib/api";
import { t } from "@/lib/i18n";
import { formatRiskFreeRate } from "@/lib/riskFree";
import Chart, { COLOURS } from "@/components/Chart";
import MetricCard from "@/components/MetricCard";

const FREQ_OPTIONS = ["Daily", "Weekly", "Monthly"];

export default function FundsPage() {
  const {
    funds,
    prices,
    stats,
    corr,
    dateRange,
    riskFreeRate,
    isDefault,
    freq,
    lang,
    setAnalysisData,
    setFreq,
  } = useAppStore();

  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasData = funds.length > 0;
  const riskFreeText = formatRiskFreeRate(lang, riskFreeRate);

  const load = useCallback(
    async (files: File[], selectedFreq: string) => {
      setLoading(true);
      setError(null);
      try {
        const data =
          files.length > 0
            ? await analyzeFunds(files, selectedFreq)
            : await analyzeDefaults(selectedFreq);
        setAnalysisData(data as any);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [setAnalysisData]
  );

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const csvs = Array.from(files).filter((f) => f.name.endsWith(".csv"));
    setUploadedFiles(csvs);
    load(csvs, freq);
  };

  const handleFreqChange = (f: string) => {
    setFreq(f);
    load(uploadedFiles, f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  // Auto-load defaults on first visit without triggering side effects during render.
  const initialized = useRef(false);
  useEffect(() => {
    if (!initialized.current && !hasData) {
      initialized.current = true;
      load([], freq);
    }
  }, [hasData, freq, load]);

  // Chart data
  const priceTraces = Object.entries(prices).map(([name, series], i) => ({
    x: series.dates,
    y: series.values,
    name,
    type: "scatter" as const,
    mode: "lines" as const,
    line: { color: COLOURS[i % COLOURS.length], width: 1.8 },
  }));

  const corrTraces: Plotly.Data[] =
    corr
      ? [
          {
            z: corr.values,
            x: corr.funds,
            y: corr.funds,
            type: "heatmap",
            colorscale: [
              [0.0, "#1d4ed8"],
              [0.2, "#3b82f6"],
              [0.4, "#93c5fd"],
              [0.5, "#ffffff"],
              [0.7, "#fca5a5"],
              [0.85, "#b91c1c"],
              [1.0, "#7f1d1d"],
            ],
            zmin: -1,
            zmax: 1,
            text: corr.values.map((row) => row.map((v) => v?.toFixed(2) ?? "")) as any,
            texttemplate: "%{text}",
            textfont: { size: 10, color: "#e2e8f0" },
          } as Plotly.Data,
        ]
      : [];

  return (
    <div>
      {/* Header */}
      <motion.div
        className="page-header"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="page-title">{t(lang, "page_funds_title")}</h1>
        <p className="page-subtitle">{t(lang, "page_funds_subtitle")}</p>
      </motion.div>

      {/* Controls row */}
      <motion.div
        className="flex flex-wrap items-center gap-4 mb-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        {/* File upload drop zone */}
        <div
          className={`flex-1 min-w-[260px] border-2 border-dashed rounded-2xl p-4 flex items-center gap-3 cursor-pointer transition-all duration-200 ${
            dragging
              ? "border-blue bg-blue/5"
              : "border-border hover:border-border-bright"
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <Upload size={18} className="text-muted shrink-0" />
          <div className="min-w-0">
            <p className="text-secondary text-sm font-medium truncate">
              {uploadedFiles.length > 0
                ? t(
                    lang,
                    uploadedFiles.length > 1 ? "upload_selected_plural" : "upload_selected",
                    { count: uploadedFiles.length }
                  )
                : t(lang, "upload_drop")}
            </p>
            <p className="text-muted text-xs mt-0.5">
              {uploadedFiles.length > 0
                ? uploadedFiles.map((f) => f.name).join(", ")
                : t(lang, "upload_accepts")}
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        {/* Frequency selector */}
        <div className="flex gap-1.5 p-1 rounded-xl border border-border bg-card">
          {FREQ_OPTIONS.map((f) => (
            <button
              key={f}
              onClick={() => handleFreqChange(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                freq === f
                  ? "bg-blue text-white shadow-lg"
                  : "text-muted hover:text-secondary"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Reload button */}
        <button
          onClick={() => load(uploadedFiles, freq)}
          disabled={loading}
          className="btn-ghost flex items-center gap-2"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          {t(lang, "reload")}
        </button>
      </motion.div>

      {/* Status badge */}
      <AnimatePresence>
        {hasData && dateRange && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="badge-emerald mb-6 text-xs"
          >
            <CheckCircle size={12} />
            {funds.length} funds loaded · {dateRange.start} → {dateRange.end} ·{" "}
            {dateRange.observations} {t(lang, "observations")} ·{" "}
            {isDefault ? t(lang, "default_data") : t(lang, "uploaded_files")}
          </motion.div>
        )}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="badge-red mb-6"
          >
            <AlertCircle size={12} />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-24" />
            ))}
          </div>
          <div className="skeleton h-80" />
          <div className="skeleton h-64" />
        </div>
      )}

      {/* Content */}
      {!loading && hasData && (
        <div className="space-y-8">
          {/* Stats metric cards */}
          <div>
            <p className="section-title">{t(lang, "performance_summary")}</p>
            {riskFreeText && (
              <p className="text-muted text-xs mb-3">{riskFreeText}</p>
            )}
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
              {stats.map((s, i) => (
                <MetricCard
                  key={s.fund}
                  label={s.fund}
                  value={`${(s.return * 100).toFixed(2)}%`}
                  sub={`${t(lang, "metric_vol")}: ${(s.volatility * 100).toFixed(2)}% · ${t(lang, "metric_sr")}: ${s.sharpe.toFixed(2)}`}
                  accent={
                    (["blue", "cyan", "emerald", "amber", "purple", "red", "cyan", "amber"] as const)[i % 8]
                  }
                  delay={i * 0.05}
                />
              ))}
            </div>
          </div>

          {/* Price chart */}
          <motion.div
            className="glass-card p-6"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <p className="section-title">{t(lang, "normalised_price")}</p>
            <Chart
              data={priceTraces}
              layout={{
                xaxis: { title: { text: "Date" } },
                yaxis: { title: { text: "Value (base 100)" } },
                legend: {
                  orientation: "h",
                  yanchor: "bottom",
                  y: 1.02,
                  xanchor: "right",
                  x: 1,
                } as any,
              }}
              height={380}
            />
          </motion.div>

          {/* Stats table */}
          <motion.div
            className="glass-card p-6"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <p className="section-title">{t(lang, "performance_summary")}</p>
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t(lang, "fund")}</th>
                  <th>{lang === "zh" ? "年化收益率" : "Ann. Return"}</th>
                  <th>{lang === "zh" ? "年化波动率" : "Ann. Volatility"}</th>
                  <th>{lang === "zh" ? "夏普比率" : "Sharpe Ratio"}</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((s) => (
                  <tr key={s.fund}>
                    <td>{s.fund}</td>
                    <td
                      className={
                        s.return >= 0 ? "text-emerald" : "text-red"
                      }
                    >
                      {(s.return * 100).toFixed(2)}%
                    </td>
                    <td>{(s.volatility * 100).toFixed(2)}%</td>
                    <td
                      className={
                        s.sharpe >= 1
                          ? "text-emerald"
                          : s.sharpe >= 0.5
                          ? "text-amber"
                          : "text-red"
                      }
                    >
                      {s.sharpe.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>

          {/* Correlation heatmap */}
          {corr && (
            <motion.div
              className="glass-card p-6"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <p className="section-title">{t(lang, "correlation_matrix")}</p>
              <Chart
                data={corrTraces}
                layout={{
                  margin: { t: 10, b: 150, l: 175, r: 20 },
                  xaxis: {
                    automargin: true,
                    tickangle: 30,
                  } as any,
                  yaxis: {
                    automargin: true,
                    tickfont: { size: 11 },
                  } as any,
                }}
                height={Math.max(340, corr.funds.length * 42 + 80)}
              />
            </motion.div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && !hasData && !error && (
        <motion.div
          className="flex flex-col items-center justify-center py-24 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl mb-4"
            style={{
              background: "linear-gradient(135deg, #3b82f6, #06b6d4)",
              boxShadow: "0 0 40px rgba(59,130,246,0.4)",
            }}
          >
            📈
          </div>
          <h2 className="text-primary font-bold text-xl mb-2" style={{ fontFamily: "var(--font-heading)" }}>
            {lang === "zh" ? "暂无数据" : "No data yet"}
          </h2>
          <p className="text-muted text-sm max-w-sm">
            {lang === "zh"
              ? "请上传基金 CSV 文件，或点击重新加载以载入默认基金数据。"
              : "Upload CSV fund files above, or click Reload to load the bundled default funds."}
          </p>
        </motion.div>
      )}
    </div>
  );
}
