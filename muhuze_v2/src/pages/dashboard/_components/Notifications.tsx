import { Bell } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const notifications = [
  { id: 1, title: 'New seller registered', text: 'Urban Stay joined through a referral link.', time: '5 min ago' },
  { id: 2, title: 'Subscription expired', text: 'Prime Homes contact is now hidden.', time: '1 hour ago' },
  { id: 3, title: 'Commission received', text: 'RWF 50,400 from a smartphone sale.', time: 'Yesterday' },
]

export function Notifications() {
  const [unread, setUnread] = useState(notifications.length)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon" aria-label="Notifications" className="relative" />}>
        <Bell />
        {unread > 0 && <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-highlight ring-2 ring-background" />}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuGroup>
          <DropdownMenuLabel>Notifications</DropdownMenuLabel>
          {notifications.map((item) => (
            <DropdownMenuItem key={item.id} className="flex-col items-start gap-0.5">
              <span className="font-medium">{item.title}</span>
              <span className="text-xs text-muted-foreground">{item.text}</span>
              <span className="text-[11px] text-muted-foreground/70">{item.time}</span>
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled={!unread} onClick={() => setUnread(0)} className="justify-center text-primary">
          Mark all as read
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
