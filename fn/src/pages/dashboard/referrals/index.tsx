import { Coins, Copy, Percent, UserPlus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { formatDate, formatPrice } from '@/lib/format'
import { DataTable, type Column } from '../_components/DataTable'
import { PageHeader } from '../_components/PageHeader'
import { StatCard } from '../_components/StatCard'
import { StatusBadge } from '../_components/StatusBadge'
import { useRates } from '../_data'

interface Referral {
  id: number
  name: string
  joinedAs: 'Buyer' | 'Seller'
  joined: string
  deals: number
  /** Total value of the transactions this person made. */
  volume: number
}

// Demo data until the referrals endpoint exists.
const link = 'https://muhuze.app/r/DEMO2026'
const referrals: Referral[] = [
  { id: 1, name: 'Sandrine Umutoni', joinedAs: 'Buyer', joined: '2026-05-02', deals: 6, volume: 1_240_000 },
  { id: 2, name: 'Claire Mukamana', joinedAs: 'Seller', joined: '2026-07-08', deals: 14, volume: 3_910_000 },
  { id: 3, name: 'Kevin Ishimwe', joinedAs: 'Buyer', joined: '2026-06-14', deals: 2, volume: 149_000 },
  { id: 4, name: 'Yves Ndayisaba', joinedAs: 'Buyer', joined: '2026-08-25', deals: 0, volume: 0 },
  { id: 5, name: 'Bella Gasana', joinedAs: 'Buyer', joined: '2026-09-11', deals: 1, volume: 95_000 },
]

export default function DashboardReferrals() {
  const { items: [rates] } = useRates()
  const earned = (volume: number) => (volume * rates.referral) / 100
  const total = referrals.reduce((sum, row) => sum + earned(row.volume), 0)

  const columns: Column<Referral>[] = [
    { header: 'Person', cell: (row) => <span className="font-medium">{row.name}</span> },
    { header: 'Joined as', cell: (row) => <StatusBadge tone={row.joinedAs === 'Seller' ? 'warning' : 'neutral'}>{row.joinedAs}</StatusBadge> },
    { header: 'Joined', cell: (row) => formatDate(row.joined) },
    { header: 'Deals', cell: (row) => row.deals },
    { header: 'Volume', cell: (row) => formatPrice(row.volume) },
    { header: 'You earned', className: 'text-right', cell: (row) => <span className="font-medium text-primary">{formatPrice(earned(row.volume))}</span> },
  ]

  return (
    <>
      <PageHeader title="Referrals" description="Share your link and earn each time the people you invite buy or sell." />
      <div className="relative overflow-hidden rounded-2xl bg-primary p-6 text-primary-foreground">
        <div className="absolute -top-16 -right-10 size-56 animate-blob rounded-full bg-highlight/40 blur-3xl" />
        <p className="relative font-heading text-lg font-semibold">Your referral link</p>
        <div className="relative mt-3 flex max-w-xl gap-2">
          <Input readOnly value={link} aria-label="Referral link" className="border-white/30 bg-white/15 text-primary-foreground" />
          <Button
            className="bg-highlight text-highlight-foreground hover:bg-highlight/90"
            onClick={async () => {
              await navigator.clipboard.writeText(link)
              toast.success('Link copied')
            }}
          >
            <Copy /> Copy
          </Button>
        </div>
      </div>
      <div className="stagger grid gap-4 sm:grid-cols-3">
        <StatCard label="People referred" value={String(referrals.length)} hint="Joined through your link" icon={UserPlus} />
        <StatCard label="Total earned" value={formatPrice(total)} hint="Across all their deals" icon={Coins} />
        <StatCard label="Your commission" value={`${rates.referral}%`} hint="Of every transaction they make" icon={Percent} />
      </div>
      <DataTable rows={referrals} columns={columns} search={(row) => row.name} />
    </>
  )
}
