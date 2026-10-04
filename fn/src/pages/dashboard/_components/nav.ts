import {
  CreditCard, LayoutDashboard, Package, Share2, ShieldCheck, Users, Wallet,
  type LucideIcon,
} from 'lucide-react'

interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  permission: string
}

export const navGroups: { label: string; items: NavItem[] }[] = [
  {
    label: 'Main',
    items: [{ label: 'Overview', to: '/dashboard', icon: LayoutDashboard, permission: 'dashboard.view' }],
  },
  {
    label: 'Marketplace',
    items: [
      { label: 'Products', to: '/dashboard/products', icon: Package, permission: 'product.manage' },
      { label: 'Subscriptions', to: '/dashboard/subscriptions', icon: CreditCard, permission: 'subscription.manage' },
      { label: 'Referrals', to: '/dashboard/referrals', icon: Share2, permission: 'referral.view' },
    ],
  },
  {
    label: 'Finance',
    items: [{ label: 'Wallet', to: '/dashboard/wallet', icon: Wallet, permission: 'wallet.view' }],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Users', to: '/dashboard/users', icon: Users, permission: 'user.manage' },
      { label: 'Roles & permissions', to: '/dashboard/roles', icon: ShieldCheck, permission: 'role.manage' },
    ],
  },
]

export const navItems = navGroups.flatMap((group) => group.items)
