export type NotificationType =
  | "system"
  | "premium"
  | "wallet"
  | "referral"
  | "order"
  | "product";

export interface Notification {
  id: string;

  userId: string;

  title: string;

  message: string;

  type: NotificationType;

  read: boolean;

  createdAt: string;
}