"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileUp, FileSpreadsheet, Bot, Leaf } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Upload Form 16", href: "/upload", icon: FileUp },
  { name: "ITR Mapping", href: "/mapping", icon: FileSpreadsheet },
  { name: "AI Assistant", href: "/assistant", icon: Bot },
];

export default function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex flex-col bg-sidebar border-r border-sidebar-border h-full max-h-screen py-6 px-4 shadow-sm",
        className
      )}
    >
      <div className="flex items-center gap-3 px-3 mb-10">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-md shadow-primary/20">
          <Leaf className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight text-slate-800">
          Tax<span className="text-primary">Ease</span>
        </span>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-smooth group",
                isActive
                  ? "bg-primary-light text-primary-dark"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon
                className={cn(
                  "w-5 h-5 transition-smooth",
                  isActive ? "text-primary" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-3">
        <div className="bg-primary/5 rounded-xl p-4 border border-primary/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none">
            <Bot className="w-12 h-12 text-primary" />
          </div>
          <p className="text-xs font-semibold text-primary-dark mb-1">TaxEase AI</p>
          <p className="text-xs text-slate-500 mb-3">Upgrade to Pro for deeper insights.</p>
          <button className="w-full bg-white text-primary border border-primary/20 rounded-lg py-1.5 text-xs font-medium hover:bg-primary-light transition-smooth">
            Upgrade Plan
          </button>
        </div>
      </div>
    </aside>
  );
}
