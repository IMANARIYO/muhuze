import type {
  MarketplaceItem,
  CreateMarketplaceItem,
  UpdateMarketplaceItem,
} from "../../types/marketplaceItem";

const API_URL = "http://localhost:5000/api/marketplace";

export class MarketplaceApiService {
  /**
   * ==========================================
   * GET ALL MARKETPLACE ITEMS
   * ==========================================
   */
  async getAll(): Promise<MarketplaceItem[]> {
    const response = await fetch(API_URL);

    if (!response.ok) {
      const errorText = await response.text();

      throw new Error(
        `Failed to load marketplace items: ${response.status} ${errorText}`
      );
    }

    const result = await response.json();

    return result.data ?? [];
  }

  /**
   * ==========================================
   * GET SINGLE MARKETPLACE ITEM
   * ==========================================
   */
  async getById(
    id: string
  ): Promise<MarketplaceItem> {
    const response = await fetch(
      `${API_URL}/${id}`
    );

    if (!response.ok) {
      const errorText = await response.text();

      throw new Error(
        `Failed to load marketplace item: ${response.status} ${errorText}`
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * ==========================================
   * CREATE MARKETPLACE ITEM
   * ==========================================
   */
  async create(
    item: CreateMarketplaceItem
  ): Promise<MarketplaceItem> {
    const formData = new FormData();

    /*
     * BASIC INFORMATION
     */
    formData.append(
      "sellerId",
      item.sellerId
    );

    formData.append(
      "title",
      item.title
    );

    formData.append(
      "description",
      item.description
    );

    /*
     * MARKETPLACE TYPE
     */
    formData.append(
      "marketplaceItemType",
      item.marketplaceItemType
    );

    /*
     * CATEGORY
     */
    formData.append(
      "category",
      item.category
    );

    formData.append(
      "subCategory",
      item.subCategory
    );

    /*
     * PRICE
     */
    formData.append(
      "price",
      item.price.toString()
    );

    formData.append(
      "currency",
      item.currency
    );

    /*
     * LOCATION
     */
    formData.append(
      "location",
      item.location
    );

    /*
     * MARKETPLACE STATUS
     */
    formData.append(
      "verified",
      String(item.verified)
    );

    formData.append(
      "featured",
      String(item.featured)
    );

    formData.append(
      "rating",
      item.rating.toString()
    );

    formData.append(
      "reviews",
      item.reviews.toString()
    );

    formData.append(
      "status",
      item.status
    );

    /*
     * DETAILS
     */
    formData.append(
      "details",
      JSON.stringify(item.details)
    );

    /*
     * IMAGES
     */
    item.images.forEach((image) => {
      formData.append(
        "images",
        image
      );
    });

    /*
     * SEND REQUEST
     */
    const response = await fetch(
      API_URL,
      {
        method: "POST",
        body: formData,
      }
    );

    /*
     * HANDLE BACKEND ERRORS
     */
    if (!response.ok) {
      const errorText =
        await response.text();

      throw new Error(
        `Failed to create marketplace item: ${response.status} ${errorText}`
      );
    }

    const result =
      await response.json();

    return result.data;
  }

  /**
   * ==========================================
   * UPDATE MARKETPLACE ITEM
   * ==========================================
   */
  async update(
    id: string,
    item: UpdateMarketplaceItem
  ): Promise<MarketplaceItem> {
    const formData =
      new FormData();

    /*
     * BASIC INFORMATION
     */
    formData.append(
      "sellerId",
      item.sellerId
    );

    formData.append(
      "title",
      item.title
    );

    formData.append(
      "description",
      item.description
    );

    /*
     * MARKETPLACE TYPE
     */
    formData.append(
      "marketplaceItemType",
      item.marketplaceItemType
    );

    /*
     * CATEGORY
     */
    formData.append(
      "category",
      item.category
    );

    formData.append(
      "subCategory",
      item.subCategory
    );

    /*
     * PRICE
     */
    formData.append(
      "price",
      item.price.toString()
    );

    formData.append(
      "currency",
      item.currency
    );

    /*
     * LOCATION
     */
    formData.append(
      "location",
      item.location
    );

    /*
     * MARKETPLACE STATUS
     */
    formData.append(
      "verified",
      String(item.verified)
    );

    formData.append(
      "featured",
      String(item.featured)
    );

    formData.append(
      "rating",
      item.rating.toString()
    );

    formData.append(
      "reviews",
      item.reviews.toString()
    );

    formData.append(
      "status",
      item.status
    );

    /*
     * DETAILS
     */
    formData.append(
      "details",
      JSON.stringify(item.details)
    );

    /*
     * EXISTING IMAGES
     *
     * These are images already stored
     * in MongoDB.
     */
    formData.append(
      "existingImages",
      JSON.stringify(
        item.images
      )
    );

    /*
     * NEW IMAGES
     */
    item.newImages.forEach(
      (image) => {
        formData.append(
          "images",
          image
        );
      }
    );

    /*
     * SEND REQUEST
     */
    const response =
      await fetch(
        `${API_URL}/${id}`,
        {
          method: "PUT",
          body: formData,
        }
      );

    /*
     * HANDLE BACKEND ERRORS
     */
    if (!response.ok) {
      const errorText =
        await response.text();

      throw new Error(
        `Failed to update marketplace item: ${response.status} ${errorText}`
      );
    }

    const result =
      await response.json();

    return result.data;
  }

  /**
   * ==========================================
   * DELETE MARKETPLACE ITEM
   * ==========================================
   */
  async delete(
    id: string
  ): Promise<void> {
    const response =
      await fetch(
        `${API_URL}/${id}`,
        {
          method: "DELETE",
        }
      );

    if (!response.ok) {
      const errorText =
        await response.text();

      throw new Error(
        `Failed to delete marketplace item: ${response.status} ${errorText}`
      );
    }
  }
}

/**
 * ==========================================
 * SINGLE API SERVICE INSTANCE
 * ==========================================
 */
export const marketplaceApiService =
  new MarketplaceApiService();