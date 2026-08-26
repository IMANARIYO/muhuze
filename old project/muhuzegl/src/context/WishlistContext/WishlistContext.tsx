import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { MarketplaceItem } from "../../types/marketplaceItem";

import { wishlistApiService } from "../../business/services/wishlistApiService";

import { useAuth } from "../AuthContext";

interface WishlistContextType {
  wishlist: MarketplaceItem[];

  addToWishlist: (
    item: MarketplaceItem
  ) => Promise<void>;

  removeFromWishlist: (
    id: string
  ) => Promise<void>;

  isInWishlist: (
    id: string
  ) => boolean;
}

const WishlistContext =
  createContext<
    WishlistContextType | undefined
  >(undefined);

interface Props {
  children: ReactNode;
}

export function WishlistProvider({
  children,
}: Props) {
  const { currentUser } = useAuth();

  const [wishlist, setWishlist] =
    useState<MarketplaceItem[]>([]);

  /*
   * Check whether a marketplace item
   * is valid before putting it into
   * the wishlist state.
   */
  function isValidMarketplaceItem(
    item: MarketplaceItem | null | undefined
  ): item is MarketplaceItem {
    return (
      item !== null &&
      item !== undefined &&
      typeof item._id === "string"
    );
  }

  /*
   * Load wishlist from backend
   * when the logged-in user changes.
   */
  useEffect(() => {
    async function loadWishlist() {
      if (!currentUser?._id) {
        setWishlist([]);
        return;
      }

      try {
        const data =
          await wishlistApiService.getWishlist(
            currentUser._id
          );

        /*
         * The backend may contain a wishlist
         * record whose marketplace item has
         * already been deleted.
         *
         * Remove those null/invalid items
         * before storing them in React state.
         */
        const validItems = data.filter(
          isValidMarketplaceItem
        );

        setWishlist(validItems);
      } catch (error) {
        console.error(
          "Failed to load wishlist:",
          error
        );

        setWishlist([]);
      }
    }

    loadWishlist();
  }, [currentUser?._id]);

  /*
   * Add item to wishlist
   */
  async function addToWishlist(
    item: MarketplaceItem
  ): Promise<void> {
    if (!currentUser?._id) {
      console.warn(
        "User must be logged in to save items."
      );

      return;
    }

    if (!isValidMarketplaceItem(item)) {
      console.warn(
        "Cannot add invalid marketplace item to wishlist."
      );

      return;
    }

    try {
      await wishlistApiService.addToWishlist(
        currentUser._id,
        item._id
      );

      setWishlist((current) => {
        const existing = current.find(
          (currentItem) =>
            currentItem?._id === item._id
        );

        if (existing) {
          return current;
        }

        return [...current, item];
      });
    } catch (error) {
      console.error(
        "Failed to add item to wishlist:",
        error
      );
    }
  }

  /*
   * Remove item from wishlist
   */
  async function removeFromWishlist(
    id: string
  ): Promise<void> {
    if (!currentUser?._id) {
      return;
    }

    try {
      await wishlistApiService.removeFromWishlist(
        currentUser._id,
        id
      );

      setWishlist((current) =>
        current.filter(
          (item) =>
            item !== null &&
            item !== undefined &&
            item._id !== id
        )
      );
    } catch (error) {
      console.error(
        "Failed to remove item from wishlist:",
        error
      );
    }
  }

  /*
   * Check if item is saved
   */
  function isInWishlist(
    id: string
  ): boolean {
    return wishlist.some(
      (item) =>
        item !== null &&
        item !== undefined &&
        item._id === id
    );
  }

  return (
    <WishlistContext.Provider
      value={{
        wishlist,

        addToWishlist,

        removeFromWishlist,

        isInWishlist,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  const context =
    useContext(WishlistContext);

  if (!context) {
    throw new Error(
      "useWishlist must be used inside WishlistProvider"
    );
  }

  return context;
}

export default WishlistContext;