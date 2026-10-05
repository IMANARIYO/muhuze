import { Skeleton } from '@/components/ui/skeleton'
import { formatPrice } from '@/lib/format'
import type { Product } from '@/types/product'

/** Pass `undefined` while loading. */
export function OrderSummary({ items }: { items?: Product[] }) {
  if (!items) return <Skeleton className="h-64 rounded-2xl" />

  return (
    <aside className="self-start rounded-2xl border bg-card p-6 lg:sticky lg:top-40">
      <h2 className="font-heading text-lg font-semibold">Your order</h2>
      <ul className="mt-4 space-y-3">
        {items.map((product) => (
          <li key={product.id} className="flex items-center gap-3">
            <img src={product.image} alt="" width={48} height={48} loading="lazy" className="size-12 shrink-0 rounded-lg object-cover" />
            <p className="line-clamp-2 flex-1 text-sm">{product.title}</p>
            <p className="text-sm font-medium whitespace-nowrap">{formatPrice(product.price)}</p>
          </li>
        ))}
      </ul>
      <p className="mt-5 flex items-center justify-between border-t pt-4 text-muted-foreground">
        Total
        <span className="font-heading text-xl font-extrabold text-foreground">
          {formatPrice(items.reduce((sum, product) => sum + product.price, 0))}
        </span>
      </p>
    </aside>
  )
}
