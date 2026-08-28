"use client";

import { useEffect, useState } from "react";
import { Check, Layers, Plus, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Input } from "@/app/_components/ui/input";
import { adminService, type AttributeRecord, type BrandRecord, type CategoryRecord } from "@/app/services/admin.service";

type Tab = "categories" | "brands" | "attributes";

export default function CatalogSetupPage() {
  const [tab, setTab] = useState<Tab>("categories");
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [brands, setBrands] = useState<BrandRecord[]>([]);
  const [attributes, setAttributes] = useState<AttributeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Create forms
  const [catForm, setCatForm] = useState({ name: "", description: "", parent_id: "" });
  const [brandForm, setBrandForm] = useState({ name: "", description: "" });
  const [attrForm, setAttrForm] = useState({ name: "", input_type: "select" as AttributeRecord["input_type"], unit: "" });
  const [saving, setSaving] = useState(false);

  // Edit state
  const [editCat, setEditCat] = useState<CategoryRecord | null>(null);
  const [editBrand, setEditBrand] = useState<BrandRecord | null>(null);
  const [editAttr, setEditAttr] = useState<AttributeRecord | null>(null);

  async function loadAll() {
    setLoading(true);
    try {
      const [cats, brnds, attrs] = await Promise.all([
        adminService.listCategories(),
        adminService.listBrands(),
        adminService.listAttributes(),
      ]);
      setCategories(cats);
      setBrands(brnds);
      setAttributes(attrs);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Catalog data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      adminService.listCategories(),
      adminService.listBrands(),
      adminService.listAttributes(),
    ])
      .then(([cats, brnds, attrs]) => {
        if (!cancelled) { setCategories(cats); setBrands(brnds); setAttributes(attrs); setError(""); }
      })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Catalog data could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  function flash(msg: string) { setSuccess(msg); setTimeout(() => setSuccess(""), 3000); }

  async function createCategory(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await adminService.createCategory({ name: catForm.name, description: catForm.description || undefined, parent_id: catForm.parent_id || undefined });
      setCatForm({ name: "", description: "", parent_id: "" });
      flash("Category created.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Category could not be created."); } finally { setSaving(false); }
  }

  async function saveCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!editCat) return;
    setSaving(true);
    try {
      await adminService.updateCategory(editCat.id, { name: editCat.name, description: editCat.description || undefined, sort_order: editCat.sort_order, status: editCat.status });
      setEditCat(null);
      flash("Category updated.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Category could not be updated."); } finally { setSaving(false); }
  }

  async function createBrand(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await adminService.createBrand({ name: brandForm.name, description: brandForm.description || undefined });
      setBrandForm({ name: "", description: "" });
      flash("Brand created.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Brand could not be created."); } finally { setSaving(false); }
  }

  async function saveBrand(e: React.FormEvent) {
    e.preventDefault();
    if (!editBrand) return;
    setSaving(true);
    try {
      await adminService.updateBrand(editBrand.id, { name: editBrand.name, description: editBrand.description || undefined, status: editBrand.status });
      setEditBrand(null);
      flash("Brand updated.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Brand could not be updated."); } finally { setSaving(false); }
  }

  async function createAttribute(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await adminService.createAttribute({ name: attrForm.name, input_type: attrForm.input_type, unit: attrForm.unit || undefined });
      setAttrForm({ name: "", input_type: "select", unit: "" });
      flash("Attribute created.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Attribute could not be created."); } finally { setSaving(false); }
  }

  async function saveAttribute(e: React.FormEvent) {
    e.preventDefault();
    if (!editAttr) return;
    setSaving(true);
    try {
      await adminService.updateAttribute(editAttr.id, { name: editAttr.name, input_type: editAttr.input_type, unit: editAttr.unit || undefined, status: editAttr.status });
      setEditAttr(null);
      flash("Attribute updated.");
      await loadAll();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Attribute could not be updated."); } finally { setSaving(false); }
  }

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: "categories", label: "Categories", count: categories.length },
    { key: "brands", label: "Brands", count: brands.length },
    { key: "attributes", label: "Attributes", count: attributes.length },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Catalog setup</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Manage the controlled vocabulary — categories, brands, and attributes — that sellers pick from when listing products.</p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}
      {success && <p className="rounded-lg bg-[#e8f4ed] px-4 py-3 text-sm text-[#2d7a5e] flex items-center gap-2"><Check size={14} /> {success}</p>}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-[var(--line)] bg-[#f9fbf9] p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${tab === t.key ? "bg-white shadow-sm text-[var(--ink)]" : "text-[var(--muted)] hover:text-[var(--ink)]"}`}
          >
            {t.label}
            <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${tab === t.key ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[var(--line)] text-[var(--muted)]"}`}>{t.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading catalog data...</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.6fr]">

          {/* ── CATEGORIES ── */}
          {tab === "categories" && (
            <>
              <div className="rounded-xl border border-[var(--line)] bg-white p-6">
                <h2 className="font-bold">Add category</h2>
                <p className="mt-1 text-xs text-[var(--muted)]">Categories keep the catalog organized. Sellers pick from these when requesting products.</p>
                <form onSubmit={createCategory} className="mt-5 space-y-4">
                  <label className="block text-sm font-semibold">Name
                    <Input required value={catForm.name} onChange={(e) => setCatForm({ ...catForm, name: e.target.value })} placeholder="e.g. Smartphones" className="mt-2" />
                  </label>
                  <label className="block text-sm font-semibold">Parent category (optional)
                    <select value={catForm.parent_id} onChange={(e) => setCatForm({ ...catForm, parent_id: e.target.value })} className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                      <option value="">Top-level (no parent)</option>
                      {categories.filter((c) => c.status === "active").map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </label>
                  <label className="block text-sm font-semibold">Description (optional)
                    <Input value={catForm.description} onChange={(e) => setCatForm({ ...catForm, description: e.target.value })} placeholder="Brief description" className="mt-2" />
                  </label>
                  <Button type="submit" disabled={saving}><Plus size={14} /> Add category</Button>
                </form>
              </div>
              <div className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                <div className="border-b border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                  <p className="text-xs font-bold text-[var(--ink)]">All categories ({categories.length})</p>
                </div>
                <div className="divide-y divide-[#eff1ef]">
                  {categories.length === 0 ? (
                    <div className="p-8 text-center text-sm text-[var(--muted)]"><Layers className="mx-auto mb-2 text-[#9aa9a1]" size={24} />No categories yet</div>
                  ) : categories.map((cat) => (
                    <div key={cat.id} className="px-5 py-4">
                      {editCat?.id === cat.id ? (
                        <form onSubmit={saveCategory} className="space-y-3">
                          <Input required value={editCat.name} onChange={(e) => setEditCat({ ...editCat, name: e.target.value })} />
                          <Input value={editCat.description ?? ""} onChange={(e) => setEditCat({ ...editCat, description: e.target.value })} placeholder="Description" />
                          <select value={editCat.status} onChange={(e) => setEditCat({ ...editCat, status: e.target.value as CategoryRecord["status"] })} className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                          <div className="flex gap-2">
                            <Button type="submit" size="sm" disabled={saving}><Check size={13} /> Save</Button>
                            <Button type="button" size="sm" variant="outline" onClick={() => setEditCat(null)}><X size={13} /></Button>
                          </div>
                        </form>
                      ) : (
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold text-[var(--ink)]">{cat.name}</p>
                            {cat.parent_id && <p className="text-[10px] text-[var(--muted)]">Child of {categories.find((c) => c.id === cat.parent_id)?.name ?? cat.parent_id.slice(0, 8)}</p>}
                            {cat.description && <p className="text-xs text-[var(--muted)]">{cat.description}</p>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${cat.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>{cat.status}</span>
                            <button onClick={() => setEditCat(cat)} className="text-[11px] font-bold text-[var(--teal)] hover:underline">Edit</button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── BRANDS ── */}
          {tab === "brands" && (
            <>
              <div className="rounded-xl border border-[var(--line)] bg-white p-6">
                <h2 className="font-bold">Add brand</h2>
                <p className="mt-1 text-xs text-[var(--muted)]">Brands are assigned to products. Keeping them controlled prevents duplicates like &quot;Samsung&quot; vs &quot;SAMSUNG&quot;.</p>
                <form onSubmit={createBrand} className="mt-5 space-y-4">
                  <label className="block text-sm font-semibold">Brand name
                    <Input required value={brandForm.name} onChange={(e) => setBrandForm({ ...brandForm, name: e.target.value })} placeholder="e.g. Samsung" className="mt-2" />
                  </label>
                  <label className="block text-sm font-semibold">Description (optional)
                    <Input value={brandForm.description} onChange={(e) => setBrandForm({ ...brandForm, description: e.target.value })} placeholder="Brief description" className="mt-2" />
                  </label>
                  <Button type="submit" disabled={saving}><Plus size={14} /> Add brand</Button>
                </form>
              </div>
              <div className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                <div className="border-b border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                  <p className="text-xs font-bold text-[var(--ink)]">All brands ({brands.length})</p>
                </div>
                <div className="divide-y divide-[#eff1ef]">
                  {brands.length === 0 ? (
                    <div className="p-8 text-center text-sm text-[var(--muted)]">No brands yet</div>
                  ) : brands.map((brand) => (
                    <div key={brand.id} className="px-5 py-4">
                      {editBrand?.id === brand.id ? (
                        <form onSubmit={saveBrand} className="space-y-3">
                          <Input required value={editBrand.name} onChange={(e) => setEditBrand({ ...editBrand, name: e.target.value })} />
                          <Input value={editBrand.description ?? ""} onChange={(e) => setEditBrand({ ...editBrand, description: e.target.value })} placeholder="Description" />
                          <select value={editBrand.status} onChange={(e) => setEditBrand({ ...editBrand, status: e.target.value as BrandRecord["status"] })} className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                          <div className="flex gap-2">
                            <Button type="submit" size="sm" disabled={saving}><Check size={13} /> Save</Button>
                            <Button type="button" size="sm" variant="outline" onClick={() => setEditBrand(null)}><X size={13} /></Button>
                          </div>
                        </form>
                      ) : (
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold text-[var(--ink)]">{brand.name}</p>
                            {brand.description && <p className="text-xs text-[var(--muted)]">{brand.description}</p>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${brand.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>{brand.status}</span>
                            <button onClick={() => setEditBrand(brand)} className="text-[11px] font-bold text-[var(--teal)] hover:underline">Edit</button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── ATTRIBUTES ── */}
          {tab === "attributes" && (
            <>
              <div className="rounded-xl border border-[var(--line)] bg-white p-6">
                <h2 className="font-bold">Add attribute</h2>
                <p className="mt-1 text-xs text-[var(--muted)]">Attributes define what can vary between product variants — Color, RAM, Size, etc. Sellers pick from these; they can&apos;t invent free-text fields.</p>
                <form onSubmit={createAttribute} className="mt-5 space-y-4">
                  <label className="block text-sm font-semibold">Attribute name
                    <Input required value={attrForm.name} onChange={(e) => setAttrForm({ ...attrForm, name: e.target.value })} placeholder="e.g. Color" className="mt-2" />
                  </label>
                  <label className="block text-sm font-semibold">Input type
                    <select value={attrForm.input_type} onChange={(e) => setAttrForm({ ...attrForm, input_type: e.target.value as AttributeRecord["input_type"] })} className="mt-2 flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                      <option value="select">Select (dropdown)</option>
                      <option value="text">Text (free-form)</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean (yes/no)</option>
                    </select>
                  </label>
                  <label className="block text-sm font-semibold">Unit (optional)
                    <Input value={attrForm.unit} onChange={(e) => setAttrForm({ ...attrForm, unit: e.target.value })} placeholder="e.g. GB, kg, inches" className="mt-2" />
                  </label>
                  <Button type="submit" disabled={saving}><Plus size={14} /> Add attribute</Button>
                </form>
              </div>
              <div className="rounded-xl border border-[var(--line)] bg-white overflow-hidden">
                <div className="border-b border-[var(--line)] bg-[#f9fbf9] px-5 py-3">
                  <p className="text-xs font-bold text-[var(--ink)]">All attributes ({attributes.length})</p>
                </div>
                <div className="divide-y divide-[#eff1ef]">
                  {attributes.length === 0 ? (
                    <div className="p-8 text-center text-sm text-[var(--muted)]">No attributes yet</div>
                  ) : attributes.map((attr) => (
                    <div key={attr.id} className="px-5 py-4">
                      {editAttr?.id === attr.id ? (
                        <form onSubmit={saveAttribute} className="space-y-3">
                          <Input required value={editAttr.name} onChange={(e) => setEditAttr({ ...editAttr, name: e.target.value })} />
                          <select value={editAttr.input_type} onChange={(e) => setEditAttr({ ...editAttr, input_type: e.target.value as AttributeRecord["input_type"] })} className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                            <option value="select">Select</option>
                            <option value="text">Text</option>
                            <option value="number">Number</option>
                            <option value="boolean">Boolean</option>
                          </select>
                          <Input value={editAttr.unit ?? ""} onChange={(e) => setEditAttr({ ...editAttr, unit: e.target.value })} placeholder="Unit (optional)" />
                          <select value={editAttr.status} onChange={(e) => setEditAttr({ ...editAttr, status: e.target.value as AttributeRecord["status"] })} className="flex h-9 w-full rounded-lg border border-[var(--line)] bg-white px-3 text-sm outline-none focus:border-[var(--teal)]">
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                          <div className="flex gap-2">
                            <Button type="submit" size="sm" disabled={saving}><Check size={13} /> Save</Button>
                            <Button type="button" size="sm" variant="outline" onClick={() => setEditAttr(null)}><X size={13} /></Button>
                          </div>
                        </form>
                      ) : (
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold text-[var(--ink)]">{attr.name}</p>
                            <p className="text-[10px] text-[var(--muted)] capitalize">{attr.input_type}{attr.unit ? ` · ${attr.unit}` : ""}</p>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${attr.status === "active" ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#f2f5f2] text-[#7e8b84]"}`}>{attr.status}</span>
                            <button onClick={() => setEditAttr(attr)} className="text-[11px] font-bold text-[var(--teal)] hover:underline">Edit</button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
