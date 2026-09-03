"use client";

import { useEffect, useState } from "react";
import { CheckCircle, Package, Send, Smartphone, Truck, X } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { useRole } from "@/app/(private)/_components/role-context";
import { orderService, type OrderDetailResponse, type OrderSummaryResponse, type SellerOrderResponse } from "@/app/services/order.service";
import { paymentService, type PaymentResponse } from "@/app/services/payment.service";
import { revenueService, type RevenueLine, type RevenueSummaryResponse, type RevenueTransactionResponse } from "@/app/services/revenue.service";
import { rwf } from "@/app/lib/utils";

const statusColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: "#fbf0ce", text: "#b58a24" },
  cancelled: { bg: "#fbe6e0", text: "#d75e4a" },
  paid: { bg: "#e8f4ed", text: "#2d7a5e" },
  failed: { bg: "#fbe6e0", text: "#d75e4a" },
  accepted: { bg: "#e4edfa", text: "#577ebd" },
  rejected: { bg: "#fbe6e0", text: "#d75e4a" },
  shipped: { bg: "#d5f2e2", text: "#39836e" },
  delivered: { bg: "#e8f4ed", text: "#2d7a5e" },
  active: { bg: "#e8f4ed", text: "#2d7a5e" },
};

function StatusBadge({ value }: { value: string }) {
  const colors = statusColors[value] ?? statusColors.pending;
  return (
    <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: colors.bg, color: colors.text }}>
      {value.replace(/_/g, " ")}
    </span>
  );
}

export default function OrdersPage() {
  const { role } = useRole();
  const isAdmin = role === "admin";
  const isSeller = role === "seller";

  if (isAdmin) return <AdminOrders />;
  if (isSeller) return <SellerOrders />;
  return <ClientOrders />;
}

/* ─────────────────────────────── CLIENT ─────────────────────────────── */

