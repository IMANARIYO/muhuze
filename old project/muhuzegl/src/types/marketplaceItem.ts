import type {
  ProductData,
  RentalData,
  ServiceData,
  JobData,
} from "./marketplaceForm";

export type MarketplaceItemType =
  | "product"
  | "rental"
  | "service"
  | "job";

export type MarketplaceItemStatus =
  | "draft"
  | "published"
  | "sold"
  | "rented"
  | "inactive";

export interface Seller {
  _id: string;
  fullName: string;
  email: string;
  phone: string;
  profileImage?: string;
}

/**
 * Returned from MongoDB
 */
export interface MarketplaceItem {
  _id: string;

  sellerId: string | Seller;

  title: string;

  description: string;

  marketplaceItemType: MarketplaceItemType;

  category: string;

  subCategory: string;

  images: string[];

  price: number;

  oldPrice?: number;

  currency: "RWF" | "USD";

  location: string;

  verified: boolean;

  featured: boolean;

  rating: number;

  reviews: number;

  status: MarketplaceItemStatus;

  details:
    | ProductData
    | RentalData
    | ServiceData
    | JobData;

  createdAt: string;

  updatedAt: string;
}

/**
 * Create Request
 */
export interface CreateMarketplaceItem {
  sellerId: string;

  title: string;

  description: string;

  marketplaceItemType: MarketplaceItemType;

  category: string;

  subCategory: string;

  images: File[];

  price: number;

  oldPrice?: number;

  currency: "RWF" | "USD";

  location: string;

  verified: boolean;

  featured: boolean;

  rating: number;

  reviews: number;

  status: MarketplaceItemStatus;

  details:
    | ProductData
    | RentalData
    | ServiceData
    | JobData;

  createdAt: string;

  updatedAt: string;
}

/**
 * Update Request
 */
export interface UpdateMarketplaceItem {
  _id: string;

  sellerId: string;

  title: string;

  description: string;

  marketplaceItemType: MarketplaceItemType;

  category: string;

  subCategory: string;

  // Existing images already stored
  images: string[];

  // New images selected by the user
  newImages: File[];

  price: number;

  oldPrice?: number;

  currency: "RWF" | "USD";

  location: string;

  verified: boolean;

  featured: boolean;

  rating: number;

  reviews: number;

  status: MarketplaceItemStatus;

  details:
    | ProductData
    | RentalData
    | ServiceData
    | JobData;

  updatedAt: string;
}