import { Heart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useWishlist } from '@/hooks/use-wishlist'
import { cn } from '@/lib/utils'

export function WishlistButton({ id, className }: { id: number; className?: string }) {
  const { ids, toggle } = useWishlist()
  const saved = ids.includes(id)

  return (
    <Button
      variant="secondary"
      size="icon"
      aria-label={saved ? 'Remove from wishlist' : 'Add to wishlist'}
      aria-pressed={saved}
      className={cn('rounded-full shadow-sm transition active:scale-75', className)}
      onClick={(event) => {
        event.preventDefault()
        toggle(id)
      }}
    >
      <Heart className={cn('transition', saved && 'scale-110 fill-destructive text-destructive')} />
    </Button>
  )
}
