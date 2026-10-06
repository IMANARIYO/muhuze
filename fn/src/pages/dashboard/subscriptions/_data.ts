import { createStore, type Stored } from '@/lib/demo-store'
import { isoDate } from '@/lib/format'
import type { ProductType } from '@/types/product'

interface Plan {
  name: string
  amount: number
  days: number
  active: boolean
}

interface SellerSubscription {
  seller: string
  sells: ProductType
  /** When true and unpaid, the seller's contact is hidden from buyers. */
  required: boolean
  plan: string | null
  paidUntil: string | null
  /** A plan the seller asked for and says they paid; cleared when an admin records the payment. */
  requested?: { plan: string; paymentPhone: string }
}

export type StoredPlan = Stored<Plan>
export type StoredSubscription = Stored<SellerSubscription>

export const usePlans = createStore<Plan>([
  { name: 'Weekly', amount: 3_000, days: 7, active: true },
  { name: 'Monthly', amount: 10_000, days: 30, active: true },
  { name: 'Quarterly', amount: 25_000, days: 90, active: true },
  { name: 'Yearly', amount: 90_000, days: 365, active: false },
])

export const useSubscriptions = createStore<SellerSubscription>([
  { seller: 'Prime Homes', sells: 'rental', required: true, plan: 'Monthly', paidUntil: isoDate(-6) },
  { seller: 'Urban Stay', sells: 'rental', required: true, plan: 'Quarterly', paidUntil: isoDate(54) },
  { seller: 'DriveNow', sells: 'rental', required: true, plan: 'Monthly', paidUntil: isoDate(12) },
  { seller: 'Fresh Cuts', sells: 'service', required: true, plan: null, paidUntil: null },
  { seller: 'Chef Aline', sells: 'service', required: true, plan: 'Weekly', paidUntil: isoDate(3) },
  { seller: 'CareerLift', sells: 'service', required: false, plan: null, paidUntil: null },
  { seller: 'Kigali Mobile', sells: 'sale', required: true, plan: null, paidUntil: null },
  { seller: 'TechPoint', sells: 'sale', required: true, plan: 'Monthly', paidUntil: isoDate(21) },
  { seller: 'SoundHub', sells: 'sale', required: false, plan: null, paidUntil: null },
])

const today = isoDate()

export const isPaid = (row: SellerSubscription) => row.paidUntil !== null && row.paidUntil >= today
