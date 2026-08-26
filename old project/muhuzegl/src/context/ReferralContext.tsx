import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  Referral,
  ReferralContextType,
} from "../components/referral/types";

import { referralApiService } from "../business/services/referralApiService";

import { useAuth } from "./AuthContext";

const ReferralContext =
  createContext<ReferralContextType | null>(null);

interface ReferralProviderProps {
  children: ReactNode;
}

export function ReferralProvider({
  children,
}: ReferralProviderProps) {
  const { currentUser } =
    useAuth();

  const [
    referrals,
    setReferrals,
  ] = useState<Referral[]>([]);

  const [
    totalRewards,
    setTotalRewards,
  ] = useState(0);

  /**
   * ==========================================
   * REAL REFERRAL CODE
   * ==========================================
   *
   * We use the logged-in user's MongoDB
   * _id as the referral identifier.
   *
   * Example:
   *
   * 6a6cdeff5496b1f4db58de19
   */

  const referralCode =
    currentUser?._id || "";

  /**
   * ==========================================
   * REAL REFERRAL LINK
   * ==========================================
   *
   * Example:
   *
   * http://localhost:5173/register?ref=USER_ID
   *
   * Production:
   *
   * https://muhuzeglobalink.com/register?ref=USER_ID
   */

  const frontendBaseUrl =
    window.location.origin;

  const referralLink =
    referralCode
      ? `${frontendBaseUrl}/register?ref=${referralCode}`
      : "";

  /**
   * ==========================================
   * LOAD USER REFERRALS
   * ==========================================
   */

  useEffect(() => {
    async function loadReferrals() {
      if (!currentUser?._id) {
        setReferrals([]);
        setTotalRewards(0);
        return;
      }

      try {
        const [
          referralData,
          rewardData,
        ] = await Promise.all([
          referralApiService.getUserReferrals(
            currentUser._id
          ),

          referralApiService.getTotalRewards(
            currentUser._id
          ),
        ]);

        setReferrals(
          referralData
        );

        setTotalRewards(
          rewardData
        );
      } catch (error) {
        console.error(
          "Failed to load referrals:",
          error
        );

        setReferrals([]);
        setTotalRewards(0);
      }
    }

    loadReferrals();
  }, [currentUser?._id]);

  /**
   * ==========================================
   * TOTAL REFERRALS
   * ==========================================
   */

  const totalReferrals =
    referrals.length;

  /**
   * ==========================================
   * PROVIDER
   * ==========================================
   */

  return (
    <ReferralContext.Provider
      value={{
        referralCode,

        referralLink,

        referrals,

        totalReferrals,

        totalRewards,

        /**
         * Referral creation is now handled
         * automatically by the backend during
         * user registration.
         *
         * We therefore do not expose a frontend
         * manual referral creator here.
         */
        addReferral: async () => {
          throw new Error(
            "Referrals are created automatically when a user registers through a referral link."
          );
        },
      }}
    >
      {children}
    </ReferralContext.Provider>
  );
}

export function useReferral() {
  const context =
    useContext(
      ReferralContext
    );

  if (!context) {
    throw new Error(
      "useReferral must be used inside ReferralProvider."
    );
  }

  return context;
}

export default ReferralContext;