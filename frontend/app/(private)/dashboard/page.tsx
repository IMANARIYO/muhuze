import Link from "next/link";
import {
  ArrowRight,
  CreditCard,
  Package,
  ShoppingBag,
  ShoppingCart,
  Store,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Badge } from "@/app/_components/ui/badge";
import { orders, payments, products, earnings, users } from "@/app/lib/data";

const statusColors: Record<string, string> = {
  pending: "#edc35a",
  processing: "#6d9bdb",
  shipped: "#31a59a",
  delivered: "#39836e",
  cancelled: "#ee765e",
};

export default function DashboardOverview() {
  const clientOrders = orders.filter((o) => o.clientId === "u1");
  const sellerProducts = products.filter((p) => p.sellerId === "u2");
  const sellerEarnings = earnings.filter((e) => e.payoutStatus === "sent");
  const pendingPayouts = payments.filter((p) => p.payoutStatus === "pending");
  const totalRevenue = payments.filter((p) => p.status === "completed").reduce((s, p) => s + p.amount, 0);

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Welcome */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.13em] text-[#93a09a]">
            {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--ink)] md:text-4xl">
            Welcome back, Amina
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Here&apos;s what&apos;s happening across the marketplace today.
          </p>
        </div>
      </div>

      {/* ── CLIENT VIEW ── */}
      <section>
        <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Client Overview</p>
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

        {/* Recent orders */}
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

      {/* ── SELLER VIEW ── */}
      <section>
        <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Seller Overview</p>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="border-[#bdded1] bg-[#e8f4ed]">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#78857f]">My Products</span>
                <Store size={16} className="text-[#59ac88]" />
              </div>
              <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{sellerProducts.length}</p>
              <p className="mt-1 text-[11px] text-[#9aa39e]">Active listings</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#78857f]">Total Earned</span>
                <Wallet size={16} className="text-[#a7b0aa]" />
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
        </div>

        <Card className="mt-4">
          <CardContent className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-bold text-[var(--ink)]">My Products</h2>
              <Link href="/dashboard/products" className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline">
                Manage <ArrowRight size={12} />
              </Link>
            </div>
            <div className="divide-y divide-[#eff1ef]">
              {sellerProducts.slice(0, 3).map((p) => (
                <div key={p.id} className="flex items-center gap-3 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-[var(--ink)]">{p.name}</p>
                    <p className="text-[10px] text-[var(--muted)]">{p.category} · Stock: {p.stock}</p>
                  </div>
                  <span className="text-xs font-bold text-[var(--ink)]">${p.price.toFixed(2)}{p.unit ? ` / ${p.unit}` : ""}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ── ADMIN VIEW ── */}
      <section>
        <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">Admin Overview</p>
        <div className="grid gap-4 sm:grid-cols-4">
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
                <span className="text-xs text-[#78857f]">Total Users</span>
                <Users size={16} className="text-[#a7b0aa]" />
              </div>
              <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{users.length}</p>
              <p className="mt-1 text-[11px] text-[#9aa39e]">{users.filter((u) => u.role === "seller").length} sellers</p>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-4">
          <CardContent className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-bold text-[var(--ink)]">Pending Payouts</h2>
              <Link href="/dashboard/payments" className="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)] hover:underline">
                View all <ArrowRight size={12} />
              </Link>
            </div>
            <div className="divide-y divide-[#eff1ef]">
              {pendingPayouts.map((pay) => (
                <div key={pay.id} className="flex items-center gap-3 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-[var(--ink)]">Order #{pay.orderId}</p>
                    <p className="text-[10px] text-[var(--muted)]">{pay.clientName} → {pay.sellerName}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-bold text-[var(--ink)]">${pay.sellerPayout.toFixed(2)}</p>
                    <p className="text-[10px] text-[var(--muted)]">Commission: ${pay.commission.toFixed(2)}</p>
                  </div>
                  <Badge variant="outline">{pay.payoutStatus}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
