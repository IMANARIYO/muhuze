import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import {
  ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { formatCount } from '@/lib/format'
import { monthlyRevenue } from '../_data'

const config = {
  commission: { label: 'Sale commission', color: 'var(--chart-1)' },
  subscription: { label: 'Subscriptions', color: 'var(--chart-2)' },
} satisfies ChartConfig

export function RevenueChart() {
  return (
    <section className="rounded-2xl border bg-card p-5">
      <h2 className="font-heading font-semibold">Platform revenue</h2>
      <p className="text-sm text-muted-foreground">Last 6 months, in RWF</p>
      <ChartContainer config={config} className="mt-4 h-72 w-full">
        <BarChart data={monthlyRevenue} accessibilityLayer maxBarSize={40}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={44} tickFormatter={formatCount} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar dataKey="commission" stackId="revenue" fill="var(--color-commission)" stroke="var(--card)" strokeWidth={2} />
          <Bar dataKey="subscription" stackId="revenue" fill="var(--color-subscription)" stroke="var(--card)" strokeWidth={2} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ChartContainer>
    </section>
  )
}
