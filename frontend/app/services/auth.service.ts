import { api, clearTokens, getAccessToken, getApiErrorMessage, getRefreshToken, saveRole, saveTokens } from "@/app/lib/api/client";
import type { ApiResponse } from "@/app/lib/api/client";
import type { Account, AuthUser, Authorization, LoginInput, RegisterInput, TokenPair } from "@/app/lib/auth/types";

// ── Types ──────────────────────────────────────────────────────────────────

export interface RoleRecord {
  id: string;
  name: string;
  description: string | null;
}

export interface PermissionRecord {
  id: string;
  code: string;
  name: string;
  description: string | null;
  resource: string;
  action: string;
}

export interface AccountRecord {
  id: string;
  email: string;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  roles: string[];
}

export interface ProfileRecord {
  account_id: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  created_at: string;
  updated_at: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

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

async function unwrap<T>(req: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await req;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

// ── Auth service ───────────────────────────────────────────────────────────

export const authService = {
  // ── Core auth ──
  async register(input: RegisterInput): Promise<Account> {
    return unwrap(api.post<ApiResponse<Account>>("/auth/register", input), "Registration failed.");
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
      const authorization = authorizationResponse.data.data;
      const role = roleForUser(authorization.roles);
      saveRole(role);
      // Build account from token — is_verified will be refreshed on next full restore
      const email = window.localStorage.getItem("muhuze.accountEmail") ?? "";
      const account = accountFromToken(email);
      return { ...account, ...authorization, role };
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

  // ── Email verification ──
  async requestEmailVerification(): Promise<void> {
    await api.post("/auth/email/verification/request");
  },

  async confirmEmailVerification(code: string): Promise<void> {
    await api.post("/auth/email/verification/confirm", { code });
  },

  // ── Password reset ──
  async forgotPassword(email: string): Promise<void> {
    await api.post("/auth/password/forgot", { email });
  },

  async resetPassword(token: string, new_password: string): Promise<void> {
    await api.post("/auth/password/reset", { token, new_password });
  },

  // ── My authorization ──
  async getMyAuthorization(): Promise<Authorization> {
    return unwrap(api.get<ApiResponse<Authorization>>("/auth/me/authorization"), "Authorization could not be loaded.");
  },

  async getMyRoles(): Promise<string[]> {
    return unwrap(api.get<ApiResponse<string[]>>("/auth/me/roles"), "Roles could not be loaded.");
  },

  async getMyPermissions(): Promise<string[]> {
    return unwrap(api.get<ApiResponse<string[]>>("/auth/me/permissions"), "Permissions could not be loaded.");
  },

  // ── Roles (admin) ──
  async listRoles(): Promise<RoleRecord[]> {
    return unwrap(api.get<ApiResponse<RoleRecord[]>>("/auth/roles"), "Roles could not be loaded.");
  },

  async createRole(name: string, description?: string): Promise<RoleRecord> {
    return unwrap(api.post<ApiResponse<RoleRecord>>("/auth/roles", { name, description }), "Role could not be created.");
  },

  async updateRole(roleName: string, changes: { name: string; description?: string | null }): Promise<RoleRecord> {
    return unwrap(api.patch<ApiResponse<RoleRecord>>(`/auth/roles/${roleName}`, changes), "Role could not be updated.");
  },

  async deleteRole(roleName: string): Promise<void> {
    await api.delete(`/auth/roles/${roleName}`);
  },

  // ── Permissions (admin) ──
  async listPermissions(): Promise<PermissionRecord[]> {
    return unwrap(api.get<ApiResponse<PermissionRecord[]>>("/auth/permissions"), "Permissions could not be loaded.");
  },

  async createPermission(input: { code: string; name: string; resource: string; action: string; description?: string }): Promise<PermissionRecord> {
    return unwrap(api.post<ApiResponse<PermissionRecord>>("/auth/permissions", input), "Permission could not be created.");
  },

  async updatePermission(code: string, changes: { name: string; description?: string | null; resource: string; action: string }): Promise<PermissionRecord> {
    return unwrap(api.patch<ApiResponse<PermissionRecord>>(`/auth/permissions/${code}`, changes), "Permission could not be updated.");
  },

  async deletePermission(code: string): Promise<void> {
    await api.delete(`/auth/permissions/${code}`);
  },

  // ── Accounts directory (admin) ──
  async listAccounts(): Promise<AccountRecord[]> {
    return unwrap(api.get<ApiResponse<AccountRecord[]>>("/auth/accounts"), "Accounts could not be loaded.");
  },

  // ── Account roles (admin) ──
  async listAccountRoles(accountId: string): Promise<RoleRecord[]> {
    return unwrap(api.get<ApiResponse<RoleRecord[]>>(`/auth/accounts/${accountId}/roles`), "Account roles could not be loaded.");
  },

  async assignRoleToAccount(accountId: string, roleName: string): Promise<void> {
    await api.post(`/auth/accounts/${accountId}/roles`, { role_name: roleName });
  },

  async revokeRoleFromAccount(accountId: string, roleName: string): Promise<void> {
    await api.delete(`/auth/accounts/${accountId}/roles/${roleName}`);
  },

  // ── Role permissions (admin) ──
  async listRolePermissions(roleName: string): Promise<PermissionRecord[]> {
    return unwrap(api.get<ApiResponse<PermissionRecord[]>>(`/auth/roles/${roleName}/permissions`), "Role permissions could not be loaded.");
  },

  async assignPermissionToRole(roleName: string, permissionCode: string): Promise<void> {
    await api.post(`/auth/roles/${roleName}/permissions`, { permission_code: permissionCode });
  },

  async revokePermissionFromRole(roleName: string, permissionCode: string): Promise<void> {
    await api.delete(`/auth/roles/${roleName}/permissions/${permissionCode}`);
  },

  // ── Direct account permissions (admin) ──
  async listDirectPermissions(accountId: string): Promise<string[]> {
    return unwrap(api.get<ApiResponse<string[]>>(`/auth/accounts/${accountId}/permissions`), "Direct permissions could not be loaded.");
  },

  async grantDirectPermission(accountId: string, permissionCode: string): Promise<void> {
    await api.post(`/auth/accounts/${accountId}/permissions`, { permission_code: permissionCode });
  },

  async revokeDirectPermission(accountId: string, permissionCode: string): Promise<void> {
    await api.delete(`/auth/accounts/${accountId}/permissions/${permissionCode}`);
  },

  errorMessage(error: unknown, fallback: string): string {
    return getApiErrorMessage(error, fallback);
  },
};

// ── User profile service ───────────────────────────────────────────────────

export const userService = {
  async getProfile(): Promise<ProfileRecord> {
    return unwrap(api.get<ApiResponse<ProfileRecord>>("/users/me"), "Profile could not be loaded.");
  },

  async upsertProfile(input: { first_name?: string; last_name?: string; date_of_birth?: string }): Promise<ProfileRecord> {
    return unwrap(api.put<ApiResponse<ProfileRecord>>("/users/me", input), "Profile could not be saved.");
  },
};
