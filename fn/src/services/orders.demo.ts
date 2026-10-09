import { createStore, type Stored } from '@/lib/demo-store'
import type { DeliveryDetails } from '@/types/order'
import type { ProductType } from '@/types/product'

// Demo orders used only while VITE_API_URL is unset. Delete with the backend connection.

export interface OrderItem {
  title: string
  seller: string
  type: ProductType
  price: number
}

interface OrderRecord extends DeliveryDetails {
  reference: string
  date: string
  /** Set by an admin once the money has arrived outside the app. */
  approved: boolean
  items: OrderItem[]
}

export type StoredOrder = Stored<OrderRecord>

const item = (title: string, seller: string, price: number): OrderItem => ({ title, seller, price, type: 'sale' })
const smartphone = item('Smartphone 128GB, dual SIM', 'Kigali Mobile', 420_000)
const headphones = item('Wireless studio headphones', 'Kigali Mobile', 95_000)
const laptop = item('Ultrabook laptop 14"', 'Kigali Mobile', 890_000)

const order = (
  reference: string, date: string, name: string, phone: string, district: string, sector: string, cell: string,
  approved: boolean, items: OrderItem[],
): OrderRecord => ({
  reference, date, name, phone, district, sector, cell, approved, items, province: 'Kigali City', paymentPhone: phone,
})

export const useOrders = createStore<OrderRecord>([
  order('MZ-1008', '2026-10-02', 'Grace Ineza', '0788300108', 'Gasabo', 'Remera', 'Rukiri I', false, [headphones, item('Instant film camera', 'Lens & Co', 130_000)]),
  order('MZ-1007', '2026-09-30', 'Diane Keza', '0728300107', 'Kicukiro', 'Niboye', 'Nyakabanda', false, [smartphone]),
  order('MZ-1006', '2026-09-12', 'Claire Mukamana', '0788300106', 'Nyarugenge', 'Nyamirambo', 'Cyivugiza', true, [laptop]),
  order('MZ-1005', '2026-08-27', 'Yves Ndayisaba', '0738300105', 'Gasabo', 'Kimironko', 'Bibare', true, [headphones, item('Classic minimalist watch', 'Timeless', 68_000)]),
  order('MZ-1004', '2026-08-03', 'Patrick Nshuti', '0788300104', 'Kicukiro', 'Kagarama', 'Muyange', true, [smartphone]),
  order('MZ-1003', '2026-07-09', 'Bella Gasana', '0798300103', 'Gasabo', 'Kacyiru', 'Kamatamu', true, [laptop]),
  order('MZ-1002', '2026-06-20', 'Kevin Ishimwe', '0728300102', 'Nyarugenge', 'Muhima', 'Kabeza', true, [headphones, item('Running sneakers', 'Stride Store', 54_000)]),
  order('MZ-1001', '2026-05-14', 'Sandrine Umutoni', '0788300101', 'Gasabo', 'Kimironko', 'Kibagabaga', true, [smartphone]),
])

/** One item a shop sold in an approved order, with what the platform keeps and what the shop receives. */
export interface Sale extends OrderItem {
  id: number
  reference: string
  date: string
  buyer: string
  phone: string
  place: string
  fee: number
  net: number
}

/** Approved sales of one shop. Commission (in percent) is only taken from sale products. */
export const salesOf = (orders: StoredOrder[], shop: string | undefined, commission: number): Sale[] =>
  orders.filter((row) => row.approved).flatMap((row) =>
    row.items.flatMap((line, index) => {
      if (line.seller !== shop) return []
      const fee = line.type === 'sale' ? Math.round((line.price * commission) / 100) : 0
      return {
        ...line, id: row.id * 100 + index, reference: row.reference, date: row.date, buyer: row.name, phone: row.phone,
        place: `${row.cell}, ${row.sector}, ${row.district}`, fee, net: line.price - fee,
      }
    }),
  )
