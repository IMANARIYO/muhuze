import { Percent } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Field } from '../../_components/FormDialog'
import { useRates } from '../../_data'

export function RatesCard() {
  const { items: [rates], update } = useRates()

  return (
    <form
      className="flex flex-wrap items-end gap-4 rounded-2xl border bg-card p-5"
      action={(data) => {
        update(rates.id, { commission: Number(data.get('commission')), referral: Number(data.get('referral')) })
        toast.success('Rates saved')
      }}
    >
      <div className="flex min-w-56 flex-1 items-center gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-highlight/25 text-highlight-foreground dark:text-highlight">
          <Percent className="size-5" />
        </span>
        <div>
          <h2 className="font-heading font-semibold">Platform rates</h2>
          <p className="text-sm text-muted-foreground">Taken from each sale, and paid to referrers.</p>
        </div>
      </div>
      <Field label="Sale commission %" name="commission" type="number" min={0} max={100} step="0.5" defaultValue={rates.commission} className="w-36" required />
      <Field label="Referral commission %" name="referral" type="number" min={0} max={100} step="0.5" defaultValue={rates.referral} className="w-36" required />
      <Button type="submit">Save rates</Button>
    </form>
  )
}
