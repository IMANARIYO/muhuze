import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { CartItem } from "../../types/cart";
import type { MarketplaceItem } from "../../types/marketplaceItem";

import { cartApiService } from "../../business/services/cartApiService";
import { useAuth } from "../AuthContext";

interface CartContextType {
  cart: CartItem[];

  addToCart: (
    item: MarketplaceItem
  ) => Promise<void>;

  increaseQuantity: (
    id: string
  ) => Promise<void>;

  decreaseQuantity: (
    id: string
  ) => Promise<void>;

  removeFromCart: (
    id: string
  ) => Promise<void>;

  clearCart: () => Promise<void>;

  totalItems: number;

  totalPrice: number;

  refreshCart: () => Promise<void>;
}

const CartContext =
  createContext<CartContextType | undefined>(
    undefined
  );

interface Props {
  children: ReactNode;
}

export function CartProvider({
  children,
}: Props) {
  const { currentUser } = useAuth();

  const [cart, setCart] =
    useState<CartItem[]>([]);

  /*
   * Load cart from backend
   * whenever the logged-in user changes.
   */
  useEffect(() => {
    async function loadCart() {
      if (!currentUser?._id) {
        setCart([]);
        return;
      }

      try {
        const data =
          await cartApiService.getCart(
            currentUser._id
          );

        /*
         * Remove invalid cart items.
         *
         * This protects the application when
         * a marketplace product was deleted
         * but its cart reference still exists.
         */
        const validItems = data.filter(
          (cartItem) =>
            cartItem?.item !== null &&
            cartItem?.item !== undefined
        );

        setCart(validItems);
      } catch (error) {
        console.error(
          "Failed to load cart:",
          error
        );

        setCart([]);
      }
    }

    loadCart();
  }, [currentUser?._id]);

  /*
   * Refresh cart from backend
   */
  async function refreshCart() {
    if (!currentUser?._id) {
      setCart([]);
      return;
    }

    try {
      const data =
        await cartApiService.getCart(
          currentUser._id
        );

      /*
       * Only keep cart items whose
       * marketplace item still exists.
       */
      const validItems = data.filter(
        (cartItem) =>
          cartItem?.item !== null &&
          cartItem?.item !== undefined
      );

      setCart(validItems);
    } catch (error) {
      console.error(
        "Failed to refresh cart:",
        error
      );

      setCart([]);
    }
  }

  /*
   * Add item to cart
   */
  async function addToCart(
    item: MarketplaceItem
  ) {
    if (!currentUser?._id) {
      console.warn(
        "User must be logged in to add items to cart."
      );

      return;
    }

    try {
      await cartApiService.addToCart(
        currentUser._id,
        item._id,
        1
      );

      await refreshCart();
    } catch (error) {
      console.error(
        "Failed to add item to cart:",
        error
      );
    }
  }

  /*
   * Increase quantity
   */
  async function increaseQuantity(
    id: string
  ) {
    const existing = cart.find(
      (cartItem) =>
        cartItem?.item?._id === id
    );

    if (!existing) {
      return;
    }

    if (!currentUser?._id) {
      return;
    }

    try {
      await cartApiService.updateQuantity(
        currentUser._id,
        id,
        existing.quantity + 1
      );

      await refreshCart();
    } catch (error) {
      console.error(
        "Failed to increase quantity:",
        error
      );
    }
  }

  /*
   * Decrease quantity
   */
  async function decreaseQuantity(
    id: string
  ) {
    const existing = cart.find(
      (cartItem) =>
        cartItem?.item?._id === id
    );

    if (!existing) {
      return;
    }

    if (!currentUser?._id) {
      return;
    }

    if (existing.quantity > 1) {
      try {
        await cartApiService.updateQuantity(
          currentUser._id,
          id,
          existing.quantity - 1
        );

        await refreshCart();
      } catch (error) {
        console.error(
          "Failed to decrease quantity:",
          error
        );
      }
    }
  }

  /*
   * Remove item from cart
   */
  async function removeFromCart(
    id: string
  ) {
    if (!currentUser?._id) {
      return;
    }

    try {
      await cartApiService.removeFromCart(
        currentUser._id,
        id
      );

      await refreshCart();
    } catch (error) {
      console.error(
        "Failed to remove item from cart:",
        error
      );
    }
  }

  /*
   * Clear cart
   */
  async function clearCart() {
    if (!currentUser?._id) {
      setCart([]);
      return;
    }

    try {
      await cartApiService.clearCart(
        currentUser._id
      );

      await refreshCart();
    } catch (error) {
      console.error(
        "Failed to clear cart:",
        error
      );
    }
  }

  /*
   * Calculate total items
   */
  const totalItems = cart.reduce(
    (total, item) =>
      total + item.quantity,
    0
  );

  /*
   * Calculate total price
   *
   * Protect against a cart item whose
   * marketplace item is missing.
   */
  const totalPrice = cart.reduce(
    (total, item) => {
      if (!item?.item) {
        return total;
      }

      return (
        total +
        item.item.price * item.quantity
      );
    },
    0
  );

  return (
    <CartContext.Provider
      value={{
        cart,

        addToCart,

        increaseQuantity,

        decreaseQuantity,

        removeFromCart,

        clearCart,

        totalItems,

        totalPrice,

        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context =
    useContext(CartContext);

  if (!context) {
    throw new Error(
      "useCart must be used inside CartProvider."
    );
  }

  return context;
}

export default CartContext;