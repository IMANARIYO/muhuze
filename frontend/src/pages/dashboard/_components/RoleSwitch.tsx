import { useQueryClient } from '@tanstack/react-query'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { demoRoles, setDemoRole, type DemoRole } from '@/services/auth'

/** Demo only: swaps the signed-in user so each role's dashboard can be seen. Hidden once the API is connected. */
export function RoleSwitch({ role }: { role: string }) {
  const client = useQueryClient()
  if (!demoRoles.length) return null

  return (
    <Tabs
      value={role}
      onValueChange={(next: DemoRole) => {
        setDemoRole(next)
        void client.invalidateQueries({ queryKey: ['me'] })
      }}
    >
      <TabsList aria-label="View the dashboard as">
        {demoRoles.map((item) => <TabsTrigger key={item} value={item} className="px-3">{item}</TabsTrigger>)}
      </TabsList>
    </Tabs>
  )
}
