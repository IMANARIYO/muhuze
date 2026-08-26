import { BUSINESS_SETTINGS } from "./settings";

export function calculateCommission(
  amount: number
) {
  return (
    amount *
    (BUSINESS_SETTINGS.referralPercentage / 100)
  );
}