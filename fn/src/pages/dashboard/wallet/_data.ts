import { createStore, type Stored } from '@/lib/demo-store'

export const kinds = {
  commission: 'Sale commission',
  subscription: 'Subscription',
  referral: 'Referral payout',
  settlement: 'Settlement',
}

interface Transaction {
  date: string
  description: string
  kind: keyof typeof kinds
  /** Positive is money in, negative is money out. */
  amount: number
  pending: boolean
}

export type StoredTransaction = Stored<Transaction>

export const useTransactions = createStore<Transaction>([
  { date: '2026-09-29', description: 'Smartphone 128GB sold by Kigali Mobile', kind: 'commission', amount: 50_400, pending: true },
  { date: '2026-09-27', description: 'Urban Stay · Quarterly plan', kind: 'subscription', amount: 25_000, pending: false },
  { date: '2026-09-25', description: 'Paid out to bank account', kind: 'settlement', amount: -300_000, pending: false },
  { date: '2026-09-22', description: 'Ultrabook laptop sold by Kigali Mobile', kind: 'commission', amount: 106_800, pending: false },
  { date: '2026-09-20', description: 'Referral reward to Aline Uwase', kind: 'referral', amount: -12_600, pending: false },
  { date: '2026-09-18', description: 'DriveNow · Monthly plan', kind: 'subscription', amount: 10_000, pending: false },
  { date: '2026-09-15', description: 'Running sneakers sold by Stride Store', kind: 'commission', amount: 6_480, pending: false },
  { date: '2026-09-11', description: 'Chef Aline · Weekly plan', kind: 'subscription', amount: 3_000, pending: true },
  { date: '2026-09-08', description: 'Wireless headphones sold by Kigali Mobile', kind: 'commission', amount: 11_400, pending: false },
  { date: '2026-09-02', description: 'Instant film camera sold by Lens & Co', kind: 'commission', amount: 15_600, pending: false },
  { date: '2026-08-30', description: 'TechPoint · Monthly plan', kind: 'subscription', amount: 10_000, pending: false },
  { date: '2026-08-24', description: 'Carried over from August', kind: 'commission', amount: 742_000, pending: false },
])
