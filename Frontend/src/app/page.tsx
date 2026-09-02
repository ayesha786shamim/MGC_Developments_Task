"use client";

import { FormEvent, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const EXAMPLE_QUESTIONS = [
  "What's the base price of a 2-bed in Block B?",
  "What's the total for a Margalla-facing corner unit on floor 15, 2-bed Block B?",
  "What's the transfer fee?",
  "What's the rental yield on a 1-bed?",
  "Who is the anchor tenant?",
];

type Source = {
  document: string;
  section: string;
  file: string;
  score: number;
  excerpt: string;
};

type AskResponse = {
  question: string;
  answer: string;
  sources: Source[];
  confidence: string;
};

type ScoreResponse = {
  conversion_probability: number;
  likely_to_convert: boolean;
  threshold: number;
  model_metric: { name: string; value: number };
  features_used: string[];
};

const defaultLead = {
  source: "Facebook",
  city: "Islamabad",
  area: "Bahria Town",
  property_type: "Apartment",
  budget_pkr_lac: 220,
  bedrooms: 2,
  first_response_minutes: 25,
  calls_made: 2,
  total_call_seconds: 180,
  whatsapp_replies: 2,
  site_visits: 0,
  agent_experience_years: 3,
  is_overseas: 0,
  referred_by_existing_client: 0,
  has_financing_approved: 0,
};

const inputClass =
  "w-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-brand-700";

const labelClass = "mb-1 block text-[13px] font-medium text-slate-500";

export default function Home() {
  const [mode, setMode] = useState<"ask" | "score">("ask");
  const [question, setQuestion] = useState("");
  const [askResult, setAskResult] = useState<AskResponse | null>(null);
  const [askError, setAskError] = useState("");
  const [askLoading, setAskLoading] = useState(false);

  const [lead, setLead] = useState(defaultLead);
  const [scoreResult, setScoreResult] = useState<ScoreResponse | null>(null);
  const [scoreError, setScoreError] = useState("");
  const [scoreLoading, setScoreLoading] = useState(false);

  const scorePct = useMemo(() => {
    if (!scoreResult) return 0;
    return Math.round(scoreResult.conversion_probability * 100);
  }, [scoreResult]);

  async function onAsk(e: FormEvent) {
    e.preventDefault();
    setAskLoading(true);
    setAskError("");
    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        let detail = await res.text();
        try {
          const parsed = JSON.parse(detail);
          detail = parsed.detail || detail;
        } catch {
          /* keep raw */
        }
        throw new Error(detail);
      }
      setAskResult(await res.json());
    } catch (err) {
      setAskResult(null);
      setAskError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setAskLoading(false);
    }
  }

  async function onScore(e: FormEvent) {
    e.preventDefault();
    setScoreLoading(true);
    setScoreError("");
    try {
      const res = await fetch(`${API_BASE}/api/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lead),
      });
      if (!res.ok) throw new Error(await res.text());
      setScoreResult(await res.json());
    } catch (err) {
      setScoreResult(null);
      setScoreError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setScoreLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5 sm:px-8">
          <div className="flex items-baseline gap-3">
            <span className="text-sm font-semibold tracking-tight text-brand-700">
              MGC
            </span>
            <span className="hidden h-3 w-px bg-slate-200 sm:block" />
            <h1 className="text-sm font-medium text-slate-800">Sales Desk</h1>
          </div>
          <p className="text-xs text-slate-400">Aurora Heights · Islamabad</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <div className="mb-8 flex items-end justify-between gap-6 border-b border-slate-200">
          <div className="flex gap-6">
            {(
              [
                ["ask", "Document Q&A"],
                ["score", "Lead score"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setMode(id)}
                className={`-mb-px border-b-2 pb-3 text-sm font-medium transition ${
                  mode === id
                    ? "border-brand-700 text-brand-700"
                    : "border-transparent text-slate-400 hover:text-slate-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="hidden pb-3 text-xs text-slate-400 md:block">
            {mode === "ask"
              ? "Answers grounded in MGC documents"
              : "Conversion probability for call priority"}
          </p>
        </div>

        {mode === "ask" ? (
          <div className="animate-fade-up grid gap-0 overflow-hidden rounded-lg border border-slate-200 bg-white lg:grid-cols-2">
            <section className="border-b border-slate-200 p-6 lg:border-r lg:border-b-0 lg:p-8">
              <h2 className="text-base font-semibold text-slate-900">Ask a question</h2>
              <p className="mt-1 text-sm text-slate-500">
                Brochure, price list, and booking policy.
              </p>

              <form onSubmit={onAsk} className="mt-6 space-y-4">
                <label className="block">
                  <span className={labelClass}>Question</span>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    rows={4}
                    placeholder="e.g. What is the transfer fee?"
                    className={`${inputClass} resize-y`}
                    required
                  />
                </label>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={askLoading || !question.trim()}
                    className="bg-brand-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-800 disabled:opacity-40"
                  >
                    {askLoading ? "Searching…" : "Ask"}
                  </button>
                  {askError ? (
                    <p className="text-sm text-red-600">{askError}</p>
                  ) : null}
                </div>
              </form>

              <div className="mt-8">
                <p className={labelClass}>Examples</p>
                <div className="mt-2 space-y-0 divide-y divide-slate-100 border-t border-slate-100">
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => setQuestion(q)}
                      className="block w-full py-2.5 text-left text-sm text-slate-600 transition hover:text-brand-700"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <section className="min-h-[420px] bg-slate-50/60 p-6 lg:p-8">
              {askResult ? (
                <div className="animate-fade-up space-y-6">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-900">Answer</h3>
                    <span className="text-xs text-slate-400">
                      {askResult.confidence} confidence
                    </span>
                  </div>

                  <div className="whitespace-pre-wrap text-[15px] leading-7 text-slate-800">
                    {askResult.answer.replace(/\*\*/g, "")}
                  </div>

                  {askResult.sources.length > 0 ? (
                    <div className="border-t border-slate-200 pt-5">
                      <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                        Source
                      </p>
                      {askResult.sources.map((s, i) => (
                        <div key={`${s.file}-${s.section}-${i}`} className="mt-3">
                          <p className="text-sm font-medium text-slate-800">
                            {s.document}
                            <span className="font-normal text-slate-400">
                              {" "}
                              · {s.section}
                            </span>
                          </p>
                          <p className="mt-1 text-sm leading-6 text-slate-500">
                            {s.excerpt}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="flex h-full min-h-[360px] flex-col justify-center">
                  <p className="text-sm font-medium text-slate-400">Response</p>
                  <p className="mt-2 max-w-sm text-sm leading-6 text-slate-400">
                    Ask a question to see a grounded answer and its document
                    source here.
                  </p>
                </div>
              )}
            </section>
          </div>
        ) : (
          <div className="animate-fade-up grid gap-0 overflow-hidden rounded-lg border border-slate-200 bg-white lg:grid-cols-[1.35fr_0.65fr]">
            <form
              onSubmit={onScore}
              className="border-b border-slate-200 p-6 lg:border-r lg:border-b-0 lg:p-8"
            >
              <h2 className="text-base font-semibold text-slate-900">Score a lead</h2>
              <p className="mt-1 text-sm text-slate-500">
                Estimate conversion likelihood for call priority.
              </p>

              <div className="mt-6 space-y-6">
                <div>
                  <p className="mb-3 text-xs font-medium tracking-wide text-slate-400 uppercase">
                    Profile
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {(
                      [
                        ["source", "Source", "text"],
                        ["city", "City", "text"],
                        ["area", "Area", "text"],
                        ["property_type", "Property type", "text"],
                        ["budget_pkr_lac", "Budget (PKR lac)", "number"],
                        ["bedrooms", "Bedrooms", "number"],
                      ] as const
                    ).map(([key, label, type]) => (
                      <label key={key} className="block">
                        <span className={labelClass}>{label}</span>
                        <input
                          type={type}
                          value={lead[key] as string | number}
                          onChange={(e) =>
                            setLead((prev) => ({
                              ...prev,
                              [key]:
                                type === "number"
                                  ? Number(e.target.value)
                                  : e.target.value,
                            }))
                          }
                          className={inputClass}
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-3 text-xs font-medium tracking-wide text-slate-400 uppercase">
                    Engagement
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {(
                      [
                        ["first_response_minutes", "First response (min)"],
                        ["calls_made", "Calls made"],
                        ["total_call_seconds", "Total call seconds"],
                        ["whatsapp_replies", "WhatsApp replies"],
                        ["site_visits", "Site visits"],
                        ["agent_experience_years", "Agent experience (yrs)"],
                      ] as const
                    ).map(([key, label]) => (
                      <label key={key} className="block">
                        <span className={labelClass}>{label}</span>
                        <input
                          type="number"
                          value={lead[key] as number}
                          onChange={(e) =>
                            setLead((prev) => ({
                              ...prev,
                              [key]: Number(e.target.value),
                            }))
                          }
                          className={inputClass}
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-3 text-xs font-medium tracking-wide text-slate-400 uppercase">
                    Flags
                  </p>
                  <div className="flex flex-wrap gap-x-6 gap-y-2">
                    {(
                      [
                        ["is_overseas", "Overseas"],
                        ["referred_by_existing_client", "Client referral"],
                        ["has_financing_approved", "Financing approved"],
                      ] as const
                    ).map(([key, label]) => (
                      <label
                        key={key}
                        className="flex items-center gap-2 text-sm text-slate-600"
                      >
                        <input
                          type="checkbox"
                          checked={Boolean(lead[key])}
                          onChange={(e) =>
                            setLead((prev) => ({
                              ...prev,
                              [key]: e.target.checked ? 1 : 0,
                            }))
                          }
                          className="h-3.5 w-3.5 accent-brand-700"
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <button
                    type="submit"
                    disabled={scoreLoading}
                    className="bg-brand-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-800 disabled:opacity-40"
                  >
                    {scoreLoading ? "Scoring…" : "Score lead"}
                  </button>
                  {scoreError ? (
                    <p className="text-sm text-red-600">{scoreError}</p>
                  ) : null}
                </div>
              </div>
            </form>

            <aside className="flex min-h-[360px] flex-col justify-center bg-slate-50/60 p-6 lg:p-8">
              {scoreResult ? (
                <div className="animate-fade-up">
                  <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                    Conversion likelihood
                  </p>
                  <p className="mt-3 font-display text-5xl tracking-tight text-slate-900">
                    {scorePct}
                    <span className="text-2xl text-slate-400">%</span>
                  </p>
                  <p className="mt-3 text-sm text-slate-600">
                    {scoreResult.likely_to_convert
                      ? "Prioritize this call"
                      : "Lower priority vs warmer leads"}
                  </p>
                  <p className="mt-6 border-t border-slate-200 pt-4 text-xs text-slate-400">
                    {scoreResult.model_metric.name} ={" "}
                    {scoreResult.model_metric.value}
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium text-slate-400">Score</p>
                  <p className="mt-2 max-w-xs text-sm leading-6 text-slate-400">
                    Submit lead details to see conversion probability.
                  </p>
                </div>
              )}
            </aside>
          </div>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-8 text-xs text-slate-400 sm:px-8">
        MGC Developments · Near Al-Jannat Mall, GT Road, Islamabad
      </footer>
    </div>
  );
}
