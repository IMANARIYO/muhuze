import { Link } from 'react-router'
import { Logo } from '@/components/shared/Logo'

const links = [
  { to: '/products?type=sale', label: 'Buy' },
  { to: '/products?type=rental', label: 'Rent' },
  { to: '/products?type=service', label: 'Services' },
  { to: '/wishlist', label: 'Wishlist' },
]

export function Footer() {
  return (
    <footer className="mt-auto border-t bg-sidebar">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-4 px-4 py-8 md:flex-row md:justify-between">
        <Logo />
        <nav className="flex gap-5 text-sm text-muted-foreground">
          {links.map((link) => (
            <Link key={link.to} to={link.to} className="transition hover:text-primary">{link.label}</Link>
          ))}
        </nav>
        <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} Muhuze. All rights reserved.</p>
      </div>
    </footer>
  )
}
