import { useMutation } from '@tanstack/react-query'
import { Navigate } from 'react-router'
import { toast } from 'sonner'
import { useCart } from '@/hooks/use-cart'
import { useProducts } from '@/hooks/use-products'
import { useSession } from '@/hooks/use-session'
import { createOrder } from '@/services/orders'
import { DeliveryForm } from './_components/DeliveryForm'
import { OrderPlaced } from './_components/OrderPlaced'
import { OrderSummary } from './_components/OrderSummary'

export default function Checkout() {
  const { ids, clear } = useCart()
  const { user } = useSession()
  const { data: products } = useProducts()
  const order = useMutation({
    mutationFn: createOrder,
    onSuccess: () => clear(),
    onError: () => toast.error('Could not place the order. Please try again.'),
  })

  if (order.data && order.variables) return <OrderPlaced order={order.data} details={order.variables} />
  // The cart is emptied just before the order result arrives, so wait for it rather than leaving.
  if (ids.length === 0 && !order.isPending) return <Navigate to="/cart" replace />

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
      <h1 className="animate-rise font-heading text-3xl font-bold">Checkout</h1>
      <p className="mb-6 text-muted-foreground">Tell us where to deliver. No payment is taken here.</p>
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <DeliveryForm
          defaultName={user?.name}
          pending={order.isPending}
          onSubmit={(details) => order.mutate({ ...details, items: ids })}
        />
        <OrderSummary items={products?.filter((product) => ids.includes(product.id))} />
      </div>
    </main>
  )
}
