import { Navigate, Outlet, useLocation } from 'react-router'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { useSession } from '@/hooks/use-session'
import { AppSidebar } from '@/pages/dashboard/_components/AppSidebar'
import { navItems } from '@/pages/dashboard/_components/nav'
import { Topbar } from '@/pages/dashboard/_components/Topbar'

export default function DashboardLayout() {
  const { user, isPending, can } = useSession()
  const pathname = useLocation().pathname.replace(/\/$/, '')
  const page = navItems.find((item) => item.to === pathname)

  if (isPending) return null
  if (!user || !can('dashboard.view')) return <Navigate to="/" replace />
  if (page && !page.permissions.some(can)) return <Navigate to="/dashboard" replace />

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      <SidebarInset className="min-w-0 bg-muted/40">
        <Topbar title={page?.label ?? 'Dashboard'} role={user.role} />
        <main key={pathname} className="flex flex-1 animate-rise flex-col gap-6 p-4 md:p-6">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
