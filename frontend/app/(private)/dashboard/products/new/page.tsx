"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Send } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { adminService, type CategoryRecord } from "@/app/services/admin.service";
import { productService } from "@/app/services/product.service";

export default function NewProductPage() {
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [form, setForm] = useState({ name: "", description: "", category_id: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    adminService.listCategories().then(setCategories).catch((caught) => setError(caught instanceof Error ? caught.message : "Categories could not be loaded."));
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const product = await productService.create({ category_id: form.category_id, name: form.name, description: form.description });
      await productService.submit(product.id);
      setMessage("Product request submitted for admin review.");
      setForm({ name: "", description: "", category_id: "" });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Product request failed.");
    } finally {
      setSaving(false);
    }
  }

  return <div className="mx-auto max-w-2xl space-y-6"><div className="flex items-center gap-3"><Link href="/dashboard/products" className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--line)] bg-white text-[var(--muted)]"><ArrowLeft size={16} /></Link><div><p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Seller workspace</p><h1 className="mt-1 text-2xl font-black tracking-[-.04em]">Request a catalog product</h1></div></div><div className="rounded-xl border border-[var(--line)] bg-white p-6"><p className="text-sm leading-6 text-[var(--muted)]">A product is the shared catalog definition. Price and stock are added later as a seller listing after approval.</p><form onSubmit={handleSubmit} className="mt-7 space-y-5"><label className="block text-sm font-semibold">Product name<Input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="e.g. Organic Arabica Coffee" className="mt-2" /></label><label className="block text-sm font-semibold">Category<select required value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })} className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"><option value="">Select a catalog category</option>{categories.filter((category) => category.status === "active").map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label className="block text-sm font-semibold">Description<textarea required rows={5} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Tell the admin and future buyers what this product is." className="mt-2 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)]" /></label>{message && <p className="rounded-lg bg-[#e8f4ed] px-3 py-2 text-sm text-[#2d7a5e]">{message}</p>}{error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-3 py-2 text-sm text-[#b74d3b]">{error}</p>}<Button type="submit" disabled={saving}><Send size={15} /> {saving ? "Submitting..." : "Submit for review"}</Button></form></div></div>;
}
