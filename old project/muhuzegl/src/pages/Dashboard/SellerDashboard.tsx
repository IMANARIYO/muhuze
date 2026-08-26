import Container from "../../components/ui/Container";

import {
  DashboardHeader,
  DashboardStats,
  DashboardQuickActions,
  DashboardListings,
  DashboardOrders,
} from "../../components/dashboard";

export default function SellerDashboard() {
  return (
    <section className="py-16 bg-slate-50 min-h-screen">
      <Container>
        <DashboardHeader />

        <DashboardStats />

        <DashboardQuickActions />

       <DashboardListings />
        <DashboardOrders />
      </Container>
    </section>
  );
}