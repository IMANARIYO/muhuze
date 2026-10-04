import { Link } from 'react-router'
import { buttonVariants } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="grid flex-1 place-items-center px-4 py-24 text-center">
      <div className="space-y-4">
        <p className="font-heading text-6xl font-bold text-primary">404</p>
        <p className="text-muted-foreground">This page does not exist yet.</p>
        <Link to="/" className={buttonVariants()}>Back home</Link>
      </div>
    </div>
  )
}
