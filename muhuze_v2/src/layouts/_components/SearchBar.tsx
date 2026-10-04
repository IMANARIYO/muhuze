import { Search } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function SearchBar({ className }: { className?: string }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()

  return (
    <form
      role="search"
      className={className}
      action={(data) => navigate(`/products?q=${encodeURIComponent(String(data.get('q') ?? ''))}`)}
    >
      <div className="flex rounded-full border-2 border-primary bg-background p-0.5 transition focus-within:shadow-lg focus-within:shadow-primary/20">
        <Input
          name="q"
          defaultValue={params.get('q') ?? ''}
          placeholder="Search phones, houses, barbers..."
          className="h-9 border-0 bg-transparent px-4 shadow-none focus-visible:ring-0"
        />
        <Button type="submit" className="h-9 rounded-full px-5">
          <Search /> <span className="hidden sm:inline">Search</span>
        </Button>
      </div>
    </form>
  )
}
