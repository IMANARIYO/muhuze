import { BadgeCheck, Gift, Headset, Wallet, type LucideIcon } from 'lucide-react'

// Shared by the header and the footer.
export const links = [
  { to: '/products', label: 'All products' },
  { to: '/products?type=sale', label: 'Buy' },
  { to: '/products?type=rental', label: 'Rent' },
  { to: '/products?type=service', label: 'Services' },
]

export const features: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: BadgeCheck, title: 'Verified sellers', text: 'Subscribed and trusted' },
  { icon: Gift, title: 'Referral rewards', text: 'Earn on every deal' },
  { icon: Wallet, title: 'Clear earnings', text: 'Track it in your wallet' },
  { icon: Headset, title: 'Direct contact', text: 'Talk to the seller' },
]
