"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, ChevronRight, Clock, FileText, Send, ShieldCheck, Store, Upload, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { sellerService, type SellerDocument, type SellerProfile } from "@/app/services/seller.service";

const documentTypes: SellerDocument["document_type"][] = [
  "national_id_front",
  "national_id_back",
  "passport",
  "driving_license",
];

const docLabels: Record<SellerDocument["document_type"], string> = {
  national_id_front: "National ID — Front",
  national_id_back: "National ID — Back",
  passport: "Passport",
  driving_license: "Driving License",
};

function hasRequiredDocs(docs: SellerDocument[]): boolean {
  const types = new Set(docs.map((d) => d.document_type));
  return (types.has("national_id_front") && types.has("national_id_back")) || types.has("passport") || types.has("driving_license");
}

const statusMeta: Record<SellerProfile["status"], { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  draft: { label: "Draft", color: "#7e8b84", bg: "#f2f5f2", icon: <Store size={14} /> },
  pending_review: { label: "Under review", color: "#b58a24", bg: "#fbf0ce", icon: <Clock size={14} /> },
  active: { label: "Active seller", color: "#2d7a5e", bg: "#e8f4ed", icon: <ShieldCheck size={14} /> },
  rejected: { label: "Rejected", color: "#b74d3b", bg: "#fbe6e0", icon: <X size={14} /> },
  suspended: { label: "Suspended", color: "#b74d3b", bg: "#fbe6e0", icon: <X size={14} /> },
  deactivated: { label: "Deactivated", color: "#7e8b84", bg: "#f2f5f2", icon: <X size={14} /> },
};

