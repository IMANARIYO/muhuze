import { PackageSearch } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import type { Product } from '@/types/product'
import { ProductCard } from './ProductCard'

const grid = 'grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4'

/** Pass `undefined` while loading. */
export function ProductGrid({ products, empty }: { products?: Product[]; empty: string }) {
  if (!products) {
    return (
      <div className={grid}>
        {Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="aspect-3/4 rounded-2xl" />)}
      </div>
    )
  }

  if (!products.length) {
    return (
      <div className="grid place-items-center gap-3 rounded-2xl border border-dashed py-20 text-muted-foreground">
        <PackageSearch className="size-10" />
        <p>{empty}</p>
      </div>
    )
  }

  return (
    <div className={`${grid} stagger`}>
      {products.map((product) => <ProductCard key={product.id} product={product} />)}
    </div>
  )
}
