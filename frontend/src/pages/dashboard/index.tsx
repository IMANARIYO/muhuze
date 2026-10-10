import { ArrowRight, CreditCard, Package, Users, Wallet } from 'lucide-react'
import { Link } from 'react-router'
import { useSession } from '@/hooks/use-session'
import { formatCount, formatDate, formatPrice } from '@/lib/format'
import { salesOf, useOrders } from '@/services/orders.demo'
import { cn } from '@/lib/utils'
import { PageHeader } from './_components/PageHeader'
import { RevenueChart } from './_components/RevenueChart'
import { SellerOverview } from './_components/SellerOverview'
import { StatCard } from './_components/StatCard'
import { useRates } from './_data'
import { useListings } from './products/_data'
import { isPaid, useSubscriptions } from './subscriptions/_data'
import { useUsers } from './users/_data'
import { useTransactions } from './wallet/_data'

const panel = 'rounded-2xl border bg-card p-5'
const panelLink = 'flex items-center gap-1 text-sm font-medium text-primary hover:underline'

export default function DashboardHome() {
  const { user, can } = useSession()
  const { items: orders } = useOrders()
  const { items: [rates] } = useRates()
  const { items: listings } = useListings()
  const { items: transactions } = useTransactions()
  const { items: subscriptions } = useSubscriptions()
  const { items: users } = useUsers()

  if (!user) return null
  // Without `order.manage` the user runs a shop, not the platform.
  if (!can('order.manage')) {
    return (
      <SellerOverview
        name={user.name}
        sales={salesOf(orders, user.shop, rates.commission)}
        listings={listings.filter((row) => row.seller === user.shop)}
      />
    )
  }

  const waiting = orders.filter((row) => !row.approved).length
  const balance = transactions.filter((row) => !row.pending).reduce((total, row) => total + row.amount, 0)
  const required = subscriptions.filter((row) => row.required)
  const top = listings.toSorted((a, b) => b.views - a.views).slice(0, 5)

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.name}`}
        description={waiting ? `${waiting} ${waiting === 1 ? 'order is' : 'orders are'} waiting for you to confirm payment.` : 'Here is what is happening on Muhuze today.'}
      />
      <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Wallet balance" value={formatPrice(balance)} hint="Confirmed earnings" icon={Wallet} />
        <StatCard label="Live listings" value={String(listings.filter((row) => row.active).length)} hint={`${listings.length} in total`} icon={Package} />
        <StatCard label="Paid subscriptions" value={`${required.filter(isPaid).length} / ${required.length}`} hint="Of sellers required to subscribe" icon={CreditCard} />
        <StatCard label="Users" value={String(users.length)} hint={`${users.filter((row) => row.suspended).length} suspended`} icon={Users} />
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2"><RevenueChart /></div>
        <section className={panel}>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-heading font-semibold">Top listings</h2>
            <Link to="/dashboard/products" className={panelLink}>All <ArrowRight className="size-4" /></Link>
          </div>
          <ul className="space-y-3">
            {top.map((row) => (
              <li key={row.id} className="flex items-center gap-3">
                <img src={row.image} alt="" loading="lazy" className="size-11 rounded-lg object-cover" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{row.title}</p>
                  <p className="text-xs text-muted-foreground">{row.seller}</p>
                </div>
                <span className="text-sm text-muted-foreground tabular-nums">{formatCount(row.views)} views</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
      <section className={panel}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-heading font-semibold">Recent transactions</h2>
          <Link to="/dashboard/wallet" className={panelLink}>Wallet <ArrowRight className="size-4" /></Link>
        </div>
        <ul className="divide-y">
          {transactions.slice(0, 5).map((row) => (
            <li key={row.id} className="flex items-center justify-between gap-4 py-2.5 text-sm">
              <div className="min-w-0">
                <p className="truncate font-medium">{row.description}</p>
                <p className="text-xs text-muted-foreground">{formatDate(row.date)}</p>
              </div>
              <span className={cn('font-medium tabular-nums', row.amount > 0 && 'text-primary')}>
                {row.amount > 0 && '+'}{formatPrice(row.amount)}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
