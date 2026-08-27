export type UserRole = "client" | "seller" | "admin";

export type ProductCategory =
  | "Electronics"
  | "Clothing"
  | "Food & Beverage"
  | "Home & Garden"
  | "Health & Beauty"
  | "Sports"
  | "Books"
  | "Other";

export type OrderStatus = "pending" | "processing" | "shipped" | "delivered" | "cancelled";
export type PaymentStatus = "pending" | "completed" | "refunded";
export type PayoutStatus = "pending" | "sent" | "failed";

export interface User {
  id: string;
  name: string;
  initials: string;
  role: UserRole;
  email: string;
  joinedAt: string;
}

export interface Product {
  id: string;
  name: string;
  price: number;
  category: ProductCategory;
  unit?: string;
  sellerId: string;
  sellerName: string;
  stock: number;
  description: string;
  createdAt: string;
}

export interface CartItem {
  productId: string;
  productName: string;
  price: number;
  quantity: number;
  unit?: string;
  sellerName: string;
}

export interface Order {
  id: string;
  clientId: string;
  clientName: string;
  sellerId: string;
  sellerName: string;
  items: CartItem[];
  total: number;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  createdAt: string;
}

export interface Payment {
  id: string;
  orderId: string;
  clientName: string;
  sellerName: string;
  amount: number;
  commission: number;
  sellerPayout: number;
  status: PaymentStatus;
  payoutStatus: PayoutStatus;
  createdAt: string;
}

export interface Earning {
  id: string;
  orderId: string;
  productName: string;
  clientName: string;
  grossAmount: number;
  commission: number;
  netAmount: number;
  payoutStatus: PayoutStatus;
  createdAt: string;
}

export interface NavItem {
  label: string;
  icon: string;
  href: string;
  count?: number;
  roles: UserRole[];
}
