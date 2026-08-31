"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  ChevronRight,
  Cpu,
  Home as HomeIcon,
  Leaf,
  ShieldCheck,
  Shirt,
  Sparkles,
  Store,
  type LucideIcon,
} from "lucide-react";
import { Footer } from "./_components/public/footer";
import { Header } from "./_components/public/header";
import { FeaturedProducts } from "./_components/public/featured-products";
import { adminService, type CategoryRecord } from "./services/admin.service";

const steps = [
  { number: "01", title: "Find your next favorite", text: "Explore thoughtful products from independent sellers across Africa." },
  { number: "02", title: "Order with confidence", text: "Your payment is protected while your order makes its way to you." },
  { number: "03", title: "Good commerce, shared", text: "We notify everyone at each step and release the seller payout fairly." },
];

const palette = ["#e8f1df", "#f8e2d6", "#dcebed", "#f4eccf", "#e7e0f0", "#fbe8cf"];

function categoryMeta(name: string, index: number): { icon: LucideIcon; color: string } {
  const n = name.toLowerCase();
  if (n.includes("samsung") || n.includes("techno") || n.includes("tech") || n.includes("phone") || n.includes("electronic")) return { icon: Cpu, color: "#dcebed" };
  if (n.includes("food") || n.includes("drink") || n.includes("grocery")) return { icon: Leaf, color: "#e8f1df" };
  if (n.includes("cloth") || n.includes("fashion") || n.includes("wear")) return { icon: Shirt, color: "#f8e2d6" };
  if (n.includes("home") || n.includes("furniture")) return { icon: HomeIcon, color: "#f4eccf" };
  if (n.includes("health") || n.includes("beauty")) return { icon: Sparkles, color: "#fbe0d8" };
  if (n.includes("book")) return { icon: BookOpen, color: "#e7e0f0" };
  return { icon: Store, color: palette[index % palette.length] };
}

