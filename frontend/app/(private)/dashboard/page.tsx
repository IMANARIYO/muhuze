"use client";

import Link from "next/link";
import { ArrowRight, CreditCard, Layers, Package, ShoppingBag, ShoppingCart, Store, Tag, TrendingUp, Users, Wallet } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { useAuth } from "@/app/context/auth-context";
// orders/payments/earnings use dummy data — real APIs not yet mounted (orders, payments, revenue modules)
import { orders, payments, products, earnings } from "@/app/lib/data";

const statusColors: Record<string, string> = {
  pending: "#edc35a",
  processing: "#6d9bdb",
  shipped: "#31a59a",
  delivered: "#39836e",
  cancelled: "#ee765e",
};

export default function DashboardOverview() {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const isSeller = hasRole("seller");

  const clientOrders = orders.filter((o) => o.clientId === "u1");
  const sellerEarnings = earnings.filter((e) => e.payoutStatus === "sent");
  const pendingPayouts = payments.filter((p) => p.payoutStatus === "pending");
  const totalRevenue = payments.filter((p) => p.status === "completed").reduce((s, p) => s + p.amount, 0);

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

      {/* ── ADMIN VIEW ── */}
      {isAdmin && (
        <section>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Platform overview</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-[#bdded1] bg-[#e8f4ed]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Total Revenue</span>
                  <CreditCard size={16} className="text-[#59ac88]" />
                </div>
                <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">${totalRevenue.toFixed(2)}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Completed payments</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">All Orders</span>
                  <Package size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{orders.length}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">{orders.filter((o) => o.status === "pending").length} pending</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Pending Payouts</span>
                  <Wallet size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{pendingPayouts.length}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Need to be sent</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Products</span>
                  <ShoppingBag size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{products.length}</p>
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

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Link href="/dashboard/catalog" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
              <div className="flex items-center justify-between">
                <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#f2f5f2] text-[var(--muted)]"><Layers size={17} /></div>
                <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
              </div>
              <p className="mt-3 font-bold text-[var(--ink)]">Catalog setup</p>
              <p className="mt-1 text-xs text-[var(--muted)]">Manage categories, brands, and attributes</p>
            </Link>
            <Link href="/dashboard/payments" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
              <div className="flex items-center justify-between">
                <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#fbe6e0] text-[#b74d3b]"><CreditCard size={17} /></div>
                <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
              </div>
              <p className="mt-3 font-bold text-[var(--ink)]">Payments</p>
              <p className="mt-1 text-xs text-[var(--muted)]">Manage payouts and payment records</p>
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
                  <span className="text-xs text-[#78857f]">Total Earned</span>
                  <Wallet size={16} className="text-[#59ac88]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
                  ${sellerEarnings.reduce((s, e) => s + e.netAmount, 0).toFixed(2)}
                </p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">After commission</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Pending Payout</span>
                  <TrendingUp size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
                  ${earnings.filter((e) => e.payoutStatus === "pending").reduce((s, e) => s + e.netAmount, 0).toFixed(2)}
                </p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Awaiting admin payout</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Products Available</span>
                  <Store size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{products.length}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">In catalog</p>
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
            <Link href="/dashboard/products" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
              <div className="flex items-center justify-between">
                <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e4edfa] text-[#577ebd]"><Package size={17} /></div>
                <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
              </div>
              <p className="mt-3 font-bold text-[var(--ink)]">My products</p>
              <p className="mt-1 text-xs text-[var(--muted)]">Request and track catalog products</p>
            </Link>
            <Link href="/dashboard/listings" className="group rounded-xl border border-[var(--line)] bg-white p-5 hover:border-[var(--teal)] transition-colors">
              <div className="flex items-center justify-between">
                <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#fbf0ce] text-[#b58a24]"><Tag size={17} /></div>
                <ArrowRight size={14} className="text-[var(--muted)] group-hover:text-[var(--teal)] transition-colors" />
              </div>
              <p className="mt-3 font-bold text-[var(--ink)]">My listings</p>
              <p className="mt-1 text-xs text-[var(--muted)]">Create and manage your product listings</p>
            </Link>
          </div>
        </section>
      )}

      {/* ── CLIENT VIEW ── */}
      {!isAdmin && (
        <section>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">
            {isSeller ? "Buyer overview" : "Overview"}
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card className="border-[#bdded1] bg-[#e8f4ed]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">My Orders</span>
                  <Package size={16} className="text-[#59ac88]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{clientOrders.length}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">
                  <b className="text-[#4fa67d]">{clientOrders.filter((o) => o.status === "delivered").length} delivered</b>
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Cart Items</span>
                  <ShoppingCart size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">2</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Ready to checkout</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#78857f]">Products Available</span>
                  <ShoppingBag size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{products.length}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Across all categories</p>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-4">
            <CardContent className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-[var(--ink)]">Recent Orders</h2>
                <Link href="/dashboard/orders" className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline">
                  View all <ArrowRight size={12} />
                </Link>
              </div>
              <div className="divide-y divide-[#eff1ef]">
                {clientOrders.slice(0, 3).map((order) => (
                  <div key={order.id} className="flex items-center gap-3 py-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-[var(--ink)] truncate">
                        {order.items.map((i) => i.productName).join(", ")}
                      </p>
                      <p className="text-[10px] text-[var(--muted)]">{order.sellerName} · {order.createdAt}</p>
                    </div>
                    <span className="text-xs font-bold text-[var(--ink)]">${order.total.toFixed(2)}</span>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize"
                      style={{ backgroundColor: `${statusColors[order.status]}22`, color: statusColors[order.status] }}
                    >
                      {order.status}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
}
