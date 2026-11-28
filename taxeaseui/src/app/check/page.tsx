"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";

type Question = {
  id: string;
  type: "bool" | "int" | "amount" | "percent" | "choice";
  text: string;
  help?: string;
  options?: string[];
};

type Analysis = {
  recommendation: {
    form: string;
    status: "final" | "provisional";
    reasons: string[];
    schedules: string[];
    notes: string[];
  };
  report: { conflicts: string[]; hints: string[]; open_questions: Question[] };
  taxpayer: { pan_masked: string; assessment_year: string };
  disclaimer: string;
};

type Files = { ais?: File; form16?: File; tis?: File };

const FILE_INPUTS: { key: keyof Files; label: string; accept: string }[] = [
  { key: "ais", label: "AIS (JSON, required)", accept: ".json" },
  { key: "form16", label: "Form 16 (PDF)", accept: ".pdf" },
  { key: "tis", label: "TIS (JSON)", accept: ".json" },
];

const inputClass = "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900";
const cardClass = "bg-white border border-slate-200 rounded-2xl p-6 shadow-sm";

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-4">
      <h3 className="text-sm font-bold text-slate-700 mb-1">{title}</h3>
      <ul className="list-disc pl-5 text-sm text-slate-600 space-y-1">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default function CheckPage() {
  const [files, setFiles] = useState<Files>({});
  // Raw strings as typed; converted to the engine's types only when sent.
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [asked, setAsked] = useState<Question[]>([]);
  const [result, setResult] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pickFile = (key: keyof Files, file?: File) => {
    // A different document can raise different questions: start over.
    setFiles((prev) => ({ ...prev, [key]: file }));
    setDraft({});
    setAsked([]);
    setResult(null);
    setError(null);
  };

  const analyze = async () => {
    if (!files.ais) return;
    const answers: Record<string, string | number | boolean> = {};
    for (const q of asked) {
      const raw = draft[q.id];
      if (raw === undefined || raw === "") continue;
      if (q.type === "bool") answers[q.id] = raw === "true";
      else if (q.type === "choice") answers[q.id] = raw;
      else answers[q.id] = Number(raw);
    }

    const body = new FormData();
    for (const { key } of FILE_INPUTS) {
      const file = files[key];
      if (file) body.append(key, file);
    }
    body.append("answers", JSON.stringify(answers));

    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/itr/analyze", { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Analysis failed");
      setResult(data);
      // Keep answered questions on screen so they can be corrected.
      setAsked((prev) => [
        ...prev,
        ...(data as Analysis).report.open_questions.filter((q) => !prev.some((p) => p.id === q.id)),
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  };

  const rec = result?.recommendation;
  const isFinal = rec?.status === "final";

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">ITR Form Check</h1>
        <p className="text-slate-500 text-sm">
          Which ITR form to file for AY 2026-27, decided by fixed rules from your documents and answers. Files are not
          stored.
        </p>
      </div>

      <div className={`${cardClass} space-y-4`}>
        {FILE_INPUTS.map(({ key, label, accept }) => (
          <label key={key} className="block">
            <span className="block text-sm font-semibold text-slate-700 mb-1">{label}</span>
            <input
              type="file"
              accept={accept}
              className={inputClass}
              onChange={(e) => pickFile(key, e.target.files?.[0])}
            />
          </label>
        ))}
      </div>

      {rec && result && (
        <div className={cardClass} aria-live="polite">
          <div className="flex items-center gap-3">
            {isFinal ? (
              <CheckCircle2 className="w-7 h-7 text-emerald-500" />
            ) : (
              <AlertTriangle className="w-7 h-7 text-amber-500" />
            )}
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{rec.form}</h2>
              <p className="text-sm text-slate-500">
                {isFinal ? "Final" : "Provisional: answer the questions below to confirm"}
                {result.taxpayer.pan_masked && ` · PAN ${result.taxpayer.pan_masked}`}
              </p>
            </div>
          </div>
          <List title="Why" items={rec.reasons} />
          <List title="Conflicts between documents" items={result.report.conflicts} />
          <List title="Check these" items={[...rec.notes, ...result.report.hints]} />
          <List title="Schedules to fill" items={rec.schedules} />
          <p className="mt-4 text-xs text-slate-400">{result.disclaimer}</p>
        </div>
      )}

      {asked.length > 0 && (
        <div className={`${cardClass} space-y-5`}>
          <h2 className="text-lg font-bold text-slate-800">Questions your documents cannot answer</h2>
          {asked.map((q) => (
            <label key={q.id} className="block">
              <span className="block text-sm font-medium text-slate-800">{q.text}</span>
              {q.help && <span className="block text-xs text-slate-500 mt-0.5">{q.help}</span>}
              {q.type === "bool" || q.type === "choice" ? (
                <select
                  className={`${inputClass} mt-2`}
                  value={draft[q.id] ?? ""}
                  onChange={(e) => setDraft((d) => ({ ...d, [q.id]: e.target.value }))}
                >
                  <option value="">Not answered</option>
                  {q.type === "bool" ? (
                    <>
                      <option value="false">No</option>
                      <option value="true">Yes</option>
                    </>
                  ) : (
                    q.options?.map((o) => (
                      <option key={o} value={o}>
                        {o}
                      </option>
                    ))
                  )}
                </select>
              ) : (
                <input
                  type="number"
                  // A capital gain can be a loss, so amounts have no lower bound.
                  min={q.type === "amount" ? undefined : 0}
                  className={`${inputClass} mt-2`}
                  value={draft[q.id] ?? ""}
                  onChange={(e) => setDraft((d) => ({ ...d, [q.id]: e.target.value }))}
                />
              )}
            </label>
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={analyze}
        disabled={!files.ais || busy}
        className="bg-primary hover:bg-primary-dark disabled:opacity-50 text-white px-6 py-3 rounded-xl font-medium text-sm flex items-center gap-2"
      >
        {busy && <Loader2 className="w-4 h-4 animate-spin" />}
        {result ? "Update recommendation" : "Check my ITR form"}
      </button>
    </div>
  );
}
