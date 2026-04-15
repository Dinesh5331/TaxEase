"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, ChevronDown, ChevronUp, Layers, IndianRupee } from "lucide-react";

export default function MappingPage() {
  const [openSections, setOpenSections] = useState({
    income: true,
    deductions: true,
    taxes: false,
  });

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">ITR Mapping</h1>
        <p className="text-slate-500 flex items-center gap-2">
          <Layers className="w-4 h-4" />
          Review and confirm data extracted from your Form 16 before final submission.
        </p>
      </div>

      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div className="flex gap-4">
          <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-100 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            12 Fields Mapped Successfully
          </div>
          <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100 font-medium">
            <AlertTriangle className="w-4 h-4" />
            1 Field Needs Review
          </div>
        </div>
        <button className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-xl font-medium shadow-sm transition-smooth text-sm">
          Confirm & Proceed
        </button>
      </div>

      <div className="space-y-4">
        {/* Section: Income Details */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button 
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection('income')}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">1</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Gross Salary Income</h2>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-semibold text-slate-900 flex items-center"><IndianRupee className="w-4 h-4" />12,80,000</span>
              {openSections.income ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </div>
          </button>
          
          {openSections.income && (
            <div className="p-5 border-t border-slate-100">
              <table className="w-full text-sm text-left text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 rounded-lg">
                  <tr>
                    <th className="px-4 py-3 rounded-l-lg">Field (As per Form 16)</th>
                    <th className="px-4 py-3">Extracted Value</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 rounded-r-lg text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="hover:bg-slate-50 transition-smooth">
                    <td className="px-4 py-4 font-medium text-slate-800">Basic Salary (17(1))</td>
                    <td className="px-4 py-4">₹ 8,40,000</td>
                    <td className="px-4 py-4">
                      <span className="flex items-center gap-1.5 text-emerald-600"><CheckCircle2 className="w-4 h-4" /> Mapped</span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <button className="text-primary hover:text-primary-dark font-medium">Edit</button>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-smooth">
                    <td className="px-4 py-4 font-medium text-slate-800">Perquisites (17(2))</td>
                    <td className="px-4 py-4">₹ 1,50,000</td>
                    <td className="px-4 py-4">
                      <span className="flex items-center gap-1.5 text-emerald-600"><CheckCircle2 className="w-4 h-4" /> Mapped</span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <button className="text-primary hover:text-primary-dark font-medium">Edit</button>
                    </td>
                  </tr>
                  <tr className="hover:bg-amber-50/50 transition-smooth bg-amber-50/30">
                    <td className="px-4 py-4 font-medium text-slate-800">Allowances Exampt (10)</td>
                    <td className="px-4 py-4">
                      <input className="border border-amber-300 rounded px-2 py-1 bg-white max-w-[120px] focus:ring-2 focus:ring-amber-500 outline-none" defaultValue="2,90,000" />
                    </td>
                    <td className="px-4 py-4">
                      <span className="flex items-center gap-1.5 text-amber-600 font-medium"><AlertTriangle className="w-4 h-4" /> Verify</span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <button className="text-amber-700 hover:text-amber-800 font-medium">Auto-fix</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section: Deductions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button 
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection('deductions')}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">2</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Deductions (Chapter VI-A)</h2>
            </div>
            <div className="flex items-center gap-4">
               <span className="text-sm font-semibold text-slate-900 flex items-center"><IndianRupee className="w-4 h-4" />1,50,000</span>
              {openSections.deductions ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </div>
          </button>
          
          {openSections.deductions && (
            <div className="p-5 border-t border-slate-100">
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border border-slate-200 rounded-xl p-4 flex justify-between items-center bg-white shadow-sm">
                     <div>
                        <h4 className="font-bold text-slate-800">80C</h4>
                        <p className="text-xs text-slate-500 mt-0.5">Life insurance, EPF, ELSS</p>
                     </div>
                     <div className="text-right">
                        <p className="font-bold text-slate-900">₹ 1,50,000</p>
                        <p className="text-xs text-emerald-600 flex items-center justify-end gap-1 mt-0.5"><CheckCircle2 className="w-3 h-3" /> Maxed</p>
                     </div>
                  </div>
                  <div className="border border-slate-200 rounded-xl p-4 flex justify-between items-center bg-white shadow-sm opacity-60">
                     <div>
                        <h4 className="font-bold text-slate-800">80D</h4>
                        <p className="text-xs text-slate-500 mt-0.5">Medical Insurance</p>
                     </div>
                     <div className="text-right">
                        <p className="font-bold text-slate-500">₹ 0</p>
                        <p className="text-xs text-slate-400 flex items-center justify-end gap-1 mt-0.5">Not Claimed</p>
                     </div>
                  </div>
               </div>
            </div>
          )}
        </div>
        
        {/* Section: Taxes Paid */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <button 
            className="w-full flex items-center justify-between p-5 bg-slate-50 hover:bg-slate-100 transition-smooth"
            onClick={() => toggleSection('taxes')}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center border border-slate-200 shadow-sm">
                <span className="text-sm font-bold text-slate-600">3</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800">Taxes Deducted (TDS)</h2>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-semibold text-slate-900 flex items-center"><IndianRupee className="w-4 h-4" />1,24,800</span>
              {openSections.taxes ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
