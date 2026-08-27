"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronDown, Search, ShoppingBag, SlidersHorizontal, Star } from "lucide-react";
import { Footer } from "@/app/_components/public/footer";
import { Header } from "@/app/_components/public/header";
import { products } from "@/app/lib/data";

const productImages = [
  "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1612817288484-6f916006741a?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1596433809254-4aded0b8a742?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
  "https://images.unsplash.com/photo-1602928321679-560bb453f190?auto=format&fit=crop&w=900&q=85",
];

const categories = ["All products", "Food & Beverage", "Clothing", "Health & Beauty", "Home & Garden", "Electronics"];

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All products");

  const filteredProducts = useMemo(() => products.filter((product) => {
    const matchesCategory = category === "All products" || product.category === category;
    const query = search.toLowerCase().trim();
    return matchesCategory && (!query || `${product.name} ${product.sellerName} ${product.category}`.toLowerCase().includes(query));
  }), [category, search]);

  return <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]"><Header /><main>
    <section className="border-b border-[var(--line)] bg-[#f0f5ed]"><div className="mx-auto max-w-6xl px-6 pb-12 pt-14 sm:pb-16 sm:pt-20"><div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">The Muhuze shop</p><h1 className="mt-4 text-4xl font-black tracking-[-.05em] sm:text-6xl">Find something <span className="text-[var(--coral)]">worth keeping.</span></h1><p className="mt-5 max-w-xl text-base leading-7 text-[var(--muted)]">A considered collection of products from independent sellers across the network.</p></div><div className="mt-9 flex max-w-2xl items-center gap-3 rounded-xl border border-[#c8d7cc] bg-white p-2 shadow-sm"><Search className="ml-2 text-[#899990]" size={19} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products, sellers, or categories" className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm outline-none placeholder:text-[#899990]" /><button className="hidden rounded-lg bg-[var(--ink)] px-5 py-2.5 text-sm font-bold text-white sm:block">Search</button></div></div></section>
    <section className="mx-auto max-w-6xl px-6 py-10 sm:py-14"><div className="flex flex-col gap-5 lg:flex-row lg:items-start"><aside className="w-full shrink-0 lg:w-52"><div className="flex items-center justify-between"><h2 className="text-sm font-bold">Browse categories</h2><SlidersHorizontal size={16} className="text-[#899990] lg:hidden" /></div><div className="mt-4 flex gap-2 overflow-x-auto pb-2 lg:grid lg:gap-1 lg:overflow-visible">{categories.map((item) => <button key={item} onClick={() => setCategory(item)} className={`whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm transition-colors ${category === item ? "bg-[var(--ink)] font-bold text-white" : "text-[var(--muted)] hover:bg-white hover:text-[var(--ink)]"}`}>{item}</button>)}</div></aside><div className="min-w-0 flex-1"><div className="flex items-center justify-between border-b border-[var(--line)] pb-4"><div><p className="text-xs text-[var(--muted)]">Showing {filteredProducts.length} of {products.length} products</p><h2 className="mt-1 text-xl font-black tracking-[-.03em]">All products</h2></div><button className="flex items-center gap-2 rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-xs font-semibold">Featured <ChevronDown size={14} /></button></div>{filteredProducts.length ? <div className="mt-7 grid grid-cols-2 gap-x-4 gap-y-9 sm:grid-cols-3 lg:grid-cols-4">{filteredProducts.map((product) => { const imageIndex = products.findIndex((item) => item.id === product.id); return <Link href="/login" key={product.id} className="group"><div className="relative aspect-square overflow-hidden rounded-xl bg-[#e8f3ed]"><div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${productImages[imageIndex]})` }} /><span className="absolute left-2.5 top-2.5 rounded-full bg-white/90 px-2 py-1 text-[9px] font-bold text-[var(--ink)]">{product.category}</span><button aria-label={`Add ${product.name} to cart`} className="absolute bottom-2.5 right-2.5 grid h-9 w-9 place-items-center rounded-full bg-white text-[var(--ink)] opacity-0 shadow-md transition-opacity group-hover:opacity-100"><ShoppingBag size={16} /></button></div><div className="mt-3 flex items-start justify-between gap-2"><div className="min-w-0"><h3 className="truncate text-sm font-bold group-hover:text-[#39836e]">{product.name}</h3><p className="mt-1 truncate text-xs text-[var(--muted)]">{product.sellerName}</p><div className="mt-2 flex items-center gap-1 text-[10px] text-[#c29142]"><Star size={11} fill="currentColor" /> 4.8 <span className="text-[var(--muted)]">(12)</span></div></div><p className="shrink-0 text-sm font-bold">${product.price.toFixed(2)}</p></div></Link>; })}</div> : <div className="py-20 text-center"><p className="text-lg font-bold">No products found</p><p className="mt-2 text-sm text-[var(--muted)]">Try another search or category.</p></div>}</div></div></section>
  </main><Footer /></div>;
}
