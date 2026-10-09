import { MapPin } from 'lucide-react'
import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

/** Hero search: type a place, see the listings near it. */
export function LocationSearch() {
  const navigate = useNavigate()

  return (
    <form
      role="search"
      className="mx-auto mt-8 flex max-w-lg items-center border bg-card transition focus-within:border-foreground md:mx-0"
      action={(data) => navigate(`/products?location=${encodeURIComponent(String(data.get('location') ?? '').trim())}`)}
    >
      <Input
        name="location"
        required
        aria-label="Your location"
        placeholder="Where are you?"
        className="h-13 rounded-none border-0 bg-transparent px-5 text-base shadow-none focus-visible:ring-0 md:text-base dark:bg-transparent"
      />
      <MapPin className="mr-3 size-5 shrink-0 text-muted-foreground" />
      <Button type="submit" className="h-13 shrink-0 rounded-none bg-foreground px-8 text-sm font-medium tracking-widest text-background uppercase hover:bg-foreground/85">
        Find nearby
      </Button>
    </form>
  )
}
