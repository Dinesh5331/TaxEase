"use client";

import { useState, useRef } from "react";
import {
  UploadCloud,
  CheckCircle2,
  FileText,
  X,
  AlertCircle,
  Loader2,
  Bot,
  ArrowRight,
  IndianRupee,
} from "lucide-react";
import { useRouter } from "next/navigation";

type Stage = "idle" | "uploading" | "ocr" | "ai" | "done" | "error";

type ExtractedData = {
  employee_name?: string;
  pan?: string;
  employer_name?: string;
  assessment_year?: string;
  total_salary?: string;
  gross_income?: string;
  taxable_income?: string;
  deductions?: Record<string, string>;
  tds?: string;
  [key: string]: unknown;
};

type UploadResult = {
  success: boolean;
  file_name: string;
  extracted_data: ExtractedData;
  itr_recommendation: string;
};

const STAGE_LABELS: Record<Stage, string> = {
  idle: "",
  uploading: "Uploading document...",
  ocr: "Extracting text with OCR...",
  ai: "Analysing data with AI...",
  done: "Processing complete!",
  error: "Something went wrong",
};

function ShieldCheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [stage, setStage] = useState<Stage>("idle");
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFileName(file.name);
    setErrorMsg(null);
    setResult(null);

    // Stage 1: uploading
    setStage("uploading");
    await pause(400);

    // Stage 2: OCR
    setStage("ocr");

    const formData = new FormData();
    formData.append("file", file);

    let data: UploadResult;
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      // Stage 3: AI (visual feedback while we parse large response)
      setStage("ai");

      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.error ?? "Upload failed");
      }

      data = json as UploadResult;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setErrorMsg(message);
      setStage("error");
      return;
    }

    setResult(data);
    setStage("done");

    // Persist data so dashboard + mapping pages can read it
    sessionStorage.setItem("taxease_ocr_result", JSON.stringify(data));
  };

  const handleProceedToMapping = () => {
    if (!result) return;
    // Persist extracted data so the mapping page can read it
    sessionStorage.setItem("taxease_ocr_result", JSON.stringify(result));
    router.push("/mapping");
  };

  const handleReset = () => {
    setStage("idle");
    setUploadedFileName(null);
    setResult(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const fmt = (v?: string) =>
    v && v !== "" && v !== "null" && v !== "N/A" ? v : "—";

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
          Upload Form 16
        </h1>
        <p className="text-slate-500">
          Drop your Form 16 PDF or image. AI will extract and analyse your data instantly.
        </p>
      </div>

      {/* Drop zone — shown only when idle */}
      {stage === "idle" && (
        <label className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center hover:border-primary/50 hover:bg-primary/5 transition-smooth cursor-pointer group">
          <input
            type="file"
            className="hidden"
            ref={fileInputRef}
            accept=".pdf,image/png,image/jpeg,image/jpg"
            onChange={handleFileUpload}
          />
          <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-6 group-hover:bg-white group-hover:scale-110 transition-smooth shadow-sm">
            <UploadCloud className="w-8 h-8 text-slate-400 group-hover:text-primary transition-smooth" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">
            Drag files here or click to select
          </h3>
          <p className="text-sm text-slate-500 mb-8 max-w-sm">
            Accepted: PDF, PNG, JPG, JPEG — up to 25 MB
          </p>
          <div className="bg-primary hover:bg-primary-dark text-white px-8 py-3 rounded-xl font-medium shadow-sm shadow-primary/30 transition-smooth">
            Select File
          </div>
        </label>
      )}

      {/* Progress — uploading / ocr / ai stages */}
      {(stage === "uploading" || stage === "ocr" || stage === "ai") && (
        <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            {STAGE_LABELS[stage]}
          </h3>

          <div className="space-y-4">
            {(["uploading", "ocr", "ai"] as Stage[]).map((s, idx) => {
              const stages: Stage[] = ["uploading", "ocr", "ai"];
              const currentIdx = stages.indexOf(stage);
              const isDone = idx < currentIdx;
              const isActive = idx === currentIdx;

              return (
                <div key={s} className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold border-2 transition-smooth ${
                      isDone
                        ? "bg-emerald-500 border-emerald-500 text-white"
                        : isActive
                        ? "bg-primary border-primary text-white animate-pulse"
                        : "bg-white border-slate-200 text-slate-400"
                    }`}
                  >
                    {isDone ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      isDone
                        ? "text-emerald-600"
                        : isActive
                        ? "text-primary"
                        : "text-slate-400"
                    }`}
                  >
                    {STAGE_LABELS[s]}
                  </span>
                </div>
              );
            })}
          </div>

          <p className="mt-6 text-xs text-slate-400 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            {uploadedFileName}
          </p>
        </div>
      )}

      {/* Error */}
      {stage === "error" && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 shadow-sm">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-red-500 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-bold text-red-800 mb-1">Processing Failed</h3>
              <p className="text-sm text-red-700">{errorMsg}</p>
              <p className="text-xs text-red-500 mt-2">
                Make sure the backend is running:{" "}
                <code className="bg-red-100 px-1 rounded font-mono">
                  cd backend &amp;&amp; uvicorn server:app --reload
                </code>
              </p>
            </div>
          </div>
          <button
            onClick={handleReset}
            className="mt-6 bg-white border border-slate-200 text-slate-700 px-5 py-2 rounded-xl text-sm font-medium hover:bg-slate-50 transition-smooth"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Done — show extracted data */}
      {stage === "done" && result && (
        <div className="space-y-6">
          {/* Success header */}
          <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center border border-emerald-100 shrink-0">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Upload Successful</h3>
                  <p className="text-sm text-slate-500 mt-1">{result.file_name}</p>
                </div>
              </div>
              <button
                onClick={handleReset}
                className="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-slate-600 transition-smooth"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Extracted fields */}
          <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
            <h4 className="text-sm font-bold text-slate-700 mb-5 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-primary" />
              Extracted Data
            </h4>
            <div className="grid grid-cols-2 gap-x-8 gap-y-5 text-sm">
              {[
                { label: "Employee Name", value: result.extracted_data?.employee_name },
                { label: "PAN", value: result.extracted_data?.pan },
                { label: "Employer Name", value: result.extracted_data?.employer_name },
                { label: "Assessment Year", value: result.extracted_data?.assessment_year },
                { label: "Gross Income", value: result.extracted_data?.gross_income },
                { label: "Taxable Income", value: result.extracted_data?.taxable_income },
                { label: "Total TDS", value: result.extracted_data?.tds },
                {
                  label: "80C Deduction",
                  value: result.extracted_data?.deductions?.["80C"],
                },
              ].map(({ label, value }) => (
                <div key={label}>
                  <span className="text-slate-400 block mb-1 text-xs uppercase tracking-wider font-semibold">
                    {label}
                  </span>
                  <span className="font-semibold text-slate-800 flex items-center gap-1">
                    {label.toLowerCase().includes("income") ||
                    label.toLowerCase().includes("tds") ||
                    label.toLowerCase().includes("deduction") ? (
                      <IndianRupee className="w-3.5 h-3.5 text-slate-500" />
                    ) : null}
                    {fmt(value as string)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* ITR Recommendation */}
          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5">
              <Bot className="w-20 h-20 text-primary" />
            </div>
            <h4 className="text-sm font-bold text-primary-dark mb-3 flex items-center gap-2">
              <Bot className="w-4 h-4" />
              ITR Recommendation (RAG)
            </h4>
            <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {result.itr_recommendation}
            </div>
          </div>

          {/* CTA */}
          <div className="flex justify-end">
            <button
              onClick={handleProceedToMapping}
              className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-xl font-medium shadow-sm transition-smooth text-sm flex items-center gap-2"
            >
              Proceed to ITR Mapping
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Privacy notice */}
      <div className="flex items-center gap-2 text-xs text-slate-500 justify-center bg-slate-50 py-3 rounded-lg border border-slate-100">
        <ShieldCheckIcon className="w-4 h-4 text-slate-400" />
        <strong>Privacy First:</strong> Files are processed locally and never stored permanently.
      </div>
    </div>
  );
}

function pause(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
