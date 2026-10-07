import { Gift, Heart, ShoppingCart } from 'lucide-react'
import { Link, NavLink } from 'react-router'
import { Logo } from '@/components/shared/Logo'
import { buttonVariants } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import type { User } from '@/types/user'
import { features, links } from './nav'
import { ProfileMenu } from './ProfileMenu'
import { SearchBar } from './SearchBar'
import { ShopsMenu } from './ShopsMenu'

interface HeaderProps {
  shops: string[]
  user?: User
  showDashboard: boolean
  wishlistCount: number
  cartCount: number
}

export function Header({ shops, user, showDashboard, wishlistCount, cartCount }: HeaderProps) {
  const counters = [
    { to: '/wishlist', label: 'Wishlist', icon: Heart, count: wishlistCount },
    { to: '/cart', label: 'Cart', icon: ShoppingCart, count: cartCount },
  ]

  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur-lg">
      <p className="flex items-center justify-center gap-2 bg-primary px-4 py-1.5 text-center text-xs font-medium text-primary-foreground">
        <Gift className="size-3.5" /> Invite friends and earn commission on every deal they make
      </p>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Logo />
        <SearchBar className="order-last w-full md:order-none md:w-auto md:flex-1" />
        <div className="ml-auto flex items-center gap-1">
          {counters.map(({ to, label, icon: Icon, count }) => (
            <Link key={to} to={to} aria-label={label} className={cn(buttonVariants({ variant: 'ghost', size: 'icon-lg' }), 'relative')}>
              <Icon />
              {count > 0 && (
                <span className="absolute -top-0.5 -right-0.5 grid size-4 place-items-center rounded-full bg-highlight text-[10px] font-bold text-highlight-foreground">
                  {count}
                </span>
              )}
            </Link>
          ))}
          {user && <ProfileMenu user={user} showDashboard={showDashboard} />}
        </div>
      </div>
      <div className="mx-auto flex max-w-7xl items-center gap-1 overflow-x-auto px-4 pb-2 text-sm/[18px]">
        <nav className="flex gap-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className="rounded-full px-3 py-1 whitespace-nowrap text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
            >
              {link.label}
            </NavLink>
          ))}
          {shops.length > 0 && <ShopsMenu shops={shops} />}
        </nav>
        <ul className="ml-auto flex gap-5 pl-4">
          {features.map(({ icon: Icon, title, text }) => (
            <Tooltip key={title}>
              <TooltipTrigger render={<li className="flex items-center gap-1.5 text-xs whitespace-nowrap text-muted-foreground" />}>
                <Icon className="size-4 text-primary" /> {title}
              </TooltipTrigger>
              <TooltipContent>{text}</TooltipContent>
            </Tooltip>
          ))}
        </ul>
      </div>
    </header>
  )
}
