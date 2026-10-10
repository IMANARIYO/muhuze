import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useSession } from '@/hooks/use-session'
import { formatDate, formatPrice } from '@/lib/format'
import { salesOf, useOrders, type Sale, type StoredOrder } from '@/services/orders.demo'
import { DataTable, type Column } from '../_components/DataTable'
import { PageHeader } from '../_components/PageHeader'
import { StatusBadge } from '../_components/StatusBadge'
import { useRates } from '../_data'

const reference = (row: { reference: string; date: string }) => (
  <div>
    <p className="font-medium">{row.reference}</p>
    <p className="text-xs text-muted-foreground">{formatDate(row.date)}</p>
  </div>
)

const person = (name: string, phone: string) => (
  <div>
    <p className="font-medium">{name}</p>
    <p className="text-xs text-muted-foreground">{phone}</p>
  </div>
)

// What a seller sees: only their own items, and only from orders an admin approved.
const saleColumns: Column<Sale>[] = [
  { header: 'Order', cell: reference },
  { header: 'Item', cell: (row) => row.title },
  { header: 'Buyer', cell: (row) => person(row.buyer, row.phone) },
  { header: 'Deliver to', cell: (row) => row.place },
  { header: 'Price', cell: (row) => formatPrice(row.price) },
  { header: 'You receive', className: 'text-right', cell: (row) => <span className="font-medium text-primary">{formatPrice(row.net)}</span> },
]

export default function DashboardOrders() {
  const { user, can } = useSession()
  const { items, update } = useOrders()
  const { items: [rates] } = useRates()

  if (!can('order.manage')) {
    return (
      <>
        <PageHeader title="Orders" description="Orders for your products appear here once Muhuze has confirmed the buyer's payment." />
        <DataTable rows={salesOf(items, user?.shop, rates.commission)} columns={saleColumns} search={(row) => `${row.reference} ${row.title} ${row.buyer}`} />
      </>
    )
  }

  const columns: Column<StoredOrder>[] = [
    { header: 'Order', cell: reference },
    { header: 'Buyer', cell: (row) => person(row.name, row.phone) },
    { header: 'Pays from', cell: (row) => row.paymentPhone },
    {
      header: 'Items',
      cell: (row) => row.items.map((line) => (
        <p key={line.title} className="text-sm">{line.title} <span className="text-xs text-muted-foreground">· {line.seller}</span></p>
      )),
    },
    { header: 'Deliver to', cell: (row) => `${row.cell}, ${row.sector}, ${row.district}` },
    { header: 'Total', cell: (row) => <span className="font-medium">{formatPrice(row.items.reduce((sum, line) => sum + line.price, 0))}</span> },
    {
      header: 'Status',
      cell: (row) => <StatusBadge tone={row.approved ? 'success' : 'warning'}>{row.approved ? 'Approved' : 'Waiting for payment'}</StatusBadge>,
    },
    {
      header: '',
      className: 'text-right',
      cell: (row) => !row.approved && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            update(row.id, { approved: true })
            toast.success(`${row.reference} approved: the sellers can now see it`)
          }}
        >
          Payment received
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Orders"
        description="Buyers pay outside the app. Approve an order once its money has arrived; only then do the sellers see it."
      />
      <DataTable rows={items} columns={columns} search={(row) => `${row.reference} ${row.name} ${row.phone} ${row.paymentPhone}`} />
    </>
  )
}
