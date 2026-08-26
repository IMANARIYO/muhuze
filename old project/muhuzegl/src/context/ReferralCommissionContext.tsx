import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  ReferralCommission,
  ReferralCommissionSummary,
} from "../types/referralCommission";

import {
  referralCommissionApiService,
} from "../business/services/referralCommissionApiService";

import { useAuth } from "./AuthContext";

/**
 * ==========================================
 * CONTEXT TYPE
 * ==========================================
 */

interface ReferralCommissionContextType {
  commissions: ReferralCommission[];

  summary: ReferralCommissionSummary;

  loading: boolean;

  error: string | null;

  refreshCommissions: () => Promise<void>;
}

/**
 * ==========================================
 * DEFAULT SUMMARY
 * ==========================================
 */

const defaultSummary: ReferralCommissionSummary = {
  totalCommission: 0,

  pendingCommission: 0,

  availableCommission: 0,

  reversedCommission: 0,

  cancelledCommission: 0,
};

/**
 * ==========================================
 * CONTEXT
 * ==========================================
 */

const ReferralCommissionContext =
  createContext<
    ReferralCommissionContextType | null
  >(null);

/**
 * ==========================================
 * PROVIDER PROPS
 * ==========================================
 */

interface ReferralCommissionProviderProps {
  children: ReactNode;
}

/**
 * ==========================================
 * PROVIDER
 * ==========================================
 */

export function ReferralCommissionProvider({
  children,
}: ReferralCommissionProviderProps) {
  const { currentUser } =
    useAuth();

  const [
    commissions,
    setCommissions,
  ] = useState<ReferralCommission[]>(
    []
  );

  const [
    summary,
    setSummary,
  ] = useState<ReferralCommissionSummary>(
    defaultSummary
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  /**
   * ==========================================
   * LOAD COMMISSIONS
   * ==========================================
   */

  async function refreshCommissions() {
    if (!currentUser?._id) {
      setCommissions([]);

      setSummary(
        defaultSummary
      );

      return;
    }

    try {
      setLoading(true);

      setError(null);

      const [
        commissionData,
        summaryData,
      ] = await Promise.all([
        referralCommissionApiService.getUserCommissions(
          currentUser._id
        ),

        referralCommissionApiService.getCommissionSummary(
          currentUser._id
        ),
      ]);

      setCommissions(
        commissionData
      );

      setSummary(
        summaryData
      );
    } catch (error) {
      console.error(
        "Failed to load referral commissions:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Failed to load referral commissions."
      );

      setCommissions([]);

      setSummary(
        defaultSummary
      );
    } finally {
      setLoading(false);
    }
  }

  /**
   * ==========================================
   * LOAD WHEN USER CHANGES
   * ==========================================
   */

  useEffect(() => {
    refreshCommissions();
  }, [currentUser?._id]);

  /**
   * ==========================================
   * PROVIDER
   * ==========================================
   */

  return (
    <ReferralCommissionContext.Provider
      value={{
        commissions,

        summary,

        loading,

        error,

        refreshCommissions,
      }}
    >
      {children}
    </ReferralCommissionContext.Provider>
  );
}

/**
 * ==========================================
 * HOOK
 * ==========================================
 */

export function useReferralCommission() {
  const context =
    useContext(
      ReferralCommissionContext
    );

  if (!context) {
    throw new Error(
      "useReferralCommission must be used inside ReferralCommissionProvider."
    );
  }

  return context;
}

export default ReferralCommissionContext;