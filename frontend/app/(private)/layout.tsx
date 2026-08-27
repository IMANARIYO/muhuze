"use client";

import { useState } from "react";
import { Sidebar } from "./_components/sidebar";
import { Topbar } from "./_components/topbar";
import type { UserRole } from "@/app/lib/types";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<UserRole>("client");
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[var(--paper)]">
      <Sidebar
        role={role}
        onRoleChange={setRole}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {mobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <section className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-10">{children}</main>
      </section>
    </div>
  );
}
