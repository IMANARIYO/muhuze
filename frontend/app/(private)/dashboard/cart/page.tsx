"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle, Minus, Plus, ShoppingBag, Smartphone, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { cartService, type CartResponse } from "@/app/services/cart.service";
import { orderService, type OrderDetailResponse, type ShippingInput } from "@/app/services/order.service";
import { paymentService, type PaymentResponse } from "@/app/services/payment.service";
import { notifyCartUpdated, rwf } from "@/app/lib/utils";

type Step = "cart" | "delivery" | "payment" | "done";

export default function CartPage() {
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState<Step>("cart");
  const [working, setWorking] = useState(false);
  const [order, setOrder] = useState<OrderDetailResponse | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);

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
  const [momo, setMomo] = useState({ momo_phone: "", airtel_phone: "" });

  useEffect(() => {
    let cancelled = false;
    cartService
      .get()
      .then((cart) => { if (!cancelled) setCart(cart); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Your cart could not be loaded."); })
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
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Quantity could not be updated.");
    }
  }

  async function remove(itemId: string) {
    try {
      await cartService.removeItem(itemId);
      setCart(await cartService.get());
      notifyCartUpdated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Item could not be removed.");
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
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Order could not be placed.");
    } finally {
      setWorking(false);
    }
  }

  async function startPayment() {
    if (!order || !momo.momo_phone.trim() || !momo.airtel_phone.trim()) {
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
      setStep("done");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be confirmed.");
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
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be marked as failed.");
    } finally {
      setWorking(false);
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-4xl p-10 text-center text-sm text-[var(--muted)]">Loading your cart…</div>;
  }

  if (step === "done" && order) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-16 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#e8f4ed] text-[var(--teal)]">
          <CheckCircle size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Payment successful</h2>
        <p className="text-sm text-[var(--muted)]">
          Order <b className="text-[var(--ink)]">{order.order_number}</b> is paid and confirmed. The seller has been notified and will arrange delivery.
        </p>
        <Link href="/dashboard/orders" className="mt-2">
          <Button className="mt-2">View My Orders <ArrowRight size={14} /></Button>
        </Link>
      </div>
    );
  }

  if (step === "payment" && order) {
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Step 3 of 3</p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--ink)]">Pay by mobile money</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Order <b className="text-[var(--ink)]">{order.order_number}</b> · {rwf(order.total_amount)}. Payment is made with Airtel Money <b>outside the app</b>.
          </p>
        </div>

        {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

        {!payment ? (
          <Card>
            <CardContent className="space-y-4 p-6">
              <div className="flex items-center gap-2 text-sm font-bold">
                <Smartphone size={16} /> Airtel Money details
              </div>
              <div>
                <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Airtel Money wallet to charge</label>
                <input
                  value={momo.momo_phone}
                  onChange={(e) => setMomo((m) => ({ ...m, momo_phone: e.target.value }))}
                  placeholder="e.g. 0788 123 456"
                  className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Airtel line the payment is sent from</label>
                <input
                  value={momo.airtel_phone}
                  onChange={(e) => setMomo((m) => ({ ...m, airtel_phone: e.target.value }))}
                  placeholder="e.g. 0733 123 456"
                  className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                />
              </div>
              <Button className="w-full" onClick={startPayment} disabled={working}>
                Start payment <ArrowRight size={15} />
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
                <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#b58a24]">Payment started — pay on your phone</p>
                <p className="mt-3 text-3xl font-black tracking-tight">{rwf(payment.amount)}</p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Reference: <span className="font-mono">{payment.provider_ref ?? payment.id}</span>
                </p>
              </div>
              <ol className="list-decimal space-y-1 pl-5 text-xs leading-6 text-[var(--muted)]">
                <li>Open your Airtel Money menu (dial <b>*500#</b>).</li>
                <li>Send the amount above to the Muhuze reference.</li>
                <li>After you approve the payment on your phone, confirm here.</li>
              </ol>
              <Button className="w-full" onClick={confirmPaid} disabled={working}>
                <CheckCircle size={15} /> I&apos;ve completed the payment
              </Button>
              <button onClick={confirmFailed} disabled={working} className="w-full text-xs font-semibold text-[var(--coral)] hover:underline">
                Payment didn&apos;t go through
              </button>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

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

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#f2f5f2] text-[var(--muted)]">
          <ShoppingBag size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Your cart is empty</h2>
        <Link href="/products">
          <Button>Browse Products</Button>
        </Link>
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

        {/* Order summary */}
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