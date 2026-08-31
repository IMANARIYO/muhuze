"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Mail, Shield, User } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { Avatar } from "@/app/_components/ui/avatar";
import { useAuth } from "@/app/context/auth-context";
import { userService, type ProfileRecord } from "@/app/services/auth.service";

function getInitials(email: string): string {
  const parts = email.split("@")[0].split(/[._-]/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return email.slice(0, 2).toUpperCase();
}

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileRecord | null>(null);
  const [form, setForm] = useState({ first_name: "", last_name: "", date_of_birth: "" });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    userService.getProfile()
      .then((p) => {
        setProfile(p);
        setForm({
          first_name: p.first_name ?? "",
          last_name: p.last_name ?? "",
          date_of_birth: p.date_of_birth ?? "",
        });
      })
      .catch(() => {
        // No profile yet — form stays empty, upsert will create it
      });
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const updated = await userService.upsertProfile({
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        date_of_birth: form.date_of_birth || undefined,
      });
      setProfile(updated);
      setSuccess("Profile saved.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Profile could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const initials = user?.email ? getInitials(user.email) : "?";
  const displayName = profile?.first_name
    ? `${profile.first_name}${profile.last_name ? " " + profile.last_name : ""}`
    : user?.email?.split("@")[0] ?? "Account";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Account</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">My profile</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Your personal information and account details.</p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {success && <p className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2"><CheckCircle2 size={14} /> {success}</p>}

      {/* Account identity card */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-5">
          <Avatar initials={initials} size="lg" />
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-bold text-[var(--ink)] truncate">{displayName}</h2>
            <p className="flex items-center gap-1.5 text-xs text-[var(--muted)] mt-1">
              <Mail size={12} /> {user?.email}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {user?.roles.map((r) => (
                <span key={r} className="flex items-center gap-1 rounded-full bg-[#e8f4ed] px-2.5 py-0.5 text-[10px] font-bold text-[#2d7a5e] capitalize">
                  <Shield size={10} /> {r}
                </span>
              ))}
              {user?.is_verified && (
                <span className="flex items-center gap-1 rounded-full bg-[#e4edfa] px-2.5 py-0.5 text-[10px] font-bold text-[#577ebd]">
                  <CheckCircle2 size={10} /> Verified
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Personal info form */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]"><User size={16} /></div>
          <h2 className="font-bold">Personal information</h2>
        </div>
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-semibold">
              First name
              <Input
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                placeholder="e.g. Amina"
                className="mt-2"
              />
            </label>
            <label className="block text-sm font-semibold">
              Last name
              <Input
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                placeholder="e.g. Mugisha"
                className="mt-2"
              />
            </label>
          </div>
          <label className="block text-sm font-semibold">
            Date of birth
            <Input
              type="date"
              value={form.date_of_birth}
              onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
              className="mt-2"
            />
          </label>
          <div className="rounded-lg bg-[#f9fbf9] border border-[var(--line)] px-4 py-3 text-xs text-[var(--muted)]">
            Email and phone are part of your login identity and cannot be changed here.
          </div>
          <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save profile"}</Button>
        </form>
      </div>

      {/* Account info (read-only) */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <h2 className="font-bold mb-4">Account details</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Email</span>
            <span className="font-semibold">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Account ID</span>
            <span className="font-mono text-xs text-[var(--muted)]">{user?.id?.slice(0, 16)}…</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Email verified</span>
            <span className={user?.is_verified ? "text-[#2d7a5e] font-bold" : "text-[#b58a24] font-bold"}>
              {user?.is_verified ? "Yes" : "No — verify in Settings"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Member since</span>
            <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) : "—"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
