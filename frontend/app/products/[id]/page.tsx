"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowRight, Check, Minus, Plus, ShoppingCart, Truck } from "lucide-react";
import { Footer } from "@/app/_components/public/footer";
import { Header } from "@/app/_components/public/header";
import { cartService } from "@/app/services/cart.service";
import { catalogService, type CatalogProductDetail } from "@/app/services/catalog.service";
import { useAuth } from "@/app/context/auth-context";
import { notifyCartUpdated, rwf } from "@/app/lib/utils";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();

  const [product, setProduct] = useState<CatalogProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [variantIndex, setVariantIndex] = useState(0);
  const [offerIndex, setOfferIndex] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await catalogService.getProduct(params.id);
        if (!cancelled) setProduct(data);
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Product could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [params.id]);

  const variant = product?.variants[variantIndex];
  const offer = variant?.offers[Math.min(offerIndex, variant.offers.length - 1)];

  async function addToCart() {
    if (!offer) return;
    if (!user) { router.push("/login"); return; }
    try {
      await cartService.addItem(offer.listing_id, quantity);
      notifyCartUpdated();
      setAdded(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Item could not be added to your cart.");
    }
  }

  const variantLabel = (idx: number): string =>
    product!.variants[idx].attribute_values.map((v) => `${v.attribute_name}: ${v.value}`).join(" · ");

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-10 sm:py-14">
        <Link href="/products" className="text-xs font-bold text-[var(--teal)] hover:underline">
          ← Back to shop
        </Link>

        {loading ? (
          <div className="mt-8 rounded-xl border border-[var(--line)] bg-white p-14 text-center text-sm text-[var(--muted)]">
            Loading product…
          </div>
        ) : error || !product ? (
          <div className="mt-8 rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
            <p className="font-bold text-[#b74d3b]">{error || "Product could not be loaded."}</p>
            <p className="mt-2 text-sm text-[var(--muted)]">It may have been archived or removed.</p>
          </div>
        ) : (
          <div className="mt-8 grid gap-10 lg:grid-cols-2">
            {/* Gallery */}
            <div>
              <div className="relative aspect-square overflow-hidden rounded-2xl bg-[#e8f3ed]">
                {product.images.length ? (
                  <>
                    <div className="absolute inset-0 grid h-full w-full place-items-center font-black tracking-tight text-[#9aa9a1]">
                      {product.name.slice(0, 2).toUpperCase()}
                    </div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={product.images[activeImage]?.url ?? product.images[0].url}
                      alt={product.name}
                      className="absolute inset-0 h-full w-full object-cover"
                      onError={(e) => { e.currentTarget.style.display = "none"; }}
                    />
                  </>
                ) : (
                  <div className="absolute inset-0 grid h-full w-full place-items-center font-black tracking-tight text-[#9aa9a1]">
                    {product.name.slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>
              {product.images.length > 1 && (
                <div className="mt-3 flex gap-2 overflow-x-auto">
                  {product.images.map((image, index) => (
                    <button
                      key={image.id}
                      onClick={() => setActiveImage(index)}
                      className={`h-20 w-20 shrink-0 overflow-hidden rounded-xl border-2 ${
                        activeImage === index ? "border-[var(--teal)]" : "border-transparent"
                      }`}
                    >
                      <div className="h-full w-full bg-cover bg-center" style={{ backgroundImage: `url(${image.url})` }} />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Info + offers */}
            <div>
              <h1 className="text-3xl font-black tracking-[-.04em] sm:text-4xl">{product.name}</h1>
              {product.description && (
                <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{product.description}</p>
              )}

              {/* Variants */}
              {product.variants.length > 0 && (
                <div className="mt-7">
                  <h2 className="text-xs font-bold uppercase tracking-[.1em] text-[#a4aaa6]">Choose a variant</h2>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {product.variants.map((v, index) => (
                      <button
                        key={v.id}
                        onClick={() => {
                          setVariantIndex(index);
                          setOfferIndex(0);
                          setQuantity(1);
                          setAdded(false);
                        }}
                        className={`rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                          index === variantIndex
                            ? "border-[var(--ink)] bg-[var(--ink)] text-white"
                            : "border-[var(--line)] bg-white text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)]"
                        }`}
                      >
                        {variantLabel(index)}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Offers for the selected variant */}
              {variant && variant.offers.length > 0 ? (
                <div className="mt-7 rounded-2xl border border-[var(--line)] bg-white p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-[var(--muted)]">Best offer for this variant</p>
                      <p className="mt-1 text-3xl font-black tracking-tight">{rwf(offer!.price)}</p>
                    </div>
                    <span className="rounded-full bg-[#e8f4ed] px-2.5 py-1 text-[10px] font-bold text-[#2d7a5e]">
                      {offer!.stock > 0 ? `${offer!.stock} in stock` : "Out of stock"}
                    </span>
                  </div>

                  {variant.offers.length > 1 && (
                    <div className="mt-4">
                      <p className="mb-2 text-[11px] font-bold uppercase tracking-[.1em] text-[#a4aaa6]">
                        Choose a seller
                      </p>
                      <div className="space-y-2">
                        {variant.offers.map((of, index) => (
                          <button
                            key={of.listing_id}
                            onClick={() => { setOfferIndex(index); setAdded(false); }}
                            className={`flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-left transition-colors ${
                              index === offerIndex
                                ? "border-[var(--ink)] bg-[#f6f8f6]"
                                : "border-[var(--line)] hover:border-[var(--ink)]"
                            }`}
                          >
                            <div>
                              <p className="text-xs font-bold">{of.seller.business_name}</p>
                              <p className="text-[10px] text-[var(--muted)] capitalize">{of.condition.replace("_", " ")} condition</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-black">{rwf(of.price)}</p>
                              <p className="text-[10px] text-[var(--muted)]">{of.stock > 0 ? `${of.stock} left` : "Out of stock"}</p>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {offer!.stock > 0 && (
                    <div className="mt-5 flex flex-wrap items-center gap-3">
                      <div className="flex items-center gap-2 rounded-lg border border-[var(--line)] px-2 py-1.5">
                        <button
                          onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                          className="grid h-7 w-7 place-items-center rounded-lg text-[var(--muted)] hover:bg-[#f2f5f2] hover:text-[var(--ink)]"
                          aria-label="Decrease quantity"
                        >
                          <Minus size={13} />
                        </button>
                        <span className="w-6 text-center text-sm font-bold">{quantity}</span>
                        <button
                          onClick={() => setQuantity((q) => Math.min(offer!.stock, q + 1))}
                          className="grid h-7 w-7 place-items-center rounded-lg text-[var(--muted)] hover:bg-[#f2f5f2] hover:text-[var(--ink)]"
                          aria-label="Increase quantity"
                        >
                          <Plus size={13} />
                        </button>
                      </div>
                      <button
                        onClick={() => void addToCart()}
                        className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-bold transition-all hover:-translate-y-0.5 ${
                          added ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[var(--ink)] text-white hover:bg-[#2e3d38]"
                        }`}
                      >
                        {added ? (<><Check size={15} /> Added to cart</>) : (<><ShoppingCart size={15} /> {isAuthenticated ? "Add to cart" : "Log in to buy"}</>)}
                      </button>
                      {added && (
                        <Link href="/dashboard/cart" className="flex items-center gap-1 text-xs font-bold text-[var(--teal)] hover:underline">
                          View cart <ArrowRight size={12} />
                        </Link>
                      )}
                    </div>
                  )}

                  <div className="mt-5 flex items-start gap-2 border-t border-[var(--line)] pt-4 text-[11px] text-[var(--muted)]">
                    <Truck size={15} className="mt-0.5 shrink-0" />
                    <p>Delivery is arranged with the seller after you pay. Payment is outside the app.</p>
                  </div>
                </div>
              ) : (
                <div className="mt-7 rounded-2xl border border-dashed border-[var(--line)] bg-white p-6 text-sm text-[var(--muted)]">
                  {variant
                    ? "This variant is currently out of stock."
                    : "No sellers are currently offering this product."}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}