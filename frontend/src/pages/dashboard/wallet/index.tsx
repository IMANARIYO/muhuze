import { ArrowDownLeft, ArrowUpRight, Banknote, Clock, Info, Wallet } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { formatDate, formatPrice, isoDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import { DataTable, type Column } from '../_components/DataTable'
import { Field, FormDialog } from '../_components/FormDialog'
import { PageHeader } from '../_components/PageHeader'
import { StatCard } from '../_components/StatCard'
import { StatusBadge } from '../_components/StatusBadge'
import { kinds, useTransactions, type StoredTransaction } from './_data'

const sum = (rows: StoredTransaction[]) => rows.reduce((total, row) => total + row.amount, 0)

export default function DashboardWallet() {
  const { items, add, update } = useTransactions()
  const [settling, setSettling] = useState(false)
  const balance = sum(items.filter((row) => !row.pending))
  const pending = sum(items.filter((row) => row.pending))
  const settled = -sum(items.filter((row) => row.kind === 'settlement'))

  const columns: Column<StoredTransaction>[] = [
    {
      header: 'Transaction',
      cell: (row) => (
        <div className="flex items-center gap-3">
          <span className={cn('grid size-9 shrink-0 place-items-center rounded-full', row.amount > 0 ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground')}>
            {row.amount > 0 ? <ArrowDownLeft className="size-4" /> : <ArrowUpRight className="size-4" />}
          </span>
          <div>
            <p className="font-medium">{row.description}</p>
            <p className="text-xs text-muted-foreground">{kinds[row.kind]}</p>
          </div>
        </div>
      ),
    },
    { header: 'Date', cell: (row) => formatDate(row.date) },
    {
      header: 'Status',
      cell: (row) => <StatusBadge tone={row.pending ? 'warning' : 'success'}>{row.pending ? 'Pending' : 'Completed'}</StatusBadge>,
    },
    {
      header: 'Amount',
      className: 'text-right',
      cell: (row) => (
        <span className={cn('font-medium tabular-nums', row.amount > 0 && 'text-primary')}>
          {row.amount > 0 && '+'}{formatPrice(row.amount)}
        </span>
      ),
    },
    {
      header: '',
      className: 'text-right',
      cell: (row) => row.pending && (
        <Button variant="outline" size="sm" onClick={() => { update(row.id, { pending: false }); toast.success('Marked as received') }}>
          Confirm
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Wallet" description="A record of what the platform earned and what was paid out.">
        <Button onClick={() => setSettling(true)}><Banknote /> Record settlement</Button>
      </PageHeader>
      <p className="flex items-start gap-2 rounded-xl border border-highlight/50 bg-highlight/15 p-3 text-sm">
        <Info className="mt-0.5 size-4 shrink-0" />
        Balances are records only. Real money moves outside the app; record each payout here to keep the numbers right.
      </p>
      <div className="stagger grid gap-4 sm:grid-cols-3">
        <StatCard label="Available balance" value={formatPrice(balance)} hint="Confirmed and not yet paid out" icon={Wallet} />
        <StatCard label="Pending" value={formatPrice(pending)} hint="Waiting for confirmation" icon={Clock} />
        <StatCard label="Settled" value={formatPrice(settled)} hint="Paid out outside the app" icon={Banknote} />
      </div>
      <DataTable rows={items} columns={columns} search={(row) => `${row.description} ${kinds[row.kind]}`} />
      <FormDialog
        open={settling}
        onClose={() => setSettling(false)}
        title="Record settlement"
        description={`Enter money you already transferred outside the app. Available: ${formatPrice(balance)}.`}
        onSubmit={(data) => {
          add({
            date: isoDate(),
            description: String(data.get('note')),
            kind: 'settlement',
            amount: -Number(data.get('amount')),
            pending: false,
          })
          toast.success('Settlement recorded')
        }}
      >
        <Field label="Amount (RWF)" name="amount" type="number" min={1} max={balance} required />
        <Field label="Note" name="note" placeholder="Paid out to bank account" required />
      </FormDialog>
    </>
  )
}
