import { Outlet } from 'react-router'
import { useCart } from '@/hooks/use-cart'
import { useSession } from '@/hooks/use-session'
import { useWishlist } from '@/hooks/use-wishlist'
import { Footer } from './_components/Footer'
import { Header } from './_components/Header'

export default function PublicLayout() {
  const { user, can } = useSession()
  const { ids } = useWishlist()
  const cart = useCart()

  return (
    <div className="flex min-h-svh flex-col">
      <Header user={user} showDashboard={can('dashboard.view')} wishlistCount={ids.length} cartCount={cart.ids.length} />
      <Outlet />
      <Footer />
    </div>
  )
}
