import { ArrowLeft, ArrowRight } from 'lucide-react'
import { useRef } from 'react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { formatCount } from '@/lib/format'
import type { Product } from '@/types/product'

/** The most sold products as round pictures in a row, with arrows to move through it. */
export function BestSellers({ products }: { products: Product[] }) {
  const row = useRef<HTMLUListElement>(null)
  const sold = products.filter((product) => product.type === 'sale').toSorted((a, b) => b.uses - a.uses)
  const move = (direction: 1 | -1) =>
    row.current?.scrollBy({ left: direction * row.current.clientWidth * 0.8, behavior: 'smooth' })

  if (!sold.length) return null

  return (
    <section className="reveal  py-10 text-white">
      <h2 className="mb-6 text-center text-xs tracking-[0.2em] text-white/60 uppercase">Most sold on Muhuze</h2>
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-4">
        <Button variant="ghost" size="icon-lg" aria-label="Previous products" className="hidden shrink-0 rounded-full hover:bg-white/15 hover:text-white sm:inline-flex" onClick={() => move(-1)}>
          <ArrowLeft />
        </Button>
        <ul ref={row} className="flex flex-1 snap-x gap-6 overflow-x-auto [scrollbar-width:none]">
          {sold.map((product) => (
            <li key={product.id} className="w-36 shrink-0 snap-start text-center md:w-44">
              <Link to={`/products/${product.id}`} className="group block">
                <img
                  src={product.image}
                  alt=""
                  width={176}
                  height={176}
                  loading="lazy"
                  className="aspect-square w-full rounded-full bg-card object-cover shadow-sm"
                />
                <p className="mt-4 truncate text-sm font-medium group-hover:underline">{product.title}</p>
                <p className="text-xs text-white/60">{formatCount(product.uses)} sold</p>
              </Link>
            </li>
          ))}
        </ul>
        <Button variant="ghost" size="icon-lg" aria-label="Next products" className="hidden shrink-0 rounded-full hover:bg-white/15 hover:text-white sm:inline-flex" onClick={() => move(1)}>
          <ArrowRight />
        </Button>
      </div>
    </section>
  )
}
