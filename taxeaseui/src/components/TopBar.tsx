"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, LogOut, User } from "lucide-react";

type UserInfo = { name: string; email: string; id: number };

export default function TopBar() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("taxease_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {}
  }, []);

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    localStorage.removeItem("taxease_user");
    router.push("/login");
    router.refresh();
  };

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

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

      {/* User avatar + dropdown */}
      <div className="relative ml-4">
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className="flex items-center gap-2.5 hover:bg-slate-50 rounded-xl px-3 py-2 transition-smooth"
        >
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold shadow-sm">
            {initials}
          </div>
          {user && (
            <div className="hidden md:block text-left">
              <p className="text-sm font-semibold text-slate-800 leading-tight">{user.name}</p>
              <p className="text-xs text-slate-400 leading-tight">{user.email}</p>
            </div>
          )}
        </button>

        {showUserMenu && (
          <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl border border-slate-100 shadow-lg overflow-hidden z-50">
            {user && (
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">{user.name}</p>
                <p className="text-xs text-slate-500 truncate">{user.email}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-smooth"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        )}
      </div>

      {/* Close dropdown on outside click */}
      {showUserMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </header>
  );
}
