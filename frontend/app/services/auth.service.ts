import { api, clearTokens, getAccessToken, getApiErrorMessage, getRefreshToken, saveRole, saveTokens } from "@/app/lib/api/client";
import type { ApiResponse } from "@/app/lib/api/client";
import type { Account, AuthUser, Authorization, LoginInput, RegisterInput, TokenPair } from "@/app/lib/auth/types";

function roleForUser(roles: string[]): AuthUser["role"] {
  if (roles.includes("admin")) return "admin";
  if (roles.includes("seller")) return "seller";
  return "client";
}

async function getUserWithAuthorization(account: Account): Promise<AuthUser> {
  const { data } = await api.get<ApiResponse<Authorization>>("/auth/me/authorization");
  const authorization = data.data ?? { roles: [], permissions: [] };
  const role = roleForUser(authorization.roles);
  saveRole(role);
  return { ...account, ...authorization, role };
}

function accountFromToken(email: string): Account {
  const token = getAccessToken();
  const subject = token?.split(".")[1];
  let id = "unknown";

  if (subject) {
    try {
      const payload = JSON.parse(atob(subject.replace(/-/g, "+").replace(/_/g, "/"))) as { sub?: string };
      id = payload.sub ?? id;
    } catch {
      id = "unknown";
    }
  }

  return { id, email, phone: null, is_active: true, is_verified: false, created_at: "" };
}

export const authService = {
  async register(input: RegisterInput): Promise<Account> {
    const { data } = await api.post<ApiResponse<Account>>("/auth/register", input);
    if (!data.data) throw new Error(data.message || "Registration failed.");
    return data.data;
  },

  async login(input: LoginInput): Promise<AuthUser> {
    const { data } = await api.post<ApiResponse<TokenPair>>("/auth/login", input);
    if (!data.data) throw new Error(data.message || "Login failed.");
    saveTokens(data.data.access_token, data.data.refresh_token);
    window.localStorage.setItem("muhuze.accountEmail", input.email);
    return getUserWithAuthorization(accountFromToken(input.email));
  },

  async registerAndLogin(input: RegisterInput): Promise<AuthUser> {
    await this.register(input);
    return this.login({ email: input.email, password: input.password });
  },

  async restore(): Promise<AuthUser | null> {
    if (!getRefreshToken()) return null;
    try {
      const authorizationResponse = await api.get<ApiResponse<Authorization>>("/auth/me/authorization");
      if (!authorizationResponse.data.data) return null;
      const email = window.localStorage.getItem("muhuze.accountEmail") ?? "";
      return getUserWithAuthorization(accountFromToken(email));
    } catch {
      clearTokens();
      return null;
    }
  },

  async logout(): Promise<void> {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) await api.post("/auth/logout", { refresh_token: refreshToken });
    } finally {
      clearTokens();
      window.localStorage.removeItem("muhuze.accountEmail");
    }
  },

  errorMessage(error: unknown, fallback: string): string {
    return getApiErrorMessage(error, fallback);
  },
};
