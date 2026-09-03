"use client";

import { useEffect, useState } from "react";
import { ExternalLink, FileText, X } from "lucide-react";
import type { SellerDocument } from "@/app/services/seller.service";

interface DocumentViewerProps {
  document: SellerDocument;
  onClose: () => void;
}

const docLabels: Record<SellerDocument["document_type"], string> = {
  national_id_front: "National ID — Front",
  national_id_back: "National ID — Back",
  passport: "Passport",
  driving_license: "Driving License",
};

function isImage(mime: string | undefined): boolean {
  return (mime ?? "").toLowerCase().startsWith("image/");
}

export function DocumentViewer({ document, onClose }: DocumentViewerProps) {
  const [embedFailed, setEmbedFailed] = useState(false);
  const isImg = isImage(document.mime_type);

  // Close on the Escape key.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${docLabels[document.document_type]} preview`}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-4">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e8f4ed] text-[var(--teal)]">
            <FileText size={17} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-[var(--ink)]">
              {docLabels[document.document_type]}
            </p>
            <p className="truncate text-[11px] text-[var(--muted)]">
              {document.original_filename ?? "Identity document"} ·{" "}
              {Math.round(document.file_size / 1024)} KB
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--muted)] hover:bg-[#f2f5f2] hover:text-[var(--ink)] transition-colors"
            aria-label="Close preview"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="min-h-64 flex-1 overflow-auto bg-[#f4f6f4]">
          {embedFailed ? (
            <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 p-8 text-center">
              <FileText size={36} className="text-[#9aa9a1]" />
              <p className="text-sm font-bold text-[var(--ink)]">This document can&apos;t be embedded</p>
              <p className="max-w-sm text-xs text-[var(--muted)]">
                The file&apos;s host restricts inline previews. Open it in a new tab to view it directly.
              </p>
              <a
                href={document.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-flex items-center gap-2 rounded-lg bg-[var(--ink)] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#2e3d38] transition-colors"
              >
                <ExternalLink size={14} /> Open document
              </a>
            </div>
          ) : isImg ? (
            // Private signed URLs (off-domain, expiring) aren't suitable for next/image optimization.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={document.url}
              alt={docLabels[document.document_type]}
              className="mx-auto max-h-[70vh] w-auto object-contain"
              onError={() => setEmbedFailed(true)}
            />
          ) : (
            <iframe
              src={document.url}
              title={docLabels[document.document_type]}
              className="h-[70vh] w-full"
              onError={() => setEmbedFailed(true)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
