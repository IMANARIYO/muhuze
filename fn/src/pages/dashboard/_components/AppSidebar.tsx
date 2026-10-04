import { Link, useLocation } from 'react-router'
import { Logo } from '@/components/shared/Logo'
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarHeader,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarRail,
} from '@/components/ui/sidebar'
import { useSession } from '@/hooks/use-session'
import type { User } from '@/types/user'
import { navGroups } from './nav'
import { UserMenu } from './UserMenu'

export function AppSidebar({ user }: { user: User }) {
  const { can } = useSession()
  const pathname = useLocation().pathname.replace(/\/$/, '')

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-16 justify-center border-b">
        <Logo />
      </SidebarHeader>
      <SidebarContent>
        {navGroups.map((group) => {
          const items = group.items.filter((item) => can(item.permission))
          if (!items.length) return null
          return (
            <SidebarGroup key={group.label}>
              <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.to}>
                    <SidebarMenuButton
                      isActive={pathname === item.to}
                      tooltip={item.label}
                      render={<Link to={item.to} />}
                      className="data-active:bg-primary data-active:text-primary-foreground data-active:shadow-md data-active:shadow-primary/25"
                    >
                      <item.icon />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroup>
          )
        })}
      </SidebarContent>
      <SidebarFooter className="border-t">
        <UserMenu user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
