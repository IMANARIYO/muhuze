import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'

const tones = {
  success: 'bg-primary/10 text-primary',
  warning: 'bg-highlight/25 text-highlight-foreground dark:text-highlight',
  danger: 'bg-destructive/10 text-destructive',
  neutral: 'bg-muted text-muted-foreground',
}

export function StatusBadge({ tone, children }: { tone: keyof typeof tones; children: ReactNode }) {
  return (
    <Badge variant="secondary" className={tones[tone]}>
      <span className="size-1.5 rounded-full bg-current" />
      {children}
    </Badge>
  )
}
