import { useSearchParams } from 'react-router'
import { ProductGrid } from '@/components/shared/ProductGrid'
import { useProducts } from '@/hooks/use-products'
import { isProductType } from '@/types/product'

export default function Products() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const location = params.get('location') ?? ''
  const seller = params.get('seller') ?? ''
  const typeParam = params.get('type')
  const type = isProductType(typeParam) ? typeParam : undefined
  const { data: products } = useProducts({ type, q, location, seller })

  const heading = q ? `Results for "${q}"` : seller ? `Listings by ${seller}` : location ? `Listings near ${location}` : 'Explore the marketplace'

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">
      <div className="mb-6 animate-rise">
        <h1 className="font-heading text-3xl font-bold">{heading}</h1>
        <p className="text-muted-foreground">{products ? `${products.length} listings` : 'Loading listings...'}</p>
      </div>
      <ProductGrid key={`${type}-${q}-${location}-${seller}`} products={products} empty="No listings match your search." />
    </main>
  )
}
