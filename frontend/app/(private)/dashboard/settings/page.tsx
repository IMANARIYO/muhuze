"use client";

import { useState } from "react";
import { CheckCircle2, Lock, Mail, Shield } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { useAuth } from "@/app/context/auth-context";
import { authService } from "@/app/services/auth.service";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();

  // Email verification
  const [verifyStep, setVerifyStep] = useState<"idle" | "sent" | "done">("idle");
  const [otpCode, setOtpCode] = useState("");
  const [verifyError, setVerifyError] = useState("");
  const [verifyLoading, setVerifyLoading] = useState(false);

  // Password reset (via forgot flow — sends email)
  const [pwStep, setPwStep] = useState<"idle" | "sent">("idle");
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState("");

  async function requestVerification() {
    setVerifyLoading(true);
    setVerifyError("");
    try {
      await authService.requestEmailVerification();
      setVerifyStep("sent");
    } catch (caught) {
      setVerifyError(caught instanceof Error ? caught.message : "Could not send verification email.");
    } finally {
      setVerifyLoading(false);
    }
  }

  async function confirmVerification(e: React.FormEvent) {
    e.preventDefault();
    setVerifyLoading(true);
    setVerifyError("");
    try {
      await authService.confirmEmailVerification(otpCode);
      setVerifyStep("done");
      await refreshUser();
    } catch (caught) {
      setVerifyError(caught instanceof Error ? caught.message : "Invalid or expired code.");
    } finally {
      setVerifyLoading(false);
    }
  }

  async function sendPasswordReset() {
    if (!user?.email) return;
    setPwLoading(true);
    setPwError("");
    try {
      await authService.forgotPassword(user.email);
      setPwStep("sent");
    } catch (caught) {
      setPwError(caught instanceof Error ? caught.message : "Could not send reset email.");
    } finally {
      setPwLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Account</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Settings</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Manage your account security and verification.</p>
      </div>

      {/* Email verification */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e4edfa] text-[#577ebd]"><Mail size={16} /></div>
          <div>
            <h2 className="font-bold">Email verification</h2>
            <p className="text-xs text-[var(--muted)]">Verify your email address to unlock full platform features.</p>
          </div>
          {user?.is_verified && (
            <span className="ml-auto flex items-center gap-1 rounded-full bg-[#e8f4ed] px-3 py-1 text-[11px] font-bold text-[#2d7a5e]">
              <CheckCircle2 size={12} /> Verified
            </span>
          )}
        </div>

        {user?.is_verified ? (
          <p className="text-sm text-[var(--muted)]">Your email <strong>{user.email}</strong> is verified.</p>
        ) : verifyStep === "done" ? (
          <div className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2">
            <CheckCircle2 size={15} /> Email verified successfully!
          </div>
        ) : verifyStep === "sent" ? (
          <form onSubmit={confirmVerification} className="space-y-3">
            <p className="text-sm text-[var(--muted)]">A 6-digit code was sent to <strong>{user?.email}</strong>. Enter it below.</p>
            {verifyError && <p className="text-xs text-[#b74d3b]">{verifyError}</p>}
            <div className="flex gap-2">
              <Input
                required
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="Enter 6-digit code"
                maxLength={6}
                className="max-w-[180px]"
              />
              <Button type="submit" disabled={verifyLoading || otpCode.length < 4}>
                {verifyLoading ? "Verifying..." : "Confirm"}
              </Button>
              <Button type="button" variant="outline" onClick={() => setVerifyStep("idle")}>Cancel</Button>
            </div>
          </form>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--muted)]">Your email <strong>{user?.email}</strong> is not yet verified.</p>
            {verifyError && <p className="text-xs text-[#b74d3b]">{verifyError}</p>}
            <Button onClick={requestVerification} disabled={verifyLoading}>
              {verifyLoading ? "Sending..." : "Send verification email"}
            </Button>
          </div>
        )}
      </div>

      {/* Password */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#fbf0ce] text-[#b58a24]"><Lock size={16} /></div>
          <div>
            <h2 className="font-bold">Password</h2>
            <p className="text-xs text-[var(--muted)]">Change your password via a secure email reset link.</p>
          </div>
        </div>

        {pwStep === "sent" ? (
          <div className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2">
            <CheckCircle2 size={15} /> Reset link sent to <strong>{user?.email}</strong>. Check your inbox.
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--muted)]">
              We&apos;ll send a password reset link to <strong>{user?.email}</strong>. All active sessions will be revoked when you reset.
            </p>
            {pwError && <p className="text-xs text-[#b74d3b]">{pwError}</p>}
            <Button variant="outline" onClick={sendPasswordReset} disabled={pwLoading}>
              {pwLoading ? "Sending..." : "Send password reset email"}
            </Button>
          </div>
        )}
      </div>

      {/* Roles & permissions (read-only for self) */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]"><Shield size={16} /></div>
          <div>
            <h2 className="font-bold">My roles & permissions</h2>
            <p className="text-xs text-[var(--muted)]">Your current access level on the platform.</p>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-bold text-[var(--muted)] mb-2">Roles</p>
            <div className="flex flex-wrap gap-2">
              {(user?.roles ?? []).map((r) => (
                <span key={r} className="rounded-full bg-[#e8f4ed] px-3 py-1 text-[11px] font-bold text-[#2d7a5e] capitalize">{r}</span>
              ))}
              {(user?.roles ?? []).length === 0 && <p className="text-xs text-[var(--muted)]">No roles assigned.</p>}
            </div>
          </div>
          <div>
            <p className="text-xs font-bold text-[var(--muted)] mb-2">Permissions</p>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {(user?.permissions ?? []).map((p) => (
                <span key={p} className="rounded-full border border-[var(--line)] bg-[#f9fbf9] px-3 py-1 text-[10px] font-mono text-[var(--muted)]">{p}</span>
              ))}
              {(user?.permissions ?? []).length === 0 && <p className="text-xs text-[var(--muted)]">No permissions.</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder sections */}
      <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-6 text-center">
        <p className="text-sm font-bold text-[var(--muted)]">Notifications, payment methods, and appearance settings</p>
        <p className="mt-1 text-xs text-[var(--muted)]">Coming soon — these require backend modules not yet mounted.</p>
      </div>
    </div>
  );
}
