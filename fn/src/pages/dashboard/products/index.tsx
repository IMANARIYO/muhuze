import { Package, Plus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { formatCount, formatPrice, typeLabels } from '@/lib/format'
import type { ProductType } from '@/types/product'
import { DataTable, type Column } from '../_components/DataTable'
import { PageHeader } from '../_components/PageHeader'
import { RowActions } from '../_components/RowActions'
import { TypeTabs } from '../_components/TypeTabs'
import { ListingForm } from './_components/ListingForm'
import { useListings, type StoredListing } from './_data'

export default function DashboardProducts() {
  const { items, update, remove } = useListings()
  const [type, setType] = useState<ProductType>()
  const [target, setTarget] = useState<StoredListing | 'new' | null>(null)

  const columns: Column<StoredListing>[] = [
    {
      header: 'Listing',
      cell: (row) => (
        <div className="flex items-center gap-3">
          <span className="grid size-11 shrink-0 place-items-center overflow-hidden rounded-lg bg-muted text-muted-foreground">
            {row.image ? <img src={row.image} alt="" loading="lazy" className="size-full object-cover" /> : <Package className="size-5" />}
          </span>
          <div>
            <p className="font-medium">{row.title}</p>
            <p className="text-xs text-muted-foreground">{row.category} · {row.seller}</p>
          </div>
        </div>
      ),
    },
    { header: 'Type', cell: (row) => <Badge variant="secondary">{typeLabels[row.type].name}</Badge> },
    {
      header: 'Price',
      cell: (row) => (
        <span className="font-medium">
          {formatPrice(row.price)}
          {row.unit && <span className="text-xs font-normal text-muted-foreground"> / {row.unit}</span>}
        </span>
      ),
    },
    { header: 'Views', cell: (row) => formatCount(row.views) },
    { header: 'Deals', cell: (row) => `${formatCount(row.uses)} ${typeLabels[row.type].used}` },
    {
      header: 'Visible',
      cell: (row) => (
        <Switch
          checked={row.active}
          aria-label={`Show ${row.title} in the store`}
          onCheckedChange={(active) => {
            update(row.id, { active })
            toast.success(active ? 'Listing is visible' : 'Listing hidden from the store')
          }}
        />
      ),
    },
    {
      header: '',
      cell: (row) => (
        <RowActions
          name={row.title}
          onEdit={() => setTarget(row)}
          onDelete={() => {
            remove(row.id)
            toast.success('Listing deleted')
          }}
        />
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Products" description="Every sale, rental and service listed on the marketplace.">
        <Button onClick={() => setTarget('new')}><Plus /> Add listing</Button>
      </PageHeader>
      <DataTable
        rows={items.filter((row) => !type || row.type === type)}
        columns={columns}
        search={(row) => `${row.title} ${row.category} ${row.seller}`}
        toolbar={<TypeTabs value={type} onChange={setType} />}
      />
      <ListingForm target={target} onClose={() => setTarget(null)} />
    </>
  )
}
