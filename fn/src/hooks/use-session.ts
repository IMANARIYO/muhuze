import { useQuery } from '@tanstack/react-query'
import { getMe } from '@/services/auth'

export function useSession() {
  const { data: user, isPending } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: Infinity,
    retry: false,
  })
  const can = (permission: string) => user?.permissions.includes(permission) ?? false
  return { user, isPending, can }
}