function PayModal({ order, onClose, onPaid }: { order: OrderSummaryResponse; onClose: () => void; onPaid: () => void }) {
  const [momo, setMomo] = useState({ momo_phone: "", airtel_phone: "" });
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    if (!momo.momo_phone.trim() || !momo.airtel_phone.trim()) {
      setError("Please provide both the Airtel Money wallet and the Airtel line numbers.");
      return;
    }
    setWorking(true);
    setError("");
    try {
      setPayment(await paymentService.create({ order_id: order.id, momo_phone: momo.momo_phone.trim(), airtel_phone: momo.airtel_phone.trim() }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be started.");
    } finally {
      setWorking(false);
    }
  }

  async function confirmPaid() {
    if (!payment) return;
    setWorking(true);
    setError("");
    try {
      await paymentService.markPaid(payment.id);
      onPaid();
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be confirmed.");
    } finally {
      setWorking(false);
    }
  }

  async function markFailed() {
    if (!payment) return;
    setWorking(true);
    setError("");
    try {
      await paymentService.markFailed(payment.id);
      setPayment(null);
      setError("Payment was marked as failed. You can retry below.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be marked as failed.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold">Pay by mobile money</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              {order.order_number} · {rwf(order.total_amount)} · paid outside the app
            </p>
          </div>
          <button onClick={onClose} className="text-[var(--muted)] hover:text-[var(--ink)]" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {error && <p role="alert" className="mt-4 rounded-lg bg-[#fbe6e0] px-3 py-2 text-xs text-[#b74d3b]">{error}</p>}

        {!payment ? (
          <div className="mt-5 space-y-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Airtel Money wallet to charge</label>
              <input
                value={momo.momo_phone}
                onChange={(e) => setMomo((m) => ({ ...m, momo_phone: e.target.value }))}
                placeholder="e.g. 0788 123 456"
                className="w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Airtel line the payment is sent from</label>
              <input
                value={momo.airtel_phone}
                onChange={(e) => setMomo((m) => ({ ...m, airtel_phone: e.target.value }))}
                placeholder="e.g. 0733 123 456"
                className="w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
              />
            </div>
            <Button className="w-full" onClick={start} disabled={working}>
              <Smartphone size={15} /> Start payment
            </Button>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            <div className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] p-4">
              <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#b58a24]">Pay on your phone</p>
              <p className="mt-2 text-2xl font-black tracking-tight">{rwf(payment.amount)}</p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                Reference: <span className="font-mono">{payment.provider_ref ?? payment.id}</span> · dial <b>*500#</b>
              </p>
            </div>
            <Button className="w-full" onClick={confirmPaid} disabled={working}>
              <CheckCircle size={15} /> I&apos;ve completed the payment
            </Button>
            <button onClick={markFailed} disabled={working} className="w-full text-xs font-semibold text-[var(--coral)] hover:underline">
              Payment didn&apos;t go through
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ClientOrders() {
  const [orders, setOrders] = useState<OrderSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [paying, setPaying] = useState<OrderSummaryResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<OrderDetailResponse | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setOrders(await orderService.listMine());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Your orders could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    orderService
      .listMine()
      .then((list) => { if (!cancelled) setOrders(list); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Your orders could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function openDetail(orderId: string) {
    if (expanded === orderId) { setExpanded(null); setDetail(null); return; }
    try {
      setDetail(await orderService.get(orderId));
      setExpanded(orderId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Order could not be loaded.");
    }
  }

  async function receive(orderId: string) {
    try {
      await orderService.receive(orderId);
      void openDetail(orderId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Order could not be marked as received.");
    }
  }

  const unpaid = orders.filter((o) => o.payment_status !== "paid");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">My Orders</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {unpaid.length > 0 ? `${unpaid.length} order${unpaid.length > 1 ? "s" : ""} waiting for payment` : "Track your purchases and delivery."}
        </p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {paying && <PayModal order={paying} onClose={() => setPaying(null)} onPaid={load} />}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading orders…</div>
      ) : orders.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <Package className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">No orders yet</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">Once you check out, your orders appear here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card key={order.id} className="transition-shadow hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
                      <Package size={18} />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[var(--ink)]">{order.order_number}</p>
                      <p className="text-[10px] text-[var(--muted)]">{new Date(order.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge value={order.status} />
                    <StatusBadge value={order.payment_status} />
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-[#eff1ef] pt-3">
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => void openDetail(order.id)}>
                      {expanded === order.id ? "Hide details" : "Details"}
                    </Button>
                    {order.payment_status !== "paid" && (
                      <Button size="sm" onClick={() => setPaying(order)}><Smartphone size={13} /> Pay now</Button>
                    )}
                  </div>
                  <p className="text-sm font-extrabold text-[var(--ink)]">{rwf(order.total_amount)}</p>
                </div>

                {expanded === order.id && detail && (
                  <div className="mt-4 rounded-xl bg-[#f9fbf9] p-4 text-xs">
                    {detail.items.map((item) => (
                      <div key={item.id} className="flex items-center justify-between py-1">
                        <div>
                          <p className="font-semibold text-[var(--ink)]">{item.product_name}</p>
                          <p className="text-[10px] text-[var(--muted)]">Qty: {item.quantity}{item.variant_name ? ` · ${item.variant_name}` : ""}</p>
                        </div>
                        <span className="font-bold text-[var(--ink)]">{rwf(item.subtotal)}</span>
                      </div>
                    ))}
                    {detail.shipping && (
                      <div className="mt-3 border-t border-[var(--line)] pt-3 text-[var(--muted)]">
                        Deliver to {detail.shipping.recipient_name} · {detail.shipping.phone}
                        {detail.shipping.district && ` · ${detail.shipping.district}`}
                        {detail.shipping.sector && `, ${detail.shipping.sector}`}
                        {detail.shipping.address_line && ` · ${detail.shipping.address_line}`}
                      </div>
                    )}
                    {detail.fulfillment.length > 0 && (
                      <div className="mt-3 border-t border-[var(--line)] pt-3">
                        <p className="mb-2 font-bold text-[var(--ink)]">Fulfillment</p>
                        {detail.fulfillment.map((line) => (
                          <div key={line.id} className="flex items-center justify-between py-0.5">
                            <span className="text-[var(--muted)]">Seller status</span>
                            <StatusBadge value={line.status} />
                          </div>
                        ))}
                      </div>
                    )}
                    {detail.payment_status === "paid" && detail.fulfillment.length > 0 && detail.fulfillment.every((f) => f.status === "delivered") && detail.status !== "cancelled" && !detail.completed_at && (
                      <button
                        onClick={() => void receive(order.id)}
                        className="mt-3 w-full rounded-lg bg-[var(--ink)] py-2 font-bold text-white hover:bg-[#2e3d38]"
                      >
                        Confirm received — completes the order
                      </button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────── SELLER ─────────────────────────────── */

function SellerOrders() {
  const [rows, setRows] = useState<SellerOrderResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [shipping, setShipping] = useState<{ id: string; carrier: string; tracking: string } | null>(null);
  const [shipForm, setShipForm] = useState({ carrier: "", tracking_number: "" });
  const [walletModal, setWalletModal] = useState<{ orderLine: RevenueLine | null; released: number; held: number; loading: boolean }>({
    orderLine: null,
    released: 0,
    held: 0,
    loading: true,
  });
  const [confirmed, setConfirmed] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setRows(await orderService.listSellerOrders());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Orders received could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    orderService
      .listSellerOrders()
      .then((list) => { if (!cancelled) setRows(list); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Orders received could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function act(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await load();
      setRejecting(null);
      setReason("");
      setShipping(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed.");
    }
  }

  async function prepareShip(row: SellerOrderResponse) {
    setError("");
    setShipForm({ carrier: "", tracking_number: "" });
    setConfirmed(false);
    setWalletModal({ orderLine: null, released: 0, held: 0, loading: true });
    setShipping({ id: row.id, carrier: "", tracking: "" });
    try {
      const [orderLines, allLines] = await Promise.all([
        revenueService.mineForOrder(row.order_id),
        revenueService.mine(),
      ]);
      const orderLine = orderLines[0] ?? null;
      setWalletModal({
        orderLine,
        released: allLines.filter((l) => l.status === "released").reduce((s, l) => s + l.seller_earning, 0),
        held: allLines.filter((l) => l.status === "held").reduce((s, l) => s + l.seller_earning, 0),
        loading: false,
      });
    } catch (caught) {
      setWalletModal({ orderLine: null, released: 0, held: 0, loading: false });
      setError(caught instanceof Error ? caught.message : "Your wallet summary could not be loaded.");
    }
  }

  const pendingCount = rows.filter((r) => r.status === "pending").length;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Orders Received</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {pendingCount > 0 ? `${pendingCount} order${pendingCount > 1 ? "s" : ""} awaiting your response` : "Confirm, ship, and deliver your orders."}
        </p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {rejecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Reject order</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Tell the buyer why you cannot fulfill this order.</p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Out of stock, cannot fulfil this order."
              className="mt-4 min-h-[100px] w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setRejecting(null)}>Cancel</Button>
              <Button onClick={() => rejecting && void act(() => orderService.rejectSellerOrder(rejecting, reason))} disabled={!reason.trim()}>
                Confirm rejection
              </Button>
            </div>
          </div>
        </div>
      )}

      {shipping && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Mark as shipped</h2>

            <div className="mt-4 rounded-xl border border-[var(--line)] bg-[#fffdf0] p-4">
              <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#b58a24]">Review your wallet before shipping</p>
              {walletModal.loading ? (
                <p className="mt-2 text-sm text-[var(--muted)]">Loading your earnings…</p>
              ) : walletModal.orderLine ? (
                <div className="mt-2 space-y-1.5 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--muted)]">This order&apos;s gross</span>
                    <span className="font-bold text-[var(--ink)]">{rwf(walletModal.orderLine.amount)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--muted)]">Commission ({Math.round(walletModal.orderLine.revenue_rate)}%)</span>
                    <span className="font-bold text-[var(--coral)]">-{rwf(walletModal.orderLine.commission_amount)}</span>
                  </div>
                  <div className="flex items-center justify-between border-t border-[#f0e2c0] pt-1.5">
                    <span className="font-semibold text-[var(--ink)]">Your net for this order</span>
                    <span className="font-extrabold text-[var(--teal)]">{rwf(walletModal.orderLine.seller_earning)}</span>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-sm text-[var(--coral)]">No earning record found yet for this order.</p>
              )}
              {!walletModal.loading && (
                <div className="mt-3 flex gap-3 border-t border-[#f0e2c0] pt-3 text-xs">
                  <div>
                    <p className="text-[var(--muted)]">Wallet released</p>
                    <p className="mt-0.5 font-bold text-[var(--teal)]">{rwf(walletModal.released)}</p>
                  </div>
                  <div>
                    <p className="text-[var(--muted)]">Wallet held</p>
                    <p className="mt-0.5 font-bold text-[var(--ink)]">{rwf(walletModal.held)}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 space-y-3">
              <input
                value={shipForm.carrier}
                onChange={(e) => setShipForm((f) => ({ ...f, carrier: e.target.value }))}
                placeholder="Carrier (e.g. Zipline)"
                className="w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
              />
              <input
                value={shipForm.tracking_number}
                onChange={(e) => setShipForm((f) => ({ ...f, tracking_number: e.target.value }))}
                placeholder="Tracking number"
                className="w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
              />
            </div>

            {!walletModal.loading && (
              <label className="mt-4 flex cursor-pointer items-start gap-2 rounded-lg border border-[var(--line)] px-3 py-2.5 text-xs text-[var(--ink)]">
                <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} className="mt-0.5 accent-[var(--teal)]" />
                <span>I&apos;ve reviewed my earnings and confirm I want to ship this order.</span>              </label>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShipping(null)}>Cancel</Button>
              <Button
                onClick={() => shipping && void act(() => orderService.shipSellerOrder(shipping.id, shipForm))}
                disabled={!shipForm.tracking_number.trim() || walletModal.loading || !confirmed}
              >
                <Truck size={14} /> Ship
              </Button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading orders…</div>
      ) : rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <Package className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">No orders yet</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">When clients buy your listings, orders appear here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <Card key={row.id} className="transition-shadow hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-lg bg-[#e4edfa] text-[#577ebd]">
                      <Send size={18} />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[var(--ink)]">#{row.order_id.slice(0, 8)}</p>
                      <p className="text-[10px] text-[var(--muted)]">{new Date(row.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <StatusBadge value={row.status} />
                </div>

                {row.status === "rejected" && row.rejected_reason && (
                  <p className="mt-3 rounded-lg bg-[#fbe6e0] px-3 py-2 text-xs text-[#b74d3b]">You declined: {row.rejected_reason}</p>
                )}

                {row.shipment && (
                  <p className="mt-3 text-[11px] text-[var(--muted)]">
                    Shipment: {row.shipment.carrier || "Carrier"} {row.shipment.tracking_number ? `· ${row.shipment.tracking_number}` : ""} · <b className="capitalize">{row.shipment.status}</b>
                  </p>
                )}

                <div className="mt-4 flex flex-wrap gap-2 border-t border-[#eff1ef] pt-3">
                  {row.status === "pending" && (
                    <>
                      <Button size="sm" onClick={() => void act(() => orderService.acceptSellerOrder(row.id))}><CheckCircle size={13} /> Accept</Button>
                      <Button size="sm" variant="outline" onClick={() => { setReason(""); setRejecting(row.id); }}><X size={13} /> Reject</Button>
                    </>
                  )}
                  {row.status === "accepted" && (
                    <Button size="sm" onClick={() => void prepareShip(row)}>
                      <Truck size={13} /> Mark as shipped
                    </Button>
                  )}
                  {row.status === "shipped" && row.shipment && (
                    <Button size="sm" onClick={() => void act(() => orderService.deliverShipment(row.shipment!.id))}>
                      <CheckCircle size={13} /> Mark as delivered
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────── ADMIN ─────────────────────────────── */

function AdminOrders() {
  const [txns, setTxns] = useState<RevenueTransactionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedOrder, setExpandedOrder] = useState<string | null>(null);
  const [breakdown, setBreakdown] = useState<RevenueLine[] | null>(null);
  const [summary, setSummary] = useState<RevenueSummaryResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    revenueService
      .all()
      .then((rows) => { if (!cancelled) setTxns(rows); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Revenue transactions could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const byOrder = new Map<string, RevenueTransactionResponse[]>();
  for (const row of txns) {
    byOrder.set(row.order_id, [...(byOrder.get(row.order_id) ?? []), row]);
  }

  const totalGross = txns.reduce((s, t) => s + t.amount, 0);
  const totalCommission = txns.reduce((s, t) => s + t.commission_amount, 0);

  async function toggleBreakdown(orderId: string) {
    if (expandedOrder === orderId) { setExpandedOrder(null); setBreakdown(null); setSummary(null); return; }
    setExpandedOrder(orderId);
    setBreakdown(null);
    setSummary(null);
    setDetailLoading(true);
    setError("");
    try {
      const [brk, sum] = await Promise.all([
        revenueService.orderBreakdown(orderId),
        revenueService.orderSummary(orderId),
      ]);
      setBreakdown(brk);
      setSummary(sum);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Order breakdown could not be loaded.");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">All Orders</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Paid orders with the per-seller commission split (derived at payment time).
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-[#bdded1] bg-[#e8f4ed]">
          <CardContent className="p-6">
            <span className="text-xs text-[#78857f]">Gross volume</span>
            <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalGross)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <span className="text-xs text-[#78857f]">Platform commission</span>
            <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalCommission)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <span className="text-xs text-[#78857f]">Orders</span>
            <p className="mt-3 text-2xl font-extrabold tracking-tight text-[var(--ink)]">{byOrder.size}</p>
          </CardContent>
        </Card>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading orders…</div>
      ) : txns.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <Package className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">No paid orders yet</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">Revenue transactions appear once buyers complete payments.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {Array.from(byOrder.entries()).map(([orderId, lines]) => {
            const total = lines.reduce((s, l) => s + l.amount, 0);
            const commission = lines.reduce((s, l) => s + l.commission_amount, 0);
            const released = lines.every((l) => l.status === "released");
            return (
              <Card key={orderId}>
                <CardContent className="p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
                        <Package size={18} />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-[var(--ink)]">Order #{orderId.slice(0, 8)}</p>
                        <p className="text-[10px] text-[var(--muted)]">
                          {lines.length} seller line{lines.length > 1 ? "s" : ""} · {new Date(lines[0].created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge value={released ? "delivered" : "active"} />
                      <span className="text-sm font-extrabold text-[var(--ink)]">{rwf(total)}</span>
                    </div>
                  </div>
                  <div className="mt-3 divide-y divide-[#eff1ef]">
                    {lines.map((line) => (
                      <div key={line.id} className="flex items-center justify-between py-2 text-xs">
                        <div>
                          <p className="font-semibold text-[var(--ink)]">Seller {line.seller_id.slice(0, 8)}</p>
                          <p className="text-[10px] text-[var(--muted)]">
                            Rate {line.revenue_rate}% · {line.status}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-[var(--ink)]">Net {rwf(line.seller_earning)}</p>
                          <p className="text-[10px] text-[var(--coral)]">-{rwf(line.commission_amount)} commission</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="mt-2 border-t border-[#eff1ef] pt-2 text-[11px] text-[var(--muted)]">
                    Order commission total: <b className="text-[var(--ink)]">{rwf(commission)}</b>
                  </p>
                  <button
                    onClick={() => void toggleBreakdown(orderId)}
                    className="mt-3 text-[11px] font-bold text-[var(--teal)] hover:underline"
                  >
                    {expandedOrder === orderId ? "Hide breakdown" : "View breakdown &amp; summary"}
                  </button>
                  {expandedOrder === orderId && (
                    <div className="mt-3 rounded-xl border border-[var(--line)] bg-[#f9fbf9] p-4">
                      {detailLoading ? (
                        <p className="text-xs text-[var(--muted)]">Loading breakdown…</p>
                      ) : summary && breakdown ? (
                        <div className="space-y-3">
                          <div className="grid gap-3 sm:grid-cols-3">
                            <div>
                              <p className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">Gross</p>
                              <p className="mt-1 text-sm font-extrabold text-[var(--ink)]">{rwf(summary.total_gross)}</p>
                            </div>
                            <div>
                              <p className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">Commission</p>
                              <p className="mt-1 text-sm font-extrabold text-[var(--coral)]">{rwf(summary.total_commission)}</p>
                            </div>
                            <div>
                              <p className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">Seller net</p>
                              <p className="mt-1 text-sm font-extrabold text-[var(--teal)]">{rwf(summary.total_seller_earning)}</p>
                            </div>
                          </div>
                          <div className="border-t border-[var(--line)] pt-2">
                            <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">Per-seller breakdown</p>
                            {breakdown.map((line) => (
                              <div key={line.id} className="flex items-center justify-between py-1.5 text-xs">
                                <div>
                                  <p className="font-semibold text-[var(--ink)]">Seller {line.seller_id.slice(0, 8)}</p>
                                  <p className="text-[10px] text-[var(--muted)]">
                                    Rate {line.revenue_rate}% · {line.status}{line.released_at ? ` · released ${new Date(line.released_at).toLocaleDateString()}` : ""}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="font-bold text-[var(--ink)]">Net {rwf(line.seller_earning)}</p>
                                  <p className="text-[10px] text-[var(--coral)]">-{rwf(line.commission_amount)} commission</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-[var(--coral)]">Breakdown unavailable.</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}