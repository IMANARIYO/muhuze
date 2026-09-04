import { api, type ApiResponse } from "@/app/lib/api/client";

export interface OrderItemResponse {
  id: string;
  seller_id: string;
  listing_id: string;
  product_variant_id: string;
  product_name: string;
  variant_name: string | null;
  unit_price: number;
  quantity: number;
  subtotal: number;
}

export interface ShippingInfoResponse {
  id: string;
  recipient_name: string;
  phone: string;
  country: string;
  province: string | null;
  district: string | null;
  sector: string | null;
  cell: string | null;
  village: string | null;
  address_line: string | null;
  delivery_instructions: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface ShipmentResponse {
  id: string;
  carrier: string | null;
  tracking_number: string | null;
  status: string;
  shipped_at: string | null;
  delivered_at: string | null;
  notes: string | null;
}

export interface SellerOrderItemResponse {
  listing_id: string;
  product_name: string;
  variant_name: string | null;
  unit_price: number;
  quantity: number;
  subtotal: number;
}

export interface SellerOrderResponse {
  id: string;
  order_id: string;
  seller_id: string;
  status: string;
  rejected_reason: string | null;
  accepted_at: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  created_at: string;
  updated_at: string;
  shipment: ShipmentResponse | null;
  order_number: string | null;
  payment_status: string | null;
  currency: string;
  gross: number;
  commission_amount: number;
  seller_net: number;
  revenue_rate: number;
  revenue_status: string | null;
  items: SellerOrderItemResponse[];
}

export interface OrderDetailResponse {
  id: string;
  order_number: string;
  status: string;
  payment_status: string;
  subtotal: number;
  shipping_fee: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  paid_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItemResponse[];
  shipping: ShippingInfoResponse | null;
  contact_phone: string | null;
  notes: string | null;
  fulfillment: SellerOrderResponse[];
}

export interface OrderSummaryResponse {
  id: string;
  order_number: string;
  status: string;
  payment_status: string;
  total_amount: number;
  currency: string;
  created_at: string;
}

export interface AdminOrderSummaryResponse extends OrderSummaryResponse {
  payment_id: string | null;
  payment_status_detail: string | null;
}

export interface ShippingInput {
  recipient_name: string;
  phone: string;
  country?: string;
  province?: string;
  district?: string;
  sector?: string;
  cell?: string;
  village?: string;
  address_line?: string;
  delivery_instructions?: string;
  latitude?: number;
  longitude?: number;
}

export interface CheckoutInput {
  shipping?: ShippingInput;
  shipping_address_id?: string;
  contact_phone?: string;
  notes?: string;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const orderService = {
  checkout(input: CheckoutInput) {
    return unwrap(api.post<ApiResponse<OrderDetailResponse>>("/orders", input), "Order could not be placed.");
  },
  listMine() {
    return unwrap(api.get<ApiResponse<OrderSummaryResponse[]>>("/orders"), "Your orders could not be loaded.");
  },
  listAll() {
    return unwrap(api.get<ApiResponse<AdminOrderSummaryResponse[]>>("/orders/admin"), "Orders could not be loaded.");
  },
  get(orderId: string) {
    return unwrap(api.get<ApiResponse<OrderDetailResponse>>(`/orders/${orderId}`), "Order could not be loaded.");
  },
  receive(orderId: string) {
    return unwrap(api.post<ApiResponse<OrderDetailResponse>>(`/orders/${orderId}/receive`), "Order could not be marked as received.");
  },
  listSellerOrders() {
    return unwrap(api.get<ApiResponse<SellerOrderResponse[]>>("/orders/seller"), "Orders received could not be loaded.");
  },
  acceptSellerOrder(sellerOrderId: string) {
    return unwrap(api.post<ApiResponse<SellerOrderResponse>>(`/orders/seller/${sellerOrderId}/accept`), "Order could not be accepted.");
  },
  rejectSellerOrder(sellerOrderId: string, reason: string) {
    return unwrap(api.post<ApiResponse<SellerOrderResponse>>(`/orders/seller/${sellerOrderId}/reject`, { reason }), "Order could not be rejected.");
  },
  shipSellerOrder(sellerOrderId: string, input: { carrier?: string; tracking_number?: string; notes?: string }) {
    return unwrap(api.post<ApiResponse<SellerOrderResponse>>(`/orders/seller/${sellerOrderId}/ship`, input), "Order could not be marked as shipped.");
  },
  deliverShipment(shipmentId: string) {
    return unwrap(api.post<ApiResponse<SellerOrderResponse>>(`/orders/seller/shipments/${shipmentId}/deliver`), "Shipment could not be marked as delivered.");
  },
};