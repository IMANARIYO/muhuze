"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Search } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { productService, type ListingRecord, type ProductRecord, type VariantRecord } from "@/app/services/product.service";

type Condition = ListingRecord["condition"];

export default function NewListingPage() {
  const [search, setSearch] = useState("");
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductRecord | null>(null);
  const [productVariants, setProductVariants] = useState<VariantRecord[]>([]);
  const [selectedVariant, setSelectedVariant] = useState<VariantRecord | null>(null);
  const [form, setForm] = useState({ price: "", stock: "", seller_sku: "", condition: "new" as Condition });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Search active products
  useEffect(() => {
    if (!search.trim()) { setProducts([]); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const results = await productService.list({ status: "active", search: search.trim() });
        setProducts(results);
      } catch {
        setProducts([]);
      } finally {
        setSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  async function selectProduct(product: ProductRecord) {
    setSelectedProduct(product);
    setSelectedVariant(null);
    setSearch("");
    setProducts([]);
    try {
      const v = await productService.listVariants(product.id);
      setProductVariants(v.filter((variant) => variant.status === "active"));
    } catch {
      setProductVariants([]);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedVariant) return;
    setSaving(true);
    setError("");
    try {
      const listing = await productService.createListing({
        variant_id: selectedVariant.id,
        price: parseFloat(form.price),
        stock: parseInt(form.stock, 10),
        seller_sku: form.seller_sku || undefined,
        condition: form.condition,
      });
      setSuccess(`Listing created (ID: ${listing.id.slice(0, 8)}). Submit it for admin review from My Listings.`);
      setSelectedProduct(null);
      setSelectedVariant(null);
      setForm({ price: "", stock: "", seller_sku: "", condition: "new" });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Listing could not be created.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/dashboard/listings" className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--line)] bg-white text-[var(--muted)] hover:bg-[#f9fbf9] transition-colors">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Seller workspace</p>
          <h1 className="mt-0.5 text-2xl font-black tracking-[-.04em]">Create a listing</h1>
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {success && (
        <div className="rounded-xl border border-[#bdded1] bg-[#e8f4ed] px-5 py-4">
          <p className="flex items-center gap-2 text-sm font-bold text-[#2d7a5e]"><CheckCircle2 size={16} /> Listing created!</p>
          <p className="mt-1 text-xs text-[var(--muted)]">{success}</p>
          <Link href="/dashboard/listings" className="mt-3 inline-flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline">
            Go to My Listings →
          </Link>
        </div>
      )}

      {/* Step 1: Find a product */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <h2 className="font-bold">Step 1 — Find a catalog product</h2>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Search for an approved product in the catalog. Only active products can be listed.
          If the product doesn&apos;t exist yet, <Link href="/dashboard/products/new" className="text-[var(--teal)] hover:underline">request it first</Link>.
        </p>

        {selectedProduct ? (
          <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border border-[#bdded1] bg-[#e8f4ed] px-4 py-3">
            <div>
              <p className="text-sm font-bold text-[var(--ink)]">{selectedProduct.name}</p>
              <p className="text-xs text-[var(--muted)]">{selectedProduct.description?.slice(0, 80) ?? "No description"}</p>
            </div>
            <button
              onClick={() => { setSelectedProduct(null); setSelectedVariant(null); setProductVariants([]); }}
              className="shrink-0 text-[var(--muted)] hover:text-[#b74d3b] transition-colors text-xs font-bold"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="relative mt-4">
            <div className="flex items-center gap-2 rounded-lg border border-[var(--line)] bg-[#f9fbf9] px-3">
              <Search size={15} className="shrink-0 text-[var(--muted)]" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by product name..."
                className="border-0 bg-transparent px-0 focus:ring-0 shadow-none"
              />
            </div>
            {(searching || products.length > 0) && (
              <div className="absolute left-0 right-0 top-full z-10 mt-1 rounded-xl border border-[var(--line)] bg-white shadow-lg overflow-hidden">
                {searching ? (
                  <p className="px-4 py-3 text-xs text-[var(--muted)]">Searching...</p>
                ) : products.length === 0 ? (
                  <p className="px-4 py-3 text-xs text-[var(--muted)]">No active products found for &ldquo;{search}&rdquo;</p>
                ) : (
                  <div className="divide-y divide-[#eff1ef] max-h-60 overflow-y-auto">
                    {products.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => selectProduct(p)}
                        className="w-full px-4 py-3 text-left hover:bg-[#f9fbf9] transition-colors"
                      >
                        <p className="text-sm font-bold text-[var(--ink)]">{p.name}</p>
                        <p className="text-xs text-[var(--muted)]">{p.description?.slice(0, 60) ?? ""}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Step 2: Pick a variant */}
      {selectedProduct && (
        <div className="rounded-xl border border-[var(--line)] bg-white p-6">
          <h2 className="font-bold">Step 2 — Select a variant</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Each variant is a specific version of the product (e.g. Color=Black, Storage=128GB). You&apos;ll create one listing per variant.
          </p>
          {productVariants.length === 0 ? (
            <p className="mt-4 rounded-lg bg-[#fbf0ce] px-4 py-3 text-xs text-[#b58a24]">
              This product has no active variants yet. Variants need to be added and approved before you can create a listing.
            </p>
          ) : (
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {productVariants.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVariant(v)}
                  className={`rounded-lg border px-4 py-3 text-left transition-colors ${selectedVariant?.id === v.id ? "border-[var(--teal)] bg-[#f0faf6]" : "border-[var(--line)] bg-[#f9fbf9] hover:border-[var(--teal)]"}`}
                >
                  <p className="font-mono text-[10px] text-[var(--muted)]">{v.id.slice(0, 8)}</p>
                  {v.sku_code && <p className="mt-0.5 text-xs font-bold text-[var(--ink)]">SKU: {v.sku_code}</p>}
                  {v.attribute_values.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {v.attribute_values.map((av) => (
                        <span key={av.attribute_id} className="rounded-full bg-white border border-[var(--line)] px-2 py-0.5 text-[10px] text-[var(--muted)]">
                          {av.value}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-1 text-xs text-[var(--muted)]">No attribute values</p>
                  )}
                  {selectedVariant?.id === v.id && (
                    <p className="mt-2 text-[10px] font-bold text-[var(--teal)]">✓ Selected</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Listing details */}
      {selectedVariant && (
        <div className="rounded-xl border border-[var(--line)] bg-white p-6">
          <h2 className="font-bold">Step 3 — Your listing details</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">Set your price, stock, and condition. These are specific to your listing — other sellers can list the same variant at different prices.</p>
          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-semibold">
                Price (RWF)
                <Input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  placeholder="e.g. 25000"
                  className="mt-2"
                />
              </label>
              <label className="block text-sm font-semibold">
                Stock quantity
                <Input
                  required
                  type="number"
                  min="0"
                  step="1"
                  value={form.stock}
                  onChange={(e) => setForm({ ...form, stock: e.target.value })}
                  placeholder="e.g. 50"
                  className="mt-2"
                />
              </label>
            </div>
            <label className="block text-sm font-semibold">
              Condition
              <select
                value={form.condition}
                onChange={(e) => setForm({ ...form, condition: e.target.value as Condition })}
                className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
              >
                <option value="new">New</option>
                <option value="like_new">Like new</option>
                <option value="used">Used</option>
              </select>
            </label>
            <label className="block text-sm font-semibold">
              Your SKU code (optional)
              <Input
                value={form.seller_sku}
                onChange={(e) => setForm({ ...form, seller_sku: e.target.value })}
                placeholder="Your internal reference code"
                className="mt-2"
              />
            </label>
            <div className="rounded-lg bg-[#f9fbf9] border border-[var(--line)] px-4 py-3 text-xs text-[var(--muted)]">
              After creating, go to <strong>My Listings</strong> to submit for admin review. Your listing won&apos;t be visible to buyers until it&apos;s approved.
            </div>
            <Button type="submit" disabled={saving}>
              {saving ? "Creating..." : "Create listing"}
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
