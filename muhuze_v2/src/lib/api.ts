export const API_URL: string | undefined = import.meta.env.VITE_API_URL

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_URL + path, {
    credentials: 'include',
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}
