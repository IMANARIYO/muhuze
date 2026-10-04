import { createStore, type Stored } from '@/lib/demo-store'
import { demoProducts } from '@/services/products.demo'
import type { ProductType } from '@/types/product'

interface Listing {
  title: string
  type: ProductType
  category: string
  price: number
  unit?: string
  image: string
  seller: string
  views: number
  uses: number
  active: boolean
}

export type StoredListing = Stored<Listing>

export const useListings = createStore<Listing>(
  demoProducts.map(({ title, type, category, price, unit, image, seller, views, uses }) => ({
    title, type, category, price, unit, image, views, uses, seller: seller.name, active: true,
  })),
)
