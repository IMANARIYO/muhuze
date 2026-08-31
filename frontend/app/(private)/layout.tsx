"use client";

import { useState } from "react";
import { Sidebar } from "./_components/sidebar";
import { Topbar } from "./_components/topbar";
import type { UserRole } from "@/app/lib/types";
import { useAuth } from "@/app/context/auth-context";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  // Default to the highest role the user actually has; falls back to client
  const defaultRole = (): UserRole => {
    if (user?.roles.includes("admin")) return "admin";
    if (user?.roles.includes("seller")) return "seller";
    return "client";
  };
  const [role, setRole] = useState<UserRole>(defaultRole);
  const [mobileOpen, setMobileOpen] = useState(false);

  const activeRole = user?.roles.includes(role === "client" ? "buyer" : role)
    ? role
    : user?.role ?? "client";

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-[var(--paper)]">
      <Sidebar
        role={activeRole}
        onRoleChange={(nextRole) => {
          if (user?.roles.includes(nextRole === "client" ? "buyer" : nextRole)) {
            setRole(nextRole);
          }
        }}
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
