import { Lock, Phone } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import type { Product } from '@/types/product'

export function SellerCard({ seller }: { seller: Product['seller'] }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border bg-card p-4">
      <Avatar className="size-12">
        <AvatarFallback className="bg-primary text-primary-foreground">{seller.name[0]}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{seller.name}</p>
        {seller.contact ? (
          <a href={`tel:${seller.contact.replaceAll(' ', '')}`} className="flex items-center gap-1.5 text-sm text-primary hover:underline">
            <Phone className="size-3.5" /> {seller.contact}
          </a>
        ) : (
          <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Lock className="size-3.5" /> Contact available once the seller activates their subscription
          </p>
        )}
      </div>
    </div>
  )
}
