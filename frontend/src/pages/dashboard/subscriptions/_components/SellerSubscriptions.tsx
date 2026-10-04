import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { formatDate, formatPrice, isoDate, typeLabels } from '@/lib/format'
import { DataTable, type Column } from '../../_components/DataTable'
import { FormDialog, SelectField } from '../../_components/FormDialog'
import { StatusBadge } from '../../_components/StatusBadge'
import { isPaid, usePlans, useSubscriptions, type StoredSubscription } from '../_data'

export function SellerSubscriptions() {
  const { items, update } = useSubscriptions()
  const { items: plans } = usePlans()
  const [paying, setPaying] = useState<StoredSubscription | null>(null)
  const offered = plans.filter((plan) => plan.active)

  const columns: Column<StoredSubscription>[] = [
    { header: 'Seller', cell: (row) => <span className="font-medium">{row.seller}</span> },
    { header: 'Sells', cell: (row) => typeLabels[row.sells].name },
    {
      header: 'Subscription required',
      cell: (row) => (
        <Switch
          checked={row.required}
          aria-label={`Require a subscription from ${row.seller}`}
          onCheckedChange={(required) => update(row.id, { required })}
        />
      ),
    },
    {
      header: 'Status',
      cell: (row) => {
        if (row.requested) return <StatusBadge tone="warning">{row.requested.plan} requested · pays from {row.requested.paymentPhone}</StatusBadge>
        if (!row.required) return <StatusBadge tone="neutral">Exempt</StatusBadge>
        return isPaid(row)
          ? <StatusBadge tone="success">Active</StatusBadge>
          : <StatusBadge tone="danger">Unpaid · contact hidden</StatusBadge>
      },
    },
    { header: 'Plan', cell: (row) => row.plan ?? '—' },
    { header: 'Paid until', cell: (row) => (row.paidUntil ? formatDate(row.paidUntil) : '—') },
    {
      header: '',
      className: 'text-right',
      cell: (row) => (row.required || row.requested) && (
        <Button variant="outline" size="sm" onClick={() => setPaying(row)}>
          {isPaid(row) ? 'Renew' : 'Record payment'}
        </Button>
      ),
    },
  ]

  return (
    <section className="space-y-3">
      <h2 className="font-heading text-lg font-semibold">Sellers</h2>
      <DataTable rows={items} columns={columns} search={(row) => row.seller} />
      <FormDialog
        open={paying !== null}
        onClose={() => setPaying(null)}
        title={`Record payment for ${paying?.seller}`}
        description="Money is received outside the app. Saving shows the seller's contact to buyers again."
        onSubmit={(data) => {
          const plan = offered.find((item) => item.name === data.get('plan'))
          if (!paying || !plan) return
          update(paying.id, { plan: plan.name, paidUntil: isoDate(plan.days), requested: undefined })
          toast.success(`${paying.seller} is subscribed until ${formatDate(isoDate(plan.days))}`)
        }}
      >
        <SelectField
          label="Plan"
          name="plan"
          defaultValue={paying?.requested?.plan ?? paying?.plan ?? undefined}
          options={offered.map((plan) => ({ value: plan.name, label: `${plan.name} · ${formatPrice(plan.amount)} / ${plan.days} days` }))}
        />
      </FormDialog>
    </section>
  )
}
