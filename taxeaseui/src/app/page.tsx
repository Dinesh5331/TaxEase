"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  TrendingUp,
  ShieldCheck,
  Zap,
  IndianRupee,
  Bot,
  Leaf,
  FileUp,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Upload,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";

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

type OcrResult = {
  success: boolean;
  file_name: string;
  extracted_data: ExtractedData;
  itr_recommendation: string;
};

/** Parse Indian formatted numbers like "12,80,000" or "₹12,80,000" into a number */
function parseIndianNumber(val?: string): number {
  if (!val || val === "—" || val === "N/A" || val === "null" || val === "") return 0;
  return Number(val.replace(/[₹,\s]/g, "")) || 0;
}

/** Format a number in Indian locale style */
function fmtINR(n: number): string {
  if (n === 0) return "0";
  return n.toLocaleString("en-IN");
}

const PIE_COLORS = ["#22C55E", "#0F172A", "#3B82F6", "#F59E0B"];

export default function Dashboard() {
  const router = useRouter();
  const [ocrResult, setOcrResult] = useState<OcrResult | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [userName, setUserName] = useState("TaxEase");

  useEffect(() => {
    // Load OCR data from sessionStorage (set by upload page)
    try {
      const raw = sessionStorage.getItem("taxease_ocr_result");
      if (raw) {
        const parsed = JSON.parse(raw) as OcrResult;
        setOcrResult(parsed);
      }
    } catch {
      // no data
    }

    // Load user name
    try {
      const userRaw = localStorage.getItem("taxease_user");
      if (userRaw) {
        const user = JSON.parse(userRaw);
        if (user?.name) setUserName(user.name.split(" ")[0]);
      }
    } catch {
      // no user
    }

    setIsLoaded(true);
  }, []);

  // Don't render until hydrated to avoid mismatch
  if (!isLoaded) {
    return (
      <div className="max-w-6xl mx-auto flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // ── No Form-16 uploaded yet → show empty state ────────────────────────
  if (!ocrResult) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 pb-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Hello, {userName}
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary" />
            AI-driven tax insights in a sleek workspace
          </p>
        </div>

        {/* Empty State Hero */}
        <div
          className="relative rounded-3xl overflow-hidden p-10 md:p-14 flex flex-col items-center text-center"
          style={{
            background: "linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 40%, #f8fafc 100%)",
            border: "1px solid #bbf7d0",
          }}
        >
          {/* Decorative circles */}
          <div
            className="absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-30"
            style={{ background: "radial-gradient(circle, #22C55E 0%, transparent 70%)" }}
          />
          <div
            className="absolute -bottom-12 -left-12 w-40 h-40 rounded-full opacity-20"
            style={{ background: "radial-gradient(circle, #4ADE80 0%, transparent 70%)" }}
          />

          <div className="w-20 h-20 rounded-2xl bg-white flex items-center justify-center mb-6 shadow-lg shadow-emerald-100 border border-emerald-100">
            <Upload className="w-10 h-10 text-primary" />
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            Upload your Form 16 to get started
          </h2>
          <p className="text-slate-500 max-w-md mb-8 leading-relaxed">
            Your dashboard will come alive with real salary income, tax paid,
            deductions, and AI-powered insights — all extracted from your Form 16.
          </p>

          <button
            onClick={() => router.push("/upload")}
            className="bg-primary hover:bg-primary-dark text-white px-8 py-3.5 rounded-xl font-semibold shadow-md shadow-primary/30 transition-smooth flex items-center gap-2 text-sm"
          >
            <FileUp className="w-5 h-5" />
            Upload Form 16
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[
            {
              icon: BarChart3,
              title: "Salary Breakdown",
              desc: "See monthly income, tax deducted, and deductions at a glance.",
              color: "text-emerald-600",
              bg: "bg-emerald-50",
              border: "border-emerald-100",
            },
            {
              icon: ShieldCheck,
              title: "Deduction Analysis",
              desc: "Know exactly which sections (80C, 80D, etc.) you've claimed.",
              color: "text-blue-600",
              bg: "bg-blue-50",
              border: "border-blue-100",
            },
            {
              icon: Bot,
              title: "AI Recommendations",
              desc: "Get personalized tips to optimize your tax and maximize savings.",
              color: "text-amber-600",
              bg: "bg-amber-50",
              border: "border-amber-100",
            },
          ].map((card) => (
            <div
              key={card.title}
              className={`bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-smooth`}
            >
              <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center mb-4 border ${card.border}`}>
                <card.icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <h3 className="text-sm font-bold text-slate-800 mb-1">{card.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{card.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Form-16 data exists → show real dashboard ─────────────────────────
  const data = ocrResult.extracted_data;
  const grossIncome = parseIndianNumber(data.gross_income);
  const taxableIncome = parseIndianNumber(data.taxable_income);
  const totalSalary = parseIndianNumber(data.total_salary);
  const tds = parseIndianNumber(data.tds);
  const deductions = data.deductions ?? {};
  const ded80C = parseIndianNumber(deductions["80C"]);
  const ded80D = parseIndianNumber(deductions["80D"]);
  const totalDeductions = ded80C + ded80D;

  // Build a bar chart from the data we have
  const barData = [
    { name: "Gross Income", value: grossIncome, fill: "#22C55E" },
    { name: "Taxable Income", value: taxableIncome, fill: "#3B82F6" },
    { name: "Total TDS", value: tds, fill: "#0F172A" },
    { name: "Deductions", value: totalDeductions, fill: "#F59E0B" },
  ].filter((d) => d.value > 0);

  // Build a pie chart for deductions breakdown
  const pieData = Object.entries(deductions)
    .map(([key, val]) => ({ name: `Section ${key}`, value: parseIndianNumber(val) }))
    .filter((d) => d.value > 0);

  // Calculate effective tax rate
  const effectiveTaxRate = grossIncome > 0 ? ((tds / grossIncome) * 100).toFixed(1) : "0";

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div className="flex flex-col gap-1 md:flex-row md:items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Hello, {data.employee_name?.split(" ")[0] || userName}
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary" />
            {data.assessment_year
              ? `Assessment Year ${data.assessment_year}`
              : "AI-driven tax insights in a sleek workspace"}
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-100">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Form 16 Uploaded
          </span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Salary Income */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <Briefcase className="w-16 h-16 text-primary" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center border border-slate-100">
              <Briefcase className="w-5 h-5 text-slate-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Gross Income
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              {fmtINR(grossIncome)}
            </h2>
          </div>
          {totalSalary > 0 && totalSalary !== grossIncome && (
            <div className="mt-4 text-sm text-slate-500">
              Total Salary: <span className="font-semibold text-slate-700">₹{fmtINR(totalSalary)}</span>
            </div>
          )}
        </div>

        {/* Tax Paid */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <TrendingUp className="w-16 h-16 text-emerald-500" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center border border-emerald-100">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Tax Paid (TDS)
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              {fmtINR(tds)}
            </h2>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-emerald-700">
            <span>Effective rate: {effectiveTaxRate}%</span>
          </div>
        </div>

        {/* Deductions */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <ShieldCheck className="w-16 h-16 text-blue-500" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center border border-blue-100">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Total Deductions
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              {fmtINR(totalDeductions)}
            </h2>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {ded80C > 0 && (
              <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
                80C: ₹{fmtINR(ded80C)}
              </span>
            )}
            {ded80D > 0 && (
              <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
                80D: ₹{fmtINR(ded80D)}
              </span>
            )}
            {totalDeductions === 0 && (
              <span className="text-xs text-slate-400">No deductions claimed</span>
            )}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Tax Breakdown</h3>
              <p className="text-sm text-slate-500 mt-1">
                Income vs Tax vs Deductions
              </p>
            </div>
            {data.assessment_year && (
              <span className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-slate-600 font-medium">
                AY {data.assessment_year}
              </span>
            )}
          </div>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={barData}
                margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#E2E8F0"
                  opacity={0.5}
                />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                  dy={10}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                  tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`}
                />
                <Tooltip
                  cursor={{ fill: "#f1f5f9" }}
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  formatter={(value) => [`₹${fmtINR(Number(value ?? 0))}`, ""]}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={48}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col">
          <div className="mb-6">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              AI Insights
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              From your Form 16 analysis
            </p>
          </div>

          <div className="flex-1 flex flex-col gap-4">
            {/* ITR Recommendation */}
            {ocrResult.itr_recommendation && (
              <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 flex gap-3 relative overflow-hidden">
                <div className="w-1.5 h-full bg-primary absolute left-0 top-0" />
                <div className="mt-0.5">
                  <Zap className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-primary-dark">
                    ITR Recommendation
                  </h4>
                  <p className="text-sm text-slate-600 mt-1 leading-snug line-clamp-4">
                    {ocrResult.itr_recommendation.slice(0, 200)}
                    {ocrResult.itr_recommendation.length > 200 ? "..." : ""}
                  </p>
                  <button
                    onClick={() => router.push("/mapping")}
                    className="mt-3 text-xs font-semibold text-primary hover:text-primary-dark flex items-center transition-smooth"
                  >
                    View Full Mapping
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </button>
                </div>
              </div>
            )}

            {/* Deduction Summary */}
            {ded80C > 0 && (
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-3">
                <div className="mt-0.5">
                  <ShieldCheck className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-700">
                    Section 80C
                  </h4>
                  <p className="text-sm text-slate-500 mt-1 leading-snug">
                    You claimed{" "}
                    <span className="font-semibold text-slate-800">
                      ₹{fmtINR(ded80C)}
                    </span>{" "}
                    {ded80C >= 150000
                      ? "— limit fully utilized!"
                      : `out of ₹1,50,000 limit.`}
                  </p>
                </div>
              </div>
            )}

            {/* NPS suggestion */}
            {ded80C < 150000 && (
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-3">
                <div className="mt-0.5">
                  <Leaf className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-700">
                    Tax Saving Opportunity
                  </h4>
                  <p className="text-sm text-slate-500 mt-1 leading-snug">
                    Consider investing ₹{fmtINR(150000 - ded80C)} more under
                    80C (EPF/ELSS/PPF) and ₹50,000 in NPS under 80CCD(1B) for
                    additional deductions.
                  </p>
                </div>
              </div>
            )}

            {/* PAN Info */}
            {data.pan && (
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-3">
                <div className="mt-0.5">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-700">PAN Verified</h4>
                  <p className="text-sm text-slate-500 mt-1 leading-snug">
                    PAN:{" "}
                    <span className="font-mono font-semibold text-slate-700 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                      {data.pan}
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Deductions Pie Chart (if any) */}
      {pieData.length > 0 && (
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            Deductions Breakdown
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            Chapter VI-A deductions claimed
          </p>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="w-48 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pieData.map((_entry, index) => (
                      <Cell
                        key={`pie-${index}`}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [`₹${fmtINR(Number(value ?? 0))}`, ""]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-4">
              {pieData.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{
                      background: PIE_COLORS[index % PIE_COLORS.length],
                    }}
                  />
                  <span className="text-sm text-slate-600">
                    {entry.name}:{" "}
                    <span className="font-semibold text-slate-800">
                      ₹{fmtINR(entry.value)}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Employer Info Strip */}
      {data.employer_name && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex items-center justify-between text-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center border border-slate-200">
              <Briefcase className="w-4 h-4 text-slate-500" />
            </div>
            <div>
              <span className="text-slate-500">Employer: </span>
              <span className="font-semibold text-slate-800">{data.employer_name}</span>
            </div>
          </div>
          <button
            onClick={() => router.push("/mapping")}
            className="text-primary hover:text-primary-dark font-medium flex items-center gap-1 transition-smooth"
          >
            View Full Details <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
