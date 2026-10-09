import { useQuery } from '@tanstack/react-query'
import { Outlet } from 'react-router'
import { useCart } from '@/hooks/use-cart'
import { useSession } from '@/hooks/use-session'
import { useWishlist } from '@/hooks/use-wishlist'
import { getShops } from '@/services/products'
import { Footer } from './_components/Footer'
import { Header } from './_components/Header'

export default function PublicLayout() {
  const { user, can } = useSession()
  const { ids } = useWishlist()
  const cart = useCart()
  const { data: shops } = useQuery({ queryKey: ['shops'], queryFn: getShops })

  return (
    <div className="flex min-h-svh flex-col">
      <Header shops={shops ?? []} user={user} showDashboard={can('dashboard.view')} wishlistCount={ids.length} cartCount={cart.ids.length} />
      <Outlet />
      <Footer />
    </div>
  )
}
