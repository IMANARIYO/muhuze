import { useSyncExternalStore } from 'react'

// In-memory list with add/update/remove, used by dashboard pages until their API endpoints exist.
// Replace each store with useQuery/useMutation when the backend is connected.
export function createStore<T>(initial: T[]) {
  let items = initial.map((item, index) => ({ ...item, id: index + 1 }))
  const listeners = new Set<() => void>()

  const set = (next: typeof items) => {
    items = next
    listeners.forEach((listener) => listener())
  }
  const subscribe = (listener: () => void) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
  }
  const actions = {
    add: (item: T) => set([{ ...item, id: Math.max(0, ...items.map((i) => i.id)) + 1 }, ...items]),
    update: (id: number, patch: Partial<T>) => set(items.map((i) => (i.id === id ? { ...i, ...patch } : i))),
    remove: (id: number) => set(items.filter((i) => i.id !== id)),
  }

  function useStore() {
    return { items: useSyncExternalStore(subscribe, () => items), ...actions }
  }
  // The actions are also reachable outside React, e.g. from a demo service.
  return Object.assign(useStore, actions)
}

export type Stored<T> = T & { id: number }
