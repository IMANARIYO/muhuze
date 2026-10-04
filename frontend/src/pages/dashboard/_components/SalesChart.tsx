import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { formatCount } from '@/lib/format'

const config = { earnings: { label: 'Earnings', color: 'var(--chart-1)' } } satisfies ChartConfig

export function SalesChart({ data }: { data: { month: string; earnings: number }[] }) {
  return (
    <section className="rounded-2xl border bg-card p-5">
      <h2 className="font-heading font-semibold">Your earnings</h2>
      <p className="text-sm text-muted-foreground">From approved orders, per month, in RWF</p>
      <ChartContainer config={config} className="mt-4 h-72 w-full">
        <BarChart data={data} accessibilityLayer maxBarSize={40}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={44} tickFormatter={formatCount} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="earnings" fill="var(--color-earnings)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ChartContainer>
    </section>
  )
}
