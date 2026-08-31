"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LogOut, Menu, ShoppingCart, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { useAuth } from "@/app/context/auth-context";
import { cartService } from "@/app/services/cart.service";
import { CART_UPDATED_EVENT } from "@/app/lib/utils";

const CART_POLL_INTERVAL = 30_000;

function useCartCount(enabled: boolean): number | null {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const refresh = async () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      try {
        const cart = await cartService.get();
        if (!cancelled) setCount(cart.item_count);
      } catch {
        if (!cancelled) setCount(0);
      }
    };

    void refresh();
    const interval = window.setInterval(() => void refresh(), CART_POLL_INTERVAL);
    const onChanged = () => void refresh();
    window.addEventListener(CART_UPDATED_EVENT, onChanged);
    window.addEventListener("focus", onChanged);
    window.addEventListener("visibilitychange", onChanged);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      window.removeEventListener(CART_UPDATED_EVENT, onChanged);
      window.removeEventListener("focus", onChanged);
      window.removeEventListener("visibilitychange", onChanged);
    };
  }, [enabled]);

  return count;
}

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, logout } = useAuth();
  const cartCount = useCartCount(isAuthenticated);

  async function handleLogout() {
    await logout();
    setMobileOpen(false);
  }

  const cartButton = (
    <Link
      href="/dashboard/cart"
      aria-label={cartCount ? `Open cart (${cartCount} items)` : "Open cart"}
      title={cartCount ? `Cart · ${cartCount} item${cartCount === 1 ? "" : "s"}` : "Cart"}
      className="relative grid h-9 w-9 place-items-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[#edf1ed] hover:text-[var(--ink)]"
    >
      <ShoppingCart size={19} />
      {isAuthenticated && cartCount != null && cartCount > 0 && (
        <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-[var(--coral)] px-1 text-[9px] font-bold text-white">
          {cartCount > 99 ? "99+" : cartCount}
        </span>
      )}
    </Link>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--line)] bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-[14px] font-extrabold text-[#d6f34d] -rotate-6">
            M
          </div>
          <span className="text-xl font-extrabold tracking-tight text-[var(--ink)]">
            muhuze<span className="text-[var(--coral)]">.</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-7 md:flex">
          <Link
            href="/products"
            className="text-sm font-medium text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
          >
            Shop
          </Link>
          <a
            href="#how-it-works"
            className="text-sm font-medium text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
          >
            How It Works
          </a>
          <a
            href="#how-it-works"
            className="text-sm font-medium text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
          >
            For Sellers
          </a>
        </nav>

        <div className="flex items-center gap-1.5">
          {cartButton}

          <div className="hidden items-center gap-3 md:flex">
            {isAuthenticated ? (
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut size={14} /> Log out
              </Button>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">Log in</Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">Get Started</Button>
                </Link>
              </>
            )}
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </Button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-[var(--line)] bg-white px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            <Link
              href="/products"
              className="text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)]"
              onClick={() => setMobileOpen(false)}
            >
              Shop
            </Link>
            <a
              href="#how-it-works"
              className="text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)]"
              onClick={() => setMobileOpen(false)}
            >
              How It Works
            </a>
            <a
              href="#how-it-works"
              className="text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)]"
              onClick={() => setMobileOpen(false)}
            >
              For Sellers
            </a>
            <hr className="border-[var(--line)]" />
            {isAuthenticated ? (
              <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
                <LogOut size={15} /> Log out
              </Button>
            ) : (
              <>
                <Link href="/login" onClick={() => setMobileOpen(false)}>
                  <Button variant="ghost" size="sm" className="w-full justify-start">Log in</Button>
                </Link>
                <Link href="/register" onClick={() => setMobileOpen(false)}>
                  <Button size="sm" className="w-full">Get Started</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}