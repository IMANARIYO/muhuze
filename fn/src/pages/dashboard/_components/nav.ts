import {
  BadgeCheck, ClipboardList, CreditCard, LayoutDashboard, Package, PiggyBank, Share2, ShieldCheck, Users, Wallet,
  type LucideIcon,
} from 'lucide-react'

interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** The link and its page are open to anyone holding at least one of these. */
  permissions: string[]
}

// `.manage` permissions cover the whole platform; `.own` ones cover only what belongs to the user.
export const navGroups: { label: string; items: NavItem[] }[] = [
  {
    label: 'Main',
    items: [{ label: 'Overview', to: '/dashboard', icon: LayoutDashboard, permissions: ['dashboard.view'] }],
  },
  {
    label: 'Marketplace',
    items: [
      { label: 'Products', to: '/dashboard/products', icon: Package, permissions: ['product.manage', 'product.own'] },
      { label: 'Orders', to: '/dashboard/orders', icon: ClipboardList, permissions: ['order.manage', 'order.own'] },
      { label: 'Subscriptions', to: '/dashboard/subscriptions', icon: CreditCard, permissions: ['subscription.manage'] },
      { label: 'My subscription', to: '/dashboard/subscription', icon: BadgeCheck, permissions: ['subscription.own'] },
      { label: 'Referrals', to: '/dashboard/referrals', icon: Share2, permissions: ['referral.view'] },
    ],
  },
  {
    label: 'Finance',
    items: [
      { label: 'Wallet', to: '/dashboard/wallet', icon: Wallet, permissions: ['wallet.view'] },
      { label: 'My wallet', to: '/dashboard/earnings', icon: PiggyBank, permissions: ['wallet.own'] },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Users', to: '/dashboard/users', icon: Users, permissions: ['user.manage'] },
      { label: 'Roles & permissions', to: '/dashboard/roles', icon: ShieldCheck, permissions: ['role.manage'] },
    ],
  },
]

export const navItems = navGroups.flatMap((group) => group.items)
