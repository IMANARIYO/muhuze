import { ProductGrid } from '@/components/shared/ProductGrid'
import type { Product } from '@/types/product'

export function Trending({ products }: { products?: Product[] }) {
  const top = products
    ?.toSorted((a, b) => b.views - a.views)
    .slice(0, 8)

  return (
    <section className="mx-auto max-w-7xl px-4 py-10">
      <ProductGrid products={top} empty="Nothing trending here yet." />
    </section>
  )
}
