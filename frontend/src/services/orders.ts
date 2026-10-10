import { api, API_URL } from '@/lib/api'
import { isoDate } from '@/lib/format'
import type { Order, OrderRequest } from '@/types/order'

export async function createOrder(body: OrderRequest): Promise<Order> {
  if (API_URL) return api<Order>('/orders', { method: 'POST', body: JSON.stringify(body) })
  // Demo: the order joins the in-memory list the dashboard reads, waiting for an admin to approve it.
  const [{ demoProducts }, { useOrders }] = await Promise.all([import('./products.demo'), import('./orders.demo')])
  const { items: ids, ...details } = body
  const items = demoProducts
    .filter((product) => ids.includes(product.id))
    .map(({ title, seller, type, price }) => ({ title, seller: seller.name, type, price }))
  const reference = `MZ-${Date.now().toString(36).toUpperCase()}`
  useOrders.add({ ...details, reference, date: isoDate(), approved: false, items })
  return { reference, total: items.reduce((sum, line) => sum + line.price, 0) }
}
