import { apiClient } from "./apiClient";

export interface Wallet {
  _id: string;
  userId: string;

  balance: number;
  pendingBalance: number;
  totalEarned: number;
  totalWithdrawn: number;

  currency: string;
  status: string;

  createdAt?: string;
  updatedAt?: string;
}

interface WalletResponse {
  success: boolean;
  data: Wallet;
}

class WalletService {
  /**
   * Get current authenticated user's wallet
   */
  async getWallet(): Promise<Wallet> {
    const response =
      await apiClient.get<WalletResponse>(
        "/wallet"
      );

    return response.data;
  }
}

export default new WalletService();