"use client";

import { Search } from "lucide-react";

export default function TopBar() {
  return (
    <header className="h-16 px-6 border-b border-border bg-white flex items-center justify-between shadow-sm z-10 sticky top-0 shrink-0">
      <div className="flex-1 flex items-center gap-4">
        <div className="relative w-full max-w-md hidden md:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-xl leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary sm:text-sm transition-smooth"
            placeholder="Search anything (e.g. deductions, sections)..."
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
            <kbd className="hidden sm:inline-block border border-slate-200 rounded px-2 text-xs font-sans font-medium text-slate-400 bg-white shadow-sm">
              ⌘K
            </kbd>
          </div>
        </div>
      </div>


    </header>
  );
}
