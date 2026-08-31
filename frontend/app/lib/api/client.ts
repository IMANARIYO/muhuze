import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";
const ACCESS_TOKEN_KEY = "muhuze.accessToken";
const REFRESH_TOKEN_KEY = "muhuze.refreshToken";

export interface ApiResponse<T> {
  status: "success" | "error";
  message: string;
  data: T | null;
}

export const ACCESS_TOKEN_STORAGE_KEY = ACCESS_TOKEN_KEY;
export const REFRESH_TOKEN_STORAGE_KEY = REFRESH_TOKEN_KEY;

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function saveTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  document.cookie = `${ACCESS_TOKEN_KEY}=present; Path=/; SameSite=Lax`;
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  document.cookie = `${ACCESS_TOKEN_KEY}=; Max-Age=0; Path=/; SameSite=Lax`;
  document.cookie = "muhuze.role=; Max-Age=0; Path=/; SameSite=Lax";
}

export function saveRole(role: "client" | "seller" | "admin"): void {
  if (typeof window !== "undefined") document.cookie = `muhuze.role=${role}; Path=/; SameSite=Lax`;
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshRequest: Promise<string | null> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const refreshToken = getRefreshToken();

    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry || !refreshToken || originalRequest.url?.endsWith("/auth/refresh")) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    refreshRequest ??= api.post<ApiResponse<{ access_token: string; refresh_token: string }>>("/auth/refresh", { refresh_token: refreshToken })
      .then(({ data }) => {
        if (!data.data) return null;
        saveTokens(data.data.access_token, data.data.refresh_token);
        return data.data.access_token;
      })
      .catch(() => {
        clearTokens();
        return null;
      })
      .finally(() => {
        refreshRequest = null;
      });

    const newAccessToken = await refreshRequest;
    if (!newAccessToken) return Promise.reject(error);
    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
    return api(originalRequest);
  },
);

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiResponse<unknown>>(error)) {
    return error.response?.data?.message ?? fallback;
  }
  return error instanceof Error ? error.message : fallback;
}
