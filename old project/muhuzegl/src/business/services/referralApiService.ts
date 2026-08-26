import type {
  Referral,
} from "../../components/referral/types";

import { apiClient } from "./apiClient";

/**
 * ==========================================
 * API RESPONSE TYPES
 * ==========================================
 */

interface ReferralListResponse {
  success: boolean;
  count: number;
  data: Referral[];
}

interface ReferralRewardsResponse {
  success: boolean;
  data: {
    totalRewards: number;
  };
}

interface ReferralResponse {
  success: boolean;
  data: Referral;
}

/**
 * ==========================================
 * REFERRAL API SERVICE
 * ==========================================
 */

export class ReferralApiService {
  /**
   * ==========================================
   * GET ALL REFERRALS
   * ==========================================
   *
   * GET:
   * /api/referrals/:referrerId
   */
  async getUserReferrals(
    referrerId: string
  ): Promise<Referral[]> {
    const response =
      await apiClient.get<ReferralListResponse>(
        `/referrals/${referrerId}`
      );

    return response.data;
  }

  /**
   * ==========================================
   * GET TOTAL REFERRAL REWARDS
   * ==========================================
   *
   * GET:
   * /api/referrals/:referrerId/rewards
   */
  async getTotalRewards(
    referrerId: string
  ): Promise<number> {
    const response =
      await apiClient.get<ReferralRewardsResponse>(
        `/referrals/${referrerId}/rewards`
      );

    return response.data.totalRewards || 0;
  }

  /**
   * ==========================================
   * GET ONE REFERRAL
   * ==========================================
   *
   * GET:
   * /api/referrals/:referrerId/:referralId
   */
  async getReferral(
    referrerId: string,
    referralId: string
  ): Promise<Referral> {
    const response =
      await apiClient.get<ReferralResponse>(
        `/referrals/${referrerId}/${referralId}`
      );

    return response.data;
  }

  /**
   * ==========================================
   * UPDATE REFERRAL STATUS
   * ==========================================
   *
   * PUT:
   * /api/referrals/:referrerId/:referralId/status
   */
  async updateReferralStatus(
    referrerId: string,
    referralId: string,
    status:
      | "Pending"
      | "Completed"
  ): Promise<Referral> {
    const response =
      await apiClient.put<ReferralResponse>(
        `/referrals/${referrerId}/${referralId}/status`,
        {
          status,
        }
      );

    return response.data;
  }

  /**
   * ==========================================
   * CREATE REFERRAL
   * ==========================================
   *
   * POST:
   * /api/referrals
   *
   * NOTE:
   * In the normal MUHUZE flow, referrals
   * should be created automatically during
   * registration.
   */
  async createReferral(
    data: {
      referrer: string;
      referredUser: string;
      referralCode: string;
      reward?: number;
      status?:
        | "Pending"
        | "Completed";
    }
  ): Promise<Referral> {
    const response =
      await apiClient.post<ReferralResponse>(
        "/referrals",
        data
      );

    return response.data;
  }
}

/**
 * ==========================================
 * SHARED SERVICE INSTANCE
 * ==========================================
 */

export const referralApiService =
  new ReferralApiService();