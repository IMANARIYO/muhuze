import { api, type ApiResponse } from "@/app/lib/api/client";

export interface ProductRecord {
  id: string;
  category_id: string;
  brand_id: string | null;
  created_by_seller_id: string | null;
  name: string;
  slug: string;
  description: string | null;
  status: "draft" | "pending_review" | "active" | "rejected" | "archived";
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface VariantRecord {
  id: string;
  product_id: string;
  sku_code: string | null;
  status: "active" | "inactive";
  attribute_values: Array<{ attribute_id: string; value: string }>;
  created_at: string;
  updated_at: string;
}

export interface ListingRecord {
  id: string;
  seller_id: string;
  variant_id: string;
  price: number;
  stock: number;
  seller_sku: string | null;
  condition: "new" | "like_new" | "used";
  status: "draft" | "pending_review" | "active" | "rejected" | "suspended" | "out_of_stock" | "archived";
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const productService = {
  list(filters: { category_id?: string; brand_id?: string; status?: string; search?: string } = {}) {
    return unwrap(api.get<ApiResponse<ProductRecord[]>>("/products", { params: filters }), "Products could not be loaded.");
  },
  listMine() { return unwrap(api.get<ApiResponse<ProductRecord[]>>("/products/mine"), "Your product requests could not be loaded."); },
  create(input: { category_id: string; brand_id?: string; name: string; description?: string }) { return unwrap(api.post<ApiResponse<ProductRecord>>("/products", input), "Product could not be created."); },
  update(id: string, input: { category_id: string; brand_id?: string; name: string; description?: string }) { return unwrap(api.patch<ApiResponse<ProductRecord>>(`/products/${id}`, input), "Product could not be updated."); },
  submit(id: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/submit`), "Product could not be submitted."); },
  approve(id: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/approve`), "Product could not be approved."); },
  reject(id: string, reason: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/reject`, { reason }), "Product could not be rejected."); },
  archive(id: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/archive`), "Product could not be archived."); },
  listVariants(id: string) { return unwrap(api.get<ApiResponse<VariantRecord[]>>(`/products/${id}/variants`), "Variants could not be loaded."); },
  createVariant(id: string, input: { sku_code?: string; attribute_values: Array<{ attribute_id: string; value: string }> }) { return unwrap(api.post<ApiResponse<VariantRecord>>(`/products/${id}/variants`, input), "Variant could not be created."); },
  updateVariant(productId: string, variantId: string, input: { sku_code?: string; status: "active" | "inactive" }) { return unwrap(api.patch<ApiResponse<VariantRecord>>(`/products/${productId}/variants/${variantId}`, input), "Variant could not be updated."); },
  listProductImages(id: string) { return unwrap(api.get<ApiResponse<Array<{ id: string; product_id: string; url: string; is_primary: boolean; sort_order: number; created_at: string }>>>(`/products/${id}/images`), "Product images could not be loaded."); },
  uploadProductImage(id: string, file: File, isPrimary = false) { const body = new FormData(); body.append("file", file); body.append("is_primary", String(isPrimary)); return unwrap(api.post<ApiResponse<{ id: string; product_id: string; url: string; is_primary: boolean; sort_order: number; created_at: string }>>(`/products/${id}/images`, body, { headers: { "Content-Type": "multipart/form-data" } }), "Product image upload failed."); },
  deleteProductImage(productId: string, imageId: string) { return unwrap(api.delete<ApiResponse<null>>(`/products/${productId}/images/${imageId}`), "Product image could not be deleted."); },
  listListings(status?: string) { return unwrap(api.get<ApiResponse<ListingRecord[]>>("/listings", { params: status ? { status } : undefined }), "Listings could not be loaded."); },
  createListing(input: { variant_id: string; price: number; stock: number; seller_sku?: string; condition?: ListingRecord["condition"] }) { return unwrap(api.post<ApiResponse<ListingRecord>>("/listings", input), "Listing could not be created."); },
  updateListing(id: string, input: Partial<Pick<ListingRecord, "price" | "stock" | "seller_sku" | "condition">>) { return unwrap(api.patch<ApiResponse<ListingRecord>>(`/listings/${id}`, input), "Listing could not be updated."); },
  submitListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/submit`), "Listing could not be submitted."); },
  updateListingPrice(id: string, price: number) { return unwrap(api.patch<ApiResponse<ListingRecord>>(`/listings/${id}/price`, { price }), "Listing price could not be updated."); },
  updateListingStock(id: string, stock: number) { return unwrap(api.patch<ApiResponse<ListingRecord>>(`/listings/${id}/stock`, { stock }), "Listing stock could not be updated."); },
  approveListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/approve`), "Listing could not be approved."); },
  rejectListing(id: string, reason: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/reject`, { reason }), "Listing could not be rejected."); },
  suspendListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/suspend`), "Listing could not be suspended."); },
  reactivateListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/reactivate`), "Listing could not be reactivated."); },
  archiveListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/archive`), "Listing could not be archived."); },
  unarchiveListing(id: string) { return unwrap(api.post<ApiResponse<ListingRecord>>(`/listings/${id}/unarchive`), "Listing could not be unarchived."); },
  deleteListing(id: string) { return unwrap(api.delete<ApiResponse<null>>(`/listings/${id}`), "Listing could not be deleted."); },
};
