import { Package } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { orders } from "@/app/lib/data";

const statusColors: Record<string, { bg: string; text: string }> = {
  pending:    { bg: "#fbf0ce", text: "#b58a24" },
  processing: { bg: "#e4edfa", text: "#577ebd" },
  shipped:    { bg: "#d5f2e2", text: "#39836e" },
  delivered:  { bg: "#e8f4ed", text: "#2d7a5e" },
  cancelled:  { bg: "#fbe6e0", text: "#d75e4a" },
};

const paymentColors: Record<string, { bg: string; text: string }> = {
  pending:   { bg: "#fbf0ce", text: "#b58a24" },
  completed: { bg: "#e8f4ed", text: "#2d7a5e" },
  refunded:  { bg: "#fbe6e0", text: "#d75e4a" },
};

export default function OrdersPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Orders</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Track all orders and their current status.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        {(["all", "pending", "processing", "shipped", "delivered"] as const).map((s) => (
          <button
            key={s}
            className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-[11px] font-semibold capitalize text-[var(--muted)] transition-colors hover:border-[var(--teal)] hover:text-[var(--teal)]"
          >
            {s === "all"
              ? `All (${orders.length})`
              : `${s} (${orders.filter((o) => o.status === s).length})`}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {orders.map((order) => {
          const sc = statusColors[order.status];
          const pc = paymentColors[order.paymentStatus];
          return (
            <Card key={order.id} className="transition-shadow hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
                      <Package size={18} />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[var(--ink)]">Order #{order.id}</p>
                      <p className="text-[10px] text-[var(--muted)]">{order.createdAt}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                      style={{ backgroundColor: sc.bg, color: sc.text }}
                    >
                      {order.status}
                    </span>
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                      style={{ backgroundColor: pc.bg, color: pc.text }}
                    >
                      {order.paymentStatus}
                    </span>
                  </div>
                </div>

                <div className="mt-4 divide-y divide-[#eff1ef]">
                  {order.items.map((item) => (
                    <div key={item.productId} className="flex items-center justify-between py-2">
                      <div>
                        <p className="text-xs font-semibold text-[var(--ink)]">{item.productName}</p>
                        <p className="text-[10px] text-[var(--muted)]">
                          Qty: {item.quantity}{item.unit ? ` ${item.unit}` : ""} · by {item.sellerName}
                        </p>
                      </div>
                      <span className="text-xs font-bold text-[var(--ink)]">
                        ${(item.price * item.quantity).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-3 flex items-center justify-between border-t border-[#eff1ef] pt-3">
                  <div>
                    <p className="text-[10px] text-[var(--muted)]">Client: {order.clientName}</p>
                    <p className="text-[10px] text-[var(--muted)]">Seller: {order.sellerName}</p>
                  </div>
                  <p className="text-sm font-extrabold text-[var(--ink)]">
                    Total: ${order.total.toFixed(2)}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
