import type { ComponentType } from 'react'
import { createBrowserRouter } from 'react-router'
import RouteError from '@/pages/error'

// Every layout and page is its own chunk: buyers never download dashboard code.
const page = (load: () => Promise<{ default: ComponentType }>) => async () => ({
  Component: (await load()).default,
})

export const router = createBrowserRouter([
  {
    ErrorBoundary: RouteError,
    lazy: page(() => import('@/layouts/PublicLayout')),
    children: [
      { index: true, lazy: page(() => import('@/pages/home')) },
      { path: 'products', lazy: page(() => import('@/pages/products')) },
      { path: 'products/:id', lazy: page(() => import('@/pages/products/detail')) },
      { path: 'wishlist', lazy: page(() => import('@/pages/wishlist')) },
      { path: 'cart', lazy: page(() => import('@/pages/cart')) },
      { path: 'checkout', lazy: page(() => import('@/pages/checkout')) },
      { path: '*', lazy: page(() => import('@/pages/not-found')) },
    ],
  },
  {
    path: 'dashboard',
    ErrorBoundary: RouteError,
    lazy: page(() => import('@/layouts/DashboardLayout')),
    children: [
      { index: true, lazy: page(() => import('@/pages/dashboard')) },
      { path: 'products', lazy: page(() => import('@/pages/dashboard/products')) },
      { path: 'orders', lazy: page(() => import('@/pages/dashboard/orders')) },
      { path: 'subscriptions', lazy: page(() => import('@/pages/dashboard/subscriptions')) },
      { path: 'subscription', lazy: page(() => import('@/pages/dashboard/subscription')) },
      { path: 'referrals', lazy: page(() => import('@/pages/dashboard/referrals')) },
      { path: 'wallet', lazy: page(() => import('@/pages/dashboard/wallet')) },
      { path: 'earnings', lazy: page(() => import('@/pages/dashboard/earnings')) },
      { path: 'users', lazy: page(() => import('@/pages/dashboard/users')) },
      { path: 'roles', lazy: page(() => import('@/pages/dashboard/roles')) },
      { path: '*', lazy: page(() => import('@/pages/not-found')) },
    ],
  },
])
