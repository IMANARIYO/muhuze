import { PageHeader } from '../_components/PageHeader'
import { Plans } from './_components/Plans'
import { RatesCard } from './_components/RatesCard'
import { SellerSubscriptions } from './_components/SellerSubscriptions'

export default function DashboardSubscriptions() {
  return (
    <>
      <PageHeader title="Subscriptions" description="How the platform earns: commission on sales and plans for sellers." />
      <RatesCard />
      <Plans />
      <SellerSubscriptions />
    </>
  )
}
