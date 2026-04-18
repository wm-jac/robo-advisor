import { create } from "zustand";
import type { Lang, ThemeMode } from "@/lib/i18n";

export interface FundStat {
  fund: string;
  return: number;
  volatility: number;
  sharpe: number;
}

export interface PriceSeries {
  dates: string[];
  values: number[];
}

export interface CorrData {
  funds: string[];
  values: number[][];
}

export interface DateRange {
  start: string;
  end: string;
  observations: number;
}

export interface AllocationRow {
  fund: string;
  weight: number;
  weight_pct: number;
}

export interface RiskProfile {
  label: string;
  description: string;
  color: string;
  emoji: string;
}

interface AppState {
  lang: Lang;
  theme: ThemeMode;

  // Analysis data (from /api/analyze)
  funds: string[];
  mu: number[];
  sigma: number[][];
  prices: Record<string, PriceSeries>;
  stats: FundStat[];
  corr: CorrData | null;
  dateRange: DateRange | null;
  isDefault: boolean;
  freq: string;

  // Risk profile (from /api/profile)
  riskA: number | null;
  riskProfile: RiskProfile | null;
  portfolioReady: boolean;
  questionnaireAnswers: (number | null)[];

  // Actions
  setAnalysisData: (data: {
    funds: string[];
    mu: number[];
    sigma: number[][];
    prices: Record<string, PriceSeries>;
    stats: FundStat[];
    corr: CorrData;
    date_range: DateRange;
    is_default: boolean;
  }) => void;
  setLang: (lang: Lang) => void;
  setTheme: (theme: ThemeMode) => void;
  setFreq: (freq: string) => void;
  setRiskProfile: (A: number, profile: RiskProfile) => void;
  setPortfolioReady: (ready: boolean) => void;
  setQuestionnaireAnswers: (answers: (number | null)[]) => void;
  clearRiskProfile: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  lang: "en",
  theme: "dark",
  funds: [],
  mu: [],
  sigma: [],
  prices: {},
  stats: [],
  corr: null,
  dateRange: null,
  isDefault: true,
  freq: "Daily",

  riskA: null,
  riskProfile: null,
  portfolioReady: false,
  questionnaireAnswers: [],

  setAnalysisData: (data) =>
    set({
      funds: data.funds,
      mu: data.mu,
      sigma: data.sigma,
      prices: data.prices,
      stats: data.stats,
      corr: data.corr,
      dateRange: data.date_range,
      isDefault: data.is_default,
      portfolioReady: false,
    }),

  setLang: (lang) => set({ lang }),
  setTheme: (theme) => set({ theme }),

  setFreq: (freq) => set({ freq }),

  setRiskProfile: (A, profile) =>
    set({ riskA: A, riskProfile: profile, portfolioReady: false }),

  setPortfolioReady: (ready) => set({ portfolioReady: ready }),

  setQuestionnaireAnswers: (answers) => set({ questionnaireAnswers: answers }),

  clearRiskProfile: () =>
    set({
      riskA: null,
      riskProfile: null,
      portfolioReady: false,
      questionnaireAnswers: [],
    }),
}));
