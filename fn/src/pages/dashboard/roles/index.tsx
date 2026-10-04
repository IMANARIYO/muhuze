import { KeyRound, Plus, ShieldCheck, Users } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageHeader } from '../_components/PageHeader'
import { RowActions } from '../_components/RowActions'
import { useUsers } from '../users/_data'
import { RoleForm } from './_components/RoleForm'
import { useRoles, type StoredRole } from './_data'

export default function DashboardRoles() {
  const { items, remove } = useRoles()
  const { items: users } = useUsers()
  const [target, setTarget] = useState<StoredRole | 'new' | null>(null)

  return (
    <>
      <PageHeader title="Roles & permissions" description="Create roles and assign predefined permissions to them.">
        <Button onClick={() => setTarget('new')}><Plus /> New role</Button>
      </PageHeader>
      <div className="stagger grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((role) => (
          <article key={role.id} className="flex flex-col gap-4 rounded-2xl border bg-card p-5 transition hover:shadow-lg hover:shadow-primary/10">
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                <ShieldCheck className="size-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="flex items-center gap-2 font-heading font-semibold">
                  {role.name} {role.system && <Badge variant="secondary">System</Badge>}
                </h2>
                <p className="text-sm text-muted-foreground">{role.description}</p>
              </div>
              <RowActions
                name={role.name}
                onEdit={() => setTarget(role)}
                onDelete={role.system ? undefined : () => {
                  remove(role.id)
                  toast.success('Role deleted')
                }}
              />
            </div>
            <div className="mt-auto flex gap-5 border-t pt-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5"><KeyRound className="size-4" /> {role.permissions.length} permissions</span>
              <span className="flex items-center gap-1.5">
                <Users className="size-4" /> {users.filter((user) => user.role === role.name).length} assigned
              </span>
            </div>
          </article>
        ))}
      </div>
      <RoleForm target={target} onClose={() => setTarget(null)} />
    </>
  )
}
