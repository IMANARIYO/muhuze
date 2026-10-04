import { useState, type ComponentProps } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { phoneField } from '@/lib/phone'
import type { DeliveryDetails } from '@/types/order'
import { provinces } from '../_data'

interface Props {
  /** Known when the buyer is signed in. */
  defaultName?: string
  pending: boolean
  onSubmit: (details: DeliveryDetails) => void
}

function Field({ label, hint, ...props }: ComponentProps<typeof Input> & { label: string; hint?: string }) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={props.name}>{label}</Label>
      <Input id={props.name} required className="h-10" {...props} />
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

function Select({ label, name, options, ...props }: ComponentProps<typeof NativeSelect> & { label: string; options: string[] }) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={name}>{label}</Label>
      <NativeSelect id={name} name={name} required className="w-full [&_select]:h-10" {...props}>
        <NativeSelectOption value="">Choose…</NativeSelectOption>
        {options.map((option) => <NativeSelectOption key={option}>{option}</NativeSelectOption>)}
      </NativeSelect>
    </div>
  )
}

export function DeliveryForm({ defaultName, pending, onSubmit }: Props) {
  const [province, setProvince] = useState('')

  return (
    <form
      className="grid gap-8 rounded-2xl border bg-card p-6"
      onSubmit={(event) => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        const text = (name: keyof DeliveryDetails) => String(data.get(name) ?? '').trim()
        onSubmit({
          name: text('name'), phone: text('phone'), province: text('province'), district: text('district'),
          sector: text('sector'), cell: text('cell'), paymentPhone: text('paymentPhone'),
        })
      }}
    >
      <fieldset className="grid gap-4 sm:grid-cols-2">
        <legend className="mb-4 font-heading text-lg font-semibold">Who is receiving it?</legend>
        <Field label="Full name" name="name" autoComplete="name" defaultValue={defaultName} />
        <Field label="Phone number" name="phone" autoComplete="tel" {...phoneField} />
      </fieldset>

      <fieldset className="grid gap-4 sm:grid-cols-2">
        <legend className="mb-4 font-heading text-lg font-semibold">Where should it be delivered?</legend>
        <Select label="Province" name="province" options={Object.keys(provinces)} value={province} onChange={(event) => setProvince(event.target.value)} />
        <Select key={province} label="District" name="district" options={provinces[province] ?? []} disabled={!province} />
        <Field label="Sector" name="sector" />
        <Field label="Cell" name="cell" />
      </fieldset>

      <fieldset className="grid gap-4">
        <legend className="mb-4 font-heading text-lg font-semibold">Which number will you pay from?</legend>
        <Field
          label="Mobile money number"
          name="paymentPhone"
          hint="You send the money yourself, outside Muhuze. We use this number to match your payment to the order."
          {...phoneField}
        />
      </fieldset>

      <Button type="submit" size="lg" disabled={pending} className="h-12 rounded-full text-base shadow-lg shadow-primary/30">
        {pending ? 'Placing order…' : 'Complete order'}
      </Button>
    </form>
  )
}
