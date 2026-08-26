export type OrderStatus =
  | "Pending"
  | "Accepted"
  | "Preparing"
  | "Shipped"
  | "Delivered"
  | "Cancelled"
  | "Rejected";

export type PaymentStatus =
  | "Pending"
  | "Paid"
  | "Failed"
  | "Refunded";

export interface OrderProduct {
  productId: string;
  quantity: number;
}

export interface CreateOrder {
  buyerId: string;
  buyer: string;
  products: OrderProduct[];
  deliveryAddress: string;
  paymentMethod: string;
}

export interface Order {
  _id: string;

  buyerId: string;

  buyer: string;

  products: OrderProduct[];

  total: number;

  status: OrderStatus;

  deliveryAddress: string;

  paymentMethod: string;

  paymentStatus: PaymentStatus;

  createdAt: string;

  updatedAt: string;
}