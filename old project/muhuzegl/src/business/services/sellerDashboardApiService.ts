const API_BASE_URL = "http://localhost:5000";

export interface SellerDashboardStats {
  totalListings: number;
  activeListings: number;
  totalOrders: number;
  pendingOrders: number;
  acceptedOrders: number;
  rejectedOrders: number;
  revenue: number;
}

interface SellerDashboardResponse {
  success: boolean;
  data: SellerDashboardStats;
  message?: string;
}

class SellerDashboardApiService {
  async getDashboard(
    sellerId: string
  ): Promise<SellerDashboardStats> {
    const response = await fetch(
      `${API_BASE_URL}/api/seller/${sellerId}/dashboard`
    );

    const result =
      (await response.json()) as SellerDashboardResponse;

    if (!response.ok || !result.success) {
      throw new Error(
        result.message ||
          "Failed to load seller dashboard."
      );
    }

    return result.data;
  }
}

export const sellerDashboardApiService =
  new SellerDashboardApiService();