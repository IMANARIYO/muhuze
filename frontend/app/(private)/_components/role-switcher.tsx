"use client";

import { ChevronDown } from "lucide-react";
import { Avatar } from "@/app/_components/ui/avatar";
import { useAuth } from "@/app/context/auth-context";
import type { UserRole } from "@/app/lib/types";

const roles: { value: UserRole; label: string; color: string }[] = [
  { value: "client", label: "Client", color: "#d7896d" },
  { value: "seller", label: "Seller", color: "#39836e" },
  { value: "admin", label: "Admin", color: "#577ebd" },
];

interface RoleSwitcherProps {
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
  availableRoles: string[];
}

function getInitials(email: string): string {
  const parts = email.split("@")[0].split(/[._-]/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return email.slice(0, 2).toUpperCase();
}

export function RoleSwitcher({ role, onRoleChange, availableRoles }: RoleSwitcherProps) {
  const { user } = useAuth();
  const allowedRoles = roles.filter((r) =>
    availableRoles.includes(r.value === "client" ? "buyer" : r.value)
  );

  const cycleRole = () => {
    if (allowedRoles.length < 2) return;
    const idx = allowedRoles.findIndex((r) => r.value === role);
    onRoleChange(allowedRoles[(idx + 1) % allowedRoles.length].value);
  };

  const current = roles.find((r) => r.value === role) ?? roles[0];
  const initials = user?.email ? getInitials(user.email) : "?";
  const displayName = user?.email?.split("@")[0] ?? "Account";

  return (
    <button
      onClick={cycleRole}
      className="flex w-full items-center gap-2.5 rounded-lg border border-[var(--line)] bg-white px-3 py-2.5 text-left transition-colors hover:bg-[#f4f8f4]"
      aria-label={allowedRoles.length > 1 ? `Current role: ${current.label}. Click to switch.` : `Current role: ${current.label}.`}
    >
      <Avatar initials={initials} size="sm" color={current.color} />
      <div className="flex flex-1 flex-col min-w-0">
        <span className="truncate text-xs font-bold text-[var(--ink)]">{displayName}</span>
        <span className="text-[11px] text-[var(--muted)]">{current.label}</span>
      </div>
      {allowedRoles.length > 1 && <ChevronDown size={14} className="shrink-0 text-[var(--muted)]" />}
    </button>
  );
}
