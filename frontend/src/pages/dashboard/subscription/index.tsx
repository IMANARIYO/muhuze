import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useSession } from '@/hooks/use-session'
import { formatDate, formatPrice } from '@/lib/format'
import { phoneField } from '@/lib/phone'
import { Field, FormDialog } from '../_components/FormDialog'
import { PageHeader } from '../_components/PageHeader'
import { StatusBadge } from '../_components/StatusBadge'
import { isPaid, usePlans, useSubscriptions, type StoredPlan } from '../subscriptions/_data'

export default function DashboardSubscription() {
  const { user } = useSession()
  const { items: subscriptions, update } = useSubscriptions()
  const { items: plans } = usePlans()
  const [choosing, setChoosing] = useState<StoredPlan | null>(null)
  const mine = subscriptions.find((row) => row.seller === user?.shop)

  if (!mine) {
    return <PageHeader title="My subscription" description="Your shop is not set up for subscriptions yet. Please contact Muhuze." />
  }

  const paid = isPaid(mine)
  const steps = [
    `Send ${choosing ? formatPrice(choosing.amount) : ''} to the Muhuze account, outside the app.`,
    'Enter the number you paid from below and send the request.',
    'Muhuze confirms the payment and your plan starts.',
  ]

  return (
    <>
      <PageHeader title="My subscription" description="A paid plan keeps your contact visible to buyers." />
      <section className="flex flex-wrap items-center gap-3 rounded-2xl border bg-card p-5">
        {!mine.required && <StatusBadge tone="neutral">Not required for your shop</StatusBadge>}
        {mine.required && paid && <StatusBadge tone="success">Active · {mine.plan} until {mine.paidUntil && formatDate(mine.paidUntil)}</StatusBadge>}
        {mine.required && !paid && <StatusBadge tone="danger">Unpaid · your contact is hidden from buyers</StatusBadge>}
        {mine.requested && (
          <StatusBadge tone="warning">{mine.requested.plan} requested · waiting for Muhuze to confirm your payment</StatusBadge>
        )}
      </section>

      <h2 className="font-heading text-lg font-semibold">Muhuze plans</h2>
      <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {plans.filter((plan) => plan.active).map((plan) => (
          <article key={plan.id} className="flex flex-col rounded-2xl border bg-card p-5 transition hover:shadow-lg hover:shadow-primary/10">
            <h3 className="font-medium">{plan.name}</h3>
            <p className="mt-3 font-heading text-2xl font-bold text-primary">{formatPrice(plan.amount)}</p>
            <p className="mb-4 text-sm text-muted-foreground">for {plan.days} days</p>
            <Button className="mt-auto" variant={mine.plan === plan.name && paid ? 'outline' : 'default'} onClick={() => setChoosing(plan)}>
              {mine.plan === plan.name && paid ? 'Renew' : 'Subscribe'}
            </Button>
          </article>
        ))}
      </div>

      <FormDialog
        open={choosing !== null}
        onClose={() => setChoosing(null)}
        title={`Subscribe to ${choosing?.name}`}
        description="Payment is made outside the app."
        onSubmit={(data) => {
          if (!choosing) return
          update(mine.id, { requested: { plan: choosing.name, paymentPhone: String(data.get('paymentPhone')) } })
          toast.success('Request sent. Your plan starts when Muhuze confirms the payment.')
        }}
      >
        <ol className="list-decimal space-y-1.5 pl-5 text-sm text-muted-foreground">
          {steps.map((step) => <li key={step}>{step}</li>)}
        </ol>
        <Field label="Number you paid from" name="paymentPhone" required {...phoneField} />
      </FormDialog>
    </>
  )
}
