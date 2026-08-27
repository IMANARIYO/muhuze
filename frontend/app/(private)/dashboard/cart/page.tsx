"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle, Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import type { CartItem } from "@/app/lib/types";

const initialCart: CartItem[] = [
  { productId: "p3", productName: "Shea Butter Moisturizer", price: 9.99, quantity: 1, unit: "100ml", sellerName: "Sarah Nkosi" },
  { productId: "p6", productName: "Beaded Maasai Bracelet", price: 14.0, quantity: 2, unit: "piece", sellerName: "David Mugisha" },
];

export default function CartPage() {
  const [cart, setCart] = useState<CartItem[]>(initialCart);
  const [checkedOut, setCheckedOut] = useState(false);

  const updateQty = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) =>
          item.productId === productId
            ? { ...item, quantity: Math.max(0, item.quantity + delta) }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  };

  const remove = (productId: string) =>
    setCart((prev) => prev.filter((i) => i.productId !== productId));

  const subtotal = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  const commission = subtotal * 0.1;
  const total = subtotal;

  if (checkedOut) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#e8f4ed] text-[var(--teal)]">
          <CheckCircle size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Payment Successful!</h2>
        <p className="text-sm text-[var(--muted)]">
          Your order has been placed. The seller will be notified and admin will process the payout.
        </p>
        <Link href="/dashboard/orders">
          <Button className="mt-2">View My Orders <ArrowRight size={14} /></Button>
        </Link>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#f2f5f2] text-[var(--muted)]">
          <ShoppingBag size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Your cart is empty</h2>
        <Link href="/dashboard/products">
          <Button>Browse Products</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">My Cart</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">{cart.length} item{cart.length !== 1 ? "s" : ""} in your cart</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          {cart.map((item) => (
            <Card key={item.productId}>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
                  <ShoppingBag size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-[var(--ink)]">{item.productName}</p>
                  <p className="text-[10px] text-[var(--muted)]">
                    by {item.sellerName}{item.unit ? ` · ${item.unit}` : ""}
                  </p>
                  <p className="mt-0.5 text-xs font-bold text-[var(--ink)]">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateQty(item.productId, -1)}
                    className="grid h-7 w-7 place-items-center rounded-lg border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)]"
                  >
                    <Minus size={12} />
                  </button>
                  <span className="w-5 text-center text-sm font-bold text-[var(--ink)]">{item.quantity}</span>
                  <button
                    onClick={() => updateQty(item.productId, 1)}
                    className="grid h-7 w-7 place-items-center rounded-lg border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)]"
                  >
                    <Plus size={12} />
                  </button>
                </div>
                <button
                  onClick={() => remove(item.productId)}
                  className="ml-2 text-[var(--muted)] hover:text-[var(--coral)]"
                  aria-label="Remove item"
                >
                  <Trash2 size={15} />
                </button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Order summary */}
        <Card className="h-fit">
          <CardContent className="p-6 space-y-4">
            <h2 className="text-sm font-bold text-[var(--ink)]">Order Summary</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-[var(--muted)]">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[var(--muted)]">
                <span>Platform fee (10%)</span>
                <span>${commission.toFixed(2)}</span>
              </div>
              <div className="my-2 border-t border-[var(--line)]" />
              <div className="flex justify-between font-bold text-[var(--ink)]">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
            <button
              onClick={() => setCheckedOut(true)}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] py-2.5 text-sm font-bold text-white transition-all hover:-translate-y-0.5 hover:bg-[#2e3d38]"
            >
              Complete Payment <ArrowRight size={15} />
            </button>
            <Link href="/dashboard/products">
              <button className="w-full rounded-lg border border-[var(--line)] py-2 text-xs font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
                Continue Shopping
              </button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
