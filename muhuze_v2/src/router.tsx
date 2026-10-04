import type { ComponentType } from 'react'
import { createBrowserRouter } from 'react-router'

// Every layout and page is its own chunk: buyers never download dashboard code.
const page = (load: () => Promise<{ default: ComponentType }>) => async () => ({
  Component: (await load()).default,
})

export const router = createBrowserRouter([
  {
    lazy: page(() => import('@/layouts/PublicLayout')),
    children: [
      { index: true, lazy: page(() => import('@/pages/home')) },
      { path: 'products', lazy: page(() => import('@/pages/products')) },
      { path: 'products/:id', lazy: page(() => import('@/pages/products/detail')) },
      { path: 'wishlist', lazy: page(() => import('@/pages/wishlist')) },
      { path: '*', lazy: page(() => import('@/pages/not-found')) },
    ],
  },
  {
    path: 'dashboard',
    lazy: page(() => import('@/layouts/DashboardLayout')),
    children: [
      { index: true, lazy: page(() => import('@/pages/dashboard')) },
      { path: 'products', lazy: page(() => import('@/pages/dashboard/products')) },
      { path: 'subscriptions', lazy: page(() => import('@/pages/dashboard/subscriptions')) },
      { path: 'referrals', lazy: page(() => import('@/pages/dashboard/referrals')) },
      { path: 'wallet', lazy: page(() => import('@/pages/dashboard/wallet')) },
      { path: 'users', lazy: page(() => import('@/pages/dashboard/users')) },
      { path: 'roles', lazy: page(() => import('@/pages/dashboard/roles')) },
      { path: '*', lazy: page(() => import('@/pages/not-found')) },
    ],
  },
])
