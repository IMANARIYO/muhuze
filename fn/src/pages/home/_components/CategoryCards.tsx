import { Link } from 'react-router'
import type { Product, ProductType } from '@/types/product'

const title: Record<ProductType, (category: string) => string> = {
  sale: (category) => `Shop ${category.toLowerCase()}`,
  rental: (category) => `Rent ${category.toLowerCase()}`,
  service: (category) => `${category} services`,
}

/** One tall picture card per category, in a row that scrolls sideways. */
export function CategoryCards({ products }: { products: Product[] }) {
  // The first listing of each category lends the card its picture.
  const cards = [...new Map(products.map((product) => [product.category, product])).values()]

  return (
    <section className="mx-auto max-w-7xl px-4 py-10">
      <div className="reveal -mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-2">
        {cards.map((product) => (
          <Link
            key={product.category}
            to={`/products?q=${encodeURIComponent(product.category)}`}
            className="relative h-96 w-64 shrink-0 snap-start overflow-hidden rounded-2xl bg-muted shadow-sm transition hover:shadow-xl hover:shadow-primary/10"
          >
            <img src={product.image} alt="" width={256} height={384} loading="lazy" className="size-full object-cover" />
            <div className="absolute inset-x-0 top-0 h-40 bg-linear-to-b from-black/70 to-transparent" />
            <h2 className="absolute inset-x-0 top-0 p-4 font-heading text-2xl leading-tight font-extrabold text-balance text-white">
              {title[product.type](product.category)}
            </h2>
          </Link>
        ))}
      </div>
    </section>
  )
}
