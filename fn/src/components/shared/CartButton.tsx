import { Check, ShoppingCart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCart } from '@/hooks/use-cart'
import { typeLabels } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Product } from '@/types/product'

/** Adds the listing to the cart; disabled while the seller cannot be reached. */
export function CartButton({ product, className }: { product: Pick<Product, 'id' | 'type' | 'seller'>; className?: string }) {
  const { ids, toggle } = useCart()
  const added = ids.includes(product.id)

  return (
    <Button
      variant={added ? 'secondary' : 'default'}
      disabled={!product.seller.contact}
      aria-pressed={added}
      className={cn('rounded-full transition active:scale-95', className)}
      onClick={(event) => {
        event.preventDefault()
        toggle(product.id)
      }}
    >
      {added ? <Check /> : <ShoppingCart />} {added ? 'In cart' : typeLabels[product.type].action}
    </Button>
  )
}
