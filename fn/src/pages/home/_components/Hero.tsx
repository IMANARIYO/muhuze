import { Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
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
    <section className="relative overflow-hidden bg-linear-to-b from-accent/60 to-background">
      <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-12 md:grid-cols-2 md:py-20">
        <div className="animate-rise text-center md:text-left">
          <Badge className="bg-highlight text-highlight-foreground">
            <Sparkles /> One marketplace, three ways to deal
          </Badge>
          <h1 className="mt-5 font-heading text-4xl font-extrabold tracking-tight text-balance md:text-6xl">
            Buy, rent and hire,{' '}
            <span className="bg-linear-to-r from-primary to-highlight bg-clip-text text-transparent">together</span>
          </h1>
          <p className="mx-auto mt-4 max-w-md text-lg text-muted-foreground md:mx-0">
            Phones, houses, cars and skilled people in one place. Share with friends and earn on every deal.
          </p>
          <LocationSearch />
          <dl className="mt-10 flex flex-wrap justify-center gap-x-8 gap-y-4 md:justify-start">
            {stats.map((stat) => (
              <div key={stat.label}>
                <dd className="font-heading text-2xl font-bold"><CountUp to={stat.value} suffix={stat.suffix} /></dd>
                <dt className="text-sm text-muted-foreground">{stat.label}</dt>
              </div>
            ))}
          </dl>
        </div>
        <HeroScene products={products} />
      </div>
    </section>
  )
}
