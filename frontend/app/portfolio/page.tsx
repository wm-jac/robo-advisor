"use client";

import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { Briefcase, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useAppStore, type RiskFreeRateInfo } from "@/lib/store";
import { computeFrontier, computeOptimal } from "@/lib/api";
import { t, translateProfile } from "@/lib/i18n";
import { formatRiskFreeRateShort } from "@/lib/riskFree";
import Chart, { COLOURS } from "@/components/Chart";
import MetricCard from "@/components/MetricCard";

interface AllocationRow {
  fund: string;
  weight: number;
  weight_pct: number;
}

interface OptimalResult {
  return: number;
  volatility: number;
  utility: number;
  sharpe: number;
  success: boolean;
  allocation: AllocationRow[];
  sensitivity: Record<string, number>[];
  risk_free_rate?: RiskFreeRateInfo;
}

interface FrontierResult {
  frontier: { return: number; volatility: number }[];
}

export default function PortfolioPage() {
  const {
    mu,
    sigma,
    funds,
    riskA,
    riskProfile,
    stats,
    riskFreeRate,
    lang,
    setPortfolioReady,
  } = useAppStore();

  const [A, setA] = useState<number>(riskA ?? 4.0);
  const [allowShort, setAllowShort] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OptimalResult | null>(null);
  const [frontierResult, setFrontierResult] = useState<FrontierResult | null>(null);

  const hasData = mu.length > 0;
  const hasProfile = riskA !== null;
  const appliedRiskFreeRate = result?.risk_free_rate ?? riskFreeRate;
  const riskFreeText = formatRiskFreeRateShort(lang, appliedRiskFreeRate);

  // Sync slider with profile A when it changes
  useEffect(() => {
    if (riskA !== null) setA(riskA);
  }, [riskA]);

  const compute = useCallback(async () => {
    if (!hasData) return;
    setLoading(true);
    setError(null);
    try {
      const [optimalRes, frontierRes] = await Promise.all([
        computeOptimal(mu, sigma, A, allowShort, funds),
        computeFrontier(mu, sigma, allowShort),
      ]);
      setResult(optimalRes as OptimalResult);
      setFrontierResult(frontierRes as FrontierResult);
      setPortfolioReady(true);
    } catch (e: any) {
      setError(e.message);
      setPortfolioReady(false);
    } finally {
      setLoading(false);
    }
  }, [mu, sigma, A, allowShort, funds, hasData, setPortfolioReady]);

  // Auto-compute when profile & data available
  useEffect(() => {
    if (hasData && hasProfile && !result) {
      compute();
    }
  }, [hasData, hasProfile]); // eslint-disable-line react-hooks/exhaustive-deps

  // Build bar chart for allocation
  const buildAllocChart = (alloc: AllocationRow[]) => {
    const sorted = [...alloc].sort((a, b) => b.weight_pct - a.weight_pct);
    const longs = sorted.filter((r) => r.weight_pct >= 0);
    const shorts = sorted.filter((r) => r.weight_pct < 0);
    const maxAbs = Math.max(...sorted.map((r) => Math.abs(r.weight_pct)), 1);

    const traces: Plotly.Data[] = [];
    if (longs.length) {
      traces.push({
        name: t(lang, "long"),
        x: longs.map((r) => r.weight_pct),
        y: longs.map((r) => r.fund),
        type: "bar",
        orientation: "h",
        marker: { color: "#f97316" },
        text: longs.map((r) => `${r.weight_pct.toFixed(2)}%`),
        textposition: "outside",
        textfont: { color: "#94a3b8", size: 11 },
      } as any);
    }
    if (shorts.length) {
      traces.push({
        name: t(lang, "short"),
        x: shorts.map((r) => r.weight_pct),
        y: shorts.map((r) => r.fund),
        type: "bar",
        orientation: "h",
        marker: { color: "#3b82f6" },
        text: shorts.map((r) => `${r.weight_pct.toFixed(2)}%`),
        textposition: "outside",
        textfont: { color: "#94a3b8", size: 11 },
      } as any);
    }
    return { traces, maxAbs };
  };

  // Sensitivity chart — stacked area
  const buildSensChart = (sens: Record<string, number>[]) => {
    if (!sens.length) return [];
    const aValues = sens.map((r) => r.A);
    const fundKeys = Object.keys(sens[0]).filter((k) => k !== "A");

    return fundKeys.map((name, i) => ({
      x: aValues,
      y: sens.map((r) => r[name] ?? 0),
      name,
      type: "scatter" as const,
      mode: "lines" as const,
      stackgroup: "one",
      line: { color: COLOURS[i % COLOURS.length], width: 1.5 },
    }));
  };

  // Frontier overlay
  const buildFrontierOverlay = (res: OptimalResult) => {
    const traces: Plotly.Data[] = [
      ...(frontierResult
        ? [
            {
              x: frontierResult.frontier.map((p) => p.volatility * 100),
              y: frontierResult.frontier.map((p) => p.return * 100),
              name: t(lang, "frontier_label"),
              type: "scatter",
              mode: "lines",
              line: { color: "#3b82f6", width: 2.5 },
            } as Plotly.Data,
          ]
        : []),
      {
        x: stats.map((s) => s.volatility * 100),
        y: stats.map((s) => s.return * 100),
        text: stats.map((s) => s.fund),
        name: t(lang, "individual_funds"),
        type: "scatter",
        mode: "markers+text",
        textposition: "top right",
        textfont: { size: 9, color: "#94a3b8" },
        marker: { color: "#f59e0b", size: 8 },
      } as any,
      {
        x: [res.volatility * 100],
        y: [res.return * 100],
        text: [`Optimal (A=${A.toFixed(1)})`],
        name: t(lang, "portfolio_title"),
        type: "scatter",
        mode: "markers+text",
        textposition: "top right",
        textfont: { color: "#10b981", size: 11 },
        marker: { color: "#10b981", size: 16, symbol: "diamond" },
      } as any,
    ];
    return traces;
  };

  return (
    <div>
      <motion.div
        className="page-header"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="page-title">{t(lang, "portfolio_title")}</h1>
        <p className="page-subtitle">{t(lang, "portfolio_subtitle")}</p>
      </motion.div>

      {/* Guard: need data */}
      {!hasData && (
        <div className="glass-card p-10 text-center">
          <AlertCircle className="mx-auto mb-3 text-muted" size={32} />
          <p className="text-secondary font-medium mb-1">{t(lang, "no_fund_data")}</p>
          <Link href="/funds" className="btn-primary inline-flex items-center gap-2 mt-3">
            {t(lang, "load_funds")}
          </Link>
        </div>
      )}

      {/* Guard: need profile */}
      {hasData && !hasProfile && (
        <div className="glass-card p-10 text-center">
          <AlertCircle className="mx-auto mb-3 text-muted" size={32} />
          <p className="text-secondary font-medium mb-1">{t(lang, "no_risk_profile")}</p>
          <p className="text-muted text-sm mb-4">{t(lang, "complete_questionnaire_first")}</p>
          <Link href="/profile" className="btn-primary inline-flex items-center gap-2">
            {t(lang, "take_questionnaire")}
          </Link>
        </div>
      )}

      {hasData && hasProfile && (
        <>
          {/* Controls */}
          <motion.div
            className="glass-card p-6 mb-8"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex flex-wrap items-center gap-6">
              {/* Profile badge */}
              {riskProfile && (
                <div
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-medium border"
                  style={{
                    color: riskProfile.color,
                    background: `${riskProfile.color}12`,
                    borderColor: `${riskProfile.color}30`,
                  }}
                >
                  {(() => {
                    const localProfile = translateProfile(riskProfile, lang);
                    return `${localProfile.emoji} ${localProfile.label} · A = ${riskA?.toFixed(1)}`;
                  })()}
                </div>
              )}

              {/* Short toggle */}
              <label className="flex items-center gap-2 cursor-pointer">
                <div
                  className={`w-10 h-5.5 rounded-full relative transition-all duration-200 ${
                    allowShort ? "bg-blue" : "bg-elevated border border-border"
                  }`}
                  style={{ height: "22px" }}
                  onClick={() => setAllowShort(!allowShort)}
                >
                  <div
                    className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200 ${
                      allowShort ? "left-5" : "left-0.5"
                    }`}
                  />
                </div>
                <span className="text-secondary text-sm">{t(lang, "allow_short_selling")}</span>
              </label>

              <button
                onClick={compute}
                disabled={loading}
                className="btn-primary flex items-center gap-2"
              >
                <Briefcase size={14} className={loading ? "animate-pulse" : ""} />
                {loading ? t(lang, "optimising") : t(lang, "optimise")}
              </button>
            </div>

            {error && (
              <p className="text-red text-sm mt-3 flex items-center gap-2">
                <AlertCircle size={14} /> {error}
              </p>
            )}
          </motion.div>

          {loading && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24" />)}
              </div>
              <div className="skeleton h-80" />
            </div>
          )}

          {!loading && result && (
            <div className="space-y-8">
              {/* Metrics */}
              <div>
                <p className="section-title">{t(lang, "portfolio_metrics")}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    label={t(lang, "expected_return")}
                    value={`${(result.return * 100).toFixed(2)}%`}
                    accent="emerald"
                    delay={0}
                  />
                  <MetricCard
                    label={t(lang, "volatility")}
                    value={`${(result.volatility * 100).toFixed(2)}%`}
                    accent="blue"
                    delay={0.05}
                  />
                  <MetricCard
                    label={t(lang, "utility")}
                    value={result.utility.toFixed(4)}
                    sub={`U = r − (A/2)σ²`}
                    accent="cyan"
                    delay={0.1}
                  />
                  <MetricCard
                    label={t(lang, "sharpe_ratio")}
                    value={result.sharpe.toFixed(3)}
                    sub={riskFreeText}
                    accent={result.sharpe >= 1 ? "emerald" : result.sharpe >= 0.5 ? "amber" : "red"}
                    delay={0.15}
                  />
                </div>
              </div>

              {/* Allocation chart + table */}
              <div className="space-y-6">
                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <p className="section-title">{t(lang, "portfolio_allocation")}</p>
                  {(() => {
                    const { traces, maxAbs } = buildAllocChart(result.allocation);
                    return (
                      <Chart
                        data={traces}
                        layout={{
                          barmode: "relative",
                          xaxis: {
                            title: { text: `${t(lang, "weight")} (%)` },
                            ticksuffix: "%",
                            range: [-maxAbs * 1.25, maxAbs * 1.25],
                          } as any,
                          yaxis: { autorange: "reversed", automargin: true } as any,
                          legend: { orientation: "h", y: 1.05 } as any,
                          margin: { t: 10, b: 40, l: 10, r: 60 },
                        }}
                        height={Math.max(300, 38 * result.allocation.length + 80)}
                      />
                    );
                  })()}
                </motion.div>

                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                >
                  <p className="section-title">{t(lang, "allocation_table")}</p>
                  <table className="data-table mb-6">
                    <thead>
                      <tr>
                        <th>{t(lang, "fund")}</th>
                        <th>{t(lang, "weight")}</th>
                        <th>{lang === "zh" ? "方向" : "Position"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.allocation.map((r) => (
                        <tr key={r.fund}>
                          <td>{r.fund}</td>
                          <td className={r.weight_pct >= 0 ? "text-emerald" : "text-red"}>
                            {r.weight_pct.toFixed(2)}%
                          </td>
                          <td>
                            <span className={r.weight_pct >= 0 ? "badge-emerald" : "badge-red"}>
                              {r.weight_pct >= 0 ? t(lang, "long") : t(lang, "short")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <div className="border-t border-border pt-4">
                    <p className="text-muted text-xs mb-2 font-medium uppercase tracking-widest">
                      {t(lang, "utility_decomp")}
                    </p>
                    <p className="font-mono text-sm text-secondary">
                      U = {(result.return * 100).toFixed(4)}% − ({A.toFixed(1)}/2) × {(result.volatility ** 2 * 100).toFixed(4)}%
                    </p>
                    <p className="font-mono text-sm text-primary mt-1">
                      = <span className="text-blue">{result.utility.toFixed(6)}</span>
                    </p>
                  </div>
                </motion.div>
              </div>

              {/* Position on risk-return space */}
              {stats.length > 0 && (
                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <p className="section-title">{t(lang, "position_vs_funds")}</p>
                  <Chart
                    data={buildFrontierOverlay(result)}
                    layout={{
                      xaxis: { title: { text: t(lang, "volatility_pct") } },
                      yaxis: { title: { text: t(lang, "return_pct") } },
                      legend: { orientation: "h", y: 1.05 } as any,
                    }}
                    height={360}
                  />
                </motion.div>
              )}

              {/* Sensitivity analysis */}
              {result.sensitivity.length > 0 && (
                <motion.div
                  className="glass-card p-6"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35 }}
                >
                  <p className="section-title">{t(lang, "sensitivity_analysis")}</p>
                  <Chart
                    data={buildSensChart(result.sensitivity)}
                    layout={{
                      xaxis: { title: t(lang, "risk_aversion") } as any,
                      yaxis: { title: `${t(lang, "weight")} (%)`, range: [0, 100] } as any,
                      legend: { orientation: "h", y: 1.05 } as any,
                    }}
                    height={360}
                  />
                  <p className="text-muted text-xs mt-3">
                    {t(lang, "how_portfolio_changes", { A: A.toFixed(1) })}
                  </p>
                </motion.div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
