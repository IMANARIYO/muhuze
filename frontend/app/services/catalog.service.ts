import { api, type ApiResponse } from "@/app/lib/api/client";

export interface CatalogImage {
  id: string;
  url: string;
  is_primary: boolean;
  sort_order: number;
}

export interface CatalogVariantAttribute {
  attribute_id: string;
  attribute_name: string;
  value: string;
}

export interface CatalogProductRef {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  category_id: string;
}

export interface CatalogVariantRef {
  id: string;
  sku_code: string | null;
  attribute_values: CatalogVariantAttribute[];
}

export interface CatalogSellerRef {
  id: string;
  business_name: string;
}

export interface CatalogListingItem {
  listing_id: string;
  price: number;
  stock: number;
  condition: "new" | "like_new" | "used";
  product: CatalogProductRef;
  variant: CatalogVariantRef;
  seller: CatalogSellerRef;
  images: CatalogImage[];
}

export interface CatalogOffer {
  listing_id: string;
  price: number;
  stock: number;
  condition: "new" | "like_new" | "used";
  seller: CatalogSellerRef;
}

export interface CatalogVariantDetail {
  id: string;
  sku_code: string | null;
  attribute_values: CatalogVariantAttribute[];
  offers: CatalogOffer[];
}

export interface CatalogProductDetail {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  category_id: string;
  brand_id: string | null;
  images: CatalogImage[];
  variants: CatalogVariantDetail[];
}

export interface CatalogFilterAttribute {
  attribute_id: string;
  name: string;
  input_type: string;
  values: string[];
}

export interface CatalogFilterOption {
  id: string;
  name: string;
}

export interface CatalogFiltersPayload {
  category_id: string | null;
  category_ids: string[];
  brands: CatalogFilterOption[];
  attributes: CatalogFilterAttribute[];
  price_range: { min: number; max: number };
  conditions: string[];
}

export interface CatalogListParams {
  category_id?: string;
  brand_id?: string;
  search?: string;
  min_price?: number;
  max_price?: number;
  condition?: string[];
  in_stock?: boolean;
  attribute_id?: string[];
  value?: string[];
  sort?: "price_asc" | "price_desc" | "newest";
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const catalogService = {
  list(params: CatalogListParams = {}) {
    return unwrap(api.get<ApiResponse<CatalogListingItem[]>>("/catalog", { params }), "Catalog could not be loaded.");
  },

  getProduct(productId: string) {
    return unwrap(api.get<ApiResponse<CatalogProductDetail>>(`/catalog/products/${productId}`), "Product could not be loaded.");
  },

  getFilters(categoryId?: string) {
    return unwrap(api.get<ApiResponse<CatalogFiltersPayload>>("/catalog/filters", { params: categoryId ? { category_id: categoryId } : undefined }), "Catalog filters could not be loaded.");
  },
};