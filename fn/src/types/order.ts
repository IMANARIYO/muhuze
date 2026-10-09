export interface OrderRequest {
  /** Product ids only: prices and totals are worked out by the backend. */
  items: number[]
  name: string
  phone: string
  province: string
  district: string
  sector: string
  cell: string
  /** Mobile-money number the buyer will send the money from. */
  paymentPhone: string
}

export type DeliveryDetails = Omit<OrderRequest, 'items'>

export interface Order {
  reference: string
  total: number
}
