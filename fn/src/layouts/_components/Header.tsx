import { Gift, Heart, LayoutDashboard } from 'lucide-react'
import { Link, NavLink } from 'react-router'
import { Logo } from '@/components/shared/Logo'
import { buttonVariants } from '@/components/ui/button'
import { useSession } from '@/hooks/use-session'
import { useWishlist } from '@/hooks/use-wishlist'
import { cn } from '@/lib/utils'
import { SearchBar } from './SearchBar'

const links = [
  { to: '/products', label: 'All products' },
  { to: '/products?type=sale', label: 'Buy' },
  { to: '/products?type=rental', label: 'Rent' },
  { to: '/products?type=service', label: 'Services' },
]

export function Header() {
  const { can } = useSession()
  const { ids } = useWishlist()

  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur-lg">
      <p className="flex items-center justify-center gap-2 bg-primary px-4 py-1.5 text-center text-xs font-medium text-primary-foreground">
        <Gift className="size-3.5" /> Invite friends and earn commission on every deal they make
      </p>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Logo />
        <SearchBar className="order-last w-full md:order-none md:w-auto md:flex-1" />
        <div className="ml-auto flex items-center gap-1">
          <Link to="/wishlist" aria-label="Wishlist" className={cn(buttonVariants({ variant: 'ghost', size: 'icon-lg' }), 'relative')}>
            <Heart />
            {ids.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 grid size-4 place-items-center rounded-full bg-highlight text-[10px] font-bold text-highlight-foreground">
                {ids.length}
              </span>
            )}
          </Link>
          {can('dashboard.view') && (
            <Link to="/dashboard" className={buttonVariants({ size: 'lg' })}>
              <LayoutDashboard /> <span className="hidden sm:inline">Dashboard</span>
            </Link>
          )}
        </div>
      </div>
      <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-2 text-sm font-medium">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className="rounded-full px-3 py-1 whitespace-nowrap text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
