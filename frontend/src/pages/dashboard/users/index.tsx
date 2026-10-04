import { Ban, CircleCheck, Plus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { formatDate, isoDate } from '@/lib/format'
import { DataTable, type Column } from '../_components/DataTable'
import { Field, FormDialog, SelectField } from '../_components/FormDialog'
import { PageHeader } from '../_components/PageHeader'
import { RowActions } from '../_components/RowActions'
import { StatusBadge } from '../_components/StatusBadge'
import { useRoles } from '../roles/_data'
import { useUsers, type StoredAccount } from './_data'

export default function DashboardUsers() {
  const { items, add, update, remove } = useUsers()
  const { items: roles } = useRoles()
  const [adding, setAdding] = useState(false)
  const roleOptions = roles.map((role) => ({ value: role.name, label: role.name }))

  const columns: Column<StoredAccount>[] = [
    {
      header: 'User',
      cell: (row) => (
        <div className="flex items-center gap-3">
          <Avatar><AvatarFallback className="bg-primary/10 text-primary">{row.name[0]}</AvatarFallback></Avatar>
          <div>
            <p className="font-medium">{row.name}</p>
            <p className="text-xs text-muted-foreground">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      header: 'Role',
      cell: (row) => (
        <NativeSelect
          size="sm"
          value={row.role}
          aria-label={`Role of ${row.name}`}
          onChange={(event) => {
            update(row.id, { role: event.target.value })
            toast.success(`${row.name} is now ${event.target.value}`)
          }}
        >
          {roleOptions.map((role) => <NativeSelectOption key={role.value} value={role.value}>{role.label}</NativeSelectOption>)}
        </NativeSelect>
      ),
    },
    {
      header: 'Status',
      cell: (row) => <StatusBadge tone={row.suspended ? 'danger' : 'success'}>{row.suspended ? 'Suspended' : 'Active'}</StatusBadge>,
    },
    { header: 'Joined', cell: (row) => formatDate(row.joined) },
    {
      header: '',
      cell: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={row.suspended ? `Activate ${row.name}` : `Suspend ${row.name}`}
            onClick={() => update(row.id, { suspended: !row.suspended })}
          >
            {row.suspended ? <CircleCheck /> : <Ban />}
          </Button>
          <RowActions name={row.name} onDelete={() => { remove(row.id); toast.success('User deleted') }} />
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Users" description="Everyone on the platform, with the role that decides what they can do.">
        <Button onClick={() => setAdding(true)}><Plus /> Add user</Button>
      </PageHeader>
      <DataTable rows={items} columns={columns} search={(row) => `${row.name} ${row.email} ${row.role}`} />
      <FormDialog
        open={adding}
        onClose={() => setAdding(false)}
        title="Add user"
        description="The user receives the permissions of the selected role."
        onSubmit={(data) => {
          add({
            name: String(data.get('name')),
            email: String(data.get('email')),
            role: String(data.get('role')),
            suspended: false,
            joined: isoDate(),
          })
          toast.success('User added')
        }}
      >
        <Field label="Full name" name="name" required />
        <Field label="Email" name="email" type="email" required />
        <SelectField label="Role" name="role" options={roleOptions} />
      </FormDialog>
    </>
  )
}
