import { api, type ApiResponse } from "@/app/lib/api/client";

export interface CatalogImage {
  id: string;
  url: string;
  is_primary: boolean;
  sort_order: number;
}

export interface CatalogListingItem {
  listing_id: string;
  price: number;
  stock: number;
  condition: "new" | "like_new" | "used";
  product: { id: string; name: string; slug: string; description: string | null; category_id: string };
  variant: { id: string; sku_code: string | null; attribute_values: Array<{ attribute_id: string; attribute_name: string; value: string }> };
  seller: { id: string; business_name: string };
  images: CatalogImage[];
}

export interface CatalogFilters {
  category_id?: string;
  brand_id?: string;
  search?: string;
  sort?: "price_asc" | "price_desc";
}

export const catalogService = {
  async list(filters: CatalogFilters = {}): Promise<CatalogListingItem[]> {
    const { data } = await api.get<ApiResponse<CatalogListingItem[]>>("/catalog", { params: filters });
    return data.data ?? [];
  },

  async getProduct(productId: string): Promise<unknown> {
    const { data } = await api.get<ApiResponse<unknown>>(`/catalog/products/${productId}`);
    if (!data.data) throw new Error(data.message || "Product not found.");
    return data.data;
  },
};
