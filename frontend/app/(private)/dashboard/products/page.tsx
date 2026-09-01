"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  Archive, Check, ChevronDown, ImagePlus, Package, Pencil, Plus,
  Star, Trash2, X,
} from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { useAuth } from "@/app/context/auth-context";
import { adminService, type AttributeRecord } from "@/app/services/admin.service";
import { productService, type ProductRecord, type VariantRecord } from "@/app/services/product.service";

interface ProductImage { id: string; product_id: string; url: string; is_primary: boolean; sort_order: number; created_at: string; }

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  draft: { bg: "#f2f5f2", text: "#7e8b84" },
  pending_review: { bg: "#fbf0ce", text: "#b58a24" },
  active: { bg: "#e8f4ed", text: "#2d7a5e" },
  rejected: { bg: "#fbe6e0", text: "#b74d3b" },
  archived: { bg: "#f2f5f2", text: "#7e8b84" },
};

const STATUS_FILTERS = ["all", "pending_review", "active", "rejected", "draft", "archived"];

// ─── Variant add form (seller) ────────────────────────────────────────────────
function AddVariantForm({ productId, onDone }: { productId: string; onDone: () => void }) {
  const [attributes, setAttributes] = useState<Array<{ attribute_id: string; value: string }>>([{ attribute_id: "", value: "" }]);
  const [sku, setSku] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [attrList, setAttrList] = useState<Array<{ id: string; name: string }>>([]);

  useEffect(() => {
    adminService.listAttributes().then((a) => setAttrList(a.filter((x) => x.status === "active"))).catch(() => {});
  }, []);

  const hasAttributes = attrList.length > 0;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const filled = attributes.filter((a) => a.attribute_id && a.value.trim());
    if (filled.length === 0) { setError("Add at least one attribute value."); return; }
    setSaving(true); setError("");
    try {
      await productService.createVariant(productId, { sku_code: sku || undefined, attribute_values: filled });
      onDone();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Variant could not be created.");
    } finally { setSaving(false); }
  }

  return (
    <form onSubmit={submit} className="mt-4 rounded-lg border border-[var(--line)] bg-[#f9fbf9] p-4 space-y-3">
      <p className="text-xs font-bold text-[var(--ink)]">Add variant</p>
      <label className="block text-xs font-semibold">
        SKU code <span className="font-normal text-[var(--muted)]">(optional)</span>
        <Input value={sku} onChange={(e) => setSku(e.target.value)} placeholder="e.g. SAM-S24-BLK-256" className="mt-1 h-8 text-xs" />
      </label>
      <div className="space-y-2">
        <p className="text-xs font-semibold">Attribute values</p>
        {!hasAttributes && (
          <p className="rounded-lg bg-[#fbf0ce] px-3 py-2 text-xs text-[#b58a24]">
            No attributes available yet — an admin needs to create attributes in Catalog setup before a variant can be added.
          </p>
        )}
        {attributes.map((attr, i) => (
          <div key={i} className="flex gap-2">
            <select
              value={attr.attribute_id}
              onChange={(e) => { const a = [...attributes]; a[i] = { ...a[i], attribute_id: e.target.value }; setAttributes(a); }}
              className="flex-1 h-8 rounded-lg border border-[var(--line)] bg-white px-2 text-xs outline-none focus:border-[var(--teal)]"
            >
              <option value="">Select attribute</option>
              {attrList.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <Input
              value={attr.value}
              onChange={(e) => { const a = [...attributes]; a[i] = { ...a[i], value: e.target.value }; setAttributes(a); }}
              placeholder="Value (e.g. Black)"
              className="flex-1 h-8 text-xs"
            />
            {attributes.length > 1 && (
              <button type="button" onClick={() => setAttributes(attributes.filter((_, j) => j !== i))} className="text-[#b74d3b]"><X size={13} /></button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => setAttributes([...attributes, { attribute_id: "", value: "" }])} className="text-[10px] font-bold text-[var(--teal)] hover:underline">
          + Add another attribute
        </button>
      </div>
      {error && <p className="text-xs text-[#b74d3b]">{error}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={saving}>{saving ? "Saving..." : "Add variant"}</Button>
        <Button type="button" size="sm" variant="outline" onClick={onDone}>Cancel</Button>
      </div>
    </form>
  );
}

// ─── Image strip (admin) ──────────────────────────────────────────────────────
function ImageStrip({ productId }: { productId: string }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [images, setImages] = useState<ProductImage[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    productService.listProductImages(productId).then(setImages).catch(() => setImages([]));
  }, [productId]);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true); setError("");
    try {
      await productService.uploadProductImage(productId, file, (images ?? []).length === 0);
      setImages(await productService.listProductImages(productId));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Upload failed."); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function remove(imageId: string) {
    try {
      await productService.deleteProductImage(productId, imageId);
      setImages(await productService.listProductImages(productId));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Delete failed."); }
  }

  if (images === null) return <p className="text-xs text-[var(--muted)]">Loading images...</p>;

  return (
    <div>
      {error && <p className="mb-2 text-xs text-[#b74d3b]">{error}</p>}
      <div className="flex flex-wrap gap-2 items-center">
        {images.map((img) => (
          <div key={img.id} className="group relative h-16 w-16 rounded-lg overflow-hidden border border-[var(--line)] bg-[#f2f5f2]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={img.url} alt="" className="h-full w-full object-cover" />
            {img.is_primary && <Star size={9} className="absolute top-1 left-1 text-white fill-white drop-shadow" />}
            <button onClick={() => remove(img.id)} className="absolute inset-0 hidden group-hover:flex items-center justify-center bg-black/40 text-white">
              <Trash2 size={13} />
            </button>
          </div>
        ))}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="flex h-16 w-16 flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-[var(--line)] bg-[#f9fbf9] text-[var(--muted)] hover:border-[var(--teal)] hover:text-[var(--teal)] transition-colors disabled:opacity-60"
        >
          <ImagePlus size={16} />
          <span className="text-[9px] font-bold">{uploading ? "..." : "Upload"}</span>
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={upload} />
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function ProductsPage() {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole("admin");

  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // expanded panels
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [variants, setVariants] = useState<Record<string, VariantRecord[]>>({});
  const [showAddVariant, setShowAddVariant] = useState<string | null>(null);
  const [showImages, setShowImages] = useState<string | null>(null);
  const [attrMap, setAttrMap] = useState<Record<string, AttributeRecord>>({});

  // admin modals
  const [rejectTarget, setRejectTarget] = useState<ProductRecord | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // seller search
  const [search, setSearch] = useState("");

  async function load() {
    setLoading(true);
    try {
      const data = isAdmin
        ? await adminService.listProducts({ status: statusFilter === "all" ? undefined : statusFilter })
        : await productService.list({ status: "active", search: search || undefined });
      setProducts(data);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Products could not be loaded.");
    } finally { setLoading(false); }
  }

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    async function init() {
      setLoading(true);
      try {
        const data = isAdmin
          ? await adminService.listProducts({ status: statusFilter === "all" ? undefined : statusFilter })
          : await productService.list({ status: "active" });
        if (!cancelled) { setProducts(data); setError(""); }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Products could not be loaded.");
      } finally { if (!cancelled) setLoading(false); }
    }
    void init();
    return () => { cancelled = true; };
  }, [isAdmin, user, statusFilter]);

  // seller debounced search
  useEffect(() => {
    if (isAdmin) return;
    const t = setTimeout(() => load(), 350);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  async function toggleVariants(product: ProductRecord) {
    if (expandedId === product.id) { setExpandedId(null); return; }
    setExpandedId(product.id);
    if (!variants[product.id]) {
      try {
        const v = await productService.listVariants(product.id);
        setVariants((prev) => ({ ...prev, [product.id]: v }));
      } catch { setVariants((prev) => ({ ...prev, [product.id]: [] })); }
    }
    if (Object.keys(attrMap).length === 0) {
      try {
        const list = await adminService.listAttributes();
        const map: Record<string, AttributeRecord> = {};
        for (const a of list) map[a.id] = a;
        setAttrMap(map);
      } catch { /* attribute names are a nice-to-have */ }
    }
  }

  async function reloadVariants(productId: string) {
    try {
      const v = await productService.listVariants(productId);
      setVariants((prev) => ({ ...prev, [productId]: v }));
    } catch { /* ignore */ }
    setShowAddVariant(null);
  }

  async function approve(id: string) {
    try { await adminService.approveProduct(id); await load(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Approval failed."); }
  }

  async function confirmReject() {
    if (!rejectTarget || !rejectReason.trim()) return;
    try {
      await adminService.rejectProduct(rejectTarget.id, rejectReason);
      setRejectTarget(null); setRejectReason(""); await load();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Rejection failed."); }
  }

  async function archive(id: string) {
    try { await adminService.archiveProduct(id); await load(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Archive failed."); }
  }

  const pending = products.filter((p) => p.status === "pending_review");

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">
            {isAdmin ? "Admin workspace" : "Seller workspace"}
          </p>
          <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">
            {isAdmin ? "Product catalog" : "Catalog products"}
          </h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {isAdmin
              ? "Create and manage the shared product catalog. Sellers add variants and listings on top."
              : "Browse active catalog products and add your variants to start selling."}
          </p>
        </div>
        <div className="flex flex-col gap-3 items-end">
          {isAdmin && (
            <>
              <div className="flex gap-1.5 flex-wrap justify-end">
                {STATUS_FILTERS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`rounded-full px-3 py-1.5 text-[11px] font-bold capitalize transition-colors ${statusFilter === s ? "bg-[var(--ink)] text-white" : "bg-white border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)]"}`}
                  >
                    {s === "all" ? "All" : s.replace("_", " ")}
                  </button>
                ))}
              </div>
              <Link href="/dashboard/products/new">
                <Button><Plus size={15} /> Create product</Button>
              </Link>
            </>
          )}
          {!isAdmin && (
            <div className="w-64">
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products..."
                className="h-9"
              />
            </div>
          )}
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {/* Reject modal */}
      {rejectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Reject &ldquo;{rejectTarget.name}&rdquo;</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Give a clear reason so the requester can fix and resubmit.</p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Product name is too generic. Please provide a specific model name."
              className="mt-4 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] min-h-[100px]"
            />
            <div className="mt-4 flex gap-2 justify-end">
              <Button variant="outline" onClick={() => { setRejectTarget(null); setRejectReason(""); }}>Cancel</Button>
              <Button onClick={confirmReject} disabled={!rejectReason.trim()}>Confirm rejection</Button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading products...</div>
      ) : products.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <Package className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">Nothing here yet</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {isAdmin ? "Create the first catalog product to get started." : "No active catalog products found."}
          </p>
          {isAdmin && (
            <Link href="/dashboard/products/new" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[var(--ink)] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#2e3d38] transition-colors">
              <Plus size={14} /> Create product
            </Link>
          )}
        </div>
      ) : (
        <>
          {isAdmin && pending.length > 0 && statusFilter === "all" && (
            <div className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] px-5 py-4">
              <p className="text-sm font-bold text-[#b58a24]">{pending.length} product{pending.length > 1 ? "s" : ""} waiting for your review</p>
            </div>
          )}

          <div className="space-y-4">
            {products.map((product) => {
              const colors = STATUS_COLORS[product.status] ?? STATUS_COLORS.draft;
              const isExpanded = expandedId === product.id;
              const productVariants = variants[product.id];

              return (
                <article key={product.id} className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                  {/* Card header */}
                  <div className="flex items-start gap-4 p-5">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#f2f5f2] text-[var(--muted)]">
                      <Package size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="font-bold text-[var(--ink)]">{product.name}</h2>
                        <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold capitalize" style={{ backgroundColor: colors.bg, color: colors.text }}>
                          {product.status.replace("_", " ")}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2">{product.description || "No description."}</p>
                      <p className="mt-2 text-[10px] text-[var(--muted)]">
                        {new Date(product.created_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                        <span className="ml-2 font-mono">{product.id.slice(0, 8)}</span>
                      </p>
                      {product.rejection_reason && (
                        <p className="mt-2 rounded-lg bg-[#fbe6e0] px-3 py-2 text-xs text-[#b74d3b]">Rejection reason: {product.rejection_reason}</p>
                      )}
                    </div>
                    <button
                      onClick={() => toggleVariants(product)}
                      className="shrink-0 rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[#f9fbf9] transition-colors"
                    >
                      <ChevronDown size={15} className={`transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                    </button>
                  </div>

                  {/* Actions bar */}
                  <div className="flex gap-2 flex-wrap items-center border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                    {isAdmin && (
                      <>
                        {product.status === "pending_review" && (
                          <>
                            <Button size="sm" onClick={() => approve(product.id)}><Check size={14} /> Approve</Button>
                            <Button size="sm" variant="outline" onClick={() => setRejectTarget(product)}><X size={14} /> Reject</Button>
                          </>
                        )}
                        {(product.status === "draft" || product.status === "rejected") && (
                          <Link href={`/dashboard/products/${product.id}`}>
                            <Button size="sm" variant="outline"><Pencil size={13} /> Edit</Button>
                          </Link>
                        )}
                        {product.status === "active" && (
                          <Button size="sm" variant="outline" onClick={() => archive(product.id)}><Archive size={14} /> Archive</Button>
                        )}
                      </>
                    )}

                    {!isAdmin && product.status === "active" && (
                      <>
                        <button
                          onClick={() => { setShowAddVariant(showAddVariant === product.id ? null : product.id); toggleVariants(product); }}
                          className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline"
                        >
                          <Plus size={13} /> Add variant
                        </button>
                        <Link href="/dashboard/listings/new" className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--muted)] hover:underline">
                          Create listing →
                        </Link>
                      </>
                    )}

                    {product.status === "active" && (
                      <button
                        onClick={() => setShowImages(showImages === product.id ? null : product.id)}
                        className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline"
                      >
                        <ImagePlus size={13} /> {showImages === product.id ? "Hide images" : "Manage images"}
                      </button>
                    )}

                    <button
                      onClick={() => toggleVariants(product)}
                      className="ml-auto flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline"
                    >
                      {isExpanded ? "Hide" : "View"} variants
                    </button>
                  </div>

                  {/* Images panel (active products, admin or seller) */}
                  {showImages === product.id && (
                    <div className="border-t border-[var(--line)] p-5">
                      <p className="mb-3 text-xs font-bold text-[var(--ink)]">Catalog images</p>
                      <ImageStrip productId={product.id} />
                    </div>
                  )}

                  {/* Variants panel */}
                  {isExpanded && (
                    <div className="border-t border-[var(--line)] bg-[#fbfdfb] px-5 py-5">
                      <div className="mb-4 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Package size={15} className="text-[var(--teal)]" />
                          <p className="text-sm font-bold text-[var(--ink)]">Variants (SKUs)</p>
                          {productVariants && productVariants.length > 0 && (
                            <span className="rounded-full bg-[#e8f4ed] px-2 py-0.5 text-[10px] font-bold text-[#2d7a5e]">
                              {productVariants.length}
                            </span>
                          )}
                        </div>
                      </div>
                      {!productVariants ? (
                        <p className="text-xs text-[var(--muted)]">Loading variants...</p>
                      ) : productVariants.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white px-6 py-8 text-center">
                          <Package size={22} className="mx-auto text-[var(--muted)]" />
                          <p className="mt-3 text-xs font-semibold text-[var(--ink)]">No variants yet</p>
                          <p className="mt-1 text-xs text-[var(--muted)]">Add a variant to offer this product in different configurations.</p>
                        </div>
                      ) : (
                        <div className="grid gap-3 lg:grid-cols-2">
                          {productVariants.map((v, idx) => (
                            <div key={v.id} className="overflow-hidden rounded-xl border border-[var(--line)] bg-white shadow-sm">
                              <div className="flex items-center justify-between gap-2 border-b border-[var(--line)] bg-[#f6f9f7] px-4 py-2.5">
                                <p className="text-xs font-bold text-[var(--ink)]">Variant {idx + 1}</p>
                                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold capitalize ${v.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>
                                  {v.status}
                                </span>
                              </div>
                              <div className="px-4 py-3">
                                {v.sku_code ? (
                                  <div className="mb-3 flex items-center gap-1.5">
                                    <span className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">SKU</span>
                                    <span className="font-mono text-xs font-semibold text-[var(--ink)]">{v.sku_code}</span>
                                  </div>
                                ) : (
                                  <div className="mb-3 flex items-center gap-1.5">
                                    <span className="text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">SKU</span>
                                    <span className="text-xs text-[var(--muted)]">—</span>
                                  </div>
                                )}
                                {v.attribute_values.length > 0 ? (
                                  <dl className="grid grid-cols-1 gap-y-1.5">
                                    {v.attribute_values.map((av) => {
                                      const attr = attrMap[av.attribute_id];
                                      const label = attr?.name ?? "Attribute";
                                      const unit = attr?.unit ? ` ${attr.unit}` : "";
                                      return (
                                        <div key={av.attribute_id} className="flex items-center justify-between gap-3 rounded-lg bg-[#fafcfb] px-3 py-1.5">
                                          <dt className="text-[11px] font-semibold text-[var(--muted)]">{label}</dt>
                                          <dd className="text-xs font-bold text-[var(--ink)]">{av.value}{unit}</dd>
                                        </div>
                                      );
                                    })}
                                  </dl>
                                ) : (
                                  <p className="text-xs text-[var(--muted)]">No attribute values</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Seller: add variant form */}
                      {!isAdmin && showAddVariant === product.id && (
                        <AddVariantForm productId={product.id} onDone={() => reloadVariants(product.id)} />
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
