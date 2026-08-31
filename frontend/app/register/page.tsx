"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/app/context/auth-context";
import { authService } from "@/app/services/auth.service";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [form, setForm] = useState({ email: "", phone: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await register(form);
      router.replace("/dashboard");
    } catch (caught) {
      setError(authService.errorMessage(caught, "Unable to create your account."));
    } finally {
      setSubmitting(false);
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-[#f0f5ed] px-6 py-12"><div className="w-full max-w-md rounded-2xl border border-[var(--line)] bg-white p-8 shadow-xl"><Link href="/" className="flex items-center gap-2 text-lg font-extrabold text-[var(--ink)]"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-sm text-[#d6f34d]">M</span> muhuze<span className="text-[var(--coral)]">.</span></Link><div className="mt-10"><p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Join the network</p><h1 className="mt-3 text-3xl font-black tracking-[-.04em]">Create your account</h1><p className="mt-3 text-sm leading-6 text-[var(--muted)]">Start as a client. Seller access can be added through the platform.</p></div><form onSubmit={handleSubmit} className="mt-8 space-y-5"><label className="block text-sm font-semibold">Email<input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} className="mt-2 h-11 w-full rounded-lg border border-[var(--line)] px-3 outline-none focus:border-[var(--teal)]" /></label><label className="block text-sm font-semibold">Phone <span className="font-normal text-[var(--muted)]">(optional)</span><input type="tel" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className="mt-2 h-11 w-full rounded-lg border border-[var(--line)] px-3 outline-none focus:border-[var(--teal)]" /></label><label className="block text-sm font-semibold">Password<input required minLength={8} type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="mt-2 h-11 w-full rounded-lg border border-[var(--line)] px-3 outline-none focus:border-[var(--teal)]" /></label>{error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-3 py-2 text-sm text-[#b74d3b]">{error}</p>}<button disabled={submitting} className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] text-sm font-bold text-white disabled:opacity-60">{submitting ? "Creating account..." : "Create account"} <ArrowRight size={16} /></button></form><p className="mt-7 text-center text-sm text-[var(--muted)]">Already have an account? <Link href="/login" className="font-bold text-[#39836e]">Sign in</Link></p></div></main>;
}
