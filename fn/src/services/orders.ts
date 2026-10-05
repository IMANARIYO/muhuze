import { api, API_URL } from '@/lib/api'
import type { Order, OrderRequest } from '@/types/order'

export async function createOrder(body: OrderRequest): Promise<Order> {
  if (API_URL) return api<Order>('/orders', { method: 'POST', body: JSON.stringify(body) })
  // Demo: nothing is saved, the order only gets a reference and a total.
  const { demoProducts } = await import('./products.demo')
  return {
    reference: `MZ-${Date.now().toString(36).toUpperCase()}`,
    total: demoProducts.filter((p) => body.items.includes(p.id)).reduce((sum, p) => sum + p.price, 0),
  }
}
