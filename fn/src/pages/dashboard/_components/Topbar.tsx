import { Moon, Store, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Link } from 'react-router'
import { Button, buttonVariants } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Notifications } from './Notifications'
import { RoleSwitch } from './RoleSwitch'

export function Topbar({ title, role }: { title: string; role: string }) {
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger />
      <Separator orientation="vertical" className="my-auto h-5" />
      <p className="font-heading font-semibold">{title}</p>
      <div className="ml-auto flex items-center gap-1">
        <RoleSwitch role={role} />
        <Link to="/" className={buttonVariants({ variant: 'outline' })}>
          <Store /> <span className="hidden sm:inline">View store</span>
        </Link>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle dark mode"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
        >
          <Sun className="dark:hidden" />
          <Moon className="hidden dark:block" />
        </Button>
        <Notifications />
      </div>
    </header>
  )
}
