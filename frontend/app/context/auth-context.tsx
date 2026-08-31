"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authService } from "@/app/services/auth.service";
import type { AuthUser, LoginInput, RegisterInput } from "@/app/lib/auth/types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (input: LoginInput) => Promise<AuthUser>;
  register: (input: RegisterInput) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authService.restore().then(setUser).finally(() => setLoading(false));
  }, []);

  async function login(input: LoginInput) {
    const nextUser = await authService.login(input);
    setUser(nextUser);
    return nextUser;
  }

  async function register(input: RegisterInput) {
    const nextUser = await authService.registerAndLogin(input);
    setUser(nextUser);
    return nextUser;
  }

  async function logout() {
    await authService.logout();
    setUser(null);
  }

  async function refreshUser() {
    const restored = await authService.restore();
    setUser(restored);
  }

  const value: AuthContextValue = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
    refreshUser,
    hasRole: (...roles) => Boolean(user && roles.some((role) => user.roles.includes(role))),
    hasPermission: (permission) => Boolean(user?.permissions.includes(permission)),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
