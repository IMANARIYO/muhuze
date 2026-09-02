import { api, type ApiResponse } from "@/app/lib/api/client";

export interface RevenueLine {
  id: string;
  seller_id: string;
  amount: number;
  revenue_rate: number;
  commission_amount: number;
  seller_earning: number;
  referral_eligible: boolean;
  status: string;
  released_at: string | null;
}

export interface RevenueTransactionResponse extends RevenueLine {
  order_id: string;
  payment_id: string;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface RevenueSummaryResponse {
  total_gross: number;
  total_commission: number;
  total_seller_earning: number;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const revenueService = {
  mine() {
    return unwrap(api.get<ApiResponse<RevenueLine[]>>("/revenue/me"), "Your earnings could not be loaded.");
  },
  mineForOrder(orderId: string) {
    return unwrap(api.get<ApiResponse<RevenueLine[]>>(`/revenue/order/${orderId}/me`), "This order's earnings could not be loaded.");
  },
  all() {
    return unwrap(api.get<ApiResponse<RevenueTransactionResponse[]>>("/revenue"), "Revenue transactions could not be loaded.");
  },
  orderSummary(orderId: string) {
    return unwrap(api.get<ApiResponse<RevenueSummaryResponse>>(`/revenue/order/${orderId}/summary`), "Revenue summary could not be loaded.");
  },
  orderBreakdown(orderId: string) {
    return unwrap(api.get<ApiResponse<RevenueLine[]>>(`/revenue/order/${orderId}`), "Revenue breakdown could not be loaded.");
  },
};