import { processPayment } from "../payment";

import { TransactionService } from "./transactionService";
import { NotificationService } from "./notificationService";

import type { PremiumPlan } from "../../types/premium";
import type { PaymentResult } from "../../types/payment";

/**
 * ==========================================
 * PREMIUM SERVICE
 * ==========================================
 *
 * Handles the frontend Premium purchase flow.
 *
 * IMPORTANT:
 *
 * This service does NOT directly manage the
 * backend wallet or referral commissions.
 *
 * Financial operations are controlled by the
 * MUHUZE backend.
 *
 * Backend flow:
 *
 * Payment
 *   ↓
 * RevenueTransaction
 *   ↓
 * Referral eligibility
 *   ↓
 * Premium eligibility
 *   ↓
 * ReferralCommission
 *   ↓
 * Pending wallet
 *   ↓
 * Available after release conditions
 */

export class PremiumService {
  /**
   * Local transaction service.
   *
   * This is retained for the existing frontend
   * transaction/history UI.
   */
  private transactionService =
    new TransactionService();

  /**
   * Notification service.
   */
  private notificationService =
    new NotificationService();

  /**
   * ==========================================
   * BUY PREMIUM
   * ==========================================
   *
   * Purchases an Individual Premium plan.
   *
   * Current plans:
   *
   * Monthly → $10
   * Annual  → $100
   *
   * Business and Enterprise are not handled
   * here yet.
   *
   * IMPORTANT:
   *
   * This frontend service must not:
   *
   * - create referral commissions
   * - directly credit the wallet
   * - directly modify wallet balances
   *
   * Those operations belong to the backend.
   */

  buy(
    plan: PremiumPlan,
    userId: string,
    _referredBy?: string
  ): PaymentResult {
    /**
     * ========================================
     * PAYMENT
     * ========================================
     *
     * The existing frontend payment function
     * is retained for compatibility with the
     * current frontend service architecture.
     *
     * The authoritative financial processing
     * remains on the backend.
     */

    const result = processPayment({
      userId,

      service: plan.service,

      amount: plan.price,
    });

    /**
     * Stop if payment failed.
     */
    if (!result.success) {
      return result;
    }

    /**
     * ========================================
     * SAVE FRONTEND TRANSACTION
     * ========================================
     *
     * This is only a frontend transaction
     * record for the existing UI.
     *
     * It does NOT create referral commissions
     * and does NOT credit the backend wallet.
     */

    this.transactionService.create({
      id: crypto.randomUUID(),

      userId,

      type: "premium",

      amount: plan.price,

      description:
        `${plan.name} Premium Membership`,

      status: "completed",

      createdAt:
        new Date().toISOString(),
    });

    /**
     * ========================================
     * PREMIUM ACTIVATION NOTIFICATION
     * ========================================
     *
     * This notification belongs to the
     * existing frontend notification system.
     *
     * Backend Premium activation should still
     * happen only after confirmed payment.
     */

    this.notificationService.create({
      id: crypto.randomUUID(),

      userId,

      title:
        "Premium Payment Submitted",

      message:
        `${plan.name} Premium Membership payment was submitted successfully.`,

      type: "premium",

      read: false,

      createdAt:
        new Date().toISOString(),
    });

    /**
     * ========================================
     * REFERRAL COMMISSION
     * ========================================
     *
     * DO NOT create referral commissions here.
     *
     * The old system did:
     *
     * referredBy
     *     ↓
     * plan.commission
     *     ↓
     * wallet credit
     *
     * That system is no longer used.
     *
     * New MUHUZE architecture:
     *
     * Premium payment
     *     ↓
     * Backend PaymentService
     *     ↓
     * NOWPayments
     *     ↓
     * RevenueService
     *     ↓
     * RevenueTransaction
     *     ↓
     * Referral eligibility
     *     ↓
     * ReferralCommissionService
     *     ↓
     * ReferralCommission
     *     ↓
     * WalletService
     *
     * Commission levels:
     *
     * Level 1 = 12%
     * Level 2 = 5%
     * Level 3 = 3%
     *
     * The commission is calculated from
     * eligible MUHUZE revenue, not from a
     * fixed frontend Premium commission.
     */

    return result;
  }
}

/**
 * ==========================================
 * SHARED PREMIUM SERVICE INSTANCE
 * ==========================================
 */

export const premiumService =
  new PremiumService();