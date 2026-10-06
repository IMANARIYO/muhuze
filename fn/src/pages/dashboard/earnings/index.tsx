import { Info, Percent, PiggyBank, ShoppingBag } from 'lucide-react'
import { useSession } from '@/hooks/use-session'
import { formatDate, formatPrice } from '@/lib/format'
import { salesOf, useOrders, type Sale } from '@/services/orders.demo'
import { DataTable, type Column } from '../_components/DataTable'
import { PageHeader } from '../_components/PageHeader'
import { StatCard } from '../_components/StatCard'
import { useRates } from '../_data'

const columns: Column<Sale>[] = [
  {
    header: 'Sale',
    cell: (row) => (
      <div>
        <p className="font-medium">{row.title}</p>
        <p className="text-xs text-muted-foreground">{row.reference} · {row.buyer}</p>
      </div>
    ),
  },
  { header: 'Date', cell: (row) => formatDate(row.date) },
  { header: 'Price', cell: (row) => formatPrice(row.price) },
  { header: 'Muhuze commission', cell: (row) => (row.fee ? `−${formatPrice(row.fee)}` : '—') },
  { header: 'You receive', className: 'text-right', cell: (row) => <span className="font-medium text-primary">+{formatPrice(row.net)}</span> },
]

const total = (sales: Sale[], pick: (sale: Sale) => number) => formatPrice(sales.reduce((sum, sale) => sum + pick(sale), 0))

export default function DashboardEarnings() {
  const { user } = useSession()
  const { items } = useOrders()
  const { items: [rates] } = useRates()
  const sales = salesOf(items, user?.shop, rates.commission)

  return (
    <>
      <PageHeader title="My wallet" description="What you earned from orders Muhuze approved." />
      <p className="flex items-start gap-2 rounded-xl border border-highlight/50 bg-highlight/15 p-3 text-sm">
        <Info className="mt-0.5 size-4 shrink-0" />
        Balances are records only. Buyers pay Muhuze outside the app, and Muhuze pays you outside the app.
      </p>
      <div className="stagger grid gap-4 sm:grid-cols-3">
        <StatCard label="Balance" value={total(sales, (sale) => sale.net)} hint="From approved orders" icon={PiggyBank} />
        <StatCard label="Sold" value={total(sales, (sale) => sale.price)} hint={`${sales.length} items`} icon={ShoppingBag} />
        <StatCard label="Muhuze commission" value={total(sales, (sale) => sale.fee)} hint={`${rates.commission}% of each sale`} icon={Percent} />
      </div>
      <DataTable rows={sales} columns={columns} search={(row) => `${row.title} ${row.reference} ${row.buyer}`} />
    </>
  )
}
