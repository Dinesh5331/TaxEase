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
  CheckCircle2,
  User,
  Mail,
  Lock,
} from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const passwordStrength = password.length === 0
    ? null
    : password.length < 6
    ? "weak"
    : password.length < 10
    ? "fair"
    : "strong";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Signup failed");

      localStorage.setItem("taxease_user", JSON.stringify(data.user));
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex font-sans" style={{ background: "#F8FAFC" }}>
      {/* ── Left brand panel ── */}
      <div
        className="hidden lg:flex lg:w-[520px] xl:w-[600px] shrink-0 relative overflow-hidden flex-col items-center justify-center p-14"
        style={{ background: "linear-gradient(135deg, #16A34A 0%, #22C55E 50%, #4ADE80 100%)" }}
      >
        <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full opacity-20"
          style={{ background: "rgba(255,255,255,0.4)" }} />
        <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full opacity-10"
          style={{ background: "rgba(255,255,255,0.5)", transform: "translate(-30%, 30%)" }} />

        <div
          className="w-20 h-20 rounded-3xl flex items-center justify-center mb-8 shadow-xl"
          style={{ background: "rgba(255,255,255,0.25)", backdropFilter: "blur(10px)", border: "2px solid rgba(255,255,255,0.4)" }}
        >
          <Leaf className="w-11 h-11 text-white" />
        </div>

        <h1 className="text-5xl font-bold text-white mb-3 tracking-tight">
          Tax<span style={{ color: "rgba(255,255,255,0.75)" }}>Ease</span>
        </h1>
        <p className="text-green-50 text-center text-lg max-w-sm leading-relaxed mb-12">
          Join thousands of taxpayers who use TaxEase AI for smarter, faster tax filing.
        </p>

        <div className="space-y-3 w-full max-w-xs">
          {[
            "Free to use with your documents",
            "AI-powered ITR form selection",
            "Always grounded in official tax documents",
            "Bank-grade privacy, local processing",
          ].map((text) => (
            <div key={text} className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-200 shrink-0" />
              <span className="text-sm text-green-50">{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right form panel ── */}
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

          <h2 className="text-3xl font-bold text-slate-900 mb-2">Create your account</h2>
          <p className="text-slate-500 mb-8">Get started with TaxEase AI — it&apos;s free.</p>

          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm mb-6">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Arjun Sharma"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="arjun@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="w-full pl-10 pr-12 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-smooth"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {/* Strength indicator */}
              {passwordStrength && (
                <div className="flex gap-1.5 mt-2">
                  {(["weak", "fair", "strong"] as const).map((level, i) => {
                    const active = ["weak", "fair", "strong"].indexOf(passwordStrength) >= i;
                    const color = { weak: "#EF4444", fair: "#F59E0B", strong: "#22C55E" }[passwordStrength];
                    return (
                      <div
                        key={level}
                        className="h-1 flex-1 rounded-full transition-smooth"
                        style={{ background: active ? color : "#E2E8F0" }}
                      />
                    );
                  })}
                  <span className="text-xs text-slate-500 capitalize ml-1">{passwordStrength}</span>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary text-slate-800 bg-white transition-smooth text-sm"
                  required
                />
                {confirmPassword && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2">
                    {password === confirmPassword
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      : <AlertCircle className="w-4 h-4 text-red-400" />}
                  </span>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary hover:bg-primary-dark disabled:opacity-60 text-white py-3.5 rounded-xl font-semibold text-sm shadow-sm transition-smooth flex items-center justify-center gap-2 mt-2"
              style={{ boxShadow: "0 4px 14px rgba(34, 197, 94, 0.35)" }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-sm text-slate-500">
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-primary font-semibold hover:text-primary-dark transition-smooth"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
