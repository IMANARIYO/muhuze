import { createStore, type Stored } from '@/lib/demo-store'

interface Account {
  name: string
  email: string
  role: string
  suspended: boolean
  joined: string
}

export type StoredAccount = Stored<Account>

const account = (name: string, role: string, joined: string, suspended = false): Account => ({
  name, role, joined, suspended, email: `${name.toLowerCase().replaceAll(' ', '.')}@example.com`,
})

export const useUsers = createStore<Account>([
  account('Aline Uwase', 'Admin', '2026-01-12'),
  account('Eric Mugisha', 'Seller', '2026-02-03'),
  account('Grace Ineza', 'Seller', '2026-02-21'),
  account('Patrick Nshuti', 'Buyer', '2026-03-09'),
  account('Diane Keza', 'Support', '2026-03-30'),
  account('Jean Habimana', 'Seller', '2026-04-17', true),
  account('Sandrine Umutoni', 'Buyer', '2026-05-02'),
  account('Kevin Ishimwe', 'Buyer', '2026-06-14'),
  account('Claire Mukamana', 'Seller', '2026-07-08'),
  account('Yves Ndayisaba', 'Buyer', '2026-08-25'),
  account('Bella Gasana', 'Buyer', '2026-09-11'),
])
