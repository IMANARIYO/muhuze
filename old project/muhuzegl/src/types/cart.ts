import type { MarketplaceItem } from "./marketplaceItem";

export interface CartItem {
  item: MarketplaceItem;
  quantity: number;
}