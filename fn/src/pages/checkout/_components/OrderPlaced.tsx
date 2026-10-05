import { CircleCheck } from 'lucide-react'
import { Link } from 'react-router'
import { buttonVariants } from '@/components/ui/button'
import { formatPrice } from '@/lib/format'
import type { DeliveryDetails, Order } from '@/types/order'

export function OrderPlaced({ order, details }: { order: Order; details: DeliveryDetails }) {
  const steps = [
    <>Send <strong>{formatPrice(order.total)}</strong> from <strong>{details.paymentPhone}</strong>. Payment happens outside Muhuze.</>,
    <>We match the payment to order <strong>{order.reference}</strong> using that number.</>,
    <>The seller calls <strong>{details.phone}</strong> and delivers to {details.cell}, {details.sector}, {details.district}.</>,
  ]

  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-16 text-center">
      <CircleCheck className="mx-auto size-16 animate-rise text-primary" />
      <h1 className="mt-4 font-heading text-3xl font-bold">Order received</h1>
      <p className="mt-2 text-muted-foreground">Thank you, {details.name}. Keep this reference: <strong className="text-foreground">{order.reference}</strong></p>
      <ol className="stagger mt-8 space-y-3 text-left">
        {steps.map((step, index) => (
          <li key={index} className="flex gap-3 rounded-2xl border bg-card p-4 text-sm">
            <span className="grid size-6 shrink-0 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{index + 1}</span>
            <p>{step}</p>
          </li>
        ))}
      </ol>
      <Link to="/products" className={buttonVariants({ size: 'lg', className: 'mt-8 h-12 rounded-full px-8 text-base' })}>
        Continue shopping
      </Link>
    </main>
  )
}
