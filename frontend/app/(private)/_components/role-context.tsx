"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { UserRole } from "@/app/lib/types";
import { useAuth } from "@/app/context/auth-context";

const STORAGE_KEY = "muhuze.selectedRole";

function defaultRole(roles: string[]): UserRole {
  if (roles.includes("admin")) return "admin";
  if (roles.includes("seller")) return "seller";
  return "client";
}

function hasRole(roles: string[], role: UserRole): boolean {
  return roles.includes(role === "client" ? "buyer" : role);
}

/** Read the persisted role preference (may be null / already stale). */
function readStoredRole(): UserRole | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(STORAGE_KEY) as UserRole | null;
  return value === "client" || value === "seller" || value === "admin" ? value : null;
}

interface RoleContextValue {
  /** The role currently selected in the sidebar role-switcher (the one driving nav + page views). */
  role: UserRole;
  /** Switch the active role. Only allowed if the user actually has that role. Persisted across refreshes. */
  setRole: (role: UserRole) => void;
}

const RoleContext = createContext<RoleContextValue | undefined>(undefined);

export function RoleProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  // The user's explicit role choice, persisted so a refresh keeps it.
  const [override, setOverride] = useState<UserRole | null>(readStoredRole);

  // The effective role is derived on every render. Until the session has loaded the user
  // is null and we fall back to the highest *available* role — but we only ever expose a
  // role the user actually has, so a seller/admin never flashes the "client" view.
  const role: UserRole =
    user && override && hasRole(user.roles, override)
      ? override
      : defaultRole(user?.roles ?? []);

  const setRole = (next: UserRole) => {
    if (!user || !hasRole(user.roles, next)) return;
    setOverride(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  };

  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export function useRole(): RoleContextValue {
  const context = useContext(RoleContext);
  if (!context) throw new Error("useRole must be used inside RoleProvider");
  return context;
}
