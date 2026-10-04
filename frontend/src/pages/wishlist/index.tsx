import { ProductGrid } from '@/components/shared/ProductGrid'
import { useProducts } from '@/hooks/use-products'
import { useWishlist } from '@/hooks/use-wishlist'

export default function Wishlist() {
  const { ids } = useWishlist()
  const { data: products } = useProducts()

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">
      <h1 className="mb-6 animate-rise font-heading text-3xl font-bold">My wishlist</h1>
      <ProductGrid
        products={products?.filter((p) => ids.includes(p.id))}
        empty="Tap the heart on any listing to save it here."
      />
    </main>
  )
}
