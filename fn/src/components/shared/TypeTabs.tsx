import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { ProductType } from '@/types/product'

const tabs: { value: ProductType | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'sale', label: 'Buy' },
  { value: 'rental', label: 'Rent' },
  { value: 'service', label: 'Services' },
]

interface Props {
  value?: ProductType
  onChange: (type?: ProductType) => void
}

export function TypeTabs({ value, onChange }: Props) {
  return (
    <Tabs
      value={value ?? 'all'}
      onValueChange={(next: ProductType | 'all') => onChange(next === 'all' ? undefined : next)}
    >
      <TabsList>
        {tabs.map((tab) => (
          <TabsTrigger key={tab.value} value={tab.value} className="px-4">{tab.label}</TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}
