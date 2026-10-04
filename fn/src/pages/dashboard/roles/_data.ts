import { createStore, type Stored } from '@/lib/demo-store'

// Predefined by the backend: admins assign these to roles but cannot create new ones.
export const permissionGroups = [
  { group: 'General', items: [{ key: 'dashboard.view', label: 'Access the dashboard' }] },
  { group: 'Marketplace', items: [
    { key: 'product.manage', label: 'Manage products' },
    { key: 'subscription.manage', label: 'Manage subscriptions and rates' },
    { key: 'referral.view', label: 'View referrals' },
  ] },
  { group: 'Finance', items: [{ key: 'wallet.view', label: 'View wallet' }] },
  { group: 'Administration', items: [
    { key: 'user.manage', label: 'Manage users' },
    { key: 'role.manage', label: 'Manage roles and permissions' },
  ] },
]

const all = permissionGroups.flatMap((group) => group.items.map((item) => item.key))

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
  { name: 'Seller', description: 'Lists products and tracks earnings.', permissions: ['dashboard.view', 'product.manage', 'referral.view', 'wallet.view'], system: true },
  { name: 'Buyer', description: 'Browses, buys and refers friends.', permissions: [], system: true },
  { name: 'Support', description: 'Helps users and reviews listings.', permissions: ['dashboard.view', 'product.manage', 'user.manage'] },
])
