import type { Withdrawal } from "../../types/withdrawal";

import { authService } from "./authService";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:5000";

export class WithdrawalService {
  /**
   * ==========================================
   * AUTH HEADERS
   * ==========================================
   */

  private getHeaders(): HeadersInit {
    const token =
      authService.getToken();

    return {
      "Content-Type":
        "application/json",

      ...(token
        ? {
            Authorization:
              `Bearer ${token}`,
          }
        : {}),
    };
  }

  /**
   * ==========================================
   * GET USER WITHDRAWALS
   * ==========================================
   */

  async getUserWithdrawals(
    userId: string
  ): Promise<Withdrawal[]> {
    const response =
      await fetch(
        `${API_URL}/api/withdrawals/${userId}`,
        {
          headers:
            this.getHeaders(),
        }
      );

    const result =
      await response.json();

    if (
      !response.ok ||
      !result.success
    ) {
      throw new Error(
        result.message ||
          "Failed to load withdrawals."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * GET ALL WITHDRAWALS — ADMIN
   * ==========================================
   */

  async getAllWithdrawals(): Promise<
    Withdrawal[]
  > {
    const response =
      await fetch(
        `${API_URL}/api/withdrawals/admin/all`,
        {
          headers:
            this.getHeaders(),
        }
      );

    const result =
      await response.json();

    if (
      !response.ok ||
      !result.success
    ) {
      throw new Error(
        result.message ||
          "Failed to load withdrawals."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * PROCESS WITHDRAWAL
   * ==========================================
   */

  async processWithdrawal(
    withdrawalId: string
  ): Promise<Withdrawal> {
    const response =
      await fetch(
        `${API_URL}/api/withdrawals/${withdrawalId}/process`,
        {
          method: "POST",

          headers:
            this.getHeaders(),
        }
      );

    const result =
      await response.json();

    if (
      !response.ok ||
      !result.success
    ) {
      throw new Error(
        result.message ||
          "Failed to process withdrawal."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * COMPLETE WITHDRAWAL
   * ==========================================
   */

  async completeWithdrawal(
    withdrawalId: string
  ): Promise<Withdrawal> {
    const response =
      await fetch(
        `${API_URL}/api/withdrawals/${withdrawalId}/complete`,
        {
          method: "POST",

          headers:
            this.getHeaders(),
        }
      );

    const result =
      await response.json();

    if (
      !response.ok ||
      !result.success
    ) {
      throw new Error(
        result.message ||
          "Failed to complete withdrawal."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * REJECT WITHDRAWAL
   * ==========================================
   */

  async rejectWithdrawal(
    withdrawalId: string,
    rejectionReason: string
  ): Promise<Withdrawal> {
    const response =
      await fetch(
        `${API_URL}/api/withdrawals/${withdrawalId}/reject`,
        {
          method: "POST",

          headers:
            this.getHeaders(),

          body: JSON.stringify({
            rejectionReason,
          }),
        }
      );

    const result =
      await response.json();

    if (
      !response.ok ||
      !result.success
    ) {
      throw new Error(
        result.message ||
          "Failed to reject withdrawal."
      );
    }

    return result.data;
  }
}