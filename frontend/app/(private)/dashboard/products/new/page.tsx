"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { adminService, type CategoryRecord, type BrandRecord } from "@/app/services/admin.service";
import { productService } from "@/app/services/product.service";
import { useAuth } from "@/app/context/auth-context";

export default function NewProductPage() {
  const { hasRole } = useAuth();
  const router = useRouter();
  const isAdmin = hasRole("admin");

  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [brands, setBrands] = useState<BrandRecord[]>([]);
  const [form, setForm] = useState({ name: "", description: "", category_id: "", brand_id: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([adminService.listCategories(), adminService.listBrands()])
      .then(([cats, brs]) => { setCategories(cats); setBrands(brs); })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load catalog data."));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.category_id) { setError("Please select a category."); return; }
    setSaving(true); setError("");
    try {
      const product = await productService.create({
        category_id: form.category_id,
        brand_id: form.brand_id || undefined,
        name: form.name,
        description: form.description || undefined,
      });
      // Admin: approve immediately after create so it's active in catalog
      if (isAdmin) {
        await productService.submit(product.id);
        await productService.approve(product.id);
      } else {
        await productService.submit(product.id);
      }
      router.push("/dashboard/products");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Product could not be created.");
    } finally {
      setSaving(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-[var(--line)] bg-white p-10 text-center">
        <p className="text-sm text-[var(--muted)]">Only admins can create catalog products.</p>
        <Link href="/dashboard/products" className="mt-4 inline-block text-sm font-bold text-[var(--teal)] hover:underline">← Back to products</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/products" className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--line)] bg-white text-[var(--muted)] hover:bg-[#f9fbf9]">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
          <h1 className="mt-1 text-2xl font-black tracking-[-.04em]">Create catalog product</h1>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <p className="text-sm leading-6 text-[var(--muted)]">
          Admin-created products go directly to <strong>active</strong> status in the catalog. Sellers can then add variants and create listings on top of them.
        </p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <label className="block text-sm font-semibold">
            Product name <span className="text-[#b74d3b]">*</span>
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Samsung Galaxy S24 Ultra" className="mt-2" />
          </label>

          <label className="block text-sm font-semibold">
            Category <span className="text-[#b74d3b]">*</span>
            <select
              required
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
            >
              <option value="">Select a category</option>
              {categories.filter((c) => c.status === "active").map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-semibold">
            Brand <span className="text-[10px] font-normal text-[var(--muted)]">(optional)</span>
            <select
              value={form.brand_id}
              onChange={(e) => setForm({ ...form, brand_id: e.target.value })}
              className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]"
            >
              <option value="">No brand / unbranded</option>
              {brands.filter((b) => b.status === "active").map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-semibold">
            Description <span className="text-[10px] font-normal text-[var(--muted)]">(optional)</span>
            <textarea
              rows={4}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the product for buyers and sellers."
              className="mt-2 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] resize-none"
            />
          </label>

          {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-3 py-2 text-sm text-[#b74d3b]">{error}</p>}

          <div className="flex gap-3">
            <Button type="submit" disabled={saving}>{saving ? "Creating..." : "Create & activate product"}</Button>
            <Link href="/dashboard/products"><Button type="button" variant="outline">Cancel</Button></Link>
          </div>
        </form>
      </div>
    </div>
  );
}
