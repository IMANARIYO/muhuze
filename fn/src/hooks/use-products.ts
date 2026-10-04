import { useQuery } from '@tanstack/react-query'
import { getProducts } from '@/services/products'
import type { ProductFilters } from '@/types/product'

export const useProducts = (filters: ProductFilters = {}) =>
  useQuery({ queryKey: ['products', filters], queryFn: () => getProducts(filters) })
