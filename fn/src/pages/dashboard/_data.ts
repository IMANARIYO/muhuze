import { createStore } from '@/lib/demo-store'

// Demo data shared by several dashboard pages. Replace with API calls when the backend is connected.

/** Platform rates, in percent. Index 0 is the only row. */
export const useRates = createStore([{ commission: 12, referral: 3 }])

export const monthlyRevenue = [
  { month: 'Apr', commission: 412_000, subscription: 180_000 },
  { month: 'May', commission: 468_000, subscription: 215_000 },
  { month: 'Jun', commission: 531_000, subscription: 240_000 },
  { month: 'Jul', commission: 497_000, subscription: 290_000 },
  { month: 'Aug', commission: 624_000, subscription: 335_000 },
  { month: 'Sep', commission: 703_000, subscription: 380_000 },
]
