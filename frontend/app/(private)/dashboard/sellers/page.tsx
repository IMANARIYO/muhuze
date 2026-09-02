"use client";

import { useEffect, useState } from "react";
import { Check, ChevronDown, FileText, UserRound, X } from "lucide-react";
import { DocumentViewer } from "./document-viewer";
import { Button } from "@/app/_components/ui/button";
import { adminService } from "@/app/services/admin.service";
import { sellerService, type SellerDocument, type SellerProfile } from "@/app/services/seller.service";

type StatusFilter = "all" | SellerProfile["status"];

const statusColors: Record<string, { bg: string; text: string }> = {
  draft: { bg: "#f2f5f2", text: "#7e8b84" },
  pending_review: { bg: "#fbf0ce", text: "#b58a24" },
  active: { bg: "#e8f4ed", text: "#2d7a5e" },
  rejected: { bg: "#fbe6e0", text: "#b74d3b" },
  suspended: { bg: "#fbe6e0", text: "#b74d3b" },
  deactivated: { bg: "#f2f5f2", text: "#7e8b84" },
};

export default function SellerReviewPage() {
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Record<string, SellerDocument[]>>({});
  const [rejectTarget, setRejectTarget] = useState<SellerProfile | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [suspendTarget, setSuspendTarget] = useState<SellerProfile | null>(null);
  const [suspendReason, setSuspendReason] = useState("");
  const [viewDoc, setViewDoc] = useState<SellerDocument | null>(null);

  async function load() {
    setLoading(true);
    try {
      setSellers(await adminService.listSellers(filter === "all" ? undefined : filter));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sellers could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setLoading(true);
      try {
        const data = await adminService.listSellers(filter === "all" ? undefined : filter);
        if (!cancelled) { setSellers(data); setError(""); }
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Sellers could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void init();
    return () => { cancelled = true; };
  }, [filter]);

  async function toggleExpand(seller: SellerProfile) {
    if (expandedId === seller.id) { setExpandedId(null); return; }
    setExpandedId(seller.id);
    if (!documents[seller.id]) {
      try {
        const docs = await sellerService.getDocumentForReview(seller.id);
        setDocuments((prev) => ({ ...prev, [seller.id]: docs }));
      } catch {
        setDocuments((prev) => ({ ...prev, [seller.id]: [] }));
      }
    }
  }

  async function approve(id: string) {
    try { await adminService.approveSeller(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Approval failed."); }
  }

  async function confirmReject() {
    if (!rejectTarget || !rejectReason.trim()) return;
    try { await adminService.rejectSeller(rejectTarget.id, rejectReason); setRejectTarget(null); setRejectReason(""); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Rejection failed."); }
  }

  async function confirmSuspend() {
    if (!suspendTarget) return;
    try { await adminService.suspendSeller(suspendTarget.id, suspendReason || undefined); setSuspendTarget(null); setSuspendReason(""); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Suspension failed."); }
  }

  async function reactivate(id: string) {
    try { await adminService.reactivateSeller(id); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Reactivation failed."); }
  }

  const pending = sellers.filter((s) => s.status === "pending_review");

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
          <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Seller review</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">Review applications, inspect identity documents, and manage seller status.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {(["all", "pending_review", "active", "rejected", "suspended", "draft"] as StatusFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`rounded-full px-3 py-1.5 text-[11px] font-bold capitalize transition-colors ${filter === s ? "bg-[var(--ink)] text-white" : "bg-white border border-[var(--line)] text-[var(--muted)] hover:border-[var(--ink)]"}`}
            >
              {s === "all" ? "All" : s.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {/* Reject modal */}
      {rejectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Reject {rejectTarget.business_name}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Provide a clear reason. The seller will see this and can edit and resubmit.</p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Identity document is unclear. Please upload a higher-quality scan."
              className="mt-4 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] min-h-[100px]"
            />
            <div className="mt-4 flex gap-2 justify-end">
              <Button variant="outline" onClick={() => { setRejectTarget(null); setRejectReason(""); }}>Cancel</Button>
              <Button onClick={confirmReject} disabled={!rejectReason.trim()}>Confirm rejection</Button>
            </div>
          </div>
        </div>
      )}

      {/* Suspend modal */}
      {suspendTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-bold">Suspend {suspendTarget.business_name}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">The seller&apos;s account stays active — they can still log in and buy. Only seller operations are suspended.</p>
            <textarea
              value={suspendReason}
              onChange={(e) => setSuspendReason(e.target.value)}
              placeholder="Optional reason for suspension..."
              className="mt-4 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] min-h-[80px]"
            />
            <div className="mt-4 flex gap-2 justify-end">
              <Button variant="outline" onClick={() => { setSuspendTarget(null); setSuspendReason(""); }}>Cancel</Button>
              <Button onClick={confirmSuspend}>Confirm suspension</Button>
            </div>
          </div>
        </div>
      )}

      {viewDoc && (
        <DocumentViewer
          document={viewDoc}
          onClose={() => setViewDoc(null)}
        />
      )}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading seller applications...</div>
      ) : sellers.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
          <UserRound className="mx-auto text-[#9aa9a1]" size={32} />
          <h2 className="mt-4 font-bold">No sellers found</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {filter === "all" ? "New applications will appear here." : `No sellers with status "${filter.replace("_", " ")}".`}
          </p>
        </div>
      ) : (
        <>
          {/* Pending highlight */}
          {filter === "all" && pending.length > 0 && (
            <div className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] px-5 py-4">
              <p className="text-sm font-bold text-[#b58a24]">{pending.length} application{pending.length > 1 ? "s" : ""} waiting for your review</p>
            </div>
          )}

          <div className="space-y-4">
            {sellers.map((seller) => {
              const colors = statusColors[seller.status] ?? statusColors.draft;
              const isExpanded = expandedId === seller.id;
              const sellerDocs = documents[seller.id];

              return (
                <article key={seller.id} className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                  <div className="flex items-start gap-4 p-5">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#e8f4ed] text-[#2d7a5e] font-extrabold text-sm">
                      {seller.business_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="font-bold text-[var(--ink)]">{seller.business_name}</h2>
                        <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold capitalize" style={{ backgroundColor: colors.bg, color: colors.text }}>
                          {seller.status.replace("_", " ")}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2">{seller.business_description || "No business description provided."}</p>
                      <p className="mt-2 text-[10px] text-[var(--muted)]">
                        Submitted {seller.submitted_at ? new Date(seller.submitted_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) : "not yet"}
                        {seller.reviewed_at && ` · Reviewed ${new Date(seller.reviewed_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}`}
                      </p>
                      {seller.rejection_reason && (
                        <p className="mt-2 rounded-lg bg-[#fbe6e0] px-3 py-2 text-xs text-[#b74d3b]">
                          Rejection reason: {seller.rejection_reason}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => toggleExpand(seller)}
                      className="shrink-0 rounded-lg border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[#f9fbf9] transition-colors"
                      aria-label="Toggle details"
                    >
                      <ChevronDown size={15} className={`transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                    </button>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 flex-wrap border-t border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                    {seller.status === "pending_review" && (
                      <>
                        <Button size="sm" onClick={() => approve(seller.id)}><Check size={14} /> Approve</Button>
                        <Button size="sm" variant="outline" onClick={() => setRejectTarget(seller)}><X size={14} /> Reject</Button>
                      </>
                    )}
                    {seller.status === "active" && (
                      <Button size="sm" variant="outline" onClick={() => setSuspendTarget(seller)}>Suspend</Button>
                    )}
                    {seller.status === "suspended" && (
                      <Button size="sm" onClick={() => reactivate(seller.id)}>Reactivate</Button>
                    )}
                    <button
                      onClick={() => toggleExpand(seller)}
                      className="ml-auto flex items-center gap-1.5 text-[11px] font-bold text-[var(--teal)] hover:underline"
                    >
                      <FileText size={13} /> {isExpanded ? "Hide" : "View"} documents
                    </button>
                  </div>

                  {/* Documents panel */}
                  {isExpanded && (
                    <div className="border-t border-[var(--line)] p-5">
                      <p className="mb-3 text-xs font-bold text-[var(--ink)]">Identity documents</p>
                      {!sellerDocs ? (
                        <p className="text-xs text-[var(--muted)]">Loading documents...</p>
                      ) : sellerDocs.length === 0 ? (
                        <p className="text-xs text-[var(--muted)]">No documents uploaded yet.</p>
                      ) : (
                        <div className="grid gap-2 sm:grid-cols-2">
                          {sellerDocs.map((doc) => (
                            <button
                              key={doc.id}
                              onClick={() => setViewDoc(doc)}
                              className="flex items-center gap-3 rounded-lg border border-[var(--line)] bg-[#f9fbf9] px-4 py-3 text-left text-xs hover:border-[var(--teal)] transition-colors"
                            >
                              <FileText size={15} className="shrink-0 text-[var(--teal)]" />
                              <div className="flex-1 min-w-0">
                                <p className="font-bold capitalize">{doc.document_type.replace(/_/g, " ")}</p>
                                <p className="text-[var(--muted)] truncate">{doc.original_filename ?? "Document"}</p>
                              </div>
                              <span className="shrink-0 rounded-md border border-[var(--line)] px-2 py-1 text-[10px] font-bold text-[var(--muted)] hover:border-[var(--teal)] hover:text-[var(--teal)]">
                                View
                              </span>
                            </button>
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
