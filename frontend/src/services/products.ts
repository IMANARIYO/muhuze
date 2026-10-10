import { api, API_URL } from '@/lib/api'
import type { Product, ProductFilters } from '@/types/product'

const demo = async () => (await import('./products.demo')).demoProducts

export async function getProducts({ type, q, location, seller }: ProductFilters = {}): Promise<Product[]> {
  if (API_URL) {
    const params = new URLSearchParams({ ...(type && { type }), ...(q && { q }), ...(location && { location }), ...(seller && { seller }) })
    return api<Product[]>(`/products?${params}`)
  }
  const term = q?.toLowerCase() ?? ''
  const place = location?.toLowerCase() ?? ''
  return (await demo()).filter(
    (p) => (!type || p.type === type)
      && `${p.title} ${p.category}`.toLowerCase().includes(term)
      && p.location.toLowerCase().includes(place)
      && (!seller || p.seller.name === seller),
  )
}

/** Names of the shops that have listings, for the header filter. */
export async function getShops(): Promise<string[]> {
  if (API_URL) return api<string[]>('/shops')
  return [...new Set((await demo()).map((p) => p.seller.name))].sort()
}

export async function getProduct(id: number): Promise<Product> {
  if (API_URL) return api<Product>(`/products/${id}`)
  const product = (await demo()).find((p) => p.id === id)
  if (!product) throw new Error('Product not found')
  return product
}
