"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, CheckCircle2, Mail } from "lucide-react";
import { authService } from "@/app/services/auth.service";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await authService.forgotPassword(email);
      setSent(true);
    } catch (caught) {
      // Backend always returns 200 to avoid email enumeration — show success anyway
      setSent(true);
      void caught;
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f0f5ed] px-6 py-12">
      <div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-white p-8 shadow-xl">
        <Link href="/login" className="flex items-center gap-2 text-lg font-extrabold text-[var(--ink)]">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-sm text-[#d6f34d]">M</span>
          muhuze<span className="text-[var(--coral)]">.</span>
        </Link>

        <div className="mt-10">
          <p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Account recovery</p>
          <h1 className="mt-3 text-3xl font-black tracking-[-.04em]">Forgot password?</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
            Enter your email and we&apos;ll send you a reset link. The link expires in 30 minutes.
          </p>
        </div>

        {sent ? (
          <div className="mt-8 space-y-4">
            <div className="rounded-xl border border-[#bdded1] bg-[#e8f4ed] p-5 text-center">
              <CheckCircle2 className="mx-auto text-[var(--teal)]" size={28} />
              <p className="mt-3 font-bold text-[var(--ink)]">Check your inbox</p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                If an account exists for <strong>{email}</strong>, a reset link has been sent.
              </p>
            </div>
            <p className="text-center text-xs text-[var(--muted)]">
              Didn&apos;t receive it? Check your spam folder or{" "}
              <button onClick={() => setSent(false)} className="font-bold text-[var(--teal)] hover:underline">try again</button>.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <label className="block text-sm font-semibold">
              Email address
              <div className="relative mt-2">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="h-11 w-full rounded-lg border border-[var(--line)] pl-9 pr-3 outline-none focus:border-[var(--teal)]"
                />
              </div>
            </label>
            {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-3 py-2 text-sm text-[#b74d3b]">{error}</p>}
            <button
              disabled={loading}
              className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] text-sm font-bold text-white disabled:opacity-60"
            >
              {loading ? "Sending..." : "Send reset link"}
            </button>
          </form>
        )}

        <div className="mt-8 flex items-center justify-center">
          <Link href="/login" className="flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--ink)]">
            <ArrowLeft size={14} /> Back to sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
