import { toast } from 'sonner'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Field, FormDialog } from '../../_components/FormDialog'
import { permissionGroups, useRoles, type StoredRole } from '../_data'

interface Props {
  target: StoredRole | 'new' | null
  onClose: () => void
}

export function RoleForm({ target, onClose }: Props) {
  const { add, update } = useRoles()
  const role = target === 'new' ? null : target

  function save(data: FormData) {
    const values = {
      name: String(data.get('name')),
      description: String(data.get('description')),
      permissions: data.getAll('permissions').map(String),
    }
    if (role) update(role.id, values)
    else add(values)
    toast.success(role ? 'Role updated' : 'Role created')
  }

  return (
    <FormDialog
      open={target !== null}
      onClose={onClose}
      title={role ? `Edit ${role.name}` : 'New role'}
      description="Choose what people with this role are allowed to do."
      onSubmit={save}
    >
      <Field label="Role name" name="name" defaultValue={role?.name} required />
      <Field label="Description" name="description" defaultValue={role?.description} required />
      <div className="grid max-h-64 gap-4 overflow-y-auto rounded-xl border p-4 sm:grid-cols-2">
        {permissionGroups.map(({ group, items }) => (
          <fieldset key={group} className="grid content-start gap-2">
            <legend className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{group}</legend>
            {items.map((item) => (
              <Label key={item.key} className="font-normal">
                <Checkbox name="permissions" value={item.key} defaultChecked={role?.permissions.includes(item.key)} />
                {item.label}
              </Label>
            ))}
          </fieldset>
        ))}
      </div>
    </FormDialog>
  )
}
