import { ChevronDown, Store } from 'lucide-react'
import { Link } from 'react-router'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

/** Header filter: pick a shop to see only that seller's listings. */
export function ShopsMenu({ shops }: { shops: string[] }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="group flex items-center gap-1 rounded-full px-3 py-1 whitespace-nowrap text-muted-foreground transition outline-none hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring data-popup-open:bg-accent data-popup-open:text-accent-foreground">
        Shops <ChevronDown className="size-3.5 transition group-data-popup-open:rotate-180" />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-80 w-56 p-1.5">
        {shops.map((shop) => (
          <DropdownMenuItem key={shop} render={<Link to={`/products?seller=${encodeURIComponent(shop)}`} />} className="gap-2.5 px-2 py-2">
            <Store className="text-primary" /> {shop}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
