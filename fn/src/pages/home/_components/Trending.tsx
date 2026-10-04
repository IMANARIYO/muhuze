import { Flame } from 'lucide-react'
import { useState } from 'react'
import { ProductGrid } from '@/components/shared/ProductGrid'
import { TypeTabs } from '@/components/shared/TypeTabs'
import type { Product, ProductType } from '@/types/product'

export function Trending({ products }: { products?: Product[] }) {
  const [type, setType] = useState<ProductType>()
  const top = products
    ?.filter((p) => !type || p.type === type)
    .toSorted((a, b) => b.views - a.views)
    .slice(0, 8)

  return (
    <section className="mx-auto max-w-7xl px-4 py-10">
      <div className="reveal mb-6 flex flex-wrap items-center justify-between gap-4">
        <h2 className="flex items-center gap-2 font-heading text-2xl font-bold">
          <Flame className="text-highlight" /> Trending this week
        </h2>
        <TypeTabs value={type} onChange={setType} />
      </div>
      <ProductGrid key={type} products={top} empty="Nothing trending here yet." />
    </section>
  )
}
