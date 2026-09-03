import { api, type ApiResponse } from "@/app/lib/api/client";

export interface SellerProfile {
  id: string;
  account_id: string;
  business_name: string;
  business_description: string | null;
  status: "draft" | "pending_review" | "active" | "rejected" | "suspended" | "deactivated";
  rejection_reason: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SellerDocument {
  id: string;
  seller_id: string;
  document_type: "national_id_front" | "national_id_back" | "passport" | "driving_license";
  original_filename: string | null;
  mime_type: string;
  file_size: number;
  url: string;
  created_at: string;
}

export const sellerService = {
  async getMine(): Promise<SellerProfile> {
    const { data } = await api.get<ApiResponse<SellerProfile>>("/sellers/me");
    if (!data.data) throw new Error(data.message || "Seller profile not found.");
    return data.data;
  },
  async register(input: { business_name: string; business_description?: string }): Promise<SellerProfile> {
    const { data } = await api.post<ApiResponse<SellerProfile>>("/sellers", input);
    if (!data.data) throw new Error(data.message || "Seller profile could not be created.");
    return data.data;
  },
  async updateMine(input: { business_name: string; business_description?: string }): Promise<SellerProfile> {
    const { data } = await api.patch<ApiResponse<SellerProfile>>("/sellers/me", input);
    if (!data.data) throw new Error(data.message || "Seller profile could not be updated.");
    return data.data;
  },
  async submit(): Promise<SellerProfile> {
    const { data } = await api.post<ApiResponse<SellerProfile>>("/sellers/me/submit");
    if (!data.data) throw new Error(data.message || "Seller profile could not be submitted.");
    return data.data;
  },
  async deactivate(): Promise<SellerProfile> {
    const { data } = await api.post<ApiResponse<SellerProfile>>("/sellers/me/deactivate");
    if (!data.data) throw new Error(data.message || "Seller account could not be deactivated.");
    return data.data;
  },
  async reactivate(): Promise<SellerProfile> {
    const { data } = await api.post<ApiResponse<SellerProfile>>("/sellers/me/reactivate");
    if (!data.data) throw new Error(data.message || "Seller account could not be reactivated.");
    return data.data;
  },
  async listDocuments(): Promise<SellerDocument[]> {
    const { data } = await api.get<ApiResponse<SellerDocument[]>>("/sellers/me/documents");
    return data.data ?? [];
  },
  async getDocumentForReview(sellerId: string): Promise<SellerDocument[]> {
    const { data } = await api.get<ApiResponse<SellerDocument[]>>(`/sellers/${sellerId}/documents`);
    return data.data ?? [];
  },
  async uploadDocument(documentType: SellerDocument["document_type"], file: File): Promise<SellerDocument> {
    const body = new FormData();
    body.append("document_type", documentType);
    body.append("file", file);
    const { data } = await api.post<ApiResponse<SellerDocument>>("/sellers/me/documents", body, { headers: { "Content-Type": "multipart/form-data" } });
    if (!data.data) throw new Error(data.message || "Document upload failed.");
    return data.data;
  },
  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/sellers/me/documents/${documentId}`);
  },
};
