import { ClipboardList, Eye, Package, PiggyBank } from 'lucide-react'
import { formatCount, formatPrice } from '@/lib/format'
import type { Sale } from '@/services/orders.demo'
import type { StoredListing } from '../products/_data'
import { PageHeader } from './PageHeader'
import { SalesChart } from './SalesChart'
import { StatCard } from './StatCard'

const monthName = new Intl.DateTimeFormat('en', { month: 'short' })

interface Props {
  name: string
  /** The seller's approved sales and own listings. */
  sales: Sale[]
  listings: StoredListing[]
}

export function SellerOverview({ name, sales, listings }: Props) {
  const byMonth = new Map<string, number>()
  for (const sale of sales.toSorted((a, b) => a.date.localeCompare(b.date))) {
    const month = sale.date.slice(0, 7)
    byMonth.set(month, (byMonth.get(month) ?? 0) + sale.net)
  }
  const chart = [...byMonth].map(([month, earnings]) => ({ month: monthName.format(new Date(`${month}-01`)), earnings }))
  const top = listings.toSorted((a, b) => b.views - a.views).slice(0, 5)

  return (
    <>
      <PageHeader title={`Welcome back, ${name}`} description="How your shop is doing on Muhuze." />
      <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Earnings" value={formatPrice(sales.reduce((sum, sale) => sum + sale.net, 0))} hint="From approved orders" icon={PiggyBank} />
        <StatCard label="Items sold" value={String(sales.length)} hint="In approved orders" icon={ClipboardList} />
        <StatCard label="Live listings" value={String(listings.filter((row) => row.active).length)} hint={`${listings.length} in total`} icon={Package} />
        <StatCard label="Views" value={formatCount(listings.reduce((sum, row) => sum + row.views, 0))} hint="Across your listings" icon={Eye} />
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2"><SalesChart data={chart} /></div>
        <section className="rounded-2xl border bg-card p-5">
          <h2 className="mb-3 font-heading font-semibold">Your top listings</h2>
          {!top.length && <p className="text-sm text-muted-foreground">Add your first listing to see it here.</p>}
          <ul className="space-y-3">
            {top.map((row) => (
              <li key={row.id} className="flex items-center gap-3">
                <img src={row.image} alt="" loading="lazy" className="size-11 rounded-lg object-cover" />
                <p className="min-w-0 flex-1 truncate text-sm font-medium">{row.title}</p>
                <span className="text-sm text-muted-foreground tabular-nums">{formatCount(row.views)} views</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  )
}
