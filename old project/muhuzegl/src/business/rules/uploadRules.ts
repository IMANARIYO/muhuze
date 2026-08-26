import type { User } from "../../types/user";

export function requiresUploadFee(
  user: User
) {
  return !user.premium.active;
}

export function canUploadProduct(
  user: User
) {
  return (
    user.role === "seller" ||
    user.role === "admin"
  );
}