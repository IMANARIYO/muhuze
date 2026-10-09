import { useQuery } from '@tanstack/react-query'
import { Eye, MapPin, TrendingUp } from 'lucide-react'
import { useParams } from 'react-router'
import { CartButton } from '@/components/shared/CartButton'
import { WishlistButton } from '@/components/shared/WishlistButton'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCount, formatPrice, typeLabels } from '@/lib/format'
import NotFound from '@/pages/not-found'
import { getProduct } from '@/services/products'
import { SellerCard } from './_components/SellerCard'

export default function ProductDetail() {
  const id = Number(useParams().id)
  const { data: product, isError } = useQuery({
    queryKey: ['product', id],
    queryFn: () => getProduct(id),
    retry: false,
  })

  if (isError) return <NotFound />
  if (!product) {
    return (
      <main className="mx-auto grid w-full max-w-6xl flex-1 gap-8 px-4 py-8 md:grid-cols-2">
        <Skeleton className="aspect-square rounded-3xl" />
        <Skeleton className="h-80 rounded-3xl" />
      </main>
    )
  }

  const labels = typeLabels[product.type]

  return (
    <main className="mx-auto grid w-full max-w-6xl flex-1 gap-8 px-4 py-8 md:grid-cols-2">
      <div className="relative animate-rise self-start overflow-hidden rounded-3xl border bg-muted">
        <img src={product.image} alt={product.title} width={640} height={640} className="aspect-square w-full object-cover" />
        <WishlistButton id={product.id} className="absolute top-4 right-4 size-11" />
      </div>
      <div className="flex animate-rise flex-col gap-5 [animation-delay:120ms]">
        <div className="flex gap-2">
          <Badge>{labels.name}</Badge>
          <Badge variant="secondary">{product.category}</Badge>
        </div>
        <h1 className="font-heading text-3xl font-bold md:text-4xl">{product.title}</h1>
        <p className="font-heading text-3xl font-extrabold text-primary">
          {formatPrice(product.price)}
          {product.unit && <span className="text-base font-normal text-muted-foreground"> / {product.unit}</span>}
        </p>
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5"><MapPin className="size-4" />{product.location}</span>
          <span className="flex items-center gap-1.5"><Eye className="size-4" />{formatCount(product.views)} views</span>
          <span className="flex items-center gap-1.5">
            <TrendingUp className="size-4" />{formatCount(product.uses)} {labels.used}
          </span>
        </div>
        <p className="leading-relaxed text-muted-foreground">{product.description}</p>
        <SellerCard seller={product.seller} />
        <CartButton product={product} className="h-12 text-base shadow-lg shadow-primary/30" />
      </div>
    </main>
  )
}
