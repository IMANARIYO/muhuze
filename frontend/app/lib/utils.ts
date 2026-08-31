import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function rwf(amount: number): string {
  const value = Number.isFinite(amount) ? amount : 0;
  return `RWF ${value.toLocaleString("en-RW", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

export const CART_UPDATED_EVENT = "muhuze:cart-updated";

export function notifyCartUpdated(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(CART_UPDATED_EVENT));
}

export interface ImageRef {
  url: string;
  is_primary?: boolean;
  sort_order?: number;
}

export function pickPrimaryImage(images: ImageRef[] | null | undefined): string | null {
  if (!images || images.length === 0) return null;
  const sorted = [...images].sort(
    (a, b) =>
      Number(Boolean(b.is_primary)) - Number(Boolean(a.is_primary)) ||
      (a.sort_order ?? 0) - (b.sort_order ?? 0)
  );
  return sorted[0]?.url ?? null;
}
