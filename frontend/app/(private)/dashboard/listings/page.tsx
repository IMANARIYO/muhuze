"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Check, DollarSign, Package, Plus, Send, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { useAuth } from "@/app/context/auth-context";
import { adminService } from "@/app/services/admin.service";
import { productService, type ListingRecord } from "@/app/services/product.service";

const statusColors: Record<string, { bg: string; text: string }> = {
  draft: { bg: "#f2f5f2", text: "#7e8b84" },
  pending_review: { bg: "#fbf0ce", text: "#b58a24" },
  active: { bg: "#e8f4ed", text: "#2d7a5e" },
  rejected: { bg: "#fbe6e0", text: "#b74d3b" },
  suspended: { bg: "#fbe6e0", text: "#b74d3b" },
  out_of_stock: { bg: "#f2f5f2", text: "#7e8b84" },
  archived: { bg: "#f2f5f2", text: "#7e8b84" },
};

export default function ListingsPage() {
  const { user, hasRole } = useAuth();
  const [listings, setListings] = useState<ListingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rejectId, setRejectId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const isAdmin = hasRole("admin");

  async function load() {
    setLoading(true);
    try {
      setListings(isAdmin ? await adminService.listListings() : await productService.listListings());
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Listings could not be loaded.");
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
        const data = isAdmin ? await adminService.listListings() : await productService.listListings();
        if (!cancelled) { setListings(data); setError(""); }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Listings could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void init();
    return () => { cancelled = true; };
  }, [isAdmin, user]);

  async function submitListing(id: string) {
    try { await productService.submitListing(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Listing could not be submitted."); }
  }

  async function approveListing(id: string) {
    try { await adminService.approveListing(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Listing could not be approved."); }
  }

  async function confirmReject() {
    if (!rejectId || !rejectReason.trim()) return;
    try { await adminService.rejectListing(rejectId, rejectReason); setRejectId(null); setRejectReason(""); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Listing could not be rejected."); }
  }

  async function suspendListing(id: string) {
    try { await adminService.suspendListing(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Listing could not be suspended."); }
  }

  async function reactivateListing(id: string) {
    try { await adminService.reactivateListing(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Listing could not be reactivated."); }
  }

  const pending = listings.filter((l) => l.status === "pending_review");
  const rest = listings.filter((l) => l.status !== "pending_review");

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">
          {isAdmin ? "Admin workspace" : "Seller workspace"}
        </p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">
          {isAdmin ? "Listing review" : "My listings"}
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          {isAdmin
            ? "Approve or reject seller listing submissions before they go live."
            : "Your offers, prices, stock, and review status. A listing is what clients can actually buy."}
        </p>
      </div>
      {!isAdmin && (
        <Link href="/dashboard/listings/new">
          <Button><Plus size={15} /> Create listing</Button>
        </Link>
      )}

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {/* Reject modal */}
      {rejectId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Reject listing</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Give the seller a clear reason so they can fix and resubmit.</p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Price appears incorrect, please verify and resubmit."
              className="mt-4 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] min-h-[100px]"
            />
            <div className="mt-4 flex gap-2 justify-end">
              <Button variant="outline" onClick={() => { setRejectId(null); setRejectReason(""); }}>Cancel</Button>
              <Button onClick={confirmReject} disabled={!rejectReason.trim()}>Confirm rejection</Button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading listings...</div>
      ) : listings.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <Package className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">No listings yet</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {isAdmin ? "Seller listing submissions will appear here." : "Create a listing after an approved product has an active variant."}
          </p>
        </div>
      ) : (
        <>
          {/* Pending section for admin */}
          {isAdmin && pending.length > 0 && (
            <section>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[.1em] text-[#a4aaa6]">Awaiting review — {pending.length}</p>
              <div className="grid gap-4 md:grid-cols-2">
                {pending.map((listing) => (
                  <article key={listing.id} className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-mono text-[11px] text-[var(--muted)]">Listing {listing.id.slice(0, 8)}</p>
                        <p className="mt-1 text-sm font-bold text-[var(--ink)]">
                          <DollarSign size={13} className="inline -mt-0.5" />{listing.price.toFixed(2)} · {listing.stock} in stock
                        </p>
                        <p className="mt-1 text-xs text-[var(--muted)] capitalize">{listing.condition.replace("_", " ")} condition</p>
                      </div>
                      <span className="rounded-full bg-[#fbf0ce] px-2.5 py-1 text-[10px] font-bold text-[#b58a24]">Pending review</span>
                    </div>
                    <div className="mt-4 flex gap-2 border-t border-[#f0d98a] pt-4">
                      <Button size="sm" onClick={() => approveListing(listing.id)}><Check size={14} /> Approve</Button>
                      <Button size="sm" variant="outline" onClick={() => setRejectId(listing.id)}><X size={14} /> Reject</Button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* All listings table */}
          <section>
            {isAdmin && rest.length > 0 && <p className="mb-3 text-[10px] font-bold uppercase tracking-[.1em] text-[#a4aaa6]">All listings</p>}
            <div className="overflow-hidden rounded-xl border border-[var(--line)] bg-white">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[700px] text-left text-xs">
                  <thead className="border-b border-[var(--line)] bg-[#f9fbf9] text-[var(--muted)]">
                    <tr>
                      <th className="px-5 py-3">ID</th>
                      <th className="px-5 py-3">Price</th>
                      <th className="px-5 py-3">Stock</th>
                      <th className="px-5 py-3">Condition</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3">Created</th>
                      <th className="px-5 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#eff1ef]">
                    {(isAdmin ? rest : listings).map((listing) => {
                      const colors = statusColors[listing.status] ?? statusColors.draft;
                      return (
                        <tr key={listing.id} className="hover:bg-[#f9fbf9]">
                          <td className="px-5 py-4 font-mono text-[10px] text-[var(--muted)]">{listing.id.slice(0, 8)}</td>
                          <td className="px-5 py-4 font-bold">${listing.price.toFixed(2)}</td>
                          <td className="px-5 py-4">{listing.stock}</td>
                          <td className="px-5 py-4 capitalize text-[var(--muted)]">{listing.condition.replace("_", " ")}</td>
                          <td className="px-5 py-4">
                            <span className="rounded-full px-2 py-1 text-[10px] font-bold capitalize" style={{ backgroundColor: colors.bg, color: colors.text }}>
                              {listing.status.replace(/_/g, " ")}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-[var(--muted)]">{new Date(listing.created_at).toLocaleDateString()}</td>
                          <td className="px-5 py-4">
                            <div className="flex gap-1.5">
                              {!isAdmin && ["draft", "rejected"].includes(listing.status) && (
                                <Button size="sm" variant="outline" onClick={() => submitListing(listing.id)}><Send size={12} /> Submit</Button>
                              )}
                              {isAdmin && listing.status === "active" && (
                                <Button size="sm" variant="outline" onClick={() => suspendListing(listing.id)}>Suspend</Button>
                              )}
                              {isAdmin && listing.status === "suspended" && (
                                <Button size="sm" onClick={() => reactivateListing(listing.id)}>Reactivate</Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
