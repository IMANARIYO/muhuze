import { api, type ApiResponse } from "@/app/lib/api/client";
import type { ProductRecord } from "@/app/services/product.service";
import type { SellerProfile } from "@/app/services/seller.service";

export interface CategoryRecord { id: string; parent_id: string | null; name: string; slug: string; description: string | null; image: string | null; sort_order: number; status: "active" | "inactive"; created_at: string; updated_at: string; }
export interface BrandRecord { id: string; name: string; slug: string; description: string | null; status: "active" | "inactive"; created_at: string; updated_at: string; }
export interface AttributeRecord { id: string; name: string; slug: string; input_type: "select" | "text" | "number" | "boolean"; unit: string | null; status: "active" | "inactive"; created_at: string; updated_at: string; }

async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>, fallback: string): Promise<T> {
  const { data } = await request;
  if (!data.data) throw new Error(data.message || fallback);
  return data.data;
}

export const adminService = {
  listSellers(status?: SellerProfile["status"]) { return unwrap(api.get<ApiResponse<SellerProfile[]>>("/sellers", { params: status ? { status } : undefined }), "Sellers could not be loaded."); },
  approveSeller(id: string) { return unwrap(api.post<ApiResponse<SellerProfile>>(`/sellers/${id}/approve`), "Seller could not be approved."); },
  rejectSeller(id: string, reason: string) { return unwrap(api.post<ApiResponse<SellerProfile>>(`/sellers/${id}/reject`, { reason }), "Seller could not be rejected."); },
  suspendSeller(id: string, reason?: string) { return unwrap(api.post<ApiResponse<SellerProfile>>(`/sellers/${id}/suspend`, reason ? { reason } : {}), "Seller could not be suspended."); },
  reactivateSeller(id: string) { return unwrap(api.post<ApiResponse<SellerProfile>>(`/sellers/${id}/reactivate`), "Seller could not be reactivated."); },
  listProducts(filters: { status?: string; search?: string } = {}) { return unwrap(api.get<ApiResponse<ProductRecord[]>>("/products", { params: Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== "all")) }), "Products could not be loaded."); },
  approveProduct(id: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/approve`), "Product could not be approved."); },
  rejectProduct(id: string, reason: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/reject`, { reason }), "Product could not be rejected."); },
  archiveProduct(id: string) { return unwrap(api.post<ApiResponse<ProductRecord>>(`/products/${id}/archive`), "Product could not be archived."); },
  listListings(status?: string) { return unwrap(api.get<ApiResponse<import("@/app/services/product.service").ListingRecord[]>>("/listings", { params: status ? { status } : undefined }), "Listings could not be loaded."); },
  approveListing(id: string) { return unwrap(api.post<ApiResponse<import("@/app/services/product.service").ListingRecord>>(`/listings/${id}/approve`), "Listing could not be approved."); },
  rejectListing(id: string, reason: string) { return unwrap(api.post<ApiResponse<import("@/app/services/product.service").ListingRecord>>(`/listings/${id}/reject`, { reason }), "Listing could not be rejected."); },
  suspendListing(id: string) { return unwrap(api.post<ApiResponse<import("@/app/services/product.service").ListingRecord>>(`/listings/${id}/suspend`), "Listing could not be suspended."); },
  reactivateListing(id: string) { return unwrap(api.post<ApiResponse<import("@/app/services/product.service").ListingRecord>>(`/listings/${id}/reactivate`), "Listing could not be reactivated."); },
  listCategories() { return unwrap(api.get<ApiResponse<CategoryRecord[]>>("/categories"), "Categories could not be loaded."); },
  createCategory(input: { name: string; description?: string; parent_id?: string; sort_order?: number }) { return unwrap(api.post<ApiResponse<CategoryRecord>>("/categories", input), "Category could not be created."); },
  updateCategory(id: string, input: { name: string; description?: string; sort_order?: number; status: "active" | "inactive" }) { return unwrap(api.patch<ApiResponse<CategoryRecord>>(`/categories/${id}`, input), "Category could not be updated."); },
  listBrands() { return unwrap(api.get<ApiResponse<BrandRecord[]>>("/brands"), "Brands could not be loaded."); },
  createBrand(input: { name: string; description?: string }) { return unwrap(api.post<ApiResponse<BrandRecord>>("/brands", input), "Brand could not be created."); },
  updateBrand(id: string, input: { name: string; description?: string; status: "active" | "inactive" }) { return unwrap(api.patch<ApiResponse<BrandRecord>>(`/brands/${id}`, input), "Brand could not be updated."); },
  listAttributes() { return unwrap(api.get<ApiResponse<AttributeRecord[]>>("/attributes"), "Attributes could not be loaded."); },
  createAttribute(input: { name: string; input_type?: AttributeRecord["input_type"]; unit?: string }) { return unwrap(api.post<ApiResponse<AttributeRecord>>("/attributes", input), "Attribute could not be created."); },
  updateAttribute(id: string, input: { name: string; input_type: AttributeRecord["input_type"]; unit?: string; status: "active" | "inactive" }) { return unwrap(api.patch<ApiResponse<AttributeRecord>>(`/attributes/${id}`, input), "Attribute could not be updated."); },
};
