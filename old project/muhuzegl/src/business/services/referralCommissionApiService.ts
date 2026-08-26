import type {
  ReferralCommission,
  ReferralCommissionSummary,
} from "../../types/referralCommission";

import { apiClient } from "./apiClient";

interface ReferralCommissionListResponse {
  success: boolean;
  data: ReferralCommission[];
}

interface ReferralCommissionSummaryResponse {
  success: boolean;
  data: ReferralCommissionSummary;
}

export const referralCommissionApiService = {
  /**
   * ==========================================
   * GET USER COMMISSIONS
   * ==========================================
   */
  async getUserCommissions(
    referrerId: string
  ): Promise<ReferralCommission[]> {
    const response =
      await apiClient.get<ReferralCommissionListResponse>(
        `/referral-commissions/${referrerId}`
      );

    return response.data;
  },

  /**
   * ==========================================
   * GET COMMISSION SUMMARY
   * ==========================================
   */
  async getCommissionSummary(
    referrerId: string
  ): Promise<ReferralCommissionSummary> {
    const response =
      await apiClient.get<ReferralCommissionSummaryResponse>(
        `/referral-commissions/${referrerId}/summary`
      );

    return response.data;
  },
};