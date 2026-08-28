import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function rwf(amount: number): string {
  const value = Number.isFinite(amount) ? amount : 0;
  return `RWF ${value.toLocaleString("en-RW", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}
