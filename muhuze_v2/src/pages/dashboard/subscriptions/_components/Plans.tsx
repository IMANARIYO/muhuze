import { Plus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { formatPrice } from '@/lib/format'
import { cn } from '@/lib/utils'
import { Field, FormDialog } from '../../_components/FormDialog'
import { RowActions } from '../../_components/RowActions'
import { usePlans, type StoredPlan } from '../_data'

export function Plans() {
  const { items, add, update, remove } = usePlans()
  const [target, setTarget] = useState<StoredPlan | 'new' | null>(null)
  const plan = target === 'new' ? null : target

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold">Plans</h2>
        <Button variant="outline" onClick={() => setTarget('new')}><Plus /> New plan</Button>
      </div>
      <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <article key={item.id} className={cn('rounded-2xl border bg-card p-5 transition hover:shadow-lg hover:shadow-primary/10', !item.active && 'opacity-60')}>
            <div className="flex items-center justify-between">
              <h3 className="font-medium">{item.name}</h3>
              <Switch
                checked={item.active}
                aria-label={`Offer the ${item.name} plan`}
                onCheckedChange={(active) => update(item.id, { active })}
              />
            </div>
            <p className="mt-3 font-heading text-2xl font-bold text-primary">{formatPrice(item.amount)}</p>
            <p className="text-sm text-muted-foreground">every {item.days} days</p>
            <div className="mt-3 border-t pt-2">
              <RowActions
                name={`${item.name} plan`}
                onEdit={() => setTarget(item)}
                onDelete={() => { remove(item.id); toast.success('Plan deleted') }}
              />
            </div>
          </article>
        ))}
      </div>
      <FormDialog
        open={target !== null}
        onClose={() => setTarget(null)}
        title={plan ? `Edit ${plan.name}` : 'New plan'}
        description="Set any amount and any duration."
        onSubmit={(data) => {
          const values = { name: String(data.get('name')), amount: Number(data.get('amount')), days: Number(data.get('days')) }
          if (plan) update(plan.id, values)
          else add({ ...values, active: true })
          toast.success(plan ? 'Plan updated' : 'Plan created')
        }}
      >
        <Field label="Plan name" name="name" defaultValue={plan?.name} required />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Amount (RWF)" name="amount" type="number" min={0} defaultValue={plan?.amount} required />
          <Field label="Duration (days)" name="days" type="number" min={1} defaultValue={plan?.days} required />
        </div>
      </FormDialog>
    </section>
  )
}
