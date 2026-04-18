import { t, type Lang } from "@/lib/i18n";
import type { RiskFreeRateInfo } from "@/lib/store";

export function formatRiskFreeRate(
  lang: Lang,
  info: RiskFreeRateInfo | null | undefined
) {
  if (!info) return "";
  if (info.fallback) return t(lang, "risk_free_note_fallback");

  return t(lang, "risk_free_note", {
    rate: (info.rate * 100).toFixed(2),
    asOf: info.as_of ?? "latest",
  });
}

export function formatRiskFreeRateShort(
  lang: Lang,
  info: RiskFreeRateInfo | null | undefined
) {
  if (!info) return "";
  if (info.fallback) return t(lang, "risk_free_note_short_fallback");

  return t(lang, "risk_free_note_short", {
    rate: (info.rate * 100).toFixed(2),
    asOf: info.as_of ?? "latest",
  });
}
