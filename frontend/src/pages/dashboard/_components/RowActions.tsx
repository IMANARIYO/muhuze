import { Pencil, Trash2 } from 'lucide-react'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

interface Props {
  /** Name shown in the delete confirmation. */
  name: string
  onEdit?: () => void
  onDelete?: () => void
}

export function RowActions({ name, onEdit, onDelete }: Props) {
  return (
    <div className="flex justify-end gap-1">
      {onEdit && (
        <Button variant="ghost" size="icon-sm" aria-label={`Edit ${name}`} onClick={onEdit}>
          <Pencil />
        </Button>
      )}
      {onDelete && (
        <AlertDialog>
          <AlertDialogTrigger
            render={<Button variant="ghost" size="icon-sm" aria-label={`Delete ${name}`} className="text-destructive hover:text-destructive" />}
          >
            <Trash2 />
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete {name}?</AlertDialogTitle>
              <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction variant="destructive" onClick={onDelete}>Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  )
}
