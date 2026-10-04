import { useSyncExternalStore } from 'react'

// Kept in the browser until the backend wishlist endpoint exists.
const KEY = 'wishlist'
const listeners = new Set<() => void>()
let ids: number[] = JSON.parse(localStorage.getItem(KEY) ?? '[]')

const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function toggle(id: number) {
  ids = ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]
  localStorage.setItem(KEY, JSON.stringify(ids))
  listeners.forEach((listener) => listener())
}

export function useWishlist() {
  const saved = useSyncExternalStore(subscribe, () => ids)
  return { ids: saved, toggle }
}
