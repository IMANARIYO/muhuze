import type { ProductType } from '@/types/product'

const money = new Intl.NumberFormat('en-RW', { style: 'currency', currency: 'RWF', maximumFractionDigits: 0 })
const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
const date = new Intl.DateTimeFormat('en', { dateStyle: 'medium' })

export const formatPrice = (value: number) => money.format(value)
export const formatCount = (value: number) => compact.format(value)
export const formatDate = (iso: string) => date.format(new Date(iso))

/** ISO date (YYYY-MM-DD) a number of days from now. */
export const isoDate = (daysFromNow = 0) =>
  new Date(Date.now() + daysFromNow * 86_400_000).toISOString().slice(0, 10)

export const typeLabels: Record<ProductType, { name: string; used: string; action: string }> = {
  sale: { name: 'For sale', used: 'sold', action: 'Buy now' },
  rental: { name: 'For rent', used: 'rented', action: 'Rent now' },
  service: { name: 'Service', used: 'booked', action: 'Book now' },
}
