import { ChevronRight, PackageSearch } from 'lucide-react'
import { Link } from 'react-router'
import { Skeleton } from '@/components/ui/skeleton'
import { formatPrice } from '@/lib/format'
import { productTypes, type Product, type ProductType } from '@/types/product'

const grid = 'grid gap-4 sm:grid-cols-2 xl:grid-cols-4'
const PANEL_SIZE = 4

const titles: Record<ProductType, string> = {
  sale: 'Top picks to buy',
  rental: 'Ready to rent',
  service: 'Services to book',
}

/** Splits the listings by type into panels of four, so every listing stays visible. */
function panels(products: Product[]) {
  return productTypes.flatMap((type) => {
    const items = products.filter((product) => product.type === type)
    return Array.from({ length: Math.ceil(items.length / PANEL_SIZE) }, (_, index) => ({
      type,
      title: index ? `More: ${titles[type].toLowerCase()}` : titles[type],
      items: items.slice(index * PANEL_SIZE, (index + 1) * PANEL_SIZE),
    }))
  })
}

/** Pass `undefined` while loading. */
export function ProductGrid({ products, empty }: { products?: Product[]; empty: string }) {
  if (!products) {
    return (
      <div className={grid}>
        {Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="aspect-4/5 rounded-2xl" />)}
      </div>
    )
  }

  if (!products.length) {
    return (
      <div className="grid place-items-center gap-3 rounded-2xl border border-dashed py-20 text-muted-foreground">
        <PackageSearch className="size-10" />
        <p>{empty}</p>
      </div>
    )
  }

  return (
    <div className={`${grid} stagger`}>
      {panels(products).map((panel) => (
        <section key={panel.title} className="rounded-2xl border bg-card p-4">
          <Link to={`/products?type=${panel.type}`} className="mb-3 flex items-center justify-between gap-2 hover:text-primary">
            <h3 className="font-heading text-lg leading-tight font-bold">{panel.title}</h3>
            <ChevronRight className="size-5 shrink-0" />
          </Link>
          <div className="grid grid-cols-2 gap-3">
            {panel.items.map((product) => (
              <Link key={product.id} to={`/products/${product.id}`} className="group min-w-0">
                <img
                  src={product.image}
                  alt=""
                  width={320}
                  height={320}
                  loading="lazy"
                  className="aspect-square w-full rounded-xl bg-muted object-cover"
                />
                <p className="mt-1.5 truncate text-sm group-hover:text-primary">{product.title}</p>
                <p className="text-sm font-semibold text-primary">{formatPrice(product.price)}</p>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
