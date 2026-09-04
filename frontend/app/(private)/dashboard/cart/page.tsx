"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle, Copy, Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { cartService, type CartResponse } from "@/app/services/cart.service";
import { orderService, type OrderDetailResponse, type ShippingInput } from "@/app/services/order.service";
import { paymentService, type PaymentResponse } from "@/app/services/payment.service";
import { notifyCartUpdated, rwf } from "@/app/lib/utils";

// MUHUZE's MoMo number buyers send money to
const MUHUZE_MOMO = "0788 000 000";

type Step = "cart" | "delivery" | "payment" | "done";

export default function CartPage() {
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState<Step>("cart");
  const [working, setWorking] = useState(false);
  const [order, setOrder] = useState<OrderDetailResponse | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const [form, setForm] = useState<ShippingInput & { contact_phone: string; notes: string }>({
    recipient_name: "",
    phone: "",
    province: "",
    district: "",
    sector: "",
    cell: "",
    village: "",
    address_line: "",
    delivery_instructions: "",
    contact_phone: "",
    notes: "",
  });
  const [momoPhone, setMomoPhone] = useState("");

  useEffect(() => {
    let cancelled = false;
    cartService
      .get()
      .then((c) => { if (!cancelled) setCart(c); })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "Your cart could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function updateQty(itemId: string, quantity: number) {
    if (quantity < 1) return;
    setCart((prev) => prev ? { ...prev, items: prev.items.map((i) => (i.id === itemId ? { ...i, quantity } : i)) } : prev);
    try {
      const updated = await cartService.updateQuantity(itemId, quantity);
      setCart(updated);
      notifyCartUpdated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Quantity could not be updated.");
    }
  }

  async function remove(itemId: string) {
    try {
      await cartService.removeItem(itemId);
      setCart(await cartService.get());
      notifyCartUpdated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Item could not be removed.");
    }
  }

  async function placeOrder() {
    if (!form.recipient_name.trim() || !form.phone.trim()) {
      setError("Please provide the recipient name and phone number.");
      return;
    }
    setWorking(true);
    setError("");
    try {
      const created = await orderService.checkout({
        shipping: {
          recipient_name: form.recipient_name.trim(),
          phone: form.phone.trim(),
          province: form.province || undefined,
          district: form.district || undefined,
          sector: form.sector || undefined,
          cell: form.cell || undefined,
          village: form.village || undefined,
          address_line: form.address_line || undefined,
          delivery_instructions: form.delivery_instructions || undefined,
        },
        contact_phone: form.contact_phone || undefined,
        notes: form.notes || undefined,
      });
      setOrder(created);
      setCart({ items: [], item_count: 0, total: 0 });
      notifyCartUpdated();
      setStep("payment");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Order could not be placed.");
    } finally {
      setWorking(false);
    }
  }

  async function startPayment() {
    if (!order) return;
    setWorking(true);
    setError("");
    try {
      // momo_phone is optional — the buyer pays the MUHUZE MoMo number shown
      // above outside the system. We only record their number if provided.
      setPayment(await paymentService.create({
        order_id: order.id,
        momo_phone: momoPhone.trim() || undefined,
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payment could not be started.");
    } finally {
      setWorking(false);
    }
  }

  async function confirmPaid() {
    if (!payment) return;
    setWorking(true);
    setError("");
    try {
      await paymentService.reportPaid(payment.id);
      setStep("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payment could not be reported.");
    } finally {
      setWorking(false);
    }
  }

  async function confirmFailed() {
    if (!payment) return;
    setWorking(true);
    setError("");
    try {
      await paymentService.markFailed(payment.id);
      setPayment(null);
      setError("Payment was marked as failed. You can retry below.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not mark payment as failed.");
    } finally {
      setWorking(false);
    }
  }

  function copyMomo() {
    navigator.clipboard.writeText(MUHUZE_MOMO).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  if (loading) {
    return <div className="mx-auto max-w-4xl p-10 text-center text-sm text-[var(--muted)]">Loading your cart…</div>;
  }

  // ── Done ──────────────────────────────────────────────────────────────────
  if (step === "done" && order) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-16 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#e8f4ed] text-[var(--teal)]">
          <CheckCircle size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Payment reported</h2>
        <p className="text-sm text-[var(--muted)]">
          Order <b className="text-[var(--ink)]">{order.order_number}</b> is recorded. MUHUZE will confirm the money arrived, then the seller will start preparing your order.
        </p>
        <Link href="/dashboard/orders">
          <Button className="mt-2">View My Orders <ArrowRight size={14} /></Button>
        </Link>
      </div>
    );
  }

  // ── Payment step ──────────────────────────────────────────────────────────
  if (step === "payment" && order) {
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Step 3 of 3</p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--ink)]">Pay by mobile money</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Order <b className="text-[var(--ink)]">{order.order_number}</b> · {rwf(order.total_amount)}
          </p>
        </div>

        {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

        {!payment ? (
          <Card>
            <CardContent className="space-y-5 p-6">
              {/* MUHUZE MoMo number to pay to */}
              <div className="rounded-xl border border-[#bdded1] bg-[#e8f4ed] p-4">
                <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#2d7a5e]">Send payment to this MoMo number</p>
                <div className="mt-2 flex items-center justify-between gap-3">
                  <p className="text-2xl font-black tracking-tight text-[var(--ink)]">{MUHUZE_MOMO}</p>
                  <button
                    onClick={copyMomo}
                    className="flex items-center gap-1.5 rounded-lg border border-[#bdded1] bg-white px-3 py-1.5 text-xs font-bold text-[#2d7a5e] hover:bg-[#d5f2e2] transition-colors"
                  >
                    <Copy size={12} /> {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="mt-2 text-xs text-[#2d7a5e]">Amount: <b>{rwf(order.total_amount)}</b></p>
              </div>

              <ol className="list-decimal space-y-1.5 pl-5 text-xs leading-6 text-[var(--muted)]">
                <li>Open your MoMo app or dial <b>*182#</b> (MTN) / <b>*500#</b> (Airtel).</li>
                <li>Send <b>{rwf(order.total_amount)}</b> to <b>{MUHUZE_MOMO}</b>.</li>
                <li>Use your order number <b>{order.order_number}</b> as the reference/reason.</li>
                <li>Once sent, enter your phone number below and click confirm.</li>
              </ol>

              <div>
                <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Your MoMo phone number <span className="font-normal">(optional — for our records)</span></label>
                <input
                  value={momoPhone}
                  onChange={(e) => setMomoPhone(e.target.value)}
                  placeholder="e.g. 0788 123 456"
                  className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                />
              </div>

              <Button className="w-full" onClick={startPayment} disabled={working}>
                {working ? "Processing…" : "I've sent the payment"} <ArrowRight size={15} />
              </Button>
              <button onClick={() => setStep("delivery")} className="w-full text-xs font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
                ← Back to delivery details
              </button>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-[#f0d98a] bg-[#fffdf0]">
            <CardContent className="space-y-4 p-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#b58a24]">Confirm your payment</p>
                <p className="mt-3 text-3xl font-black tracking-tight">{rwf(payment.amount)}</p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Reference: <span className="font-mono">{payment.provider_ref ?? payment.id.slice(0, 8)}</span>
                </p>
              </div>
              <p className="text-xs text-[var(--muted)]">
                Once you have confirmed the MoMo transfer went through, click below to complete your order.
              </p>
              <Button className="w-full" onClick={confirmPaid} disabled={working}>
                <CheckCircle size={15} /> Confirm — payment sent
              </Button>
              <button onClick={confirmFailed} disabled={working} className="w-full text-xs font-semibold text-[var(--coral)] hover:underline">
                Payment didn&apos;t go through — cancel
              </button>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // ── Delivery step ─────────────────────────────────────────────────────────
  if (step === "delivery") {
    const field = (key: keyof typeof form, label: string, placeholder: string, span = false) => (
      <div className={span ? "sm:col-span-2" : ""}>
        <label className="mb-1 block text-xs font-bold text-[var(--muted)]">{label}</label>
        <input
          value={form[key]}
          onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
          placeholder={placeholder}
          className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
        />
      </div>
    );

    return (
      <div className="mx-auto max-w-xl space-y-6">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Step 2 of 3</p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--ink)]">Delivery details</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">Where should the seller deliver your order?</p>
        </div>

        {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              {field("recipient_name", "Recipient name *", "Who to hand it to")}
              {field("phone", "Recipient phone *", "e.g. 0788 123 456")}
              {field("province", "Province", "e.g. Kigali City")}
              {field("district", "District", "e.g. Nyarugenge")}
              {field("sector", "Sector", "e.g. Nyamirambo")}
              {field("cell", "Cell", "e.g. Kanyinya")}
              {field("village", "Village", "e.g. Rwampara")}
              {field("address_line", "Street / landmark", "Building or street name")}
              {field("delivery_instructions", "Delivery instructions", "Gates, colors, anything useful", true)}
            </div>
            <details className="rounded-lg border border-[var(--line)] px-4 py-3 text-xs">
              <summary className="cursor-pointer font-bold text-[var(--muted)]">Optional: contact &amp; notes</summary>
              <div className="mt-3 grid gap-4 sm:grid-cols-2">
                {field("contact_phone", "Your contact phone", "e.g. 0788 123 456")}
                {field("notes", "Order notes", "Anything else?")}
              </div>
            </details>
            <Button className="w-full" onClick={placeOrder} disabled={working}>
              {working ? "Placing order…" : "Place order"} <ArrowRight size={15} />
            </Button>
            <button onClick={() => setStep("cart")} className="w-full text-xs font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
              ← Back to cart
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Cart step ─────────────────────────────────────────────────────────────
  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#f2f5f2] text-[var(--muted)]">
          <ShoppingBag size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Your cart is empty</h2>
        <Link href="/products"><Button>Browse Products</Button></Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Step 1 of 3</p>
        <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--ink)]">My Cart</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">{cart.item_count} item{cart.item_count !== 1 ? "s" : ""} in your cart</p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          {cart.items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
                  <ShoppingBag size={20} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-[var(--ink)]">{item.product_name}</p>
                  <p className="text-[10px] text-[var(--muted)]">
                    {item.variant_name ?? "Standard variant"} · {rwf(item.unit_price)} each
                  </p>
                  <p className="mt-0.5 text-xs font-bold text-[var(--ink)]">{rwf(item.subtotal)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => void updateQty(item.id, item.quantity - 1)}
                    disabled={item.quantity <= 1}
                    className="grid h-7 w-7 place-items-center rounded-lg border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)] disabled:opacity-40"
                    aria-label="Decrease quantity"
                  >
                    <Minus size={12} />
                  </button>
                  <span className="w-5 text-center text-sm font-bold text-[var(--ink)]">{item.quantity}</span>
                  <button
                    onClick={() => void updateQty(item.id, item.quantity + 1)}
                    className="grid h-7 w-7 place-items-center rounded-lg border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)]"
                    aria-label="Increase quantity"
                  >
                    <Plus size={12} />
                  </button>
                </div>
                <button
                  onClick={() => void remove(item.id)}
                  className="ml-2 text-[var(--muted)] hover:text-[var(--coral)]"
                  aria-label="Remove item"
                >
                  <Trash2 size={15} />
                </button>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="h-fit">
          <CardContent className="space-y-4 p-6">
            <h2 className="text-sm font-bold text-[var(--ink)]">Order Summary</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-[var(--muted)]">
                <span>Subtotal</span>
                <span>{rwf(cart.total)}</span>
              </div>
              <div className="flex justify-between text-[var(--muted)]">
                <span>Delivery</span>
                <span>Arranged with seller</span>
              </div>
              <div className="my-2 border-t border-[var(--line)]" />
              <div className="flex justify-between font-bold text-[var(--ink)]">
                <span>Total</span>
                <span>{rwf(cart.total)}</span>
              </div>
            </div>
            <button
              onClick={() => { setError(""); setStep("delivery"); }}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] py-2.5 text-sm font-bold text-white transition-all hover:-translate-y-0.5 hover:bg-[#2e3d38]"
            >
              Checkout <ArrowRight size={15} />
            </button>
            <Link href="/products">
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
