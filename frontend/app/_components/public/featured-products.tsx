"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { catalogService, type CatalogListingItem } from "@/app/services/catalog.service";
import { rwf } from "@/app/lib/utils";

export function FeaturedProducts() {
  const [items, setItems] = useState<CatalogListingItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    catalogService
      .list({ sort: "newest", in_stock: true })
      .then((data) => { if (!cancelled) setItems(data.slice(0, 4)); })
      .catch(() => undefined)
      .finally(() => { if (!cancelled) setLoaded(true); });
    return () => { cancelled = true; };
  }, []);

  if (!loaded) {
    return (
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="aspect-[.92] animate-pulse rounded-xl bg-[#e8f3ed]" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="mt-9 rounded-xl border border-dashed border-[var(--line)] bg-[#fafcfa] p-10 text-center text-sm text-[var(--muted)]">
        New products are on the way — check back soon.
      </p>
    );
  }

  return (
    <div className="mt-9 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => {
        const image = item.images.length ? item.images[0].url : null;
        const variantLabel = item.variant.attribute_values.map((v) => v.value).join(" · ");
        return (
          <Link href={`/products/${item.product.id}`} key={item.listing_id} className="group">
            <div className="relative aspect-[.92] overflow-hidden rounded-xl bg-[#e8f3ed]">
              {image ? (
                <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${image})` }} />
              ) : (
                <div className="grid h-full w-full place-items-center font-black tracking-tight text-[#9aa9a1]">
                  {item.product.name.slice(0, 2).toUpperCase()}
                </div>
              )}
              <span className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-[10px] font-bold text-[var(--ink)]">
                {item.condition.replace("_", " ")}
              </span>
            </div>
            <div className="mt-4 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-sm font-bold group-hover:text-[#39836e]">{item.product.name}</h3>
                <p className="mt-1 truncate text-xs text-[var(--muted)]">
                  {item.seller.business_name}{variantLabel ? ` · ${variantLabel}` : ""}
                </p>
              </div>
              <p className="shrink-0 text-sm font-bold">{rwf(item.price)}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}