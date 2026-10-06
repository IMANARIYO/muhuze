export const productTypes = ['sale', 'rental', 'service'] as const
export type ProductType = (typeof productTypes)[number]

export const isProductType = (value: unknown): value is ProductType =>
  productTypes.some((type) => type === value)

export interface Product {
  id: number
  title: string
  type: ProductType
  category: string
  /** Town or district where the listing is available. */
  location: string
  price: number
  /** Billing period for rentals and services, e.g. "month". */
  unit?: string
  image: string
  description: string
  views: number
  /** Times bought, rented or booked. */
  uses: number
  seller: {
    name: string
    /** null while the seller's required subscription is unpaid. */
    contact: string | null
  }
}

export interface ProductFilters {
  type?: ProductType
  q?: string
  location?: string
  /** Shop name: only this seller's listings. */
  seller?: string
}
