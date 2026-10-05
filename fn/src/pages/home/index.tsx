import { useProducts } from '@/hooks/use-products'
import { useSession } from '@/hooks/use-session'
import { Hero } from './_components/Hero'
import { Highlights } from './_components/Highlights'
import { Trending } from './_components/Trending'
import { TypeBanners } from './_components/TypeBanners'

// One listing per product type for the hero: a phone, a house and a service.
const heroIds = [1, 7, 10]

export default function Home() {
  const { data: products } = useProducts()
  const { user } = useSession()
  const featured = heroIds.flatMap((id) => products?.find((p) => p.id === id) ?? [])

  return (
    <main className="flex-1">
      <Hero products={featured} />
      <TypeBanners products={products ?? []} />
      <Trending products={products} />
      <Highlights referralCode={user?.referralCode} />
    </main>
  )
}
