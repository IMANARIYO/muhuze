"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ImagePlus, Star, Trash2 } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { adminService, type CategoryRecord, type BrandRecord } from "@/app/services/admin.service";
import { productService, type ProductRecord } from "@/app/services/product.service";
import { useAuth } from "@/app/context/auth-context";

interface ProductImage { id: string; product_id: string; url: string; is_primary: boolean; sort_order: number; created_at: string; }

export default function EditProductPage() {
  const { id } = useParams<{ id: string }>();
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const fileRef = useRef<HTMLInputElement>(null);

  const [product, setProduct] = useState<ProductRecord | null>(null);
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [brands, setBrands] = useState<BrandRecord[]>([]);
  const [images, setImages] = useState<ProductImage[]>([]);
  const [form, setForm] = useState({ name: "", description: "", category_id: "", brand_id: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  async function loadImages() {
    try { setImages(await productService.listProductImages(id)); } catch { /* ignore */ }
  }

  useEffect(() => {
    if (!isAdmin) return;
    Promise.all([
      productService.list({ status: undefined }),
      adminService.listCategories(),
      adminService.listBrands(),
      productService.listProductImages(id),
    ]).then(([products, cats, brs, imgs]) => {
      const p = products.find((x) => x.id === id);
      if (p) {
        setProduct(p);
        setForm({ name: p.name, description: p.description ?? "", category_id: p.category_id, brand_id: p.brand_id ?? "" });
      }
      setCategories(cats);
      setBrands(brs);
      setImages(imgs);
    }).catch((e) => setError(e instanceof Error ? e.message : "Could not load product."));
  }, [id, isAdmin]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!product) return;
    setSaving(true); setError(""); setSuccess("");
    try {
      await productService.update(id, {
        category_id: form.category_id,
        brand_id: form.brand_id || undefined,
        name: form.name,
        description: form.description || undefined,
      });
      setSuccess("Product updated successfully.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Update failed.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setError("");
    try {
      await productService.uploadProductImage(id, file, images.length === 0);
      await loadImages();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleDeleteImage(imageId: string) {
    try { await productService.deleteProductImage(id, imageId); await loadImages(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Delete failed."); }
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-[var(--line)] bg-white p-10 text-center">
        <p className="text-sm text-[var(--muted)]">Admin access required.</p>
      </div>
    );
  }

  const canEdit = product && (product.status === "draft" || product.status === "rejected");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/products" className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--line)] bg-white text-[var(--muted)] hover:bg-[#f9fbf9]">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
          <h1 className="mt-1 text-2xl font-black tracking-[-.04em]">{product?.name ?? "Edit product"}</h1>
        </div>
        {product && (
          <span className="ml-auto rounded-full px-3 py-1 text-[11px] font-bold capitalize" style={{ backgroundColor: product.status === "active" ? "#e8f4ed" : product.status === "rejected" ? "#fbe6e0" : "#f2f5f2", color: product.status === "active" ? "#2d7a5e" : product.status === "rejected" ? "#b74d3b" : "#7e8b84" }}>
            {product.status.replace("_", " ")}
          </span>
        )}
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {success && <p className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e]">{success}</p>}

      {/* Details form */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <h2 className="text-sm font-bold text-[var(--ink)]">Product details</h2>
        {!canEdit && product && (
          <p className="mt-2 rounded-lg bg-[#fbf0ce] px-3 py-2 text-xs text-[#b58a24]">
            This product is <strong>{product.status}</strong> — details can only be edited when status is draft or rejected.
          </p>
        )}
        <form onSubmit={handleSave} className="mt-5 space-y-4">
          <label className="block text-sm font-semibold">
            Product name
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-2" disabled={!canEdit} />
          </label>
          <label className="block text-sm font-semibold">
            Category
            <select
              required
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              disabled={!canEdit}
              className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)] disabled:opacity-60"
            >
              <option value="">Select a category</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
          <label className="block text-sm font-semibold">
            Brand
            <select
              value={form.brand_id}
              onChange={(e) => setForm({ ...form, brand_id: e.target.value })}
              disabled={!canEdit}
              className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)] disabled:opacity-60"
            >
              <option value="">No brand</option>
              {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </label>
          <label className="block text-sm font-semibold">
            Description
            <textarea
              rows={4}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              disabled={!canEdit}
              className="mt-2 w-full rounded-lg border border-[var(--line)] px-3 py-2 text-sm outline-none focus:border-[var(--teal)] resize-none disabled:opacity-60"
            />
          </label>
          {canEdit && (
            <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save changes"}</Button>
          )}
        </form>
      </div>

      {/* Images */}
      <div className="rounded-xl border border-[var(--line)] bg-white p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-[var(--ink)]">Catalog images</h2>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs font-bold text-[var(--ink)] hover:bg-[#f9fbf9] disabled:opacity-60 transition-colors"
          >
            <ImagePlus size={13} /> {uploading ? "Uploading..." : "Upload image"}
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleUpload} />
        </div>
        {images.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--muted)]">No images yet. Upload the first one — it will be set as primary automatically.</p>
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {images.map((img) => (
              <div key={img.id} className="group relative rounded-lg overflow-hidden border border-[var(--line)] bg-[#f9fbf9] aspect-square">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img.url} alt="product" className="h-full w-full object-cover" />
                {img.is_primary && (
                  <span className="absolute top-1.5 left-1.5 flex items-center gap-1 rounded-full bg-[var(--ink)] px-2 py-0.5 text-[10px] font-bold text-white">
                    <Star size={9} fill="white" /> Primary
                  </span>
                )}
                <button
                  onClick={() => handleDeleteImage(img.id)}
                  className="absolute top-1.5 right-1.5 hidden group-hover:flex h-6 w-6 items-center justify-center rounded-full bg-[#b74d3b] text-white"
                >
                  <Trash2 size={11} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
