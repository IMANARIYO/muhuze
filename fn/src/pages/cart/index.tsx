import { ShoppingCart, Trash2 } from 'lucide-react'
import { Link } from 'react-router'
import { Button, buttonVariants } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useCart } from '@/hooks/use-cart'
import { useProducts } from '@/hooks/use-products'
import { formatPrice, typeLabels } from '@/lib/format'

export default function Cart() {
  const { ids, toggle } = useCart()
  const { data: products } = useProducts()
  const items = products?.filter((p) => ids.includes(p.id))

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
      <h1 className="mb-6 animate-rise font-heading text-3xl font-bold">My cart</h1>
      {!items && <Skeleton className="h-64 rounded-2xl" />}
      {items?.length === 0 && (
        <div className="grid place-items-center gap-3 rounded-2xl border border-dashed py-20 text-muted-foreground">
          <ShoppingCart className="size-10" />
          <p>Your cart is empty.</p>
          <Link to="/products" className={buttonVariants({ className: 'rounded-full' })}>Browse listings</Link>
        </div>
      )}
      {items && items.length > 0 && (
        <>
          <ul className="stagger divide-y rounded-2xl border bg-card">
            {items.map((product) => (
              <li key={product.id} className="flex items-center gap-4 p-4">
                <img src={product.image} alt="" width={80} height={80} loading="lazy" className="size-20 shrink-0 rounded-xl object-cover" />
                <div className="min-w-0 flex-1">
                  <Link to={`/products/${product.id}`} className="line-clamp-1 font-medium hover:text-primary">{product.title}</Link>
                  <p className="text-xs text-muted-foreground">{typeLabels[product.type].name} · {product.seller.name}</p>
                  <p className="mt-1 font-heading font-bold text-primary">
                    {formatPrice(product.price)}
                    {product.unit && <span className="text-xs font-normal text-muted-foreground"> / {product.unit}</span>}
                  </p>
                </div>
                <Button variant="ghost" size="icon" aria-label={`Remove ${product.title}`} onClick={() => toggle(product.id)}>
                  <Trash2 />
                </Button>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border bg-card p-5">
            <p className="text-muted-foreground">
              Total <span className="ml-2 font-heading text-2xl font-extrabold text-foreground">{formatPrice(items.reduce((sum, p) => sum + p.price, 0))}</span>
            </p>
            <Link to="/checkout" className={buttonVariants({ size: 'lg', className: 'h-12 rounded-full px-8 text-base' })}>
              Checkout
            </Link>
          </div>
        </>
      )}
    </main>
  )
}
