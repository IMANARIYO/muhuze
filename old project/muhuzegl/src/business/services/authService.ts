import type {
  LoginData,
  RegisterData,
} from "../../types/auth";

import type { User } from "../../types/user";

import { apiClient } from "./apiClient";

export class AuthService {
  private currentUserKey =
    "currentUser";

  private tokenKey =
    "authToken";

  /**
   * ==========================================
   * REGISTER
   * ==========================================
   */

  async register(
    data: RegisterData
  ): Promise<User> {
    const response =
      await fetch(
        "http://localhost:5000/api/users/register",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            fullName:
              data.fullName,

            email:
              data.email,

            password:
              data.password,

            phone:
              data.phone,

            referralCode:
              data.referralCode ||
              undefined,
          }),
        }
      );

    const result =
      await response.json();

    if (!response.ok) {
      throw new Error(
        result.message ||
          "Registration failed."
      );
    }

    this.setCurrentUser(
      result.data
    );

    return result.data;
  }
async getAuthenticatedUser(): Promise<User> {
  const result =
    await apiClient.get<{
      success: boolean;
      user: User;
    }>("/users/me");

  if (!result.success || !result.user) {
    throw new Error(
      "Unable to get authenticated user."
    );
  }

  this.setCurrentUser(
    result.user
  );

  return result.user;
}
  /**
   * ==========================================
   * LOGIN
   * ==========================================
   */

  async login(
    data: LoginData
  ): Promise<User> {
    const response =
      await fetch(
        "http://localhost:5000/api/users/login",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            email:
              data.email,

            password:
              data.password,
          }),
        }
      );

    const result =
      await response.json();

    if (!response.ok) {
      throw new Error(
        result.message ||
          "Login failed."
      );
    }

    /**
     * ==========================================
     * SAVE JWT TOKEN
     * ==========================================
     */

    if (!result.token) {
      throw new Error(
        "Login successful but authentication token was not provided."
      );
    }

    localStorage.setItem(
      this.tokenKey,
      result.token
    );

    /**
     * ==========================================
     * SAVE USER
     * ==========================================
     */

    this.setCurrentUser(
      result.user
    );

    return result.user;
  }

  /**
   * ==========================================
   * GET AUTH TOKEN
   * ==========================================
   */

  getToken(): string | null {
    return localStorage.getItem(
      this.tokenKey
    );
  }

  /**
 * ==========================================
 * UPDATE PROFILE
 * ==========================================
 */

async updateProfile(
  data: {
    fullName: string;
    phone?: string;
  }
): Promise<User> {
  const result =
    await apiClient.put<{
      success: boolean;
      message: string;
      user: User;
    }>(
      "/users/profile",
      data
    );

  if (
    !result.success ||
    !result.user
  ) {
    throw new Error(
      result.message ||
        "Profile update failed."
    );
  }

  this.setCurrentUser(
    result.user
  );

  return result.user;
}

  /**
   * ==========================================
   * LOGOUT
   * ==========================================
   */

  logout(): void {
    localStorage.removeItem(
      this.currentUserKey
    );

    localStorage.removeItem(
      this.tokenKey
    );
  }

  /**
   * ==========================================
   * GET CURRENT USER
   * ==========================================
   */

  getCurrentUser():
    User | null {
    const user =
      localStorage.getItem(
        this.currentUserKey
      );

    if (!user) {
      return null;
    }

    try {
      return JSON.parse(
        user
      ) as User;
    } catch {
      localStorage.removeItem(
        this.currentUserKey
      );

      return null;
    }
  }

  /**
   * ==========================================
   * IS AUTHENTICATED
   * ==========================================
   */

  isAuthenticated(): boolean {
    return (
      this.getCurrentUser() !==
      null &&
      this.getToken() !== null
    );
  }

  /**
   * ==========================================
   * SAVE CURRENT USER
   * ==========================================
   */

  private setCurrentUser(
    user: User
  ): void {
    localStorage.setItem(
      this.currentUserKey,
      JSON.stringify(user)
    );
  }
}

/**
 * Shared AuthService instance
 */

export const authService =
  new AuthService();