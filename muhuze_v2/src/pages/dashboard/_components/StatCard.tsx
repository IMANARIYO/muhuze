import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string
  hint: string
  icon: LucideIcon
}

export function StatCard({ label, value, hint, icon: Icon }: Props) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border bg-card p-5 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/10">
      <div className="absolute -top-8 -right-8 size-24 rounded-full bg-primary/10 transition group-hover:scale-150" />
      <div className="relative flex items-start justify-between">
        <p className="text-sm text-muted-foreground">{label}</p>
        <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
          <Icon className="size-4.5" />
        </span>
      </div>
      <p className="relative mt-2 font-heading text-2xl font-bold tracking-tight">{value}</p>
      <p className="relative mt-1 text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}
