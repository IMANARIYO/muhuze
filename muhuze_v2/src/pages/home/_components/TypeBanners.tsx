import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router'
import type { Product, ProductType } from '@/types/product'

const banners: { type: ProductType; title: string; text: string }[] = [
  { type: 'sale', title: 'Buy & sell', text: 'Phones, electronics and everyday goods' },
  { type: 'rental', title: 'Rent', text: 'Houses, apartments and cars' },
  { type: 'service', title: 'Services', text: 'Barbers, chefs, job help and more' },
]

export function TypeBanners({ products }: { products: Product[] }) {
  return (
    <section className="mx-auto grid max-w-7xl gap-4 px-4 py-10 md:grid-cols-3">
      {banners.map((banner) => (
        <Link
          key={banner.type}
          to={`/products?type=${banner.type}`}
          className="reveal group relative flex h-52 items-end overflow-hidden rounded-3xl p-6 text-white"
        >
          <img
            src={products.find((p) => p.type === banner.type)?.image}
            alt=""
            loading="lazy"
            className="absolute inset-0 size-full object-cover transition duration-700 group-hover:scale-110"
          />
          <div className="absolute inset-0 bg-linear-to-t from-black/80 via-black/30 to-transparent" />
          <div className="relative">
            <h2 className="font-heading text-2xl font-bold">{banner.title}</h2>
            <p className="text-sm text-white/80">{banner.text}</p>
          </div>
          <span className="absolute top-4 right-4 grid size-10 place-items-center rounded-full bg-white/20 backdrop-blur transition group-hover:rotate-45 group-hover:bg-highlight group-hover:text-highlight-foreground">
            <ArrowUpRight className="size-5" />
          </span>
        </Link>
      ))}
    </section>
  )
}
