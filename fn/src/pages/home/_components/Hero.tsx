import { ArrowRight, Sparkles } from 'lucide-react'
import { Link } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Product } from '@/types/product'
import { HeroScene } from './HeroScene'

const stats = [
  { value: '12k+', label: 'Listings' },
  { value: '3.4k', label: 'Sellers' },
  { value: '98%', label: 'Happy buyers' },
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
          <div className="mt-7 flex flex-wrap justify-center gap-3 md:justify-start">
            <Link to="/products" className={cn(buttonVariants({ size: 'lg' }), 'group h-12 rounded-full px-7 text-base shadow-lg shadow-primary/30')}>
              Start exploring <ArrowRight className="transition group-hover:translate-x-1" />
            </Link>
            <Link to="/products?type=service" className={cn(buttonVariants({ size: 'lg', variant: 'outline' }), 'h-12 rounded-full px-7 text-base')}>
              Find a service
            </Link>
          </div>
          <dl className="mt-10 flex justify-center gap-8 md:justify-start">
            {stats.map((stat) => (
              <div key={stat.label}>
                <dd className="font-heading text-2xl font-bold">{stat.value}</dd>
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
