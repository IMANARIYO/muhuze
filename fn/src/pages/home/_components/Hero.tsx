import type { Product } from '@/types/product'
import { CountUp } from './CountUp'
import { HeroScene } from './HeroScene'
import { LocationSearch } from './LocationSearch'

const stats = [
  { value: 15_000, suffix: '+', label: 'Products' },
  { value: 5_000, suffix: '+', label: 'Verified sellers' },
  { value: 35_000, suffix: '+', label: 'Happy buyers' },
  { value: 98, suffix: '%', label: 'Satisfaction' },
]

export function Hero({ products }: { products: Product[] }) {
  return (
    <section className="relative overflow-hidden bg-muted">
      <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-12 md:grid-cols-2 md:py-20">
        <div className="animate-rise text-center md:text-left">
          <p className="text-xs tracking-[0.2em] text-muted-foreground uppercase">One marketplace, three ways to deal</p>
          <h1 className="mt-5 font-heading text-4xl leading-[1.15] font-light text-balance md:text-6xl">
            Buy, rent and hire,{' '}
            <strong className="font-medium">together</strong>
          </h1>
          <p className="mx-auto mt-5 max-w-md text-lg font-light text-muted-foreground md:mx-0">
            Phones, houses, cars and skilled people in one place. Share with friends and earn on every deal.
          </p>
          <LocationSearch />
          <dl className="mt-10 flex flex-wrap justify-center gap-x-8 gap-y-4 md:justify-start">
            {stats.map((stat) => (
              <div key={stat.label}>
                <dd className="font-heading text-3xl font-light"><CountUp to={stat.value} suffix={stat.suffix} /></dd>
                <dt className="text-xs tracking-widest text-muted-foreground uppercase">{stat.label}</dt>
              </div>
            ))}
          </dl>
        </div>
        <HeroScene products={products} />
      </div>
    </section>
  )
}
