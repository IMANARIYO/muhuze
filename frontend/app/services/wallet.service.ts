import { api, type ApiResponse } from "@/app/lib/api/client";

export interface WalletResponse {
  id: string;
  seller_id: string;
  available_balance: number;
  held_balance: number;
  total_earned: number;
  total_withdrawn: number;
  currency: string;
  created_at: string;
}

export interface WalletTransactionResponse {
  id: string;
  wallet_id: string;
  type: string;
  amount: number;
  balance_after: number;
  currency: string;
  status: string;
  reference_type: string | null;
  reference_id: string | null;
  description: string | null;
  created_at: string;
}

export interface WithdrawalResponse {
  id: string;
  wallet_id: string;
  seller_id: string;
  amount: number;
  currency: string;
  mobile_money_number: string;
  status: string;
  note: string | null;
  processed_by: string | null;
  processed_at: string | null;
  created_at: string;
}

export interface WalletSummary {
  wallet: WalletResponse;
  transactions: WalletTransactionResponse[];
  withdrawals: WithdrawalResponse[];
}

export interface AdminWalletOverview {
  total_available: number;
  total_held: number;
  total_platform_earned: number;
  total_withdrawn: number;
  seller_count: number;
  withdrawals_pending: WithdrawalResponse[];
}

export interface CreateWithdrawalInput {
  amount: number;
  mobile_money_number: string;
  note?: string;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const walletService = {
  getMine() {
    return unwrap(api.get<ApiResponse<WalletSummary>>("/wallet"), "Your wallet could not be loaded.");
  },
  requestWithdrawal(input: CreateWithdrawalInput) {
    return unwrap(api.post<ApiResponse<WithdrawalResponse>>("/wallet/withdrawals", input), "Withdrawal could not be requested.");
  },
  getAdminOverview() {
    return unwrap(api.get<ApiResponse<AdminWalletOverview>>("/wallet/admin/overview"), "Wallet overview could not be loaded.");
  },
  listPendingWithdrawals() {
    return unwrap(api.get<ApiResponse<WithdrawalResponse[]>>("/wallet/admin/withdrawals"), "Withdrawals could not be loaded.");
  },
  updateWithdrawal(withdrawalId: string, input: { status: string; note?: string }) {
    return unwrap(api.post<ApiResponse<WithdrawalResponse>>(`/wallet/admin/withdrawals/${withdrawalId}`, input), "Withdrawal could not be updated.");
  },
};
