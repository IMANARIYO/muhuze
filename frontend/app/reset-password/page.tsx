"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ArrowRight, CheckCircle2, Eye, EyeOff } from "lucide-react";
import { authService } from "@/app/services/auth.service";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setLoading(true);
    setError("");
    try {
      await authService.resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.replace("/login"), 3000);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Reset failed. The link may have expired.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <p className="text-sm text-[#b74d3b]">Invalid reset link. No token found.</p>
        <Link href="/forgot-password" className="text-sm font-bold text-[var(--teal)] hover:underline">Request a new link</Link>
      </div>
    );
  }

  return done ? (
    <div className="mt-8 space-y-4">
      <div className="rounded-xl border border-[#bdded1] bg-[#e8f4ed] p-5 text-center">
        <CheckCircle2 className="mx-auto text-[var(--teal)]" size={28} />
        <p className="mt-3 font-bold text-[var(--ink)]">Password reset!</p>
        <p className="mt-2 text-sm text-[var(--muted)]">All sessions have been revoked. Redirecting to sign in...</p>
      </div>
    </div>
  ) : (
    <form onSubmit={handleSubmit} className="mt-8 space-y-5">
      <label className="block text-sm font-semibold">
        New password
        <div className="relative mt-2">
          <input
            required
            type={showPw ? "text" : "password"}
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            className="h-11 w-full rounded-lg border border-[var(--line)] px-3 pr-10 outline-none focus:border-[var(--teal)]"
          />
          <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]">
            {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        </div>
      </label>
      <label className="block text-sm font-semibold">
        Confirm password
        <input
          required
          type={showPw ? "text" : "password"}
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Repeat your new password"
          className="mt-2 h-11 w-full rounded-lg border border-[var(--line)] px-3 outline-none focus:border-[var(--teal)]"
        />
      </label>
      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-3 py-2 text-sm text-[#b74d3b]">{error}</p>}
      <button
        disabled={loading}
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] text-sm font-bold text-white disabled:opacity-60"
      >
        {loading ? "Resetting..." : "Set new password"} <ArrowRight size={16} />
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f0f5ed] px-6 py-12">
      <div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-white p-8 shadow-xl">
        <Link href="/login" className="flex items-center gap-2 text-lg font-extrabold text-[var(--ink)]">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-sm text-[#d6f34d]">M</span>
          muhuze<span className="text-[var(--coral)]">.</span>
        </Link>
        <div className="mt-10">
          <p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Account recovery</p>
          <h1 className="mt-3 text-3xl font-black tracking-[-.04em]">Set new password</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">Choose a strong password. All active sessions will be signed out.</p>
        </div>
        <Suspense fallback={<div className="mt-8 text-sm text-[var(--muted)]">Loading...</div>}>
          <ResetPasswordForm />
        </Suspense>
        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm text-[var(--muted)] hover:text-[var(--ink)]">Back to sign in</Link>
        </div>
      </div>
    </main>
  );
}