export default function SellerPage() {
  const [seller, setSeller] = useState<SellerProfile | null>(null);
  const [documents, setDocuments] = useState<SellerDocument[]>([]);
  const [form, setForm] = useState({ business_name: "", business_description: "" });
  const [documentType, setDocumentType] = useState<SellerDocument["document_type"]>("passport");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      try {
        const profile = await sellerService.getMine();
        const docs = await sellerService.listDocuments();
        if (!cancelled) {
          setSeller(profile);
          setForm({ business_name: profile.business_name, business_description: profile.business_description ?? "" });
          setDocuments(docs);
        }
      } catch {
        // No seller profile yet — that's fine, show the registration form
      }
    }
    void restore();
    return () => { cancelled = true; };
  }, []);

  const isEditable = !seller || ["draft", "rejected"].includes(seller.status);
  const canSubmit = seller && isEditable && hasRequiredDocs(documents);
  const meta = seller ? statusMeta[seller.status] : null;

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const next = seller ? await sellerService.updateMine(form) : await sellerService.register(form);
      setSeller(next);
      setMessage("Business profile saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Profile could not be saved.");
    } finally { setSaving(false); }
  }

  async function uploadDocument() {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await sellerService.uploadDocument(documentType, file);
      setFile(null);
      setDocuments(await sellerService.listDocuments());
      setMessage("Document uploaded securely.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Document upload failed.");
    } finally { setUploading(false); }
  }

  async function deleteDocument(id: string) {
    try {
      await sellerService.deleteDocument(id);
      setDocuments(await sellerService.listDocuments());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Document could not be deleted.");
    }
  }

  async function submit() {
    setSaving(true);
    setError("");
    try {
      setSeller(await sellerService.submit());
      setMessage("Application submitted! We'll review it shortly.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Application could not be submitted.");
    } finally { setSaving(false); }
  }

  // Step indicators
  const steps = [
    { label: "Business profile", done: Boolean(seller), active: !seller || isEditable },
    { label: "Identity documents", done: hasRequiredDocs(documents), active: Boolean(seller && isEditable) },
    { label: "Submit for review", done: seller?.status === "active", active: Boolean(canSubmit) },
    { label: "Admin approval", done: seller?.status === "active", active: seller?.status === "pending_review" },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Header */}
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Seller workspace</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Set up your shop</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Complete these steps to become an active seller on MUHUZE. Once approved, you can list products and start selling.
        </p>
      </div>

      {/* Status badge */}
      {meta && (
        <div className="flex items-center gap-3 rounded-xl border px-5 py-4" style={{ borderColor: meta.color + "44", backgroundColor: meta.bg }}>
          <span style={{ color: meta.color }}>{meta.icon}</span>
          <div>
            <p className="text-sm font-bold" style={{ color: meta.color }}>{meta.label}</p>
            {seller?.status === "pending_review" && <p className="text-xs text-[var(--muted)]">Your application is being reviewed. We&apos;ll notify you once a decision is made.</p>}
            {seller?.status === "active" && <p className="text-xs text-[var(--muted)]">You&apos;re an active seller. Go to My Products to start listing.</p>}
            {seller?.rejection_reason && <p className="mt-1 text-xs" style={{ color: meta.color }}>Reason: {seller.rejection_reason}</p>}
          </div>
        </div>
      )}

      {/* Progress steps */}
      <div className="flex items-center gap-0">
        {steps.map((step, i) => (
          <div key={step.label} className="flex items-center flex-1 min-w-0">
            <div className="flex flex-col items-center gap-1.5 flex-1">
              <div className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold transition-colors ${step.done ? "bg-[var(--teal)] text-white" : step.active ? "bg-[var(--ink)] text-white" : "bg-[#e5e9e5] text-[var(--muted)]"}`}>
                {step.done ? <CheckCircle2 size={14} /> : i + 1}
              </div>
              <p className={`text-center text-[10px] font-bold leading-tight ${step.done ? "text-[var(--teal)]" : step.active ? "text-[var(--ink)]" : "text-[var(--muted)]"}`}>{step.label}</p>
            </div>
            {i < steps.length - 1 && <div className={`h-px flex-1 mx-1 mb-5 ${step.done ? "bg-[var(--teal)]" : "bg-[#e5e9e5]"}`} />}
          </div>
        ))}
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {message && <p className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2"><CheckCircle2 size={14} /> {message}</p>}

      {/* Step 1: Business profile */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]"><Store size={16} /></div>
          <div>
            <h2 className="font-bold">Business profile</h2>
            <p className="text-xs text-[var(--muted)]">Tell us about your business</p>
          </div>
          {seller && <span className="ml-auto rounded-full px-2.5 py-1 text-[10px] font-bold capitalize" style={{ backgroundColor: meta?.bg, color: meta?.color }}>{meta?.label}</span>}
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          <label className="block text-sm font-semibold">Business name
            <Input
              required
              disabled={!isEditable}
              value={form.business_name}
              onChange={(e) => setForm({ ...form, business_name: e.target.value })}
              placeholder="e.g. Kigali Crafts Co."
              className="mt-2"
            />
          </label>
          <label className="block text-sm font-semibold">Business description
            <textarea
              required
              disabled={!isEditable}
              value={form.business_description}
              onChange={(e) => setForm({ ...form, business_description: e.target.value })}
              placeholder="What do you sell? Who are your customers? What makes your business unique?"
              className="mt-2 min-h-28 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] disabled:bg-[#f9fbf9] disabled:text-[var(--muted)]"
            />
          </label>
          {isEditable && (
            <Button type="submit" disabled={saving}>{saving ? "Saving..." : seller ? "Update profile" : "Save & continue"}</Button>
          )}
        </form>
      </div>

      {/* Step 2: Documents */}
      {seller && (
        <div className="rounded-xl border border-[var(--line)] bg-white p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]"><FileText size={16} /></div>
            <div>
              <h2 className="font-bold">Identity documents</h2>
              <p className="text-xs text-[var(--muted)]">Upload one of: passport, driving license, or both sides of a national ID</p>
            </div>
            {hasRequiredDocs(documents) && <CheckCircle2 size={18} className="ml-auto text-[var(--teal)]" />}
          </div>

          {/* Uploaded docs */}
          {documents.length > 0 && (
            <div className="mb-5 grid gap-2">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center gap-3 rounded-lg bg-[#f9fbf9] border border-[var(--line)] px-4 py-3">
                  <CheckCircle2 size={15} className="shrink-0 text-[var(--teal)]" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold">{docLabels[doc.document_type]}</p>
                    <p className="text-[10px] text-[var(--muted)] truncate">{doc.original_filename ?? "Uploaded"}</p>
                  </div>
                  {isEditable && (
                    <button onClick={() => deleteDocument(doc.id)} className="shrink-0 text-[var(--muted)] hover:text-[#b74d3b] transition-colors" aria-label="Delete document">
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {isEditable && (
            <div className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-[1fr_1.4fr_auto]">
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value as SellerDocument["document_type"])}
                  className="h-10 rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
                >
                  {documentTypes.map((type) => (
                    <option key={type} value={type}>{docLabels[type]}</option>
                  ))}
                </select>
                <label className="flex h-10 cursor-pointer items-center gap-2 rounded-lg border border-dashed border-[var(--line)] bg-[#f9fbf9] px-3 text-xs text-[var(--muted)] hover:border-[var(--teal)] transition-colors">
                  <Upload size={13} />
                  {file ? file.name : "Choose file (JPG, PNG, PDF · max 10 MB)"}
                  <input type="file" accept="image/jpeg,image/png,application/pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="sr-only" />
                </label>
                <Button type="button" disabled={!file || uploading} onClick={uploadDocument}>
                  {uploading ? "Uploading..." : "Upload"}
                </Button>
              </div>
              <p className="text-[10px] text-[var(--muted)]">Files are stored privately and only accessible via signed URLs. They are never publicly accessible.</p>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Submit */}
      {seller && isEditable && (
        <div className={`rounded-xl border p-6 ${canSubmit ? "border-[var(--teal)] bg-[#f0faf6]" : "border-[var(--line)] bg-white"}`}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`grid h-8 w-8 place-items-center rounded-lg ${canSubmit ? "bg-[var(--teal)] text-white" : "bg-[#e5e9e5] text-[var(--muted)]"}`}>
              <Send size={16} />
            </div>
            <div>
              <h2 className="font-bold">Submit for review</h2>
              <p className="text-xs text-[var(--muted)]">Once submitted, your application goes to the admin team for review</p>
            </div>
          </div>
          {!canSubmit && (
            <div className="mb-4 rounded-lg bg-[#fbf0ce] px-4 py-3 text-xs text-[#b58a24]">
              Complete your business profile and upload at least one required identity document before submitting.
            </div>
          )}
          <div className="flex items-center gap-3">
            <Button disabled={!canSubmit || saving} onClick={submit}>
              <Send size={14} /> {saving ? "Submitting..." : "Submit application"}
            </Button>
            {canSubmit && <p className="text-xs text-[var(--muted)]">You won&apos;t be able to edit your profile while it&apos;s under review.</p>}
          </div>
        </div>
      )}

      {/* Pending state */}
      {seller?.status === "pending_review" && (
        <div className="rounded-xl border border-[#f0d98a] bg-[#fffdf0] p-6 text-center">
          <Clock size={28} className="mx-auto text-[#b58a24]" />
          <h2 className="mt-3 font-bold">Application under review</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">Our team is reviewing your application. This usually takes 1–2 business days. You&apos;ll be notified once a decision is made.</p>
        </div>
      )}

      {/* Active state */}
      {seller?.status === "active" && (
        <div className="rounded-xl border border-[#bdded1] bg-[#e8f4ed] p-6 text-center">
          <ShieldCheck size={28} className="mx-auto text-[var(--teal)]" />
          <h2 className="mt-3 font-bold text-[var(--ink)]">You&apos;re an active seller!</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">Your seller account is approved and operational. Head to My Products to request catalog entries and start creating listings.</p>
          <a href="/dashboard/products" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[var(--teal)] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#28918a] transition-colors">
            Go to My Products <ChevronRight size={15} />
          </a>
        </div>
      )}
    </div>
  );
}
