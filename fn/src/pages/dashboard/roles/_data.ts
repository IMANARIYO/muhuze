import { createStore, type Stored } from '@/lib/demo-store'

// Predefined by the backend: admins assign these to roles but cannot create new ones.
export const permissionGroups = [
  { group: 'General', items: [{ key: 'dashboard.view', label: 'Access the dashboard' }] },
  { group: 'Marketplace', items: [
    { key: 'product.manage', label: 'Manage all products' },
    { key: 'product.own', label: 'Manage own products' },
    { key: 'order.manage', label: 'See and approve all orders' },
    { key: 'order.own', label: 'See own approved orders' },
    { key: 'subscription.manage', label: 'Manage subscriptions and rates' },
    { key: 'subscription.own', label: 'Subscribe to a plan' },
    { key: 'referral.view', label: 'View referrals' },
  ] },
  { group: 'Finance', items: [
    { key: 'wallet.view', label: 'View the platform wallet' },
    { key: 'wallet.own', label: 'View own wallet' },
  ] },
  { group: 'Administration', items: [
    { key: 'user.manage', label: 'Manage users' },
    { key: 'role.manage', label: 'Manage roles and permissions' },
  ] },
]

// `.own` permissions are for people who sell; an admin manages everything instead.
const all = permissionGroups.flatMap((group) => group.items.map((item) => item.key)).filter((key) => !key.endsWith('.own'))

interface Role {
  name: string
  description: string
  permissions: string[]
  /** System roles cannot be deleted. */
  system?: boolean
}

export type StoredRole = Stored<Role>

export const useRoles = createStore<Role>([
  { name: 'Admin', description: 'Full control of the platform.', permissions: all, system: true },
  { name: 'Seller', description: 'Lists products and tracks earnings.', permissions: ['dashboard.view', 'product.own', 'order.own', 'subscription.own', 'referral.view', 'wallet.own'], system: true },
  { name: 'Buyer', description: 'Browses, buys and refers friends.', permissions: [], system: true },
  { name: 'Support', description: 'Helps users and reviews listings.', permissions: ['dashboard.view', 'product.manage', 'user.manage'] },
])
