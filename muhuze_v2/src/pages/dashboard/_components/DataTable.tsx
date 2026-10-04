import { ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export interface Column<T> {
  header: string
  cell: (row: T) => ReactNode
  className?: string
}

interface Props<T> {
  rows: T[]
  columns: Column<T>[]
  /** Text of a row that the search box matches against. */
  search?: (row: T) => string
  toolbar?: ReactNode
}

const PAGE_SIZE = 8

export function DataTable<T extends { id: number }>({ rows, columns, search, toolbar }: Props<T>) {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(0)

  const found = search ? rows.filter((row) => search(row).toLowerCase().includes(query.toLowerCase())) : rows
  const lastPage = Math.max(0, Math.ceil(found.length / PAGE_SIZE) - 1)
  const current = Math.min(page, lastPage)
  const start = current * PAGE_SIZE
  const visible = found.slice(start, start + PAGE_SIZE)

  return (
    <div className="overflow-hidden rounded-2xl border bg-card">
      {(search || toolbar) && (
        <div className="flex flex-wrap items-center gap-3 border-b p-3">
          {search && (
            <div className="relative w-full sm:w-64">
              <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                placeholder="Search..."
                className="pl-8"
                onChange={(event) => {
                  setQuery(event.target.value)
                  setPage(0)
                }}
              />
            </div>
          )}
          <div className="ml-auto">{toolbar}</div>
        </div>
      )}
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            {columns.map((column) => (
              <TableHead key={column.header} className={column.className}>{column.header}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {visible.map((row) => (
            <TableRow key={row.id}>
              {columns.map((column) => (
                <TableCell key={column.header} className={column.className}>{column.cell(row)}</TableCell>
              ))}
            </TableRow>
          ))}
          {!visible.length && (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-32 text-center text-muted-foreground">
                Nothing to show.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="flex items-center justify-between border-t px-4 py-2.5 text-sm text-muted-foreground">
        <span>
          {found.length ? `${start + 1}–${start + visible.length} of ${found.length}` : '0 results'}
        </span>
        <div className="flex gap-1">
          <Button variant="outline" size="icon-sm" aria-label="Previous page" disabled={current === 0} onClick={() => setPage(current - 1)}>
            <ChevronLeft />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Next page" disabled={current === lastPage} onClick={() => setPage(current + 1)}>
            <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  )
}
