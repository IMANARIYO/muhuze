import { api, type ApiResponse } from "@/app/lib/api/client";

export interface CartItemResponse {
  id: string;
  listing_id: string;
  seller_id: string;
  product_name: string;
  variant_name: string | null;
  unit_price: number;
  quantity: number;
  subtotal: number;
  created_at: string;
  updated_at: string;
}

export interface CartResponse {
  items: CartItemResponse[];
  item_count: number;
  total: number;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const cartService = {
  get() {
    return unwrap(api.get<ApiResponse<CartResponse>>("/carts"), "Your cart could not be loaded.");
  },
  addItem(listingId: string, quantity = 1) {
    return unwrap(api.post<ApiResponse<CartResponse>>("/carts/items", { listing_id: listingId, quantity }), "Item could not be added to cart.");
  },
  updateQuantity(itemId: string, quantity: number) {
    return unwrap(api.patch<ApiResponse<CartResponse>>(`/carts/items/${itemId}`, { quantity }), "Cart item could not be updated.");
  },
  removeItem(itemId: string) {
    return unwrap(api.delete<ApiResponse<null>>(`/carts/items/${itemId}`), "Item could not be removed from cart.");
  },
  clear() {
    return unwrap(api.delete<ApiResponse<null>>("/carts"), "Cart could not be cleared.");
  },
};