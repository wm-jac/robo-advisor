"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { TrendingUp, AlertCircle } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { computeFrontier } from "@/lib/api";
import { t } from "@/lib/i18n";
import Chart from "@/components/Chart";
import MetricCard from "@/components/MetricCard";
import Link from "next/link";

interface FrontierResult {
  frontier: { return: number; volatility: number }[];
  gmvp: { return: number; volatility: number; weights: number[] };
}

const AXIS = (text: string) => ({ title: { text } });

function getAxisRange(values: number[], paddingRatio = 0.12) {
  if (!values.length) return undefined;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1);
  const pad = span * paddingRatio;
  return [min - pad, max + pad];
}

export default function FrontierPage() {
  const { mu, sigma, stats, funds, lang } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ long: FrontierResult | null; short: FrontierResult | null }>({
    long: null,
    short: null,
  });
  const [computed, setComputed] = useState(false);

  const hasData = mu.length > 0;

  const compute = useCallback(async () => {
    if (!hasData) return;
    setLoading(true);
    setError(null);
    try {
      const [long, short] = await Promise.all([
        computeFrontier(mu, sigma, false),
        computeFrontier(mu, sigma, true),
      ]);
      setResult({ long: long as FrontierResult, short: short as FrontierResult });
      setComputed(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [mu, sigma, hasData]);

  // Auto-compute when data becomes available.
  const autoComputedRef = useRef(false);
  useEffect(() => {
    if (hasData && !computed && !loading && !autoComputedRef.current) {
      autoComputedRef.current = true;
      compute();
    }
  }, [compute, computed, hasData, loading]);

  useEffect(() => {
    if (!hasData) {
      autoComputedRef.current = false;
      setComputed(false);
      setResult({ long: null, short: null });
    }
  }, [hasData]);

  const buildFrontierChart = (res: FrontierResult | null) => {
    if (!res) return [];
    const traces: Plotly.Data[] = [
      {
        x: res.frontier.map((p) => p.volatility * 100),
        y: res.frontier.map((p) => p.return * 100),
        name: t(lang, "frontier_label"),
        type: "scatter",
        mode: "lines",
        line: { color: "#3b82f6", width: 2.5 },
        fill: "tozeroy",
        fillcolor: "rgba(59,130,246,0.05)",
      } as any,
      {
        x: stats.map((s) => s.volatility * 100),
        y: stats.map((s) => s.return * 100),
        text: stats.map((s) => s.fund),
        name: t(lang, "individual_funds"),
        type: "scatter",
        mode: "markers+text",
        textposition: "top right",
        textfont: { size: 9, color: "#94a3b8" },
        marker: { color: "#f59e0b", size: 10, symbol: "circle" },
      } as any,
      {
        x: [res.gmvp.volatility * 100],
        y: [res.gmvp.return * 100],
        text: ["GMVP"],
        name: t(lang, "min_variance"),
        type: "scatter",
        mode: "markers+text",
        textposition: "top right",
        textfont: { color: "#ef4444" },
        marker: { color: "#ef4444", size: 14, symbol: "star" },
      } as any,
    ];
    return traces;
  };

  const getFrontierRanges = (res: FrontierResult | null) => {
    if (!res) return {};
    const xValues = [
      ...res.frontier.map((p) => p.volatility * 100),
      ...stats.map((s) => s.volatility * 100),
      res.gmvp.volatility * 100,
    ];
    const yValues = [
      ...res.frontier.map((p) => p.return * 100),
      ...stats.map((s) => s.return * 100),
      res.gmvp.return * 100,
    ];
    return {
      xaxis: {
        ...AXIS(t(lang, "volatility_pct")),
        range: getAxisRange(xValues),
        automargin: true,
      },
      yaxis: {
        ...AXIS(t(lang, "return_pct")),
        range: getAxisRange(yValues),
        automargin: true,
      },
    };
  };

  return (
    <div>
      <motion.div
        className="page-header"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="page-title">{t(lang, "frontier_title")}</h1>
        <p className="page-subtitle">{t(lang, "frontier_subtitle")}</p>
      </motion.div>

      {!hasData && (
        <motion.div
          className="glass-card p-10 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <AlertCircle className="mx-auto mb-3 text-muted" size={32} />
          <p className="text-secondary font-medium mb-1">{t(lang, "no_fund_data")}</p>
          <p className="text-muted text-sm mb-4">{t(lang, "go_funds_first")}</p>
          <Link href="/funds" className="btn-primary inline-flex items-center gap-2">
            <TrendingUp size={14} /> {t(lang, "load_funds")}
          </Link>
        </motion.div>
      )}

      {hasData && (
        <>
          <motion.div
            className="flex items-center gap-4 mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <button
              onClick={compute}
              disabled={loading}
              className="btn-primary flex items-center gap-2"
            >
              <TrendingUp size={14} className={loading ? "animate-pulse" : ""} />
              {loading ? t(lang, "computing") : t(lang, "recompute")}
            </button>
            {error && (
              <span className="badge-red text-xs">
                <AlertCircle size={12} /> {error}
              </span>
            )}
          </motion.div>

          {loading && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="skeleton h-80" />
                <div className="skeleton h-80" />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-20" />)}
              </div>
            </div>
          )}

          {!loading && computed && result.long && result.short && (
            <div className="space-y-8">
              {/* GMVP metrics */}
              <div>
                <p className="section-title">{t(lang, "gmvp_title")}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    label={t(lang, "gmvp_return_long")}
                    value={`${(result.long.gmvp.return * 100).toFixed(2)}%`}
                    accent="emerald"
                    delay={0}
                  />
                  <MetricCard
                    label={t(lang, "gmvp_vol_long")}
                    value={`${(result.long.gmvp.volatility * 100).toFixed(2)}%`}
                    accent="blue"
                    delay={0.05}
                  />
                  <MetricCard
                    label={t(lang, "gmvp_return_short")}
                    value={`${(result.short.gmvp.return * 100).toFixed(2)}%`}
                    accent="cyan"
                    delay={0.1}
                  />
                  <MetricCard
                    label={t(lang, "gmvp_vol_short")}
                    value={`${(result.short.gmvp.volatility * 100).toFixed(2)}%`}
                    accent="purple"
                    delay={0.15}
                  />
                </div>
              </div>

              {/* Frontier charts */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <p className="section-title mb-0">{t(lang, "long_only")}</p>
                    <span className="badge-emerald text-xs">{t(lang, "no_short_selling")}</span>
                  </div>
                  <Chart
                    data={buildFrontierChart(result.long)}
                    layout={{
                      ...getFrontierRanges(result.long),
                      legend: { orientation: "h", yanchor: "bottom", y: 1.02 } as any,
                    }}
                    config={{ displaylogo: false }}
                    height={380}
                  />
                </motion.div>

                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <p className="section-title mb-0">{t(lang, "with_short_selling")}</p>
                    <span className="badge-blue text-xs">{t(lang, "full_parabola")}</span>
                  </div>
                  <Chart
                    data={buildFrontierChart(result.short)}
                    layout={{
                      ...getFrontierRanges(result.short),
                      legend: { orientation: "h", yanchor: "bottom", y: 1.02 } as any,
                    }}
                    config={{ displaylogo: false }}
                    height={380}
                  />
                </motion.div>
              </div>

              {/* GMVP weights tables */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {[
                  { label: t(lang, "long_gmvp_weights"), res: result.long },
                  { label: t(lang, "short_gmvp_weights"), res: result.short },
                ].map(({ label, res }) => (
                  <motion.div
                    key={label}
                    className="glass-card p-6"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <p className="section-title">{label}</p>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>{t(lang, "fund")}</th>
                          <th>{t(lang, "weight")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {funds
                          .map((name, i) => ({
                            name,
                            w: res.gmvp.weights[i] ?? 0,
                          }))
                          .filter((r) => Math.abs(r.w) > 0.001)
                          .sort((a, b) => b.w - a.w)
                          .map((r) => (
                            <tr key={r.name}>
                              <td>{r.name}</td>
                              <td className={r.w >= 0 ? "text-emerald" : "text-red"}>
                                {(r.w * 100).toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
