import Link from "next/link";
import { Package, Plus, ShoppingCart } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Badge } from "@/app/_components/ui/badge";
import { Button } from "@/app/_components/ui/button";
import { products } from "@/app/lib/data";

const categoryColors: Record<string, string> = {
  "Electronics": "#e4edfa",
  "Clothing": "#fbe6e0",
  "Food & Beverage": "#d5f2e2",
  "Home & Garden": "#fbf0ce",
  "Health & Beauty": "#f3e8f8",
  "Sports": "#e8f4ed",
  "Books": "#fdf0e0",
  "Other": "#f2f5f2",
};

export default function ProductsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Products</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Browse all available products from our sellers.
          </p>
        </div>
        <Link href="/dashboard/products/new">
          <Button className="flex items-center gap-2">
            <Plus size={15} /> Add Product
          </Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {["All", "Food & Beverage", "Clothing", "Health & Beauty", "Electronics", "Home & Garden"].map((cat) => (
          <button
            key={cat}
            className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-[11px] font-semibold text-[var(--muted)] transition-colors hover:border-[var(--teal)] hover:text-[var(--teal)]"
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {products.map((product) => (
          <Card key={product.id} className="group transition-shadow hover:shadow-md">
            <CardContent className="p-5">
              <div
                className="mb-4 grid h-16 w-full place-items-center rounded-lg"
                style={{ backgroundColor: categoryColors[product.category] ?? "#f2f5f2" }}
              >
                <Package size={28} className="text-[var(--muted)]" />
              </div>

              <div className="mb-1 flex items-start justify-between gap-2">
                <h3 className="text-sm font-bold leading-tight text-[var(--ink)]">{product.name}</h3>
                <Badge variant="outline" className="shrink-0 text-[9px]">{product.category}</Badge>
              </div>

              <p className="mb-3 text-[11px] leading-relaxed text-[var(--muted)] line-clamp-2">
                {product.description}
              </p>

              <div className="flex items-center justify-between">
                <div>
                  <span className="text-base font-extrabold text-[var(--ink)]">
                    ${product.price.toFixed(2)}
                  </span>
                  {product.unit && (
                    <span className="ml-1 text-[10px] text-[var(--muted)]">/ {product.unit}</span>
                  )}
                </div>
                <span className="text-[10px] text-[var(--muted)]">Stock: {product.stock}</span>
              </div>

              <p className="mt-1 text-[10px] text-[#9ba49e]">by {product.sellerName}</p>

              <button className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--ink)] py-2 text-xs font-bold text-white transition-all hover:-translate-y-0.5 hover:bg-[#2e3d38]">
                <ShoppingCart size={13} /> Add to Cart
              </button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
