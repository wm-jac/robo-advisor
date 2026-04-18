"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, ChevronLeft, ChevronRight, RotateCcw, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useAppStore } from "@/lib/store";
import { fetchQuestions, computeProfile } from "@/lib/api";
import { localizeQuestions, t, translateProfile } from "@/lib/i18n";
import MetricCard from "@/components/MetricCard";

interface Question {
  id: number;
  text: string;
  options: string[];
  scores: number[];
}

interface QuestionsData {
  questions: Question[];
  min_score: number;
  max_score: number;
}

export default function ProfilePage() {
  const {
    riskA,
    riskProfile,
    portfolioReady,
    questionnaireAnswers,
    setRiskProfile,
    setQuestionnaireAnswers,
    clearRiskProfile,
    lang,
  } = useAppStore();

  const [data, setData] = useState<QuestionsData | null>(null);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [current, setCurrent] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuestions().then((d: any) => {
      setData(d);
      const initialAnswers =
        questionnaireAnswers.length === d.questions.length
          ? questionnaireAnswers
          : Array(d.questions.length).fill(null);
      setAnswers(initialAnswers);
      setLoading(false);
    });
    // Restore submitted state if profile already exists
    if (riskA !== null) setSubmitted(true);
  }, [questionnaireAnswers, riskA]);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-64" />
      </div>
    );
  }

  const { questions: rawQuestions, min_score, max_score } = data;
  const questions = localizeQuestions(rawQuestions, lang);
  const q = questions[current];
  const answered = answers.filter((a) => a !== null).length;
  const progress = answered / questions.length;

  const handleSelect = (optIdx: number) => {
    const next = [...answers];
    next[current] = optIdx;
    setAnswers(next);
    setQuestionnaireAnswers(next);
  };

  const handleNext = async () => {
    if (current < questions.length - 1) {
      setCurrent(current + 1);
    } else {
      // Submit
      const total = questions.reduce((sum, q, i) => {
        const ans = answers[i];
        return sum + (ans !== null ? q.scores[ans] : 0);
      }, 0);
      const res: any = await computeProfile(total);
      setRiskProfile(res.A, res.profile);
      setSubmitted(true);
    }
  };

  const handleRetake = () => {
    setAnswers(Array(questions.length).fill(null));
    setQuestionnaireAnswers(Array(questions.length).fill(null));
    setCurrent(0);
    setSubmitted(false);
    clearRiskProfile();
  };

  const profileColorMap: Record<string, "red" | "amber" | "blue" | "emerald" | "cyan"> = {
    "Very Conservative": "red",
    Conservative: "amber",
    Moderate: "blue",
    Aggressive: "emerald",
    "Very Aggressive": "cyan",
  };

  if (submitted && riskA !== null && riskProfile) {
    const localProfile = translateProfile(riskProfile, lang);
    const totalScore = questions.reduce((sum, q, i) => {
      const ans = answers[i];
      return sum + (ans !== null ? q.scores[ans] : 0);
    }, 0);

    return (
      <div>
        <motion.div className="page-header flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <div>
            <h1 className="page-title">{t(lang, "profile_result_title")}</h1>
            <p className="page-subtitle">{t(lang, "profile_result_subtitle")}</p>
          </div>
          {portfolioReady ? (
            <Link href="/portfolio" className="btn-primary inline-flex items-center gap-2 self-start">
              {t(lang, "view_portfolio")}
            </Link>
          ) : (
            <button
              type="button"
              disabled
              title={t(lang, "portfolio_not_ready")}
              className="btn-ghost inline-flex items-center gap-2 self-start opacity-50 cursor-not-allowed"
            >
              {t(lang, "view_portfolio")}
            </button>
          )}
        </motion.div>

        {/* Profile card */}
        <motion.div
          className="glass-card p-8 mb-8"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          style={{
            borderColor: `${riskProfile.color}30`,
            boxShadow: `0 0 60px ${riskProfile.color}15`,
          }}
        >
          {/* Top border accent */}
          <div
            className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl"
            style={{ background: riskProfile.color }}
          />

          <div className="flex flex-col sm:flex-row items-start gap-6">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shrink-0"
              style={{
                background: `${riskProfile.color}20`,
                border: `1px solid ${riskProfile.color}40`,
              }}
            >
              {riskProfile.emoji}
            </div>
            <div className="flex-1">
              <h2
                className="text-2xl font-bold mb-2"
                style={{
                  fontFamily: "var(--font-heading)",
                  color: riskProfile.color,
                  letterSpacing: "-0.03em",
                }}
              >
                {localProfile.label}
              </h2>
              <p className="text-secondary leading-relaxed">{localProfile.description}</p>
            </div>
          </div>
        </motion.div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <MetricCard
            label={t(lang, "risk_aversion")}
            value={riskA.toFixed(1)}
            sub={t(lang, "lower_more_aggressive")}
            accent={profileColorMap[riskProfile.label] ?? "blue"}
            delay={0}
          />
          <MetricCard
            label={t(lang, "profile_label")}
            value={localProfile.emoji + " " + localProfile.label}
            accent={profileColorMap[riskProfile.label] ?? "blue"}
            delay={0.05}
          />
        </div>

        {/* A value visual bar */}
        <motion.div
          className="glass-card p-6 mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <p className="section-title">{t(lang, "risk_aversion_scale")}</p>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-muted text-xs">{t(lang, "aggressive_a1")}</span>
            <div className="flex-1 h-2 rounded-full bg-elevated relative overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  width: `${((riskA - 1) / 7) * 100}%`,
                  background: `linear-gradient(90deg, #10b981, ${riskProfile.color})`,
                }}
              />
            </div>
            <span className="text-muted text-xs">{t(lang, "conservative_a8")}</span>
          </div>
          <p className="text-center text-sm text-secondary mt-1">
            Your A = <span className="font-mono font-medium text-primary">{riskA.toFixed(2)}</span>
            {" "}· This will be used to compute your optimal portfolio
          </p>
        </motion.div>

        {/* Answer review */}
        <motion.div
          className="glass-card p-6 mb-6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <p className="section-title">{t(lang, "answer_review")}</p>
          <div className="space-y-4">
            {questions.map((q, i) => {
              const ans = answers[i];
              return (
                <div key={q.id} className="border-b border-border/50 last:border-0 pb-4 last:pb-0">
                  <p className="text-secondary text-sm font-medium mb-1">
                    Q{i + 1}. {q.text}
                  </p>
                  {ans !== null && (
                    <p className="text-muted text-xs flex items-center gap-1.5">
                      <CheckCircle size={11} className="text-emerald shrink-0" />
                      {q.options[ans]}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>

        <button onClick={handleRetake} className="btn-ghost flex items-center gap-2">
          <RotateCcw size={14} /> {t(lang, "retake")}
        </button>
      </div>
    );
  }

  // Questionnaire UI
  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">{t(lang, "profile_title")}</h1>
        <p className="page-subtitle">{t(lang, "profile_subtitle", { count: questions.length })}</p>
      </motion.div>

      {/* Progress bar */}
      <motion.div className="mb-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="flex justify-between items-center mb-2">
          <span className="text-muted text-xs">
            {t(lang, "question_of", {
              current: Math.min(current + 1, questions.length),
              total: questions.length,
            })}
          </span>
          <span className="text-muted text-xs">{t(lang, "answered", { count: answered })}</span>
        </div>
        <div className="h-1.5 bg-elevated rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: "linear-gradient(90deg, #3b82f6, #06b6d4)" }}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </motion.div>

      {/* Question card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          className="glass-card p-8 mb-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.25 }}
          style={{ borderLeft: "3px solid #3b82f6" }}
        >
          <div className="badge-blue mb-4 text-xs w-fit">
            <Brain size={11} /> {t(lang, "question_of", { current: current + 1, total: questions.length })}
          </div>
          <h2
            className="text-lg font-semibold text-primary mb-6 leading-snug"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            {q.text}
          </h2>

          <div className="space-y-3">
            {q.options.map((opt, i) => {
              const selected = answers[current] === i;
              return (
                <motion.button
                  key={i}
                  onClick={() => handleSelect(i)}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.99 }}
                  className={`w-full text-left px-5 py-3.5 rounded-xl border text-sm transition-all duration-150 ${
                    selected
                      ? "border-blue bg-blue/10 text-primary"
                      : "border-border bg-elevated text-secondary hover:border-border-bright hover:text-primary"
                  }`}
                >
                  <span className="flex items-center gap-3">
                    <span
                      className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center ${
                        selected ? "border-blue bg-blue" : "border-border-bright"
                      }`}
                    >
                      {selected && (
                        <span className="w-2 h-2 rounded-full bg-white block" />
                      )}
                    </span>
                    {opt}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setCurrent(Math.max(0, current - 1))}
          disabled={current === 0}
          className="btn-ghost flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={16} /> {lang === "zh" ? "上一题" : "Back"}
        </button>

        <button
          onClick={handleNext}
          disabled={answers[current] === null}
          className="btn-primary flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {current < questions.length - 1 ? (
            <>{lang === "zh" ? "下一题" : "Next"} <ChevronRight size={16} /></>
          ) : (
            <>{lang === "zh" ? "提交" : "Submit"} <CheckCircle size={16} /></>
          )}
        </button>
      </div>
    </div>
  );
}
