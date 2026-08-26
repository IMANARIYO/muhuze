import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { CreateMarketplaceItem, MarketplaceItem, UpdateMarketplaceItem, } from "../types/marketplaceItem";

import { marketplaceApiService } from "../business/services/marketplaceApiService";
/**
 * Context Interface
 */
interface MarketplaceContextType {
  items: MarketplaceItem[];

  createItem: (
  item: CreateMarketplaceItem
) => Promise<void>;
updateItem: (
  item:  UpdateMarketplaceItem
) => Promise<void>;

deleteItem: (
  id: string
) => Promise<void>;
 refreshItems: () => Promise<void>;

 getItemById: (
  id: string
) => Promise<MarketplaceItem>;
}

/**
 * Context
 */
const MarketplaceContext =
  createContext<MarketplaceContextType | null>(
    null
  );

/**
 * Provider Props
 */
interface Props {
  children: ReactNode;
}

/**
 * Provider
 */
export function MarketplaceProvider({
  children,
}: Props) {

  const [items, setItems] =
    useState<MarketplaceItem[]>([]);

  useEffect(() => {
  refreshItems();
  
}, []);

  async function refreshItems() {
  try {
    const data =
      await marketplaceApiService.getAll();

    setItems(data);
  } catch (error) {
    console.error(
      "Failed to load marketplace items:",
      error
    );
  }
}
async function getItemById(
  id: string
): Promise<MarketplaceItem> {
  return await marketplaceApiService.getById(id);
}

  async function createItem(
  item: CreateMarketplaceItem
) {
  await marketplaceApiService.create(item);

  await refreshItems();
}

  async function updateItem(
  item: UpdateMarketplaceItem
) {
  await marketplaceApiService.update(
    item._id,
    item
  );

  await refreshItems();
}

  async function deleteItem(
  id: string
) {
  await marketplaceApiService.delete(id);

  await refreshItems();
}
  return (
    <MarketplaceContext.Provider
      value={{
        items,
        createItem,
        updateItem,
        deleteItem,
        refreshItems,
        getItemById,
      }}
    >
      {children}
    </MarketplaceContext.Provider>
  );
}

/**
 * Hook
 */
export function useMarketplace() {

  const context =
    useContext(MarketplaceContext);

  if (!context) {
    throw new Error(
      "useMarketplace must be used inside MarketplaceProvider."
    );
  }

  return context;
}