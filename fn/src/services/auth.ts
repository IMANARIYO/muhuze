import { api, API_URL } from '@/lib/api'
import type { User } from '@/types/user'

// Until the backend is connected (VITE_API_URL unset), demo users are used so the UI can be developed.
// The dashboard can switch between them to show what each set of permissions sees.
const demoUsers = {
  Admin: {
    id: 1,
    name: 'Demo Admin',
    email: 'admin@muhuze.app',
    role: 'Admin',
    referralCode: 'DEMO2026',
    permissions: [
      'dashboard.view', 'product.manage', 'order.manage', 'subscription.manage',
      'referral.view', 'wallet.view', 'user.manage', 'role.manage',
    ],
  },
  Seller: {
    id: 2,
    name: 'Eric Mugisha',
    email: 'eric@kigalimobile.rw',
    role: 'Seller',
    shop: 'Kigali Mobile',
    referralCode: 'ERIC2026',
    permissions: ['dashboard.view', 'product.own', 'order.own', 'subscription.own', 'referral.view', 'wallet.own'],
  },
} satisfies Record<string, User>

export type DemoRole = keyof typeof demoUsers

const KEY = 'demo-role'

/** Empty once the backend is connected: the real user comes from the API. */
export const demoRoles: DemoRole[] = API_URL ? [] : ['Admin', 'Seller']

const demoRole = (): DemoRole => (localStorage.getItem(KEY) === 'Seller' ? 'Seller' : 'Admin')

export const setDemoRole = (role: DemoRole) => localStorage.setItem(KEY, role)

export const getMe = (): Promise<User> =>
  API_URL ? api<User>('/auth/me') : Promise.resolve(demoUsers[demoRole()])
