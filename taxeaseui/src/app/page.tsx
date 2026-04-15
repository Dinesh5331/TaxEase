"use client";

import { Briefcase, TrendingUp, ShieldCheck, Zap, ArrowUpRight, ArrowDownRight, IndianRupee, Bot, Leaf } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const chartData = [
  { name: "Apr", income: 106000, tax: 10400, deduct: 8000 },
  { name: "May", income: 106000, tax: 10400, deduct: 8000 },
  { name: "Jun", income: 106000, tax: 10400, deduct: 8000 },
  { name: "Jul", income: 120000, tax: 12500, deduct: 15000 },
  { name: "Aug", income: 106000, tax: 10400, deduct: 12000 },
  { name: "Sep", income: 106000, tax: 10400, deduct: 8000 },
  { name: "Oct", income: 150000, tax: 18000, deduct: 25000 },
  { name: "Nov", income: 106000, tax: 10400, deduct: 10000 },
  { name: "Dec", income: 106000, tax: 10400, deduct: 12000 },
  { name: "Jan", income: 106000, tax: 10400, deduct: 8000 },
  { name: "Feb", income: 106000, tax: 10400, deduct: 15000 },
  { name: "Mar", income: 154000, tax: 19500, deduct: 21000 },
];

export default function Dashboard() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col gap-1 md:flex-row md:items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Hello, TaxEase</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary" />
            AI-driven tax insights in a sleek workspace
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <button className="bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl font-medium shadow-sm shadow-primary/30 transition-smooth flex items-center gap-2 text-sm">
            <span>Generate Report</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <Briefcase className="w-16 h-16 text-primary" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center border border-slate-100">
              <Briefcase className="w-5 h-5 text-slate-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Salary Income</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              12,80,000
            </h2>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-emerald-600 bg-emerald-50 w-fit px-2.5 py-1 rounded-md">
            <TrendingUp className="w-4 h-4" />
            <span>+12% from last year</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <TrendingUp className="w-16 h-16 text-emerald-500" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center border border-emerald-100">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Tax Paid</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              1,24,800
            </h2>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-emerald-700">
            <span>Optimized deductions applied</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-smooth">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <ShieldCheck className="w-16 h-16 text-blue-500" />
          </div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center border border-blue-100">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Deductions</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-slate-900 flex items-center">
              <IndianRupee className="w-6 h-6 mr-1" />
              1,50,000
            </h2>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-blue-700">
            <ShieldCheck className="w-4 h-4" />
            <span>Maximized savings (80C full)</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Tax Breakdown</h3>
              <p className="text-sm text-slate-500 mt-1">Income vs Tax vs Deductions (Monthly)</p>
            </div>
            <select className="text-sm border-slate-200 rounded-lg text-slate-600 focus:ring-primary/20 cursor-pointer p-2 border outline-none">
              <option>FY 2023-24</option>
              <option>FY 2022-23</option>
            </select>
          </div>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" opacity={0.5} />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#64748b', fontSize: 12 }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#64748b', fontSize: 12 }} 
                />
                <Tooltip 
                  cursor={{ fill: '#f1f5f9' }}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="income" fill="#22C55E" radius={[4, 4, 0, 0]} barSize={12} />
                <Bar dataKey="tax" fill="#0F172A" radius={[4, 4, 0, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col">
          <div className="mb-6">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              AI Insights
            </h3>
            <p className="text-sm text-slate-500 mt-1">Recommended actions from TaxEase AI</p>
          </div>

          <div className="flex-1 flex flex-col gap-4">
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 flex gap-3 relative overflow-hidden">
              <div className="w-1.5 h-full bg-primary absolute left-0 top-0"></div>
              <div className="mt-0.5">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-primary-dark">Optimization Opportunity</h4>
                <p className="text-sm text-slate-600 mt-1 leading-snug">
                  Claim an extra <span className="font-semibold text-slate-900 px-1 bg-white rounded border border-slate-200">₹25,000</span> through HRA. Upload your rent receipts to map them correctly.
                </p>
                <button className="mt-3 text-xs font-semibold text-primary hover:text-primary-dark flex items-center transition-smooth">
                  Review HRA Mapping <ArrowUpRight className="w-3 h-3 ml-1" />
                </button>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-3">
              <div className="mt-0.5">
                <ShieldCheck className="w-5 h-5 text-slate-500" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-700">Section 80C Full</h4>
                <p className="text-sm text-slate-500 mt-1 leading-snug">
                  You have maxed out your ₹1.5L limit for 80C. No further ELSS investments will reduce your tax burden this year.
                </p>
              </div>
            </div>
            
             <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex gap-3">
              <div className="mt-0.5">
                <Leaf className="w-5 h-5 text-emerald-500" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-700">NPS Addition</h4>
                <p className="text-sm text-slate-500 mt-1 leading-snug">
                  Consider investing ₹50,000 in NPS (Tier-1) for an additional deduction under section 80CCD(1B).
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
