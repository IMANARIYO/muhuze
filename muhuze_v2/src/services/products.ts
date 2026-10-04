import { api, API_URL } from '@/lib/api'
import type { Product, ProductFilters } from '@/types/product'

const demo = async () => (await import('./products.demo')).demoProducts

export async function getProducts({ type, q }: ProductFilters = {}): Promise<Product[]> {
  if (API_URL) {
    const params = new URLSearchParams({ ...(type && { type }), ...(q && { q }) })
    return api<Product[]>(`/products?${params}`)
  }
  const term = q?.toLowerCase() ?? ''
  return (await demo()).filter(
    (p) => (!type || p.type === type) && `${p.title} ${p.category}`.toLowerCase().includes(term),
  )
}

export async function getProduct(id: number): Promise<Product> {
  if (API_URL) return api<Product>(`/products/${id}`)
  const product = (await demo()).find((p) => p.id === id)
  if (!product) throw new Error('Product not found')
  return product
}
