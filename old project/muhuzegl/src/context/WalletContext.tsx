import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "./AuthContext";

import type {
  WalletContextType,
  WalletTransaction,
} from "../components/wallet/types";
import { apiClient } from "../business/services/apiClient";


/**
 * ==========================================
 * WALLET CONTEXT
 * ==========================================
 */

const WalletContext =
  createContext<WalletContextType | null>(null);

interface WalletProviderProps {
  children: ReactNode;
}

/**
 * ==========================================
 * BACKEND WALLET TRANSACTION
 * ==========================================
 */

interface BackendWalletTransaction {
  _id: string;

  userId: string;

  type:
    | "REFERRAL_COMMISSION"
    | "COMMISSION_REVERSAL"
    | "WITHDRAWAL"
    | "REFUND"
    | "ADJUSTMENT";

  amount: number;

  currency: string;

  referenceId?: string;

  referenceType?: string;

  status:
    | "Pending"
    | "Completed"
    | "Reversed"
    | "Cancelled";

  description?: string;

  createdAt: string;

  updatedAt: string;
}

/**
 * ==========================================
 * BACKEND WALLET RESPONSE
 * ==========================================
 */

interface BackendWallet {
  balance: number;

  pendingBalance: number;

  totalEarned: number;

  totalWithdrawn: number;

  currency?: string;

  status?: string;
}

/**
 * ==========================================
 * WALLET PROVIDER
 * ==========================================
 */

export function WalletProvider({
  children,
}: WalletProviderProps) {
  const { currentUser } = useAuth();

  /**
   * ==========================================
   * WALLET STATE
   * ==========================================
   */

  const [balance, setBalance] =
    useState<number>(0);

  const [pendingBalance, setPendingBalance] =
    useState<number>(0);

  const [totalEarned, setTotalEarned] =
    useState<number>(0);

  const [totalWithdrawn, setTotalWithdrawn] =
    useState<number>(0);
const [currency, setCurrency] =
  useState<string>("RWF");
  const [transactions, setTransactions] =
    useState<WalletTransaction[]>([]);

  const [loading, setLoading] =
    useState<boolean>(false);

  /**
   * ==========================================
   * LOAD WALLET FROM BACKEND
   * ==========================================
   *
   * IMPORTANT:
   *
   * We no longer send the user ID
   * through the URL.
   *
   * The backend identifies the current
   * user through the authentication token.
   *
   * GET /api/wallet
   *
   * GET /api/wallet/transactions
   *
   */

  async function loadWallet() {
    /**
     * ----------------------------------------
     * No authenticated user
     * ----------------------------------------
     */

    if (!currentUser?._id) {
      setBalance(0);

      setPendingBalance(0);

      setTotalEarned(0);

      setTotalWithdrawn(0);
      setCurrency("RWF");
      setTransactions([]);

      return;
    }

    try {
      setLoading(true);

      /**
       * ======================================
       * GET CURRENT USER WALLET
       * ======================================
       */

      const walletResult =
        await apiClient.get<{
          success: boolean;

          data: BackendWallet;
        }>("/wallet");

      if (!walletResult.success) {
        throw new Error(
          "Failed to load wallet."
        );
      }

      const wallet =
        walletResult.data;
        setCurrency(
  wallet.currency || "RWF"
);

      /**
       * --------------------------------------
       * Update wallet balances
       * --------------------------------------
       */

      setBalance(
        Number(wallet.balance) || 0
      );

      setPendingBalance(
        Number(
          wallet.pendingBalance
        ) || 0
      );

      setTotalEarned(
        Number(
          wallet.totalEarned
        ) || 0
      );

      setTotalWithdrawn(
        Number(
          wallet.totalWithdrawn
        ) || 0
      );

      /**
       * ======================================
       * GET CURRENT USER TRANSACTIONS
       * ======================================
       */

      const transactionResult =
        await apiClient.get<{
          success: boolean;

          count: number;

          data: BackendWalletTransaction[];
        }>(
          "/wallet/transactions"
        );

      if (!transactionResult.success) {
        throw new Error(
          "Failed to load wallet transactions."
        );
      }

      const backendTransactions =
        transactionResult.data || [];

      /**
       * ======================================
       * FORMAT TRANSACTIONS FOR FRONTEND
       * ======================================
       */

      const formattedTransactions =
        backendTransactions.map(
          (
            transaction: BackendWalletTransaction
          ): WalletTransaction => ({
            id:
              transaction._id,

            type:
              transaction.type,

            amount:
              transaction.amount,

            currency:
              transaction.currency,

            status:
              transaction.status,

            description:
              transaction.description ||
              "",

            date:
              transaction.createdAt,

            referenceId:
              transaction.referenceId,

            referenceType:
              transaction.referenceType as
                | "ReferralCommission"
                | "Withdrawal"
                | "RevenueTransaction"
                | "Order"
                | undefined,
          })
        );

      setTransactions(
        formattedTransactions
      );

    } catch (error) {

      console.error(
        "Failed to load wallet:",
        error
      );

      /**
       * --------------------------------------
       * Reset frontend wallet state
       * if loading fails
       * --------------------------------------
       */

      setBalance(0);

      setPendingBalance(0);

      setTotalEarned(0);

      setTotalWithdrawn(0);
      
      setCurrency("RWF");

      setTransactions([]);

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
    loadWallet();
  }, [currentUser?._id]);

  /**
   * ==========================================
   * REFRESH WALLET
   * ==========================================
   */

  async function refreshWallet() {
    await loadWallet();
  }

  /**
   * ==========================================
   * FINANCIAL OPERATIONS
   * ==========================================
   *
   * IMPORTANT:
   *
   * These functions intentionally DO NOT
   * modify the wallet locally.
   *
   * Financial operations must be processed
   * by the backend.
   *
   */

  function deposit(
    _amount: number,
    _description?: string
  ): boolean {
    console.warn(
      "Deposit must be processed by the backend."
    );

    return false;
  }

  function withdraw(
    _amount: number,
    _description?: string
  ): boolean {
    console.warn(
      "Withdrawal must be processed by the backend."
    );

    return false;
  }

  function addSale(
    _amount: number,
    _description?: string
  ): boolean {
    console.warn(
      "Sales must be processed by the backend."
    );

    return false;
  }

  function addReferralReward(
    _amount: number,
    _description?: string
  ): boolean {
    console.warn(
      "Referral rewards must be processed by the backend."
    );

    return false;
  }

  /**
   * ==========================================
   * PROVIDER
   * ==========================================
   */

  return (
    <WalletContext.Provider
      value={{
        balance,

        pendingBalance,

        totalEarned,

        totalWithdrawn,

        currency,

        transactions,

        loading,

        refreshWallet,

        deposit,

        withdraw,

        addSale,

        addReferralReward,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

/**
 * ==========================================
 * USE WALLET HOOK
 * ==========================================
 */

export function useWallet() {
  const context =
    useContext(WalletContext);

  if (!context) {
    throw new Error(
      "useWallet must be used inside WalletProvider."
    );
  }

  return context;
}

export default WalletContext;