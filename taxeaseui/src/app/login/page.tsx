"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Leaf,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  ShieldCheck,
  TrendingUp,
  Bot,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Login failed");

      localStorage.setItem("taxease_user", JSON.stringify(data.user));
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex font-sans" style={{ background: "#F8FAFC" }}>
      {/* ── Left panel ── */}
      <div className="hidden lg:flex lg:w-[520px] xl:w-[600px] shrink-0 relative overflow-hidden flex-col items-center justify-center p-14"
        style={{ background: "linear-gradient(135deg, #16A34A 0%, #22C55E 50%, #4ADE80 100%)" }}
      >
        {/* Decorative blobs */}
        <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full opacity-20"
          style={{ background: "rgba(255,255,255,0.4)" }} />
        <div className="absolute bottom-0 right-0 w-80 h-80 rounded-full opacity-10"
          style={{ background: "rgba(255,255,255,0.5)", transform: "translate(30%, 30%)" }} />
        <div className="absolute top-1/2 left-8 w-32 h-32 rounded-full opacity-10"
          style={{ background: "rgba(255,255,255,0.6)" }} />

        {/* Brand logo */}
        <div className="w-20 h-20 rounded-3xl flex items-center justify-center mb-8 shadow-xl"
          style={{ background: "rgba(255,255,255,0.25)", backdropFilter: "blur(10px)", border: "2px solid rgba(255,255,255,0.4)" }}
        >
          <Leaf className="w-11 h-11 text-white" />
        </div>

        <h1 className="text-5xl font-bold text-white mb-3 tracking-tight">
          Tax<span style={{ color: "rgba(255,255,255,0.75)" }}>Ease</span>
        </h1>
        <p className="text-green-50 text-center text-lg max-w-sm leading-relaxed mb-12">
          Your AI-powered Indian income tax assistant — smart, accurate, and always up-to-date.
        </p>

        {/* Feature pills */}
        <div className="space-y-3 w-full max-w-xs">
          {[
            { icon: Bot, text: "RAG-powered tax Q&A on real ITR docs" },
            { icon: ShieldCheck, text: "Secure Form 16 OCR extraction" },
            { icon: TrendingUp, text: "Smart ITR form recommendations" },
          ].map(({ icon: Icon, text }) => (
            <div key={text}
              className="flex items-center gap-3 px-4 py-3 rounded-xl"
              style={{ background: "rgba(255,255,255,0.15)", backdropFilter: "blur(8px)", border: "1px solid rgba(255,255,255,0.2)" }}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: "rgba(255,255,255,0.25)" }}>
                <Icon className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-green-50 font-medium">{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-10 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Leaf className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-800">
              Tax<span className="text-primary">Ease</span>
            </span>
          </div>

          <h2 className="text-3xl font-bold text-slate-900 mb-2">Welcome back</h2>
          <p className="text-slate-500 mb-8">Sign in to your TaxEase account to continue.</p>

          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm mb-6">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm pr-12"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-smooth"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary hover:bg-primary-dark disabled:opacity-60 text-white py-3.5 rounded-xl font-semibold text-sm shadow-sm transition-smooth flex items-center justify-center gap-2"
              style={{ boxShadow: "0 4px 14px rgba(34, 197, 94, 0.35)" }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-sm text-slate-500">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="text-primary font-semibold hover:text-primary-dark transition-smooth"
              >
                Create one free
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
