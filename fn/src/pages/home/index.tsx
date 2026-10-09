import { useProducts } from '@/hooks/use-products'
import { BestSellers } from './_components/BestSellers'
import { CategoryCards } from './_components/CategoryCards'
import { Hero } from './_components/Hero'
import { Trending } from './_components/Trending'

// One listing per product type for the hero: a phone, a house and a service.
const heroIds = [1, 7, 10]

export default function Home() {
  const { data: products } = useProducts()
  const featured = heroIds.flatMap((id) => products?.find((p) => p.id === id) ?? [])

  return (
    <main className="flex-1">
      <Hero products={featured} />
      <CategoryCards products={products ?? []} />
      <Trending products={products} />
      <BestSellers products={products ?? []} />
    </main>
  )
}
