import type { ReactNode } from 'react'

interface Props {
  title: string
  description: string
  children?: ReactNode
}

export function PageHeader({ title, description, children }: Props) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </div>
  )
}
