import type { IconType } from 'react-icons'
import { FaFacebook, FaInstagram, FaLinkedin, FaXTwitter, FaYoutube } from 'react-icons/fa6'
import { Link } from 'react-router'
import { Logo } from '@/components/shared/Logo'
import { features, links } from './nav'

// Placeholder addresses until the real Muhuze accounts are known.
const socials: { label: string; href: string; icon: IconType }[] = [
  { label: 'Facebook', href: '#', icon: FaFacebook },
  { label: 'Instagram', href: '#', icon: FaInstagram },
  { label: 'X', href: '#', icon: FaXTwitter },
  { label: 'YouTube', href: '#', icon: FaYoutube },
  { label: 'LinkedIn', href: '#', icon: FaLinkedin },
]

export function Footer() {
  return (
    <footer className="mt-auto border-t bg-sidebar">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-[1.6fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-3 text-sm font-semibold text-highlight">Buy • Rent • Book • Earn</p>
          <p className="mt-3 max-w-xs text-sm leading-6 text-muted-foreground">
            A social marketplace where sellers, buyers and the people who invite them meet around products.
          </p>
          <div className="mt-5 flex gap-2">
            {socials.map(({ label, href, icon: Icon }) => (
              <a
                key={label}
                href={href}
                aria-label={label}
                target="_blank"
                rel="noreferrer"
                className="grid size-9 place-items-center rounded-full bg-accent text-muted-foreground transition hover:-translate-y-0.5 hover:bg-primary hover:text-primary-foreground"
              >
                <Icon className="size-4" />
              </a>
            ))}
          </div>
        </div>

        <nav aria-label="Marketplace">
          <h3 className="font-heading font-semibold">Marketplace</h3>
          <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
            {[...links, { to: '/wishlist', label: 'Wishlist' }].map((link) => (
              <li key={link.to}>
                <Link to={link.to} className="transition hover:text-primary">{link.label}</Link>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h3 className="font-heading font-semibold">Why Muhuze</h3>
          <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
            {features.map(({ icon: Icon, title }) => (
              <li key={title} className="flex items-center gap-2">
                <Icon className="size-4 text-primary" /> {title}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="border-t px-4 py-5 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} Muhuze. All rights reserved.
      </p>
    </footer>
  )
}
