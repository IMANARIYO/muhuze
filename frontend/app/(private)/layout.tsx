"use client";

import { useState } from "react";
import { Sidebar } from "./_components/sidebar";
import { Topbar } from "./_components/topbar";
import { RoleProvider, useRole } from "./_components/role-context";
import { useAuth } from "@/app/context/auth-context";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const { role, setRole } = useRole();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Wait for the session to restore before painting the shell, otherwise the sidebar
  // would briefly show the "client" default and then switch — the visual "shaking".
  if (loading || !user) {
    return (
      <div className="grid min-h-screen place-items-center bg-[var(--paper)]">
        <div className="flex flex-col items-center gap-3">
          <div className="grid h-10 w-10 animate-pulse place-items-center rounded-xl bg-[var(--ink)] text-sm font-extrabold text-[#d6f34d] -rotate-6">
            M
          </div>
          <p className="text-xs text-[var(--muted)]">Loading your workspace…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-[var(--paper)]">
      <Sidebar
        role={role}
        onRoleChange={setRole}
        availableRoles={user?.roles ?? []}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {mobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="shrink-0">
          <Topbar onMenuClick={() => setMobileOpen(true)} />
        </div>
        <main className="min-h-0 flex-1 overflow-y-auto p-6 lg:p-10">{children}</main>
      </section>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleProvider>
      <DashboardShell>{children}</DashboardShell>
    </RoleProvider>
  );
}
