import type { ComponentProps, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  description: string
  onSubmit: (data: FormData) => void
  children: ReactNode
}

export function FormDialog({ open, onClose, title, description, onSubmit, children }: Props) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent>
        <form
          className="grid gap-4"
          action={(data) => {
            onSubmit(data)
            onClose()
          }}
        >
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          {children}
          <DialogFooter showCloseButton>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function Field({ label, name, ...props }: { label: string; name: string } & ComponentProps<typeof Input>) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} name={name} {...props} />
    </div>
  )
}

interface SelectFieldProps {
  label: string
  name: string
  defaultValue?: string
  options: { value: string; label: string }[]
}

export function SelectField({ label, name, defaultValue, options }: SelectFieldProps) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={name}>{label}</Label>
      <NativeSelect id={name} name={name} defaultValue={defaultValue} className="w-full">
        {options.map((option) => (
          <NativeSelectOption key={option.value} value={option.value}>{option.label}</NativeSelectOption>
        ))}
      </NativeSelect>
    </div>
  )
}
