import { useSearchParams } from 'react-router'
import { ProductGrid } from '@/components/shared/ProductGrid'
import { TypeTabs } from '@/components/shared/TypeTabs'
import { useProducts } from '@/hooks/use-products'
import { isProductType } from '@/types/product'

export default function Products() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const typeParam = params.get('type')
  const type = isProductType(typeParam) ? typeParam : undefined
  const { data: products } = useProducts({ type, q })

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div className="animate-rise">
          <h1 className="font-heading text-3xl font-bold">{q ? `Results for "${q}"` : 'Explore the marketplace'}</h1>
          <p className="text-muted-foreground">{products ? `${products.length} listings` : 'Loading listings...'}</p>
        </div>
        <TypeTabs
          value={type}
          onChange={(next) => setParams({ ...(q && { q }), ...(next && { type: next }) })}
        />
      </div>
      <ProductGrid key={`${type}-${q}`} products={products} empty="No listings match your search." />
    </main>
  )
}
