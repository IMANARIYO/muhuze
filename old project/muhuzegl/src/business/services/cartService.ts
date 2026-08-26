import type { CartItem } from "../../types/cart";

export class CartService {
  private storageKey = "cart";

  /**
   * Get all cart items
   */
  getAll(): CartItem[] {
    return JSON.parse(
      localStorage.getItem(this.storageKey) || "[]"
    );
  }

  /**
   * Save cart
   */
  private save(items: CartItem[]): void {
    localStorage.setItem(
      this.storageKey,
      JSON.stringify(items)
    );
  }

  /**
   * Add item to cart
   */
  add(item: CartItem): void {
    const items = this.getAll();

    const existing = items.find(
      (cartItem) =>
        cartItem.item._id === item.item._id
    );

    if (existing) {
      existing.quantity += item.quantity;
    } else {
      items.push(item);
    }

    this.save(items);
  }

  /**
   * Remove item
   */
  remove(itemId: string): void {
    const items = this.getAll().filter(
      (cartItem) =>
        cartItem.item._id !== itemId
    );

    this.save(items);
  }

  /**
   * Update quantity
   */
  updateQuantity(
    itemId: string,
    quantity: number
  ): void {
    const items = this.getAll();

    const item = items.find(
      (cartItem) =>
        cartItem.item._id === itemId
    );

    if (!item) return;

    item.quantity = quantity;

    this.save(items);
  }

  /**
   * Clear cart
   */
  clear(): void {
    localStorage.removeItem(this.storageKey);
  }

  /**
   * Total items
   */
  getItemCount(): number {
    return this.getAll().reduce(
      (total, item) => total + item.quantity,
      0
    );
  }

  /**
   * Total price
   */
  getTotalPrice(): number {
    return this.getAll().reduce(
      (total, item) =>
        total +
        item.item.price * item.quantity,
      0
    );
  }
}

export const cartService =
  new CartService();