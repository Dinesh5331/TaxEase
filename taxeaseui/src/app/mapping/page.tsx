"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Layers,
  IndianRupee,
  Bot,
  Info,
} from "lucide-react";

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
};

type EditableField = Exclude<keyof ExtractedData, "deductions">;

type OcrResult = {
  success: boolean;
  file_name: string;
  extracted_data: ExtractedData;
  itr_recommendation: string;
};

// Fallback data shown when no real OCR result is available (demo mode)
const DEMO_DATA: ExtractedData = {
  employee_name: "Demo User",
  pan: "ABCDE1234F",
  employer_name: "Acme Corp Ltd.",
  assessment_year: "2024-25",
  total_salary: "12,80,000",
  gross_income: "12,80,000",
  taxable_income: "11,30,000",
  deductions: { "80C": "1,50,000", "80D": "0" },
  tds: "1,24,800",
};

function fmt(v?: string) {
  if (!v || v === "" || v === "null" || v === "N/A") return "—";
  return v;
}

export default function MappingPage() {
  const [openSections, setOpenSections] = useState({
    income: true,
    deductions: true,
    taxes: false,
  });
  const [ocrResult, setOcrResult] = useState<OcrResult | null>(null);
  const [data, setData] = useState<ExtractedData>(DEMO_DATA);
  const [isDemo, setIsDemo] = useState(false);
  const [editingField, setEditingField] = useState<EditableField | null>(null);
  const [editingValue, setEditingValue] = useState("");

  // Load real OCR data from sessionStorage (set by upload page)
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("taxease_ocr_result");
      if (raw) {
        const parsed = JSON.parse(raw) as OcrResult;
        setOcrResult(parsed);
        setData(parsed.extracted_data ?? DEMO_DATA);
        setIsDemo(false);
      } else {
        setData(DEMO_DATA);
        setIsDemo(true);
      }
    } catch {
      setData(DEMO_DATA);
      setIsDemo(true);
    }
  }, []);

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleEdit = (field: EditableField) => {
    setEditingField(field);
    setEditingValue(data[field] ?? "");
  };

  const handleCancel = () => {
    setEditingField(null);
    setEditingValue("");
  };

  const handleSave = () => {
    if (!editingField) return;

    const updatedData = {
      ...data,
      [editingField]: editingValue,
    } as ExtractedData;

    setData(updatedData);

    if (ocrResult) {
      const updatedResult = {
        ...ocrResult,
        extracted_data: updatedData,
      };
      setOcrResult(updatedResult);
    }

    setEditingField(null);
    setEditingValue("");
  };

  const deductions = data.deductions ?? {};
  const has80C = deductions["80C"] && deductions["80C"] !== "0" && deductions["80C"] !== "";
  const has80D = deductions["80D"] && deductions["80D"] !== "0" && deductions["80D"] !== "";

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
          ITR Mapping
        </h1>
        <p className="text-slate-500 flex items-center gap-2">
          <Layers className="w-4 h-4" />
          Review data extracted from{" "}
          {ocrResult?.file_name ? (
            <span className="font-medium text-slate-700">{ocrResult.file_name}</span>
          ) : (
            "Form 16"
          )}{" "}
          before final submission.
        </p>
      </div>

      {/* Demo mode notice */}
      {isDemo && (
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs">
          <Info className="w-4 h-4 shrink-0" />
          <span>
            Showing <strong>demo data</strong>. Upload a Form 16 on the{" "}
            <a href="/upload" className="underline">Upload page</a> to see real extracted data here.
          </span>
        </div>
      )}

      {/* Status bar */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div className="flex gap-3">
          <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-100 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Fields Mapped Successfully
          </div>
          {!has80D && (
            <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100 font-medium">
              <AlertTriangle className="w-4 h-4" />
              80D Not Claimed
            </div>
          )}
        </div>
        <button className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-xl font-medium shadow-sm transition-smooth text-sm">
          Confirm &amp; Proceed
        </button>
      </div>

      <div className="space-y-4">
        {/* Section 1: Income */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection("income")}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">1</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Gross Salary Income</h2>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-semibold text-slate-900 flex items-center">
                <IndianRupee className="w-4 h-4" />
                {fmt(data.gross_income)}
              </span>
              {openSections.income ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </div>
          </button>

          {openSections.income && (
            <div className="p-5 border-t border-slate-100">
              <table className="w-full text-sm text-left text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500">
                  <tr>
                    <th className="px-4 py-3 rounded-l-lg">Field</th>
                    <th className="px-4 py-3">Extracted Value</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 rounded-r-lg text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[
                    { label: "Employee Name", key: "employee_name" as EditableField },
                    { label: "Employer Name", key: "employer_name" as EditableField },
                    { label: "PAN", key: "pan" as EditableField },
                    { label: "Assessment Year", key: "assessment_year" as EditableField },
                    { label: "Total Salary", key: "total_salary" as EditableField },
                    { label: "Gross Income", key: "gross_income" as EditableField },
                    { label: "Taxable Income", key: "taxable_income" as EditableField },
                  ].map(({ label, key }) => {
                    const value = data[key];
                    const isEditing = editingField === key;

                    return (
                      <tr key={label} className="hover:bg-slate-50 transition-smooth">
                        <td className="px-4 py-4 font-medium text-slate-800">{label}</td>
                        <td className="px-4 py-4">
                          {isEditing ? (
                            <input
                              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900"
                              value={editingValue}
                              onChange={(e) => setEditingValue(e.target.value)}
                            />
                          ) : (
                            fmt(value)
                          )}
                        </td>
                        <td className="px-4 py-4">
                          {fmt(value) !== "—" ? (
                            <span className="flex items-center gap-1.5 text-emerald-600">
                              <CheckCircle2 className="w-4 h-4" /> Mapped
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 text-amber-600">
                              <AlertTriangle className="w-4 h-4" /> Not found
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-4 text-right">
                          {isEditing ? (
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                onClick={handleSave}
                                className="rounded-xl bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary-dark"
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                onClick={handleCancel}
                                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              className="text-primary hover:text-primary-dark font-medium"
                              onClick={() => handleEdit(key)}
                            >
                              Edit
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 2: Deductions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection("deductions")}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">2</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Deductions (Chapter VI-A)</h2>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-semibold text-slate-900 flex items-center">
                <IndianRupee className="w-4 h-4" />
                {fmt(deductions["80C"])}
              </span>
              {openSections.deductions ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </div>
          </button>

          {openSections.deductions && (
            <div className="p-5 border-t border-slate-100">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  className={`border rounded-xl p-4 flex justify-between items-center bg-white shadow-sm ${
                    has80C ? "border-slate-200" : "border-amber-100 bg-amber-50/30 opacity-70"
                  }`}
                >
                  <div>
                    <h4 className="font-bold text-slate-800">80C</h4>
                    <p className="text-xs text-slate-500 mt-0.5">Life insurance, EPF, ELSS</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-900 flex items-center gap-0.5">
                      <IndianRupee className="w-3.5 h-3.5" />
                      {fmt(deductions["80C"])}
                    </p>
                    <p className="text-xs text-emerald-600 flex items-center justify-end gap-1 mt-0.5">
                      {has80C ? (
                        <><CheckCircle2 className="w-3 h-3" /> Claimed</>
                      ) : (
                        <span className="text-slate-400">Not Claimed</span>
                      )}
                    </p>
                  </div>
                </div>

                <div
                  className={`border rounded-xl p-4 flex justify-between items-center bg-white shadow-sm ${
                    has80D ? "border-slate-200" : "border-slate-200 opacity-60"
                  }`}
                >
                  <div>
                    <h4 className="font-bold text-slate-800">80D</h4>
                    <p className="text-xs text-slate-500 mt-0.5">Medical Insurance</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-500 flex items-center gap-0.5">
                      <IndianRupee className="w-3.5 h-3.5" />
                      {fmt(deductions["80D"]) !== "—" ? fmt(deductions["80D"]) : "0"}
                    </p>
                    <p className="text-xs text-slate-400 flex items-center justify-end gap-1 mt-0.5">
                      Not Claimed
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Section 3: Taxes */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection("taxes")}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">3</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Taxes Deducted (TDS)</h2>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-semibold text-slate-900 flex items-center">
                <IndianRupee className="w-4 h-4" />
                {fmt(data.tds)}
              </span>
              {openSections.taxes ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </div>
          </button>

          {openSections.taxes && (
            <div className="p-5 border-t border-slate-100">
              <table className="w-full text-sm text-left text-slate-600">
                <tbody className="divide-y divide-slate-100">
                  <tr className="hover:bg-slate-50">
                    <td className="px-4 py-4 font-medium text-slate-800">Total TDS Deducted</td>
                    <td className="px-4 py-4 flex items-center gap-1">
                      <IndianRupee className="w-3.5 h-3.5" />
                      {fmt(data.tds)}
                    </td>
                    <td className="px-4 py-4">
                      <span className="flex items-center gap-1.5 text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" /> Mapped
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ITR Recommendation — shown only with real data */}
        {ocrResult?.itr_recommendation && (
          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 shadow-sm">
            <h4 className="text-sm font-bold text-primary-dark mb-3 flex items-center gap-2">
              <Bot className="w-4 h-4" />
              ITR Recommendation
            </h4>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {ocrResult.itr_recommendation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
