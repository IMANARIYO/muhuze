import type { IconType } from "react-icons";

export interface Seller {
  id: number;
  name: string;
  location: string;
  rating: number;
  products: number;
  avatar: string;
  verified: boolean;
  badge: IconType;
}