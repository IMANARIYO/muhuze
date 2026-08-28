"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, Check, ChevronDown, Clock3, Package, Plus, Send, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { useAuth } from "@/app/context/auth-context";
import { adminService } from "@/app/services/admin.service";
import { productService, type ProductRecord, type VariantRecord } from "@/app/services/product.service";

const statusColors: Record<string, { bg: string; text: string }> = {
  draft: { bg: "#f2f5f2", text: "#7e8b84" },
  pending_review: { bg: "#fbf0ce", text: "#b58a24" },
  active: { bg: "#e8f4ed", text: "#2d7a5e" },
  rejected: { bg: "#fbe6e0", text: "#b74d3b" },
  archived: { bg: "#f2f5f2", text: "#7e8b84" },
};

export default function ProductsPage() {
  const { user, hasRole } = useAuth();
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [variants, setVariants] = useState<Record<string, VariantRecord[]>>({});
  const [rejectTarget, setRejectTarget] = useState<ProductRecord | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const isAdmin = hasRole("admin");

  async function load() {
    setLoading(true);
    try {
      const data = isAdmin
        ? await adminService.listProducts({ status: statusFilter === "all" ? undefined : statusFilter })
        : await productService.listMine();
      setProducts(data);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Products could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    async function init() {
      setLoading(true);
      try {
        const data = isAdmin
          ? await adminService.listProducts({ status: statusFilter === "all" ? undefined : statusFilter })
          : await productService.listMine();
        if (!cancelled) { setProducts(data); setError(""); }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Products could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void init();
    return () => { cancelled = true; };
  }, [isAdmin, user, statusFilter]);

  async function toggleExpand(product: ProductRecord) {
    if (expandedId === product.id) { setExpandedId(null); return; }
    setExpandedId(product.id);
    if (!variants[product.id]) {
      try {
        const v = await productService.listVariants(product.id);
        setVariants((prev) => ({ ...prev, [product.id]: v }));
      } catch {
        setVariants((prev) => ({ ...prev, [product.id]: [] }));
      }
    }
  }

  async function approve(id: string) {
    try { await adminService.approveProduct(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Approval failed."); }
  }

  async function confirmReject() {
    if (!rejectTarget || !rejectReason.trim()) return;
    try {
      await adminService.rejectProduct(rejectTarget.id, rejectReason);
      setRejectTarget(null); setRejectReason("");
      await load();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Rejection failed."); }
  }

  async function archive(id: string) {
    try { await adminService.archiveProduct(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Archive failed."); }
  }

  async function submitProduct(id: string) {
    try { await productService.submit(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Submission failed."); }
  }

  const pending = products.filter((p) => p.status === "pending_review");
  const rest = products.filter((p) => p.status !== "pending_review");

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">
            {isAdmin ? "Admin workspace" : "Seller workspace"}
          </p>
          <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">
            {isAdmin ? "Product review" : "My product requests"}
          </h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {isAdmin
              ? "Approve or reject catalog product requests from sellers."
              : "Request new catalog products and track their review status."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isAdmin && (
            <div className="flex gap-1.5 flex-wrap">
              {["all", "pending_review", "active", "rejected", "draft", "archived"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`rounded-full px-3 py-1.5 text-[11px] font-bold capitalize transition-colors ${statusFilter === s ? "bg-[var(--ink)] text-white" : "bg-white border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)]"}`}
                >
                  {s === "all" ? "All" : s.replace("_", " ")}
                </button>
              ))}
            </div>
          )}
          {!isAdmin && (
            <Link href="/dashboard/products/new">
              <Button><Plus size={15} /> Request product</Button>
            </Link>
          )}
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {/* Reject modal */}
      {rejectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Reject &ldquo;{rejectTarget.name}&rdquo;</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Give the seller a clear reason so they can fix and resubmit.</p>
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
            {isAdmin ? "Seller product requests will appear here." : "Request your first product to get started."}
          </p>
          {!isAdmin && (
            <Link href="/dashboard/products/new" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[var(--ink)] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#2e3d38] transition-colors">
              <Plus size={14} /> Request a product
            </Link>
          )}
        </div>
      ) : (
        <>
          {/* Pending highlight for admin */}
          {isAdmin && pending.length > 0 && statusFilter === "all" && (
            <div className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] px-5 py-4">
              <p className="text-sm font-bold text-[#b58a24]">{pending.length} product{pending.length > 1 ? "s" : ""} waiting for your review</p>
            </div>
          )}

          <div className="space-y-4">
            {products.map((product) => {
              const colors = statusColors[product.status] ?? statusColors.draft;
              const isExpanded = expandedId === product.id;
              const productVariants = variants[product.id];

              return (
                <article key={product.id} className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                  <div className="flex items-start gap-4 p-5">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#f2f5f2] text-[var(--muted)]">
                      <Package size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="font-bold text-[var(--ink)]">{product.name}</h2>
                        <span
                          className="rounded-full px-2.5 py-0.5 text-[10px] font-bold capitalize"
                          style={{ backgroundColor: colors.bg, color: colors.text }}
                        >
                          {product.status.replace("_", " ")}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2">{product.description || "No description provided."}</p>
                      <p className="mt-2 text-[10px] text-[var(--muted)]">
                        Created {new Date(product.created_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                        <span className="ml-2 font-mono">{product.id.slice(0, 8)}</span>
                      </p>
                      {product.rejection_reason && (
                        <p className="mt-2 rounded-lg bg-[#fbe6e0] px-3 py-2 text-xs text-[#b74d3b]">
                          Rejection reason: {product.rejection_reason}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => toggleExpand(product)}
                      className="shrink-0 rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[#f9fbf9] transition-colors"
                      aria-label="Toggle variants"
                    >
                      <ChevronDown size={15} className={`transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                    </button>
                  </div>

                  {/* Actions bar */}
                  <div className="flex gap-2 flex-wrap border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                    {isAdmin && product.status === "pending_review" && (
                      <>
                        <Button size="sm" onClick={() => approve(product.id)}><Check size={14} /> Approve</Button>
                        <Button size="sm" variant="outline" onClick={() => setRejectTarget(product)}><X size={14} /> Reject</Button>
                      </>
                    )}
                    {isAdmin && product.status === "active" && (
                      <Button size="sm" variant="outline" onClick={() => archive(product.id)}><Archive size={14} /> Archive</Button>
                    )}
                    {!isAdmin && product.status === "draft" && (
                      <Button size="sm" onClick={() => submitProduct(product.id)}><Send size={14} /> Submit for review</Button>
                    )}
                    {!isAdmin && product.status === "pending_review" && (
                      <p className="flex items-center gap-2 text-xs text-[#b58a24]"><Clock3 size={13} /> Waiting for admin review</p>
                    )}
                    {!isAdmin && product.status === "active" && (
                      <Link href="/dashboard/listings" className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline">
                        Create a listing for this product →
                      </Link>
                    )}
                    <button
                      onClick={() => toggleExpand(product)}
                      className="ml-auto flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline"
                    >
                      {isExpanded ? "Hide" : "View"} variants
                    </button>
                  </div>

                  {/* Variants panel */}
                  {isExpanded && (
                    <div className="border-t border-[var(--line)] p-5">
                      <p className="mb-3 text-xs font-bold text-[var(--ink)]">Variants (SKUs)</p>
                      {!productVariants ? (
                        <p className="text-xs text-[var(--muted)]">Loading variants...</p>
                      ) : productVariants.length === 0 ? (
                        <p className="text-xs text-[var(--muted)]">No variants yet. Variants define the specific versions of this product (e.g. Color=Black, Storage=128GB).</p>
                      ) : (
                        <div className="grid gap-2 sm:grid-cols-2">
                          {productVariants.map((v) => (
                            <div key={v.id} className="rounded-lg border border-[var(--line)] bg-[#f9fbf9] px-4 py-3">
                              <div className="flex items-center justify-between gap-2">
                                <p className="font-mono text-[10px] text-[var(--muted)]">{v.id.slice(0, 8)}</p>
                                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${v.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>
                                  {v.status}
                                </span>
                              </div>
                              {v.sku_code && <p className="mt-1 text-xs font-bold text-[var(--ink)]">SKU: {v.sku_code}</p>}
                              {v.attribute_values.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-1.5">
                                  {v.attribute_values.map((av) => (
                                    <span key={av.attribute_id} className="rounded-full bg-white border border-[var(--line)] px-2 py-0.5 text-[10px] text-[var(--muted)]">
                                      {av.value}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
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
