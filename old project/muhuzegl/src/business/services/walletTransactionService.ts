import type { WalletTransaction } from "../../types/walletTransaction";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:5000";

export class WalletTransactionService {
  /**
   * ==========================================
   * GET ALL TRANSACTIONS — ADMIN
   * ==========================================
   */

  async getAllTransactions(): Promise<
    WalletTransaction[]
  > {
    const token =
      localStorage.getItem("authToken");

    const response = await fetch(
      `${API_URL}/api/wallet-transactions/admin/all`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
          "Failed to load wallet transactions."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * GET USER TRANSACTIONS
   * ==========================================
   */

  async getUserTransactions(
    userId: string
  ): Promise<WalletTransaction[]> {
    const token =
      localStorage.getItem("authToken");

    const response = await fetch(
      `${API_URL}/api/wallet-transactions/${userId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
          "Failed to load wallet transactions."
      );
    }

    return result.data;
  }

  /**
   * ==========================================
   * GET ONE TRANSACTION
   * ==========================================
   */

  async getTransaction(
    transactionId: string
  ): Promise<WalletTransaction> {
    const token =
      localStorage.getItem("authToken");

    const response = await fetch(
      `${API_URL}/api/wallet-transactions/transaction/${transactionId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
          "Failed to load transaction."
      );
    }

    return result.data;
  }
}

export const walletTransactionService =
  new WalletTransactionService();