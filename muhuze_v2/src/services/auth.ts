import { api, API_URL } from '@/lib/api'
import type { User } from '@/types/user'

// Until the backend is connected (VITE_API_URL unset), a demo admin is used so the UI can be developed.
const demoUser: User = {
  id: 1,
  name: 'Demo Admin',
  email: 'admin@muhuze.app',
  role: 'Admin',
  permissions: [
    'dashboard.view', 'product.manage', 'subscription.manage',
    'referral.view', 'wallet.view', 'user.manage', 'role.manage',
  ],
}

export const getMe = (): Promise<User> =>
  API_URL ? api<User>('/auth/me') : Promise.resolve(demoUser)
