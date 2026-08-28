"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search, ShoppingCart, SlidersHorizontal } from "lucide-react";
import { Footer } from "@/app/_components/public/footer";
import { Header } from "@/app/_components/public/header";
import { cartService } from "@/app/services/cart.service";
import {
  catalogService,
  type CatalogFiltersPayload,
  type CatalogListingItem,
} from "@/app/services/catalog.service";
import { adminService, type CategoryRecord } from "@/app/services/admin.service";
import { useAuth } from "@/app/context/auth-context";
import { rwf } from "@/app/lib/utils";

export default function ProductsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();

  const [items, setItems] = useState<CatalogListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [filtersData, setFiltersData] = useState<CatalogFiltersPayload | null>(null);

  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState<string | undefined>(undefined);
  const [brandId, setBrandId] = useState<string | undefined>(undefined);
  const [attrSelections, setAttrSelections] = useState<Record<string, string>>({});
  const [conditions, setConditions] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [inStock, setInStock] = useState(false);
  const [sort, setSort] = useState<"price_asc" | "price_desc" | "newest">("price_asc");
  const [addedId, setAddedId] = useState<string | null>(null);

  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    adminService
      .listCategories()
      .then((list) => { if (!cancelled) setCategories(list); })
      .catch(() => undefined);
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    catalogService
      .getFilters(categoryId)
      .then((payload) => { if (!cancelled) setFiltersData(payload); })
      .catch(() => { if (!cancelled) setFiltersData(null); });
    return () => { cancelled = true; };
  }, [categoryId]);

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => { setQuery(search.trim()); }, 350);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const attributeIds = Object.keys(attrSelections).filter((id) => attrSelections[id]);
        const attributeValues = attributeIds.map((id) => attrSelections[id]);
        const data = await catalogService.list({
          category_id: categoryId,
          brand_id: brandId,
          search: query || undefined,
          min_price: minPrice ? Number(minPrice) : undefined,
          max_price: maxPrice ? Number(maxPrice) : undefined,
          condition: conditions.length ? conditions : undefined,
          in_stock: inStock || undefined,
          attribute_id: attributeIds.length ? attributeIds : undefined,
          value: attributeValues.length ? attributeValues : undefined,
          sort,
        });
        if (!cancelled) setItems(data);
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Catalog could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [query, categoryId, brandId, attrSelections, conditions, minPrice, maxPrice, inStock, sort]);

  async function addToCart(listingId: string) {
    if (!user) { router.push("/login"); return; }
    try {
      await cartService.addItem(listingId);
      setAddedId(listingId);
      setTimeout(() => setAddedId(null), 1600);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Item could not be added to your cart.");
    }
  }

  const attributeGroups = useMemo(() => filtersData?.attributes ?? [], [filtersData]);
  const conditionOptions = useMemo(
    () => filtersData?.conditions.length ? filtersData.conditions : ["new", "like_new", "used"],
    [filtersData]
  );

  const filterInput = (label: string, value: string, checked: boolean, onChange: (next: boolean) => void) => (
    <label className="flex cursor-pointer items-center gap-2 text-[13px] text-[var(--muted)]">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-[var(--teal)]"
      />
      <span>{label}</span>
    </label>
  );

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      <Header />
      <main>
        <section className="border-b border-[var(--line)] bg-[#f0f5ed]">
          <div className="mx-auto max-w-6xl px-6 pb-12 pt-14 sm:pb-16 sm:pt-20">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">The Muhuze shop</p>
              <h1 className="mt-4 text-4xl font-black tracking-[-.05em] sm:text-6xl">
                Find something <span className="text-[var(--coral)]">worth keeping.</span>
              </h1>
              <p className="mt-5 max-w-xl text-base leading-7 text-[var(--muted)]">
                A considered collection of products from independent sellers across the network.
              </p>
            </div>
            <div className="mt-9 flex max-w-2xl items-center gap-3 rounded-xl border border-[#c8d7cc] bg-white p-2 shadow-sm">
              <Search className="ml-2 text-[#899990]" size={19} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products, sellers, or attributes"
                className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm outline-none placeholder:text-[#899990]"
              />
              <button onClick={() => setQuery(search.trim())} className="hidden rounded-lg bg-[var(--ink)] px-5 py-2.5 text-sm font-bold text-white sm:block">
                Search
              </button>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-10 sm:py-14">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
            {/* Sidebar filters */}
            <aside className="w-full shrink-0 space-y-7 lg:w-56">
              <div>
                <h2 className="text-sm font-bold">Browse categories</h2>
                <div className="mt-3 flex gap-2 overflow-x-auto pb-1 lg:grid lg:gap-1 lg:overflow-visible">
                  <button
                    onClick={() => setCategoryId(undefined)}
                    className={`whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                      !categoryId ? "bg-[var(--ink)] font-bold text-white" : "text-[var(--muted)] hover:bg-white hover:text-[var(--ink)]"
                    }`}
                  >
                    All products
                  </button>
                  {categories.filter((c) => !c.parent_id).map((c) => (
                    <button
                      key={c.id}
                      onClick={() => setCategoryId(categoryId === c.id ? undefined : c.id)}
                      className={`whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                        categoryId === c.id ? "bg-[var(--ink)] font-bold text-white" : "text-[var(--muted)] hover:bg-white hover:text-[var(--ink)]"
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-[.1em] text-[#a4aaa6]">Brand</h3>
                <div className="mt-3 space-y-2">
                  {(filtersData?.brands ?? []).map((brand) =>
                    filterInput(brand.name, brand.id, brandId === brand.id, (next) =>
                      setBrandId(next ? brand.id : undefined)
                    )
                  )}
                </div>
              </div>

              {attributeGroups.map((group) => (
                <div key={group.attribute_id}>
                  <h3 className="text-xs font-bold uppercase tracking-[.1em] text-[#a4aaa6]">{group.name}</h3>
                  <div className="mt-3 space-y-2">
                    {group.values.map((value) =>
                      filterInput(value, value, attrSelections[group.attribute_id] === value, (next) =>
                        setAttrSelections((prev) => ({
                          ...prev,
                          [group.attribute_id]: next ? value : "",
                        }))
                      )
                    )}
                  </div>
                </div>
              ))}

              <div>
                <h3 className="text-xs font-bold uppercase tracking-[.1em] text-[#a4aaa6]">Condition</h3>
                <div className="mt-3 space-y-2">
                  {conditionOptions.map((condition) =>
                    filterInput(condition.replace("_", " "), condition, conditions.includes(condition), (next) =>
                      setConditions((prev) => next ? [...prev, condition] : prev.filter((c) => c !== condition))
                    )
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-[.1em] text-[#a4aaa6]">Price (RWF)</h3>
                <div className="mt-3 flex items-center gap-2">
                  <input
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    placeholder="Min"
                    inputMode="numeric"
                    className="w-full rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
                  />
                  <span className="text-[var(--muted)]">–</span>
                  <input
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    placeholder="Max"
                    inputMode="numeric"
                    className="w-full rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm outline-none focus:border-[var(--teal)]"
                  />
                </div>
              </div>

              {filterInput("In stock only", "stock", inStock, setInStock)}

              {(attributeGroups.length > 1 || conditions.length > 0 || brandId || minPrice || maxPrice || inStock) && (
                <button
                  onClick={() => {
                    setBrandId(undefined);
                    setAttrSelections({});
                    setConditions([]);
                    setMinPrice("");
                    setMaxPrice("");
                    setInStock(false);
                  }}
                  className="text-xs font-bold text-[var(--coral)] hover:underline"
                >
                  Clear all filters
                </button>
              )}
            </aside>

            {/* Results */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
                <div>
                  <p className="text-xs text-[var(--muted)]">
                    {loading ? "Loading…" : `Showing ${items.length} offer${items.length === 1 ? "" : "s"}`}
                  </p>
                  <h2 className="mt-1 text-xl font-black tracking-[-.03em]">
                    {categoryId ? categories.find((c) => c.id === categoryId)?.name ?? "All products" : "All products"}
                  </h2>
                </div>
                <div className="relative">
                  <select
                    value={sort}
                    onChange={(e) => setSort(e.target.value as typeof sort)}
                    className="appearance-none rounded-lg border border-[var(--line)] bg-white py-2 pl-3 pr-8 text-xs font-semibold outline-none"
                  >
                    <option value="price_asc">Price: low to high</option>
                    <option value="price_desc">Price: high to low</option>
                    <option value="newest">Newest</option>
                  </select>
                  <ChevronDown size={14} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
                </div>
              </div>

              {error && (
                <p role="alert" className="mt-4 rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>
              )}

              {loading ? (
                <div className="mt-7 rounded-xl border border-[var(--line)] bg-white p-14 text-center text-sm text-[var(--muted)]">
                  Loading products…
                </div>
              ) : items.length === 0 ? (
                <div className="mt-7 rounded-xl border border-dashed border-[var(--line)] bg-white p-14 text-center">
                  <SlidersHorizontal className="mx-auto text-[#9aa9a1]" size={28} />
                  <h3 className="mt-4 font-bold">No products match</h3>
                  <p className="mt-2 text-sm text-[var(--muted)]">Try clearing some filters or a different search.</p>
                </div>
              ) : (
                <div className="mt-7 grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3 lg:grid-cols-4">
                  {items.map((item) => {
                    const image = item.images.length ? item.images[0].url : null;
                    const variantLabel = item.variant.attribute_values.map((v) => v.value).join(" · ");
                    return (
                      <Link href={`/products/${item.product.id}`} key={item.listing_id} className="group">
                        <div className="relative aspect-square overflow-hidden rounded-xl bg-[#e8f3ed]">
                          {image ? (
                            <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${image})` }} />
                          ) : (
                            <div className="grid h-full w-full place-items-center font-black tracking-tight text-[#9aa9a1]">
                              {item.product.name.slice(0, 2).toUpperCase()}
                            </div>
                          )}
                          <span className="absolute left-2.5 top-2.5 rounded-full bg-white/90 px-2 py-1 text-[9px] font-bold text-[var(--ink)]">
                            {item.condition.replace("_", " ")}
                          </span>
                          {item.stock > 0 && (
                            <span className="absolute right-2.5 top-2.5 rounded-full bg-[var(--ink)]/80 px-2 py-1 text-[9px] font-bold text-white">
                              {item.stock} in stock
                            </span>
                          )}
                        </div>
                        <div className="mt-3 space-y-1">
                          <p className="truncate text-sm font-bold">{item.product.name}</p>
                          {variantLabel && <p className="truncate text-[11px] text-[var(--muted)]">{variantLabel}</p>}
                          <p className="truncate text-[11px] text-[var(--muted)]">by {item.seller.business_name}</p>
                          <p className="text-sm font-black tracking-tight">{rwf(item.price)}</p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            void addToCart(item.listing_id);
                          }}
                          className={`mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-bold transition-colors ${
                            addedId === item.listing_id
                              ? "bg-[#e8f4ed] text-[#2d7a5e]"
                              : isAuthenticated
                                ? "bg-[var(--ink)] text-white hover:bg-[#2e3d38]"
                                : "border border-[var(--line)] text-[var(--muted)] hover:text-[var(--ink)]"
                          }`}
                        >
                          {addedId === item.listing_id ? (<><Check size={13} /> Added</>) : (<><ShoppingCart size={13} /> {isAuthenticated ? "Add to cart" : "Log in to buy"}</>)}
                        </button>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}