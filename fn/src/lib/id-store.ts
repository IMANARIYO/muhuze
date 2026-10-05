import { useSyncExternalStore } from 'react'

/** A list of product ids kept in the browser until the backend endpoint exists. */
export function createIdStore(key: string) {
  const listeners = new Set<() => void>()
  let ids: number[] = JSON.parse(localStorage.getItem(key) ?? '[]')

  const subscribe = (listener: () => void) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
  }

  function set(next: number[]) {
    ids = next
    localStorage.setItem(key, JSON.stringify(ids))
    listeners.forEach((listener) => listener())
  }
  const toggle = (id: number) => set(ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id])
  const clear = () => set([])

  return function useIds() {
    const saved = useSyncExternalStore(subscribe, () => ids)
    return { ids: saved, toggle, clear }
  }
}
