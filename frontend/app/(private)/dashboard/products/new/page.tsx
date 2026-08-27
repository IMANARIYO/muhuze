"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import type { ProductCategory } from "@/app/lib/types";

const categories: ProductCategory[] = [
  "Electronics",
  "Clothing",
  "Food & Beverage",
  "Home & Garden",
  "Health & Beauty",
  "Sports",
  "Books",
  "Other",
];

export default function NewProductPage() {
  const router = useRouter();
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    price: "",
    category: "" as ProductCategory | "",
    unit: "",
    stock: "",
    description: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => router.push("/dashboard/products"), 1800);
  };

  if (submitted) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[#e8f4ed] text-[var(--teal)]">
          <CheckCircle size={32} />
        </div>
        <h2 className="text-xl font-extrabold text-[var(--ink)]">Product Listed!</h2>
        <p className="text-sm text-[var(--muted)]">Your product is now visible to clients. Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/products">
          <button className="grid h-8 w-8 place-items-center rounded-lg border border-[var(--line)] bg-white text-[var(--muted)] hover:text-[var(--ink)]">
            <ArrowLeft size={15} />
          </button>
        </Link>
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Add New Product</h1>
          <p className="text-sm text-[var(--muted)]">Fill in the details to list your product.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Product Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Product Name *</label>
              <Input
                required
                placeholder="e.g. Organic Arabica Coffee"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[var(--ink)]">Price (USD) *</label>
                <Input
                  required
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[var(--ink)]">Unit (optional)</label>
                <Input
                  placeholder="e.g. kg, piece, 100ml"
                  value={form.unit}
                  onChange={(e) => setForm({ ...form, unit: e.target.value })}
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[var(--ink)]">Category *</label>
                <select
                  required
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value as ProductCategory })}
                  className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm text-[var(--ink)] outline-none focus:border-[var(--teal)] focus:ring-1 focus:ring-[var(--teal)]"
                >
                  <option value="">Select category</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-[var(--ink)]">Stock Quantity *</label>
                <Input
                  required
                  type="number"
                  min="0"
                  placeholder="0"
                  value={form.stock}
                  onChange={(e) => setForm({ ...form, stock: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--ink)]">Description</label>
              <textarea
                rows={3}
                placeholder="Describe your product…"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="flex w-full rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)] placeholder:text-[var(--muted)] outline-none focus:border-[var(--teal)] focus:ring-1 focus:ring-[var(--teal)]"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit">List Product</Button>
              <Link href="/dashboard/products">
                <Button variant="outline" type="button">Cancel</Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
