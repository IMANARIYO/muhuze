import { calculateCommission } from "./commission";
import type {
  PaymentRequest,
  PaymentResult,
} from "../types/payment";
export function processPayment(
  request: PaymentRequest
): PaymentResult {
  const commission =
    request.referredBy
      ? calculateCommission(request.amount)
      : 0;

  // Future integrations:
  // - Activate premium
  // - Save payment
  // - Credit wallet
  // - Create notification
  // - Update referral history

  return {
    success: true,
    message: "Payment completed successfully.",
    commission,
  };
}