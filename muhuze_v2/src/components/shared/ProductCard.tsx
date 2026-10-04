import { Eye, TrendingUp } from 'lucide-react'
import { Link } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { formatCount, formatPrice, typeLabels } from '@/lib/format'
import type { Product } from '@/types/product'
import { WishlistButton } from './WishlistButton'

export function ProductCard({ product }: { product: Product }) {
  const labels = typeLabels[product.type]

  return (
    <Link
      to={`/products/${product.id}`}
      className="group relative flex flex-col overflow-hidden rounded-2xl border bg-card transition duration-300 hover:-translate-y-1.5 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10"
    >
      <div className="relative aspect-square overflow-hidden bg-muted">
        <img
          src={product.image}
          alt={product.title}
          width={640}
          height={640}
          loading="lazy"
          className="size-full object-cover transition duration-500 group-hover:scale-110"
        />
        <Badge className="absolute top-3 left-3">{labels.name}</Badge>
        <WishlistButton id={product.id} className="absolute top-3 right-3" />
      </div>
      <div className="flex flex-1 flex-col gap-1 p-4">
        <p className="text-xs text-muted-foreground">{product.category} · {product.seller.name}</p>
        <h3 className="line-clamp-1 font-medium">{product.title}</h3>
        <p className="font-heading text-lg font-bold text-primary">
          {formatPrice(product.price)}
          {product.unit && <span className="text-xs font-normal text-muted-foreground"> / {product.unit}</span>}
        </p>
        <div className="mt-auto flex items-center gap-4 pt-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Eye className="size-3.5" />{formatCount(product.views)}</span>
          <span className="flex items-center gap-1">
            <TrendingUp className="size-3.5" />{formatCount(product.uses)} {labels.used}
          </span>
        </div>
      </div>
    </Link>
  )
}