export default function Home() {
  const [categories, setCategories] = useState<CategoryRecord[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useEffect(() => {
    let cancelled = false;
    adminService
      .listCategories()
      .then((list) => {
        if (!cancelled) setCategories(list.filter((c) => !c.parent_id && c.status === "active"));
      })
      .catch(() => {
        if (!cancelled) setCategories([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingCategories(false);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="min-h-screen overflow-hidden bg-[var(--paper)] text-[var(--ink)]">
      <Header />

      <main>
        <section className="relative border-b border-[var(--line)] bg-[#f0f5ed]">
          <div className="mx-auto grid max-w-6xl gap-12 px-6 py-16 md:grid-cols-[.9fr_1.1fr] md:items-center md:py-24">
            <div className="relative z-10">
              <p className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">
                <span className="h-px w-8 bg-[var(--coral)]" /> A marketplace with meaning
              </p>
              <h1 className="max-w-xl text-5xl font-black leading-[.98] tracking-[-.055em] sm:text-6xl lg:text-[76px]">
                Goods that <span className="text-[var(--coral)]">travel</span> further.
              </h1>
              <p className="mt-7 max-w-md text-base leading-7 text-[var(--muted)] sm:text-lg">
                Discover beautiful, useful products from independent sellers across Africa. Every order helps a real business grow.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Link href="/products" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-[var(--ink)] px-6 text-sm font-bold text-white transition-transform hover:-translate-y-0.5">
                  Explore the marketplace <ArrowRight size={17} />
                </Link>
                <a href="#how-it-works" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-[#b9c9c0] px-6 text-sm font-bold text-[var(--ink)] hover:bg-white">
                  How it works <ChevronRight size={16} />
                </a>
              </div>
              <div className="mt-10 flex items-center gap-3 text-xs text-[var(--muted)]">
                <div className="flex -space-x-2">
                  {["#d7896d", "#829eb8", "#8dba9e", "#d6b55b"].map((color) => <span key={color} className="h-7 w-7 rounded-full border-2 border-[#f0f5ed]" style={{ background: color }} />)}
                </div>
                <span><strong className="text-[var(--ink)]">500+</strong> sellers building something good</span>
              </div>
            </div>

            <div className="relative min-h-[390px] sm:min-h-[470px]">
              <div className="absolute inset-5 rotate-3 rounded-[28px] bg-[#dce9d7]" />
              <div className="absolute inset-0 overflow-hidden rounded-[28px] border-[10px] border-white bg-[#dce9d7] shadow-[0_24px_60px_rgba(23,33,31,.14)]">
                <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: "url('/hero-marketplace.png')" }} />
                <div className="absolute inset-0 bg-gradient-to-t from-[#17211fbb] via-transparent to-transparent" />
                <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between text-white">
                  <div><p className="text-xs uppercase tracking-[.16em] text-white/70">Editor&apos;s find</p><p className="mt-1 text-2xl font-bold">Handmade, considered, yours.</p></div>
                  <span className="grid h-12 w-12 place-items-center rounded-full bg-[#d6f34d] text-[var(--ink)]"><ArrowRight size={20} /></span>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-3 flex items-center gap-3 rounded-xl border border-[var(--line)] bg-white p-3 shadow-lg sm:left-0">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-[#e8f3ed] text-[#39836e]"><ShieldCheck size={20} /></span>
                <div><p className="text-xs font-bold">Protected payments</p><p className="mt-1 text-[10px] text-[var(--muted)]">Every step, clearly tracked</p></div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-20 sm:py-28" aria-labelledby="categories-title">
          <div className="flex items-end justify-between gap-5"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Start somewhere good</p><h2 id="categories-title" className="mt-3 text-3xl font-black tracking-[-.04em] sm:text-4xl">Shop by category</h2></div><Link href="/products" className="hidden items-center gap-1 text-sm font-bold text-[#39836e] sm:flex">View all <ArrowRight size={15} /></Link></div>
          <div className="mt-9 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
            {loadingCategories
              ? Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="rounded-xl border border-[var(--line)] bg-white p-5">
                    <div className="grid h-12 w-12 place-items-center rounded-full bg-[#f2f5f2] animate-pulse" />
                    <div className="mt-8 h-4 w-2/3 rounded bg-[#f2f5f2] animate-pulse" />
                    <div className="mt-2 h-3 w-1/2 rounded bg-[#f2f5f2] animate-pulse" />
                  </div>
                ))
              : categories.length === 0 ? (
                <div className="col-span-2 rounded-xl border border-dashed border-[var(--line)] bg-white p-8 text-sm text-[var(--muted)] md:col-span-4 md:text-center">
                  Categories will appear here once the shop is set up.
                </div>
              ) : (
                categories.map((category, index) => {
                  const { icon: Icon, color } = categoryMeta(category.name, index);
                  return (
                    <Link href={`/products?category=${category.id}`} key={category.id} className="group rounded-xl border border-[var(--line)] bg-white p-5 transition-all hover:-translate-y-1 hover:shadow-lg">
                      <span className="grid h-12 w-12 place-items-center rounded-full" style={{ background: color }}><Icon size={22} strokeWidth={1.7} /></span>
                      <h3 className="mt-8 text-base font-bold capitalize">{category.name}</h3>
                      <p className="mt-1 truncate text-xs text-[var(--muted)]">{category.description || "Explore the collection"}</p>
                      <ArrowRight className="mt-5 text-[#9aa9a1] transition-transform group-hover:translate-x-1" size={16} />
                    </Link>
                  );
                })
              )}
          </div>
        </section>

        <section className="bg-white py-20 sm:py-24" aria-labelledby="products-title">
          <div className="mx-auto max-w-6xl px-6"><div className="flex items-end justify-between gap-5"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Fresh from the network</p><h2 id="products-title" className="mt-3 text-3xl font-black tracking-[-.04em] sm:text-4xl">A few things we love</h2></div><Link href="/products" className="hidden items-center gap-1 text-sm font-bold text-[#39836e] sm:flex">Browse products <ArrowRight size={15} /></Link></div>
            <FeaturedProducts />
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20 sm:py-28" aria-labelledby="process-title"><div className="grid gap-12 md:grid-cols-[.75fr_1.25fr] md:items-start"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#5d8974]">Simple by design</p><h2 id="process-title" className="mt-3 max-w-sm text-3xl font-black leading-tight tracking-[-.04em] sm:text-4xl">Commerce that keeps everyone in the loop.</h2><p className="mt-5 max-w-sm text-sm leading-6 text-[var(--muted)]">Clients shop, sellers grow, and admins keep every payment visible. Muhuze makes the handoff feel human.</p><Link href="/dashboard" className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-[#39836e]">See your marketplace dashboard <ArrowRight size={16} /></Link></div><div className="grid gap-0 border-t border-[var(--line)]">{steps.map((step) => <div key={step.number} className="grid gap-5 border-b border-[var(--line)] py-6 sm:grid-cols-[70px_1fr] sm:gap-7"><span className="font-mono text-sm text-[var(--coral)]">{step.number}</span><div><h3 className="text-lg font-bold">{step.title}</h3><p className="mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">{step.text}</p></div></div>)}</div></div></section>

      </main>

      <Footer />
    </div>
  );
}
