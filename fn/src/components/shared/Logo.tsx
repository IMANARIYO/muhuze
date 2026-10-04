import { Link } from 'react-router'

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-heading text-lg font-bold tracking-tight">
      <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">M</span>
      <span className="group-data-[collapsible=icon]:hidden">Muhuze</span>
    </Link>
  )
}
