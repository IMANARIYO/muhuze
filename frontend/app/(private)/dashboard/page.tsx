"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, CreditCard, Package, ShoppingBag, ShoppingCart, Store, Tag, TrendingUp, Users, Wallet } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { useAuth } from "@/app/context/auth-context";
import { adminService } from "@/app/services/admin.service";
import { cartService, type CartResponse } from "@/app/services/cart.service";
import { orderService, type OrderSummaryResponse } from "@/app/services/order.service";
import { productService, type ListingRecord } from "@/app/services/product.service";
import { revenueService, type RevenueLine, type RevenueTransactionResponse } from "@/app/services/revenue.service";
import { rwf } from "@/app/lib/utils";

const statusColors: Record<string, string> = {
  pending: "#edc35a",
  cancelled: "#ee765e",
  paid: "#39836e",
  failed: "#ee765e",
};

export default function DashboardOverview() {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const isSeller = hasRole("seller");

  const [clientOrders, setClientOrders] = useState<OrderSummaryResponse[]>([]);
  const [clientCart, setClientCart] = useState<CartResponse | null>(null);
  const [sellerEarnings, setSellerEarnings] = useState<RevenueLine[]>([]);
  const [sellerListings, setSellerListings] = useState<ListingRecord[]>([]);
  const [adminTxns, setAdminTxns] = useState<RevenueTransactionResponse[]>([]);
  const [adminProducts, setAdminProducts] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    async function init() {
      setLoading(true);
      setError("");
      try {
        if (isAdmin) {
          const [txns, products] = await Promise.all([revenueService.all(), adminService.listProducts()]);
          if (!cancelled) { setAdminTxns(txns); setAdminProducts(products.length); }
        } else if (isSeller) {
          const [earnings, listings] = await Promise.all([revenueService.mine(), productService.listListings()]);
          if (!cancelled) { setSellerEarnings(earnings); setSellerListings(listings); }
        } else {
          const [orders, cart] = await Promise.all([orderService.listMine(), cartService.get()]);
          if (!cancelled) { setClientOrders(orders); setClientCart(cart); }
        }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Data could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void init();
    return () => { cancelled = true; };
  }, [user, isAdmin, isSeller]);

  const releasedEarnings = sellerEarnings.filter((e) => e.status === "released");
  const heldEarnings = sellerEarnings.filter((e) => e.status === "held");
  const pendingPayouts = isAdmin ? adminTxns.filter((t) => t.status === "held") : heldEarnings;
  const totalGross = (isAdmin ? adminTxns : sellerEarnings).reduce((s, t) => s + t.amount, 0);
  const adminOrderCount = isAdmin ? new Set(adminTxns.map((t) => t.order_id)).size : 0;

  const displayName = user?.email?.split("@")[0] ?? "there";

  return (
    <div className="mx-auto max-w-6xl space-y-10">
      {/* Welcome */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.13em] text-[#93a09a]">
            {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--ink)] md:text-4xl">
            Welcome back, {displayName}
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {isAdmin ? "Here's what needs your attention across the marketplace." : "Here's what's happening with your account today."}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {isAdmin && (
            <Link href="/dashboard/sellers" className="flex items-center gap-1.5 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-xs font-bold text-[var(--ink)] hover:bg-[#f9fbf9] transition-colors">
              <Users size={13} /> Seller review
            </Link>
          )}
          {isSeller && !isAdmin && (
            <Link href="/dashboard/seller" className="flex items-center gap-1.5 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-xs font-bold text-[var(--ink)] hover:bg-[#f9fbf9] transition-colors">
              <Store size={13} /> Seller profile
            </Link>
          )}
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-14 text-center text-sm text-[var(--muted)]">Loading your dashboard…</div>
      ) : (
        <>
          {/* ── ADMIN VIEW ── */}
          {isAdmin && (
            <section>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Platform overview</p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card className="border-[#bdded1] bg-[#e8f4ed]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Gross volume</span>
                      <CreditCard size={16} className="text-[#59ac88]" />
                    </div>
                    <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalGross)}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">Cleared payments</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Orders paid</span>
                      <Package size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{adminOrderCount}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">Distinct orders</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Held payouts</span>
                      <Wallet size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{pendingPayouts.length}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">Awaiting buyer receipt</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Products</span>
                      <ShoppingBag size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{adminProducts}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">In catalog</p>
                  </CardContent>
                </Card>
              </div>

              {/* Quick actions */}
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <Link href="/dashboard/sellers" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#fbf0ce] text-[#b58a24]"><Users size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">Seller review</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Approve or reject seller applications</p>
                </Link>
                <Link href="/dashboard/products" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e4edfa] text-[#577ebd]"><Package size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">Product review</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Approve catalog product requests</p>
                </Link>
                <Link href="/dashboard/listings" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e8f4ed] text-[#2d7a5e]"><Tag size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">Listing review</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Approve seller listing submissions</p>
                </Link>
              </div>
            </section>
          )}

          {/* ── SELLER VIEW ── */}
          {isSeller && !isAdmin && (
            <section>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Seller overview</p>
              <div className="grid gap-4 sm:grid-cols-3">
                <Card className="border-[#bdded1] bg-[#e8f4ed]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Released</span>
                      <Wallet size={16} className="text-[#59ac88]" />
                    </div>
                    <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
                      {rwf(releasedEarnings.reduce((s, e) => s + e.seller_earning, 0))}
                    </p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">After commission</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Held</span>
                      <TrendingUp size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
                      {rwf(heldEarnings.reduce((s, e) => s + e.seller_earning, 0))}
                    </p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">Awaiting receipt</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">My listings</span>
                      <Store size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{sellerListings.length}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">
                      {sellerListings.filter((l) => l.status === "active").length} active
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Seller quick actions */}
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <Link href="/dashboard/seller" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e8f4ed] text-[#2d7a5e]"><Store size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">Seller profile</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Manage your business profile and documents</p>
                </Link>
                <Link href="/dashboard/listings" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#fbf0ce] text-[#b58a24]"><Tag size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">My listings</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Prices, stock, and review status</p>
                </Link>
                <Link href="/dashboard/orders" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e4edfa] text-[#577ebd]"><Package size={17} /></div>
                    <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
                  </div>
                  <p className="mt-3 font-bold text-[var(--ink)]">Orders received</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">Accept, ship, and deliver orders</p>
                </Link>
              </div>
            </section>
          )}

          {/* ── CLIENT VIEW ── */}
          {!isAdmin && !isSeller && (
            <section>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Overview</p>
              <div className="grid gap-4 sm:grid-cols-3">
                <Card className="border-[#bdded1] bg-[#e8f4ed]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">My Orders</span>
                      <Package size={16} className="text-[#59ac88]" />
                    </div>
                    <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{clientOrders.length}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">
                      <b className="text-[#4fa67d]">{clientOrders.filter((o) => o.status === "pending" && o.payment_status !== "paid").length} waiting for payment</b>
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#78857f]">Cart Items</span>
                      <ShoppingCart size={16} className="text-[#a7b0aa]" />
                    </div>
                    <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{clientCart?.item_count ?? 0}</p>
                    <p className="mt-1 text-[11px] text-[#9aa39e]">Ready to checkout</p>
                  </CardContent>
                </Card>
                <Link href="/dashboard/cart" className="group">
                  <Card>
                    <CardContent className="p-6 flex flex-col justify-between h-full">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-[#78857f]">Cart total</span>
                        <ArrowRight size={16} className="text-[#a7b0aa] group-hover:text-[var(--teal)] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <div>
                        <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(clientCart?.total ?? 0)}</p>
                        <p className="mt-1 text-[11px] text-[#9aa39e]">Go to checkout</p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </div>

              <Card className="mt-4">
                <CardContent className="p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-[var(--ink)]">Recent Orders</h2>
                    <Link href="/dashboard/orders" className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline">
                      View all <ArrowRight size={12} />
                    </Link>
                  </div>
                  {clientOrders.length === 0 ? (
                    <p className="py-4 text-center text-xs text-[var(--muted)]">
                      No orders yet — browse the shop and place your first order.
                    </p>
                  ) : (
                    <div className="divide-y divide-[#eff1ef]">
                      {clientOrders.slice(0, 3).map((order) => (
                        <div key={order.id} className="flex items-center gap-3 py-3">
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-xs font-bold text-[var(--ink)]">{order.order_number}</p>
                            <p className="text-[10px] text-[var(--muted)]">{new Date(order.created_at).toLocaleDateString()}</p>
                          </div>
                          <span className="text-xs font-bold text-[var(--ink)]">{rwf(order.total_amount)}</span>
                          <span
                            className="rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize"
                            style={{ backgroundColor: `${statusColors[order.payment_status] ?? "#edc35a"}22`, color: statusColors[order.payment_status] ?? "#b58a24" }}
                          >
                            {order.payment_status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </section>
          )}
        </>
      )}
    </div>
  );
}