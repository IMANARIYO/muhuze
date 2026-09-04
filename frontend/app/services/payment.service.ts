import { api, type ApiResponse } from "@/app/lib/api/client";

export interface PaymentResponse {
  id: string;
  order_id: string;
  status: string;
  amount: number;
  currency: string;
  momo_phone: string | null;
  airtel_phone: string | null;
  method: string | null;
  provider_ref: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaidPaymentResponse extends PaymentResponse {
  revenue: number;
}

export interface CreatePaymentInput {
  order_id: string;
  momo_phone?: string;
  airtel_phone?: string;
  method?: string;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const paymentService = {
  create(input: CreatePaymentInput) {
    return unwrap(api.post<ApiResponse<PaymentResponse>>("/payments", input), "Payment could not be started.");
  },
  reportPaid(paymentId: string) {
    return unwrap(api.post<ApiResponse<PaymentResponse>>(`/payments/${paymentId}/paid`, {}), "Payment could not be reported.");
  },
  confirmPaid(paymentId: string) {
    return unwrap(api.post<ApiResponse<PaidPaymentResponse>>(`/payments/${paymentId}/confirm`, {}), "Payment could not be confirmed.");
  },
  markFailed(paymentId: string) {
    return unwrap(api.post<ApiResponse<PaymentResponse>>(`/payments/${paymentId}/failed`, {}), "Payment could not be marked as failed.");
  },
  get(paymentId: string) {
    return unwrap(api.get<ApiResponse<PaymentResponse>>(`/payments/${paymentId}`), "Payment could not be loaded.");
  },
};