"use client";

import { ChevronDown } from "lucide-react";
import { Avatar } from "@/app/_components/ui/avatar";
import type { UserRole } from "@/app/lib/types";

const roles: { value: UserRole; label: string; color: string }[] = [
  { value: "client", label: "Client", color: "#d7896d" },
  { value: "seller", label: "Seller", color: "#39836e" },
  { value: "admin", label: "Admin", color: "#577ebd" },
];

interface RoleSwitcherProps {
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
}

export function RoleSwitcher({ role, onRoleChange }: RoleSwitcherProps) {
  const cycleRole = () => {
    const idx = roles.findIndex((r) => r.value === role);
    onRoleChange(roles[(idx + 1) % roles.length].value);
  };

  const current = roles.find((r) => r.value === role)!;

  return (
    <button
      onClick={cycleRole}
      className="flex w-full items-center gap-2.5 rounded-lg border border-[var(--line)] bg-white px-3 py-2.5 text-left transition-colors hover:bg-[#f4f8f4]"
      aria-label={`Current role: ${current.label}. Click to switch.`}
    >
      <Avatar initials="AM" size="sm" color={current.color} />
      <div className="flex flex-1 flex-col">
        <span className="text-xs font-bold text-[var(--ink)]">Amina M.</span>
        <span className="text-[11px] text-[var(--muted)]">{current.label}</span>
      </div>
      <ChevronDown size={14} className="text-[var(--muted)]" />
    </button>
  );
}
